# 异乡早咖啡 - AI新闻聚合机器人

基于 DeepSeek AI 的智能新闻推送系统，专为国际教育行业从业者打造每日新闻日报。

## 核心特性

- **AI智能摘要** - DeepSeek V3 大模型总结新闻，自动翻译英文资讯
- **多源聚合去重** - 50+ RSS源 + 天行数据API，自动URL去重
- **智能质量评分** - 5维评分（来源权威性、内容深度、时效性、关键词匹配、独家性）
- **24小时缓存** - 避免重复推送相同新闻
- **企业微信推送** - Markdown格式，支持多群组同时推送
- **字节级截断** - 自动适配企业微信4096字节限制

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot
python3 -m venv venv
source venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```ini
# 必填：DeepSeek API Key
DEEPSEEK_API_KEY=sk-xxxxxxxx

# 必填：企业微信 Webhook（多个用逗号分隔）
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx

# 可选：新闻API
TIANAPI_KEY=xxx
NEWSAPI_KEY=xxx

# 新闻源主题（用于获取新闻，最终合并为一条日报）
ACTIVE_TOPICS=study_abroad,market_data,industry_news
```

### 3. 运行

```bash
python bot_wecom.py
```

## 工作流程

```
1. 并行获取新闻
   ├── RSS源（50+个高质量源）
   ├── 天行数据API
   └── NewsAPI

2. 智能处理
   ├── URL去重（跨主题合并）
   ├── 24小时缓存过滤（避免重复推送）
   ├── 7天时效性过滤
   ├── 负面关键词过滤
   └── 5维质量评分排序

3. AI摘要生成
   ├── 选取Top 9条新闻
   ├── DeepSeek生成5-6条摘要
   └── 自动翻译英文内容

4. 消息发送
   ├── Markdown格式化
   ├── 字节级截断（<4096字节）
   └── 企业微信多群推送
```

## 项目结构

```
ai-news-bot/
├── bot_wecom.py       # 主程序：流程控制、消息发送
├── news_fetcher.py    # 新闻获取：API+RSS、质量评分、去重过滤
├── ai_summarizer.py   # AI摘要：DeepSeek调用
├── news_cache.py      # 缓存管理：24小时去重
├── config.py          # 配置：主题、关键词、RSS源
├── requirements.txt   # Python依赖
├── .env.example       # 环境变量模板
└── .news_cache.json   # 缓存数据（自动生成）
```

## 可用主题

| 主题代码 | 名称 | 说明 |
|---------|------|------|
| `study_abroad` | 留学资讯 | The PIE News、Inside Higher Ed、芥末堆等 |
| `market_data` | 数据趋势 | ICEF Monitor、EdSurge、黑板洞察等 |
| `industry_news` | 行业动态 | 多知网、鲸媒体、TechCrunch Education等 |
| `ai` | AI科技 | VentureBeat、TechCrunch、量子位等 |
| `finance` | 财经新闻 | 虎嗅、36氪、华尔街见闻等 |
| `education` | 教育综合 | Times Higher Education等 |

## 定时任务

```bash
# 编辑crontab
crontab -e

# 每天早9点运行（北京时间）
0 9 * * * cd /path/to/ai-news-bot && ./venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

## 常见问题

### ModuleNotFoundError: No module named 'feedparser'

```bash
python -m pip install feedparser
```

### ModuleNotFoundError: No module named 'requests'

```bash
python -m pip install requests
```

### 已激活 venv 但仍提示缺包

确认安装依赖和运行脚本都使用同一个解释器（venv 里的 `python`）：

```bash
which python
python -m pip install -r requirements.txt
python bot_wecom.py
```

### (venv) python: No module named pip

你的虚拟环境里没有安装 `pip`，先用 `ensurepip` 补上：

```bash
python -m ensurepip --upgrade
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 企业微信推送失败：exceed max length 4096

程序已内置字节级截断，会自动处理。如仍报错，检查是否使用最新代码。

### 推送内容为空

```bash
# 清除缓存重试
rm -f .news_cache.json
python3 bot_wecom.py
```

### 查看日志

```bash
tail -f /var/log/ai-news.log
grep "ERROR" /var/log/ai-news.log
```

## 成本估算

| 项目 | 月费用 |
|------|--------|
| DeepSeek API | ~¥1 |
| 服务器（可选） | ¥28-35 |
| **总计** | **¥29-36/月** |

## 更新日志

### v2.2 (2025-12-19)
- 取消主题分类，合并为统一日报（避免内容重复）
- 新增URL级跨主题去重
- 修复企业微信4096字节限制（按字节截断）
- AI摘要优化：5-6条详细新闻，每条2-3句

### v2.1 (2025-12-16)
- 智能缓存去重系统
- 5维质量评分
- 多样性过滤（单源最多3条）

### v2.0 (2025-11-21)
- 初始版本发布

---

**Powered By 异乡有你** | MIT License
