# 📰 AI新闻机器人 - 智能新闻推送系统

基于DeepSeek AI的智能新闻推送系统，专注于为团队提供高质量的每日新闻摘要。

🚀 **已验证**: DigitalOcean 服务器 + 企业微信推送 ✅

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

## 🚀 快速部署（DigitalOcean / 任意 Ubuntu 服务器）

### 1) 准备环境
- Ubuntu 22.04（2C2G 即可，DigitalOcean Droplet 已验证）
- 安装依赖：
  ```bash
  apt update && apt upgrade -y
  apt install -y python3 python3-pip python3-venv git
  ```

### 2) 获取代码并安装
```bash
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) 配置环境变量
```bash
cp .env.example .env
nano .env  # 填入 DeepSeek、企业微信 Webhook，可选天行/NewsAPI
```

### 4) 测试运行
```bash
python3 bot_wecom.py
# 看到「✅ 消息发送成功」即完成
```

### 5) 定时任务（示例：每天 9 点）
```bash
echo "0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1" | crontab -
crontab -l
```

> 更详细的发布/回滚流程见 `DEPLOY.md`、`RELEASE.md`，架构解读见 `docs/ARCHITECTURE.md`。

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
├── .env.example          # 环境变量模板
├── README.md             # 项目说明
└── docs/                 # 详细文档
    ├── ARCHITECTURE.md      # 架构与功能总览
    ├── WECOM_GUIDE.md        # 企业微信配置指南
    ├── SCHEDULE_GUIDE.md     # 定时任务配置指南
    └── MIGRATE_TO_DIGITALOCEAN.md # 迁移/部署参考
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
   登录服务器终端执行：
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
- **DigitalOcean 2核2GB**: 约 ¥28-35/月
- **总成本**: 约 ¥29-36/月

---

## 🎓 技术栈

- **Python 3.8+** - 编程语言
- **DeepSeek API** - AI模型
- **天行数据API** - 真实新闻源
- **RSS订阅** - 补充新闻源 (30+ Sources)
- **企业微信Webhook** - 消息推送（支持多群组）

---

## 📚 详细文档

- [架构与功能总览](docs/ARCHITECTURE.md)
- [部署与发布指南](DEPLOY.md)
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

**最后更新**: 2025-12-XX
**部署状态**: ✅ DigitalOcean 服务器运行中
