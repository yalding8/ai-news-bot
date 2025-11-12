# 🚀 部署指南

## 💻 本地运行 (推荐开始)

### 直接运行
```bash
python bot_deepseek.py
```

### 后台运行 (macOS/Linux)
```bash
# 后台启动
nohup python bot_deepseek.py > bot.log 2>&1 &

# 查看日志
tail -f bot.log

# 查看进程
ps aux | grep bot_deepseek

# 停止Bot
pkill -f bot_deepseek.py
```

## ☁️ 云服务器部署

### 1. Railway (免费推荐)

1. 访问 https://railway.app
2. 连接GitHub账号
3. 导入此项目
4. 设置环境变量：
   - `TELEGRAM_TOKEN`
   - `DEEPSEEK_API_KEY` 
   - `CHAT_ID`
5. 自动部署完成

### 2. Render (免费)

1. 访问 https://render.com
2. 连接GitHub
3. 创建Web Service
4. 设置环境变量
5. 部署类型选择 "Background Worker"

### 3. 阿里云ECS

```bash
# 1. 购买ECS服务器 (¥9.9/月)
# 2. 连接服务器
ssh root@your-server-ip

# 3. 安装Python和Git
yum install -y python3 python3-pip git

# 4. 克隆项目
git clone <your-repo-url>
cd ai-news-bot

# 5. 安装依赖
pip3 install -r requirements.txt

# 6. 配置环境变量
cp .env.example .env
vim .env  # 编辑配置

# 7. 后台运行
nohup python3 bot_deepseek.py > bot.log 2>&1 &
```

### 4. 使用systemd (Linux推荐)

创建服务文件：
```bash
sudo vim /etc/systemd/system/newsbot.service
```

内容：
```ini
[Unit]
Description=News Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/ai-news-bot
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile=/path/to/ai-news-bot/.env
ExecStart=/usr/bin/python3 /path/to/ai-news-bot/bot_deepseek.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start newsbot
sudo systemctl enable newsbot
sudo systemctl status newsbot
```

## 🐳 Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot_deepseek.py"]
```

运行：
```bash
docker build -t newsbot .
docker run -d --env-file .env newsbot
```

## 📊 成本对比

| 方案 | 成本 | 稳定性 | 难度 |
|------|------|--------|------|
| 本地运行 | 免费 | ⭐⭐ | ⭐ |
| Railway | 免费 | ⭐⭐⭐⭐ | ⭐⭐ |
| 阿里云ECS | ¥9.9/月 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🔧 故障排除

### Bot无响应
```bash
# 检查进程
ps aux | grep bot_deepseek

# 查看日志
tail -f bot.log

# 重启Bot
pkill -f bot_deepseek.py
python bot_deepseek.py
```

### 内存不足
```bash
# 查看内存使用
free -h

# 添加swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 💡 推荐方案

- **测试阶段**: 本地运行
- **个人使用**: Railway免费部署
- **生产环境**: 阿里云ECS + systemd