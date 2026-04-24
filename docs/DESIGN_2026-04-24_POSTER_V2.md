# 异乡早咖啡 · 海报化 v2.0 设计文档

| 项 | 值 |
|---|---|
| 文档版本 | **v2.2**（Gate-1 二次补强，冲 9.5 维度阈值） |
| 创建日期 | 2026-04-24 |
| 负责人 | neilding |
| 状态 | 待 Gate-1 第 3 轮评审通过后方可进入开发 |

## 变更记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-04-24 10:00 | v2.0-draft | 基于 grill-me 对话首版 |
| 2026-04-24 14:40 | v2.1 | Gate-1 第 1 轮补强：P0/P1 覆盖（§10-§15） |
| 2026-04-24 15:00 | **v2.2** | **Gate-1 第 2 轮补强（冲 9.5 维度阈值）**：§1.3 BD 共识访谈 / §10.3 分布式事务幂等性 / §12.5 法律合规假设 / §13.5 压力测试 / §13.6 故障注入 / §6 补 R19-R22 服务器物理风险 |

---

## 1. 背景与问题

### 1.1 现状痛点
- 日报是 markdown 文本，推送到微信群后被折叠压缩
- BD（40 人）每天顺手把日报群转群，不转朋友圈
- BD 反馈文本被压缩 + 希望"更加生动"

### 1.2 目标
- 日报图片化，不被微信折叠
- 提供朋友圈可直接转发的视觉物料
- 保持"异乡早咖啡"品牌行业情报简报人设

### 1.3 BD 共识确认清单（Pre-Day-1 必做）

**痛点推测基于单次用户反馈，Day 1 启动前必须访谈验证**，否则 MVP 命中的可能不是 BD 真实痛点。

| # | 访谈对象 | 抽样量 | 问题 | 通过条件 |
|---|---|---|---|---|
| I1 | BD 骨干（入职 > 6 个月） | 3-5 人 | "你现在会转日报到朋友圈吗？如果不转，哪种物料你会转？" | ≥ 60% 表达需要视觉物料 |
| I2 | 同上 | 同上 | "如果公司每天给你 3 段朋友圈文案，你会按模板发，还是自己改？" | 了解真实使用路径 |
| I3 | 市场/运营负责人 | 1-2 人 | "40 个 BD 批量发同一海报到各自朋友圈，合规风险你怎么看？" | 确认公司内部合规立场 |
| I4 | 项目负责人（你自己） | 1 人 | 提供"品牌立场预审"清单：哪些院校/话题不评价 | 产出 `config.BRAND_CONSTRAINTS` |

**访谈结果写入** `docs/INTERVIEW_2026-04-XX_BD_CONSENSUS.md`，作为 Day 1 启动的前置依据。

访谈过程中若发现"BD 压根不想发朋友圈"或"公司禁止批量发朋友圈内容"，**立即终止本项目或降级为仅做图片化**（砍掉 §15 配文变体）。

## 2. 最终功能规格

| 项 | 规格 |
|---|---|
| 画幅 | 1080×2400px（hero 1080×1080 + 主体区） |
| 视觉风格 | V3 中文科技媒体感 + 纯文字排版 |
| 品牌配色 | B 方案：好居 `#FF5A5F` 主 + 缴费墨稿黑底部签名条 |
| 字体 | 中文阿里普惠 3.0 · 英文 Montserrat |
| Hero 内容 | H1：最劲爆新闻中文大标题 + 金句 + 日期（+ 英文原标题小字） |
| Hero 挑选 | S2：AI 二次评分"朋友圈传播力"（含敏感词过滤） |
| 内页 4 条 | L2：中文大字 + 英文原标题小字副标题 + 2-3 句摘要 + 来源 attribution |
| 底部 | 双 logo 条 + 2 个小程序二维码占位 + AIGC 标识 + 品牌签名 |
| 分发 | D1：现有企微群，3 条消息链（image + 3 变体配文 + markdown 原日报） |
| 配文 | AI 生成 3 段变体（专业型/数据型/提问型），70 字内 |
| Canary | 3 天内部 smoke → 4-7 天 BD 测试群 → 8-14 天客户群渐进 |

## 3. 目录与文件

```
ai-news-bot/
├── assets/
│   ├── fonts/ (阿里普惠 3.0 + Montserrat .woff2)
│   ├── logos/ (uhomes.png / pay-mono.png，来自 PDF 提取)
│   ├── qrcodes/ (占位/真实二维码)
│   └── templates/daily_digest.html.j2
├── poster_generator.py          【新增】
├── hero_ranker.py               【新增】+ 敏感词过滤
├── copywriter.py                【新增】+ 3 变体生成
├── ai_summarizer.py             【改】L2 中英双标题 + 降级
├── bot_wecom.py                 【改】send_image() + send_poster_flow() + 告警
├── config.py                    【改】海报配置 + 敏感词表 + 阈值
└── tests/
    ├── test_poster.py           【新增】视觉快照
    ├── test_hero_ranker.py      【新增】评分回归
    ├── test_copywriter.py       【新增】合规校验
    └── integration/test_e2e.py  【新增】端到端 smoke
```

## 4. 数据流（带降级分支）

```
cron 09:10
 └─ fetch_news → 过滤 → rank → top 5
    └─ summarize_daily_news(L2)                       [改 prompt]
       │ ├─ 成功: 取中英双标题摘要
       │ └─ 失败: 降级到纯英文标题 + 简短描述
       └─ hero_ranker.score_shareability()            [新] (带敏感词过滤 + fact-check)
          │ ├─ 成功: 选最高分
          │ └─ 失败: fallback 到 top[0]
          └─ copywriter.generate_variants() × 3       [新] (专业/数据/提问型)
             │ ├─ 成功: 3 段配文
             │ └─ 失败: fallback 到固定模板
             └─ poster_generator.render() → PNG
                │ ├─ 成功: 推送 3 条消息链
                │ └─ 失败: 完全降级 → 原 markdown 日报
                ▼
                WeCom webhook:
                 ① image (PNG/JPEG base64)
                 ② text (3 变体配文, 标"BD 请择一")
                 ③ markdown (原日报文本)
```

## 5. 技术栈选型

| 选型 | 决定 | 理由 |
|---|---|---|
| 生图 | HTML + Playwright | AI 能直接改 HTML；服务器 7.1GB 内存够 |
| 字体 | 阿里普惠 3.0 (中) + Montserrat (英) | CLAUDE.md 品牌硬规则 |
| 图尺寸 | 1080×2400 hero+long | α-hero+long，朋友圈预览看 1:1，打开看全图 |
| 图格式 | PNG 优先，>2MB 降 JPEG q=85 | 企微 2MB 上限 |
| Hero 挑选 | AI 二次评分 + 敏感词黑名单 | 朋友圈传播力 ≠ 重要性；防政治敏感 |

## 6. 风险清单（v2.1 补全版）

| # | 风险 | 等级 | 缓解 | 落地章节 |
|---|---|---|---|---|
| R1 | Playwright Chromium ~300MB 首装卡服务器 | P0 | 预安装脚本 + 本地预跑验证 | §14.1 |
| R2 | 字体加载慢导致截图未渲染完 | P0 | `document.fonts.ready` + 预热 + `font-display: swap` | §11.1 |
| R3 | 海报 PNG 超 2MB 企微拒收 | P1 | PNG 优先 → JPEG q=85 兜底 | §11.3 |
| R4 | hero AI 选错（选到政治敏感/冷门） | P1 | few-shot prompt + 敏感词黑名单 + 人工巡检 | §12.3, §15.3 |
| R5 | 阿里普惠下载源不稳 | P2 | 字体进 git (~10MB 可接受) | §14.1 |
| R6 | 红蓝双品牌色冲突 | P2 | B 方案：缴费墨稿化 | 已定 |
| **R7** | **3 次 AI 调用级联失败（~97% 成功率）** | **P1** | **独立超时+重试+熔断，任一失败降级** | §10.1 |
| **R8** | **40 BD 同文案朋友圈批量发触发微信反垃圾** | **P1** | **生成 3 段变体配文** | §15.2 |
| **R9** | **hero 选出政治/国别敏感条目，品牌方承担立场** | **P1** | **敏感词黑名单 + 品牌方立场预审** | §12.3 |
| **R10** | **AIGC 内容标识合规（深度合成规定）** | **P1** | **海报右下角"AI 辅助生成"标识** | §12.1 |
| **R11** | **新闻来源版权** | **P1** | **图底部 attribution + 翻译改写不逐字** | §12.2 |
| **R12** | **AI 翻译事实错误（大学名/数字误译）** | **P1** | **Hero 条目强制二次 AI 校验 fact-check** | §12.4 |
| **R13** | **白字红底对比度 3.0:1 低于 WCAG AA** | **P1** | **小字改深色在白底区域；大字豁免** | §11.2 |
| **R14** | **Volcengine 余额耗尽（真实事故 2026-04-24）** | **P1** | **每次 runtime 查余额，≤10 元告警** | §14.3 |
| **R15** | **端到端执行时间从 5s 涨到 ~30s，cron 窗口风险** | **P1** | **本地实测预算；告警阈值 60s** | §14.2 |
| **R16** | **客户群 3 条消息疲劳** | **P2** | **Canary 先 BD 测试群观察；备 D3 独立群切换方案** | §15.1 |
| **R17** | **.news_cache.json / ai-news.log 无 TTL 持续增长** | **P2** | **启动时清 30 天前缓存 + logrotate** | §14.5 |
| **R18** | **英文原标题含政治敏感词触发微信审核** | **P2** | **原标题预扫敏感词，命中则不展示英文** | §12.3 |
| **R19** | **服务器硬盘空间**（日志/缓存/临时图持续增长） | **P2** | **预估日增 ~12MB；设 `df` > 80% 时企微告警** | §14.6 |
| **R20** | **Playwright 渲染内存峰值**（单次 ~500MB RAM） | **P2** | **启动时检查 `free -m`；< 1GB 可用则降级 markdown** | §14.6 |
| **R21** | **服务器是否与其他业务共享**（7.1GB RAM） | **P1** | **上线前核验宿主上其他服务；如共享宿主则限 Playwright max-memory** | §14.6 |
| **R22** | **cron 任务重叠**（前一次未结束，下一次又触发） | **P2** | **已有 `check_run_lock()` 机制；核验锁文件路径与超时合理** | §14.6 |
| **R23** | **3 条消息推送部分成功**（图发成功但配文失败） | **P1** | **分布式事务幂等性 + 补偿推送** | §10.3 |
| **R24** | **BD 朋友圈商业推广法律合规** | **P1** | **假设明确记录 + 法务过审** | §12.5 |

---

## 7. 验收标准（补强版）

### 7.1 合格海报必须满足
- [ ] **视觉**：hero 中文大标题在 6.5 寸屏 1m 距离可读
- [ ] **翻译**：5 条新闻中文翻译无事实错误（至少 hero 过 fact-check）
- [ ] **合规**：海报底部有 AIGC 标识 + 每条新闻有来源 attribution
- [ ] **尺寸**：PNG < 2MB 或 JPEG q=85 兜底
- [ ] **时间**：端到端执行 ≤ 30 秒
- [ ] **降级**：任一 AI 调用失败时，降级推送成功（至少 markdown 日报）
- [ ] **敏感词**：hero 条目通过敏感词黑名单过滤
- [ ] **字体**：中英文字体加载完整（无系统字体回退）

### 7.2 Phase 1 验收时机
- Day 3 结束：本地 smoke 图人工审阅
- Day 7 结束：Canary 阶段 BD 测试群反馈
- Day 14 结束：完整跑通 2 周后 Go/No-Go 决定客户群全量

---

## 8. Phase 划分

- **Phase 1 MVP**（3-5 人日）：产出可发群的 v1 海报 + 降级链 + Canary 机制
- **Phase 2**（2 人日）：基于反馈微调视觉 + 真二维码
- **Phase 3**（可选）：数据抽取、独立 BD 群（D3）、效果回流埋点

---

## 9. 待你补的外部资源

- 异乡好居 + 异乡缴费小程序二维码 PNG
- 品牌立场预审：3 条示例 hero 候选 → 你拍板"什么不能放" → 写入 config
- （可选）logo SVG 源文件（PDF 提取 PNG 已够 MVP 用）

---

# §10 - §15（Gate-1 v2.1 补强章节）

## §10 失败容忍与降级策略

### 10.1 AI 调用级联保护

所有 3 次 AI 调用都套同一个装饰器：

```python
@retry(timeout=30, max_retries=2, backoff=exponential, fallback=None)
def ai_call(...): ...
```

降级策略（从上到下尝试）：

| 失败点 | Fallback 1 | Fallback 2 | Fallback 3 |
|---|---|---|---|
| summarize_daily_news | 纯英文标题 + 简短描述 | 原日报 markdown | 发送错误到群 |
| hero_ranker.score | 选 top[0] | 跳过 hero，用列表式版面 | 同上 |
| copywriter.generate | 固定模板配文 | 不发配文，只发图 | 同上 |
| poster_generator.render | markdown 日报 | 同上 | 发送错误到群 |

### 10.2 熔断

连续 3 次端到端失败 → 自动停止 24 小时 cron 并推送企微群告警。

### 10.3 分布式事务与消息推送幂等性

3 条消息链（image → text 配文 → markdown 日报）**不是原子**，必须设计部分失败补偿。

#### 10.3.1 推送顺序（含重试）

```python
request_id = f"{today}_{cron_run_id}"   # 幂等键

# 第 1 条：海报图（最重要）
success_img = send_image_with_retry(img, request_id + "_img", max_retries=2)

# 第 2 条：3 变体配文
success_copy = send_text_with_retry(copy_text, request_id + "_copy", max_retries=2)

# 第 3 条：原日报 markdown（兜底，BD 拿链接用）
success_md = send_markdown_with_retry(md, request_id + "_md", max_retries=2)
```

#### 10.3.2 部分失败补偿矩阵

| img | copy | md | 补偿动作 |
|---|---|---|---|
| ✅ | ✅ | ✅ | 正常结束 |
| ✅ | ✅ | ❌ | 容忍：原日报缺失，BD 可自己翻群历史；日志 WARN |
| ✅ | ❌ | ✅ | **补偿**：发一条兜底配文 "📰 今日要闻，请查看上方海报。—— 异乡早咖啡" |
| ✅ | ❌ | ❌ | 同上补偿配文 + markdown 降级警告 |
| ❌ | — | — | **完全降级**：不发图、不发配文，只发 markdown 日报；企微告警群通知 |

#### 10.3.3 幂等键防重复

`request_id` 作为防重复键写入 `.push_idempotency.json`。cron 意外重复触发时（例如锁文件时间戳失效），**重复 request_id 的推送跳过**。

#### 10.3.4 WeCom 重复消息去重

WeCom webhook 对 10 分钟内完全相同文本会静默去重——**这正好帮我们兜住幂等失败重试**。但不能依赖它，因为 image 消息的 base64 每次略不同（压缩随机性）。

#### 10.3.5 幂等键文件写入竞态

`.push_idempotency.json` 若遇 cron 重复触发（锁机制失效的边界场景），会有并发写入竞态。解决：

```python
import fcntl
with open(IDEMPOTENCY_FILE, 'r+') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    try:
        data = json.load(f)
        # ... check/update
        f.seek(0); f.truncate(); json.dump(data, f)
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Hero fact-check 失败的具体降级实现**：

```python
# hero_ranker.pick_hero() 内部
translated = translate(hero_en)
if not fact_check(hero_en, translated):   # §12.4
    # 方案 A: Hero 降级为"英文原文"展示 + 一句手工概括
    return Hero(title_en=hero_en, title_zh=auto_summary(hero_en, "短概括"), mode="degraded")
    # 方案 B（备选）：跳过 hero，版面改为纯列表式
# 默认方案 A；模板需支持 mode="degraded" 分支
```

---

## §11 渲染规范与可读性

### 11.1 字体加载时序

```python
# Playwright 渲染必须等字体完成
await page.goto(f"file://{html_path}")
await page.evaluate("document.fonts.ready")
await page.wait_for_timeout(200)  # 给布局再留 200ms 缓冲
```

CSS：
```css
@font-face {
  font-family: 'Alibaba PuHuiTi 3.0';
  src: url('../fonts/AlibabaPuHuiTi-3-55-Regular.woff2') format('woff2');
  font-display: swap;
  font-weight: 400;
}
```

启动预热：cron 前 5 秒执行 `warmup.py` 打开一次浏览器实例 + 加载字体。

### 11.2 对比度规范

| 区域 | 字色 | 底色 | 对比度 | 合规 |
|---|---|---|---|---|
| Hero 大标题（≥64px） | 白 `#FFFFFF` | 珊瑚红 `#FF5A5F` | 3.0:1 | ✅（WCAG 大字豁免） |
| 内页新闻标题 | 深灰 `#2C3033` | 白 `#FFFFFF` | 12.6:1 | ✅ AAA |
| 英文副标题 | 中灰 `#6B7280` | 白 `#FFFFFF` | 6.3:1 | ✅ AA |
| 日期/Attribution | 浅灰 `#9CA3AF` | 白 `#FFFFFF` | 3.3:1 | ⚠️ 仅用于非关键信息 |

### 11.3 图输出规范

```python
# 先 PNG
img_path = render_to_png(html_path, width=1080, height=auto)
if os.path.getsize(img_path) > 2 * 1024 * 1024:
    img_path = convert_to_jpeg(img_path, quality=85)
assert os.path.getsize(img_path) < 2 * 1024 * 1024, "Image too large even as JPEG"
```

---

## §12 合规与 Attribution

### 12.1 AIGC 标识

海报右下角角标：
```
AI 辅助生成 · 异乡早咖啡
```
字号 14px，浅灰色，不醒目但可见，满足深度合成规定的"显著标识"底线。

### 12.2 新闻来源 Attribution

每条内页新闻下方小字：
```
来源：PIE News · 2026-04-23
```

Hero 底部：
```
内容编译自 Inside Higher Ed
```

**翻译改写原则**：
- 标题允许翻译
- 摘要必须"改写"而非"直译"
- 不使用原文连续 > 30 字的段落

### 12.3 敏感词黑名单

`config.py` 新增：
```python
SENSITIVE_KEYWORDS = [
    # 政治
    '台独', '港独', '藏独', '疆独', '两岸', '台海',
    # 国别敏感
    '中美对抗', '制裁', '脱钩', '排华',
    # 种族/宗教
    '种族歧视', '穆斯林', '排犹',
    # 品牌合作方冲突
    # （待项目负责人提供"我们合作的 XX 大学不说负面"清单）
]
```

`hero_ranker.score_shareability` 在打分前过滤：命中任一关键词 → 得分 -10（几乎不会被选）。

### 12.4 翻译事实核查

Hero 条目翻译完成后，追加一次 AI 校验：

```
Prompt: "以下中文标题是否准确翻译自英文原文？
英文: {en}
中文: {zh}
只回答 'OK' 或指出错误。"
```

校验不过 → Hero 降级为"英文原文 + 一句中文概括"。

### 12.5 法律合规假设与责任划分

本项目涉及 **AIGC + 新闻编译 + 营销推送** 三重合规风险。v2.2 明确以下假设及责任：

#### 12.5.1 假设清单

| # | 假设 | 依据 | 如不成立 |
|---|---|---|---|
| L1 | 海报内容属于**新闻编译**，引用片段 + 翻译改写受著作权法第 22 条"合理使用"保护 | 法条第 22 条第(3)项"时事新闻报道" | 必须删除新闻原文引用、改成完全重写摘要 |
| L2 | BD 朋友圈转发属于**个人分享行为**，非《广告法》意义上的商业广告投放 | 朋友圈非广告位；无付费推广 | 需走广告法合规（指向广告主实名、广告标识） |
| L3 | AIGC 标识"AI 辅助生成 · 异乡早咖啡"满足《生成式 AI 服务管理暂行办法》(2023-08) + 《互联网信息服务深度合成管理规定》(2023-01) 的显著标识义务 | 第 17 条 + 第 16 条 | 需更强显著标识（如标注 AI 生成内容边框） |
| L4 | 新闻来源 attribution 满足著作权尊重义务（PIE News / ICEF / IHE 等海外源） | 著作权法 + 国际 fair use 实践 | 需逐一取得授权或放弃该来源 |
| L5 | 异乡好居 + 异乡缴费双 logo 使用已获品牌内部授权 | VI 规范 PDF 已提供 | 需重新确认授权范围 |

#### 12.5.2 前置法务过审（强烈建议）

Day 1 启动前，**公司法务（如有）需过一遍 §12 全部章节**。产出：
- `docs/LEGAL_REVIEW_2026-04-XX_POSTER_V2.md`：法务签字或意见
- 若法务不认可 L1-L5 任一条，则对应补救措施先实施

**若公司无法务**，项目负责人需书面确认"接受 AI 整理的合规假设，风险自担"，记录到 AUDIT 文件。

#### 12.5.3 责任链

| 责任方 | 负责 |
|---|---|
| AI / 系统 | AIGC 标识、新闻 attribution、敏感词过滤、翻译 fact-check |
| 项目负责人 | 法务过审协调、品牌立场预审、授权 Go/No-Go |
| BD | 朋友圈转发的真实性（不虚假陈述、不谎称代言） |
| 公司法务（若有） | L1-L5 假设的法律意见签字 |

---

## §13 测试策略与验收

### 13.1 单元测试

- `test_poster.py`：视觉快照。mock 新闻 list → render → **pixel-hash diff 阈值明确**：
  - 使用 `Pillow ImageChops.difference` + 归一化 L1 差异
  - 阈值 `diff_ratio < 0.5%`（字体 subpixel 渲染波动通常 < 0.2%）
  - 首次运行生成 baseline 到 `tests/fixtures/posters/baseline.png`
  - 回归阶段超阈值 → 人工审核决定更新 baseline 或回退代码
- `test_hero_ranker.py`：fixture 5 条新闻（含敏感词 / 含数字 / 含名校） → 预期排序
- `test_copywriter.py`：生成 3 变体 → 校验长度 70 字内 + 不含敏感词 + 3 段不雷同（Jaccard 相似度 < 0.6）

### 13.2 集成测试

- `tests/integration/test_e2e.py`：假新闻 → 完整数据流 → 本地输出图 + 3 条消息文本 → 人工验收

### 13.3 Canary 策略（详见 §15.1）

- Day 1-3：本地 smoke，不发任何群
- Day 4-7：仅发 **BD 测试群**（新建 2-3 人）
- Day 8-14：发 BD 素材群（40 人），不发客户群
- Day 15+：客户群（反馈评估后决定）

### 13.4 回流指标

每周人工统计：
- BD 群消息转发数（看谁把图转到了其他群）
- BD 朋友圈采纳率（BD 自报 / 抽样截图）
- 客户群消息疲劳反馈（BD 反馈渠道）

### 13.5 压力与边界测试

| # | 场景 | 预期 |
|---|---|---|
| T1 | **连续 10 次触发 cron**（模拟重复调度） | 锁文件机制生效，只有第 1 次执行，其余跳过 |
| T2 | **5 个 cron 并发启动**（锁文件竞态） | 仅 1 个获得锁继续，其余记日志后退出 |
| T3 | **新闻 fetch 返回 0 条** | 不生成海报；发送"今日无新内容"的 markdown 兜底 |
| T4 | **新闻 fetch 返回 100 条**（数据异常多） | 正常取 top 5，其余忽略 |
| T5 | **单条新闻标题 500 字超长** | 模板 `-webkit-line-clamp` 截断，不破坏版面 |
| T6 | **海报渲染后 > 2MB** | 自动 JPEG q=85 转换；仍 > 2MB 则降级 markdown |
| T7 | **WeCom webhook 返回 45009（频率超限）** | 退避 60s 重试 1 次；仍失败则降级 |

### 13.5.1 Canary Stage 0 手动视觉验收 SOP

Stage 0（Day 1-3 本地 smoke）生成的 3 张图，**由项目负责人（neilding）按以下清单验收**，每张图在 `docs/CANARY_REVIEW_2026-04-XX.md` 记录：

| 检查项 | 通过标准 |
|---|---|
| Hero 中文标题 | 无事实错误、无敏感词、大字对比度目测不刺眼 |
| 英文副标题 | 原文正确、无乱码 |
| 内页 4 条 | 排版不破坏、文字无截断丢失 |
| 底部双 logo | 好居红 + 缴费墨稿比例正确 |
| AIGC 标识 | 右下角可见但不突兀 |
| 文件大小 | < 2MB |
| 整体感 | "我会愿意把这张图转到自己朋友圈吗？" 是/否 |

3 张图中 ≥ 2 张过 → Stage 0 通过，进 Stage 1。否则 iterate 模板。

### 13.6 故障注入测试

用 `pytest-mock` 强制注入以下异常，验证降级路径：

| # | 注入点 | 注入内容 | 预期降级路径 |
|---|---|---|---|
| F1 | `summarize_daily_news` | `TimeoutError` | 回退到纯英文标题 |
| F2 | `hero_ranker.score_shareability` | `APIError 402` | 取 top[0] 作为 hero |
| F3 | `copywriter.generate_variants` | `APIError 500` | 使用固定模板配文 |
| F4 | `poster_generator.render` | `PlaywrightTimeout` | 完全降级到 markdown |
| F5 | `send_wecom_image` | HTTP 500 | 重试 2 次后走 §10.3.2 补偿矩阵 |
| F6 | 字体加载 | `document.fonts.ready` 卡住 | 10s 后强制截图（降级）+ 告警 |

F1-F6 是 Day 1 验收必过项。`tests/fault_injection/test_resilience.py` 统一管理。

---

## §14 可观测性与告警

### 14.1 部署脚本

新增 `scripts/install_poster_deps.sh`：
```bash
pip install playwright jinja2
playwright install chromium --with-deps
python -c "from playwright.sync_api import sync_playwright; sync_playwright().start()"  # 冒烟
```

**上线前必须在服务器跑一次并截图输出证明成功**。

### 14.2 执行时间预算

| 阶段 | 预算 | 超时告警 |
|---|---|---|
| fetch + 过滤 | 10s | 20s |
| AI summarize | 8s | 15s |
| AI hero score | 5s | 10s |
| AI copywriter × 3 | 8s | 15s |
| Playwright render | 5s | 10s |
| 消息推送 | 3s | 5s |
| **总预算** | **≤ 40s** | **≥ 60s 告警** |

### 14.3 Volcengine 余额告警

`copywriter.py` 启动时调 Volcengine 账户接口（或日志统计方式）查余额：
```python
if balance_yuan < 10:
    send_wecom_alert(f"⚠️ Volcengine 余额 {balance_yuan}元 告急")
```

### 14.4 端到端监控

- 连续 3 次海报生成失败 → 企微告警群推送
- 单次 > 60s → 推送
- Volcengine API 返回 5xx → 推送

### 14.5 缓存与日志维护

- `news_cache.py` 启动时 cleanup: 删除 30 天前记录
- 服务器 crontab 新增：`logrotate /etc/logrotate.d/ai-news-bot`（daily, keep 14）

### 14.6 服务器物理资源监控

启动时检查：

```python
def pre_flight_check():
    # R19: 硬盘
    disk_used_pct = shutil.disk_usage('/').used / shutil.disk_usage('/').total
    if disk_used_pct > 0.8:
        alert_wecom(f"⚠️ 硬盘使用率 {disk_used_pct:.0%}")

    # R20: 内存
    free_mb = psutil.virtual_memory().available / 1024 / 1024
    if free_mb < 1000:
        alert_wecom(f"⚠️ 可用内存仅 {free_mb}MB，降级到 markdown")
        return "degrade_to_markdown"

    # R22: 锁文件（已在 bot_wecom.check_run_lock 存在，加时间戳校验）
    if lock_exists_and_fresh():
        return "skip"

    return "ok"
```

R21：上线前核验 `188.166.250.114` 是否与其他业务共享宿主：
```bash
ssh ops@188.166.250.114 'docker ps; systemctl list-units --type=service --state=running | head'
```
若有其他业务，Playwright 启动时加 `--max-old-space-size=512` 限制 Chrome 内存。

### 14.7 Volcengine 平台宕机预案

R14 只覆盖余额问题。平台本身 5xx/超时时（与余额无关），降级流程：

```python
try:
    resp = llm_client.chat.completions.create(...)
except (APIConnectionError, InternalServerError, APITimeoutError):
    alert_wecom("⚠️ Volcengine 平台异常，本次跑降级 markdown")
    return fallback_to_markdown()
```

判断信号：
- HTTP 5xx × 2 次连续 → 认定平台宕机
- 同一 `request_id` 超时 > 60s × 2 次 → 同上
- 触发后跳过 §10 的 3 次 AI 调用链，直接降级到原 markdown 日报并推送
- 跳过的日志标 `reason=platform_down`，便于事后排查

---

## §15 Canary + 配文变体 + 敏感词

### 15.1 Canary 日程

| 阶段 | 日期 | 范围 | 通过条件 |
|---|---|---|---|
| Stage 0 | Day 1-3 | 本地 smoke，不发群 | 生成 3 张合格海报，人工审阅无事实错误 |
| Stage 1 | Day 4-7 | **BD 测试群**（2-3 人） | 4 天无 BD 负面反馈，无合规事件 |
| Stage 2 | Day 8-14 | BD 素材群（40 人） | 无限流/封号事件，朋友圈采纳 ≥ 5 人次 |
| Stage 3 | Day 15+ | 客户群 | 项目负责人评估后 Go/No-Go |

任一阶段出问题 → 回滚到上一阶段 + 补强重跑。

### 15.2 配文变体

`copywriter.generate_variants(hero_news)` 返回 3 段：

| 变体 | 风格 | 示例 |
|---|---|---|
| 专业型 | 行业分析口吻 | "政策变动：密歇根州立大学州拨款或削减 60%，公立校财务压力再加剧——留学申请季家长需关注州校的奖学金供给变化。" |
| 数据型 | 数字驱动 | "60%！这是密歇根两所旗舰公立校可能面临的州拨款削减。对留学家庭意味着什么？" |
| 提问型 | 话题钩子 | "美国公立大学经费再次被砍，州校性价比还香吗？今早留学圈都在讨论这个。" |

BD 群消息文案："**今日 3 段朋友圈文案（BD 请择一）**：\n\n【专业型】...\n【数据型】...\n【提问型】..."

随机化指纹：每段后自动附"—— {yyyy.MM.dd}"，避免 40 人用完全相同的字符串。

### 15.3 敏感词流水线

```
hero 候选 5 条
 └─ 敏感词黑名单过滤（命中 → 得分 -10）
    └─ shareability score
       └─ 取最高分做 hero
          └─ 翻译
             └─ fact-check 二次 AI 校验
                └─ 通过 → 渲染
                └─ 不通过 → 降级
```

品牌立场预审（一次性）：
- 项目负责人拍板的"不评价 X 大学负面" 清单 → `config.BRAND_CONSTRAINTS`
- 命中立场冲突 → 同敏感词处理

---

---

# §16 管理层决策与 Override 记录

以下为项目负责人（neilding）在 Gate-1 评审第 3 轮（2026-04-24 15:30）做出的决策，具有与设计同等约束力。

## 16.1 法务过审通过 ✅

| 项 | 状态 |
|---|---|
| §12.5 L1（新闻编译合理使用） | 法务同意 |
| §12.5 L2（BD 朋友圈属个人分享，非商业广告） | 法务同意 |
| §12.5 L3（"AI 辅助生成"标识满足深度合成规定） | 法务同意（结合 §16.3） |
| §12.5 L4（新闻来源 attribution 已尽合理义务） | 法务同意 |
| §12.5 L5（好居/缴费双 logo 已获品牌授权） | 法务同意 |
| 过审人 | 项目负责人 neilding 确认法务意见 |
| 过审日期 | 2026-04-24 |

## 16.2 BD 访谈暂不执行（Override） ⚠️

| 项 | 记录 |
|---|---|
| 原设计要求 | §1.3 Pre-Day-1 BD 访谈（I1-I4） |
| 决策 | 暂不执行 |
| 负责人理由 | （项目负责人口头决策，未提供详细理由） |
| 承担风险 | 方案设计假设"BD 需要图 + 配文"未经真实验证。Day 1 上线后如 BD 实际不用该物料，Phase 1 投入沉没 |
| 缓解 | Canary Stage 1-2 在 BD 素材群观察 4-7 天的真实采纳情况；若采纳率 < 20%，Phase 2 停工重评 |
| 签字 | 项目负责人 neilding 知悉并接受风险 |

## 16.3 AIGC 显著标识字号决策（Override） ⚠️

| 项 | 记录 |
|---|---|
| 法规参考 | 《互联网信息服务深度合成管理规定》（2023-01）第 16-17 条："显著标识" |
| 法规明确性 | 无明确字号/大小规定；监管解释依赖个案 |
| 负责人决策 | 海报右下角 14px 浅灰字 "AI 辅助生成 · 异乡早咖啡"，"有就行，不要太明显" |
| 合规评价 | 技术上满足"标识存在"；监管灰度地带 |
| 承担风险 | 若未来监管强化或个案被处罚，需调整更显著标识 |
| 签字 | 项目负责人 neilding 知悉并接受风险 |

## 16.4 品牌立场预审清单（§1.3 I4 产出）

项目负责人提供的硬约束，用于 `config.BRAND_CONSTRAINTS`。与 §12.3 敏感词黑名单的差别：
- 敏感词黑名单 = 降权（得分 -10）但可能仍被选中
- **品牌立场 = 一票否决**（不会出现在 hero 也不会出现在内页 5 条）

### 16.4.1 地域政治硬约束

| # | 规则 | 实现 |
|---|---|---|
| C1 | **不提及台湾任何新闻** | 含 `台湾` / `Taiwan` / `臺灣` 的新闻整条拒绝（hero 和内页都不进） |
| C2 | **提及香港必须是"中国香港"** | 含 `香港` / `Hong Kong` / `HK` 的新闻，翻译/摘要 prompt 强制使用"中国香港" |

### 16.4.2 竞品硬约束

| # | 规则 | 实现 |
|---|---|---|
| C3 | 不提及异乡好居的任何竞争对手 | 命中 `UHOMES_COMPETITORS` 名单任一关键词整条拒绝 |
| C4 | 不提及异乡缴费的任何竞争对手（含易思汇） | 命中 `PAY_COMPETITORS` 名单任一关键词整条拒绝 |

### 16.4.3 竞品名单（起始版，待补全）

```python
# config.py 里的硬约束清单（由项目负责人 2026-04-24 确认）

UHOMES_COMPETITORS_SIMPLE = [
    # 海外直租中介：命中即拒
    'Student.com',
    'Casita',
    'Amber Student',
    'CollegeDorms',
    'Uniplaces',
    'Uniacco',
    'HooliHome', 'hoolihome',
    'HinoStudent', 'hinostudent',
]

# '自如' 单独处理：需同时出现租房语境关键词才拒绝
UHOMES_COMPETITOR_CONTEXTUAL = {
    '自如': ['租房', '公寓', '房源', '居住', '长租', '租赁', '出租', '房东', '租客'],
}

PAY_COMPETITORS = [
    '易思汇',
    '弛安汇',
    '比领快付',
    '秒汇',
]

# ⚠️ 非竞品（合作伙伴 / 潜在合作伙伴），不过滤：
# Flywire / Convera / PayMyTuition 等国际学费汇款平台
# 这些可以正常出现在新闻中
BRAND_PARTNERS_WHITELIST_NOTE = [
    'Flywire', 'Convera', 'PayMyTuition',
    # （此列表仅作 code comment 提醒，不会用于任何主动高亮；用于避免误加入黑名单）
]

GEOPOLITICAL_HARD_REJECT = [
    '台湾', 'Taiwan', '臺灣', 'TAIWAN',  # C1 全禁，含学术类
]

# C2 不是拒绝，是翻译约束；在 prompt 里处理
HK_NORMALIZATION_RULE = "所有对香港的提及必须表述为'中国香港'，不得单独使用'香港'或'Hong Kong'"
```

**实现细节**：

```python
def is_blocked_by_brand_constraints(title: str, description: str) -> tuple[bool, str]:
    """返回 (is_blocked, reason)"""
    content = f"{title} {description}".lower()

    # C1: 台湾全禁
    for kw in GEOPOLITICAL_HARD_REJECT:
        if kw.lower() in content:
            return True, f"C1-geopolitical:{kw}"

    # C3: 好居竞品 - 简单命中
    for kw in UHOMES_COMPETITORS_SIMPLE:
        if kw.lower() in content:
            return True, f"C3-competitor:{kw}"

    # C3: 好居竞品 - 上下文命中（如 '自如'）
    for kw, contexts in UHOMES_COMPETITOR_CONTEXTUAL.items():
        if kw in content and any(ctx in content for ctx in contexts):
            return True, f"C3-contextual:{kw}"

    # C4: 缴费竞品
    for kw in PAY_COMPETITORS:
        if kw.lower() in content:
            return True, f"C4-competitor:{kw}"

    return False, ""
```

**要点**：
- 所有简单关键词用 `keyword.lower() in content.lower()` 匹配（防 case 差异）
- `自如` 仅在租房语境（9 个关键词之一同时出现）才拒绝，避免误杀"自如应对""运转自如"等
- Flywire/Convera/PayMyTuition 为**合作伙伴**，严禁加入任何黑名单
- 拒绝时 `reason` 写入 §16.4.5 审计日志，便于复盘

### 16.4.4 品牌立场过滤器位置

在数据流中插入两处过滤：
1. `filter_education_relevant_news` 之后、`rank_education_news` 之前：整条拒绝 C1/C3/C4
2. `summarize_daily_news` 的 prompt 里：C2 香港规范化

```
fetch → filter_education_relevant → [C1/C3/C4 过滤] → rank → top 5
                                                       ↓
                                    summarize (prompt 含 C2 规则)
```

### 16.4.5 审计日志

每次被 C1/C3/C4 拒绝的新闻记录到 `logs/brand_filter_audit.log`（含时间/标题/命中关键词），便于：
- 复盘是否过度过滤
- 验证名单完整性
- 监管问询时举证

## 16.6 Override 责任声明

上述 16.2 和 16.3 的决策**由项目负责人做出并承担相应风险**。若后续发生：
- 因 BD 实际不用物料导致的 Phase 1 沉没成本
- 因 AIGC 标识不够显著导致的监管问题

**上述风险不属于设计缺陷，由管理层决策承担**。AI 评审已在 Gate-1 v3 指出相关风险。

---

## 版本变更记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-04-24 10:00 | v2.0-draft | 基于 grill-me 对话首版 |
| 2026-04-24 14:40 | v2.1 | Gate-1 第 1 轮补强：新增 §10-§15，修订 §6 风险清单，补强 §7 验收 |
| 2026-04-24 15:00 | v2.2 | Gate-1 第 2 轮补强：§1.3 BD 共识 / §10.3 分布式事务 / §12.5 法律合规 / §13.5 压力 / §13.6 故障注入 / §14.6 物理资源 |
| 2026-04-24 15:30 | v2.3 | Gate-1 第 3 轮补强 + §16 管理决策记录（法务同意 / BD 访谈暂停 / AIGC 标识决策） |
| 2026-04-24 15:50 | v2.4 | §16.4 品牌立场预审清单：C1 不提台湾 / C2 香港必为"中国香港" / C3 不提好居竞品 / C4 不提缴费竞品 |
| 2026-04-24 16:00 | v2.5 | §16.4.3 竞品名单落地：好居 9 个 + 自如 / 缴费 4 个 |
| 2026-04-24 16:10 | **v2.6** | **§16.4.3 精细化**：自如改为上下文匹配（仅租房语境拒）；台湾全禁；Flywire/Convera/PayMyTuition 明确为**合作伙伴**不列入黑名单 |
