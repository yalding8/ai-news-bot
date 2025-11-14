#!/usr/bin/env python3
"""
发送测试邮件（不调用AI API）
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')

print("📧 准备发送测试邮件...")
print(f"从: {EMAIL_FROM}")
print(f"到: {EMAIL_TO}")
print("=" * 60)

# 创建HTML邮件
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 32px;">🎉 测试成功！</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
            </p>
        </div>

        <!-- Content -->
        <div style="padding: 40px;">
            <h2 style="color: #333; margin-top: 0;">✅ 邮件推送配置成功！</h2>
            <p style="color: #666; line-height: 1.8; font-size: 16px;">
                恭喜！你的AI新闻邮件推送系统已经配置成功。
            </p>

            <div style="background-color: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #333;"><strong>📧 发件人:</strong> {EMAIL_FROM}</p>
                <p style="margin: 10px 0 0 0; color: #333;"><strong>📥 收件人:</strong> {EMAIL_TO}</p>
                <p style="margin: 10px 0 0 0; color: #333;"><strong>🔧 SMTP:</strong> {SMTP_SERVER}:{SMTP_PORT}</p>
            </div>

            <h3 style="color: #667eea; margin-top: 30px;">🚀 下一步可以做什么？</h3>
            <ul style="color: #666; line-height: 1.8;">
                <li>运行 <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python3 bot_email.py</code> 发送真实的AI新闻</li>
                <li>配置定时任务，每天自动推送</li>
                <li>自定义邮件模板和主题</li>
                <li>添加更多收件人</li>
            </ul>
        </div>

        <!-- Footer -->
        <div style="background-color: #f9f9f9; padding: 20px; text-align: center; color: #999; font-size: 14px; border-top: 1px solid #eee;">
            <p style="margin: 0;">🤖 AI News Bot 测试邮件</p>
            <p style="margin: 10px 0 0 0; font-size: 12px;">
                Powered by DeepSeek AI | 2025
            </p>
        </div>
    </div>
</body>
</html>
"""

try:
    # 创建邮件
    message = MIMEMultipart('alternative')
    message['From'] = Header(f"AI新闻助手 <{EMAIL_FROM}>", 'utf-8')
    message['To'] = Header(EMAIL_TO, 'utf-8')
    message['Subject'] = Header("🎉 测试成功！AI新闻邮件推送系统配置完成", 'utf-8')

    # 添加HTML内容
    html_part = MIMEText(html_content, 'html', 'utf-8')
    message.attach(html_part)

    # 连接并发送
    print("📡 连接SMTP服务器...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)

    print("📤 发送邮件...")
    server.sendmail(EMAIL_FROM, EMAIL_TO, message.as_string())
    server.quit()

    print("=" * 60)
    print("✅ 邮件发送成功！")
    print(f"📥 请查看 {EMAIL_TO} 的收件箱")
    print("=" * 60)
    print("\n💡 下一步：")
    print("  运行 python3 bot_email.py 发送真实的AI新闻")

except Exception as e:
    print(f"❌ 发送失败: {e}")
