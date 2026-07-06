# 🧭 架构与功能总览

> 最后更新：2026-07-05（对齐海报 / dingning.ai / watchdog 现状；上一版停留在 2025-11 的"多主题分别总结"旧架构）。
> 配套评估见 `docs/AUDIT_2026-07-05_ARCH_CODE_QUALITY.md`。

「异乡早咖啡」：每天自动聚合国际教育行业新闻 → AI 结构化摘要 → 品牌海报 + 企微群消息 + dingning.ai 网页三路分发。单次跑完即退出的批处理，无常驻进程。

---

## 系统概览

- **触发**：dingning 服务器（ops 用户）`/etc/cron.d/ai-news-bot`，每天北京 09:10 执行 `bot_wecom.py`。由 `scripts/setup_cron.sh` 幂等生成（详见 README「定时任务」）。
- **产出**（一次运行）：
  1. 企微群 **海报 PNG**（image 消息，≤2MB）
  2. 企微群 **补充文本**（dingning.ai 完整阅读入口 + 小程序 schema）
  3. **dingning.ai/coffee/{date}** 网页（MDX 提交到 dingning-ai 仓库，Vercel 自动部署）
  4. （附加）昨日阅读统计 → 运维群
- **监控**：GitHub Actions `watchdog.yml`（每天北京 10:30）检查 dingning-ai 仓库当天是否有 coffee 提交——外部死人开关，与服务器完全独立，断更即企微告警。

## 模块地图（仓库根扁平布局）

| 模块 | 行数级 | 职责 | 对外接口 |
|---|---|---|---|
| `bot_wecom.py` | ~490 | 主编排：并行抓取→过滤重排→AI→发布→海报→文本→统计 | `main()` / `send_daily_news()` |
| `news_fetcher.py` | ~500 | 抓取与编排：TianAPI + RSS + NewsAPI、RSS JSON 文件缓存（1h TTL，assets/cache/rss/）；评分/去重委托给下面两个纯函数模块（NewsFetcher 留兼容代理） | `NewsFetcher.fetch_news()` |
| `news_scoring.py` | ~265 | 纯评分/分级：质量分、教育相关性系数、信号等级、词首边界关键词匹配、时间清洗/时效（词表单一真相源在 config） | `calculate_news_quality()` 等纯函数 |
| `news_dedup.py` | ~165 | 纯去重：URL/id 规范化去重键、标题相似度、跨源去重管线、来源多样性 | `dedupe_news()` / `apply_diversity_filter()` |
| `http_util.py` | ~25 | 共享 requests.Session + 指数退避重试构建 | `make_retry_session()` |
| `ai_summarizer.py` | ~290 | LLM 调用（OpenAI 兼容，默认 DashScope）。生产路径是 `summarize_for_poster()`：5 条结构化 JSON（title_zh/title_en/summary/punch/source），带日期锚定 + 反编造 prompt 约束；`summarize_news()` 为旧路径遗留（当前无调用方） | `AISummarizer` |
| `news_cache.py` | ~230 | 已推送去重：标题+URL 哈希，24h 窗口，`.news_cache.json` 持久化 | `filter_new_news()` / `mark_news_as_sent()` |
| `image_fetcher.py` | ~170 | 头条封面：抓 og:image/twitter:image → 本地缓存 → 三道质量门（尺寸/近方形 logo/白底拼图）| `fetch_article_image()` |
| `poster_generator.py` | ~300 | 海报：Jinja2 HTML 模板 → Playwright 截图 PNG；三套品牌主题按周几轮换；>2MB 自动转 JPEG | `render_png()` / `theme_for()` |
| `dingning_publisher.py` | ~200 | MDX 生成 + GitHub Contents API 提交 dingning-ai 仓库；失败不抛异常，返回降级 URL | `publish_to_dingning()` |
| `stats_reporter.py` | ~100 | 查 dingning.ai 阅读 API → 趋势条形图 → 运维群；任何异常只 log | `send_stats_report()` |
| `config.py` | ~180 | env 加载（`override=True`，.env 是唯一真相源）、主题/关键词/负面词单一真相源、LLM 路由 | 常量 |
| `start.py` | 6 | 薄入口 → `bot_wecom.main()` | — |
| `diagnose_news.py` | ~130 | 手动诊断脚本（逐环节检查抓取链路） | CLI |

## 数据流（单次执行，bot_wecom.send_daily_news）

```
① 并行 fetch_news(topic) × 5 主题        news_fetcher：三源抓取 → URL/id/标题/相似度去重
                                          → 7 天时效 → 质量评分排序 → 单源≤2 条
② filter_new_news('daily_digest')        news_cache：24h 内已推送剔除
③ 教育相关过滤 + 政策/招生/签证优先重排    bot_wecom 内联（EDUCATION_*_KEYWORDS）
④ 全局来源多样性（单源≤2）→ top 9 候选
⑤ summarize_for_poster(top 9)            LLM 选 5 条出结构化 JSON；title_en 要求逐字复制原标题
⑥ publish_to_dingning(9 候选, 5 选中)     MDX → GitHub API → Vercel 后台构建（与 ⑦ 时间重叠）
⑦ build_poster_data → render_png → 企微图片
       hero 封面走 image_fetcher og:image 质量门，失败自动"大数字装饰"兜底
⑧ 等 Vercel 部署（DINGNING_DEPLOY_WAIT_SEC 扣减 ⑦ 已耗时）→ 企微补充文本
⑨ stats_reporter → 运维群（失败不影响主流程）
```

**关键不变量：title_en 锚定。** LLM 重排/重选后的 poster_items 与 top_news 顺序不对齐，⑥⑦ 一律用归一化 title_en 匹配回源新闻取 URL/封面，**绝不按位置下标拉链**（PR #8）。匹配不上则宁缺毋错：省略链接并带响计数。

## 降级矩阵（每个外部依赖都有显式 fallback）

| 故障点 | 行为 |
|---|---|
| LLM 海报摘要失败/JSON 不合法 | 跳过海报与 dingning 同步，文本走通用 `/coffee` 入口 |
| og:image 抓取失败/被质量门拒绝 | 海报 hero 走"大数字装饰"兜底 |
| 海报渲染/发送异常 | 不阻断补充文本发送 |
| dingning MDX 提交失败 | 返回通用 `/coffee` URL，主流程继续 |
| 统计 API/发送失败 | 只 log，永不抛出 |
| 全部新闻源为空 / 全部已推送 | 取消本次日报（watchdog 次日 10:30 兜底告警） |

## 运行与部署

- **生产**：dingning 服务器 `/etc/cron.d/ai-news-bot`（09:10 日报 + jump-autodeploy 轮询 + 心跳），`scripts/setup_cron.sh` 幂等安装。cron 行内联 `LLM_MODEL=qwen-plus`（fast model）。
- **自动部署**：`scripts/auto_pull_deploy.sh`（cron 轮询 git，更新即拉取 + 企微部署通知）。
- **CI**：`.github/workflows/ci.yml` 仅 PR 触发，单 job `ruff` → `pytest -m "not network"`；main 分支 Required Status Check = `Lint & Test`。
- **`daily_news.yml`**：GitHub Actions 推送通道，schedule 已注释停用（避免与服务器 cron 双推），仅留 workflow_dispatch 手动兜底。
- **本地**：`python3 bot_wecom.py`；海报冒烟 `python3 poster_generator.py`（出三主题 mock 图）；`scripts/smoke_wecom.py` 假数据冒烟。

## 配置要点

- 必填：`DASHSCOPE_API_KEY`（或旧名 `DEEPSEEK_API_KEY`）、`WECOM_WEBHOOK_URL`（多条逗号分隔）。
- 可选：`LLM_BASE_URL`/`LLM_MODEL`（默认 DashScope + deepseek-v4-pro）、`TIANAPI_KEY`、`NEWSAPI_KEY`、`DINGNING_GITHUB_TOKEN`（缺省跳过网页同步）、`WECOM_OPS_WEBHOOK_URL`、`ACTIVE_TOPICS`（默认 5 个教育主题，见 `config.ACTIVE_TOPICS_DEFAULT`）、`SEND_WHEN_NO_NEW`。
- `.env` 通过 `load_dotenv(override=True)` 覆盖宿主残留 export（2026-06-02 事故教训）。

## 已知取舍

- 过滤仍分三层（抓取层评分 / 相关性系数 / 日报层重排），但全部关键词表已收口 `config.py` 单一真相源（2026-07-06，AUDIT #7）；改词只动 config。
- 缓存均为本地文件（`.news_cache.json` + `assets/cache/rss/` JSON），不支持多实例。
- 企微小程序 schema 仅 iOS 可点（详见 README「已知限制」）。
- 海报渲染依赖 Playwright Chromium，服务器需 `playwright install chromium`。

---

维护者可先阅读本文件，再查阅 `README.md` 获取操作指引。
