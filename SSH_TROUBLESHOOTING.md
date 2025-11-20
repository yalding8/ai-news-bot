# SSH连接问题排查指南

## 问题症状
```
Connection closed by 39.97.39.74 port 22
```

## 可能原因
1. SSH配置禁止root密码登录
2. fail2ban封禁IP
3. 服务器SSH服务配置问题

## 解决步骤

### 方案1：通过阿里云控制台修复SSH配置

1. **登录阿里云控制台**
   - 访问：https://swas.console.aliyun.com/
   - 找到服务器：39.97.39.74

2. **使用远程连接（VNC/WorkBench）**
   - 点击「远程连接」
   - 选择「VNC远程连接」或「WorkBench」
   - 输入root密码登录

3. **检查SSH配置**

```bash
# 查看SSH配置
cat /etc/ssh/sshd_config | grep -E "PermitRootLogin|PasswordAuthentication"

# 如果显示：
# PermitRootLogin no
# 或 PasswordAuthentication no
# 则需要修改
```

4. **修改SSH配置**

```bash
# 编辑配置文件
sudo nano /etc/ssh/sshd_config

# 修改或添加以下行：
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes

# 保存并退出：Ctrl+O -> Enter -> Ctrl+X
```

5. **重启SSH服务**

```bash
# Ubuntu/Debian
sudo systemctl restart ssh

# CentOS/AliyunOS
sudo systemctl restart sshd

# 验证服务状态
sudo systemctl status sshd
```

6. **测试连接**

```bash
# 在本地Mac上测试
ssh root@39.97.39.74
```

### 方案2：配置SSH密钥认证（推荐）

#### 步骤1：生成SSH密钥（如果没有）

```bash
# 在本地Mac上
ssh-keygen -t ed25519 -C "your_email@example.com"
# 或使用RSA
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 按提示保存到默认位置：~/.ssh/id_ed25519
```

#### 步骤2：通过阿里云VNC添加公钥

1. 使用阿里云控制台VNC登录服务器

2. 在服务器上执行：

```bash
# 创建.ssh目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 编辑authorized_keys
nano ~/.ssh/authorized_keys

# 粘贴你的公钥（从本地Mac复制）
# 在本地Mac上查看公钥：
# cat ~/.ssh/id_ed25519.pub

# 设置权限
chmod 600 ~/.ssh/authorized_keys
```

3. 测试密钥登录：

```bash
# 在本地Mac上
ssh root@39.97.39.74
# 应该不需要密码直接登录
```

#### 步骤3：更新部署脚本配置

密钥配置好后，部署脚本将自动使用密钥认证，无需任何修改。

### 方案3：检查是否被fail2ban封禁

通过VNC登录后，检查fail2ban状态：

```bash
# 检查fail2ban状态
sudo fail2ban-client status sshd

# 如果你的IP被封禁，解封：
sudo fail2ban-client set sshd unbanip YOUR_LOCAL_IP

# 查看你的公网IP
curl ifconfig.me
```

### 方案4：使用非root用户

如果服务器策略禁止root登录，创建普通用户：

1. 通过VNC登录
2. 创建新用户：

```bash
# 创建用户
sudo adduser deployer
sudo usermod -aG sudo deployer

# 为新用户配置SSH密钥
sudo mkdir -p /home/deployer/.ssh
sudo cp ~/.ssh/authorized_keys /home/deployer/.ssh/
sudo chown -R deployer:deployer /home/deployer/.ssh
sudo chmod 700 /home/deployer/.ssh
sudo chmod 600 /home/deployer/.ssh/authorized_keys
```

3. 修改 `.deployrc`：

```bash
SERVER_USER="deployer"  # 改为新用户
```

## 快速诊断命令

```bash
# 1. 测试网络连接
ping -c 3 39.97.39.74

# 2. 测试SSH端口
nc -zv 39.97.39.74 22
# 或
telnet 39.97.39.74 22

# 3. 详细SSH调试
ssh -vvv root@39.97.39.74

# 4. 查看本地SSH配置
cat ~/.ssh/config
```

## 完成修复后

SSH连接正常后，直接运行部署脚本：

```bash
./deploy.sh
```

或使用快速部署（跳过连接测试）：

```bash
./deploy_quick.sh
```
