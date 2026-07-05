# 异乡早咖啡 - AI新闻聚合机器人

基于 DeepSeek AI 的智能新闻推送系统，专为国际教育行业从业者打造每日新闻日报。

## 核心特性

- **AI智能摘要** - DeepSeek V3.2（默认走火山方舟 Ark，OpenAI 兼容协议，可切回官方）总结新闻，自动翻译英文资讯
- **多源聚合去重** - 50+ RSS源 + 天行数据API，自动URL去重
- **智能质量评分** - 5维评分（来源权威性、内容深度、时效性、关键词匹配、独家性）
- **24小时缓存** - 避免重复推送相同新闻
- **企业微信推送** - Markdown格式，支持多群组同时推送
- **字节级截断** - 自动适配企业微信4096字节限制
- **dingning.ai 同步** - 每日 MDX 自动 commit 到 [yalding8/dingning-ai](https://github.com/yalding8/dingning-ai)，触发 Vercel 部署，群消息附带 `dingning.ai/coffee/{date}` 详情入口

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
# 必填：LLM API Key（阿里云百炼 DashScope，`sk-` 开头；亦兼容旧名 DEEPSEEK_API_KEY）
DASHSCOPE_API_KEY=sk-xxxxxxxx

# 可选：切换 LLM 供应商（默认走阿里云百炼 DashScope，OpenAI 兼容协议）
# LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1   # 默认
# LLM_MODEL=deepseek-v4-pro          # 默认；新闻 cron 用 qwen-plus（fast model，~5s/call）
# 切回火山方舟 Ark：
# LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
# LLM_MODEL=deepseek-v3-2-251201
# 切回 DeepSeek 官方：
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat

# 必填：企业微信 Webhook（多个用逗号分隔）
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx

# 可选：新闻API
TIANAPI_KEY=xxx
NEWSAPI_KEY=xxx

# 新闻源主题（用于获取新闻，最终合并为一条日报）
ACTIVE_TOPICS=study_abroad,market_data,industry_news,edu_policy,uni_rankings

# 可选：无新内容时也推送日报（默认 0）
SEND_WHEN_NO_NEW=0

# 可选：dingning.ai 跨项目同步
# 不填时跳过同步，群消息退化为通用 /coffee 入口
DINGNING_GITHUB_TOKEN=ghp_xxxxx     # https://github.com/settings/tokens
DINGNING_REPO=yalding8/dingning-ai
DINGNING_BASE_URL=https://dingning.ai
DINGNING_DEPLOY_WAIT_SEC=60         # Vercel 部署等待秒，扣减海报已耗时后 sleep 剩余
```

> **`.env` 是 webhook / LLM 路由的唯一真相源**：配置加载用 `load_dotenv(override=True)`，`.env` 中定义的 key 会覆盖宿主 shell 里可能残留的同名 export（2026-06 事故教训：长命 shell 残留 `WECOM_WEBHOOK_URL`/`LLM_*` 曾导致手动运行发错群）。`.env` 未定义的 key（如 CI secrets）仍从环境变量读取。

### 3. 运行

```bash
python start.py      # 入口：start.py → bot_wecom.main()
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

4. 消息发送（publish 提前 + 等待时间复用）
   ├── MDX → dingning-ai 仓库（GitHub Contents API）—— Vercel 后台开始构建
   ├── 海报 PNG → 企微 image 消息（约 30s，与 Vercel 构建并行）
   ├── 等待 Vercel 部署完成（默认 60s，扣减海报已耗时后 sleep 剩余）
   └── 文本 → 企微 markdown 消息（含 dingning.ai/coffee/{date} 入口）
```

## dingning.ai 跨项目集成

每日推送 = 海报 + MDX + 文本三件套，**publish 提前到海报之前**让 Vercel 构建与海报推送时间重叠：

```
ai-news-bot                                  dingning-ai (Next.js SSG)
─────────────                                ──────────────────────────
AI 摘要 ─────► poster_items
                  │
                  ├─► publish_to_dingning ─► PUT content/coffee/{date}.mdx
                  │   (GitHub Contents API)         │
                  │                                 ▼
                  │                           Vercel 后台构建（约 30-60s）
                  │                                 │
                  ▼                                 │
              海报渲染 + 发企微（约 30s）            │
                  │                                 │
                  ▼                                 ▼
              sleep(wait_sec - elapsed)       /coffee/{date} 就绪
                  │                                 │
                  └─► send_wecom_message ◄─────────┘
                      (含 dingning.ai/coffee/{date} 链接)
```

实测海报到文本的群内可见间隔约 25-35s（vs 顺序串行的 90s）。

**关键设计**：
- **失败隔离**：dingning.ai 同步失败不阻塞企微推送，文本退化到 `/coffee` 通用入口
- **凭据安全**：`DINGNING_GITHUB_TOKEN` 仅放服务器 `.env`，绝不进 git 跟踪文件
- **法律安全**：MDX 只收录中文标题 + ≤30 字 punch + 原文链接，不存原文长摘要
- **幂等**：同日重跑会用已存在文件 sha 覆盖更新，不会创建重复 commit

详见 `dingning_publisher.py`。

## 项目结构

```
ai-news-bot/
├── bot_wecom.py            # 主程序：流程控制、消息发送
├── news_fetcher.py         # 新闻获取：API+RSS、质量评分、去重过滤
├── ai_summarizer.py        # AI摘要：DeepSeek调用
├── news_cache.py           # 缓存管理：24小时去重
├── poster_generator.py     # 海报渲染：Jinja2 HTML → Playwright 截图 PNG（>2MB 自动转 JPEG）
├── image_fetcher.py        # 文章封面抓取（og:image，含质量门：拒绝 logo/小图/白底拼图）
├── dingning_publisher.py   # dingning.ai 跨项目发布（GitHub Contents API）
├── config.py               # 配置：主题、关键词、RSS源、跨项目参数
├── requirements.txt        # Python运行依赖
├── requirements-dev.txt    # 开发/测试依赖（pytest、ruff）
├── pyproject.toml          # ruff + pytest 配置（pythonpath、network marker）
├── .env.example            # 环境变量模板
├── .news_cache.json        # 缓存数据（自动生成）
├── tests/                  # 单元测试（pytest；外网测试标 @pytest.mark.network）
├── .github/workflows/      # ci.yml（PR 触发 lint+test）+ watchdog + daily_news
└── scripts/
    ├── wecom_notify.sh     # 企微群机器人 bash 推送工具（运维事件专用）
    ├── auto_pull_deploy.sh # 服务器端 cron 自动部署（含企微部署成功/失败通知）
    └── heartbeat.sh        # 每日 💓 心跳（磁盘 + cron 最近运行时间 + 部署 commit）
```

## 可用主题

| 主题代码 | 名称 | 说明 |
|---------|------|------|
| `study_abroad` | 留学资讯 | The PIE News、Inside Higher Ed、芥末堆等 |
| `market_data` | 数据趋势 | ICEF Monitor、EdSurge、黑板洞察等 |
| `industry_news` | 行业动态 | 多知网、鲸媒体、TechCrunch Education等 |
| `edu_policy` | 教育政策 | 各国留学、签证、移民政策更新 |
| `uni_rankings` | 院校排名 | QS、THE、US News 等大学排名动态 |
| `finance` | 财经新闻 | 虎嗅、36氪、华尔街见闻等 |
| `startup` | 创业投资 | 创业邦、36氪、Hacker News 等 |
| `education` | 教育综合 | Times Higher Education等 |
| `pbsa` | 学生公寓 | PBSA 学生公寓行业动态 |
| `uhomes` | 异乡好居 | 异乡好居企业动态 |

## 定时任务

定时任务写在 **`/etc/cron.d/ai-news-bot`**（root 拥有），由 `scripts/setup_cron.sh` 幂等安装。**为什么不放用户 crontab**：2026-05-30 与 2026-06-03 两次"集中迁移"整体重写 ops 用户 crontab 时把本项目 cron 整条漏掉，静默断更（前者 4 天）。集中迁移本质是 `crontab -l > bak; crontab newfile`，**物理上碰不到 `/etc/cron.d/*`** —— 每个项目拥有自己独立、迁移脚本删不掉的调度文件，从结构上根治该故障模式。

```bash
# /etc/cron.d 语法比用户 crontab 多一个 user 字段（这里是 ops）
# 每天早 9:10 推送新闻（北京时间）；内联 LLM_* 锁定 qwen-plus（fast model）
10 9 * * * ops cd /home/ops/ai-news-bot && LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 LLM_MODEL=qwen-plus /home/ops/ai-news-bot/venv/bin/python start.py >> /home/ops/ai-news-bot/ai-news.log 2>&1

# 每 5 分钟（2-57/5）jump-autodeploy 自动部署检测
2-57/5 * * * * ops /opt/jump-autodeploy/bin/auto-deploy.sh /home/ops/ai-news-bot >> /home/ops/ai-news-bot/logs/auto-deploy.log 2>&1

# 每天 10:00 推送运维心跳
0 10 * * * ops /home/ops/ai-news-bot/scripts/heartbeat.sh >> /home/ops/ai-news-bot/heartbeat.log 2>&1
```

安装/改排程（写 `/etc/cron.d` 需 sudo；改排程或模型只改 `setup_cron.sh` 里的 `DESIRED` 再重跑，幂等）：

```bash
bash /home/ops/ai-news-bot/scripts/setup_cron.sh   # 装到 /etc/cron.d 并清掉用户 crontab 旧行防双跑
sudo cat /etc/cron.d/ai-news-bot                   # 验证 3 行在册
# 回滚：sudo rm /etc/cron.d/ai-news-bot
```

> ⚠️ `setup_cron.sh` 是**手动一次性脚本**，jump-autodeploy 只 `git pull` 不会自动跑它 —— 迁服务器或文件被删后须手动重跑一次。

### 外部断更看门狗（dead-man's-switch）

`.github/workflows/watchdog.yml`：每天 **10:30（北京）** 在 GitHub Actions 上检查 `yalding8/dingning-ai` 是否有当天的「异乡早咖啡」提交（每次成功推送都会 commit 一份 MDX）。没有 = 断更 → 企微告警 + workflow 标红。

**为什么放 GitHub 而非服务器**：心跳本身是服务器 cron 的一条，集中迁移会**连心跳一起删** —— "看门狗与被监控对象同生共死"。本看门狗跑在 dingning 主机之外，哪怕整机宕机/crontab 清空/心跳没了仍能报警。

需在仓库配置一个 secret（**绝不硬编码**）：

```bash
gh secret set WECOM_BOT_WEBHOOK_URL   # 企微运维群 webhook，与心跳同一个
```

> 推送本身仍统一由服务器 cron 触发（GitHub Actions 的 `daily_news.yml` 定时已禁用，避免双推）；watchdog **只监控不推送**，无双推风险。

### 部署（2026-06 起接入集中部署器 jump-autodeploy）

接入共享部署器 **`/opt/jump-autodeploy`**，取代旧版走 SSH 的 `scripts/auto_pull_deploy.sh`（服务器 deploy key 失效后该脚本长期静默失败）。本仓库是 **public**，服务器 remote 用 HTTPS（`https://github.com/yalding8/ai-news-bot.git`）即可免凭证 fetch。

- **conf 驱动**（`deploy/autodeploy.conf`）：`git fetch` → `git reset --hard origin/main`（**不跑 `git clean`**，untracked `.env` / `.news_cache.json` 安全）→ `INSTALL_TRIGGER=requirements.txt` 命中才 `pip install`。无 RESTART（批量 cron job 无需重启）。
- **首次/迁服务器接入**：① `git remote set-url origin https://github.com/yalding8/ai-news-bot.git` ② `git fetch origin && git reset --hard origin/main`（先把 conf 拉到工作树，否则 jump-autodeploy 因无 conf 返回 `exit 2` 不接管）③ `bash scripts/setup_cron.sh` 装齐三条 cron。`--dry-run; echo exit=$?` 从 `exit 2` 变 `exit 0` 即接管成功。
- **部署告警**：jump-autodeploy 的 `lib/notify.py` **只发飞书卡片**，读 `.env` 中的 `DEPLOY_NOTIFY_WEBHOOK`（飞书运维群，与 aifx 共用频道）。**未配置该变量则部署静默无卡片**。
- **playwright**：chromium 二进制不在 INSTALL 链里（已装且极少变）；bump playwright 后手动 `venv/bin/python -m playwright install chromium`。

### 运维通知
- **每日心跳**：`scripts/heartbeat.sh` 每天 10:00 推送磁盘用量、cron 最近运行时间、最近部署 commit；25h 没收到 = 告警链路断。读服务器 `/home/ops/ai-news-bot/.deploy.env` 的 `WECOM_BOT_WEBHOOK_URL`（**企微**运维群，与业务推送的 `WECOM_WEBHOOK_URL` 独立）。
- **部署成功/失败/回滚**：走 jump-autodeploy 飞书卡片（见上「部署」节，`DEPLOY_NOTIFY_WEBHOOK`），不再走旧的企微 `auto_pull_deploy.sh` 链路。

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

## 开发与测试

```bash
pip install -r requirements-dev.txt   # pytest、ruff
ruff check .                          # 静态检查（沿用 ruff 默认规则集，无行长噪音）
pytest -m "not network" -q            # 跑单元测试，跳过需要外网的 RSS 抓取测试
```

- **配置在 `pyproject.toml`**：`pythonpath = ["."]` 让根目录扁平模块（`bot_wecom` 等）在 `pytest` 控制台脚本下也能 import；`@pytest.mark.network` 标记需要外网的测试（CI 用 `-m "not network"` 保证确定性）。
- **CI**（`.github/workflows/ci.yml`）：**仅 PR 触发**（PR 合并即 push to main，不重复跑），单 job `Lint & Test` 先 `ruff` 后 `pytest`，开 pip 缓存 + concurrency 去重。
- **Branch Protection**：`main` 已设 `Lint & Test` 为 Required Status Check + 禁 force-push/删除。改 CI job 名后须用 `gh api` 同步更新该保护规则，否则旧名失效。
- **架构/质量审计**：见 `docs/AUDIT_2026-07-05_ARCH_CODE_QUALITY.md`（综合 7/10；行动清单含僵尸测试清理、评分 `'the'` 关键词 bug、news_fetcher 拆分等 8 项，状态跟踪在报告内）。

## 已知限制

### 小程序卡片仅 iOS 客户端可点

群消息文本里的 `[#小程序://APPNAME/SHORTID]` schema 在企微不同客户端表现不一致（2026-04-27 验证）：

| 客户端 | 行为 |
|---|---|
| iOS | ✅ 渲染成可点小程序卡片 |
| Android / 鸿蒙 | ❌ 显示为字面文字，不可跳转 |
| 桌面端 | ❌ 多数版本显示为字面文字 |

WeCom webhook 不支持 `miniprogram_notice` 卡片类型，跨平台可点小程序的唯一官方方式是 `template_card`（`card_type: news_notice` + `card_action.type=2`），需要小程序真实 wx_appid 且每个小程序占一条独立消息。

**当前选择**：保持 2 条消息（海报 + 文字）的简洁结构，接受 Android/鸿蒙 用户看到字面 schema 的降级。如未来要做跨平台可点，需先评估"消息条数翻倍"对群体验的影响。

### 同行多 schema 会触发 markdown 解析降级

写小程序 schema 时**每个必须独占一行**，禁止同行多 schema + `|` 分隔——会让企微 markdown 解析降级，连 iOS 也不可点。

## 成本估算

| 项目 | 月费用 |
|------|--------|
| DeepSeek API | ~¥1 |
| 服务器（可选） | ¥28-35 |
| **总计** | **¥29-36/月** |

## 更新日志

### v2.7 (2026-06-22)
- 补 og:image 质量门盲区：PIE News 对 M&A/交易类报道惯用「白底 + 两个公司 logo 并排」当 og:image（如 Crizac 收购 ForeignAdmits），这类图宽幅且尺寸大，躲过 v2.6 的尺寸/正方门，却在 1080×560 cover 裁切里被切烂（右侧 logo 截成 "ForeignAdm"）。`_is_usable_cover` 新增白底占比门：64×64 缩略图近白像素占比 ≥55% 直接拒（拼图 ~85%，真实照片即便天空占比高也仅 ~39%），拒掉后回落「大数字装饰」兜底；新增对应单测

### v2.6 (2026-06-15)
- 修复头条海报顶部频繁出现 36Kr logo 的问题：36氪对约半数无配图文章返回 240×240 品牌 logo 当 og:image，旧链路无校验直接铺满 banner。`image_fetcher` 新增质量门 `_is_usable_cover`（宽<600 或接近正方形小图直接拒），拒掉后海报走"大数字装饰"兜底；对所有来源通用，新增 `tests/test_image_fetcher.py`
- 上线 PR 触发的 CI（`.github/workflows/ci.yml`）：单 job `Lint & Test`（ruff + pytest），pip 缓存 + concurrency 去重；新增 `pyproject.toml`（ruff/pytest 配置）、`requirements-dev.txt` pin `ruff`；清理全仓 24 个历史 lint 问题
- `main` 启用 Branch Protection：`Lint & Test` 为 Required Status Check，禁 force-push/删除

### v2.5 (2026-06-02)
- 部署接入集中部署器 `/opt/jump-autodeploy`（取代走 SSH 的 `auto_pull_deploy.sh`，deploy key 失效问题根治）；服务器 remote SSH→HTTPS（public 仓库免凭证）；新增 `deploy/autodeploy.conf` + `scripts/setup_cron.sh`（幂等装齐 news/auto-deploy/heartbeat 三条 cron，兼 crontab 被扫后一键恢复）
- 配置加载改 `load_dotenv(override=True)`，`.env` 成为 webhook/LLM 路由唯一真相源，根治宿主 shell 残留 export 盖住 `.env` 导致的手动运行发错群 / 打错 LLM endpoint；新增 `tests/test_config_env.py`
- 文档同步实际状态：LLM 默认已切阿里云百炼 DashScope（`deepseek-v4-pro`，新闻 cron 用 `qwen-plus`），入口 `start.py`，心跳 10:00

### v2.4 (2026-04-27)
- 接入 dingning.ai 跨项目发布：每日 MDX 自动 commit 到 yalding8/dingning-ai 触发 Vercel 部署
- 企微文本消息引入 `dingning.ai/coffee/{date}` 详情入口，群里只展示 1 条收口链接
- 修复小程序 schema 同行多次 + `|` 分隔导致企微 markdown 解析降级、卡片不可点的问题（拆回独占两行）
- 新增 `dingning_publisher.py` 模块，含失败兜底、幂等更新（按 sha 覆盖）
- 时序优化：publish 提前到海报之前，海报推送与 Vercel 构建并行，海报到文本群内可见间隔从 92s 降到 25-35s
- `DINGNING_DEPLOY_WAIT_SEC` 默认从 90 调整到 60（实测 Vercel SSG 构建 30-60s 完成）
- 文本格式微调：去除 `---` 字面分隔线（企微不渲染成 hr），改用空行做视觉分隔

### v2.3 (2026-04-24)
- LLM 接入切换为 OpenAI 兼容协议，新增 `LLM_BASE_URL` / `LLM_MODEL` 环境变量
- 默认走火山方舟 Ark 上的 DeepSeek v3.2（`deepseek-v3-2-251201`），可通过 env 切回 DeepSeek 官方
- 禁用 GitHub Actions 定时推送，统一改由服务器 cron（9:10 北京时间）
- 项目瘦身：移除冗余文档与部署脚本，保留核心业务代码

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
