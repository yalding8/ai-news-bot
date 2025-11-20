#!/usr/bin/env python3
"""
AI新闻 邮件推送版本
支持HTML格式的精美邮件推送
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

from config import (
    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, 
    EMAIL_FROM, EMAIL_TO, NEWS_TOPICS, TOPIC_KEYWORDS, get_logger
)
from news_fetcher import NewsFetcher
from ai_summarizer import AISummarizer

logger = get_logger(__name__)

# 初始化新闻获取器
news_fetcher = NewsFetcher()

# 初始化AI总结器
ai_summarizer = AISummarizer()


def get_news(topic_key: str) -> str:
    """
    获取指定主题的新闻（集成真实新闻API）

    Args:
        topic_key: 新闻主题关键词

    Returns:
        str: 新闻内容（Markdown格式，包含总结和链接）
    """
    topic_info = NEWS_TOPICS.get(topic_key)
    if not topic_info:
        return f"❌ 未知的新闻主题: {topic_key}"

    logger.info(f"📡 正在获取{topic_info['name']}...")

    try:
        today_date = datetime.now().strftime("%Y年%m月%d日")

        # 1. 获取真实新闻
        logger.info(f"  └─ 获取真实新闻数据...")
        keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
        # 获取更多新闻供AI筛选
        real_news = news_fetcher.fetch_news(topic_key, keywords, num=10)

        if not real_news:
            logger.warning(f"  └─ 未获取到真实新闻")
            return f"⚠️ 今日暂无{topic_info['name']}相关新闻（或API调用失败）。\n\n建议访问权威媒体查看。"

        # 2. 格式化供AI阅读
        news_text = news_fetcher.format_news_for_ai(real_news)
        logger.info(f"  └─ 获取到 {len(real_news)} 条新闻，正在总结...")

        # 3. AI总结
        ai_summary = ai_summarizer.summarize_news(topic_key, real_news, news_text)

        # 4. 附加原文链接
        links_section = "\n\n### 🔗 原文链接\n"
        for news in real_news[:5]:  # 只列出前5条链接
            links_section += f"- [{news['title']}]({news['url']}) - {news['source']}\n"

        final_content = ai_summary + links_section
        
        logger.info(f"✅ {topic_info['name']} 处理完成")
        return final_content

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

    # 处理链接
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html)

    # 处理换行
    html = html.replace('\n\n', '</p><p>')
    html = '<p>' + html + '</p>'

    # 清理多余的p标签
    html = html.replace('<p><h', '<h')
    html = html.replace('</h1></p>', '</h1>')
    html = html.replace('</h2></p>', '<h2>')
    html = html.replace('</h3></p>', '<h3>')
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
    发送每日新闻邮件（并行处理）

    Args:
        topics: 要发送的主题列表，默认发送AI新闻
        to_email: 收件人邮箱
    """
    import concurrent.futures

    if topics is None:
        topics = ['ai']

    logger.info("=" * 60)
    logger.info(f"📰 开始获取每日新闻，主题: {', '.join(topics)}")
    logger.info("=" * 60)

    # 并行获取所有主题的新闻
    topics_news = {}
    
    def fetch_topic_news(topic_key):
        """获取单个主题新闻"""
        return topic_key, get_news(topic_key)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(topics), 5)) as executor:
        future_to_topic = {executor.submit(fetch_topic_news, topic): topic for topic in topics}
        
        for future in concurrent.futures.as_completed(future_to_topic):
            topic_key = future_to_topic[future]
            try:
                _, news_content = future.result()
                topics_news[topic_key] = news_content
            except Exception as exc:
                logger.error(f"❌ {topic_key} 获取异常: {exc}")
                topics_news[topic_key] = f"⚠️ 获取失败: {exc}"

    # 按照原始顺序排序
    ordered_news = {k: topics_news[k] for k in topics if k in topics_news}

    # 生成邮件标题
    today_date = datetime.now().strftime("%Y年%m月%d日")
    topic_names = [NEWS_TOPICS[t]['name'] for t in topics if t in NEWS_TOPICS]
    subject = f"📰 {today_date} - {' | '.join(topic_names)} 新闻日报"

    # 生成HTML内容
    html_content = create_email_html(ordered_news)

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
