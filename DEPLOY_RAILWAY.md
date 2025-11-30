# 🚀 Railway 快速部署指南

5分钟将AI新闻机器人部署到云端,实现24小时自动推送!

---

## ✨ 为什么选择 Railway?

- ✅ **超级简单**: 点几下鼠标就部署完成
- ✅ **免费额度**: 每月 $5 的免费额度,够用!
- ✅ **自动部署**: Push代码自动重新部署
- ✅ **实时日志**: Web界面查看运行状态
- ✅ **无需管理**: 不用操心服务器运维

---

## 📋 准备工作

### 1. 确认配置

确保您已经配置好:
- ✅ DeepSeek API Key
- ✅ 企业微信 Webhook URL
- ✅ 定时任务配置 (schedule_config.json)

### 2. 创建GitHub账号

如果还没有: https://github.com/signup

---

## 🚀 部署步骤

### 第一步: 上传代码到GitHub

#### 方法1: 使用命令行 (推荐)

```bash
# 1. 初始化Git仓库 (如果还没有)
git init

# 2. 添加所有文件
git add .

# 3. 创建提交
git commit -m "Ready for Railway deployment"

# 4. 在GitHub上创建新仓库
# 访问 https://github.com/new
# 仓库名: ai-news-bot
# 设为私有 (Private)
# 不要勾选任何初始化选项
# 点击 "Create repository"

# 5. 关联远程仓库并推送
git branch -M main
git remote add origin https://github.com/你的用户名/ai-news-bot.git
git push -u origin main
```

#### 方法2: 使用GitHub Desktop (图形界面)

1. 下载 GitHub Desktop: https://desktop.github.com/
2. 登录GitHub账号
3. File → Add Local Repository → 选择项目文件夹
4. Publish repository → 设为私有
5. Publish

---

### 第二步: 在Railway创建项目

#### 1. 注册Railway账号

1. 访问 https://railway.app
2. 点击 "Login"
3. 选择 "Login with GitHub"
4. 授权Railway访问GitHub

#### 2. 创建新项目

1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 如果是第一次,需要配置GitHub访问权限:
   - 点击 "Configure GitHub App"
   - 选择要授权的仓库 (ai-news-bot)
4. 选择您的 `ai-news-bot` 仓库
5. Railway会自动开始部署

---

### 第三步: 配置环境变量

#### 在Railway项目页面:

1. 点击项目名称
2. 进入 "Variables" 标签
3. 添加以下变量:

**必需的环境变量**:

```
DEEPSEEK_API_KEY = sk-192e98a7652b4a829754a3e740f3f0c2
WECOM_WEBHOOK_URL = https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ad335a27-91dd-4fca-b73e-e1d5b4b11f03
```

> 当前版本仅保留企业微信推送；Telegram 变量已停用，可忽略。

#### 添加方式:

1. 点击 "New Variable"
2. 输入变量名 (例如: DEEPSEEK_API_KEY)
3. 输入变量值
4. 点击 "Add"
5. 重复以上步骤添加其他变量

---

### 第四步: 配置定时任务

编辑 `schedule_config.json` 文件:

```json
{
  "schedules": [
    {
      "name": "早间AI新闻",
      "enabled": true,
      "time": "09:00",
      "topics": ["ai"],
      "description": "每天早上9点推送AI新闻"
    },
    {
      "name": "午间财经快讯",
      "enabled": false,
      "time": "12:00",
      "topics": ["finance", "startup"],
      "description": "中午12点推送财经和创投新闻"
    }
  ]
}
```

提交并推送到GitHub:

```bash
git add schedule_config.json
git commit -m "Update schedule config"
git push
```

Railway会自动重新部署!

---

### 第五步: 验证部署

#### 1. 查看部署状态

在Railway项目页面:
- ✅ Status: Active (绿色)
- 📊 查看 Logs 标签,应该看到启动日志

#### 2. 手动触发测试

在Railway的 "Deployments" 标签:
- 点击最新的部署
- 查看日志输出
- 确认没有错误

#### 3. 等待定时推送

根据您配置的时间,等待定时任务执行:
- 检查企业微信群是否收到消息
- 在Railway日志中查看执行记录

---

## 📊 管理和监控

### 查看实时日志

1. 进入Railway项目
2. 点击 "Logs" 标签
3. 实时查看运行日志

### 手动重启服务

1. 点击项目
2. Settings → Restart
3. 确认重启

### 更新代码

只需推送到GitHub:

```bash
# 修改代码后
git add .
git commit -m "Update bot"
git push
```

Railway会自动检测并重新部署!

### 查看资源使用

在Railway Dashboard:
- CPU使用率
- 内存使用
- 网络流量
- 成本统计

---

## 💰 费用说明

### 免费额度

Railway提供每月 **$5** 的免费额度:
- 包含: 500小时运行时间
- 包含: 100GB出站流量
- 对于这个项目: **完全够用!**

### 预估成本

AI新闻机器人的资源消耗:
- CPU: 极低 (只在推送时运行)
- 内存: ~100MB
- 网络: ~10MB/天

**每月成本**: < $1 (远低于免费额度)

### 避免超额

1. 合理设置推送频率 (不要太频繁)
2. 监控用量: Railway Dashboard → Usage
3. 设置预算告警

---

## 🔧 故障排查

### 问题1: 部署失败

**检查步骤**:
1. 查看 Build Logs
2. 确认 requirements.txt 存在
3. 检查Python语法错误

**常见原因**:
- 依赖包版本冲突
- 代码语法错误

**解决方法**:
```bash
# 本地测试
pip install -r requirements.txt
python3 scheduler.py --check
```

### 问题2: 环境变量未生效

**检查**:
1. Variables 标签中是否已添加
2. 变量名是否拼写正确
3. 是否需要重新部署

**解决**:
- 添加变量后,点击 "Redeploy" 重新部署

### 问题3: 定时任务不执行

**检查**:
1. schedule_config.json 配置是否正确
2. enabled 是否为 true
3. 时间格式是否正确 (24小时制)

**解决**:
```bash
# 本地测试
python3 scheduler.py --now --name "早间AI新闻"
```

### 问题4: 推送失败

**检查**:
1. Logs中的错误信息
2. WECOM_WEBHOOK_URL 是否正确
3. 企业微信机器人是否被删除

**解决**:
- 测试Webhook URL
- 重新获取Webhook URL

---

## 🎯 优化建议

### 1. 设置健康检查

在 `scheduler.py` 中添加日志记录:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 2. 配置告警

使用Railway的 Webhooks:
- Settings → Webhooks
- 部署失败时发送通知

### 3. 多环境部署

创建多个分支:
- main: 生产环境
- dev: 测试环境

在Railway创建两个项目分别对应。

### 4. 备份配置

定期备份 schedule_config.json:

```bash
cp schedule_config.json schedule_config.json.backup
```

---

## 🌟 进阶功能

### 推送到多个群

修改 `bot_wecom.py` 支持多个Webhook:

```python
WEBHOOKS = [
    os.getenv('WECOM_WEBHOOK_URL'),
    os.getenv('WECOM_WEBHOOK_URL_2'),
    os.getenv('WECOM_WEBHOOK_URL_3'),
]

for webhook in WEBHOOKS:
    if webhook:
        send_wecom_message(news, webhook)
```

在Railway添加更多环境变量:
- WECOM_WEBHOOK_URL_2
- WECOM_WEBHOOK_URL_3

### 动态调整推送时间

无需重新部署,只需:
1. 修改 schedule_config.json
2. Git push
3. Railway自动重新部署

### 监控和告警

集成监控服务:
- UptimeRobot: 监控服务是否在线
- Sentry: 错误追踪
- Better Stack: 日志管理

---

## 📚 相关资源

- [Railway官方文档](https://docs.railway.app/)
- [完整云部署指南](CLOUD_DEPLOY_GUIDE.md)
- [定时任务配置](SCHEDULE_GUIDE.md)
- [企业微信接入](WECOM_GUIDE.md)

---

## ❓ 常见问题

### Q: Railway免费额度够用吗?

A: 对于这个项目,完全够用。每月$5免费额度,实际使用可能不到$1。

### Q: 可以随时停止吗?

A: 可以。在Railway项目设置中点击 "Delete Project" 即可。

### Q: 如何查看历史推送记录?

A: 在Railway的Logs标签中,可以查看所有历史日志。

### Q: 支持其他推送方式吗?

A: 当前版本仅支持企业微信推送，其余通道已停用。

### Q: 代码会泄露吗?

A: 不会。可以设置GitHub仓库为私有,Railway也是安全的。

---

## 🎓 学习要点

通过这次部署,您学到了:

1. **Git和GitHub**: 代码版本管理
2. **环境变量**: 安全管理配置信息
3. **云部署**: PaaS平台的使用
4. **CI/CD**: 自动化部署流程
5. **日志监控**: 运维和故障排查

这些都是现代软件开发的核心技能!

---

⭐ **部署成功后,记得Star项目!**

有问题随时提Issue: https://github.com/你的用户名/ai-news-bot/issues

祝您部署顺利! 🎉
