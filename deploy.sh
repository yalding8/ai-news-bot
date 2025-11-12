#!/bin/bash

echo "🚀 准备部署到Railway..."

# 检查Git状态
if [ ! -d ".git" ]; then
    echo "📝 初始化Git仓库..."
    git init
fi

# 添加所有文件
echo "📦 添加文件到Git..."
git add .

# 提交更改
echo "💾 提交更改..."
git commit -m "Deploy to Railway: $(date)"

# 检查是否有远程仓库
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ 请先设置GitHub远程仓库："
    echo "   git remote add origin https://github.com/你的用户名/ai-news-bot.git"
    exit 1
fi

# 推送到GitHub
echo "🌐 推送到GitHub..."
git push origin main

echo "✅ 代码已推送到GitHub！"
echo ""
echo "📋 下一步："
echo "1. 访问 https://railway.app"
echo "2. 登录GitHub账号"
echo "3. 选择 'Deploy from GitHub repo'"
echo "4. 选择你的 ai-news-bot 仓库"
echo "5. 添加环境变量："
echo "   - TELEGRAM_TOKEN"
echo "   - DEEPSEEK_API_KEY"
echo "   - CHAT_ID"
echo "6. 等待部署完成"
echo ""
echo "🎉 部署完成后Bot将24/7运行！"