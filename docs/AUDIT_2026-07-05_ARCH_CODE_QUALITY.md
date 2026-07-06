# AUDIT 2026-07-05 · 架构与代码质量全面评估

> **可信度声明**：本报告由 AI（Claude Code）生成。评审为单一模型的多轮阅读，**不等于真人专家独立交叉审查**；所有评分为 AI 主观判断，最终优先级由项目负责人决定。每个发现项标注核实状态：`[已核实]` = 通过实际命令 / 逐行代码阅读确认，附证据；`[未核实]` = 逻辑推断，未逐行验证；`[AI 估算]` = 未跑命令的数字。

- **日期**：2026-07-05
- **范围**：仓库根 11 个 Python 模块（共 3306 行，`wc -l *.py` 核实）+ tests/ + .github/workflows/ + scripts/ + docs/
- **客观基线**（全部实测）：
  - `ruff check .` → All checks passed `[已核实]`
  - `pytest tests/ -q` → **52 passed**，15.47s `[已核实]`
  - 96 commits，首提交 2025-11-12 `[已核实]`

---

## 一、总体评分

| 维度 | 评分 (10) | 一句话结论 |
|---|---|---|
| 架构设计 | 7.5 | 管线清晰、降级设计出色；但 news_fetcher 是 1094 行神模块，过滤逻辑三层散落 |
| 代码质量 | 7 | lint 全绿、注释承载事故记忆是亮点；存在 1 个已核实的评分逻辑 bug 和成片死代码 |
| 测试 | 5.5 | 52 个测试里 22 个（42%）在测一个不存在脚本的测试脚手架；核心排序/去重管线近乎零覆盖 |
| 运维/CI | 9 | /etc/cron.d + 外部 watchdog + PR-only CI + branch protection，同规模项目里罕见的成熟度 |
| 文档 | 6 | README 新鲜（2026-06-03）；ARCHITECTURE.md 停在 2025-11-30，整个海报/dingning 时代缺失 |
| 安全 | 7.5 | 无硬编码凭证；共享 /tmp 的 pickle 缓存是唯一值得改的点 |

**综合：7 / 10** — 一个演化健康、运维纪律极强的单人项目；主要债务集中在 news_fetcher 的内聚性、三层过滤的关键词漂移、以及"测试数量虚胖"。

---

## 二、架构评估

### 2.1 现状数据流 `[已核实]`（逐行阅读 bot_wecom.py / news_fetcher.py）

```
cron (dingning /etc/cron.d)
  └─ bot_wecom.main()
       ├─ 运行锁 check_run_lock()
       └─ send_daily_news(topics)
            ├─ ①并行 fetch_news(topic)×5      [news_fetcher: TianAPI+RSS+NewsAPI → 去重/时效/评分/多样性]
            ├─ ②filter_new_news (24h 已推送)   [news_cache: .news_cache.json]
            ├─ ③教育相关过滤 + 优先级重排       [bot_wecom 内联]
            ├─ ④全局来源多样性 → top 9
            ├─ ⑤LLM summarize_for_poster       [ai_summarizer: 结构化 JSON, title_en 锚定]
            ├─ ⑥publish_to_dingning (MDX→GitHub API→Vercel)   [dingning_publisher]
            ├─ ⑦海报 build_poster_data → render_png → 企微图片  [image_fetcher og:image 质量门 + poster_generator Playwright]
            ├─ ⑧等 Vercel 部署（扣减海报耗时）→ 企微文本
            └─ ⑨阅读统计报告 → 运维群           [stats_reporter, 永不抛异常]
```

### 2.2 优点

1. **降级设计是全项目最强的一面** `[已核实]`：每个外部依赖都有显式 fallback——LLM 失败→`_fallback_summary`；海报异常不阻断文本（bot_wecom.py:456）；publish 失败→通用 `/coffee` 入口（dingning_publisher.py:149）；统计模块"任何异常只 log 不抛出"（stats_reporter.py:5）。且遵守了"容忍式修复带响计数"（`n_unmatched` 计数，dingning_publisher.py:104）。
2. **外围模块是真正的深模块**：`image_fetcher`（1 个入口 `fetch_article_image`，内部藏 og:image 双序正则 + 三道封面质量门）、`dingning_publisher`（1 个入口，藏 GitHub API sha 协商）、`poster_generator`（`render_png` 一个入口藏 Jinja2+Playwright+2MB JPEG 兜底）。接口小、实现厚，符合 Ousterhout 深模块标准。
3. **注释承载事故记忆**：`load_dotenv(override=True)` 的 2026-06-02 事故注释（config.py:6-8）、企微 markdown 同行多 schema 降级注释（bot_wecom.py:473-474）、title_en 锚定"绝不按位置下标拉链"（bot_wecom.py:242-243）——这些是防回归的真实资产。
4. **运维结构性免疫**：cron 进 `/etc/cron.d`（迁移脚本物理碰不到）、watchdog 跑在 GitHub 上与主机完全独立（watchdog.yml 注释明确补的就是"看门狗与被监控对象同生共死"的洞）、CI 仅 PR 触发 + concurrency 去重 + network 标记隔离外网测试。

### 2.3 问题

#### A1. news_fetcher.py 是 1094 行神模块（严重度：中高）`[已核实]`

单类 `NewsFetcher` 同时拥有：HTTP 会话构建、三种源的抓取器、URL 规范化、canonical id、相似度去重、质量评分、教育相关性模型、信号分级、时间清洗/时效判断、**自带一套 pickle 文件缓存**（/tmp，与 news_cache.json 完全独立的第二套缓存）、来源多样性过滤。全项目 33% 的代码在一个文件里，且是唯一没有对应行为测试的核心文件。理解"一条新闻为什么没进日报"需要在 6 个方法 + 3 张关键词表之间跳。

**建议**：按"抓取（fetchers）/ 排序模型（scoring）/ 去重（dedup）"拆为三个纯函数模块。scoring 与 dedup 都是纯计算（依赖类别 1，最易测试），拆出即可直接补表驱动测试。

#### A2. 过滤/评分逻辑三层散落 + 关键词表漂移（严重度：中高）`[已核实]`

同一个"这条新闻教育相关吗"的判断存在于三处，各用一套关键词表：

| 层 | 位置 | 关键词表 |
|---|---|---|
| 抓取层 | `calculate_news_quality` + `contains_negative_keywords` | config.NEGATIVE_KEYWORDS + **函数内又内联了一份部分重复的 negative_keywords**（news_fetcher.py:484-493） |
| 相关性层 | `_calculate_education_relevance` | 函数内内联 strong/weak/tech_irrelevant 三张表 |
| 日报层 | bot_wecom `filter_education_relevant_news` / `rank_education_news` | config.EDUCATION_RELEVANT_KEYWORDS / EDUCATION_PRIORITY_KEYWORDS |

而 config 里的 `HARD_FILTER_KEYWORDS`（config.py:142）和 `PRIORITY_KEYWORDS`（config.py:189）**没有任何调用点**（grep 全仓库核实）——写了 55 行"Phase 1 关键词库"从未接线。结果是：改一处关键词不会生效于另两层，且没人能说清一条新闻被哪一道门杀掉。

**建议**：关键词表全部收口 config；删除未接线的两张表或真正接线；`calculate_news_quality` 内联 negative_keywords 删除、改引 config.NEGATIVE_KEYWORDS。

#### A3. send_daily_news 160 行编排函数（严重度：中）`[已核实]`

bot_wecom.py:346-503，一个函数做 9 件事（见 2.1 图 ①-⑨），含时间重叠优化（publish 提前、sleep 扣减）这类精巧但只能靠通读理解的控制流。它是全管线唯一的组装点，却没有任何测试——任何一步的回归只能在生产早上 9:10 被发现（好在有 watchdog 兜底"没发出去"，但兜不住"发错了"）。

**建议**：把 ③④ 的过滤重排、⑧ 的等待计算抽成纯函数（可测）；编排骨架保留。

#### A4. 主题（topic）概念的所有权撕裂（严重度：低）`[已核实]`

`NEWS_TOPICS`/`TOPIC_KEYWORDS` 在 config，`rss_feeds`/`tianapi_endpoints` 却硬编码在 NewsFetcher.__init__；bot_wecom 还从 news_fetcher 转口 import `TOPIC_KEYWORDS`（bot_wecom.py:26，实际源头是 config）。新增一个主题要改 2 个文件 4 个 dict。另：`main()` 的兜底 `active_topics = ['ai', 'education']`（bot_wecom.py:576）里 **'ai' 主题已不存在于 NEWS_TOPICS**——触发兜底时会静默空跑一个死主题；已停用的 daily_news.yml 默认值同病。

#### A5. ARCHITECTURE.md 严重过期（严重度：中，修复成本极低）`[已核实]`

`git log` 显示最后改于 **2025-11-30**（bfa3112）。文中描述的还是"多主题分别 AI 总结 + Markdown 消息"的旧架构，完全没有海报、dingning.ai 发布、image_fetcher、stats_reporter、watchdog——这些恰是现在系统的主体。对"快速理解与维护"的自我定位而言，它现在起误导作用。README 反而是新鲜的（2026-06-03，且有未提交的进一步更新）。

---

## 三、代码质量发现

#### C1. 质量评分里 `'the'` 高价值词 bug（严重度：中）`[已核实]`

news_fetcher.py:391：

```python
high_value_keywords = ['visa', 'policy', ..., 'qs', 'the', 'immigration', ...]
for hw in high_value_keywords:
    if hw in title_lower:   # 子串匹配
        score += 5
```

`'the'` 本意是 THE（Times Higher Education 排名），但小写子串匹配会命中**几乎所有英文标题**（the/them/weather/theory…），等于给全部英文新闻无差别 +5；`'qs'` 同理有子串误命中风险。这系统性抬高英文源相对中文源的评分，扭曲排序。修复：改为词边界匹配（`\bthe\b` 仍会大量误命中，应改为 `'times higher education'` / `'THE排名'` 这类无歧义 token）。

#### C2. 死代码成片（严重度：低-中）`[已核实]`（grep 全仓库确认零调用点）

- `bot_wecom.process_topic_news`（bot_wecom.py:163-227，65 行）：旧的"逐主题总结"流程，现行 send_daily_news 不再调用。
- `config.HARD_FILTER_KEYWORDS` / `config.PRIORITY_KEYWORDS`（共 55 行）：见 A2。
- `NEWS_TOPICS` 里 finance/startup/pbsa/uhomes 四主题在默认 ACTIVE_TOPICS 下永不运行，tianapi_endpoints/rss_feeds 为其保留的条目属陪葬配置 `[未核实]`（未确认用户是否偶尔手动启用）。
- 仓库根未跟踪杂物：`6f2ed404abe8e0288e25d6729e597d0a.png` `[已核实]`（git status）。

#### C3. 双 HTTP 重试会话 + 双企微发送循环重复（严重度：低）`[已核实]`

news_fetcher.__init__ 与 bot_wecom 模块级各搭一套一模一样的 `Session+Retry`（news_fetcher.py:27-36 / bot_wecom.py:41-50）；`send_wecom_message` 与 `send_wecom_image` 各写一遍"去重 webhook→POST→errcode 判断"循环（bot_wecom.py:127-160 / 324-343）。抽一个 `_post_to_webhooks(payload)` 即可消除第二处。

#### C4. /tmp 下的 pickle RSS 缓存（严重度：低，安全相关）`[已核实]`

news_fetcher.py:66-70 + 620-652：缓存目录 `tempfile.gettempdir()/ai_news_cache` 以默认权限创建，内容用 `pickle.load` 反序列化。多用户主机上其他本地用户可预植恶意 pickle 文件实现代码执行。当前部署是单人 VPS，风险实际很低，但改成 JSON 序列化 + 项目内目录是零成本消除。另：该缓存只写不清，TTL 只用于读判断，文件会无限累积 `[已核实]`（无删除逻辑）。

#### C5. 运行锁非原子（严重度：低）`[已核实]`

`check_run_lock`（bot_wecom.py:513-545）用 exists→open('w') 两步，存在 TOCTOU 竞态；且锁失败时选择继续运行。单机单 cron 下可接受——但全局规则要求高频任务用 `flock`，此处日频，现状可容忍。服务器 cron 行是否已带 flock 未查证 `[未核实]`。

#### C6. 轻微不一致

- send_daily_news 跨主题去重用裸 `news['url']`（bot_wecom.py:372），而 fetch_news 内部用 `_normalize_url`——同一条带 utm 差异的新闻可跨主题漏去重 `[已核实]`（代码阅读，未构造实例复现）。
- `calculate_news_quality` 注释写"来源可信度（30分）"，实际教育媒体给 35 分；总分可超 100，阈值 `>30` 的语义随通胀漂移 `[已核实]`。
- `SEND_WHEN_NO_NEW` 的实现是"跳过 24h 去重过滤"（bot_wecom.py:385-387），与名字"无新内容也发"语义不完全等价：它会导致重复推昨天内容而非"发一条空日报" `[已核实]`（代码阅读）。

---

## 四、测试评估

**数字（全部实测）**：52 collected / 52 passed；`pytest -m "not network"` 为 CI 口径。

#### T1. 42% 的测试在测不存在的东西（严重度：高，最值得先动手）`[已核实]`

`tests/test_deployment_framework.py`（22 个测试）+ `tests/conftest.py` 里 440 行中的 `DeploymentHelper` 类，服务对象是 `deploy-app.sh`——**该脚本在仓库任何位置都不存在**（`find` 核实，scripts/ 下只有 auto_pull_deploy.sh 等 5 个文件）。这是 .kiro 时代（digitalocean-migration spec）的遗物：22 个测试全部在验证"测试辅助类自己是否工作"，没有一行触达生产代码。它让"52 passed"严重虚胖。

**建议**：整体删除 test_deployment_framework.py + conftest 里的 DeploymentHelper（约 500 行），测试数会掉到 ~30，但那才是真实水位。

#### T2. 覆盖倒挂：最厚的模块测试最少 `[已核实]`（测试名清单核实）

| 模块 | 行数 | 有效测试 | 覆盖的行为 |
|---|---|---|---|
| news_fetcher.py | 1094 | 5 | 仅 format_news_for_ai + 36kr 噪音过滤 |
| bot_wecom.py | 586 | 4 | 仅 parse_active_topics + send_wecom_message |
| image_fetcher.py | 173 | 10 | 封面质量门（覆盖充分，质量好）|
| dingning_publisher.py | 204 | 5 | title_en 对齐（覆盖充分，质量好）|
| news_cache.py | 227 | 0 | — |
| poster_generator.py | 300 | 0 | 仅 __main__ 手动冒烟 |
| stats_reporter.py | 99 | 0 | — |

规律很明显：**近期修过 bug 的地方（封面门、title_en 对齐、日期锚定）测试写得又准又好；从未出过事的核心排序/去重管线零测试**。`calculate_news_quality`、`_calculate_education_relevance`、`classify_signal_level`、`_normalize_url`、`clean_rss_time`、NewsCache 全部是纯计算/本地 IO（依赖类别 1），是性价比最高的补测对象——C1 那个 `'the'` bug 若有一张评分快照表早就被抓住。

---

## 五、安全评估

- ✅ 无硬编码凭证：config.py 全部走 env；.env.example 为占位符；日志只打 webhook 尾 10 位 `[已核实]`。
- ✅ MDX 发布走"轻量索引"降版权风险、token 只存服务器 .env（dingning_publisher 头注释）。
- ⚠️ C4 pickle 缓存（见上）。
- ⚠️ image_fetcher 下载任意 og:image URL 无大小上限（`r.content` 全量入内存落盘，image_fetcher.py:133-135）——恶意/异常源可给一个数 GB 文件。加 `Content-Length` 检查 + 流式写入上限（如 10MB）即可 `[已核实]`（代码确认无上限）。
- ⚠️ requirements 锁 `requests==2.31.0`（2023-05）+ `urllib3<2`：无已知被本项目触发的漏洞路径 `[未核实]`（未逐 CVE 比对），但版本已旧，建议例行升级验证。

---

## 六、行动清单（按性价比排序）

| # | 行动 | 工作量 | 状态 |
|---|---|---|---|
| 1 | 删 test_deployment_framework.py + conftest DeploymentHelper（~500 行僵尸测试） | 30 min | ✅ 已修（2026-07-05，PR: chore/audit-items-1-4；连带删 tests/README.md、hypothesis 依赖、pyproject conftest ignore） |
| 2 | 修 C1：`'the'`/`'qs'` 高价值词改无歧义 token，并为 calculate_news_quality 建评分快照测试 | 1 h | ✅ 已修（同 PR；ASCII 词改词首边界匹配保留复数命中，新增 tests/test_news_scoring.py 9 例含 150.0 整分快照） |
| 3 | 删死代码：process_topic_news、HARD_FILTER_KEYWORDS、PRIORITY_KEYWORDS、内联 negative_keywords 收口 config、main() 兜底去掉 'ai' | 1 h | ✅ 已修（同 PR；含 daily_news.yml 默认主题同步。注意：process_topic_news 删除后 ai_summarizer.summarize_news/_validate_summary/_fallback_summary 链成为孤儿代码，保留待定，见修正记录） |
| 4 | 重写 ARCHITECTURE.md 反映海报/dingning/watchdog 现状（或并入 README 后删除） | 1 h | ✅ 已修（同 PR；重写为模块地图 + 9 步数据流 + 降级矩阵） |
| 5 | 补核心纯函数测试：_normalize_url / clean_rss_time / _calculate_education_relevance / NewsCache | 2-3 h | ✅ 已修（2026-07-06，PR: chore/audit-items-5-8；41 例新测试，先于 #6-#8 落地作安全网） |
| 6 | pickle 缓存改 JSON + 项目内目录 + 过期清理；image_fetcher 加下载大小上限 | 1-2 h | ✅ 已修（同 PR；RSS 缓存 → assets/cache/rss/ JSON + 7 天清理；封面下载 10MB 上限，Content-Length + 流中双闸） |
| 7 | news_fetcher 拆分（fetchers / scoring / dedup 三模块），关键词表全收口 config | 0.5-1 d | ✅ 已修（同 PR；1094 行 → news_fetcher 500 + news_scoring 265 + news_dedup 165；SOURCE_TIERS/RELEVANCE_*/SIGNAL_*/RSS_FEEDS/TIANAPI_ENDPOINTS 全入 config，A2/A4 一并了结；NewsFetcher 留 staticmethod 兼容代理，88 测试零改动全绿，快照 150.0 不变） |
| 8 | send_wecom_message/image 合并发送循环；两套 Session 构建抽公共函数 | 1 h | ✅ 已修（同 PR；http_util.make_retry_session + bot_wecom._post_to_webhooks，image 路径顺带补上非 JSON 响应守卫） |

不建议做的：引入分层框架/抽象仓储/异步化——单次跑完即退出的日频批处理，当前扁平结构与规模匹配，过度工程反而伤可维护性。

---

## 修正记录

- 初稿即终稿，无初筛-核实差异需要记录。所有 `[已核实]` 项均在评估过程中以命令输出或逐行阅读确认，无估算数字被呈现为事实。
- **2026-07-05 执行行动项 1-4 时的补充发现**：删除 `process_topic_news` 后，`ai_summarizer.summarize_news` → `_validate_summary` → `_fallback_summary` 整条链（约 200 行）在仓库内不再有任何调用方 `[已核实]`（grep 确认唯一调用点在被删函数内）。因超出行动项 3 的批准范围未删除，列为候选后续项：若确认不再需要"逐主题文字总结"旧能力，可整链移除。
- **词边界语义权衡**（行动项 2）：严格 `\b词\b` 会丢掉旧子串行为里 `'ranking'`→"rankings"、`'visa'`→"visas" 的复数命中，故采用**词首边界 + 允许后缀**方案（`\b` + 前缀匹配）；代价是 `'policy'` 可命中 "policyholder" 类罕见词，教育新闻语境下可接受。

---

**最终责任人**：项目负责人（AI 报告仅供参考，不构成专业审计意见）
