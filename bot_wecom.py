#!/usr/bin/env python3
"""
AI新闻 企业微信群机器人版本
使用Webhook方式发送消息到企业微信群
集成真实新闻API，避免AI编造内容
"""

import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from news_fetcher import NewsFetcher, TOPIC_KEYWORDS
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

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
ACTIVE_TOPICS_ENV = os.getenv('ACTIVE_TOPICS', 'ai,education')

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

# 复用新闻获取器（内置HTTP重试）
news_fetcher = NewsFetcher()

# 企业微信发送使用的HTTP会话（带重试）
send_session = requests.Session()
_retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods={"POST"}
)
_adapter = HTTPAdapter(max_retries=_retries)
send_session.mount("http://", _adapter)
send_session.mount("https://", _adapter)


def parse_active_topics(raw: str) -> list:
    """从环境变量解析启用的主题列表"""
    topics = []
    for key in [t.strip() for t in raw.split(',')]:
        if not key:
            continue
        if key in NEWS_TOPICS:
            topics.append(key)
        else:
            logger.warning(f"⚠️ 忽略未知主题: {key}")
    return topics

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
        response = send_session.post(
            WECOM_WEBHOOK_URL,
            json=data,
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"❌ 消息发送失败 HTTP {response.status_code}: {response.text[:200]}")
            return False

        try:
            result = response.json()
        except ValueError:
            logger.error(f"❌ 消息发送失败，非JSON响应: {response.text[:200]}")
            return False

        if result.get('errcode') == 0:
            logger.info("✅ 消息发送成功")
            return True
        else:
            logger.error(f"❌ 消息发送失败 errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
            return False

    except Exception as e:
        logger.error(f"❌ 发送消息时出错: {e}")
        return False


def get_news(topic_key: str) -> str:
    """
    获取指定主题的新闻（集成真实新闻API）

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

        # 第一步：获取真实新闻（获取更多新闻，让AI筛选精华）
        logger.info(f"  └─ 从所有新闻源获取真实新闻（API + RSS）...")
        keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
        real_news = news_fetcher.fetch_news(topic_key, keywords, num=10)  # 获取10条，已按质量排序

        if not real_news:
            # 如果没有获取到真实新闻，返回说明
            logger.warning(f"  └─ 未获取到真实新闻，使用备用方案")
            return f"""{topic_info['emoji']} {topic_info['name']} - {today_date}

⚠️ 暂时无法获取实时新闻

可能原因：
• 新闻API配额已用完
• 网络连接问题
• 今日该主题暂无新闻

💡 建议：
• 稍后重试
• 访问权威新闻网站查看
• 配置新闻API Key (TIANAPI_KEY 或 NEWSAPI_KEY)"""

        # 第二步：格式化真实新闻为文本
        news_text = news_fetcher.format_news_for_ai(real_news)
        logger.info(f"  └─ 获取到 {len(real_news)} 条真实新闻")

        # 第三步：让AI总结这些真实新闻
        logger.info(f"  └─ AI正在总结新闻...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": f"""请总结以下{topic_info['name']}的真实新闻（共{len(real_news)}条）：

{news_text}

⚠️ 重要要求：
1. 只总结上述提供的真实新闻，不要添加其他内容
2. 如果新闻超过5条，请挑选3-5条最重要、最有价值的新闻进行重点总结
3. 每条新闻用2-3句话概括关键信息和亮点
4. 保持新闻来源信息（在括号中注明）
5. 使用简洁的文本格式，适合企业微信展示
6. 用emoji增强可读性（每条新闻前加相关emoji）
7. 按重要性排序，最重要的新闻放在最前面

请开始总结（重点提炼）："""
            }],
            max_tokens=2000,
            temperature=0.3  # 降低温度，减少创造性
        )

        ai_summary = response.choices[0].message.content
        logger.info(f"✅ {topic_info['name']} 获取成功")

        # 第四步：格式化最终消息（包含新闻链接）
        news_links = "\n".join([
            f"• {news['title']}\n  {news['url']}"
            for news in real_news[:3]  # 只显示前3条链接
        ])

        formatted_message = f"""{topic_info['emoji']} {topic_info['name']} - {today_date}
📰 真实新闻 + AI智能总结

{ai_summary}

━━━━━━━━━━━━━━━━
🔗 新闻原文链接：

{news_links}

━━━━━━━━━━━━━━━━
✅ 本次推送基于真实新闻API
💡 点击链接查看详情"""

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

    # 解析环境变量决定推送哪些主题
    active_topics = parse_active_topics(ACTIVE_TOPICS_ENV)
    if not active_topics:
        active_topics = ['ai', 'education']
    logger.info(f"📡 开始发送每日新闻（{len(active_topics)}个主题）...")
    send_daily_news(active_topics)

    logger.info("\n💡 提示：")
    logger.info(f"  - 当前配置：ACTIVE_TOPICS={','.join(active_topics)}")
    logger.info("  - AI科技RSS源：天行API + 36氪 + 少数派 + IT之家")
    logger.info("  - 教育RSS源：芥末堆 + 黑板洞察 + 36氪")
    logger.info("  - 如需修改主题，设置环境变量 ACTIVE_TOPICS=ai,education")
    logger.info("  - 配合 cron 或定时任务实现自动推送")


if __name__ == '__main__':
    main()
