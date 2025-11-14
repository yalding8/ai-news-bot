#!/usr/bin/env python3
"""
AI新闻 企业微信群机器人版本
使用Webhook方式发送消息到企业微信群
"""

import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
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
WECOM_WEBHOOK_URL = os.getenv('WECOM_WEBHOOK_URL')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

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


def send_wecom_message(content: str, msgtype: str = "text") -> bool:
    """
    发送消息到企业微信群

    Args:
        content: 消息内容
        msgtype: 消息类型，支持 text/markdown

    Returns:
        bool: 发送是否成功
    """
    if not WECOM_WEBHOOK_URL:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        return False

    # 构造消息体
    if msgtype == "markdown":
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    else:
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

    try:
        response = requests.post(
            WECOM_WEBHOOK_URL,
            json=data,
            timeout=10
        )
        result = response.json()

        if result.get('errcode') == 0:
            logger.info("✅ 消息发送成功")
            return True
        else:
            logger.error(f"❌ 消息发送失败: {result.get('errmsg')}")
            return False

    except Exception as e:
        logger.error(f"❌ 发送消息时出错: {e}")
        return False


def get_news(topic_key: str) -> str:
    """
    获取指定主题的新闻

    Args:
        topic_key: 新闻主题关键词

    Returns:
        str: 格式化的新闻内容
    """
    topic_info = NEWS_TOPICS.get(topic_key)
    if not topic_info:
        return f"❌ 未知的新闻主题: {topic_key}"

    logger.info(f"📡 正在获取{topic_info['name']}...")

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
2. 使用简洁的文本格式，适合企业微信展示
3. 如果今天新闻较少，可包含近期重要动态
4. 突出重点，用emoji增强可读性
5. 标注信息来源

请开始总结。"""
            }],
            max_tokens=2000,
            temperature=0.7
        )

        news_content = response.choices[0].message.content

        # 格式化消息
        formatted_message = f"""{topic_info['emoji']} {topic_info['name']} - {today_date}
由DeepSeek AI智能总结

{news_content}

━━━━━━━━━━━━━━━━
💡 发送命令获取其他主题新闻"""

        return formatted_message

    except Exception as e:
        logger.error(f"❌ 获取{topic_info['name']}时出错: {e}")
        return f"⚠️ 获取{topic_info['name']}时出错：{str(e)}\n\n请稍后重试。"


def send_daily_news(topics: list = None):
    """
    发送每日新闻汇总

    Args:
        topics: 要发送的主题列表，默认发送所有主题
    """
    if topics is None:
        topics = list(NEWS_TOPICS.keys())

    logger.info(f"📰 开始发送每日新闻，主题数量: {len(topics)}")

    for topic_key in topics:
        news = get_news(topic_key)
        success = send_wecom_message(news)

        if success:
            logger.info(f"✅ {NEWS_TOPICS[topic_key]['name']} 发送成功")
        else:
            logger.error(f"❌ {NEWS_TOPICS[topic_key]['name']} 发送失败")


def main():
    """主函数"""
    if not WECOM_WEBHOOK_URL:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        logger.info("请在 .env 文件中设置企业微信Webhook URL")
        return

    if not DEEPSEEK_API_KEY:
        logger.error("错误：未设置 DEEPSEEK_API_KEY")
        return

    logger.info("🚀 企业微信新闻机器人启动")
    logger.info("=" * 50)

    # 显示可用主题
    logger.info("📋 可用的新闻主题：")
    for key, info in NEWS_TOPICS.items():
        logger.info(f"  {info['emoji']} {key}: {info['name']}")

    logger.info("=" * 50)

    # 示例：发送AI新闻
    logger.info("📡 示例：发送AI新闻到企业微信群...")
    news = get_news('ai')
    send_wecom_message(news)

    logger.info("\n💡 提示：")
    logger.info("  - 可以修改 main() 函数来发送不同主题的新闻")
    logger.info("  - 使用 send_daily_news(['ai', 'finance']) 发送多个主题")
    logger.info("  - 配合 cron 或定时任务实现自动推送")


if __name__ == '__main__':
    main()
