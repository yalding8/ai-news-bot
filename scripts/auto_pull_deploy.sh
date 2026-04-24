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

# 加载企微 webhook（复用 uhomes-workorder 的运维工程师群配置）
DEPLOY_ENV_FILE="/opt/dootask/.deploy.env"
if [ -f "$DEPLOY_ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$DEPLOY_ENV_FILE"
  set +a
fi

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
    local extra=""
    if [ $rc -eq 128 ] && [ -f "$ALERT_SENT_FILE" ]; then
      local count
      count=$(cat "$FAIL_COUNT_FILE" 2>/dev/null || echo "?")
      extra="\n**连续失败**：${count} 次 (已达告警阈值 ${NET_FAIL_THRESHOLD})"
    fi
    notify_wecom "⚠️ ai-news-bot 部署失败" \
      "\n**退出码**：${rc}${extra}\n**脚本**：\`${APP_DIR}/scripts/auto_pull_deploy.sh\`\n\n日志：\`tail -50 ${LOG_FILE}\`"
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

# 避开 set -o pipefail 下 git log 空范围静默失败的坑（陷阱见 CLAUDE.md §Bash 防御模式）
change_count=0
if [ "$LOCAL" != "$REMOTE" ]; then
  set +o pipefail
  change_count=$(git log --oneline "$LOCAL..$REMOTE" 2>/dev/null | wc -l | tr -d ' ')
  set -o pipefail
fi
top_change=$(git log -1 --pretty='%s' "$REMOTE" 2>/dev/null || echo "?")
top_author=$(git log -1 --pretty='%an' "$REMOTE" 2>/dev/null || echo "?")

notify_wecom "✅ ai-news-bot 部署成功" \
  "\n**变更**：${top_change}\n**作者**：${top_author}\n**版本**：\`${short_before}\` → \`${short_after}\` （${change_count} 个提交）"

# 成功时清空失败计数，给下一轮网络故障重新计数
rm -f "$FAIL_COUNT_FILE" "$ALERT_SENT_FILE"
