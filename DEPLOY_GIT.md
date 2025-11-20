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
