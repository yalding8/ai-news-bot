# 🚀 替代部署方案：Git同步部署

由于SSH连接存在问题，我们推荐使用 **Git同步部署** 方案。这种方式更稳定，不需要本地SSH连接。

## 步骤 1：本地推送代码

在本地终端运行以下命令，将最新代码推送到GitHub：

```bash
./git_push.sh
```

## 步骤 2：服务器端拉取与运行

登录 **阿里云控制台**（网页端），在终端中执行以下命令：

### 首次部署（如果服务器上还没有代码）

```bash
# 1. 准备目录
sudo mkdir -p /opt/apps
sudo chown admin:admin /opt/apps
cd /opt/apps

# 2. 克隆代码
git clone https://github.com/yalding8/ai-news-bot.git
cd ai-news-bot

# 3. 创建环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 配置环境变量
cp .env.example .env
nano .env  # 填入你的API Key

# 6. 测试运行
python3 bot_wecom.py
```

### 更新部署（如果服务器上已有代码）

以后每次本地 `./git_push.sh` 后，在服务器上执行：

```bash
cd /opt/apps/ai-news-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 bot_wecom.py
```

## 常见问题

### 1. git clone 需要密码？
如果是公开仓库，不需要密码。如果是私有仓库，需要输入 GitHub 用户名和 Token（不是密码）。

### 2. 忘记 API Key？
可以在本地查看 `.env` 文件内容：
```bash
cat .env
```
然后复制到服务器的 `.env` 文件中。

## 📊 监控与维护

在阿里云控制台终端中，你可以使用以下命令检查程序状态：

### 1. 检查程序是否在运行
查看是否有正在运行的 Python 进程：
```bash
ps -ef | grep bot_wecom.py
```

### 2. 查看运行日志
查看程序的输出日志（包括报错信息）：
```bash
# 实时查看最新日志
tail -f /var/log/ai-news.log

# 查看最后100行
tail -n 100 /var/log/ai-news.log
```

### 3. 检查定时任务
确认定时任务是否已正确设置：
```bash
crontab -l
```
应该看到类似：`0 9 * * * ... python3 bot_wecom.py ...`

### 4. 检查系统定时日志
如果定时任务没有执行，查看系统日志：
```bash
# Ubuntu
grep CRON /var/log/syslog

# CentOS/Aliyun Linux
grep CRON /var/log/cron
```

### 5. 手动测试运行
如果你想立即测试一次：
```bash
cd /opt/apps/ai-news-bot
source venv/bin/activate
python3 bot_wecom.py
```
