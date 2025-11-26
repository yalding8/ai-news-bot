# AI 新闻机器人迁移到 DigitalOcean 指南

## 概述

本文档提供了将 AI 新闻机器人从阿里云迁移到 DigitalOcean 服务器的完整步骤。迁移过程使用通用部署脚本 `deploy-app.sh`，实现自动化部署和配置。

**迁移目标：**
- ✅ 将应用从阿里云迁移到 DigitalOcean
- ✅ 保持原有功能完整性
- ✅ 配置自动化定时任务（每天 9:00 AM 执行）
- ✅ 确保日志记录和监控正常

**预计时间：** 30-60 分钟

## 前置准备

### 1. DigitalOcean 服务器要求

**推荐配置：**
- **操作系统：** Ubuntu 22.04 LTS
- **CPU：** 2 核心
- **内存：** 2 GB RAM
- **存储：** 20 GB SSD
- **网络：** 稳定的互联网连接

**创建 Droplet：**
1. 登录 [DigitalOcean 控制台](https://cloud.digitalocean.com/)
2. 点击 "Create" → "Droplets"
3. 选择 Ubuntu 22.04 LTS
4. 选择合适的配置（推荐 Basic Plan - $12/月）
5. 选择数据中心区域（推荐选择离你最近的区域）
6. 添加 SSH 密钥（强烈推荐）
7. 点击 "Create Droplet"

### 2. 本地准备

**需要的信息：**
- DigitalOcean 服务器 IP 地址
- SSH 访问权限（密钥或密码）
- 现有的 `.env` 配置文件（包含 API 密钥）
- Git 仓库地址

**需要的文件：**
```bash
# 从当前项目获取
- deploy-app.sh（部署脚本）
- .env（环境变量配置）
```

## 迁移步骤

### 步骤 1: 连接到 DigitalOcean 服务器

使用 SSH 连接到你的新服务器：

```bash
# 使用 SSH 密钥连接（推荐）
ssh root@your-digitalocean-ip

# 或使用密码连接
ssh root@your-digitalocean-ip
# 输入密码
```

**验证连接：**
```bash
# 检查系统信息
uname -a
# 应该显示 Ubuntu 22.04

# 检查网络连接
ping -c 3 github.com
```

### 步骤 2: 安装必需软件

在服务器上安装所需的软件包：

```bash
# 更新系统包
apt update && apt upgrade -y

# 安装必需软件
apt install -y python3 python3-pip python3-venv git logrotate

# 验证安装
python3 --version  # 应该显示 Python 3.10+
git --version      # 应该显示 Git 2.34+
```

### 步骤 3: 上传部署脚本

从本地机器上传部署脚本到服务器：

```bash
# 在本地机器上执行（打开新终端）
cd /path/to/ai-news-bot

# 上传部署脚本
scp deploy-app.sh root@your-digitalocean-ip:/usr/local/bin/

# 如果使用 SSH 密钥
scp -i ~/.ssh/your-key deploy-app.sh root@your-digitalocean-ip:/usr/local/bin/
```

**在服务器上设置权限：**
```bash
# 回到服务器终端
chmod +x /usr/local/bin/deploy-app.sh

# 验证脚本可执行
deploy-app.sh
# 应该显示使用说明
```

### 步骤 4: 配置 Git 访问（如果使用私有仓库）

如果你的仓库是私有的，需要配置 SSH 密钥：

```bash
# 在服务器上生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按 Enter 使用默认路径
# 可以设置密码或留空

# 显示公钥
cat ~/.ssh/id_ed25519.pub

# 复制输出的公钥
```

**添加到 GitHub：**
1. 访问 GitHub → Settings → SSH and GPG keys
2. 点击 "New SSH key"
3. 粘贴公钥内容
4. 点击 "Add SSH key"

**测试连接：**
```bash
ssh -T git@github.com
# 应该显示：Hi username! You've successfully authenticated...
```

### 步骤 5: 执行部署

使用部署脚本部署 AI 新闻机器人：

```bash
# 部署应用（使用 HTTPS URL）
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"

# 或使用 SSH URL（如果配置了 SSH 密钥）
deploy-app.sh ai-news-bot git@github.com:yalding8/ai-news-bot.git "0 9 * * *"
```

**部署过程说明：**
- 创建目录结构 `/opt/apps/ai-news-bot/`
- 克隆 Git 仓库到 `code/` 目录
- 创建 Python 虚拟环境在 `venv/` 目录
- 安装依赖包
- 创建 `.env` 模板文件
- 配置 cron 定时任务（每天 9:00 AM）
- 设置日志轮转

**预期输出：**
```
==========================================
  Universal Python App Deployment
==========================================

→ Validating inputs...
✓ Application name validated: ai-news-bot
✓ Git URL validated: https://github.com/yalding8/ai-news-bot.git
✓ Cron schedule validated: 0 9 * * *
→ Setting up directory structure...
✓ Created application directory: /opt/apps/ai-news-bot
...
✓ Deployment completed successfully!
==========================================
```

### 步骤 6: 配置环境变量

编辑 `.env` 文件，添加你的 API 密钥和配置：

```bash
# 编辑环境变量文件
nano /opt/apps/ai-news-bot/.env
```

**添加以下配置：**
```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# 企业微信 Webhook 配置
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key

# 天行数据 API 配置
TIANAPI_KEY=your-tianapi-key-here

# 活跃主题配置
ACTIVE_TOPICS=ai,education

# 可选：调试模式
DEBUG=false
```

**保存并退出：**
- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

**验证权限：**
```bash
ls -la /opt/apps/ai-news-bot/.env
# 应该显示：-rw------- 1 root root ... .env
# 权限必须是 600
```

### 步骤 7: 测试手动执行

在配置 cron 自动执行之前，先手动测试应用：

```bash
# 进入代码目录
cd /opt/apps/ai-news-bot/code

# 使用虚拟环境运行应用
/opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py

# 检查退出码
echo $?
# 应该返回 0 表示成功
```

**预期行为：**
- 应用应该成功获取新闻
- 生成 AI 摘要
- 发送消息到企业微信
- 在终端显示执行日志

**如果出现错误：**
- 检查 API 密钥是否正确
- 检查网络连接
- 查看错误信息并参考故障排查部分

### 步骤 8: 验证 Cron 任务

检查 cron 任务是否正确配置：

```bash
# 查看 cron 任务列表
crontab -l

# 应该看到类似以下内容：
# ai-news-bot - Automated task
# 0 9 * * * cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /opt/apps/ai-news-bot/logs/app.log 2>&1
```

**验证 cron 服务状态：**
```bash
systemctl status cron
# 应该显示 active (running)
```

**检查时区设置：**
```bash
timedatectl

# 如果需要更改时区（例如改为上海时区）
timedatectl set-timezone Asia/Shanghai
```

### 步骤 9: 查看日志

检查应用日志以确保一切正常：

```bash
# 查看日志文件
tail -f /opt/apps/ai-news-bot/logs/app.log

# 或查看最近 50 行
tail -n 50 /opt/apps/ai-news-bot/logs/app.log

# 搜索错误
grep -i "error\|failed\|exception" /opt/apps/ai-news-bot/logs/app.log
```

### 步骤 10: 等待自动执行

cron 任务将在每天 9:00 AM 自动执行。你可以：

1. **等待第二天 9:00 AM**，然后检查日志
2. **或者临时修改 cron 时间**进行测试：

```bash
# 编辑 crontab
crontab -e

# 修改时间为几分钟后（例如当前时间是 14:30，改为 14:35）
# 35 14 * * * cd /opt/apps/ai-news-bot/code && ...

# 保存并等待执行

# 几分钟后检查日志
tail -f /opt/apps/ai-news-bot/logs/app.log

# 测试完成后，改回正确的时间
crontab -e
# 改回：0 9 * * *
```

## 迁移验证清单

完成迁移后，使用以下清单验证：

- [ ] **服务器连接正常**
  ```bash
  ssh root@your-digitalocean-ip
  ```

- [ ] **目录结构正确**
  ```bash
  ls -la /opt/apps/ai-news-bot/
  # 应该看到：code/, venv/, logs/, .env
  ```

- [ ] **虚拟环境可用**
  ```bash
  /opt/apps/ai-news-bot/venv/bin/python3 --version
  ```

- [ ] **依赖包已安装**
  ```bash
  /opt/apps/ai-news-bot/venv/bin/pip list
  # 应该看到：requests, python-dotenv, 等
  ```

- [ ] **.env 文件配置正确**
  ```bash
  cat /opt/apps/ai-news-bot/.env
  # 检查所有 API 密钥
  ```

- [ ] **.env 文件权限正确**
  ```bash
  stat /opt/apps/ai-news-bot/.env
  # 权限应该是 600
  ```

- [ ] **手动执行成功**
  ```bash
  cd /opt/apps/ai-news-bot/code
  /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py
  # 应该成功发送消息
  ```

- [ ] **Cron 任务已配置**
  ```bash
  crontab -l | grep ai-news-bot
  ```

- [ ] **日志文件可写入**
  ```bash
  ls -la /opt/apps/ai-news-bot/logs/app.log
  ```

- [ ] **时区设置正确**
  ```bash
  timedatectl
  # 检查时区是否为你所在地区
  ```

## 故障排查

### 问题 1: 部署脚本执行失败

**症状：**
```
ERROR: Failed to clone Git repository
```

**可能原因和解决方案：**

1. **网络连接问题**
   ```bash
   # 测试网络
   ping -c 3 github.com
   
   # 如果无法连接，检查防火墙设置
   ufw status
   ```

2. **Git URL 错误**
   ```bash
   # 验证 Git URL
   git ls-remote https://github.com/yalding8/ai-news-bot.git
   ```

3. **私有仓库权限问题**
   ```bash
   # 确保 SSH 密钥已添加到 GitHub
   ssh -T git@github.com
   ```

### 问题 2: 依赖安装失败

**症状：**
```
ERROR: Failed to install dependencies
```

**解决方案：**

```bash
# 手动激活虚拟环境
source /opt/apps/ai-news-bot/venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 手动安装依赖（查看详细输出）
pip install -r /opt/apps/ai-news-bot/code/requirements.txt -v

# 如果某个包安装失败，可能需要安装系统依赖
# 例如：
apt install -y python3-dev build-essential
```

### 问题 3: 应用执行失败

**症状：**
应用运行时报错或无法发送消息

**诊断步骤：**

1. **检查环境变量**
   ```bash
   cat /opt/apps/ai-news-bot/.env
   # 确保所有 API 密钥正确
   ```

2. **检查 API 密钥有效性**
   ```bash
   # 测试 DeepSeek API
   curl -X POST https://api.deepseek.com/v1/chat/completions \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
   ```

3. **查看详细错误日志**
   ```bash
   cd /opt/apps/ai-news-bot/code
   /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py 2>&1 | tee debug.log
   ```

4. **检查 python-dotenv 是否安装**
   ```bash
   /opt/apps/ai-news-bot/venv/bin/pip show python-dotenv
   ```

### 问题 4: Cron 任务不执行

**症状：**
到了 9:00 AM 但应用没有运行

**诊断步骤：**

1. **检查 cron 服务**
   ```bash
   systemctl status cron
   
   # 如果未运行，启动它
   systemctl start cron
   systemctl enable cron
   ```

2. **检查 cron 日志**
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

3. **验证时区**
   ```bash
   timedatectl
   
   # cron 使用系统时区
   # 如果时区不对，修改它
   timedatectl set-timezone Asia/Shanghai
   ```

4. **手动测试 cron 命令**
   ```bash
   # 复制 crontab 中的命令并手动执行
   cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /opt/apps/ai-news-bot/logs/app.log 2>&1
   
   # 检查是否有错误
   echo $?
   ```

5. **检查 cron 环境变量**
   ```bash
   # 编辑 crontab
   crontab -e
   
   # 在 cron 任务前添加 PATH
   PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
   0 9 * * * cd /opt/apps/ai-news-bot/code && ...
   ```

### 问题 5: 日志文件未创建

**症状：**
`/opt/apps/ai-news-bot/logs/app.log` 不存在

**解决方案：**

```bash
# 检查目录权限
ls -ld /opt/apps/ai-news-bot/logs/

# 手动创建日志文件
touch /opt/apps/ai-news-bot/logs/app.log
chmod 644 /opt/apps/ai-news-bot/logs/app.log

# 测试写入
echo "Test log entry" >> /opt/apps/ai-news-bot/logs/app.log
```

### 问题 6: 磁盘空间不足

**症状：**
```
ERROR: No space left on device
```

**解决方案：**

```bash
# 检查磁盘使用情况
df -h

# 查找大文件
du -sh /opt/apps/* | sort -h

# 清理旧日志
find /opt/apps/*/logs/ -name "*.gz" -mtime +30 -delete

# 清理 pip 缓存
/opt/apps/ai-news-bot/venv/bin/pip cache purge

# 清理系统包缓存
apt clean
```

### 问题 7: 企业微信消息发送失败

**症状：**
应用运行但消息未发送到企业微信

**诊断步骤：**

1. **验证 Webhook URL**
   ```bash
   # 测试 Webhook
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"msgtype":"text","text":{"content":"测试消息"}}'
   ```

2. **检查 Webhook 配置**
   ```bash
   cat /opt/apps/ai-news-bot/.env | grep WECOM_WEBHOOK_URL
   # 确保 URL 完整且正确
   ```

3. **查看应用日志**
   ```bash
   grep -i "wecom\|webhook" /opt/apps/ai-news-bot/logs/app.log
   ```

## 日常维护

### 更新应用代码

当你更新了 GitHub 仓库的代码后：

```bash
# SSH 连接到服务器
ssh root@your-digitalocean-ip

# 重新运行部署脚本
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"

# 或手动更新
cd /opt/apps/ai-news-bot/code
git pull
/opt/apps/ai-news-bot/venv/bin/pip install -r requirements.txt --upgrade
```

### 查看日志

```bash
# 实时查看日志
tail -f /opt/apps/ai-news-bot/logs/app.log

# 查看最近的日志
tail -n 100 /opt/apps/ai-news-bot/logs/app.log

# 搜索特定内容
grep "关键词" /opt/apps/ai-news-bot/logs/app.log

# 查看今天的日志
grep "$(date +%Y-%m-%d)" /opt/apps/ai-news-bot/logs/app.log
```

### 修改执行时间

```bash
# 编辑 crontab
crontab -e

# 修改时间（例如改为每天 8:00 AM）
0 8 * * * cd /opt/apps/ai-news-bot/code && ...

# 或重新运行部署脚本
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 8 * * *"
```

### 备份配置

```bash
# 备份 .env 文件
cp /opt/apps/ai-news-bot/.env ~/ai-news-bot-env-backup-$(date +%Y%m%d)

# 备份整个应用目录
tar -czf ~/ai-news-bot-backup-$(date +%Y%m%d).tar.gz /opt/apps/ai-news-bot/

# 下载备份到本地
scp root@your-digitalocean-ip:~/ai-news-bot-env-backup-* ./
```

### 监控应用状态

创建一个简单的监控脚本：

```bash
# 创建监控脚本
nano /usr/local/bin/check-ai-news-bot.sh
```

添加以下内容：

```bash
#!/bin/bash
LOG_FILE="/opt/apps/ai-news-bot/logs/app.log"
WEBHOOK_URL="YOUR_ALERT_WEBHOOK_URL"

# 检查今天是否有日志
if ! grep -q "$(date +%Y-%m-%d)" "$LOG_FILE"; then
    echo "WARNING: No logs found for today"
    # 可选：发送告警到企业微信
    # curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
    #   -d '{"msgtype":"text","text":{"content":"AI新闻机器人今天未运行"}}'
fi

# 检查是否有错误
if grep -q "ERROR\|Exception" "$LOG_FILE"; then
    echo "WARNING: Errors found in logs"
fi
```

```bash
# 设置权限
chmod +x /usr/local/bin/check-ai-news-bot.sh

# 添加到 crontab（每天 10:00 AM 检查）
crontab -e
# 添加：0 10 * * * /usr/local/bin/check-ai-news-bot.sh
```

## 回滚到阿里云

如果需要回滚到阿里云服务器：

1. **保持阿里云服务器配置不变**
2. **在 DigitalOcean 上禁用 cron 任务**
   ```bash
   crontab -e
   # 注释掉或删除 ai-news-bot 的行
   ```
3. **在阿里云上重新启用 cron 任务**

## 成本对比

**阿里云 vs DigitalOcean：**

| 项目 | 阿里云 | DigitalOcean |
|------|--------|--------------|
| 基础配置 | ¥XX/月 | $12/月 (约 ¥85/月) |
| 带宽 | 按流量计费 | 2TB 免费流量 |
| 快照备份 | 额外收费 | 免费 |
| 管理界面 | 中文 | 英文 |
| 文档支持 | 中文 | 英文（更丰富） |

## 下一步

迁移完成后，你可以：

1. **部署更多应用**
   ```bash
   deploy-app.sh app2 https://github.com/user/app2.git "0 10 * * *"
   ```

2. **设置监控和告警**
3. **配置自动备份**
4. **优化性能和安全性**

## 参考资源

- [DigitalOcean 文档](https://docs.digitalocean.com/)
- [部署脚本使用指南](./DEPLOY_SCRIPT_GUIDE.md)
- [Ubuntu 服务器管理](https://ubuntu.com/server/docs)
- [Cron 表达式生成器](https://crontab.guru/)

## 支持

如果遇到问题：

1. 查看本文档的故障排查部分
2. 检查应用日志
3. 查看系统日志：`/var/log/syslog`
4. 参考部署脚本使用指南

---

**文档版本：** 1.0.0  
**最后更新：** 2025年11月  
**适用于：** AI 新闻机器人 v1.0+
