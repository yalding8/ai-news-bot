# 缓存同步问题解决方案

## 问题描述

当前系统存在两个独立的运行环境：
1. **GitHub Actions**: 每天 00:30 UTC (北京时间 08:30) 自动运行
2. **服务器 Cron**: 可能在 `188.166.250.114` 上也配置了定时任务

两个环境使用独立的 `.news_cache.json` 文件，导致：
- ❌ 新闻可能被重复推送
- ❌ 缓存数据不一致
- ❌ 无法准确追踪已推送的新闻

## 解决方案

### ✅ 推荐方案：使用环境变量控制运行

在代码中添加环境检测，确保同一时间只有一个环境运行。

#### 实施步骤：

1. **在 `bot_wecom.py` 中添加运行环境检测**
2. **在 `.env` 文件中配置 `RUN_ENVIRONMENT` 变量**
3. **禁用其中一个定时任务（推荐禁用服务器 cron）**

### 备选方案

#### 方案 A: 完全禁用服务器 Cron
```bash
# SSH 到服务器
ssh root@188.166.250.114

# 查看现有 cron 任务
crontab -l

# 如果有 ai-news-bot 相关任务，注释掉
crontab -e
# 在相关行前加 # 注释

# 或者直接删除
crontab -l | grep -v "ai-news-bot" | crontab -
```

#### 方案 B: 只保留服务器 Cron，禁用 GitHub Actions
```yaml
# 在 .github/workflows/daily_news.yml 中禁用 schedule 触发
# 注释掉或删除以下内容：
# on:
#   schedule:
#     - cron: '30 0 * * *'
```

## 当前状态检查

运行以下命令检查当前配置：

```bash
# 1. 检查 GitHub Actions 是否启用
gh workflow list  # 或在 GitHub 网页查看

# 2. 检查服务器 cron（需要 SSH 到服务器）
ssh root@188.166.250.114 'crontab -l | grep ai-news'
```

## 建议

**推荐使用 GitHub Actions**，理由：
1. ✅ 自动备份缓存
2. ✅ 完整的运行日志
3. ✅ 更容易管理和调试
4. ✅ 无需维护服务器

如果选择 GitHub Actions，请在服务器上执行：
```bash
ssh root@188.166.250.114 'crontab -l | grep -v "ai-news-bot" | crontab -'
```
