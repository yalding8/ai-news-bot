#!/usr/bin/env bash
#
# feishu_notify.sh — 飞书 / Lark 自定义群机器人 interactive card 发送器。
#
# Part of ops-deploy-kit. wecom_notify.sh 的飞书孪生（同调用接口）：
#   title → 卡片标题头；body → lark_md 正文（**粗体** / [文字](url) / 换行可渲染）。
#
# Usage:
#   ./feishu_notify.sh "<title>" "<lark_md body>"
#
# Required env:
#   FEISHU_BOT_WEBHOOK_URL   群机器人 webhook（https://open.feishu.cn/open-apis/bot/v2/hook/xxx）。
#                            未设 → log to stderr and exit 0（绝不阻塞调用方）。
# Optional env:
#   FEISHU_BOT_SIGN_SECRET   若机器人开了「签名校验」安全设置，必须给 secret，否则飞书静默拒收。
#                            （CLAUDE.md 教训：sign secret 缺失会静默失败，先检查。）
#
# Exit code: 始终 0。通知失败绝不能搞挂调用它的 deploy/cron。错误进 stderr。
#
# 协议要点（与企微的区别，踩过坑）：
#   - 飞书要 "msg_type"（蛇形），企微要 "msgtype"（驼峰）。发错 → {"code":19002,"msg":"params error, msg_type need"}
#   - 成功响应 {"code":0,...}；失败 {"code":<非0>,"msg":...}（企微是 errcode/errmsg）
set -uo pipefail

WEBHOOK_URL="${FEISHU_BOT_WEBHOOK_URL:-}"
SIGN_SECRET="${FEISHU_BOT_SIGN_SECRET:-}"
TITLE="${1:-(no title)}"
CONTENT="${2:-}"

if [ -z "$WEBHOOK_URL" ]; then
  echo "[feishu_notify] FEISHU_BOT_WEBHOOK_URL not set, skipping" >&2
  exit 0
fi

# ─── JSON 字符串转义（与 wecom_notify 同款五步，保护字面 \n）──────────────
_escape_for_json() {
  local s="$1"
  local nl=$'\001OPSKIT_NL\001'
  s="${s//\\n/$nl}"          # 1. 保护字面 \n（\ + n 两字符）
  s="${s//\\/\\\\}"           # 2. 转义剩余反斜杠
  s="${s//\"/\\\"}"           # 3. 转义双引号
  s="${s//$'\n'/\\n}"         # 4. 真实换行 → JSON \n
  s="${s//$nl/\\n}"           # 5. 还原被保护的 \n
  printf '%s' "$s"
}

TITLE_ESC=$(_escape_for_json "${TITLE}")
BODY_ESC=$(_escape_for_json "${CONTENT}")

# ─── 可选签名（飞书算法：sign = base64(HMAC-SHA256(key=<ts>\n<secret>, msg=""))）──
sign_fields=""
if [ -n "$SIGN_SECRET" ]; then
  ts=$(date +%s)
  # HMAC 的 key 本身含一个换行：<timestamp>\n<secret>；消息体为空。
  sign=$(printf '%s' '' | openssl dgst -sha256 -hmac "$(printf '%s\n%s' "$ts" "$SIGN_SECRET")" -binary | base64)
  if [ -z "$sign" ]; then
    echo "[feishu_notify] 签名计算失败（openssl 不可用？），改发不带签名（开了签名校验则会被拒）" >&2
  else
    sign_fields="\"timestamp\":\"${ts}\",\"sign\":\"${sign}\","
  fi
fi

# interactive card：title → 卡片头，body → lark_md div（渲染 **粗体** / [文字](url) 链接 / 换行；
# 注：lark_md 不支持 > 引用，会字面显示——对运维心跳/部署通知可接受）。
payload="{${sign_fields}\"msg_type\":\"interactive\",\"card\":{\"config\":{\"wide_screen_mode\":true},\"header\":{\"title\":{\"tag\":\"plain_text\",\"content\":\"${TITLE_ESC}\"}},\"elements\":[{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"${BODY_ESC}\"}}]}}"

resp_file=$(mktemp /tmp/feishu_resp.XXXXXX)
trap 'rm -f "$resp_file"' EXIT

http_code=$(curl -s -o "$resp_file" -w '%{http_code}' \
  --max-time 10 \
  -X POST \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  "$WEBHOOK_URL" 2>/dev/null || echo "000")

if [ "$http_code" != "200" ]; then
  echo "[feishu_notify] HTTP $http_code: $(head -c 200 "$resp_file" 2>/dev/null)" >&2
  exit 0
fi

# HTTP 200 仍可能 code != 0（webhook 错 / 签名不符 / 关键词不匹配 / 频控）
if grep -q '"code":0' "$resp_file" 2>/dev/null || grep -q '"StatusCode":0' "$resp_file" 2>/dev/null; then
  exit 0
fi
echo "[feishu_notify] non-zero code: $(head -c 200 "$resp_file" 2>/dev/null)" >&2
exit 0
