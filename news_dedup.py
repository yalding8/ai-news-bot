"""新闻去重/多样性纯函数（AUDIT 2026-07-05 行动项 #7，自 news_fetcher 拆出）。

无 IO、无状态：URL/id 规范化去重键、标题相似度、跨源去重管线、来源多样性。
"""
import logging
from typing import Dict, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from news_scoring import contains_negative_keywords, is_news_recent

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """规范化URL用于去重：去掉追踪参数、fragment，统一host/scheme并排序query。"""
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())
        if not parts.scheme or not parts.netloc:
            return url.strip()

        scheme = parts.scheme.lower()
        netloc = parts.netloc.lower()

        # 去掉默认端口
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        path = parts.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        # 过滤常见追踪参数
        tracking_keys = {
            "gclid",
            "fbclid",
            "igshid",
            "mc_cid",
            "mc_eid",
            "ref",
            "ref_src",
            "spm",
        }
        filtered_qs = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            key_stripped = (key or "").strip()
            if not key_stripped:
                continue
            key_lower = key_stripped.lower()
            if key_lower.startswith("utm_") or key_lower in tracking_keys:
                continue
            filtered_qs.append((key_stripped, value))
        filtered_qs.sort(key=lambda kv: (kv[0].lower(), kv[1]))

        query = urlencode(filtered_qs, doseq=True)
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return url.strip()


def canonical_id(value: str) -> str:
    """把 guid/id 规范成可比对的去重键（如果像URL则走URL规范化）。"""
    if not value:
        return ""
    raw = str(value).strip()
    if raw.lower().startswith(("http://", "https://")):
        return normalize_url(raw)
    return raw


def calculate_similarity(news1: Dict, news2: Dict) -> float:
    """标题相似度 70% + 描述相似度 30%（描述过短时退化为纯标题）。"""
    from difflib import SequenceMatcher

    title_sim = SequenceMatcher(None, news1.get('title', ''), news2.get('title', '')).ratio()

    desc1 = news1.get('description', '')
    desc2 = news2.get('description', '')

    if len(desc1) > 10 and len(desc2) > 10:
        desc_sim = SequenceMatcher(None, desc1, desc2).ratio()
        return title_sim * 0.7 + desc_sim * 0.3
    else:
        return title_sim


def dedupe_news(all_news: List[Dict], max_days: int = 7,
                similarity_threshold: float = 0.75) -> List[Dict]:
    """跨源去重 + 负面词过滤 + 时效过滤。

    去重键依次：canonical id/guid → 规范化 URL → 相似度（>threshold）→ 精确标题。
    返回保序的 unique 列表。
    """
    seen_urls = set()
    seen_ids = set()
    seen_titles = set()
    unique_news: List[Dict] = []

    for news in all_news:
        title = str(news.get('title') or '').strip()
        description = news.get('description', '')
        news_time = news.get('time', '')

        cid = canonical_id(news.get('id') or news.get('guid') or '')
        normalized_url = normalize_url(news.get('url', ''))

        if cid and cid in seen_ids:
            logger.debug(f"❌ 去重(id/guid): {title[:50]}...")
            continue
        if normalized_url and normalized_url in seen_urls:
            logger.debug(f"❌ 去重(url): {title[:50]}...")
            continue

        if contains_negative_keywords(title, description):
            logger.debug(f"🗑️ 过滤无关新闻: {title[:50]}... (包含负面关键词)")
            continue

        # 相似度去重（O(n²)，当前每日候选量级 <100 可接受）
        is_duplicate = False
        for existing_news in unique_news:
            similarity = calculate_similarity(news, existing_news)
            if similarity > similarity_threshold:
                logger.debug(
                    f"❌ 智能去重: '{title[:30]}...' 与 '{existing_news['title'][:30]}...' 相似度 {similarity:.2f}"
                )
                is_duplicate = True
                break
        if is_duplicate:
            continue

        if title not in seen_titles and is_news_recent(news_time, max_days=max_days):
            seen_titles.add(title)
            unique_news.append(news)
            if normalized_url:
                seen_urls.add(normalized_url)
            if cid:
                seen_ids.add(cid)
            logger.debug(f"✅ 保留新闻: {title[:50]}... (时间: {news_time})")
        elif title in seen_titles:
            logger.debug(f"❌ 去重(标题匹配): {title[:50]}...")
        else:
            logger.debug(f"❌ 过时: {title[:50]}... (时间: {news_time})")

    return unique_news


def apply_diversity_filter(news_list: List[Dict], max_per_source: int = 2) -> List[Dict]:
    """来源多样性：每个来源最多保留 max_per_source 条（输入需已按优先级排序）。"""
    source_counts = {}
    filtered_news = []

    for news in news_list:
        source = news.get('source', 'Unknown')
        count = source_counts.get(source, 0)
        if count < max_per_source:
            filtered_news.append(news)
            source_counts[source] = count + 1
        else:
            logger.debug(f"🔍 过滤掉同源新闻: {news['title']} (来源: {source})")

    return filtered_news
