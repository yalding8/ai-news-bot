#!/usr/bin/env python3
"""
AI日报 Telegram Bot - DeepSeek版本
使用DeepSeek API获取AI新闻
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')

# 初始化DeepSeek客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# 新闻主题配置
NEWS_TOPICS = {
    'ai': {'name': 'AI科技', 'emoji': '🤖', 'desc': 'AI领域最新动态'},
    'finance': {'name': '财经新闻', 'emoji': '💰', 'desc': '金融市场和经济动态'},
    'startup': {'name': '创业投资', 'emoji': '🚀', 'desc': '创业公司和投资动态'},
    'education': {'name': '国际教育', 'emoji': '🎓', 'desc': '国际教育行业动态'},
    'pbsa': {'name': '学生公寓', 'emoji': '🏠', 'desc': 'PBSA学生公寓行业动态'},
    'uhomes': {'name': '异乡好居', 'emoji': '🏡', 'desc': '异乡好居企业动态'}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    topics_list = '\n'.join([f"{info['emoji']} /{topic} - {info['desc']}" for topic, info in NEWS_TOPICS.items()])
    
    welcome_message = f"""👋 *欢迎使用多主题新闻Bot！*

🤖 *由DeepSeek AI驱动*

*新闻主题：*
{topics_list}

*其他命令：*
/help - ❓ 查看帮助信息

━━━━━━━━━━━━━━━━
💡 选择感兴趣的主题获取最新资讯！"""

    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def get_news(topic_key: str, update: Update):
    """获取指定主题的新闻"""
    topic_info = NEWS_TOPICS.get(topic_key)
    if not topic_info:
        return
    
    await update.message.reply_text(f"📡 正在为你获取最新{topic_info['name']}，请稍候...")

    try:
        today_date = datetime.now().strftime("%Y年%m月%d日")
        
        # 不同主题的提示词
        prompts = {
            'ai': f"请总结{today_date}全球AI领域的重要新闻和动态。包括：技术突破🚀、产品发布📦、投资并购💰、政策法规📜",
            'finance': f"请总结{today_date}全球财经领域的重要新闻。包括：市场动态📊、经济政策🏛️、企业财报💼、投资动向💰",
            'startup': f"请总结{today_date}创业投资领域的重要新闻。包括：融资动态💰、新兴公司🚀、投资趋势📈、行业分析🔍",
            'education': f"请总结{today_date}国际教育行业的重要新闻和动态。包括：留学政策🌍、教育科技💻、院校动态🏫、行业趋势📈、教育投资💰",
            'pbsa': f"请总结{today_date}PBSA(学生公寓)行业的重要新闻和动态。包括：市场动态🏠、投资并购💰、政策法规📜、项目开发🏗️、行业趋势📈",
            'uhomes': f"请总结{today_date}异乡好居(Uhomes)公司的重要新闻和动态。包括：企业动态🏡、业务发展📈、投资融资💰、合作伙伴🤝、市场扩展🌍"
        }

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user", 
                "content": f"""{prompts[topic_key]}

要求：
1. 按重要性排序，每条新闻2-3句话概括
2. 使用Markdown格式，适合Telegram展示
3. 如果今天新闻较少，可包含近期重要动态
4. 突出重点，用emoji增强可读性
5. 标注信息来源

请开始总结。"""
            }],
            max_tokens=2000,
            temperature=0.7
        )

        news_content = response.choices[0].message.content
        
        formatted_message = f"""{topic_info['emoji']} *{topic_info['name']} - {today_date}*
*由DeepSeek AI智能总结*

{news_content}

━━━━━━━━━━━━━━━━
🔄 发送 /{topic_key} 刷新内容
💡 发送 /help 查看更多命令"""

        await update.message.reply_text(
            formatted_message,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"获取{topic_info['name']}时出错: {e}")
        await update.message.reply_text(
            f"⚠️ 获取{topic_info['name']}时出错：{str(e)}\n\n请稍后重试。"
        )

# 为每个主题创建命令处理函数
async def ai_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('ai', update)

async def finance_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('finance', update)

async def startup_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('startup', update)

async def education_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('education', update)

async def pbsa_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('pbsa', update)

async def uhomes_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_news('uhomes', update)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    topics_list = '\n'.join([f"/{topic} - {info['emoji']} {info['desc']}" for topic, info in NEWS_TOPICS.items()])
    
    help_text = f"""❓ *帮助信息*

*新闻主题命令：*
{topics_list}

*其他命令：*
/start - 开始使用Bot
/help - 显示此帮助信息

*功能说明：*
• 支持多个新闻主题
• 内容由DeepSeek AI智能总结
• 实时获取最新资讯

*关于DeepSeek：*
• 成本更低，响应更快
• 中文理解能力强
• 多领域内容分析准确

━━━━━━━━━━━━━━━━
💡 有问题或建议？欢迎反馈！"""

    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """启动Bot"""
    if not TELEGRAM_TOKEN:
        logger.error("错误：未设置 TELEGRAM_TOKEN")
        return

    if not DEEPSEEK_API_KEY:
        logger.error("错误：未设置 DEEPSEEK_API_KEY")
        return

    logger.info("正在启动AI日报Bot (DeepSeek版本)...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 添加命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # 添加各主题新闻命令
    app.add_handler(CommandHandler("ai", ai_news))
    app.add_handler(CommandHandler("finance", finance_news))
    app.add_handler(CommandHandler("startup", startup_news))
    app.add_handler(CommandHandler("education", education_news))
    app.add_handler(CommandHandler("pbsa", pbsa_news))
    app.add_handler(CommandHandler("uhomes", uhomes_news))

    logger.info("✅ AI日报Bot启动成功！")
    logger.info("🤖 使用DeepSeek AI驱动")
    logger.info("💬 在Telegram中发送 /start 开始使用")
    logger.info("按 Ctrl+C 停止Bot")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()