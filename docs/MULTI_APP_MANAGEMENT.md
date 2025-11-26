# 多应用管理指南

## 概述

本文档说明如何在同一台 DigitalOcean 服务器上管理多个应用程序，包括 AI 新闻机器人和其他现有程序。

## 应用隔离策略

### 核心原则

每个应用都应该有：
- ✅ 独立的目录结构
- ✅ 独立的 Python 虚拟环境
- ✅ 独立的依赖包
- ✅ 独立的环境变量配置
- ✅ 独立的日志文件
- ✅ 独立的 cron 任务

### 推荐目录结构

```
/opt/apps/                          # 统一的应用根目录
├── ai-news-bot/                    # AI 新闻机器人
│   ├── code/                       # Git 仓库
│   ├── venv/                       # Python 虚拟环境
│   ├── logs/                       # 应用日志
│   └── .env                        # 环境变量（600 权限）
│
├── app-name-1/                     # 第一个应用
│   ├── code/
│   ├── venv/
│   ├── logs/
│   └── .env
│
└── app-name-2/                     # 第二个应用
    ├── code/
    ├── venv/
    ├── logs/
    └── .env
```

## 检查现有程序

### 步骤 1: 查看现有程序位置

```bash
# 连接到服务器
ssh root@your-digitalocean-ip

# 查找 Python 进程
ps aux | grep python

# 查看 cron 任务
crontab -l

# 查找常见的应用目录
ls -la /home/
ls -la /opt/
ls -la /var/www/
ls -la /root/
```

### 步骤 2: 记录现有程序信息

为每个现有程序记录以下信息：

**程序 1：**
- 名称：`_________________`
- 位置：`_________________`
- Python 版本：`_________________`
- 虚拟环境位置：`_________________`
- 执行方式：`[ ] cron  [ ] systemd  [ ] 手动  [ ] 其他`
- 执行时间：`_________________`
- 日志位置：`_________________`

**程序 2：**
- 名称：`_________________`
- 位置：`_________________`
- Python 版本：`_________________`
- 虚拟环境位置：`_________________`
- 执行方式：`[ ] cron  [ ] systemd  [ ] 手动  [ ] 其他`
- 执行时间：`_________________`
- 日志位置：`_________________`

### 步骤 3: 检查资源使用情况

```bash
# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查 CPU 使用
top -bn1 | head -20

# 检查各目录大小
du -sh /home/* /opt/* /var/* 2>/dev/null | sort -h
```

## 部署方案选择

### 方案 A: 统一管理（推荐）

**适用场景：**
- 现有程序也是 Python 应用
- 希望统一管理所有应用
- 愿意迁移现有程序到新结构

**操作步骤：**

1. **备份现有程序**
   ```bash
   # 备份程序 1
   tar -czf ~/backup-app1-$(date +%Y%m%d).tar.gz /path/to/app1/
   
   # 备份程序 2
   tar -czf ~/backup-app2-$(date +%Y%m%d).tar.gz /path/to/app2/
   
   # 备份 crontab
   crontab -l > ~/crontab-backup-$(date +%Y%m%d).txt
   ```

2. **使用部署脚本重新部署现有程序**
   ```bash
   # 部署程序 1
   deploy-app.sh app1 https://github.com/user/app1.git "0 8 * * *"
   
   # 部署程序 2
   deploy-app.sh app2 https://github.com/user/app2.git "*/30 * * * *"
   
   # 部署 AI 新闻机器人
   deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
   ```

3. **配置环境变量**
   ```bash
   # 为每个应用配置 .env
   nano /opt/apps/app1/.env
   nano /opt/apps/app2/.env
   nano /opt/apps/ai-news-bot/.env
   ```

4. **测试所有应用**
   ```bash
   # 测试程序 1
   cd /opt/apps/app1/code
   /opt/apps/app1/venv/bin/python3 main.py
   
   # 测试程序 2
   cd /opt/apps/app2/code
   /opt/apps/app2/venv/bin/python3 main.py
   
   # 测试 AI 新闻机器人
   cd /opt/apps/ai-news-bot/code
   /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py
   ```

5. **清理旧文件（确认新程序运行正常后）**
   ```bash
   # 删除旧的程序目录
   rm -rf /old/path/to/app1/
   rm -rf /old/path/to/app2/
   ```

**优点：**
- 统一的目录结构，易于管理
- 所有应用使用相同的部署流程
- 便于未来添加新应用
- 清晰的隔离和组织

**缺点：**
- 需要迁移现有程序
- 需要一些时间进行迁移和测试

### 方案 B: 保持现有程序不动

**适用场景：**
- 现有程序运行稳定，不想改动
- 现有程序不是 Python 应用
- 只想快速部署新的 AI 新闻机器人

**操作步骤：**

1. **只部署 AI 新闻机器人**
   ```bash
   deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
   ```

2. **配置环境变量**
   ```bash
   nano /opt/apps/ai-news-bot/.env
   ```

3. **测试新程序**
   ```bash
   cd /opt/apps/ai-news-bot/code
   /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py
   ```

4. **验证不影响现有程序**
   ```bash
   # 检查现有程序的 cron 任务
   crontab -l
   
   # 确认现有程序仍在运行
   ps aux | grep python
   ```

**优点：**
- 最小化改动
- 快速部署
- 现有程序不受影响

**缺点：**
- 目录结构不统一
- 管理相对复杂
- 未来添加新应用可能混乱

### 方案 C: 混合方案

**适用场景：**
- 部分程序适合迁移，部分不适合
- 逐步过渡到统一管理

**操作步骤：**

1. **先部署 AI 新闻机器人**
   ```bash
   deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
   ```

2. **逐步迁移现有程序**
   - 先迁移一个程序，测试稳定后
   - 再迁移下一个程序
   - 保持灵活性

## 资源分配建议

### 内存分配

假设服务器有 2GB 内存：

| 应用 | 预估内存 | 说明 |
|------|---------|------|
| 系统 | 300MB | 操作系统基础服务 |
| AI 新闻机器人 | 400MB | 包含 AI API 调用 |
| 现有程序 1 | 300MB | 根据实际情况调整 |
| 现有程序 2 | 300MB | 根据实际情况调整 |
| 缓冲 | 700MB | 预留空间 |

**监控内存使用：**
```bash
# 实时监控
watch -n 5 free -h

# 查看各进程内存使用
ps aux --sort=-%mem | head -10
```

### 磁盘空间分配

假设服务器有 20GB 磁盘：

| 用途 | 预估空间 | 说明 |
|------|---------|------|
| 系统 | 5GB | Ubuntu 系统文件 |
| AI 新闻机器人 | 2GB | 代码 + 依赖 + 日志 |
| 现有程序 1 | 2GB | 根据实际情况调整 |
| 现有程序 2 | 2GB | 根据实际情况调整 |
| 日志和缓存 | 3GB | 各应用日志累积 |
| 预留空间 | 6GB | 系统更新和临时文件 |

**监控磁盘使用：**
```bash
# 查看磁盘使用
df -h

# 查看各目录大小
du -sh /opt/apps/* | sort -h

# 清理旧日志
find /opt/apps/*/logs/ -name "*.gz" -mtime +30 -delete
```

### CPU 和执行时间规划

避免所有程序同时执行，合理安排 cron 时间：

```bash
# 示例时间安排
0 8 * * *   # 程序 1 - 每天 8:00 AM
0 9 * * *   # AI 新闻机器人 - 每天 9:00 AM
0 10 * * *  # 程序 2 - 每天 10:00 AM

# 或者错开分钟
0 9 * * *   # AI 新闻机器人 - 9:00
15 9 * * *  # 程序 1 - 9:15
30 9 * * *  # 程序 2 - 9:30
```

## Cron 任务管理

### 查看所有 Cron 任务

```bash
crontab -l
```

### 推荐的 Cron 组织方式

```bash
# 在 crontab 中添加注释，便于管理
crontab -e

# 添加内容：
# ============================================
# AI News Bot - Daily news aggregation
# ============================================
0 9 * * * cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /opt/apps/ai-news-bot/logs/app.log 2>&1

# ============================================
# App 1 - Description
# ============================================
0 8 * * * cd /opt/apps/app1/code && /opt/apps/app1/venv/bin/python3 main.py >> /opt/apps/app1/logs/app.log 2>&1

# ============================================
# App 2 - Description
# ============================================
*/30 * * * * cd /opt/apps/app2/code && /opt/apps/app2/venv/bin/python3 main.py >> /opt/apps/app2/logs/app.log 2>&1
```

## 日志管理

### 统一日志查看

创建一个便捷脚本查看所有应用日志：

```bash
# 创建日志查看脚本
nano /usr/local/bin/view-logs.sh
```

添加内容：

```bash
#!/bin/bash

echo "=== AI News Bot Logs ==="
tail -n 20 /opt/apps/ai-news-bot/logs/app.log
echo ""

echo "=== App 1 Logs ==="
tail -n 20 /opt/apps/app1/logs/app.log
echo ""

echo "=== App 2 Logs ==="
tail -n 20 /opt/apps/app2/logs/app.log
```

```bash
# 设置权限
chmod +x /usr/local/bin/view-logs.sh

# 使用
view-logs.sh
```

### 日志轮转配置

确保所有应用都配置了日志轮转：

```bash
# 查看 logrotate 配置
ls -la /etc/logrotate.d/

# 应该看到：
# ai-news-bot
# app1
# app2
```

## 监控和告警

### 创建健康检查脚本

```bash
nano /usr/local/bin/health-check.sh
```

添加内容：

```bash
#!/bin/bash

echo "=== System Health Check ==="
echo "Date: $(date)"
echo ""

echo "=== Disk Usage ==="
df -h | grep -E "Filesystem|/dev/"
echo ""

echo "=== Memory Usage ==="
free -h
echo ""

echo "=== Running Python Processes ==="
ps aux | grep python | grep -v grep
echo ""

echo "=== Cron Jobs ==="
crontab -l | grep -v "^#" | grep -v "^$"
echo ""

echo "=== Recent Logs (Last 5 lines each) ==="
for app in ai-news-bot app1 app2; do
    if [ -f "/opt/apps/$app/logs/app.log" ]; then
        echo "--- $app ---"
        tail -n 5 /opt/apps/$app/logs/app.log
        echo ""
    fi
done
```

```bash
chmod +x /usr/local/bin/health-check.sh

# 运行健康检查
health-check.sh
```

## 故障隔离

### 如果某个应用出问题

由于应用完全隔离，一个应用的问题不会影响其他应用：

```bash
# 禁用有问题的应用的 cron 任务
crontab -e
# 注释掉该应用的行

# 其他应用继续正常运行
```

### 快速恢复

```bash
# 重新部署有问题的应用
deploy-app.sh problem-app https://github.com/user/problem-app.git "0 9 * * *"

# 或回滚到备份
tar -xzf ~/backup-problem-app-20251125.tar.gz -C /
```

## 最佳实践

### 1. 命名规范

使用清晰的应用名称：
- ✅ `ai-news-bot`
- ✅ `weather-notifier`
- ✅ `data-sync-service`
- ❌ `app1`, `test`, `my-app`

### 2. 文档记录

为每个应用创建简单的 README：

```bash
# 在每个应用的 code 目录
nano /opt/apps/ai-news-bot/code/DEPLOYMENT.md
```

记录：
- 应用用途
- 执行时间
- 依赖的外部服务
- 环境变量说明
- 故障联系人

### 3. 定期备份

```bash
# 创建备份脚本
nano /usr/local/bin/backup-apps.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# 备份所有应用
for app in ai-news-bot app1 app2; do
    if [ -d "/opt/apps/$app" ]; then
        tar -czf $BACKUP_DIR/${app}-${DATE}.tar.gz /opt/apps/$app/
        echo "Backed up $app"
    fi
done

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
chmod +x /usr/local/bin/backup-apps.sh

# 添加到 crontab（每天凌晨 2 点备份）
crontab -e
# 添加：0 2 * * * /usr/local/bin/backup-apps.sh
```

### 4. 版本控制

在每个应用的 .env 文件中记录版本信息：

```bash
# Application Version
APP_VERSION=1.0.0
DEPLOYED_DATE=2025-11-25
DEPLOYED_BY=admin
```

## 常见问题

### Q: 多个应用会不会相互影响？

**A:** 不会。每个应用有独立的：
- 虚拟环境（依赖包隔离）
- 环境变量（配置隔离）
- 日志文件（日志隔离）
- 执行时间（资源隔离）

### Q: 如何确保不会同时执行导致资源不足？

**A:** 合理安排 cron 时间，错开执行：
```bash
0 8 * * *   # App 1
0 9 * * *   # AI News Bot
0 10 * * *  # App 2
```

### Q: 如果一个应用崩溃了怎么办？

**A:** 其他应用不受影响，只需要修复崩溃的应用：
```bash
# 查看日志
tail -f /opt/apps/problem-app/logs/app.log

# 重新部署
deploy-app.sh problem-app https://github.com/user/repo.git "0 9 * * *"
```

### Q: 可以在同一台服务器上运行多少个应用？

**A:** 取决于：
- 服务器配置（CPU、内存、磁盘）
- 每个应用的资源需求
- 执行频率

对于 2GB 内存的服务器，建议不超过 3-5 个轻量级应用。

## 总结

**推荐方案：**
- 如果现有程序也是 Python 应用 → 选择**方案 A（统一管理）**
- 如果现有程序运行稳定不想动 → 选择**方案 B（保持不动）**
- 如果不确定 → 先选择**方案 B**，之后逐步迁移到**方案 A**

**关键要点：**
1. ✅ 每个应用完全隔离
2. ✅ 统一的目录结构便于管理
3. ✅ 合理安排执行时间避免资源冲突
4. ✅ 定期备份和监控
5. ✅ 清晰的文档和命名

---

**文档版本：** 1.0.0  
**最后更新：** 2025年11月  
**相关文档：** 
- [迁移指南](./MIGRATE_TO_DIGITALOCEAN.md)
- [部署脚本使用指南](./DEPLOY_SCRIPT_GUIDE.md)
