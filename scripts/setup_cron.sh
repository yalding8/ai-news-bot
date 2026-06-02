#!/usr/bin/env bash
#
# setup_cron.sh — 幂等安装 ai-news-bot 的全部 cron
#
# 装三条：① jump-autodeploy 自动部署 ② 每日新闻 ③ 每日心跳。
# 同时清掉任何旧的 ai-news-bot cron 行（含已废弃的 SSH 版 auto_pull_deploy.sh）。
#
# 兼作 crontab 被整体重写/误删后的一键恢复（2026-05-30 集中迁移把本项目 cron
# 整条漏掉、断更 4 天的教训）。改排程/模型只改下面 DESIRED，再重跑本脚本即可。
#
# 用法（dingning 服务器，ops 用户）：
#   bash /home/ops/ai-news-bot/scripts/setup_cron.sh
#
# 前置：服务器 git remote 必须已是 HTTPS（public 仓库免凭证），否则 auto-deploy
#       的 git fetch 会因旧 SSH deploy key 失效而失败：
#   git -C /home/ops/ai-news-bot remote set-url origin https://github.com/yalding8/ai-news-bot.git

set -euo pipefail

APP_DIR="/home/ops/ai-news-bot"
mkdir -p "$APP_DIR/logs"

# 期望的 cron 行（单一真相源）。
# 注意 news 行保留内联 LLM_*：qwen-plus 是批量场景的 fast model；内联确保即使
# .env 未定义 LLM_MODEL 也走 qwen-plus。config 已用 load_dotenv(override=True)，
# 若 .env 显式定义 LLM_MODEL 则 .env 优先（应保持为 qwen-plus）。
DESIRED="$(cat <<'CRON'
2-57/5 * * * * /opt/jump-autodeploy/bin/auto-deploy.sh /home/ops/ai-news-bot >> /home/ops/ai-news-bot/logs/auto-deploy.log 2>&1
10 9 * * * cd /home/ops/ai-news-bot && LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 LLM_MODEL=qwen-plus /home/ops/ai-news-bot/venv/bin/python start.py >> /home/ops/ai-news-bot/ai-news.log 2>&1
0 10 * * * /home/ops/ai-news-bot/scripts/heartbeat.sh >> /home/ops/ai-news-bot/heartbeat.log 2>&1
CRON
)"

# 现有 crontab，剔除所有 ai-news-bot 相关行（按路径匹配，幂等去重 + 清旧），
# 其余项目的行/注释/空行原样保留（最小改动，不重排别人的排程）。
current="$(crontab -l 2>/dev/null || true)"
filtered="$(printf '%s\n' "$current" | grep -v -F '/home/ops/ai-news-bot' || true)"

# 重新拼装并写回。末尾去掉可能的连续空行收尾，但不动中间结构。
{ printf '%s\n' "$filtered"; printf '%s\n' "$DESIRED"; } | crontab -

echo "[setup_cron] ai-news-bot cron 已安装/刷新："
crontab -l | grep -F '/home/ops/ai-news-bot' || echo "  (未找到，安装失败？)"
