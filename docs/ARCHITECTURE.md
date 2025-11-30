# 🧭 架构与功能总览

本文汇总当前「AI 新闻机器人」的核心能力、数据流和运行方式，便于快速理解与维护。已精简为 **企业微信推送** 单一通道，并在 DigitalOcean 服务器上验证运行。

---

## 系统概览
- **目标**：每天自动聚合真实新闻 → AI 总结 → 推送到企业微信群。
- **运行方式**：定时任务/手动触发执行 `bot_wecom.py`，单次跑完即退出。
- **部署形态**：Ubuntu + Python 3.11（DigitalOcean Droplet 已实测），虚拟环境隔离依赖。

## 关键模块
- `bot_wecom.py`：主流程，按 `ACTIVE_TOPICS` 并发获取新闻、去重、AI 总结，拼接 Markdown 消息并推送到多 Webhook。
- `news_fetcher.py`：新闻聚合
  - 源：天行数据 API（可选）、RSS 列表、NewsAPI（可选）。
  - 处理：并行抓取 → 标题去重 + 7 天时效 → 质量打分（关键词/摘要/可信来源/URL）→ 按来源多样性过滤。
  - 输出：高质量新闻列表和用于 AI 的格式化文本。
- `ai_summarizer.py`：DeepSeek Chat 调用，按主题提示要求逐条总结、保留来源、使用 emoji。
- `news_cache.py`：去重缓存，按标题+URL 生成哈希，24 小时内不重复推送，`.news_cache.json` 持久化。
- `config.py`：环境变量加载、日志、主题/关键词配置（AI、财经、创业、教育细分、PBSA、Uhomes），Webhook 多通道解析。
- `start.py`：薄入口，直接调用 `bot_wecom.main()`。
- `scripts/smoke_wecom.py`：本地假数据 smoke，验证格式与依赖，无网络请求。

## 数据流（单次执行）
1) 读取环境变量（DeepSeek API Key、Webhook、多主题配置等）。  
2) 为每个主题并发抓取新闻（API + RSS + NewsAPI）。  
3) 去重 & 时效过滤 → 质量评分排序 → 来源多样性约束。  
4) 缓存过滤 24 小时内已推送新闻。  
5) 生成 AI 总结（DeepSeek）并标记缓存。  
6) 汇总 Markdown 消息，逐个 Webhook 发送到企业微信群。

## 配置要点
- 必填：`DEEPSEEK_API_KEY`、`WECOM_WEBHOOK_URL`（可多条逗号分隔）。  
- 可选：`TIANAPI_KEY`、`NEWSAPI_KEY`（提升真实新闻覆盖）。  
- 主题开关：`ACTIVE_TOPICS`（默认 `ai,education`）。  
- `.env.example` 提供模板；`.news_cache.json` 保存去重状态，需确保运行用户具备写权限。

## 运行与部署（推荐做法）
- **本地/服务器测试**：`python3 bot_wecom.py`。  
- **定时任务**：`0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1`。  
- **一键发布**：`bash publish.sh "feat: ..."`（打包推送 GitHub + 服务器部署，当前 `.deployrc` 面向 DigitalOcean）。

## 已知取舍
- 仅保留企业微信通道；Telegram/邮件相关文档与脚本已停用。  
- 缓存为本地文件，不适合多实例共享场景。  
- Dockerfile 默认命令需自行指定入口（建议改为 `python3 bot_wecom.py` 或自定义调度脚本）。

---

维护者可先阅读本文件，再查阅 `README.md` 以获取操作指引。***
