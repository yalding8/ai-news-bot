#!/usr/bin/env python3
"""
AI日报Bot启动脚本
"""

import os
import sys
from dotenv import load_dotenv

def check_config():
    """检查配置"""
    load_dotenv()
    
    required = ['TELEGRAM_TOKEN', 'DEEPSEEK_API_KEY', 'CHAT_ID']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("❌ 缺少环境变量:")
        for var in missing:
            print(f"   {var}")
        print("\n请编辑 .env 文件配置")
        return False
    
    print("✅ 配置检查通过")
    return True

def main():
    """主函数"""
    print("🤖 AI日报Bot")
    
    if not check_config():
        sys.exit(1)
    
    try:
        from bot_deepseek import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Bot已停止")

if __name__ == '__main__':
    main()