#!/usr/bin/env python3
"""
AI新闻 邮件推送版本
支持HTML格式的精美邮件推送
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
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
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM', SMTP_USER)
EMAIL_TO = os.getenv('EMAIL_TO', SMTP_USER)  # 默认发给自己
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# 初始化DeepSeek客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# 新闻主题配置
NEWS_TOPICS = {
    'ai': {'name': 'AI科技', 'emoji': '🤖', 'desc': 'AI领域最新动态', 'color': '#4A90E2'},
    'finance': {'name': '财经新闻', 'emoji': '💰', 'desc': '金融市场和经济动态', 'color': '#F5A623'},
    'startup': {'name': '创业投资', 'emoji': '🚀', 'desc': '创业公司和投资动态', 'color': '#7ED321'},
    'education': {'name': '国际教育', 'emoji': '🎓', 'desc': '国际教育行业动态', 'color': '#BD10E0'},
    'pbsa': {'name': '学生公寓', 'emoji': '🏠', 'desc': 'PBSA学生公寓行业动态', 'color': '#50E3C2'},
    'uhomes': {'name': '异乡好居', 'emoji': '🏡', 'desc': '异乡好居企业动态', 'color': '#FF6B6B'}
}


def get_news(topic_key: str) -> str:
    """
    获取指定主题的新闻

    Args:
        topic_key: 新闻主题关键词

    Returns:
        str: 新闻内容（Markdown格式）
    """
    topic_info = NEWS_TOPICS.get(topic_key)
    if not topic_info:
        return f"❌ 未知的新闻主题: {topic_key}"

    logger.info(f"📡 正在获取{topic_info['name']}...")

    try:
        today_date = datetime.now().strftime("%Y年%m月%d日")

        # 不同主题的提示词
        prompts = {
            'ai': f"请总结{today_date}全球AI领域已经发生的真实新闻和动态。包括：技术突破🚀、产品发布📦、投资并购💰、政策法规📜",
            'finance': f"请总结{today_date}全球财经领域已经发生的真实新闻。包括：市场动态📊、经济政策🏛️、企业财报💼、投资动向💰",
            'startup': f"请总结{today_date}创业投资领域已经发生的真实新闻。包括：融资动态💰、新兴公司🚀、投资趋势📈、行业分析🔍",
            'education': f"请总结{today_date}国际教育行业已经发生的真实新闻和动态。包括：留学政策🌍、教育科技💻、院校动态🏫、行业趋势📈",
            'pbsa': f"请总结{today_date}PBSA(学生公寓)行业已经发生的真实新闻和动态。包括：市场动态🏠、投资并购💰、政策法规📜、项目开发🏗️",
            'uhomes': f"请总结{today_date}异乡好居(Uhomes)公司已经发生的真实新闻和动态。包括：企业动态🏡、业务发展📈、投资融资💰、合作伙伴🤝"
        }

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": f"""{prompts[topic_key]}

⚠️ 重要要求：
1. 只总结真实发生的新闻，不要推演、预测或虚构
2. 如果今天没有相关新闻，明确说明"今日暂无相关新闻"，可以总结近1-2天的真实新闻
3. 每条新闻必须标注具体的信息来源（媒体名称或官方发布）
4. 按重要性排序，每条新闻2-3句话概括
5. 使用Markdown格式，用emoji增强可读性

请开始总结真实新闻。"""
            }],
            max_tokens=2000,
            temperature=0.3
        )

        news_content = response.choices[0].message.content
        logger.info(f"✅ {topic_info['name']} 获取成功")
        return news_content

    except Exception as e:
        logger.error(f"❌ 获取{topic_info['name']}时出错: {e}")
        return f"⚠️ 获取{topic_info['name']}时出错：{str(e)}"


def markdown_to_html(markdown_text: str) -> str:
    """
    简单的Markdown转HTML
    支持基本的格式：标题、加粗、列表、emoji等

    Args:
        markdown_text: Markdown格式文本

    Returns:
        str: HTML格式文本
    """
    html = markdown_text

    # 处理标题
    import re
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # 处理加粗
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

    # 处理列表
    html = re.sub(r'^\* (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # 处理换行
    html = html.replace('\n\n', '</p><p>')
    html = '<p>' + html + '</p>'

    # 清理多余的p标签
    html = html.replace('<p><h', '<h')
    html = html.replace('</h1></p>', '</h1>')
    html = html.replace('</h2></p>', '</h2>')
    html = html.replace('</h3></p>', '</h3>')
    html = html.replace('<p><li>', '<li>')
    html = html.replace('</li></p>', '</li>')

    # 包裹列表
    html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    html = html.replace('</ul><ul>', '')

    return html


def create_email_html(topics_news: dict) -> str:
    """
    创建HTML格式的邮件内容

    Args:
        topics_news: {topic_key: news_content} 的字典

    Returns:
        str: HTML格式的邮件内容
    """
    today_date = datetime.now().strftime("%Y年%m月%d日 %A")

    # 构建主题卡片
    topic_cards = ""
    for topic_key, news_content in topics_news.items():
        topic_info = NEWS_TOPICS.get(topic_key, {})
        emoji = topic_info.get('emoji', '📰')
        name = topic_info.get('name', topic_key)
        color = topic_info.get('color', '#4A90E2')

        news_html = markdown_to_html(news_content)

        topic_cards += f"""
        <div style="margin-bottom: 30px; border-left: 4px solid {color}; padding-left: 20px;">
            <h2 style="color: {color}; margin-top: 0;">
                {emoji} {name}
            </h2>
            <div style="color: #333; line-height: 1.8;">
                {news_html}
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI新闻日报</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                 margin: 0; padding: 0; background-color: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px 30px; text-align: center; color: white;">
                <h1 style="margin: 0; font-size: 32px; font-weight: 600;">
                    📰 AI新闻日报
                </h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                    {today_date}
                </p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">
                    🤖 由 DeepSeek AI 智能总结
                </p>
            </div>

            <!-- Content -->
            <div style="padding: 40px 30px;">
                {topic_cards}
            </div>

            <!-- Footer -->
            <div style="background-color: #f9f9f9; padding: 30px; text-align: center;
                        border-top: 1px solid #eee; color: #666; font-size: 14px;">
                <p style="margin: 0;">
                    💡 这是一封自动生成的新闻邮件
                </p>
                <p style="margin: 10px 0 0 0;">
                    成本节省：比 Claude 便宜 20 倍 | 响应速度更快 | 中文支持更好
                </p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #999;">
                    © 2025 AI News Bot | Powered by DeepSeek
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_email(subject: str, html_content: str, to_email: str = None) -> bool:
    """
    发送HTML格式的邮件

    Args:
        subject: 邮件主题
        html_content: HTML格式的邮件内容
        to_email: 收件人邮箱，默认使用环境变量配置

    Returns:
        bool: 是否发送成功
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("❌ 未配置邮箱账号信息")
        return False

    to_email = to_email or EMAIL_TO

    try:
        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = Header(f"AI新闻助手 <{EMAIL_FROM}>", 'utf-8')
        message['To'] = Header(to_email, 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')

        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)

        # 连接SMTP服务器并发送
        logger.info(f"📧 正在连接SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")

        if SMTP_PORT == 465:
            # SSL连接
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            # TLS连接
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, to_email, message.as_string())
        server.quit()

        logger.info(f"✅ 邮件发送成功: {to_email}")
        return True

    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False


def send_daily_news(topics: list = None, to_email: str = None):
    """
    发送每日新闻邮件

    Args:
        topics: 要发送的主题列表，默认发送AI新闻
        to_email: 收件人邮箱
    """
    if topics is None:
        topics = ['ai']

    logger.info("=" * 60)
    logger.info(f"📰 开始获取每日新闻，主题: {', '.join(topics)}")
    logger.info("=" * 60)

    # 获取所有主题的新闻
    topics_news = {}
    for topic_key in topics:
        news = get_news(topic_key)
        topics_news[topic_key] = news

    # 生成邮件标题
    today_date = datetime.now().strftime("%Y年%m月%d日")
    topic_names = [NEWS_TOPICS[t]['name'] for t in topics if t in NEWS_TOPICS]
    subject = f"📰 {today_date} - {' | '.join(topic_names)} 新闻日报"

    # 生成HTML内容
    html_content = create_email_html(topics_news)

    # 发送邮件
    success = send_email(subject, html_content, to_email)

    if success:
        logger.info("✅ 每日新闻发送完成")
    else:
        logger.error("❌ 每日新闻发送失败")

    return success


def main():
    """主函数"""
    logger.info("🚀 AI新闻邮件推送服务启动")
    logger.info("=" * 60)

    # 检查配置
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("❌ 错误：未配置邮箱账号")
        logger.info("💡 请在 .env 文件中配置:")
        logger.info("   SMTP_SERVER=smtp.gmail.com")
        logger.info("   SMTP_PORT=587")
        logger.info("   SMTP_USER=your_email@gmail.com")
        logger.info("   SMTP_PASSWORD=your_password")
        logger.info("   EMAIL_TO=recipient@example.com")
        return

    if not DEEPSEEK_API_KEY:
        logger.error("❌ 错误：未配置 DEEPSEEK_API_KEY")
        return

    logger.info(f"📧 SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")
    logger.info(f"📤 发件人: {EMAIL_FROM}")
    logger.info(f"📥 收件人: {EMAIL_TO}")
    logger.info("=" * 60)

    # 发送所有主题的新闻
    logger.info("\n📡 发送所有主题的新闻...")
    all_topics = ['ai', 'finance', 'startup', 'education', 'pbsa', 'uhomes']
    send_daily_news(all_topics)

    logger.info("\n💡 提示：")
    logger.info("  - 已配置发送所有6个主题")
    logger.info("  - 可修改 main() 函数中的 all_topics 列表来调整主题")
    logger.info("  - 配合定时任务实现每天自动推送")


if __name__ == '__main__':
    main()
