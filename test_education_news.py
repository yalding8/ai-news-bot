#!/usr/bin/env python3
"""
测试国际教育新闻获取和去重功能
"""

import sys
import os
sys.path.append('.')

from datetime import datetime
from news_fetcher import get_real_news
from news_cache import filter_new_news, mark_news_as_sent, news_cache
from config import get_logger

logger = get_logger(__name__)

def test_education_news():
    """测试国际教育新闻获取流程"""
    print("🧪 测试国际教育新闻获取和去重功能")
    print("=" * 60)
    print(f"测试时间: {datetime.now()}")
    print()
    
    # 1. 显示缓存统计
    print("📊 当前缓存状态:")
    stats = news_cache.get_cache_stats()
    print(f"  总主题数: {stats['total_topics']}")
    print(f"  总记录数: {stats['total_records']}")
    for topic, count in stats['topics'].items():
        print(f"  {topic}: {count} 条记录")
    print()
    
    # 2. 获取原始新闻
    print("📡 1. 获取国际教育新闻...")
    all_news = get_real_news('education', num=10)
    print(f"✅ 获取到 {len(all_news)} 条原始新闻")
    print()
    
    if all_news:
        print("📰 原始新闻列表:")
        for i, news in enumerate(all_news[:5], 1):
            print(f"  {i}. {news['title']}")
            print(f"     来源: {news['source']}")
            print(f"     时间: {news.get('time', '未知')}")
            print()
    
    # 3. 过滤重复新闻
    print("🔍 2. 过滤重复新闻...")
    new_news = filter_new_news('education', all_news)
    print(f"✅ 过滤后剩余 {len(new_news)} 条新新闻")
    print()
    
    if new_news:
        print("🆕 新新闻列表:")
        for i, news in enumerate(new_news, 1):
            print(f"  {i}. {news['title']}")
            print(f"     来源: {news['source']}")
            print(f"     时间: {news.get('time', '未知')}")
            print()
        
        # 4. 模拟推送成功，标记为已推送
        print("📝 3. 标记新闻为已推送...")
        mark_news_as_sent('education', new_news)
        print(f"✅ 已标记 {len(new_news)} 条新闻为已推送")
        print()
        
    else:
        print("ℹ️  所有新闻都已在24小时内推送过，缓存去重功能正常工作！")
        print()
    
    # 5. 再次测试过滤
    print("🔄 4. 再次测试过滤功能...")
    new_news_2 = filter_new_news('education', all_news)
    print(f"✅ 第二次过滤后剩余 {len(new_news_2)} 条新新闻")
    
    if len(new_news_2) < len(all_news):
        print("🎉 缓存去重功能工作正常！")
    else:
        print("⚠️  缓存可能未生效")
    
    print()
    print("=" * 60)
    print("🏁 测试完成")

if __name__ == '__main__':
    test_education_news()