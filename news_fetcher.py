#!/usr/bin/env python3
"""
新闻API集成模块：多源抓取（TianAPI + RSS + NewsAPI）+ 管线编排。

评分/分级在 news_scoring.py，去重/多样性在 news_dedup.py（均为纯函数，
AUDIT 2026-07-05 行动项 #7 拆分）；主题→源映射与关键词表单一真相源在 config.py。
"""
import os
import requests
import feedparser
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

import news_dedup
import news_scoring
from config import RSS_FEEDS, TIANAPI_ENDPOINTS, TOPIC_KEYWORDS
from http_util import make_retry_session

# 加载环境变量（override=True：.env 优先于宿主残留 export，详见 config.py）
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class NewsFetcher:
    """新闻获取器"""

    def __init__(self):
        # 统一的HTTP会话 + 重试，提升请求稳定性
        self.session = make_retry_session()
        self.timeout = 10

        # 天行数据API配置（主题→接口映射见 config.TIANAPI_ENDPOINTS）
        self.tianapi_key = os.getenv('TIANAPI_KEY')
        self.tianapi_endpoints = TIANAPI_ENDPOINTS

        # NewsAPI配置
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.newsapi_base = "https://newsapi.org/v2"

        # RSS订阅源（主题→源列表见 config.RSS_FEEDS）
        self.rss_feeds = RSS_FEEDS

        # RSS 结果文件缓存：JSON 存项目内 assets/cache/rss/（已 gitignore）。
        # 不用 /tmp + pickle：共享主机 /tmp 可被其他本地用户预植恶意 pickle
        # （反序列化即代码执行），且旧实现从不清理（AUDIT 2026-07-05 C4）
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'assets', 'cache', 'rss'
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_ttl = 3600  # 1小时缓存
        self._cleanup_cache()

    # ── 兼容代理：实现拆至 news_scoring / news_dedup，签名不变 ──
    _keyword_in_text = staticmethod(news_scoring.keyword_in_text)
    calculate_news_quality = staticmethod(news_scoring.calculate_news_quality)
    _calculate_education_relevance = staticmethod(news_scoring.calculate_education_relevance)
    classify_signal_level = staticmethod(news_scoring.classify_signal_level)
    contains_negative_keywords = staticmethod(news_scoring.contains_negative_keywords)
    clean_rss_time = staticmethod(news_scoring.clean_rss_time)
    is_news_recent = staticmethod(news_scoring.is_news_recent)
    calculate_similarity = staticmethod(news_dedup.calculate_similarity)
    apply_diversity_filter = staticmethod(news_dedup.apply_diversity_filter)
    _normalize_url = staticmethod(news_dedup.normalize_url)
    _canonical_id = staticmethod(news_dedup.canonical_id)

    def _is_low_value_url(self, url: str) -> bool:
        """判定低价值/不可核验链接，抓取阶段直接丢弃。

        目前针对 36氪快讯（`/newsflashes/<纯数字>`）：slug 是无意义数字 ID，
        既是泛商业噪音、又无法事后按 slug 语义核验/去重。常规文章页
        （如 `36kr.com/p/<id>`）不受影响。
        """
        if not url:
            return False
        return "/newsflashes/" in url.lower()

    def fetch_tianapi_news(self, topic: str, keyword: str = None, num: int = 5) -> List[Dict]:
        """
        从天行数据获取新闻（支持多个主题接口）

        Args:
            topic: 新闻主题（finance/startup/education等）
            keyword: 搜索关键词（用于国内新闻接口）
            num: 获取数量

        Returns:
            新闻列表
        """
        if not self.tianapi_key:
            logger.warning("未配置TIANAPI_KEY，跳过天行数据")
            return []

        # 获取该主题对应的API接口
        endpoint = self.tianapi_endpoints.get(topic)
        if not endpoint:
            logger.warning(f"未配置主题'{topic}'的天行数据接口")
            return []

        try:
            # 使用HTTPS域名 + 对应主题的接口
            url = f"https://apis.tianapi.com{endpoint}"
            params = {
                'key': self.tianapi_key,
                'num': num
            }

            # 对于使用国内新闻接口的主题，添加关键词搜索
            if endpoint == '/guonei/index' and keyword:
                params['word'] = keyword
                logger.info(f"  └─ 使用天行数据国内新闻接口，关键词: {keyword}")
            else:
                logger.info(f"  └─ 使用天行数据接口: {endpoint}")

            response = self.session.post(url, data=params, timeout=self.timeout)
            data = response.json()

            if data.get('code') == 200:
                news_list = []
                result = data.get('result', {})
                newslist = result.get('newslist', [])

                for item in newslist:
                    news_list.append({
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'source': item.get('source', '天行数据'),
                        'url': item.get('url', ''),
                        'id': item.get('url', ''),
                        'time': item.get('ctime', ''),
                        'picUrl': item.get('picUrl', '')
                    })
                logger.info(f"✅ 天行数据获取{len(news_list)}条{topic}新闻")
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

            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get('status') == 'ok':
                news_list = []
                for item in data.get('articles', []):
                    news_list.append({
                        'title': item.get('title'),
                        'description': item.get('description', ''),
                        'source': item.get('source', {}).get('name', 'NewsAPI'),
                        'url': item.get('url', ''),
                        'id': item.get('url', ''),
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

    def _cache_path(self, key: str) -> str:
        import hashlib
        return os.path.join(
            self.cache_dir, hashlib.md5(key.encode('utf-8')).hexdigest() + '.json'
        )

    def _get_cache(self, key: str):
        """读取缓存（JSON；过期/损坏返回 None）"""
        import json
        import time

        cache_path = self._cache_path(key)
        if os.path.exists(cache_path):
            mtime = os.path.getmtime(cache_path)
            if time.time() - mtime < self.cache_ttl:
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
        return None

    def _set_cache(self, key: str, data: Any):
        """写入缓存（JSON）"""
        import json

        try:
            with open(self._cache_path(key), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")

    def _cleanup_cache(self, max_age_sec: int = 7 * 86400):
        """清掉早已过期的缓存文件（旧实现只写不删，文件无限累积）"""
        import time

        cutoff = time.time() - max_age_sec
        try:
            for name in os.listdir(self.cache_dir):
                path = os.path.join(self.cache_dir, name)
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.remove(path)
        except OSError as e:
            logger.warning(f"清理缓存失败: {e}")

    def fetch_rss_news(self, topic_key: str, num: int = 5) -> List[Dict]:
        """
        从RSS订阅源获取新闻（并行处理 + 缓存）

        Args:
            topic_key: 主题关键字
            num: 获取数量

        Returns:
            新闻列表
        """
        import concurrent.futures

        feeds = self.rss_feeds.get(topic_key, [])
        if not feeds:
            logger.info(f"未配置{topic_key}的RSS源")
            return []

        all_news = []

        def fetch_single_feed(feed_url):
            def looks_like_feed_bytes(data: bytes) -> bool:
                if not data:
                    return False
                head = data.lstrip()[:400].lower()
                return head.startswith(b'<?xml') or b'<rss' in head or b'<feed' in head

            # 1. 尝试读取缓存
            cached_news = self._get_cache(feed_url)
            if cached_news is not None:
                logger.debug(f"  └─ [缓存命中] {feed_url[:30]}...")
                return cached_news

            # 2. 如果无缓存，发起网络请求
            try:
                logger.info(f"  └─ [网络请求] 从RSS获取: {feed_url[:50]}...")

                # 使用requests获取内容，带上User-Agent以绕过反爬
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'
                }

                content = None
                try:
                    response = self.session.get(feed_url, headers=headers, timeout=15)
                    status = response.status_code
                    content_type = (response.headers.get('Content-Type') or '').lower()

                    if status >= 400:
                        # 明确不存在的资源不要继续“直接解析”，避免产生大量 XML/HTML 解析噪音
                        if status in (404, 410):
                            logger.warning(f"⚠️ RSS请求失败 {feed_url}: HTTP {status}（跳过）")
                            return []

                        # 某些站点会返回非200但仍携带可解析的XML内容（如 403/429/5xx 的缓存页）
                        if response.content and ('xml' in content_type or looks_like_feed_bytes(response.content)):
                            content = response.content
                        else:
                            response.raise_for_status()
                    else:
                        content = response.content
                except requests.exceptions.HTTPError as req_err:
                    logger.warning(f"⚠️ RSS请求失败 {feed_url}: {req_err}")
                    return []
                except Exception as req_err:
                    logger.warning(f"⚠️ RSS请求失败 {feed_url}: {req_err}，尝试直接解析...")
                    # 如果请求失败（超时/连接问题等），尝试直接用feedparser解析（作为后备）
                    content = None

                if content:
                    feed = feedparser.parse(content)
                else:
                    feed = feedparser.parse(feed_url)

                if feed.bozo and not feed.entries:
                    logger.warning(f"⚠️ RSS解析警告 {feed_url}: {feed.bozo_exception}")
                    return []

                feed_news = []
                for entry in feed.entries[:num]:
                    # 提取新闻信息
                    # 尝试多种时间字段
                    pub_time = entry.get('published', entry.get('updated', entry.get('pubDate', '')))
                    entry_id = entry.get('id', entry.get('guid', ''))
                    entry_url = entry.get('link', '')
                    # 丢弃低价值/不可核验链接（如 36氪快讯 /newsflashes/<数字>）
                    if self._is_low_value_url(entry_url):
                        logger.debug(f"🗑️ 跳过低价值链接: {entry.get('title', '')[:40]}... ({entry_url})")
                        continue
                    news_item = {
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', entry.get('description', ''))[:200],
                        'source': feed.feed.get('title', 'RSS'),
                        'url': entry_url,
                        'id': entry_id,
                        'time': pub_time
                    }
                    feed_news.append(news_item)

                if feed_news:
                    logger.info(f"✅ RSS获取{len(feed_news)}条新闻 ({feed_url[:30]}...)")
                    # 3. 写入缓存
                    self._set_cache(feed_url, feed_news)
                else:
                    logger.info(f"⚠️ RSS无内容 ({feed_url[:30]}...)")

                return feed_news
            except Exception as e:
                logger.error(f"❌ RSS解析失败 {feed_url}: {e}")
                return []

        # 并行获取所有RSS源
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(feeds), 8)) as executor:
            future_to_url = {executor.submit(fetch_single_feed, url): url for url in feeds}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    feed_news = future.result()
                    all_news.extend(feed_news)
                except Exception as exc:
                    logger.error(f"❌ RSS任务异常: {exc}")

        # 返回所有新闻，不在这里截断（让后续的质量评分和去重来筛选）
        return all_news

    def fetch_news(self, topic: str, keywords: List[str], num: int = 10) -> List[Dict]:
        """
        获取新闻（从所有源合并：API + RSS，并行处理）

        Args:
            topic: 主题名称（finance/startup等）
            keywords: 搜索关键词列表
            num: 最终返回的数量（会从所有源获取更多，然后筛选）

        Returns:
            新闻列表（合并去重后的高质量新闻）
        """
        import concurrent.futures
        all_news = []

        # 定义各个获取任务
        def task_tianapi():
            if self.tianapi_key and keywords:
                # 使用第一个关键词作为搜索词（对于国内新闻接口）
                return self.fetch_tianapi_news(topic, keyword=keywords[0], num=5)
            return []

        def task_rss():
            # 获取更多RSS新闻以应对过滤（从5条增加到30条）
            return self.fetch_rss_news(topic, num=30)

        def task_newsapi():
            results = []
            if self.newsapi_key:
                # NewsAPI限制通常较严：拿到第一个有结果的关键词就停
                for keyword in keywords:
                    news = self.fetch_newsapi_news(keyword, num=3)
                    results.extend(news)
                    if news:
                        break
            return results

        # 并行执行三大类源的获取
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(task_tianapi): "TianAPI",
                executor.submit(task_rss): "RSS",
                executor.submit(task_newsapi): "NewsAPI"
            }

            for future in concurrent.futures.as_completed(futures):
                source_name = futures[future]
                try:
                    news = future.result()
                    all_news.extend(news)
                    logger.info(f"✅ {source_name} 任务完成，获取 {len(news)} 条")
                except Exception as exc:
                    logger.error(f"❌ {source_name} 任务异常: {exc}")

        # 去重 + 负面词过滤 + 7天时效（news_dedup）
        unique_news = news_dedup.dedupe_news(all_news, max_days=7)

        # 质量评分和排序（news_scoring）
        for news in unique_news:
            news['quality_score'] = news_scoring.calculate_news_quality(news, keywords)

        # 按质量分数降序排序
        unique_news.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

        logger.info(f"📰 {topic}: 从所有源获取{len(unique_news)}条真实新闻，已按质量排序")

        # 应用多样性过滤器（每个来源最多2条）
        diverse_news = news_dedup.apply_diversity_filter(unique_news, max_per_source=2)
        logger.info(f"🔍 多样性过滤: {len(unique_news)} -> {len(diverse_news)} 条")

        # 返回高质量新闻（只返回评分>30的新闻）
        quality_news = [n for n in diverse_news if n.get('quality_score', 0) > 30]

        if not quality_news:
            # 如果没有高质量新闻，至少返回评分最高的几条
            return diverse_news[:num]

        return quality_news[:num]  # 返回前N条高质量新闻（默认10条）

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
            description = news.get('description') or ''
            desc_preview = description[:200]
            formatted.append(
                f"{i}. {news['title']}\n"
                f"   来源: {news['source']}\n"
                f"   摘要: {desc_preview}...\n"
                f"   链接: {news['url']}\n"
            )

        return "\n".join(formatted)


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

    print("测试获取教育新闻...")
    news = get_real_news('education', num=3)

    if news:
        print(f"\n✅ 获取到 {len(news)} 条新闻：\n")
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   来源: {item['source']}")
            print(f"   链接: {item['url']}\n")
    else:
        print("❌ 未获取到新闻")
