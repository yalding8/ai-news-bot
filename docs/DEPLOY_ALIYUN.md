# 🚀 阿里云服务器部署指南（已归档）

⚠️ 当前默认部署环境为 DigitalOcean/通用 Ubuntu，本指南仅作历史参考。

完整的阿里云轻量应用服务器部署教程,从购买到运行,一步一步教您。

---

## 📊 服务器配置推荐

### 推荐方案: 轻量应用服务器

**配置**:
- CPU: 2核
- 内存: 2GB
- 带宽: 3-5Mbps
- 系统盘: 40GB SSD
- 操作系统: Ubuntu 20.04 / 22.04 LTS

**价格**: ¥24-30/月 (首年可能有优惠)

**为什么选轻量服务器**:
- ✅ 价格便宜 (比ECS便宜)
- ✅ 配置简单 (新手友好)
- ✅ 性能够用 (本项目需求很低)
- ✅ 包含固定带宽

---

## 🛒 第一步: 购买阿里云服务器

### 1. 注册阿里云账号

1. 访问 https://www.aliyun.com
2. 点击右上角 "免费注册"
3. 使用手机号注册
4. 完成实名认证 (需要身份证)

### 2. 购买轻量应用服务器

#### 访问购买页面

https://www.aliyun.com/product/swas

#### 选择配置

1. **地域**: 选择离您最近的 (如: 华北2-北京)
2. **套餐**:
   - 2核2GB - 24元/月 (推荐)
   - 或 1核1GB - 更便宜但性能稍弱
3. **镜像**:
   - 系统镜像 → Ubuntu → 20.04 LTS 或 22.04 LTS
4. **存储**: 默认40GB SSD (够用)
5. **时长**: 建议先买1个月测试

#### 设置服务器

1. **实例名称**: ai-news-bot
2. **密码**: 设置root密码 (记住这个密码!)
3. **勾选协议**
4. **立即购买**

### 3. 支付

- 支持支付宝、微信支付
- 约24-30元/月

### 4. 等待创建

- 约1-2分钟创建完成
- 会分配一个公网IP地址

---

## 💻 第二步: 连接服务器

### 方法1: 使用阿里云控制台 (最简单)

1. 访问 https://swas.console.aliyun.com/
2. 找到您的服务器实例
3. 点击 "远程连接" → "Workbench远程连接"
4. 在网页中直接操作终端

### 方法2: 使用SSH客户端 (推荐)

#### macOS / Linux:

打开终端:

```bash
# 连接服务器
ssh root@你的服务器IP

# 例如:
# ssh root@47.93.123.456

# 输入密码 (就是购买时设置的root密码)
# 首次连接会询问是否信任,输入 yes
```

#### Windows:

**使用Windows Terminal + OpenSSH**:

1. 安装 Windows Terminal (Microsoft Store)
2. 打开后输入:
```bash
ssh root@你的服务器IP
```

**或使用PuTTY**:

1. 下载 PuTTY: https://www.putty.org/
2. Host Name: 填入服务器IP
3. Port: 22
4. Connection Type: SSH
5. 点击 Open
6. 输入用户名: root
7. 输入密码

---

## 🔧 第三步: 配置服务器环境

连接成功后,开始配置:

### 1. 更新系统

```bash
# 更新软件包列表
apt update

# 升级已安装的软件
apt upgrade -y

# 这个过程可能需要2-5分钟
```

### 2. 安装必要软件

```bash
# 安装Python3和pip
apt install python3 python3-pip -y

# 安装Git
apt install git -y

# 安装其他依赖
apt install python3-venv curl wget -y

# 验证安装
python3 --version  # 应显示 Python 3.8+ 版本
pip3 --version
git --version
```

### 3. 创建工作目录

```bash
# 创建应用目录
mkdir -p /opt/apps
cd /opt/apps
```

---

## 📦 第四步: 部署项目

### 方法1: 从GitHub克隆 (推荐)

如果您的代码已上传到GitHub:

```bash
# 克隆仓库
cd /opt/apps
git clone https://github.com/你的用户名/ai-news-bot.git

# 进入项目目录
cd ai-news-bot
```

### 方法2: 手动上传文件

如果代码在本地:

**使用scp上传** (在本地Mac终端执行):

```bash
# 在本地项目目录
cd /Users/ningding/ai-news-bot

# 压缩项目
tar -czf ai-news-bot.tar.gz .

# 上传到服务器
scp ai-news-bot.tar.gz root@你的服务器IP:/opt/apps/

# 在服务器上解压
# (在服务器终端执行)
cd /opt/apps
mkdir ai-news-bot
tar -xzf ai-news-bot.tar.gz -C ai-news-bot/
cd ai-news-bot
```

**使用SFTP工具** (图形界面):

1. 下载 FileZilla: https://filezilla-project.org/
2. 连接信息:
   - 主机: sftp://你的服务器IP
   - 用户名: root
   - 密码: 你的root密码
   - 端口: 22
3. 连接后,将本地文件拖拽到服务器 `/opt/apps/ai-news-bot/`

### 3. 安装Python依赖

```bash
cd /opt/apps/ai-news-bot

# 安装依赖
pip3 install -r requirements.txt

# 如果速度慢,可以使用国内镜像:
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置环境变量

```bash
# 创建.env文件
nano .env
```

在编辑器中输入 (按照您的实际配置修改):

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-192e98a7652b4a829754a3e740f3f0c2

# 企业微信机器人配置
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ad335a27-91dd-4fca-b73e-e1d5b4b11f03
```

保存并退出:
- 按 `Ctrl + X`
- 按 `Y`
- 按 `Enter`

### 5. 测试运行

```bash
# 测试企业微信推送
python3 bot_wecom.py

# 如果成功,应该看到:
# ✅ 消息发送成功
```

---

## ⏰ 第五步: 配置定时任务

### 1. 编辑crontab

```bash
crontab -e
```

第一次运行会询问编辑器,选择 nano (简单):
- 输入 `1` 然后回车

### 2. 添加定时任务

在文件末尾添加:

```bash
# 每天早上9点推送AI新闻到企业微信
0 9 * * * cd /opt/apps/ai-news-bot && /usr/bin/python3 bot_wecom.py >> /var/log/ai-news-wecom.log 2>&1

# 如果想推送多个时间段,可以添加多行:
# 每天中午12点推送财经新闻
# 0 12 * * * cd /opt/apps/ai-news-bot && /usr/bin/python3 bot_wecom.py >> /var/log/ai-news-wecom.log 2>&1

# 每天晚上6点推送
# 0 18 * * * cd /opt/apps/ai-news-bot && /usr/bin/python3 bot_wecom.py >> /var/log/ai-news-wecom.log 2>&1

# 工作日早上9点 (周一到周五)
# 0 9 * * 1-5 cd /opt/apps/ai-news-bot && /usr/bin/python3 bot_wecom.py >> /var/log/ai-news-wecom.log 2>&1
```

保存:
- 按 `Ctrl + X`
- 按 `Y`
- 按 `Enter`

### 3. 验证crontab

```bash
# 查看已配置的定时任务
crontab -l

# 查看cron服务状态
systemctl status cron

# 如果服务未启动,启动它:
systemctl start cron
systemctl enable cron
```

### 4. 创建日志目录权限

```bash
# 确保日志文件可写
touch /var/log/ai-news-wecom.log
chmod 666 /var/log/ai-news-wecom.log
```

---

## 🔒 第六步: 安全加固 (重要!)

### 1. 修改SSH端口 (可选但推荐)

```bash
# 编辑SSH配置
nano /etc/ssh/sshd_config

# 找到 #Port 22 这一行
# 改为 Port 2222 (或其他端口)

# 保存并重启SSH
systemctl restart sshd
```

**注意**: 修改后,连接命令变为:
```bash
ssh -p 2222 root@你的服务器IP
```

**阿里云控制台配置**:
1. 进入轻量应用服务器控制台
2. 点击 "防火墙"
3. 添加规则: 端口 2222, 协议 TCP, 允许

### 2. 配置防火墙

阿里云轻量服务器使用自带防火墙:

1. 访问 https://swas.console.aliyun.com/
2. 选择您的实例
3. 点击 "防火墙"
4. 默认规则:
   - 22/SSH: 允许 (或您修改后的端口)
   - 80/HTTP: 根据需要
   - 443/HTTPS: 根据需要

对于AI新闻机器人,只需要SSH端口即可。

### 3. 禁用root密码登录 (可选,高级)

使用SSH密钥更安全:

```bash
# 在本地Mac生成SSH密钥
ssh-keygen -t rsa -b 4096

# 上传公钥到服务器
ssh-copy-id root@你的服务器IP

# 在服务器上禁用密码登录
nano /etc/ssh/sshd_config
# 修改: PasswordAuthentication no

# 重启SSH
systemctl restart sshd
```

---

## 📊 第七步: 监控和管理

### 1. 查看定时任务日志

```bash
# 实时查看日志
tail -f /var/log/ai-news-wecom.log

# 查看最近20条
tail -n 20 /var/log/ai-news-wecom.log

# 搜索错误
grep "ERROR\|失败" /var/log/ai-news-wecom.log
```

### 2. 查看系统资源

```bash
# 查看CPU和内存使用
top

# 按q退出

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

### 3. 手动触发推送

```bash
cd /opt/apps/ai-news-bot
python3 bot_wecom.py
```

### 4. 更新代码

如果使用Git:

```bash
cd /opt/apps/ai-news-bot
git pull
```

如果手动上传:
- 使用scp或FileZilla重新上传文件

---

## 🔄 第八步: 配置进程守护 (可选,推荐)

如果想让程序持续运行并自动重启:

### 使用systemd服务

#### 1. 创建服务文件

```bash
nano /etc/systemd/system/ai-news-scheduler.service
```

#### 2. 添加配置

```ini
[Unit]
Description=AI News Bot Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/apps/ai-news-bot
ExecStart=/usr/bin/python3 scheduler.py --check
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ai-news-scheduler.log
StandardError=append:/var/log/ai-news-scheduler-error.log

[Install]
WantedBy=multi-user.target
```

#### 3. 启动服务

```bash
# 重新加载systemd配置
systemctl daemon-reload

# 启动服务
systemctl start ai-news-scheduler

# 设置开机自启
systemctl enable ai-news-scheduler

# 查看服务状态
systemctl status ai-news-scheduler

# 查看服务日志
journalctl -u ai-news-scheduler -f
```

#### 4. 管理服务

```bash
# 停止服务
systemctl stop ai-news-scheduler

# 重启服务
systemctl restart ai-news-scheduler

# 查看日志
tail -f /var/log/ai-news-scheduler.log
```

---

## 🎯 优化建议

### 1. 配置日志轮转

防止日志文件过大:

```bash
nano /etc/logrotate.d/ai-news-bot
```

添加:

```
/var/log/ai-news-*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 2. 配置时区

确保定时任务时间正确:

```bash
# 查看当前时区
timedatectl

# 设置为中国时区
timedatectl set-timezone Asia/Shanghai

# 验证
date
```

### 3. 配置自动安全更新

```bash
# 安装自动更新工具
apt install unattended-upgrades -y

# 配置自动安全更新
dpkg-reconfigure -plow unattended-upgrades
# 选择 Yes
```

### 4. 监控磁盘空间

```bash
# 添加到crontab
crontab -e

# 添加每天检查磁盘空间
0 8 * * * df -h > /var/log/disk-usage.log
```

---

## 💰 成本优化

### 1. 关闭不需要的服务

```bash
# 查看运行的服务
systemctl list-units --type=service --state=running

# 关闭不需要的服务(谨慎操作)
# systemctl disable 服务名
```

### 2. 使用流量监控

```bash
# 安装vnstat
apt install vnstat -y

# 启动
systemctl start vnstat
systemctl enable vnstat

# 查看流量
vnstat -h  # 小时
vnstat -d  # 天
vnstat -m  # 月
```

### 3. 选择合适的镜像源

使用阿里云镜像源(默认已配置):

```bash
# 备份原配置
cp /etc/apt/sources.list /etc/apt/sources.list.backup

# 验证镜像源
cat /etc/apt/sources.list | grep aliyun
```

---

## 🔍 故障排查

### 问题1: 定时任务不执行

**排查步骤**:

```bash
# 1. 检查cron服务
systemctl status cron

# 2. 查看cron日志
grep CRON /var/log/syslog

# 3. 手动测试命令
cd /opt/apps/ai-news-bot && python3 bot_wecom.py

# 4. 检查Python路径
which python3
# 确保crontab中的路径正确

# 5. 查看定时任务日志
tail -f /var/log/ai-news-wecom.log
```

### 问题2: 依赖安装失败

```bash
# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或阿里云镜像
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 问题3: 内存不足

```bash
# 查看内存使用
free -h

# 添加swap空间
dd if=/dev/zero of=/swapfile bs=1M count=1024
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 问题4: 网络连接问题

```bash
# 测试网络
ping -c 4 qyapi.weixin.qq.com

# 测试DeepSeek API
curl -I https://api.deepseek.com

# 测试DNS
nslookup qyapi.weixin.qq.com
```

### 问题5: 权限问题

```bash
# 检查文件权限
ls -la /opt/apps/ai-news-bot/

# 修复权限
chmod +x /opt/apps/ai-news-bot/*.py
chown -R root:root /opt/apps/ai-news-bot/
```

---

## 📱 远程管理

### 1. 使用手机SSH客户端

**iOS**:
- Termius (推荐)
- Prompt

**Android**:
- JuiceSSH
- Termius

### 2. 配置告警通知

当推送失败时,发送通知:

```bash
# 修改 bot_wecom.py
# 添加错误处理和告警逻辑
```

---

## 🎓 学习要点

通过阿里云部署,您学到了:

1. **Linux服务器管理**: 基础命令和系统配置
2. **SSH连接**: 远程服务器操作
3. **Crontab定时任务**: 自动化任务调度
4. **systemd服务**: 进程守护和自动重启
5. **日志管理**: 监控和故障排查
6. **安全加固**: 防火墙和SSH配置

这些是运维工程师的核心技能!

---

## 📋 快速命令参考

```bash
# === 常用命令 ===

# 连接服务器
ssh root@服务器IP

# 进入项目目录
cd /opt/apps/ai-news-bot

# 手动触发推送
python3 bot_wecom.py

# 查看日志
tail -f /var/log/ai-news-wecom.log

# 编辑定时任务
crontab -e

# 查看定时任务列表
crontab -l

# 重启服务
systemctl restart ai-news-scheduler

# 查看服务状态
systemctl status ai-news-scheduler

# 更新代码
git pull

# 查看系统资源
top
df -h
free -h

# 查看网络流量
vnstat -d
```

---

## 🆚 对比: 阿里云 vs Railway

| 项目 | 阿里云服务器 | Railway |
|------|-------------|---------|
| 成本 | ¥24-30/月 | $0-5/月 |
| 配置难度 | ⭐⭐⭐☆☆ | ⭐☆☆☆☆ |
| 灵活性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ |
| 运维负担 | ⭐⭐⭐☆☆ | ⭐☆☆☆☆ |
| 适合场景 | 多项目/需要完全控制 | 单项目/快速部署 |

**建议**:
- 如果只运行AI新闻机器人 → Railway更合适
- 如果还有其他项目要部署 → 阿里云服务器更划算
- 如果想学习运维知识 → 阿里云服务器是好机会

---

## 📚 相关资源

- [阿里云轻量服务器文档](https://help.aliyun.com/product/59601.html)
- [Ubuntu官方文档](https://ubuntu.com/server/docs)
- [Crontab在线工具](https://crontab.guru/)

---

## ✅ 部署检查清单

部署完成后,确认以下事项:

- [ ] 服务器可以正常连接
- [ ] Python环境安装完成
- [ ] 项目代码已部署
- [ ] 环境变量已配置
- [ ] 手动推送测试成功
- [ ] crontab定时任务已配置
- [ ] 定时任务执行正常
- [ ] 日志可以正常查看
- [ ] 防火墙规则已配置
- [ ] (可选) systemd服务已配置

---

🎉 **部署成功!**

现在您的AI新闻机器人已经在阿里云上24小时运行了!

有问题随时查看日志或提Issue!
