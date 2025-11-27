# 📚 国际教育服务机构 - 新闻推送配置指南

> 5分钟快速配置，开始接收专业的留学行业资讯

---

## 🎯 可用的新闻主题

### 国际教育服务专业主题（新增）

| 主题代码 | 名称 | 覆盖内容 | 适合人群 |
|---------|------|---------|---------|
| `study_abroad` | ✈️ 留学资讯 | 留学政策、签证、院校动态 | 顾问、运营 |
| `edu_policy` | 📜 教育政策 | 各国政策、签证更新 | 管理层、顾问 |
| `uni_rankings` | 🏆 院校排名 | 大学排名、院校评估 | 顾问、市场 |
| `edu_market` | 📊 教育市场 | 市场数据、行业趋势 | 管理层、市场 |
| `competitors` | 🔍 行业动态 | 竞品动态、融资并购 | 管理层、市场 |

### 其他主题（原有）

| 主题代码 | 名称 | 说明 |
|---------|------|------|
| `ai` | 🤖 AI科技 | AI技术在教育中的应用 |
| `education` | 🎓 教育综合 | 教育科技与综合资讯 |
| `pbsa` | 🏠 学生公寓 | 学生住宿行业动态 |

---

## ⚙️ 配置方法

### 方式1：使用环境变量配置（推荐）

编辑 `.env` 文件：

```bash
# 在 .env 文件中设置启用的主题
ACTIVE_TOPICS=study_abroad,edu_policy,uni_rankings,edu_market,competitors
```

**常用配置组合**：

```bash
# 配置1：管理层版本（市场+竞品）
ACTIVE_TOPICS=edu_market,competitors,uni_rankings

# 配置2：运营团队版本（留学+政策）
ACTIVE_TOPICS=study_abroad,edu_policy,uni_rankings

# 配置3：全面版本（所有教育相关）
ACTIVE_TOPICS=study_abroad,edu_policy,uni_rankings,edu_market,competitors

# 配置4：混合版本（教育+AI科技）
ACTIVE_TOPICS=study_abroad,edu_market,ai
```

### 方式2：直接修改代码

编辑 `config.py` 文件：

```python
# 修改默认启用主题
ACTIVE_TOPICS_ENV = os.getenv('ACTIVE_TOPICS', 'study_abroad,edu_market')
```

---

## 📅 推送策略建议

### 策略1：单次推送（当前默认）

```bash
# 默认配置：每天早上9点推送所有主题
# 修改 crontab 时间即可调整
```

**优点**：配置简单
**缺点**：信息较多，可能导致信息过载

### 策略2：分类推送（推荐）

创建多个推送任务，按主题分时段推送：

```bash
# 方案A：早中晚三次推送
09:00 - 留学资讯 + 教育政策（ACTIVE_TOPICS=study_abroad,edu_policy）
12:00 - 市场动态 + 竞品信息（ACTIVE_TOPICS=edu_market,competitors）
18:00 - 院校排名更新（ACTIVE_TOPICS=uni_rankings）
```

实施方法：
1. 复制 `bot_wecom.py` 为 `bot_morning.py`、`bot_noon.py`、`bot_evening.py`
2. 在每个文件中硬编码不同的主题列表
3. 设置3个cron任务

### 策略3：角色定制（企业级）

为不同角色创建不同的企业微信群和推送配置：

```bash
# 管理层群（战略决策）
WECOM_WEBHOOK_URL_MANAGEMENT=xxx
ACTIVE_TOPICS=edu_market,competitors,uni_rankings

# 运营团队群（业务支持）
WECOM_WEBHOOK_URL_OPERATIONS=xxx
ACTIVE_TOPICS=study_abroad,edu_policy

# 市场团队群（市场洞察）
WECOM_WEBHOOK_URL_MARKETING=xxx
ACTIVE_TOPICS=competitors,edu_market,uni_rankings
```

---

## 🔍 新闻源说明

### 留学资讯 (study_abroad)

**RSS源**：
- The PIE News - 留学行业权威媒体
- Study International - 全球留学资讯
- QS TopUniversities - 留学申请指导
- NAFSA - 美国国际教育官方
- 芥末堆、黑板洞察 - 中文教育媒体

**关键词**：留学、出国、签证、F-1、Tier 4、各国留学政策

### 教育政策 (edu_policy)

**RSS源**：
- NAFSA - 美国国际教育政策
- The PIE News - 政策深度报道
- Study International - 政策更新
- 芥末堆 - 中国教育政策

**关键词**：留学政策、签证政策、OPT、CPT、PSW、移民政策

### 院校排名 (uni_rankings)

**RSS源**：
- QS World Rankings - QS世界大学排名
- Times Higher Education - 泰晤士高等教育
- University World News - 院校动态

**关键词**：QS排名、THE排名、大学排名、专业排名、商学院排名

### 教育市场 (edu_market)

**RSS源**：
- ICEF Monitor - 留学市场数据权威
- The PIE News - 市场趋势分析
- EdSurge - 教育科技市场
- 芥末堆、黑板洞察 - 中文市场分析

**关键词**：留学市场、市场报告、招生数据、留学趋势、国际学生数量

### 行业动态 (competitors)

**RSS源**：
- Crunchbase News - 融资并购信息
- TechCrunch Education - 教育科技动态
- 36氪 - 中国教育投资
- EdSurge - 行业新闻

**关键词**：新东方、启德、IDP、融资、并购、上市、教育投资

---

## 🧪 测试配置

### 1. 测试单个主题

```bash
# 临时设置环境变量测试
ACTIVE_TOPICS=study_abroad python3 bot_wecom.py
```

### 2. 查看获取到的新闻

```bash
# 运行程序，查看日志输出
python3 bot_wecom.py

# 预期输出示例：
# 📡 正在获取留学资讯...
#   └─ 从所有新闻源获取真实新闻（API + RSS）...
#   └─ 获取到 5 条真实新闻
# ✅ 留学资讯 获取成功
```

### 3. 测试所有新主题

```bash
# 测试所有教育相关主题
ACTIVE_TOPICS=study_abroad,edu_policy,uni_rankings,edu_market,competitors python3 bot_wecom.py
```

---

## ❓ 常见问题

### Q1: 某个RSS源无法访问怎么办？

**答**：部分国外RSS源可能需要代理访问。系统会自动跳过无法访问的源，使用其他可用源。

### Q2: 新闻数量太多/太少？

**答**：调整主题数量或修改 `bot_wecom.py` 中的 `num=15` 参数：

```python
# 在 bot_wecom.py 第142行
all_news = news_fetcher.fetch_news(topic_key, keywords, num=15)  # 调整这个数字
```

### Q3: 想只关注特定国家的留学资讯？

**答**：修改 `config.py` 中的关键词，只保留相关国家：

```python
'study_abroad': [
    '美国留学', '英国留学',  # 只关注美英
    'F-1 visa', 'Tier 4 visa',
]
```

### Q4: 想添加公司竞品监控？

**答**：在 `config.py` 的 `competitors` 关键词中添加公司名：

```python
'competitors': [
    # 在这里添加你的竞品公司名
    '公司A', '公司B', '公司C',
    # ... 其他关键词
]
```

---

## 📊 效果评估

运行1-2周后，评估以下指标：

- [ ] **新闻相关性**：推送的新闻是否与业务相关？目标 >80%
- [ ] **信息及时性**：是否及时获取到重要政策变化？
- [ ] **内容质量**：AI总结是否准确、有价值？
- [ ] **阅读体验**：信息量是否合适？不多不少

根据评估结果调整：
- 如果不相关新闻多 → 优化关键词
- 如果信息过载 → 减少主题数量或分时段推送
- 如果错过重要新闻 → 添加更多RSS源

---

## 🔄 持续优化

### 每月review：
1. 检查RSS源是否仍然有效
2. 根据业务变化调整关键词
3. 收集团队反馈，优化主题配置

### 建议优化：
- 添加新发现的高质量RSS源
- 移除低质量或失效的RSS源
- 根据季节性调整关键词（如招生季）

---

## 📞 获取支持

遇到问题？查看：
- [EDUCATION_OPTIMIZATION.md](EDUCATION_OPTIMIZATION.md) - 完整优化方案
- [RELEASE.md](RELEASE.md) - 发布和部署流程

---

**创建时间**: 2025-11-27
**适用版本**: v2.0+（新增教育主题）
**推荐配置**: study_abroad + edu_market + competitors
