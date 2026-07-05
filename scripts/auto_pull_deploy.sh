#!/bin/bash
#
# auto_pull_deploy.sh — generic git-pull deploy with 飞书 (Feishu) notifications.
#
# Part of ops-deploy-kit. See https://github.com/yalding8/ops-deploy-kit
#
# Designed to be called by cron every N minutes:
#   */2 * * * * /home/ops/<project>/scripts/auto_pull_deploy.sh
#
# Behavior:
#   1. Fast path: no new commits → silent exit 0, no log line, no notification.
#   2. Otherwise: backup .env / .deploy.env → git reset --hard origin/$BRANCH →
#      restore backups → run $POST_PULL_HOOK (project-specific) → notify.
#   3. Project-specific deps (pip/npm/playwright/migrations/restarts) live in
#      $POST_PULL_HOOK, NOT here. The kit script knows nothing about your stack.
#
# Required env (load via .deploy.env at $APP_DIR/.deploy.env):
#   PROJECT_NAME             human-readable name shown in notifications
#   FEISHU_BOT_WEBHOOK_URL   webhook URL (consumed by feishu_notify.sh)
#   FEISHU_BOT_SIGN_SECRET   optional — only if the 飞书 bot enables signature
#
# Optional env (sane defaults):
#   DEPLOY_BRANCH           default: main
#   POST_PULL_HOOK          default: $APP_DIR/scripts/post_pull.sh (skipped if missing)
#   NET_FAIL_THRESHOLD      consecutive git-network failures before alerting; default: 5
#
# Exit codes:
#   0   no-op (no new commits) OR full deploy success
#   128 git network failure (throttled by NET_FAIL_THRESHOLD)
#   N   $POST_PULL_HOOK exit code (immediately notified)
#
set -euo pipefail

# ─── Locate APP_DIR from script location (not cwd) ────────────────────────────
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Load .deploy.env (must define PROJECT_NAME + FEISHU_BOT_WEBHOOK_URL) ────
ENV_FILE="$APP_DIR/.deploy.env"
if [ -f "$ENV_FILE" ] && [ -r "$ENV_FILE" ]; then
  # Warn (never block) if group/other can access it — .deploy.env holds webhook
  # secrets AND gets sourced (= executed) below. GNU stat is -c, BSD/macOS is -f;
  # both failing → skip the check (fail-soft).
  env_perm=$(stat -c %a "$ENV_FILE" 2>/dev/null || stat -f %Lp "$ENV_FILE" 2>/dev/null || echo "")
  case "$env_perm" in
    ""|*00) : ;;
    *) echo "[auto_pull_deploy] WARN: $ENV_FILE perms=$env_perm (group/other-accessible)" \
            "— contains webhook secrets and is sourced; run: chmod 600 $ENV_FILE" >&2 ;;
  esac
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Fail loudly if PROJECT_NAME missing — better than mysterious "(no title)" notifications.
: "${PROJECT_NAME:?PROJECT_NAME must be set in $ENV_FILE}"

DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
NET_FAIL_THRESHOLD="${NET_FAIL_THRESHOLD:-5}"
POST_PULL_HOOK="${POST_PULL_HOOK:-$SCRIPT_DIR/post_pull.sh}"

FEISHU_SH="$SCRIPT_DIR/feishu_notify.sh"
LOG_FILE="$APP_DIR/deploy.log"
LOCK_FILE="$APP_DIR/.deploy.lock"
FAIL_COUNT_FILE="$APP_DIR/.deploy-fail-count"
ALERT_SENT_FILE="$APP_DIR/.deploy-alert-sent"

cd "$APP_DIR" || exit 1

# ─── Concurrency guard: skip silently if another deploy is in progress ────────
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

DEPLOY_SUCCESS=0
HOOK_EXIT_CODE=0

notify_feishu() {
  local title="$1" content="$2"
  [ -x "$FEISHU_SH" ] && "$FEISHU_SH" "$title" "$content" || true
}

# ─── EXIT trap: notify on failure (git-network failures throttled) ────────────
cleanup_and_notify() {
  local rc=$?
  if [ $rc -eq 0 ] || [ $DEPLOY_SUCCESS -ne 0 ]; then
    return
  fi

  local should_notify=true
  if [ $rc -eq 128 ]; then
    # Git network class failure — throttle to avoid notification storms during
    # GitHub blips. Counter resets on first success.
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
    notify_feishu "⚠️ ${PROJECT_NAME} 部署失败" \
      "\n**时间**：${now}\n**主机**：${host}\n**退出码**：${rc}${fail_extra}\n**脚本**：\`${SCRIPT_PATH}\`\n**日志**：\`tail -50 ${LOG_FILE}\`"
  fi
}
trap cleanup_and_notify EXIT

# ─── Fast path: bail if no new commits ────────────────────────────────────────
git fetch origin 2>>"$LOG_FILE"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$DEPLOY_BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
  exit 0
fi

echo "$(date) [DEPLOY] New commits detected: $LOCAL -> $REMOTE" >> "$LOG_FILE"

# ─── Backup runtime files that should survive git reset --hard ─────────────────
# .env and .deploy.env are project-managed and must not be wiped.
# Project-specific runtime files (caches, sqlite DBs, etc.) should be in
# .gitignore so git reset --hard already leaves them untouched.
cp .env .env.deploybackup 2>/dev/null || true
cp .deploy.env .deploy.env.deploybackup 2>/dev/null || true

# ─── Apply remote ─────────────────────────────────────────────────────────────
git reset --hard "origin/$DEPLOY_BRANCH" >> "$LOG_FILE" 2>&1

# ─── Restore backups ──────────────────────────────────────────────────────────
mv .env.deploybackup .env 2>/dev/null || true
mv .deploy.env.deploybackup .deploy.env 2>/dev/null || true

# ─── Project-specific post-pull hook ──────────────────────────────────────────
# This is where pip install / npm ci / migrations / service restarts live.
# Hook contract: non-zero exit → kit notifies failure with that exit code.
if [ -x "$POST_PULL_HOOK" ]; then
  echo "$(date) [DEPLOY] Running $POST_PULL_HOOK" >> "$LOG_FILE"
  # NB: `if ! cmd; then ... $? ...` would clobber $? to 0 (the negation succeeds).
  # Capture the real exit via `||` instead, which preserves it under set -e.
  HOOK_EXIT_CODE=0
  "$POST_PULL_HOOK" >> "$LOG_FILE" 2>&1 || HOOK_EXIT_CODE=$?
  if [ "$HOOK_EXIT_CODE" -ne 0 ]; then
    echo "$(date) [DEPLOY] Hook failed with exit $HOOK_EXIT_CODE" >> "$LOG_FILE"
    exit "$HOOK_EXIT_CODE"
  fi
elif [ -e "$POST_PULL_HOOK" ]; then
  echo "$(date) [DEPLOY] WARN: $POST_PULL_HOOK exists but is not executable" >> "$LOG_FILE"
fi

echo "$(date) [DEPLOY] Completed: now at $REMOTE" >> "$LOG_FILE"

DEPLOY_SUCCESS=1

# ─── Build success notification ───────────────────────────────────────────────
short_before="${LOCAL:0:8}"
short_after="${REMOTE:0:8}"

# Compute change_count safely. CLAUDE.md §Bash 防御模式 trap #1: under
# `set -o pipefail`, an empty `git log` range can silently fail the pipeline.
change_count=0
if [ "$LOCAL" != "$REMOTE" ]; then
  set +o pipefail
  change_count=$(git log --oneline "$LOCAL..$REMOTE" 2>/dev/null | wc -l | tr -d ' ')
  set -o pipefail
fi
top_author=$(git log -1 --pretty='%an' "$REMOTE" 2>/dev/null || echo "?")

# Resolve GitHub compare URL (handles both ssh and https remote forms).
remote_url=$(git remote get-url origin 2>/dev/null || echo "")
remote_url="${remote_url%.git}"
case "$remote_url" in
  git@github.com:*) repo_url="https://github.com/${remote_url#git@github.com:}" ;;
  https://*)        repo_url="$remote_url" ;;
  *)                repo_url="" ;;
esac

version_line="\`${short_before}\` → \`${short_after}\` · ${change_count} 个提交"
# 飞书 lark_md 把 [text](url) 渲染成可点链接（比企微好：企微不自动链接裸 URL）。
if [ -n "$repo_url" ]; then
  diff_line="\n**Diff**：[🔗 点击查看 diff ↗](${repo_url}/compare/${short_before}...${short_after})"
else
  diff_line=""
fi

# Build commit list (top 3 + overflow hint).
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

notify_feishu "✅ ${PROJECT_NAME} 部署成功" \
  "\n**时间**：${now}\n**主机**：${host}\n**作者**：${top_author}\n**版本**：${version_line}${diff_line}\n\n**变更**：\n${commit_list}"

# Reset failure counter so the next outage starts fresh.
rm -f "$FAIL_COUNT_FILE" "$ALERT_SENT_FILE"
