#!/bin/bash
# Auto pull and deploy ai-news-bot when new commits detected on origin/main.
# Runs via cron every 2 minutes; idempotent fast-exit when nothing to do.
#
# Adapted from /home/ops/aifx/auto_pull_deploy.sh with three ai-news-bot
# specific additions:
#   1. flock() to prevent concurrent deploys (pip / playwright install can
#      occasionally exceed the 2-min cron interval on first upgrade).
#   2. Backup + restore .news_cache.json across the hard-reset — even after
#      we untracked it, belt-and-suspenders in case it gets re-added by
#      accident upstream.
#   3. playwright install chromium (idempotent, no-op if already matches
#      the pinned version) — pip install only handles the python package,
#      the browser binary is separate.

APP_DIR="/home/ops/ai-news-bot"
LOG_FILE="$APP_DIR/deploy.log"
LOCK_FILE="$APP_DIR/.deploy.lock"

cd "$APP_DIR" || exit 1

# Prevent concurrent deploys (first-run upgrades can take > 2 min)
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

# Fast path: no new commits → exit silently
git fetch origin 2>>"$LOG_FILE"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

echo "$(date) [DEPLOY] New commits detected: $LOCAL -> $REMOTE" >> "$LOG_FILE"

# Backup stateful files that live outside source control but may be
# destroyed by hard-reset (historically .news_cache.json was tracked).
cp .env .env.deploybackup 2>/dev/null || true
cp .news_cache.json .news_cache.deploybackup 2>/dev/null || true

# Hard-reset to remote
git reset --hard origin/main >> "$LOG_FILE" 2>&1

# Restore stateful files (overwrites any file resurrected by the reset)
mv .env.deploybackup .env 2>/dev/null || true
mv .news_cache.deploybackup .news_cache.json 2>/dev/null || true

# Update python deps (quiet; pip is fast on no-op)
source venv/bin/activate
pip install -q -r requirements.txt >> "$LOG_FILE" 2>&1

# Ensure playwright chromium binary matches python package version.
# Idempotent: no-op when already at target version.
python -m playwright install chromium >> "$LOG_FILE" 2>&1

echo "$(date) [DEPLOY] Completed: now at $REMOTE" >> "$LOG_FILE"
