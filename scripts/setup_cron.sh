#!/usr/bin/env bash
#
# setup_cron.sh — 幂等安装 ai-news-bot 的全部定时任务到 /etc/cron.d
#
# 根治方案（2026-06-03）：排程写入 root 拥有的 /etc/cron.d/ai-news-bot，而非 ops
# 用户 crontab。任何"集中迁移"本质是 `crontab -l > bak; crontab newfile` 整体重写
# 用户 crontab，物理上碰不到 /etc/cron.d/* → 不会再像 2026-05-30 / 06-03 那样把本
# 项目 cron 整条漏掉、静默断更。每个项目拥有自己独立、迁移脚本碰不到的调度文件。
#
# 装三条：① jump-autodeploy 自动部署 ② 每日新闻 ③ 每日心跳。
# 并清掉 ops 用户 crontab 里任何旧的 ai-news-bot 行（防止与 /etc/cron.d 双跑）。
#
# 用法（dingning 服务器，ops 用户；写 /etc/cron.d 需要 sudo）：
#   bash /home/ops/ai-news-bot/scripts/setup_cron.sh
#
# 改排程/模型只改下面 DESIRED，再重跑本脚本即可（幂等）。
#
# 前置：服务器 git remote 必须已是 HTTPS（public 仓库免凭证），否则 auto-deploy
#       的 git fetch 会因旧 SSH deploy key 失效而失败：
#   git -C /home/ops/ai-news-bot remote set-url origin https://github.com/yalding8/ai-news-bot.git
#
# 回滚：sudo rm /etc/cron.d/ai-news-bot  （cron 立即停止本项目全部任务）

set -euo pipefail

APP_DIR="/home/ops/ai-news-bot"
RUN_USER="ops"
# 文件名【禁止含点】，否则 cron 按 run-parts 命名规则直接跳过该文件。
CRON_D="/etc/cron.d/ai-news-bot"
mkdir -p "$APP_DIR/logs"

# 期望的 cron.d 内容（单一真相源）。
# 注意 cron.d 语法与用户 crontab 的唯一区别：时间字段后必须多一个 user 字段。
# news 行保留内联 LLM_*：qwen-plus 是批量场景的 fast model；内联确保即使 .env 未定义
# LLM_MODEL 也走 qwen-plus。config 已 load_dotenv(override=True)，.env 显式定义则优先。
DESIRED="$(cat <<CRON
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=""

# ai-news-bot cron — 由 scripts/setup_cron.sh 幂等生成，勿手改。
# 位置在 /etc/cron.d 而非用户 crontab：集中迁移重写用户 crontab 时碰不到本文件。
2-57/5 * * * * ${RUN_USER} /opt/jump-autodeploy/bin/auto-deploy.sh ${APP_DIR} >> ${APP_DIR}/logs/auto-deploy.log 2>&1
10 9 * * * ${RUN_USER} cd ${APP_DIR} && LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 LLM_MODEL=qwen-plus ${APP_DIR}/venv/bin/python start.py >> ${APP_DIR}/ai-news.log 2>&1 && curl -fsS -m 10 --retry 2 "https://hc-ping.com/\$(cat /home/ops/.hc-ping-key 2>/dev/null)/ai-news-daily" >/dev/null 2>&1
0 10 * * * ${RUN_USER} ${APP_DIR}/scripts/heartbeat.sh >> ${APP_DIR}/heartbeat.log 2>&1
CRON
)"

# 1) 写 /etc/cron.d（必须 root:root 0644，否则 cron 因"文件被非 root 可写"安全策略忽略）。
if ! sudo -v 2>/dev/null; then
  echo "[setup_cron] ✗ 写 /etc/cron.d 需要 sudo，但 ops 似乎无 sudo 权限。" >&2
  echo "             请用有 sudo 的账号跑，或联系运维授予 ops 写 /etc/cron.d 的权限。" >&2
  exit 1
fi
tmp="$(mktemp)"
printf '%s\n' "$DESIRED" > "$tmp"
sudo install -m 644 -o root -g root "$tmp" "$CRON_D"
rm -f "$tmp"

# 2) 清掉 ops 用户 crontab 里的旧 ai-news-bot 行，避免与 /etc/cron.d 双跑。
current="$(crontab -l 2>/dev/null || true)"
if printf '%s\n' "$current" | grep -qF "$APP_DIR"; then
  printf '%s\n' "$current" | grep -v -F "$APP_DIR" | crontab -
  echo "[setup_cron] 已从 ops 用户 crontab 移除旧 ai-news-bot 行（防双跑）"
fi

# 3) 验证。
echo "[setup_cron] ✓ /etc/cron.d/ai-news-bot 已安装："
sudo cat "$CRON_D"
echo
echo -n "[setup_cron] 用户 crontab 残留检查："
if crontab -l 2>/dev/null | grep -qF "$APP_DIR"; then
  echo " ⚠️ 仍有残留行（请手动清理）！"
else
  echo " ✓ 干净，无双跑风险"
fi
