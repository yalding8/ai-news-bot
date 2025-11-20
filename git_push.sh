#!/bin/bash
# 快速提交代码到GitHub脚本

set -e

echo "🚀 准备提交代码到GitHub..."

# 1. 添加所有文件
git add .

# 2. 提交
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
git commit -m "feat: update for deployment $TIMESTAMP"

# 3. 推送
echo "📤 推送到远程仓库..."
git push origin main

echo "✅ 代码已推送到GitHub！"
echo "现在请在阿里云控制台执行以下命令进行部署："
echo ""
echo "cd /opt/apps/ai-news-bot"
echo "git pull"
echo "source venv/bin/activate"
echo "pip install -r requirements.txt"
echo "python3 bot_wecom.py"
