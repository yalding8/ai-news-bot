#!/usr/bin/env python3
"""
SMTP连接测试脚本
"""
import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

print(f"🔍 测试SMTP连接...")
print(f"📧 服务器: {SMTP_SERVER}:{SMTP_PORT}")
print(f"👤 用户: {SMTP_USER}")
print(f"🔐 密码: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else '未设置'}")
print("=" * 60)

try:
    print("1️⃣ 连接SMTP服务器...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
    print("✅ 连接成功！")

    print("2️⃣ 发送EHLO...")
    server.ehlo()
    print("✅ EHLO成功！")

    print("3️⃣ 启动TLS...")
    server.starttls()
    print("✅ TLS启动成功！")

    print("4️⃣ 登录...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ 登录成功！")

    print("5️⃣ 退出...")
    server.quit()
    print("✅ 退出成功！")

    print("\n" + "=" * 60)
    print("🎉 SMTP配置完全正确！可以发送邮件了！")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    print("\n💡 可能的原因:")
    print("  1. 应用专用密码不正确")
    print("  2. 网络连接问题")
    print("  3. Gmail安全设置问题")
