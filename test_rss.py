#!/usr/bin/env python3
"""
测试RSS新闻源功能
"""
import logging
from news_fetcher import NewsFetcher

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_rss_feeds():
    """测试RSS订阅源"""
    fetcher = NewsFetcher()

    print("=" * 60)
    print("测试RSS新闻源")
    print("=" * 60)

    # 测试不同主题的RSS源
    topics = ['ai', 'finance', 'startup', 'education']

    for topic in topics:
        print(f"\n📰 测试主题: {topic}")
        print("-" * 60)

        news = fetcher.fetch_rss_news(topic, num=3)

        if news:
            print(f"✅ 获取到 {len(news)} 条新闻:\n")
            for i, item in enumerate(news, 1):
                print(f"{i}. {item['title']}")
                print(f"   来源: {item['source']}")
                print(f"   链接: {item['url']}")
                print()
        else:
            print(f"⚠️  未获取到新闻\n")

if __name__ == '__main__':
    test_rss_feeds()
