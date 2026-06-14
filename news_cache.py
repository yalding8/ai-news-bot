#!/usr/bin/env python3
"""
新闻缓存管理模块
避免重复推送相同的新闻内容
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict
from config import get_logger

logger = get_logger(__name__)

class NewsCache:
    """新闻缓存管理器"""
    
    def __init__(self, cache_file: str = ".news_cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"📂 加载新闻缓存: {len(data.get('sent_news', {}))} 条记录")
                return data
            except Exception as e:
                logger.warning(f"⚠️ 加载缓存失败: {e}")
        
        return {
            "sent_news": {},  # {topic: {news_hash: timestamp}}
            "last_cleanup": datetime.now().isoformat()
        }
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
            logger.debug("💾 缓存已保存")
        except Exception as e:
            logger.error(f"❌ 保存缓存失败: {e}")
    
    def _get_news_hash(self, news: Dict) -> str:
        """生成新闻的唯一哈希值"""
        # 使用标题和URL生成哈希，避免相同新闻重复推送
        content = f"{news.get('title', '')}{news.get('url', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def is_news_sent(self, topic: str, news: Dict, hours: int = 24) -> bool:
        """
        检查新闻是否在指定时间内已推送过
        
        Args:
            topic: 新闻主题
            news: 新闻字典
            hours: 检查的时间范围（小时）
            
        Returns:
            bool: 是否已推送过
        """
        news_hash = self._get_news_hash(news)
        sent_news = self.cache_data.get("sent_news", {})
        topic_cache = sent_news.get(topic, {})
        
        if news_hash not in topic_cache:
            return False
        
        # 检查推送时间
        try:
            sent_time = datetime.fromisoformat(topic_cache[news_hash])
            time_diff = datetime.now() - sent_time
            
            if time_diff.total_seconds() / 3600 < hours:
                logger.debug(f"🔄 新闻已在{hours}小时内推送过: {news.get('title', '')[:50]}...")
                return True
            else:
                # 超过时间限制，可以重新推送
                logger.debug(f"⏰ 新闻超过{hours}小时，可重新推送: {news.get('title', '')[:50]}...")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ 解析推送时间失败: {e}")
            return False
    
    def mark_news_sent(self, topic: str, news_list: List[Dict]):
        """
        标记新闻为已推送
        
        Args:
            topic: 新闻主题
            news_list: 新闻列表
        """
        if "sent_news" not in self.cache_data:
            self.cache_data["sent_news"] = {}
        
        if topic not in self.cache_data["sent_news"]:
            self.cache_data["sent_news"][topic] = {}
        
        current_time = datetime.now().isoformat()
        
        for news in news_list:
            news_hash = self._get_news_hash(news)
            self.cache_data["sent_news"][topic][news_hash] = current_time
            logger.debug(f"✅ 标记已推送: {news.get('title', '')[:50]}...")
        
        self._save_cache()
        logger.info(f"📝 标记 {len(news_list)} 条{topic}新闻为已推送")
    
    def filter_unsent_news(self, topic: str, news_list: List[Dict], hours: int = 24) -> List[Dict]:
        """
        过滤出未推送的新闻
        
        Args:
            topic: 新闻主题
            news_list: 新闻列表
            hours: 检查的时间范围（小时）
            
        Returns:
            List[Dict]: 未推送的新闻列表
        """
        unsent_news = []
        
        for news in news_list:
            if not self.is_news_sent(topic, news, hours):
                unsent_news.append(news)
        
        logger.info(f"🔍 {topic}: 原有{len(news_list)}条新闻，过滤后{len(unsent_news)}条未推送")
        return unsent_news
    
    def cleanup_old_cache(self, days: int = 7):
        """
        清理过期的缓存记录
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        sent_news = self.cache_data.get("sent_news", {})
        
        for topic in list(sent_news.keys()):
            topic_cache = sent_news[topic]
            
            for news_hash in list(topic_cache.keys()):
                try:
                    sent_time = datetime.fromisoformat(topic_cache[news_hash])
                    if sent_time < cutoff_time:
                        del topic_cache[news_hash]
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ 清理缓存时解析时间失败: {e}")
                    del topic_cache[news_hash]
                    cleaned_count += 1
            
            # 如果主题下没有缓存了，删除主题
            if not topic_cache:
                del sent_news[topic]
        
        self.cache_data["last_cleanup"] = datetime.now().isoformat()
        self._save_cache()
        
        if cleaned_count > 0:
            logger.info(f"🧹 清理了 {cleaned_count} 条过期缓存记录")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        sent_news = self.cache_data.get("sent_news", {})
        stats = {
            "total_topics": len(sent_news),
            "total_records": sum(len(topic_cache) for topic_cache in sent_news.values()),
            "last_cleanup": self.cache_data.get("last_cleanup", "未知"),
            "topics": {}
        }
        
        for topic, topic_cache in sent_news.items():
            stats["topics"][topic] = len(topic_cache)
        
        return stats


# 全局缓存实例
news_cache = NewsCache()

def filter_new_news(topic: str, news_list: List[Dict]) -> List[Dict]:
    """
    过滤出新的（未推送过的）新闻
    
    Args:
        topic: 新闻主题
        news_list: 新闻列表
        
    Returns:
        List[Dict]: 新的新闻列表
    """
    return news_cache.filter_unsent_news(topic, news_list, hours=24)

def mark_news_as_sent(topic: str, news_list: List[Dict]):
    """
    标记新闻为已推送
    
    Args:
        topic: 新闻主题
        news_list: 新闻列表
    """
    news_cache.mark_news_sent(topic, news_list)

if __name__ == '__main__':
    # 测试代码
    cache = NewsCache()
    
    # 显示缓存统计
    stats = cache.get_cache_stats()
    print("📊 缓存统计:")
    print(f"  总主题数: {stats['total_topics']}")
    print(f"  总记录数: {stats['total_records']}")
    print(f"  上次清理: {stats['last_cleanup']}")
    
    for topic, count in stats['topics'].items():
        print(f"  {topic}: {count} 条记录")
    
    # 清理过期缓存
    cache.cleanup_old_cache(days=7)