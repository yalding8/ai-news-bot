# 📰 AI新闻机器人 - 智能新闻推送系统

基于DeepSeek AI的智能新闻推送系统，专注于为团队提供高质量的每日新闻摘要。

🚀 **已验证**: DigitalOcean服务器 + 企业微信推送 ✅

> **开发者必读**：代码更新请查看 [📦 发布流程规范](RELEASE.md) | [🚀 快速开始](QUICKSTART.md)

---

## ✨ 核心特性

- 🤖 **DeepSeek AI驱动** - 智能总结真实新闻，自动翻译英文资讯
- 📰 **多元化新闻源** - 集成天行数据API + 30+个高质量RSS源（Google AI、OpenAI、量子位、机器之心、极客公园等）
- ⚖️ **多样性算法** - 智能去重与多样性过滤，防止单一来源霸屏
- 📱 **企业微信推送** - 支持多个群组同时推送，专为团队协作设计
- ⏰ **自动定时推送** - 支持cron定时任务，24小时自动运行
- 🚀 **一键发布** - 提供 `publish.sh` 脚本，一键推送到GitHub并部署到云服务器
- 🎯 **多主题支持** - AI科技、财经、创业、教育等6大主题

---

## 🚀 快速部署

### 方案A: 阿里云服务器部署 (推荐) ⭐⭐⭐⭐⭐

**适合**: 24小时稳定运行、学习Linux运维

#### 1. 购买服务器
- 访问 [阿里云轻量应用服务器](https://www.aliyun.com/product/swas)
- 配置：2核2GB，Ubuntu 22.04 LTS，¥24/月

#### 2. 部署代码
```bash
# 连接服务器
ssh root@你的服务器IP

# 安装环境
apt update && apt upgrade -y
apt install python3 python3-pip git python3-venv -y

# 克隆项目
cd /opt/apps
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 配置环境变量
```bash
# 创建配置文件
cat > .env << 'EOF'
DEEPSEEK_API_KEY=sk-你的DeepSeek_API_Key
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
TIANAPI_KEY=你的天行数据API_Key
EOF
```

#### 4. 测试运行
```bash
python3 bot_wecom.py
# 应该看到: ✅ 消息发送成功
```

#### 5. 设置定时任务
```bash
# 设置时区
timedatectl set-timezone Asia/Shanghai

# 添加定时任务（每天早上9点）
echo "0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1" | crontab -

# 验证
crontab -l
```

**✅ 部署完成！** 明天早上9点检查企业微信群是否收到推送。

---

### 方案B: 本地macOS运行 (推荐测试) ⭐⭐⭐

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
```

---

## ⚙️ 配置说明

### 1. 获取DeepSeek API Key
1. 访问 https://platform.deepseek.com/
2. 注册账号并创建API Key
3. 充值¥10（可用很久）

**成本**: 约¥0.6/月（每天推送1次）

### 2. 获取企业微信Webhook
1. 企业微信群聊 → 右上角`···` → `群机器人` → `添加机器人`
2. 设置名称并复制Webhook URL

### 3. 获取天行数据API Key（可选）
1. 访问 https://www.tianapi.com/
2. 注册并申请免费API Key
3. 用于获取真实新闻数据

---

## 📋 支持的新闻主题

| 主题代码 | 名称 | 说明 | RSS源数量 |
|---------|------|------|----------|
| `ai` | 🤖 AI科技 | Google AI、OpenAI、量子位、机器之心、极客公园、爱范儿等 | 20+ |
| `finance` | 💰 财经新闻 | 金融市场和经济动态 | 3 |
| `startup` | 🚀 创业投资 | 创业公司和投资动态（含Crunchbase） | 5 |
| `education` | 🎓 国际教育 | 国际教育行业动态（含EdSurge、Chronicle） | 9 |
| `pbsa` | 🏠 学生公寓 | PBSA学生公寓行业动态 | 2 |
| `uhomes` | 🏡 异乡好居 | 异乡好居企业动态 | 2 |

---

## 🔧 项目结构

```
ai-news-bot/
├── bot_wecom.py          # 企业微信推送主程序
├── news_fetcher.py       # 新闻获取模块（API + RSS + 多样性过滤）
├── ai_summarizer.py      # AI总结与翻译模块
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── .env.example         # 环境变量模板
├── README.md            # 项目说明
└── docs/                # 详细文档
    ├── DEPLOY_ALIYUN.md    # 阿里云部署指南
    ├── WECOM_GUIDE.md      # 企业微信配置指南
    └── SCHEDULE_GUIDE.md   # 定时任务配置指南
```

---

## 🔧 管理和维护

### 1. 代码更新与部署

我们提供两种部署方式，请根据实际情况选择：

#### 方案 A: Git 同步部署 (推荐) ⭐⭐⭐
**适用场景**: SSH连接不稳定，或偏好手动控制。

1. **本地推送代码**:
   ```bash
   ./git_push.sh
   ```

2. **服务器端拉取**:
   登录阿里云控制台，在终端执行：
   ```bash
   cd /opt/apps/ai-news-bot
   git pull
   source venv/bin/activate
   pip install -r requirements.txt  # 如果有依赖更新
   python3 bot_wecom.py             # 测试运行
   ```
   > 详细指南请参考: [DEPLOY_GIT.md](DEPLOY_GIT.md)

#### 方案 B: 一键自动发布
**适用场景**: 本地已配置好服务器SSH免密登录。

```bash
# 提交到GitHub + 自动部署到云服务器
bash publish.sh "你的提交信息"
```

### 2. 日志与监控

#### 查看运行日志
```bash
# 实时查看日志
tail -f /var/log/ai-news.log

# 搜索错误信息
grep "ERROR\|失败" /var/log/ai-news.log
```

#### 检查定时任务
```bash
# 查看当前用户的定时任务
crontab -l

# 编辑定时任务
crontab -e
```

---

## 🐛 常见问题

### 问题1: ModuleNotFoundError
**解决**: 使用虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题2: 定时任务不执行
**检查**:
```bash
systemctl status cron
crontab -l
timedatectl  # 确认时区
```

### 问题3: 企业微信推送失败
**检查**:
```bash
# 测试Webhook
curl -X POST 你的Webhook_URL \
  -H 'Content-Type: application/json' \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'
```

---

## 💰 成本说明

### DeepSeek API成本
- **价格**: ¥1/百万tokens (输入) + ¥2/百万tokens (输出)
- **每次推送**: 约2000 tokens
- **每月成本**: 约¥0.6/月

### 服务器成本
- **阿里云2核2GB**: ¥24-30/月
- **总成本**: ¥25-31/月

---

## 🎓 技术栈

- **Python 3.8+** - 编程语言
- **DeepSeek API** - AI模型
- **天行数据API** - 真实新闻源
- **RSS订阅** - 补充新闻源 (30+ Sources)
- **企业微信Webhook** - 消息推送（支持多群组）

---

## 📚 详细文档

- [阿里云部署指南](docs/DEPLOY_ALIYUN.md)
- [企业微信配置指南](docs/WECOM_GUIDE.md)
- [定时任务配置指南](docs/SCHEDULE_GUIDE.md)

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

**最后更新**: 2025-11-23
**部署状态**: ✅ 阿里云服务器运行中
