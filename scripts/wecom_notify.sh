#!/usr/bin/env bash
#
# wecom_notify.sh — WeCom (企业微信) group-bot markdown sender.
#
# Part of ops-deploy-kit. See https://github.com/yalding8/ops-deploy-kit
#
# Usage:
#   ./wecom_notify.sh "<title>" "<markdown body>"
#
# Required env:
#   WECOM_BOT_WEBHOOK_URL   group-bot webhook URL.
#                           If unset → log to stderr and exit 0 (never blocks caller).
#
# Exit code:
#   Always 0. Notifications must never break the calling deploy/script.
#   Errors go to stderr.
#
# Calling convention:
#   - `"` and `\` in title/body are escaped automatically — pass commit messages
#     and arbitrary user input safely.
#   - Literal `\n` (two chars: backslash + n) in body is preserved as a JSON
#     newline escape — it renders as a line break in WeCom. This is the
#     idiomatic way to write multi-line markdown bodies (see auto_pull_deploy.sh).
#   - Real newline characters in body are also accepted and converted to JSON
#     `\n` escapes. Mixing both forms in one call is safe.
#
set -uo pipefail

WEBHOOK_URL="${WECOM_BOT_WEBHOOK_URL:-}"
TITLE="${1:-(no title)}"
CONTENT="${2:-}"

if [ -z "$WEBHOOK_URL" ]; then
  echo "[wecom_notify] WECOM_BOT_WEBHOOK_URL not set, skipping" >&2
  exit 0
fi

# ─── Escape for JSON string interpolation ─────────────────────────────────────
# Five-step transform; order matters. The placeholder protects literal '\n'
# (the calling convention) so that step 2 doesn't double-escape its backslash,
# and step 5 restores it as a JSON newline escape.
#
# The placeholder uses U+0001 (SOH) sentinels — vanishingly unlikely in commit
# messages, hostnames, or any other realistic input.
_escape_for_json() {
  local s="$1"
  local nl=$'\001OPSKIT_NL\001'
  s="${s//\\n/$nl}"          # 1. protect literal \n (2 chars: \ + n)
  s="${s//\\/\\\\}"           # 2. escape remaining backslashes
  s="${s//\"/\\\"}"           # 3. escape double quotes
  s="${s//$'\n'/\\n}"         # 4. real newline → JSON \n
  s="${s//$nl/\\n}"           # 5. restore protected \n as JSON \n
  printf '%s' "$s"
}

TITLE_ESC=$(_escape_for_json "$TITLE")
CONTENT_ESC=$(_escape_for_json "$CONTENT")

payload=$(cat <<EOF
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## ${TITLE_ESC}\n${CONTENT_ESC}"
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

# HTTP 200 but WeCom may still return errcode != 0 (invalid webhook / rate-limited / etc.)
if grep -q '"errcode":0' "$resp_file" 2>/dev/null; then
  exit 0
fi
echo "[wecom_notify] non-zero errcode: $(head -c 200 "$resp_file" 2>/dev/null)" >&2
exit 0
