# 🚀 一键部署到阿里云服务器

本文档介绍如何使用本项目的一键部署脚本，将 AI News Bot 快速部署到阿里云轻量应用服务器。

## 📋 前置要求

### 本地环境
- macOS 或 Linux 系统
- 已安装 `ssh` 和 `scp` 命令
- 可以通过 SSH 连接到服务器

### 服务器环境
- 阿里云轻量应用服务器（或其他云服务器）
- Ubuntu 20.04+ 或 CentOS 7+
- 已安装 Python 3.8+
- 已安装 `git`、`python3-venv`、`pip`

## 🎯 快速开始

### 1. 配置部署参数

编辑项目根目录下的 `.deployrc` 文件：

```bash
# 服务器信息
SERVER_IP="39.97.39.74"          # 修改为你的服务器IP
SERVER_USER="root"                # 修改为你的SSH用户名
SERVER_PORT="22"                  # SSH端口，默认22

# 部署路径
REMOTE_DIR="/opt/apps/ai-news-bot"  # 服务器上的部署目录

# 备份配置
BACKUP_DIR="/opt/backups/ai-news-bot"  # 备份目录
MAX_BACKUPS=5                      # 保留最近的备份数量
```

### 2. 执行一键部署

在项目根目录下运行：

```bash
./deploy.sh
```

脚本会提示你确认部署信息，输入 `yes` 继续：

```
🚀 AI News Bot - 一键部署
服务器: root@39.97.39.74:22
目标目录: /opt/apps/ai-news-bot
备份目录: /opt/backups/ai-news-bot

确认部署？(yes/no): yes
```

### 3. 部署流程

脚本会自动执行以下步骤：

#### 步骤 1/6: 检查本地文件 ✓
- 验证所有必需的Python文件和配置文件

#### 步骤 2/6: 打包代码 📦
- 将代码打包成 `.tar.gz` 文件
- 自动排除虚拟环境、日志、缓存等无关文件

#### 步骤 3/6: 测试服务器连接 🔌
- 测试SSH连接是否正常

#### 步骤 4/6: 上传代码 📤
- 将代码包上传到服务器 `/tmp` 目录
- 上传服务器端部署脚本

#### 步骤 5/6: 执行服务器端部署 🔧
服务器端会自动：
1. **备份旧版本** - 创建时间戳备份（保留最近5个）
2. **停止现有服务** - 安全停止正在运行的进程
3. **解压新代码** - 部署新版本代码
4. **设置权限** - 确保文件权限正确
5. **创建虚拟环境** - 首次部署时创建Python虚拟环境
6. **安装依赖** - 使用清华源加速安装
7. **恢复配置** - 从备份恢复 `.env` 配置文件
8. **测试导入** - 验证Python模块是否正常
9. **生成报告** - 创建详细的部署报告

#### 步骤 6/6: 清理临时文件 🧹
- 清理本地和服务器的临时文件

## 📌 部署后操作

部署成功后，你会看到以下提示：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 部署成功！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 下一步操作：

1️⃣  测试运行
   ssh -p 22 root@39.97.39.74
   cd /opt/apps/ai-news-bot
   source venv/bin/activate
   python3 bot_wecom.py

2️⃣  查看部署报告
   ssh -p 22 root@39.97.39.74 'cat /tmp/deploy_report.txt'

3️⃣  查看日志
   ssh -p 22 root@39.97.39.74 'tail -f /var/log/ai-news.log'

4️⃣  检查定时任务
   ssh -p 22 root@39.97.39.74 'crontab -l'
```

### 首次部署后必做

如果是首次部署，还需要：

#### 1. 配置环境变量

```bash
# SSH登录服务器
ssh root@39.97.39.74

# 进入项目目录
cd /opt/apps/ai-news-bot

# 编辑配置文件
nano .env
```

填入你的配置：
```env
DEEPSEEK_API_KEY=sk-你的DeepSeek_API_Key
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
TIANAPI_KEY=你的天行数据API_Key
```

#### 2. 测试运行

```bash
source venv/bin/activate
python3 bot_wecom.py
```

如果看到 `✅ 消息发送成功`，说明配置正确。

#### 3. 设置定时任务

```bash
# 添加定时任务（每天早上9点推送）
crontab -e
```

添加以下内容：
```cron
0 9 * * * cd /opt/apps/ai-news-bot && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

## 🔧 常见问题

### 1. SSH连接失败

**错误信息**：
```
✗ 无法连接到服务器
```

**解决方案**：
1. 检查服务器IP和端口是否正确
2. 确认SSH服务是否运行：`systemctl status ssh`
3. 检查防火墙规则
4. 确认使用正确的用户名

### 2. 权限错误

**错误信息**：
```
Permission denied
```

**解决方案**：
```bash
# 在服务器上创建目标目录并设置权限
sudo mkdir -p /opt/apps
sudo chown $USER:$USER /opt/apps
```

### 3. .env文件丢失

部署脚本会自动从备份恢复 `.env` 文件，但首次部署时需要手动创建。

### 4. 依赖安装失败

如果依赖安装失败，可以手动安装：

```bash
ssh root@39.97.39.74
cd /opt/apps/ai-news-bot
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 5. 旧进程没有停止

如果发现旧进程仍在运行：

```bash
# 查找进程
ps aux | grep bot_wecom

# 手动终止
killall -9 python3
```

## 📂 目录结构

部署后服务器目录结构：

```
/opt/apps/ai-news-bot/          # 主程序目录
├── bot_wecom.py                # 企业微信推送脚本
├── bot_email.py                # 邮件推送脚本
├── news_fetcher.py             # 新闻获取模块
├── config.py                   # 配置模块
├── requirements.txt            # 依赖列表
├── .env                        # 环境变量（需手动配置）
└── venv/                       # Python虚拟环境

/opt/backups/ai-news-bot/       # 备份目录
├── backup_20251120_093000/     # 时间戳备份
├── backup_20251119_154500/
└── ...

/var/log/ai-news.log            # 运行日志
```

## 🔄 更新代码

后续更新代码，只需要再次运行：

```bash
./deploy.sh
```

脚本会自动：
- 备份当前版本
- 部署新代码
- 安装新依赖
- 保留配置文件

## 🛡️ 回滚版本

如果新版本有问题，可以快速回滚：

```bash
# SSH登录服务器
ssh root@39.97.39.74

# 查看备份
ls -lt /opt/backups/ai-news-bot/

# 回滚到某个备份（替换时间戳）
cd /opt/apps
rm -rf ai-news-bot
cp -r /opt/backups/ai-news-bot/backup_20251120_093000 ai-news-bot

# 重启服务或等待下次定时任务
```

## 📊 监控和维护

### 查看日志

```bash
# 实时查看日志
ssh root@39.97.39.74 'tail -f /var/log/ai-news.log'

# 查看最近50行
ssh root@39.97.39.74 'tail -50 /var/log/ai-news.log'

# 搜索错误
ssh root@39.97.39.74 'grep ERROR /var/log/ai-news.log'
```

### 查看定时任务状态

```bash
ssh root@39.97.39.74 'crontab -l'
```

### 手动执行推送

```bash
ssh root@39.97.39.74
cd /opt/apps/ai-news-bot
source venv/bin/activate
python3 bot_wecom.py
```

## 🎨 自定义配置

### 修改备份策略

编辑 `.deployrc`：

```bash
# 保留更多备份
MAX_BACKUPS=10

# 修改备份路径
BACKUP_DIR="/data/backups/ai-news-bot"
```

### 修改部署路径

```bash
# 部署到其他目录
REMOTE_DIR="/home/user/projects/ai-news-bot"
```

## 📝 脚本说明

### deploy.sh（本地脚本）
- 打包代码
- 上传到服务器
- 触发远程部署
- 清理临时文件

### server_deploy.sh（服务器脚本）
- 备份当前版本
- 停止旧服务
- 部署新代码
- 安装依赖
- 生成部署报告

### .deployrc（配置文件）
- 服务器连接信息
- 部署路径
- 备份策略

## ⚠️ 注意事项

1. **密码认证**：本脚本使用密码认证，每次部署需要输入3-4次密码（连接测试、上传文件、执行命令）
2. **密钥认证**（推荐）：可以配置SSH密钥免密登录，避免重复输入密码
3. **配置保护**：`.env` 文件不会被上传，从备份自动恢复
4. **权限管理**：确保有足够权限访问 `/opt/apps` 和 `/opt/backups`
5. **网络稳定**：上传期间保持网络连接稳定

## 🔑 配置SSH密钥（推荐）

为了避免每次部署都输入密码，建议配置SSH密钥：

```bash
# 1. 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 2. 将公钥复制到服务器
ssh-copy-id -p 22 root@39.97.39.74

# 3. 测试免密登录
ssh root@39.97.39.74
```

配置后，`deploy.sh` 就可以免密执行了。

## 📞 支持

如有问题，请检查：
1. 部署报告：`/tmp/deploy_report.txt`
2. 运行日志：`/var/log/ai-news.log`
3. GitHub Issues

---

**最后更新**: 2025-11-20
