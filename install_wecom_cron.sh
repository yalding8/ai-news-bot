#!/bin/bash
# 安装AI新闻企业微信推送的定时任务

echo "⏰ 配置企业微信定时推送..."
echo ""

# 完整的crontab命令
CRON_CMD='0 9 * * * /Users/ningding/.pyenv/shims/python3 /Users/ningding/ai-news-bot/bot_wecom.py >> /Users/ningding/ai-news-bot/wecom_cron.log 2>&1'

# 安装到crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ 定时任务配置完成！"
echo ""
echo "📋 已配置的定时任务："
crontab -l
echo ""
echo "📱 每天上午9点自动发送AI新闻到企业微信群"
echo ""
echo "💡 提示："
echo "  - 查看日志：tail -f /Users/ningding/ai-news-bot/wecom_cron.log"
echo "  - 手动测试：python3 bot_wecom.py"
echo "  - 查看任务：crontab -l"
echo "  - 停止推送：crontab -r"
echo "  - 编辑时间：crontab -e"
echo ""
echo "⏰ Crontab时间格式："
echo "  0 9 * * *  → 每天早上9点"
echo "  0 9,18 * * *  → 每天9点和18点"
echo "  0 9 * * 1-5  → 工作日早上9点"
