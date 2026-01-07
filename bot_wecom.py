#!/usr/bin/env python3
"""
AI新闻 企业微信群机器人版本
使用Webhook方式发送消息到企业微信群
集成真实新闻API，避免AI编造内容
"""

import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import concurrent.futures
import threading
from typing import Dict

from config import (
    WECOM_WEBHOOK_URLS, 
    NEWS_TOPICS, 
    ACTIVE_TOPICS_ENV, 
    TOPIC_ALIASES,
    SEND_WHEN_NO_NEW,
    get_logger
)
from news_fetcher import NewsFetcher, TOPIC_KEYWORDS
from ai_summarizer import AISummarizer
from news_cache import filter_new_news, mark_news_as_sent

logger = get_logger(__name__)

# 复用新闻获取器（内置HTTP重试）
news_fetcher = NewsFetcher()

# 初始化AI总结器
ai_summarizer = AISummarizer()

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
        normalized = TOPIC_ALIASES.get(key, key)
        if normalized in NEWS_TOPICS:
            if normalized not in topics:
                topics.append(normalized)
            if normalized != key:
                logger.info(f"🔁 主题别名映射: {key} -> {normalized}")
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
    if not WECOM_WEBHOOK_URLS:
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

    all_success = True
    for webhook_url in WECOM_WEBHOOK_URLS:
        try:
            response = send_session.post(
                webhook_url,
                json=data,
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"❌ 消息发送失败 ({webhook_url[-10:]}) HTTP {response.status_code}: {response.text[:200]}")
                all_success = False
                continue

            try:
                result = response.json()
            except ValueError:
                logger.error(f"❌ 消息发送失败，非JSON响应: {response.text[:200]}")
                all_success = False
                continue

            if result.get('errcode') == 0:
                logger.info(f"✅ 消息发送成功 ({webhook_url[-10:]})")
            else:
                logger.error(f"❌ 消息发送失败 errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
                all_success = False

        except Exception as e:
            logger.error(f"❌ 发送消息时出错 ({webhook_url[-10:]}): {e}")
            all_success = False

    return all_success


def process_topic_news(topic_key: str) -> Dict:
    """
    处理单个主题的新闻（获取 -> 总结 -> 返回结构化数据）
    """
    topic_cfg = NEWS_TOPICS.get(topic_key)
    if not topic_cfg:
        return {"success": False, "error": f"未找到主题配置: {topic_key}"}
    
    logger.info(f"🚀 开始处理主题: {topic_cfg['name']}")
    
    try:
        # 1. 获取新闻
        logger.info(f"  └─ 从所有新闻源获取真实新闻（API + RSS）...")
        keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
        all_news = news_fetcher.fetch_news(topic_key, keywords, num=15)
        
        # 2. 过滤
        logger.info(f"  └─ 过滤重复新闻...")
        real_news = filter_new_news(topic_key, all_news)

        if not real_news:
            if not all_news:
                logger.warning(f"  └─ 未获取到真实新闻")
                return {
                    "success": True,
                    "topic_key": topic_key,
                    "topic_name": topic_cfg['name'],
                    "emoji": topic_cfg['emoji'],
                    "content": "⚠️ 暂时无法获取实时新闻，可能API配额耗尽或网络问题。",
                    "news_links": []
                }
            else:
                logger.info(f"  └─ 今日{topic_cfg['name']}暂无新内容")
                return {
                    "success": True,
                    "topic_key": topic_key,
                    "topic_name": topic_cfg['name'],
                    "emoji": topic_cfg['emoji'],
                    "content": "✅ 今日暂无新内容（已自动过滤重复资讯）",
                    "news_links": []
                }

        logger.info(f"  └─ 获取到 {len(real_news)} 条真实新闻")
        news_text = news_fetcher.format_news_for_ai(real_news)

        # 3. AI 总结
        ai_summary = ai_summarizer.summarize_news(topic_key, real_news, news_text)
        logger.info(f"✅ {topic_cfg['name']} 总结完成")
        
        # 4. 标记新闻为已推送
        mark_news_as_sent(topic_key, real_news)

        # 5. 构造返回结果
        return {
            "success": True,
            "topic_key": topic_key,
            "topic_name": topic_cfg['name'],
            "emoji": topic_cfg['emoji'],
            "content": ai_summary,
            "news_links": [{"title": n['title'], "url": n['url']} for n in real_news[:3]]
        }

    except Exception as e:
        logger.error(f"❌ 处理主题 {topic_key} 失败: {e}")
        return {"success": False, "error": str(e), "topic_key": topic_key}


def send_daily_news(topics: list = None):
    """
    发送每日新闻汇总（合并所有主题为一条消息，去重）

    Args:
        topics: 要发送的主题列表（用于获取新闻源，但最终合并展示）
    """
    if topics is None:
        topics = list(NEWS_TOPICS.keys())

    logger.info(f"📰 开始获取新闻，涉及 {len(topics)} 个主题源")

    # 并行从所有主题获取新闻
    all_news = []
    seen_urls = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(topics), 5)) as executor:
        future_to_topic = {
            executor.submit(fetch_topic_news_raw, topic): topic
            for topic in topics
        }
        for future in concurrent.futures.as_completed(future_to_topic):
            try:
                news_list = future.result()
                # 按URL去重
                for news in news_list:
                    if news['url'] not in seen_urls:
                        seen_urls.add(news['url'])
                        all_news.append(news)
            except Exception as exc:
                logger.error(f"❌ 获取新闻异常: {exc}")

    if not all_news:
        logger.warning("⚠️ 未获取到任何新闻，取消发送日报")
        return

    logger.info(f"📊 合并去重后共 {len(all_news)} 条新闻")

    # 过滤已推送的新闻
    new_news = filter_new_news('daily_digest', all_news)
    if not new_news:
        logger.warning("⚠️ 所有新闻均已推送过，取消发送日报")
        return

    logger.info(f"📰 筛选出 {len(new_news)} 条未推送新闻")

    # AI总结（取前9条最重要的新闻）
    top_news = new_news[:9]
    news_text = news_fetcher.format_news_for_ai(top_news)

    logger.info("🤖 AI正在生成新闻摘要...")
    ai_summary = ai_summarizer.summarize_daily_news(top_news, news_text)

    # 标记为已推送
    mark_news_as_sent('daily_digest', top_news)

    # 构造消息
    today_date = datetime.now().strftime("%Y年%m月%d日")

    message_parts = [
        f"📅 **异乡早咖啡 - {today_date}**\n",
        ai_summary,
        "\n**🔗 精选来源**:"
    ]

    # 添加前5条链接
    for news in top_news[:5]:
        message_parts.append(f"• [{news['title'][:40]}...]({news['url']})" if len(news['title']) > 40 else f"• [{news['title']}]({news['url']})")

    # 广告区域
    message_parts.append("\n---")
    message_parts.append("🏠 **异乡好居** - 留学生海外的家 [#小程序://异乡好居/vvS67rZGtrvbQIn]")
    message_parts.append("💰 **异乡缴费** - 比一比更省钱 [#小程序://异乡缴费/8d32ABZvjBHh1vd]")
    message_parts.append("\n💡 *Powered By 异乡有你，AI驱动 • 实时聚合全球国际教育资讯*")

    final_message = "\n".join(message_parts)
    byte_length = len(final_message.encode('utf-8'))
    logger.info(f"📊 消息长度: {len(final_message)} 字符, {byte_length} 字节")

    # 企业微信markdown限制4096字节
    MAX_BYTES = 4000
    if byte_length > MAX_BYTES:
        logger.warning(f"⚠️ 消息 {byte_length} 字节超过限制，进行截断")
        encoded = final_message.encode('utf-8')
        truncated = encoded[:MAX_BYTES - 100]
        final_message = truncated.decode('utf-8', errors='ignore') + "\n\n...\n💡 *Powered By 异乡有你*"
        logger.info(f"📊 截断后: {len(final_message.encode('utf-8'))} 字节")

    # 发送消息
    logger.info("📤 正在发送新闻日报...")
    if send_wecom_message(final_message, msgtype="markdown"):
        logger.info("✅ 日报发送成功")
    else:
        logger.error("❌ 日报发送失败")


def fetch_topic_news_raw(topic_key: str) -> list:
    """获取单个主题的原始新闻列表（不做AI总结）"""
    logger.info(f"  └─ 获取主题: {topic_key}")
    keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
    return news_fetcher.fetch_news(topic_key, keywords, num=15)


def main():
    """主函数"""
    if not WECOM_WEBHOOK_URLS:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        logger.info("请在 .env 文件中设置企业微信Webhook URL")
        return

    logger.info("🚀 企业微信新闻机器人启动")
    
    # 解析环境变量决定推送哪些主题
    active_topics = parse_active_topics(ACTIVE_TOPICS_ENV)
    if not active_topics:
        active_topics = ['ai', 'education']
        
    logger.info(f"📡 开始执行新闻任务（{len(active_topics)}个主题）...")
    send_daily_news(active_topics)

if __name__ == '__main__':
    main()
