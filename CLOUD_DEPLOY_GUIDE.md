# ☁️ AI新闻机器人 - 云部署完整指南

本指南提供3种云部署方案,从简单到复杂,选择最适合您的。

---

## 📊 方案对比

| 方案 | 成本 | 难度 | 配置时间 | 推荐度 |
|------|------|------|---------|--------|
| Railway | $5/月 (有免费额度) | ⭐☆☆☆☆ | 5分钟 | ⭐⭐⭐⭐⭐ |
| Render | 免费 / $7/月 | ⭐☆☆☆☆ | 5分钟 | ⭐⭐⭐⭐⭐ |
| 阿里云/腾讯云 | ¥20-50/月 | ⭐⭐⭐☆☆ | 30分钟 | ⭐⭐⭐☆☆ |
| Serverless函数 | 几乎免费 | ⭐⭐☆☆☆ | 15分钟 | ⭐⭐⭐⭐☆ |

---

## 🚀 方案1: Railway 部署 (强烈推荐)

### 优势
- ✅ 配置超简单,5分钟搞定
- ✅ 自动从GitHub部署
- ✅ 免费额度: $5/月 (够用了)
- ✅ 自动SSL、自动重启
- ✅ 无需管理服务器

### 部署步骤

#### 1. 准备GitHub仓库

```bash
# 如果还没有Git仓库
git init
git add .
git commit -m "Initial commit"

# 创建GitHub仓库并推送
# 在 https://github.com/new 创建新仓库
git remote add origin https://github.com/你的用户名/ai-news-bot.git
git push -u origin main
```

#### 2. 在Railway创建项目

1. 访问 https://railway.app
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择 "Deploy from GitHub repo"
5. 选择您的 `ai-news-bot` 仓库

#### 3. 配置环境变量

在Railway项目设置中添加以下环境变量:

```
DEEPSEEK_API_KEY=sk-192e98a7652b4a829754a3e740f3f0c2
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ad335a27-91dd-4fca-b73e-e1d5b4b11f03
```

#### 4. 配置启动命令

Railway会自动检测,但也可以手动设置:
- **Start Command**: `python3 scheduler.py --check`

#### 5. 部署

点击 "Deploy" 按钮,Railway会自动:
- 安装依赖 (requirements.txt)
- 运行程序
- 24小时保持运行

### 定时任务配置

需要配置 `schedule_config.json` 来定义推送时间:

```json
{
  "schedules": [
    {
      "name": "早间AI新闻",
      "enabled": true,
      "time": "09:00",
      "topics": ["ai"],
      "description": "每天早上9点推送AI新闻"
    }
  ]
}
```

然后重新部署即可。

---

## 🎨 方案2: Render 部署 (免费)

### 优势
- ✅ 完全免费 (有限制)
- ✅ 配置简单
- ✅ 自动从GitHub部署
- ❌ 免费版15分钟无活动会休眠

### 部署步骤

#### 1. 准备GitHub仓库 (同Railway)

#### 2. 在Render创建服务

1. 访问 https://render.com
2. 注册/登录
3. 点击 "New +" → "Background Worker"
4. 连接GitHub仓库

#### 3. 配置服务

- **Name**: ai-news-bot
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 scheduler.py --check`

#### 4. 添加环境变量

```
DEEPSEEK_API_KEY=你的API密钥
WECOM_WEBHOOK_URL=你的企业微信Webhook
```

#### 5. 创建并部署

点击 "Create Background Worker",自动部署!

### 注意事项

免费版会在15分钟无活动后休眠,需要定期ping:
- 使用 UptimeRobot 等服务定期访问
- 或升级到付费版 ($7/月)

---

## 🖥️ 方案3: 传统云服务器 (阿里云/腾讯云)

### 优势
- ✅ 完全控制
- ✅ 可运行其他服务
- ✅ 稳定可靠
- ❌ 需要自己管理服务器

### 推荐配置

- CPU: 1核
- 内存: 1GB
- 系统: Ubuntu 20.04
- 成本: ¥20-30/月

### 部署步骤

#### 1. 购买云服务器

**阿里云轻量应用服务器**:
1. 访问 https://www.aliyun.com/product/swas
2. 选择: 1核1GB, Ubuntu 20.04
3. 约24元/月

**腾讯云轻量应用服务器**:
1. 访问 https://cloud.tencent.com/product/lighthouse
2. 选择: 1核1GB, Ubuntu 20.04
3. 约25元/月

#### 2. 连接服务器

```bash
# 使用SSH连接
ssh root@你的服务器IP
```

#### 3. 安装依赖

```bash
# 更新系统
apt update && apt upgrade -y

# 安装Python和Git
apt install python3 python3-pip git -y

# 安装系统依赖
apt install python3-venv -y
```

#### 4. 部署项目

```bash
# 克隆代码
cd /opt
git clone https://github.com/你的用户名/ai-news-bot.git
cd ai-news-bot

# 安装Python依赖
pip3 install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
# 填入你的配置
```

#### 5. 配置定时任务

```bash
# 编辑crontab
crontab -e

# 添加定时任务 (每天早上9点)
0 9 * * * cd /opt/ai-news-bot && python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

#### 6. 配置开机自启 (可选)

创建systemd服务:

```bash
nano /etc/systemd/system/ai-news-scheduler.service
```

内容:

```ini
[Unit]
Description=AI News Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-news-bot
ExecStart=/usr/bin/python3 scheduler.py --check
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
systemctl daemon-reload
systemctl enable ai-news-scheduler
systemctl start ai-news-scheduler
systemctl status ai-news-scheduler
```

---

## ⚡ 方案4: Serverless 函数 (成本最低)

### 优势
- ✅ 几乎免费 (按调用次数计费)
- ✅ 无需管理服务器
- ✅ 自动扩展
- ❌ 需要一些配置

### 阿里云函数计算 (FC)

#### 1. 开通函数计算

访问 https://fc.console.aliyun.com/

#### 2. 创建函数

- 运行环境: Python 3.9
- 触发器: 定时触发器 (Cron: 0 9 * * *)
- 内存: 512MB
- 超时时间: 60秒

#### 3. 上传代码

```bash
# 打包代码
zip -r ai-news-bot.zip . -x "*.git*" -x "*__pycache__*"

# 在控制台上传zip包
```

#### 4. 配置环境变量

在函数配置中添加:
- DEEPSEEK_API_KEY
- WECOM_WEBHOOK_URL

#### 5. 创建入口函数

创建 `index.py`:

```python
import os
from bot_wecom import send_daily_news

def handler(event, context):
    """阿里云函数计算入口"""
    try:
        send_daily_news(['ai'])
        return {
            'statusCode': 200,
            'body': '推送成功'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'推送失败: {str(e)}'
        }
```

### 腾讯云云函数 (SCF)

类似步骤,访问 https://console.cloud.tencent.com/scf

---

## 💡 推荐选择

### 如果您是新手 → Railway / Render
- 5分钟搞定
- 不用管服务器
- 成本可控

### 如果追求免费 → Render免费版 + UptimeRobot
- 完全免费
- 需要配置定期ping

### 如果需要稳定 → 阿里云/腾讯云
- 完全掌控
- 适合长期运行

### 如果成本敏感 → Serverless函数
- 按调用付费
- 几乎免费 (每月几毛钱)

---

## 🔧 部署后的管理

### 查看日志

**Railway/Render**:
- 在Web控制台查看实时日志

**云服务器**:
```bash
tail -f /var/log/ai-news.log
```

**Serverless**:
- 在云平台控制台查看函数日志

### 更新代码

**Railway/Render**:
- Push到GitHub,自动重新部署

**云服务器**:
```bash
cd /opt/ai-news-bot
git pull
systemctl restart ai-news-scheduler
```

**Serverless**:
- 重新上传zip包

### 修改推送时间

编辑 `schedule_config.json` 后:
- Railway/Render: Git push自动部署
- 云服务器: 重启服务
- Serverless: 修改触发器配置

---

## 📚 相关文档

- [定时推送配置指南](SCHEDULE_GUIDE.md)
- [企业微信接入指南](WECOM_GUIDE.md)
- [README](README.md)

---

## ❓ 常见问题

### Q: 哪个方案最推荐?

A: 新手推荐 **Railway**,简单、稳定、便宜。

### Q: 需要一直运行吗?

A: 不需要。使用定时任务方式,只在需要推送时运行。

### Q: 成本大概多少?

A:
- Railway: 每月$5,免费额度够用
- Render: 免费
- 云服务器: ¥20-30/月
- Serverless: 几乎免费

### Q: 如何监控是否正常推送?

A:
- 查看企业微信群是否收到消息
- 查看日志
- 配置告警通知

---

⭐ 推荐从 Railway 开始,最简单!

有问题随时提Issue!
