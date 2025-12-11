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

from config import (
    WECOM_WEBHOOK_URLS, 
    NEWS_TOPICS, 
    ACTIVE_TOPICS_ENV, 
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
    发送每日新闻汇总（合并为一条消息）

    Args:
        topics: 要发送的主题列表
    """
    if topics is None:
        topics = list(NEWS_TOPICS.keys())

    logger.info(f"📰 开始处理每日新闻，主题数量: {len(topics)}")
    
    # 并行处理所有主题（移除跨主题去重，允许重要新闻多角度曝光）
    results = []
    # shared_seen_titles = set()
    # lock = threading.Lock()
    
    # 使用 ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(topics), 5)) as executor:
        future_to_topic = {
            executor.submit(process_topic_news, topic): topic
            for topic in topics
        }
        for future in concurrent.futures.as_completed(future_to_topic):
            try:
                res = future.result()
                results.append(res)
            except Exception as exc:
                logger.error(f"❌ 处理异常: {exc}")

    # 按照原始topics顺序排序结果
    results.sort(key=lambda x: topics.index(x['topic_key']) if x.get('topic_key') in topics else 999)

    # 构造合并消息
    today_date = datetime.now().strftime("%Y年%m月%d日")
    
    # 消息头部
    message_parts = [f"📅 **异乡早咖啡 - {today_date}**\n"]
    
    has_any_content = False
    
    for res in results:
        if not res.get("success"):
            message_parts.append(f"## ❌ {NEWS_TOPICS.get(res.get('topic_key', ''), {}).get('name', '未知主题')}")
            message_parts.append(f"⚠️ 获取失败: {res.get('error')}\n")
            continue

        # 添加主题标题
        message_parts.append(f"## {res['emoji']} {res['topic_name']}")
        message_parts.append(f"{res['content']}\n")
        
        # 添加链接（如果有）
        if res.get("news_links"):
            has_any_content = True
            links_text = "\n".join([f"• [{n['title']}]({n['url']})" for n in res['news_links']])
            message_parts.append(f"**🔗 精选来源**:\n{links_text}\n")
        
        message_parts.append("---")  # 分隔线

    # 移除最后一个分隔线
    if message_parts[-1] == "---":
        message_parts.pop()

    # 广告区域
    message_parts.append("---")
    message_parts.append("\n🏠 **异乡好居** - 全球长租预订平台 [点击查看](https://uhouzz.cn/a5yvnL80)")
    message_parts.append("💰 **异乡缴费** - 留学缴费省心省钱 [点击查看](https://uhouzz.cn/ebvn58O0)\n")

    # 消息尾部
    message_parts.append("💡 *Powered By 异乡有你，AI 驱动 • 实时聚合全球国际教育行业资讯*")

    final_message = "\n".join(message_parts)
    
    # 发送消息
    logger.info("📤 正在发送合并后的新闻日报...")
    if send_wecom_message(final_message, msgtype="markdown"):
        logger.info("✅ 日报发送成功")
    else:
        logger.error("❌ 日报发送失败")


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
