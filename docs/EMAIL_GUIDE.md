# 📧 邮件推送配置指南（已停用）

⚠️ 当前版本仅保留企业微信推送，邮件通道已下线，本指南仅作存档。

## ✨ 特点

- ✅ **无需第三方平台**：只需要一个邮箱
- ✅ **精美HTML格式**：响应式设计，手机电脑完美显示
- ✅ **完全免费**：使用免费邮箱服务
- ✅ **定时推送**：配合cron实现每日自动推送
- ✅ **多主题支持**：一封邮件包含多个主题新闻

## 🚀 快速开始

### 第一步：选择邮箱服务商

推荐使用以下服务（按推荐度排序）：

#### 1. Gmail（推荐，最稳定）

**优点**：
- 稳定可靠
- 全球可用
- 支持应用专用密码

**SMTP配置**：
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### 2. Outlook/Hotmail

**优点**：
- 免费无限制
- 国内可用

**SMTP配置**：
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
```

#### 3. QQ邮箱

**优点**：
- 国内用户熟悉
- 中文界面

**SMTP配置**：
```env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
# 或使用 SSL
# SMTP_PORT=465
```

#### 4. 163邮箱

**SMTP配置**：
```env
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
```

---

### 第二步：获取邮箱授权

不同邮箱服务商的授权方式不同：

#### Gmail - 应用专用密码（推荐方式）

1. **开启两步验证**
   - 访问：https://myaccount.google.com/security
   - 找到"两步验证"并开启

2. **生成应用专用密码**
   - 访问：https://myaccount.google.com/apppasswords
   - 应用：选择"邮件"
   - 设备：选择"其他"，输入"AI News Bot"
   - 点击"生成"
   - **复制16位密码**（类似：abcd efgh ijkl mnop）

3. **保存密码**
   - 这个密码只显示一次
   - 用它作为 `SMTP_PASSWORD`

#### QQ邮箱 - 授权码

1. **登录QQ邮箱**
   - 访问：https://mail.qq.com

2. **开启SMTP服务**
   - 设置 → 账户
   - 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
   - 开启"SMTP服务"

3. **生成授权码**
   - 点击"生成授权码"
   - 按提示发送短信验证
   - **复制授权码**（16位，类似：abcdefghijklmnop）

4. **使用授权码**
   - 用授权码作为 `SMTP_PASSWORD`，不是QQ密码

#### Outlook - 直接使用密码

- 可以直接使用Outlook账号密码
- 或开启两步验证后使用应用密码

#### 163邮箱 - 授权码

1. 登录163邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启"SMTP服务"
4. 生成授权码

---

### 第三步：配置环境变量

编辑 `.env` 文件：

```env
# ========== 邮件配置 ==========

# SMTP服务器配置（根据邮箱选择）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# 邮箱账号和密码/授权码
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# 发件人（通常和SMTP_USER相同）
EMAIL_FROM=your_email@gmail.com

# 收件人（可以是任何邮箱，包括自己）
EMAIL_TO=your_email@gmail.com

# DeepSeek API配置
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

**⚠️ 重要提示**：
- `SMTP_PASSWORD` 使用的是**应用专用密码/授权码**，不是邮箱登录密码
- `EMAIL_TO` 可以设置为任何邮箱，不一定是发件邮箱

---

### 第四步：测试发送

```bash
# 安装依赖（如果还没装）
pip install -r requirements.txt

# 测试发送
python3 bot_email.py
```

成功后，你会在 `EMAIL_TO` 邮箱收到一封精美的AI新闻邮件！

---

## 📋 使用示例

### 示例1：发送单个主题

```python
from bot_email import send_daily_news

# 发送AI新闻
send_daily_news(['ai'])

# 发送财经新闻
send_daily_news(['finance'])
```

### 示例2：发送多个主题

```python
# 发送AI + 财经 + 创投
send_daily_news(['ai', 'finance', 'startup'])

# 发送所有主题
send_daily_news(['ai', 'finance', 'startup', 'education', 'pbsa', 'uhomes'])
```

### 示例3：发送到多个收件人

修改 `bot_email.py`，在 `send_email()` 函数中支持多收件人：

```python
# 发送给多个人
recipients = [
    'person1@example.com',
    'person2@example.com',
    'person3@example.com'
]

for recipient in recipients:
    send_daily_news(['ai'], to_email=recipient)
```

---

## ⏰ 定时推送

### 方法1：使用scheduler.py（推荐）

修改 `scheduler.py`，添加邮件推送支持：

```python
def send_news_email(topics: list, schedule_name: str = ""):
    """使用邮件发送新闻"""
    import bot_email
    return bot_email.send_daily_news(topics)
```

然后在 `schedule_config.json` 中配置：

```json
{
  "schedules": [
    {
      "name": "早间邮报",
      "enabled": true,
      "time": "08:00",
      "topics": ["ai", "finance"],
      "platform": "email"
    }
  ]
}
```

### 方法2：直接使用cron

```bash
# 编辑 crontab
crontab -e

# 每天早上8点发送邮件
0 8 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 -c "from bot_email import send_daily_news; send_daily_news(['ai', 'finance'])" >> email_bot.log 2>&1
```

### 方法3：创建专门的脚本

创建 `send_email_news.py`：

```python
#!/usr/bin/env python3
from bot_email import send_daily_news

# 每天发送AI和财经新闻
send_daily_news(['ai', 'finance'])
```

然后在crontab中：

```bash
0 8 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 send_email_news.py >> email_bot.log 2>&1
```

---

## 🎨 邮件样式预览

邮件采用响应式HTML设计，包含：

### Header（邮件头部）
- 渐变色背景
- 大标题：📰 AI新闻日报
- 日期和AI来源说明

### Content（内容区域）
- 彩色主题标签（每个主题不同颜色）
- Markdown格式的新闻内容
- Emoji装饰
- 清晰的层次结构

### Footer（底部）
- 自动生成提示
- 成本和性能说明
- 版权信息

**效果**：
- 📱 手机完美显示
- 💻 电脑大屏也很美观
- 🎨 支持深色/浅色模式（根据邮箱客户端）

---

## 🔧 进阶配置

### 1. 自定义邮件模板

编辑 `bot_email.py` 的 `create_email_html()` 函数，修改HTML模板。

### 2. 添加附件

```python
from email.mime.base import MIMEBase
from email import encoders

# 在 send_email() 函数中添加附件
with open('report.pdf', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename=report.pdf')
    message.attach(part)
```

### 3. 批量发送

```python
# 从CSV读取收件人列表
import csv

with open('recipients.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        email = row[0]
        send_daily_news(['ai'], to_email=email)
```

### 4. 个性化内容

根据收件人偏好发送不同主题：

```python
user_preferences = {
    'user1@example.com': ['ai', 'startup'],
    'user2@example.com': ['finance'],
    'user3@example.com': ['education', 'pbsa']
}

for email, topics in user_preferences.items():
    send_daily_news(topics, to_email=email)
```

---

## 🐛 故障排查

### 问题1：535 Authentication failed

**原因**：密码错误或未使用应用专用密码

**解决**：
1. 确认使用的是应用专用密码/授权码，不是登录密码
2. 检查是否开启了两步验证（Gmail）
3. 检查是否开启了SMTP服务（QQ/163）

### 问题2：Connection refused / Timeout

**原因**：SMTP服务器或端口错误

**解决**：
1. 检查 `SMTP_SERVER` 是否正确
2. 检查 `SMTP_PORT` 是否正确（587或465）
3. 检查网络连接

### 问题3：邮件进入垃圾箱

**原因**：邮件内容被判定为垃圾邮件

**解决**：
1. 在邮箱中将发件人添加到联系人
2. 手动标记为"非垃圾邮件"
3. 修改邮件标题，避免敏感词

### 问题4：Gmail "Less secure apps"

**解决**：
- 不要使用"允许不够安全的应用"
- 使用应用专用密码（更安全）

---

## 📊 常用邮箱SMTP配置速查表

| 邮箱 | SMTP服务器 | 端口 | 加密方式 | 授权方式 |
|------|-----------|------|---------|---------|
| Gmail | smtp.gmail.com | 587 | TLS | 应用专用密码 |
| Gmail | smtp.gmail.com | 465 | SSL | 应用专用密码 |
| Outlook | smtp.office365.com | 587 | TLS | 账号密码 |
| QQ邮箱 | smtp.qq.com | 587 | TLS | 授权码 |
| QQ邮箱 | smtp.qq.com | 465 | SSL | 授权码 |
| 163邮箱 | smtp.163.com | 465 | SSL | 授权码 |
| 126邮箱 | smtp.126.com | 465 | SSL | 授权码 |
| iCloud | smtp.mail.me.com | 587 | TLS | 应用专用密码 |

---

## 💡 最佳实践

### 1. 推送时间建议

- **工作日早报**：8:00-9:00（上班前）
- **午间快讯**：12:00-13:00（午休时）
- **晚间汇总**：18:00-19:00（下班后）
- **周报**：周一早上 9:00

### 2. 主题搭配建议

- **科技人士**：AI + 创业投资
- **金融从业者**：财经 + 创业投资
- **教育行业**：国际教育 + 学生公寓
- **综合资讯**：所有主题

### 3. 性能优化

- 避免同时发送大量邮件（可能被限流）
- 发送间隔建议 ≥ 2秒
- 使用日志记录发送状态

### 4. 安全建议

- ✅ 使用应用专用密码，不要用登录密码
- ✅ 将 `.env` 文件加入 `.gitignore`
- ✅ 定期更换授权码
- ❌ 不要在代码中硬编码密码

---

## 🎯 与其他平台对比

| 特性 | 邮件推送 | 企业微信 | Telegram |
|------|---------|---------|----------|
| 配置难度 | ⭐⭐ 中等 | ⭐⭐⭐ 可能需要权限 | ⭐ 简单 |
| 访问便利 | ✅ 随时随地 | ✅ 企业内部 | ⚠️ 需要代理 |
| 格式支持 | ✅ 精美HTML | ⚠️ 文本 | ✅ Markdown |
| 多人分享 | ✅ 转发方便 | ✅ 群聊 | ✅ 群聊 |
| 交互功能 | ❌ 单向 | ❌ 单向 | ✅ 命令交互 |
| 成本 | ✅ 免费 | ✅ 免费 | ✅ 免费 |

---

## 📚 相关文档

- [README.md](README.md) - 项目总览
- [定时推送配置](SCHEDULE_GUIDE.md) - 定时任务配置
- [企业微信配置](WECOM_GUIDE.md) - 企业微信版本
- [Telegram配置](TELEGRAM_QUICKSTART.md) - Telegram版本

---

⭐ 如有问题，欢迎提Issue！
