# 📰 AI新闻机器人 - 智能新闻推送系统

基于DeepSeek AI的智能新闻推送系统，专注于为团队提供高质量的每日新闻摘要。

🚀 **已验证**: DigitalOcean 服务器 + 企业微信推送 ✅

> **开发者必读**：代码更新请查看 [📦 发布流程规范](RELEASE.md) | [🚀 快速开始](QUICKSTART.md)

---

## ✨ 核心特性

- 🤖 **DeepSeek AI驱动** - 智能总结真实新闻，自动翻译英文资讯
- 📰 **多元化新闻源** - 集成天行数据API + 50+个高质量RSS源（Inside Higher Ed、VentureBeat、TechCrunch等）
- ⚖️ **智能去重系统** - 24小时缓存去重 + 相似度过滤，避免重复推送
- 🎯 **多样性算法** - 单源最多2条，防止单一来源霸屏
- 📊 **5维质量评分** - 来源权威性、内容深度、时效性、关键词匹配、独家性
- 📱 **企业微信推送** - 支持多个群组同时推送，专为团队协作设计
- ⏰ **自动定时推送** - 支持cron定时任务，24小时自动运行
- 🎯 **多主题支持** - AI科技、财经、创业、教育等6大主题

---

## 🚀 快速部署（DigitalOcean / 任意 Ubuntu 服务器）

### 🤖 异乡早咖啡 (AI News Bot)

> **Powered By 异乡有你，AI 驱动 • 实时聚合全球国际教育行业资讯**

这是一个基于 Python 的自动化新闻聚合机器人，专为国际教育从业者打造。它每天定时从全球各大权威媒体抓取最新资讯，利用 DeepSeek V3 大模型进行智能摘要，并通过企业微信（WeCom）推送“异乡早咖啡”日报。

## ✨ 主要功能

*   **多源聚合**: 整合了 **RSS 订阅** (Inside Higher Ed, The PIE News, 芥末堆, 多知网, 鲸媒体等) 和 **新闻 API** (TianAPI, NewsAPI)。
*   **智能摘要**: 使用 DeepSeek LLM 对长篇新闻进行精准总结，提取关键信息。
*   **四大板块**:
    1.  **📊 数据趋势 (Market Data)**: 留学市场宏观数据、行业报告。
    2.  **🏢 行业动态 (Industry News)**: 教育机构融资、并购、战略合作（含竞品动态）。
    3.  **📜 教育政策 (Edu Policy)**: 各国签证、移民及教育新政。
    4.  **✈️ 留学资讯 (Study Abroad)**: 院校动态、招生信息等。
*   **智能去重**: 自动过滤重复内容，同时允许重要新闻在不同维度（如既是政策又是市场影响）进行展示。
*   **美观推送**: 生成格式优美的 Markdown 日报，包含 Emoji 图标、精选来源链接及底部小程序快捷入口。

## 🛠 技术栈

*   **语言**: Python 3.10+
*   **AI 模型**: DeepSeek V3
*   **数据源**:
    *   `feedparser`: 处理 RSS/Atom 订阅源
    *   `requests`: 处理 API 请求
    *   **RSSHub**: 辅助抓取多知网、鲸媒体等无原生 RSS 的站点
*   **通知渠道**: 企业微信 Webhook (Markdown 格式)
*   **部署**: DigitalOcean (Ubuntu) + Crontab 定时任务

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入以下信息：

```ini
# DeepSeek API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 企业微信 Webhook (支持多个，逗号分隔)
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx

# 可选：天行数据/NewsAPI Key
TIANAPI_KEY=xxx
NEWSAPI_KEY=xxx

# 激活的主题板块（可用: ai, finance, startup, education, pbsa, uhomes）
ACTIVE_TOPICS=education,ai
```

### 3. 运行测试

```bash
# 手动运行一次日报生成
python3 bot_wecom.py
```

## 📅 自动化部署

本项目通过 `crontab` 在服务器上每日定时运行。

**部署步骤**:
1.  将代码推送到 GitHub。
2.  在服务器拉取最新代码。
3.  确保 `.env` 配置正确。
4.  设置 Cron 任务（北京时间每天早 9:00）：

```bash
# 编辑 crontab
crontab -e

# 添加如下行 (服务器已设置为 CST/北京时间)
0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

## 📂 目录结构

*   `bot_wecom.py`: 主程序入口，负责流程控制和消息发送。
*   `news_fetcher.py`: 新闻抓取核心逻辑 (RSS/API)。
*   `ai_summarizer.py`: AI 摘要生成模块。
*   `config.py`: 项目配置（主题定义、RSS源列表、关键词）。
*   `requirements.txt`: Python 依赖。

## 📝 维护指南

*   **添加新源**: 修改 `config.py` 中的 `rss_feeds` 字典。
*   **调整关键词**: 修改 `config.py` 中的 `TOPIC_KEYWORDS`。
*   **更新广告**: 修改 `bot_wecom.py` 底部的广告文字和小程序链接。

---
© 2025 异乡好居 | 内部工具

## 📋 支持的新闻主题

| 主题代码 | 名称 | 说明 | RSS源数量 |
|---------|------|------|----------|
| `ai` | 🤖 AI科技 | VentureBeat、TechCrunch、The Verge、IT之家、虎嗅等 | 8 |
| `finance` | 💰 财经新闻 | 金融市场和经济动态 | 3 |
| `startup` | 🚀 创业投资 | 创业公司和投资动态 | 3 |
| `education` | 🎓 国际教育 | Inside Higher Ed、EdSurge、The PIE News、芥末堆等 | 7 |
| `pbsa` | 🏠 学生公寓 | PBSA学生公寓行业动态 | 2 |
| `uhomes` | 🏡 异乡好居 | 异乡好居企业动态 | 2 |

---

## 🔧 项目结构

```
ai-news-bot/
├── bot_wecom.py          # 企业微信推送主程序
├── news_fetcher.py       # 新闻获取模块（API + RSS + 多样性过滤）
├── news_cache.py         # 智能缓存去重系统
├── ai_summarizer.py      # AI总结与翻译模块
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量模板
├── .news_cache.json      # 新闻缓存数据（自动生成）
├── README.md             # 项目说明
├── OPTIMIZATION_TODO.md  # 优化方案TODO
├── diagnose_news.py      # 新闻获取诊断脚本
└── docs/                 # 详细文档
    ├── WECOM_GUIDE.md        # 企业微信配置指南
    ├── SCHEDULE_GUIDE.md     # 定时任务配置指南
    ├── EDUCATION_NEWS_FIX.md # 教育新闻修复报告
    └── AI_NEWS_OPTIMIZATION.md # AI新闻优化报告
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

### 问题4: 推送内容为空
**原因**: 主题配置错误或新闻被缓存过滤

**解决**:
```bash
# 1. 检查主题配置
cat .env | grep ACTIVE_TOPICS
# 应该是: ACTIVE_TOPICS=education,ai
# 不是: ACTIVE_TOPICS=study_abroad,edu_market,competitors

# 2. 清除缓存
rm -f .news_cache.json

# 3. 运行诊断脚本
python3 diagnose_news.py

# 4. 重新测试
python3 bot_wecom.py
```

**可用主题**:
- `ai` - AI科技
- `finance` - 财经新闻
- `startup` - 创业投资
- `education` - 国际教育
- `pbsa` - 学生公寓
- `uhomes` - 异乡好居

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

**最后更新**: 2025-12-16
**版本**: v2.1 - 智能去重优化版
**部署状态**: ✅ 阿里云服务器运行中

---

## 🆕 更新日志

### v2.1 (2025-12-16)
- ✅ 新增智能缓存去重系统，避免24小时内重复推送
- ✅ 扩展AI新闻源至8个，增加国际权威媒体
- ✅ 扩展教育新闻源至7个，覆盖国际教育媒体
- ✅ 实现多样性过滤，单源最多2条
- ✅ 新增5维质量评分系统
- ✅ 添加时间过滤，只推送7天内新闻
- ✅ 新增诊断脚本，方便故障排查

### v2.0 (2025-11-21)
- ✅ 初始版本发布
