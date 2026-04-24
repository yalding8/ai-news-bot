#!/usr/bin/env bash
#
# wecom_notify.sh — 推送企业微信群机器人 markdown 通知（部署事件用）
#
# 用法:
#   ./wecom_notify.sh "标题" "Markdown 正文"
#
# 环境变量:
#   WECOM_BOT_WEBHOOK_URL   企微群机器人 webhook URL（未配置则静默退出，不阻塞）
#
# 退出码:
#   始终 exit 0 — 通知失败不阻塞调用方的关键流程；错误信息写到 stderr
#
# 约定:
#   调用方不传 `"` / `\` / 除 `\n` 外的特殊字符，避免 JSON 需要额外 escape
#
set -uo pipefail

WEBHOOK_URL="${WECOM_BOT_WEBHOOK_URL:-}"
TITLE="${1:-(no title)}"
CONTENT="${2:-}"

if [ -z "$WEBHOOK_URL" ]; then
  echo "[wecom_notify] WECOM_BOT_WEBHOOK_URL 未配置，跳过推送" >&2
  exit 0
fi

payload=$(cat <<EOF
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## ${TITLE}\n${CONTENT}"
  }
}
EOF
)

resp_file=$(mktemp /tmp/wecom_resp.XXXXXX)
trap 'rm -f "$resp_file"' EXIT

http_code=$(curl -s -o "$resp_file" -w '%{http_code}' \
  --max-time 10 \
  -X POST \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  "$WEBHOOK_URL" 2>/dev/null || echo "000")

if [ "$http_code" != "200" ]; then
  echo "[wecom_notify] HTTP $http_code: $(head -c 200 "$resp_file" 2>/dev/null)" >&2
  exit 0
fi

# HTTP 200 但企微 API 可能返回 errcode != 0（例如 webhook 无效 / 限频）
if grep -q '"errcode":0' "$resp_file" 2>/dev/null; then
  exit 0
fi
echo "[wecom_notify] errcode 非 0: $(head -c 200 "$resp_file" 2>/dev/null)" >&2
exit 0
