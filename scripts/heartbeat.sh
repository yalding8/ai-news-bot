#!/usr/bin/env bash
#
# heartbeat.sh — daily liveness ping for kit-managed projects.
#
# Part of ops-deploy-kit. See https://github.com/yalding8/ops-deploy-kit
#
# Cron contract (PRD §5.8):
#   0 10 * * * /home/ops/<project>/scripts/heartbeat.sh
#
# A 💓 message lands in the 飞书 group every morning. If a project goes
# >25h without a heartbeat → its notification chain has silently broken;
# investigate .deploy.env / webhook health.
#
# Required env (from $APP_DIR/.deploy.env):
#   PROJECT_NAME, FEISHU_BOT_WEBHOOK_URL（机器人若开签名校验再加 FEISHU_BOT_SIGN_SECRET）
#
# Optional env (all sub-checks fail-soft — never break the heartbeat itself):
#   HEARTBEAT_HEALTH_URL       if set, GET it and report HTTP code
#   HEARTBEAT_HEALTH_TIMEOUT   curl --max-time, default 5 seconds
#   HEARTBEAT_BACKUP_DIR       if set, scan dir and report file count + total size + newest
#   HEARTBEAT_BACKUP_GLOB      filename glob inside $HEARTBEAT_BACKUP_DIR, default *
#
# Exit code: always 0 (heartbeat never blocks anything).
#
set -uo pipefail

# ─── Locate APP_DIR + load .deploy.env ────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.deploy.env"

if [ -f "$ENV_FILE" ] && [ -r "$ENV_FILE" ]; then
  # Warn (never block) if group/other can access it — same check as
  # auto_pull_deploy.sh; .deploy.env holds webhook secrets and is sourced.
  env_perm=$(stat -c %a "$ENV_FILE" 2>/dev/null || stat -f %Lp "$ENV_FILE" 2>/dev/null || echo "")
  case "$env_perm" in
    ""|*00) : ;;
    *) echo "[heartbeat] WARN: $ENV_FILE perms=$env_perm (group/other-accessible)" \
            "— contains webhook secrets and is sourced; run: chmod 600 $ENV_FILE" >&2 ;;
  esac
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Fail-soft: if PROJECT_NAME is missing the heartbeat would be useless, but we
# still exit 0 so cron doesn't email error reports.
if [ -z "${PROJECT_NAME:-}" ]; then
  echo "[heartbeat] PROJECT_NAME not set in $ENV_FILE — skipping" >&2
  exit 0
fi

FEISHU_SH="$SCRIPT_DIR/feishu_notify.sh"
KIT_VERSION_FILE="$SCRIPT_DIR/.kit-version"

# ─── Last deploy info (best effort) ───────────────────────────────────────────
last_commit_sha=""
last_commit_age=""
if cd "$APP_DIR" 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
  last_commit_sha=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "")
  last_commit_iso=$(git log -1 --format=%cI 2>/dev/null || echo "")
  if [ -n "$last_commit_iso" ]; then
    # Cross-platform epoch parse — try GNU date first, then BSD date.
    if last_commit_epoch=$(date -d "$last_commit_iso" +%s 2>/dev/null) || \
       last_commit_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last_commit_iso" +%s 2>/dev/null); then
      now_epoch=$(date +%s)
      delta=$(( now_epoch - last_commit_epoch ))
      if [ $delta -lt 3600 ]; then
        last_commit_age="（${delta} 秒前）"
      elif [ $delta -lt 86400 ]; then
        last_commit_age="（$((delta / 3600)) 小时前）"
      else
        last_commit_age="（$((delta / 86400)) 天前）"
      fi
    fi
  fi
fi
[ -z "$last_commit_sha" ] && last_commit_sha="?"

# ─── Kit version ──────────────────────────────────────────────────────────────
kit_version=""
if [ -f "$KIT_VERSION_FILE" ]; then
  kit_tag=$(grep '^KIT_TAG=' "$KIT_VERSION_FILE" 2>/dev/null | cut -d= -f2- || echo "")
  kit_ver=$(grep '^KIT_VERSION=' "$KIT_VERSION_FILE" 2>/dev/null | cut -d= -f2- || echo "")
  kit_commit=$(grep '^KIT_COMMIT=' "$KIT_VERSION_FILE" 2>/dev/null | cut -d= -f2- || echo "")
  if [ -n "$kit_tag" ]; then
    kit_version="$kit_tag"
  elif [ -n "$kit_ver" ]; then
    kit_version="${kit_ver} @ ${kit_commit:0:8}"
  fi
fi
[ -z "$kit_version" ] && kit_version="?"

# ─── Webhook rotation check (PRD §5.10) ───────────────────────────────────────
rotation_warning=""
if [ -f "$ENV_FILE" ]; then
  rotation_date=$(grep -oE 'created date: [0-9]{4}-[0-9]{2}-[0-9]{2}' "$ENV_FILE" 2>/dev/null | head -1 | sed 's/created date: //')
  if [ -n "$rotation_date" ]; then
    if rotation_epoch=$(date -d "$rotation_date" +%s 2>/dev/null) || \
       rotation_epoch=$(date -j -f "%Y-%m-%d" "$rotation_date" +%s 2>/dev/null); then
      now_epoch=$(date +%s)
      age_days=$(( (now_epoch - rotation_epoch) / 86400 ))
      if [ "$age_days" -gt 180 ]; then
        rotation_warning="\n\n⏰ webhook 已 ${age_days} 天未轮换 (建议每 6 个月一次)"
      fi
    fi
  fi
fi

# ─── Disk usage (always, /-only) ──────────────────────────────────────────────
disk_pct=$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,""); print $5}')
[ -z "$disk_pct" ] && disk_pct="?"

# ─── API health check (optional) ──────────────────────────────────────────────
api_line=""
if [ -n "${HEARTBEAT_HEALTH_URL:-}" ]; then
  health_timeout="${HEARTBEAT_HEALTH_TIMEOUT:-5}"
  http_code=$(curl -s -o /dev/null -m "$health_timeout" -w '%{http_code}' \
    "$HEARTBEAT_HEALTH_URL" 2>/dev/null || echo "000")
  case "$http_code" in
    2*)  api_line="\n**API**：✅ ${http_code}" ;;
    000) api_line="\n**API**：❓ unreachable" ;;
    *)   api_line="\n**API**：⚠️ ${http_code}" ;;
  esac
fi

# ─── Backup status (optional) ─────────────────────────────────────────────────
# Cross-platform stat helpers. BSD (macOS) uses `stat -f <format>` while
# GNU/Linux uses `stat -c <format>`; on Linux `stat -f` is `--file-system`
# (different feature entirely), so probe once and pick the right form.
if stat -c %Y /dev/null >/dev/null 2>&1; then
  _file_mtime() { stat -c %Y "$1" 2>/dev/null || echo 0; }
  _file_size()  { stat -c %s "$1" 2>/dev/null || echo 0; }
else
  _file_mtime() { stat -f %m "$1" 2>/dev/null || echo 0; }
  _file_size()  { stat -f %z "$1" 2>/dev/null || echo 0; }
fi

backup_line=""
if [ -n "${HEARTBEAT_BACKUP_DIR:-}" ]; then
  bdir="$HEARTBEAT_BACKUP_DIR"
  bglob="${HEARTBEAT_BACKUP_GLOB:-*}"
  if [ -d "$bdir" ]; then
    count=0
    newest=""
    newest_mtime=0
    total_bytes=0
    shopt -s nullglob
    for f in "$bdir"/$bglob; do
      [ -f "$f" ] || continue
      count=$((count + 1))
      mtime=$(_file_mtime "$f")
      if [ "$mtime" -gt "$newest_mtime" ]; then
        newest_mtime="$mtime"
        newest=$(basename "$f")
      fi
      size=$(_file_size "$f")
      total_bytes=$((total_bytes + size))
    done
    shopt -u nullglob
    human=$(awk -v b="$total_bytes" 'BEGIN {
      u="B"; s=b
      if (s>=1024) {s/=1024; u="K"}
      if (s>=1024) {s/=1024; u="M"}
      if (s>=1024) {s/=1024; u="G"}
      printf "%.1f%s", s, u
    }')
    backup_line="\n**备份**：${count} 个文件 / ${human} / 最新 ${newest:-无}"
  else
    backup_line="\n**备份**：❓ 目录 \`${bdir}\` 不存在"
  fi
fi

# ─── SLA footer (always) ──────────────────────────────────────────────────────
sla_footer="\n\n> 25h 未收到 = 告警链路异常，请排查 webhook / 出网 / cron"

# ─── Send heartbeat ───────────────────────────────────────────────────────────
if [ ! -x "$FEISHU_SH" ]; then
  echo "[heartbeat] $FEISHU_SH missing or not executable — skipping" >&2
  exit 0
fi

now=$(date '+%Y-%m-%d %H:%M:%S')
host=$(hostname 2>/dev/null || echo "?")

"$FEISHU_SH" "💓 ${PROJECT_NAME} 心跳" \
  "\n**时间**：${now}\n**主机**：${host}\n**最近部署**：\`${last_commit_sha}\` ${last_commit_age}\n**磁盘**：${disk_pct}%${api_line}${backup_line}\n**Kit 版本**：${kit_version}${rotation_warning}${sla_footer}"
