#!/usr/bin/env bash
#
# heartbeat.sh — ai-news-bot 每日心跳
# cron: 0 10 * * * /home/ops/ai-news-bot/scripts/heartbeat.sh
#
# 25h SLA：每天 10:00 推送一条 💓。25h 没收到 = 告警链路断，排查
# webhook / 出网 / cron。
#
# 退出码: 始终 0，不阻塞 cron。

set -uo pipefail

APP_DIR="/home/ops/ai-news-bot"
WECOM_SH="$APP_DIR/scripts/wecom_notify.sh"

# 加载 webhook（先找项目级，再找共享）
WECOM_BOT_WEBHOOK_URL=""
for env_candidate in "$APP_DIR/.deploy.env" "/opt/dootask/.deploy.env"; do
  if [ -f "$env_candidate" ]; then
    WECOM_BOT_WEBHOOK_URL=$(grep '^WECOM_BOT_WEBHOOK_URL=' "$env_candidate" 2>/dev/null | cut -d'=' -f2- || true)
    [ -n "$WECOM_BOT_WEBHOOK_URL" ] && break
  fi
done
export WECOM_BOT_WEBHOOK_URL

if [ ! -x "$WECOM_SH" ]; then
  echo "[heartbeat] wecom_notify.sh 不可执行，跳过" >&2
  exit 0
fi

now=$(date '+%Y-%m-%d %H:%M:%S')
host=$(hostname 2>/dev/null || echo "?")

# 最近部署 commit + 距今多久
last_commit_sha="?"
last_commit_age="(无 git 信息)"
if cd "$APP_DIR" 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
  last_commit_sha=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "?")
  last_commit_iso=$(git log -1 --format=%cI 2>/dev/null || echo "")
  if [ -n "$last_commit_iso" ]; then
    if last_epoch=$(date -d "$last_commit_iso" +%s 2>/dev/null) || \
       last_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last_commit_iso" +%s 2>/dev/null); then
      delta=$(( $(date +%s) - last_epoch ))
      if   [ $delta -lt 3600 ];  then last_commit_age="${delta}s 前"
      elif [ $delta -lt 86400 ]; then last_commit_age="$((delta/3600))h 前"
      else                            last_commit_age="$((delta/86400))d 前"
      fi
    fi
  fi
fi

# 磁盘使用率
disk_pct=$(df -P / 2>/dev/null | awk 'NR==2{gsub(/%/,""); print $5}' || echo "?")

# cron 最近运行时间（auto_pull_deploy.sh 每 2 分钟写入此文件）
last_cron="(未记录)"
cron_file="$APP_DIR/cron_last_run.txt"
if [ -f "$cron_file" ]; then
  last_cron=$(cat "$cron_file" 2>/dev/null | tr -d '\n' || echo "?")
fi

"$WECOM_SH" "💓 ai-news-bot 心跳" \
  "**时间**：${now}\n**主机**：${host}\n**最近部署**：\`${last_commit_sha}\` (${last_commit_age})\n**磁盘**：${disk_pct}%\n**cron 最近运行**：${last_cron}\n\n> 25h 未收到心跳 = 告警链路异常，排查 webhook / cron / 出网" || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 心跳已发送"
