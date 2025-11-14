#!/bin/bash
# 安装AI新闻邮件推送的定时任务

echo "⏰ 配置定时邮件推送..."
echo ""

# 完整的crontab命令（包含cd到正确目录）
CRON_CMD='0 9 * * * /Users/ningding/.pyenv/shims/python3 /Users/ningding/ai-news-bot/bot_email.py >> /Users/ningding/ai-news-bot/email_cron.log 2>&1'

# 安装到crontab
echo "$CRON_CMD" | crontab -

echo "✅ 定时任务配置完成！"
echo ""
echo "📋 已配置的定时任务："
crontab -l
echo ""
echo "📧 每天上午9点自动发送所有主题的AI新闻到："
echo "   eduagent@uhomes.com"
echo ""
echo "💡 提示："
echo "  - 查看日志：tail -f /Users/ningding/ai-news-bot/email_cron.log"
echo "  - 手动测试：cd /Users/ningding/ai-news-bot && python3 bot_email.py"
echo "  - 修改时间：crontab -e"
echo "  - 停止推送：crontab -r"
