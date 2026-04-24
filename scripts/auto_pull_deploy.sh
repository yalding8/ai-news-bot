#!/bin/bash
#
# auto_pull_deploy.sh — 服务器侧自动部署：检测新 commit → 拉取 → 装依赖 → 推企微通知
#
# 触发：crontab `*/2 * * * * /home/ops/ai-news-bot/scripts/auto_pull_deploy.sh`
# 幂等：无新 commit 时秒级退出，不写日志、不推通知
#
# 通知（复用 uhomes-workorder 运维工程师群）：
#   - 成功：✅ 部署成功（版本号 / 作者 / 变更 / 提交数）
#   - 失败：⚠️ 部署失败（退出码 / 日志查看命令）
#   - git 网络类失败（exit 128）限频：连续 5 次才告警一次，避免风暴
#
# 环境（可选）：
#   WECOM_BOT_WEBHOOK_URL  企微 webhook；默认从 /opt/dootask/.deploy.env 加载
#   NET_FAIL_THRESHOLD     git 网络类失败告警阈值（默认 5）
#
set -euo pipefail

APP_DIR="/home/ops/ai-news-bot"
LOG_FILE="$APP_DIR/deploy.log"
LOCK_FILE="$APP_DIR/.deploy.lock"
WECOM_SH="$APP_DIR/scripts/wecom_notify.sh"

FAIL_COUNT_FILE="$APP_DIR/.deploy-fail-count"
ALERT_SENT_FILE="$APP_DIR/.deploy-alert-sent"
NET_FAIL_THRESHOLD="${NET_FAIL_THRESHOLD:-5}"

# 加载企微 webhook。优先级：
#   1. $APP_DIR/.deploy.env          （项目独立配置，推荐）
#   2. /opt/dootask/.deploy.env      （与 uhomes-workorder 共用的运维工程师群，fallback）
for env_candidate in "$APP_DIR/.deploy.env" "/opt/dootask/.deploy.env"; do
  if [ -f "$env_candidate" ] && [ -r "$env_candidate" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_candidate"
    set +a
    break
  fi
done

cd "$APP_DIR" || exit 1

# 并发锁：首次 pip / playwright install 可能 > 2 min，防止 cron 重叠踩踏
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

DEPLOY_SUCCESS=0

notify_wecom() {
  local title="$1" content="$2"
  [ -x "$WECOM_SH" ] && "$WECOM_SH" "$title" "$content" || true
}

# EXIT trap：非成功退出时推失败通知（git 网络失败限频）
cleanup_and_notify() {
  local rc=$?
  if [ $rc -eq 0 ] || [ $DEPLOY_SUCCESS -ne 0 ]; then
    return
  fi

  local should_notify=true
  if [ $rc -eq 128 ]; then
    # git 网络类失败（fetch/reset），限频
    local count
    count=$(cat "$FAIL_COUNT_FILE" 2>/dev/null || echo 0)
    count=$((count + 1))
    echo "$count" > "$FAIL_COUNT_FILE"
    if [ "$count" -lt "$NET_FAIL_THRESHOLD" ] || [ -f "$ALERT_SENT_FILE" ]; then
      should_notify=false
    else
      touch "$ALERT_SENT_FILE"
    fi
  fi

  if [ "$should_notify" = "true" ]; then
    local fail_extra=""
    if [ $rc -eq 128 ] && [ -f "$ALERT_SENT_FILE" ]; then
      local count
      count=$(cat "$FAIL_COUNT_FILE" 2>/dev/null || echo "?")
      fail_extra="\n**连续失败**：${count} 次 (已达告警阈值 ${NET_FAIL_THRESHOLD})"
    fi
    local now host
    now=$(date '+%Y-%m-%d %H:%M:%S')
    host=$(hostname 2>/dev/null || echo "?")
    notify_wecom "⚠️ ai-news-bot 部署失败" \
      "\n**时间**：${now}\n**主机**：${host}\n**退出码**：${rc}${fail_extra}\n**脚本**：\`${APP_DIR}/scripts/auto_pull_deploy.sh\`\n**日志**：\`tail -50 ${LOG_FILE}\`"
  fi
}
trap cleanup_and_notify EXIT

# Fast path：无新 commit 秒退
git fetch origin 2>>"$LOG_FILE"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  exit 0
fi

echo "$(date) [DEPLOY] New commits detected: $LOCAL -> $REMOTE" >> "$LOG_FILE"

# 备份运行态文件（.news_cache.json 虽已 untrack 但历史仓库可能回退）
cp .env .env.deploybackup 2>/dev/null || true
cp .news_cache.json .news_cache.deploybackup 2>/dev/null || true

# Hard-reset 到远端
git reset --hard origin/main >> "$LOG_FILE" 2>&1

# 恢复运行态
mv .env.deploybackup .env 2>/dev/null || true
mv .news_cache.deploybackup .news_cache.json 2>/dev/null || true

# Python 依赖（幂等，已装的 pip 秒退）
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt >> "$LOG_FILE" 2>&1

# Playwright chromium 浏览器二进制（幂等，已最新秒退）
python -m playwright install chromium >> "$LOG_FILE" 2>&1

echo "$(date) [DEPLOY] Completed: now at $REMOTE" >> "$LOG_FILE"

DEPLOY_SUCCESS=1

# ── 成功通知 ──
short_before="${LOCAL:0:8}"
short_after="${REMOTE:0:8}"

# change_count 计算：避开 set -o pipefail 下 git log 空范围静默失败的坑
# （CLAUDE.md §Bash 防御模式 陷阱 1）
change_count=0
if [ "$LOCAL" != "$REMOTE" ]; then
  set +o pipefail
  change_count=$(git log --oneline "$LOCAL..$REMOTE" 2>/dev/null | wc -l | tr -d ' ')
  set -o pipefail
fi
top_author=$(git log -1 --pretty='%an' "$REMOTE" 2>/dev/null || echo "?")

# 解析 GitHub compare URL（支持 https 和 ssh 两种 remote 形式）
remote_url=$(git remote get-url origin 2>/dev/null || echo "")
remote_url="${remote_url%.git}"
case "$remote_url" in
  git@github.com:*) repo_url="https://github.com/${remote_url#git@github.com:}" ;;
  https://*)        repo_url="$remote_url" ;;
  *)                repo_url="" ;;
esac

version_line="\`${short_before}\` → \`${short_after}\` · ${change_count} 个提交"
# diff_line: wecom 群机器人 markdown 的限制发现（2026-04-24 两轮反馈）：
#   - 裸 URL：既不显色也不可点（wecom markdown 不做 URL auto-link）
#   - [text](url)：能点击但不显色（和普通文字视觉一致）
# 折中：markdown link 提供点击能力，emoji (🔗) + 文字提示 (点击查看 ↗)
# 作为"这是链接"的视觉 affordance，用户看到会尝试点
if [ -n "$repo_url" ]; then
  diff_line="\n**Diff**：[🔗 点击查看 diff ↗](${repo_url}/compare/${short_before}...${short_after})"
else
  diff_line=""
fi

# 构建 commit 列表（top 3 + 溢出提示）
commit_list=""
if [ "$LOCAL" != "$REMOTE" ]; then
  set +o pipefail
  raw_titles=$(git log --pretty=format:'%s' "$LOCAL..$REMOTE" 2>/dev/null | head -3 || true)
  set -o pipefail
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [ -z "$commit_list" ]; then
      commit_list="- ${line}"
    else
      commit_list="${commit_list}\n- ${line}"
    fi
  done <<< "$raw_titles"
  overflow_n=$((change_count - 3))
  if [ $overflow_n -gt 0 ]; then
    commit_list="${commit_list}\n- ... 还有 ${overflow_n} 条"
  fi
fi

now=$(date '+%Y-%m-%d %H:%M:%S')
host=$(hostname 2>/dev/null || echo "?")

notify_wecom "✅ ai-news-bot 部署成功" \
  "\n**时间**：${now}\n**主机**：${host}\n**作者**：${top_author}\n**版本**：${version_line}${diff_line}\n\n**变更**：\n${commit_list}"

# 成功时清空失败计数，给下一轮网络故障重新计数
rm -f "$FAIL_COUNT_FILE" "$ALERT_SENT_FILE"
