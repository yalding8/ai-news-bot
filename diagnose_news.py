#!/usr/bin/env python3
"""
新闻获取诊断脚本
检查各个环节是否正常工作
"""

import sys
import os
sys.path.append('.')

from datetime import datetime
from news_fetcher import NewsFetcher, get_real_news
from news_cache import filter_new_news
from config import TOPIC_KEYWORDS, NEWS_TOPICS

def diagnose_education_news():
    """诊断教育新闻获取"""
    print("=" * 60)
    print("🔍 教育新闻获取诊断")
    print("=" * 60)
    print(f"时间: {datetime.now()}")
    print()
    
    # 1. 检查配置
    print("📋 1. 检查配置")
    print(f"   主题: {NEWS_TOPICS.get('education')}")
    print(f"   关键词: {TOPIC_KEYWORDS.get('education')}")
    print()
    
    # 2. 检查新闻源
    print("📡 2. 检查新闻源配置")
    fetcher = NewsFetcher()
    edu_feeds = fetcher.rss_feeds.get('education', [])
    print(f"   配置的RSS源数量: {len(edu_feeds)}")
    for i, feed in enumerate(edu_feeds, 1):
        print(f"   {i}. {feed}")
    print()
    
    # 3. 测试单个RSS源
    print("🧪 3. 测试单个RSS源")
    import feedparser
    test_url = 'https://www.insidehighered.com/rss.xml'
    print(f"   测试源: {test_url}")
    try:
        feed = feedparser.parse(test_url)
        print(f"   ✅ 成功获取 {len(feed.entries)} 条新闻")
        if feed.entries:
            print(f"   最新: {feed.entries[0].title}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    print()
    
    # 4. 测试完整获取流程
    print("🔄 4. 测试完整获取流程")
    try:
        all_news = get_real_news('education', num=15)
        print(f"   原始新闻数量: {len(all_news)}")
        
        if all_news:
            print(f"   新闻来源统计:")
            sources = {}
            for news in all_news:
                source = news.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            for source, count in sources.items():
                print(f"     - {source}: {count}条")
            
            print(f"\n   前3条新闻:")
            for i, news in enumerate(all_news[:3], 1):
                print(f"   {i}. {news['title']}")
                print(f"      来源: {news['source']}")
                print(f"      质量分: {news.get('quality_score', 0):.1f}")
                print(f"      时间: {news.get('time', '未知')}")
        else:
            print("   ❌ 未获取到任何新闻")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. 测试缓存过滤
    print("🗂️  5. 测试缓存过滤")
    if all_news:
        try:
            new_news = filter_new_news('education', all_news)
            print(f"   过滤前: {len(all_news)}条")
            print(f"   过滤后: {len(new_news)}条")
            print(f"   过滤率: {(1 - len(new_news)/len(all_news))*100:.1f}%")
            
            if len(new_news) == 0:
                print("   ⚠️  所有新闻都被过滤了（可能都是24小时内已推送）")
                print("   建议: 删除缓存文件 .news_cache.json 重新测试")
        except Exception as e:
            print(f"   ❌ 过滤失败: {e}")
    print()
    
    # 6. 检查环境变量
    print("⚙️  6. 检查环境变量")
    from dotenv import load_dotenv
    load_dotenv()
    
    tianapi_key = os.getenv('TIANAPI_KEY')
    newsapi_key = os.getenv('NEWSAPI_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    
    print(f"   TIANAPI_KEY: {'✅ 已配置' if tianapi_key else '❌ 未配置'}")
    print(f"   NEWSAPI_KEY: {'✅ 已配置' if newsapi_key else '❌ 未配置'}")
    print(f"   DEEPSEEK_API_KEY: {'✅ 已配置' if deepseek_key else '❌ 未配置'}")
    print()
    
    # 7. 总结
    print("=" * 60)
    print("📊 诊断总结")
    print("=" * 60)
    
    if all_news and len(all_news) > 0:
        if new_news and len(new_news) > 0:
            print("✅ 新闻获取正常，有新内容可推送")
        else:
            print("⚠️  新闻获取正常，但都被缓存过滤了")
            print("   解决方案: rm -f .news_cache.json")
    else:
        print("❌ 新闻获取失败，需要检查:")
        print("   1. 网络连接是否正常")
        print("   2. RSS源是否可访问")
        print("   3. 防火墙是否阻止")
        print("   4. 依赖是否完整安装")

if __name__ == '__main__':
    diagnose_education_news()
