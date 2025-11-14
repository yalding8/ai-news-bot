#!/usr/bin/env python3
"""
新闻API集成模块
支持多个新闻源，获取真实新闻数据（API + RSS）
"""
import os
import requests
import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class NewsFetcher:
    """新闻获取器"""

    def __init__(self):
        # 天行数据API配置
        self.tianapi_key = os.getenv('TIANAPI_KEY')
        self.tianapi_base = "http://api.tianapi.com"

        # NewsAPI配置
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.newsapi_base = "https://newsapi.org/v2"

        # RSS订阅源配置（免费、高质量）
        self.rss_feeds = {
            'ai': [
                'https://www.36kr.com/feed',
                'https://sspai.com/feed',
                'https://www.ithome.com/rss/',
            ],
            'finance': [
                'https://www.36kr.com/feed',
                'https://www.huxiu.com/rss/0.xml',
            ],
            'startup': [
                'https://www.36kr.com/feed',
                'https://www.huxiu.com/rss/0.xml',
            ],
            'education': [
                'https://www.36kr.com/feed',
            ],
            'pbsa': [
                'https://www.36kr.com/feed',
            ],
            'uhomes': [
                'https://www.36kr.com/feed',
            ]
        }

    def fetch_tianapi_news(self, topic: str, num: int = 5) -> List[Dict]:
        """
        从天行数据获取新闻（支持AI资讯接口）

        Args:
            topic: 新闻主题关键词
            num: 获取数量

        Returns:
            新闻列表
        """
        if not self.tianapi_key:
            logger.warning("未配置TIANAPI_KEY，跳过天行数据")
            return []

        try:
            # 天行数据的AI资讯接口
            # 使用HTTPS域名
            url = "https://apis.tianapi.com/ai/index"
            params = {
                'key': self.tianapi_key,
                'num': num
            }

            response = requests.post(url, data=params, timeout=10)
            data = response.json()

            if data.get('code') == 200:
                news_list = []
                result = data.get('result', {})
                newslist = result.get('newslist', [])

                for item in newslist:
                    news_list.append({
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'source': item.get('source', 'IT之家'),
                        'url': item.get('url', ''),
                        'time': item.get('ctime', ''),
                        'picUrl': item.get('picUrl', '')
                    })
                logger.info(f"✅ 天行数据获取{len(news_list)}条AI新闻")
                return news_list
            else:
                logger.error(f"❌ 天行数据API错误: {data.get('msg')}")
                return []

        except Exception as e:
            logger.error(f"❌ 天行数据请求失败: {e}")
            return []

    def fetch_newsapi_news(self, query: str, num: int = 5) -> List[Dict]:
        """
        从NewsAPI获取新闻

        Args:
            query: 搜索关键词
            num: 获取数量

        Returns:
            新闻列表
        """
        if not self.newsapi_key:
            logger.warning("未配置NEWSAPI_KEY，跳过NewsAPI")
            return []

        try:
            # NewsAPI的everything端点
            url = f"{self.newsapi_base}/everything"
            params = {
                'apiKey': self.newsapi_key,
                'q': query,
                'language': 'zh',  # 中文新闻
                'sortBy': 'publishedAt',  # 按时间排序
                'pageSize': num
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('status') == 'ok':
                news_list = []
                for item in data.get('articles', []):
                    news_list.append({
                        'title': item.get('title'),
                        'description': item.get('description', ''),
                        'source': item.get('source', {}).get('name', 'NewsAPI'),
                        'url': item.get('url', ''),
                        'time': item.get('publishedAt', '')
                    })
                logger.info(f"✅ NewsAPI获取{len(news_list)}条新闻")
                return news_list
            else:
                logger.error(f"❌ NewsAPI错误: {data.get('message')}")
                return []

        except Exception as e:
            logger.error(f"❌ NewsAPI请求失败: {e}")
            return []

    def fetch_rss_news(self, topic_key: str, num: int = 5) -> List[Dict]:
        """
        从RSS订阅源获取新闻

        Args:
            topic_key: 主题关键字
            num: 获取数量

        Returns:
            新闻列表
        """
        feeds = self.rss_feeds.get(topic_key, [])
        if not feeds:
            logger.info(f"未配置{topic_key}的RSS源")
            return []

        all_news = []
        for feed_url in feeds:
            try:
                logger.info(f"  └─ 从RSS获取: {feed_url[:50]}...")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:num]:
                    # 提取新闻信息
                    news_item = {
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', entry.get('description', ''))[:200],
                        'source': feed.feed.get('title', 'RSS'),
                        'url': entry.get('link', ''),
                        'time': entry.get('published', entry.get('updated', ''))
                    }
                    all_news.append(news_item)

                logger.info(f"✅ RSS获取{len(feed.entries[:num])}条新闻")

            except Exception as e:
                logger.error(f"❌ RSS解析失败 {feed_url}: {e}")
                continue

        return all_news[:num]

    def fetch_news(self, topic: str, keywords: List[str], num: int = 5) -> List[Dict]:
        """
        获取新闻（自动尝试多个源：API + RSS）

        Args:
            topic: 主题名称（用于日志）
            keywords: 搜索关键词列表
            num: 每个源获取的数量

        Returns:
            新闻列表（合并去重）
        """
        all_news = []

        # 第一优先级：天行数据API（已配置的AI资讯接口）
        for keyword in keywords:
            tianapi_news = self.fetch_tianapi_news(keyword, num)
            all_news.extend(tianapi_news)
            if tianapi_news:
                break  # 如果获取到了就不继续尝试其他关键词

        # 第二优先级：RSS订阅源（免费、高质量）
        if not all_news:
            rss_news = self.fetch_rss_news(topic, num)
            all_news.extend(rss_news)

        # 第三优先级：NewsAPI（需要配置）
        if not all_news:
            for keyword in keywords:
                newsapi_news = self.fetch_newsapi_news(keyword, num)
                all_news.extend(newsapi_news)
                if newsapi_news:
                    break

        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)

        logger.info(f"📰 {topic}: 获取{len(unique_news)}条真实新闻")
        return unique_news[:num]  # 返回前N条

    def format_news_for_ai(self, news_list: List[Dict]) -> str:
        """
        格式化新闻为AI可读的文本

        Args:
            news_list: 新闻列表

        Returns:
            格式化的文本
        """
        if not news_list:
            return "今日暂无相关新闻"

        formatted = []
        for i, news in enumerate(news_list, 1):
            formatted.append(
                f"{i}. {news['title']}\n"
                f"   来源: {news['source']}\n"
                f"   摘要: {news['description'][:100]}...\n"
                f"   链接: {news['url']}\n"
            )

        return "\n".join(formatted)


# 主题关键词映射
TOPIC_KEYWORDS = {
    'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'ChatGPT', 'DeepSeek', '大模型'],
    'finance': ['财经', '金融', '股市', '经济', '投资'],
    'startup': ['创业', '融资', '风投', 'VC', '投资'],
    'education': ['教育', '留学', '国际教育', '教育科技'],
    'pbsa': ['学生公寓', 'PBSA', '租房', '宿舍'],
    'uhomes': ['异乡好居', 'Uhomes', '留学生公寓']
}


def get_real_news(topic_key: str, num: int = 5) -> List[Dict]:
    """
    获取指定主题的真实新闻

    Args:
        topic_key: 主题关键字
        num: 获取数量

    Returns:
        新闻列表
    """
    fetcher = NewsFetcher()
    keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])

    return fetcher.fetch_news(topic_key, keywords, num)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试获取AI新闻
    print("测试获取AI新闻...")
    news = get_real_news('ai', num=3)

    if news:
        print(f"\n✅ 获取到 {len(news)} 条新闻：\n")
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   来源: {item['source']}")
            print(f"   链接: {item['url']}\n")
    else:
        print("❌ 未获取到新闻")
