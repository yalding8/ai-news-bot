#!/bin/bash
# 云服务器自动更新脚本

echo "开始更新AI新闻机器人..."

cd /opt/apps/ai-news-bot

# 备份配置
cp .env .env.backup
cp run_news_bot.sh run_news_bot.sh.backup 2>/dev/null || true

# 拉取最新代码
git pull origin main

# 恢复配置
cp .env.backup .env
cp run_news_bot.sh.backup run_news_bot.sh 2>/dev/null || true

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 测试运行
echo "测试运行..."
python3 bot_wecom.py

echo "更新完成！"