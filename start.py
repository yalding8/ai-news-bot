#!/usr/bin/env python3
import subprocess
import sys

# 安装依赖
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# 启动bot
import bot_deepseek
bot_deepseek.main()