#!/bin/bash

echo "🔧 设置GitHub仓库..."

# 检查是否已有远程仓库
if git remote get-url origin > /dev/null 2>&1; then
    echo "📝 移除现有远程仓库..."
    git remote remove origin
fi

echo "📋 请按以下步骤操作："
echo ""
echo "1. 访问 https://github.com"
echo "2. 点击右上角 '+' → 'New repository'"
echo "3. 仓库名称：ai-news-bot"
echo "4. 设为 Public"
echo "5. 不要勾选 'Add a README file'"
echo "6. 点击 'Create repository'"
echo ""
echo "创建完成后，运行以下命令："
echo ""
echo "git remote add origin https://github.com/你的用户名/ai-news-bot.git"
echo "git push -u origin main"
echo ""
echo "🎯 然后就可以部署到Railway了！"