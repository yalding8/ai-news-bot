# 📰 AI新闻机器人 - 多平台智能推送

基于DeepSeek AI的智能新闻推送系统，支持企业微信、Telegram、邮件多平台推送。

🚀 **已验证**: 阿里云服务器 + 企业微信推送 ✅

---

## ✨ 功能特点

- 🤖 **DeepSeek AI驱动** - 智能搜索和总结，成本低廉（比Claude便宜20倍）
- 📰 **多主题支持** - AI科技、财经、创业、教育、学生公寓等6大主题
- 📱 **多平台推送** - 企业微信、Telegram、邮件任选
- ⏰ **定时推送** - 支持cron定时任务，自动化运行
- ☁️ **云端部署** - 支持阿里云、Railway、Render等多种部署方式
- 💰 **成本极低** - DeepSeek API每月不到1元

---

## 🎯 支持的推送方式

| 推送方式 | 特点 | 适用场景 | 配置难度 |
|---------|------|---------|---------|
| **企业微信** | 即时推送、团队协作 | 公司团队、工作群组 | ⭐☆☆ |
| **Telegram** | 全球可用、交互式 | 个人使用、需要交互 | ⭐☆☆ |
| **邮件** | 正式规范、支持富文本 | 正式通知、存档需求 | ⭐⭐☆ |

---

## 🚀 快速开始

### 方案A: 阿里云服务器部署 (推荐稳定运行) ⭐⭐⭐⭐⭐

**适合**: 24小时稳定运行、学习Linux运维

#### 第一步: 购买服务器

1. 访问 [阿里云轻量应用服务器](https://www.aliyun.com/product/swas)
2. 选择配置:
   - **地域**: 华北2(北京) 或 华东2(上海)
   - **套餐**: 2核2GB - ¥24/月
   - **镜像**: Ubuntu 20.04 LTS 或 22.04 LTS
   - **密码**: 设置root密码(记住!)
3. 购买并记下**公网IP地址**

#### 第二步: 连接服务器

```bash
# macOS/Linux 终端
ssh root@你的服务器IP

# 输入密码(购买时设置的)
```

#### 第三步: 安装环境

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装Python、Git和虚拟环境工具
apt install python3 python3-pip git python3-venv python3-full -y

# 3. 创建项目目录
mkdir -p /opt/apps && cd /opt/apps
```

#### 第四步: 部署代码

**方式1: 从GitHub克隆(推荐)**
```bash
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot
```

**方式2: 本地上传**
```bash
# 在本地Mac终端执行
cd /Users/ningding/ai-news-bot
scp -r . root@你的服务器IP:/opt/apps/ai-news-bot/
```

#### 第五步: 配置环境(重要!)

```bash
cd /opt/apps/ai-news-bot

# 1. 创建虚拟环境(Python 3.12+必需)
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖(使用国内镜像加速)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 配置环境变量
cat > .env << 'EOF'
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
WECOM_WEBHOOK_URL=你的企业微信Webhook_URL
EOF
```

#### 第六步: 测试运行

```bash
# 测试企业微信推送
python3 bot_wecom.py

# 应该看到: ✅ 消息发送成功
# 检查企业微信群是否收到消息
```

#### 第七步: 配置定时任务

```bash
# 1. 配置时区
timedatectl set-timezone Asia/Shanghai

# 2. 编辑crontab
crontab -e
# 第一次选择编辑器,选 1 (nano)

# 3. 添加定时任务(每天早上9点推送)
0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1

# 4. 保存退出: Ctrl+X, Y, Enter

# 5. 验证配置
crontab -l
```

**✅ 部署完成!** 明天早上9点检查企业微信群是否收到推送。

---

### 方案B: Railway云端部署 (推荐快速上线) ⭐⭐⭐⭐⭐

**适合**: 5分钟快速部署、自动化运维

详见: [Railway部署指南](DEPLOY_RAILWAY.md)

---

### 方案C: 本地macOS运行 (推荐测试) ⭐⭐⭐

**适合**: 本地测试、开发调试

```bash
# 1. 克隆项目
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
nano .env  # 填入你的配置

# 4. 测试运行
python3 bot_wecom.py

# 5. 配置本地定时任务
./install_wecom_cron.sh
```

---

## ⚙️ 配置说明

### 1. 获取DeepSeek API Key

1. 访问 https://platform.deepseek.com/
2. 注册账号
3. 创建API Key
4. 充值(建议充值¥10，可用很久)

**成本**: 约¥0.6/月(每天推送1次)

### 2. 获取企业微信Webhook

1. 打开企业微信,进入任意群聊
2. 右上角 `···` → `群机器人` → `添加机器人`
3. 设置名称(如: AI新闻助手)
4. 复制Webhook URL

格式: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx`

详见: [企业微信接入指南](WECOM_GUIDE.md)

### 3. 配置.env文件

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 企业微信配置
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx

# Telegram配置(可选)
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id

# 邮件配置(可选)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your@email.com
EMAIL_TO=recipient@email.com
```

---

## 📋 定时任务配置

### Crontab时间格式

```bash
# 格式: 分 时 日 月 星期 命令
# * * * * * command

# 示例:
0 9 * * *        # 每天早上9点
0 9,18 * * *     # 每天9点和18点
0 9 * * 1-5      # 工作日早上9点
0 */2 * * *      # 每2小时
30 8 * * *       # 每天早上8:30
```

### 常用定时任务

```bash
# 每天早上9点推送AI新闻
0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1

# 工作日早上9点推送
0 9 * * 1-5 cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1

# 每天早晚两次推送
0 9,18 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

---

## 📱 使用说明

### 支持的新闻主题

| 主题代码 | 名称 | 说明 |
|---------|------|------|
| `ai` | 🤖 AI科技 | AI领域最新动态 |
| `finance` | 💰 财经新闻 | 金融市场和经济动态 |
| `startup` | 🚀 创业投资 | 创业公司和投资动态 |
| `education` | 🎓 国际教育 | 国际教育行业动态 |
| `pbsa` | 🏠 学生公寓 | PBSA学生公寓行业动态 |
| `uhomes` | 🏡 异乡好居 | 异乡好居企业动态 |

### 手动推送

```bash
# 企业微信推送
python3 bot_wecom.py

# Telegram推送
python3 start.py

# 邮件推送
python3 bot_email.py
```

---

## 🔧 管理和维护

### 查看日志

```bash
# 实时查看日志
tail -f /var/log/ai-news.log

# 查看最近20条
tail -n 20 /var/log/ai-news.log

# 搜索错误
grep "ERROR\|失败" /var/log/ai-news.log
```

### 更新代码

```bash
cd /opt/apps/ai-news-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
```

### 修改推送时间

```bash
# 编辑crontab
crontab -e

# 修改时间后保存
# Ctrl+X, Y, Enter
```

### 停止定时任务

```bash
# 删除crontab
crontab -r

# 或编辑删除特定任务
crontab -e
```

---

## 🐛 故障排查

### 问题1: ModuleNotFoundError: No module named 'dotenv'

**原因**: Python 3.12+的外部管理环境保护

**解决**:
```bash
# 使用虚拟环境
cd /opt/apps/ai-news-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: 定时任务不执行

**检查**:
```bash
# 1. 查看cron服务
systemctl status cron

# 2. 查看cron日志
grep CRON /var/log/syslog

# 3. 手动测试命令
cd /opt/apps/ai-news-bot
source venv/bin/activate
python3 bot_wecom.py

# 4. 确认时区
timedatectl
```

### 问题3: 企业微信推送失败

**检查**:
```bash
# 1. 验证Webhook URL
curl -X POST 你的Webhook_URL \
  -H 'Content-Type: application/json' \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'

# 2. 查看错误日志
tail -n 50 /var/log/ai-news.log

# 3. 检查网络
ping qyapi.weixin.qq.com
```

### 问题4: pip安装慢

**解决**:
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

---

## 💰 成本说明

### DeepSeek API成本

- **价格**: ¥1/百万tokens (输入) + ¥2/百万tokens (输出)
- **每次推送**: 约2000 tokens
- **每天1次**: ¥0.02/天
- **每月成本**: 约¥0.6/月

### 阿里云服务器成本

- **2核2GB**: ¥24-30/月
- **1核1GB**: ¥15-20/月(够用)

### 总成本

- **阿里云方案**: ¥24-30/月(服务器) + ¥0.6/月(API) = **¥25-31/月**
- **Railway方案**: $0-5/月(免费额度内) + ¥0.6/月(API) = **¥0.6-40/月**
- **本地方案**: ¥0.6/月(API) = **¥0.6/月**

---

## 📚 详细文档

### 部署指南
- [📖 阿里云完整部署指南](DEPLOY_ALIYUN.md) - 30分钟从零到部署
- [🚀 Railway快速部署](DEPLOY_RAILWAY.md) - 5分钟上线
- [☁️ 云部署方案对比](CLOUD_DEPLOY_GUIDE.md) - 全方案对比

### 功能配置
- [📱 企业微信接入指南](WECOM_GUIDE.md) - 零门槛接入
- [⚡ Telegram快速开始](TELEGRAM_QUICKSTART.md) - 3分钟配置
- [📧 邮件推送配置](EMAIL_GUIDE.md) - SMTP配置

### 定时任务
- [⏰ 定时推送完整指南](SCHEDULE_GUIDE.md) - macOS/Linux/Windows
- [⚡ 5分钟快速开始](QUICKSTART_SCHEDULE.md) - 新手推荐

---

## 🎓 技术栈

- **Python 3.8+** - 编程语言
- **DeepSeek API** - AI模型
- **python-dotenv** - 环境变量管理
- **requests** - HTTP请求
- **OpenAI SDK** - API客户端
- **python-telegram-bot** - Telegram集成(可选)

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 开源协议

MIT License

---

## ⭐ 支持项目

如果这个项目对你有帮助，请给个Star！⭐

---

## 📞 联系方式

- 提交Issue: https://github.com/yalding8/ai-news-bot/issues
- 查看文档: [完整文档列表](CLOUD_DEPLOY_GUIDE.md)

---

## 🎉 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的AI能力
- [阿里云](https://www.aliyun.com/) - 稳定的云服务
- [Railway](https://railway.app/) - 简单的云部署平台

---

**最后更新**: 2025-11-14
**部署状态**: ✅ 阿里云服务器运行中
