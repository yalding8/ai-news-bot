# ⚡ Telegram版本快速开始

如果企业微信暂时不可用，Telegram是最佳替代方案！

## 🎯 5分钟快速配置

### 第1步：创建Telegram Bot

1. 在Telegram搜索：`@BotFather`
2. 发送命令：`/newbot`
3. 按提示设置机器人名称（如：AI News Bot）
4. 设置用户名（如：ai_news_assistant_bot）
5. 获得 **Token**（类似：`123456:ABC-DEF...`）

### 第2步：获取你的Chat ID

1. 在Telegram搜索：`@userinfobot`
2. 点击 `Start`
3. 它会显示你的 **Chat ID**（如：`123456789`）

### 第3步：配置环境变量

编辑 `.env` 文件：

```env
# Telegram配置
TELEGRAM_TOKEN=你的Bot_Token
CHAT_ID=你的Chat_ID

# DeepSeek API
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

### 第4步：启动机器人

```bash
cd /Users/ningding/ai-news-bot
python3 bot_deepseek.py
```

看到这个说明成功了：
```
✅ AI日报Bot启动成功！
🤖 使用DeepSeek AI驱动
💬 在Telegram中发送 /start 开始使用
```

### 第5步：开始使用

在Telegram中：
1. 搜索你刚创建的机器人
2. 点击 `Start`
3. 发送命令：
   - `/ai` - 获取AI新闻
   - `/finance` - 获取财经新闻
   - `/help` - 查看所有命令

## 🎉 完成！

Telegram版本的优势：
- ✅ 无需企业权限
- ✅ 5分钟就能用
- ✅ 支持命令交互
- ✅ 免费无限制
- ⚠️ 国内需要代理（但配置简单）

---

## 🔄 定时推送（可选）

Telegram版本也可以配置定时推送，方法类似企业微信版本。

详见：[定时推送配置指南](SCHEDULE_GUIDE.md)
