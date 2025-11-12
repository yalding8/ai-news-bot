# 📰 多主题新闻 Telegram Bot

支持多个领域的最新资讯推送，由DeepSeek AI智能总结。

## ✨ 功能特点

- 🤖 **DeepSeek驱动**：使用DeepSeek AI智能搜索和总结
- 📰 **多主题支持**：AI科技、财经新闻、创业投资、国际教育、学生公寓、异乡好居
- 💬 **交互式命令**：支持按主题获取新闻
- 📱 **Telegram原生**：完美适配Telegram的Markdown格式
- 💰 **成本低廉**：比Claude便宜20倍

## 🚀 快速开始

### 1. 获取API Keys

**Telegram Bot Token:**
1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 创建Bot
3. 保存Token

**DeepSeek API Key:**
1. 访问 https://platform.deepseek.com/
2. 注册并创建API Key

**Chat ID:**
1. 搜索 `@userinfobot` 获取你的Chat ID

### 2. 配置环境

```bash
# 克隆项目
git clone <your-repo>
cd ai-news-bot

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 启动Bot

```bash
python bot_deepseek.py
```

## 📱 使用命令

### 新闻主题命令
| 命令 | 主题 | 说明 |
|------|------|------|
| `/ai` | 🤖 AI科技 | AI领域最新动态 |
| `/finance` | 💰 财经新闻 | 金融市场和经济动态 |
| `/startup` | 🚀 创业投资 | 创业公司和投资动态 |
| `/education` | 🎓 国际教育 | 国际教育行业动态 |
| `/pbsa` | 🏠 学生公寓 | PBSA学生公寓行业动态 |
| `/uhomes` | 🏡 异乡好居 | 异乡好居企业动态 |

### 其他命令
| 命令 | 说明 |
|------|---------|
| `/start` | 开始使用Bot |
| `/help` | 查看帮助信息 |

## 🔧 配置文件

编辑 `.env` 文件：

```env
TELEGRAM_TOKEN=你的Telegram_Bot_Token
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
CHAT_ID=你的Chat_ID
```

## 💰 成本优势

- DeepSeek API：~$0.14/1M tokens
- 比Claude便宜约20倍
- 响应速度更快
- 中文支持更好

## 📄 许可证

MIT License

---

⭐ 如果这个项目对你有帮助，请给个Star！