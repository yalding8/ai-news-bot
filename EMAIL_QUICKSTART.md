# ⚡ 邮件推送 - 5分钟快速开始

最简单的配置方式，只需要一个邮箱！

## 🎯 适合谁？

- ✅ 不想依赖第三方平台
- ✅ 企业微信没有权限
- ✅ Telegram需要代理
- ✅ 想要精美的HTML格式
- ✅ 需要转发给多人

---

## 🚀 三步配置

### 第1步：选择邮箱（推荐Gmail或QQ邮箱）

#### 选项A：Gmail（国际用户推荐）

1. 打开 https://myaccount.google.com/security
2. 开启"两步验证"
3. 打开 https://myaccount.google.com/apppasswords
4. 生成应用专用密码：
   - 选择应用：邮件
   - 选择设备：其他（输入"AI News Bot"）
   - 点击"生成"
   - 复制16位密码（如：`abcd efgh ijkl mnop`）

#### 选项B：QQ邮箱（国内用户推荐）

1. 登录 https://mail.qq.com
2. 设置 → 账户 → POP3/IMAP/SMTP服务
3. 开启"SMTP服务"
4. 点击"生成授权码"
5. 发送短信验证
6. 复制授权码（16位）

---

### 第2步：配置环境变量

编辑 `.env` 文件：

**Gmail用户**：
```env
# SMTP配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop    # 你的应用专用密码

# 收发件人
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com        # 可以是任何邮箱

# DeepSeek API
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

**QQ邮箱用户**：
```env
# SMTP配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USER=123456789@qq.com
SMTP_PASSWORD=abcdefghijklmnop       # 你的授权码

# 收发件人
EMAIL_FROM=123456789@qq.com
EMAIL_TO=123456789@qq.com

# DeepSeek API
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

---

### 第3步：测试发送

```bash
# 运行邮件推送
python3 bot_email.py
```

成功后，你会收到一封精美的AI新闻邮件！📧

---

## 📧 邮件效果预览

你会收到一封包含以下内容的HTML邮件：

```
┌─────────────────────────────────────┐
│   📰 AI新闻日报                      │
│   2025年11月13日 星期三              │
│   🤖 由 DeepSeek AI 智能总结         │
├─────────────────────────────────────┤
│                                     │
│   🤖 AI科技                         │
│   ─────────────                     │
│   [精美的HTML格式新闻内容]           │
│                                     │
├─────────────────────────────────────┤
│   💡 这是一封自动生成的新闻邮件      │
│   © 2025 AI News Bot                │
└─────────────────────────────────────┘
```

**特点**：
- 🎨 渐变色标题
- 📱 手机/电脑完美显示
- 🌈 每个主题不同颜色
- ✨ Emoji 装饰

---

## ⏰ 定时推送（可选）

### macOS/Linux

```bash
# 编辑 crontab
crontab -e

# 每天早上8点发送AI新闻
0 8 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 -c "from bot_email import send_daily_news; send_daily_news(['ai'])" >> email_bot.log 2>&1
```

### Windows

使用任务计划程序（参考 [SCHEDULE_GUIDE.md](SCHEDULE_GUIDE.md)）

---

## 🎨 自定义

### 发送多个主题

编辑 `bot_email.py` 的 `main()` 函数：

```python
# 发送AI + 财经 + 创投
send_daily_news(['ai', 'finance', 'startup'])

# 发送所有主题
send_daily_news(['ai', 'finance', 'startup', 'education', 'pbsa', 'uhomes'])
```

### 发送给多人

```python
recipients = [
    'colleague1@company.com',
    'colleague2@company.com',
    'boss@company.com'
]

for email in recipients:
    send_daily_news(['ai', 'finance'], to_email=email)
```

---

## 🐛 常见问题

### Q: 535 Authentication failed

**A**: 使用的不是应用专用密码/授权码
- Gmail: 需要生成应用专用密码
- QQ: 需要使用授权码，不是QQ密码

### Q: 邮件进入垃圾箱

**A**:
1. 将发件人添加到联系人
2. 标记为"非垃圾邮件"

### Q: Connection timeout

**A**: 检查 SMTP 服务器和端口是否正确

---

## 📚 完整文档

详细配置和高级功能：[EMAIL_GUIDE.md](EMAIL_GUIDE.md)

---

## 🎉 完成！

现在你可以每天收到精美的AI新闻邮件了！

**下一步**：
- 配置定时推送，每天自动发送
- 添加更多主题
- 分享给同事和朋友

⭐ 如有问题，欢迎提Issue！
