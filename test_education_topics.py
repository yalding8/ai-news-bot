#!/usr/bin/env python3
"""
测试国际教育服务行业新闻主题
快速验证新配置是否正常工作
"""

import os
os.environ['ACTIVE_TOPICS'] = 'study_abroad'  # 测试单个主题

from news_fetcher import NewsFetcher
from config import NEWS_TOPICS, TOPIC_KEYWORDS, get_logger

logger = get_logger(__name__)

def test_topic(topic_key: str):
    """测试单个主题的新闻获取"""
    print(f"\n{'='*60}")
    print(f"测试主题: {NEWS_TOPICS[topic_key]['emoji']} {NEWS_TOPICS[topic_key]['name']}")
    print(f"{'='*60}\n")

    # 创建新闻获取器
    fetcher = NewsFetcher()

    # 获取关键词
    keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
    print(f"📋 关键词 ({len(keywords)}个):")
    print(f"   {', '.join(keywords[:10])}...")  # 显示前10个

    # 获取RSS源
    rss_feeds = fetcher.rss_feeds.get(topic_key, [])
    print(f"\n📡 RSS源 ({len(rss_feeds)}个):")
    for i, feed in enumerate(rss_feeds, 1):
        # 提取域名
        domain = feed.split('/')[2] if len(feed.split('/')) > 2 else feed
        print(f"   {i}. {domain}")

    # 获取新闻
    print(f"\n🔍 正在获取新闻...")
    try:
        news_list = fetcher.fetch_news(topic_key, keywords, num=5)
        print(f"✅ 成功获取 {len(news_list)} 条新闻\n")

        # 显示新闻标题
        if news_list:
            print("📰 新闻预览:")
            for i, news in enumerate(news_list, 1):
                print(f"\n{i}. {news.get('title', '无标题')}")
                print(f"   来源: {news.get('source', '未知')}")
                # 使用 time 字段，如果没有则显示 "未知"
                print(f"   时间: {news.get('time', '未知')}")
                if news.get('url'):
                    print(f"   链接: {news['url'][:80]}...")
        else:
            print("⚠️  未获取到新闻")
            print("可能原因：")
            print("  - RSS源暂时无法访问")
            print("  - 关键词匹配不到相关内容")
            print("  - 网络连接问题")
    except Exception as e:
        print(f"❌ 获取新闻失败: {e}")

    print(f"\n{'='*60}\n")

def main():
    """主函数：测试所有新增的教育主题"""
    print("\n🎓 国际教育服务行业新闻主题测试")
    print("="*60)

    # 测试的主题列表
    test_topics = [
        'study_abroad',    # 留学资讯
        'edu_policy',      # 教育政策
        'uni_rankings',    # 院校排名
        'edu_market',      # 教育市场
        'competitors',     # 行业动态
    ]

    print(f"\n将测试 {len(test_topics)} 个新主题\n")

    for topic in test_topics:
        try:
            test_topic(topic)
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 测试主题 {topic} 时出错: {e}\n")
            continue

    print("="*60)
    print("✅ 测试完成！")
    print("\n💡 下一步:")
    print("1. 查看上面的测试结果")
    print("2. 如果新闻获取正常，可以配置 .env 启用这些主题")
    print("3. 运行 python3 bot_wecom.py 开始正式使用")
    print("="*60)

if __name__ == '__main__':
    main()
