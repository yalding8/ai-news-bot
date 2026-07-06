"""新闻评分/分级纯函数（AUDIT 2026-07-05 行动项 #7，自 news_fetcher 拆出）。

无 IO、无状态：给定新闻 dict 与关键词表 → 质量分 / 相关性系数 / 信号等级。
所有关键词表单一真相源在 config.py。
"""
import logging
import re
from typing import Dict, List

from config import (
    HIGH_VALUE_KEYWORDS,
    NEGATIVE_KEYWORDS,
    RELEVANCE_STRONG_KEYWORDS,
    RELEVANCE_TECH_IRRELEVANT,
    RELEVANCE_WEAK_KEYWORDS,
    SIGNAL_LEVEL1_DOMAINS,
    SIGNAL_LEVEL1_KEYWORDS,
    SIGNAL_LEVEL2_KEYWORDS,
    SIGNAL_LEVEL2_SOURCES,
    SOURCE_TIERS,
)

logger = logging.getLogger(__name__)


def keyword_in_text(keyword: str, text: str) -> bool:
    """关键词匹配（AUDIT 2026-07-05 C1）。

    纯 ASCII 词要求命中位置在词首边界（允许复数等后缀）：杀掉
    'qs'→'faqs'、'the'→'weather' 这类词中误命中，同时保留旧子串行为里
    'ranking'→'rankings'、'visa'→'visas' 的合理命中。
    含中文的关键词按子串匹配（中文无词边界可用）。
    """
    if keyword.isascii():
        return re.search(rf"\b{re.escape(keyword)}", text) is not None
    return keyword in text


def contains_negative_keywords(title: str, description: str = "") -> bool:
    """是否命中一票否决负面词（词表：config.NEGATIVE_KEYWORDS）"""
    text = (title + " " + str(description)).lower()

    for keyword in NEGATIVE_KEYWORDS:
        if keyword.lower() in text:
            logger.debug(f"    -> 匹配负面关键词: {keyword}")
            return True

    return False


def clean_rss_time(time_str: str) -> str:
    """清洗RSS时间字符串，处理中文日期等问题"""
    if not time_str:
        return ""

    # 替换中文星期和月份
    replacements = [
        ('星期一', 'Mon'), ('星期二', 'Tue'), ('星期三', 'Wed'), ('星期四', 'Thu'), ('星期五', 'Fri'), ('星期六', 'Sat'), ('星期日', 'Sun'),
        ('周一', 'Mon'), ('周二', 'Tue'), ('周三', 'Wed'), ('周四', 'Thu'), ('周五', 'Fri'), ('周六', 'Sat'), ('周日', 'Sun'),
        ('十二月', 'Dec'), ('十一月', 'Nov'),
        ('一月', 'Jan'), ('二月', 'Feb'), ('三月', 'Mar'), ('四月', 'Apr'), ('五月', 'May'), ('六月', 'Jun'),
        ('七月', 'Jul'), ('八月', 'Aug'), ('九月', 'Sep'), ('十月', 'Oct')
    ]

    cleaned = time_str
    for k, v in replacements:
        cleaned = cleaned.replace(k, v)

    # 处理可能的 "2025年12月16日" 格式
    cleaned = cleaned.replace('年', '-').replace('月', '-').replace('日', '')

    return cleaned


def is_news_recent(news_time: str, max_days: int = 7) -> bool:
    """新闻是否在 max_days 内。无时间/解析失败/未来时间一律视为过期。"""
    if not news_time:
        return False

    try:
        from dateutil import parser
        from datetime import datetime, timezone

        cleaned_time = clean_rss_time(news_time)
        news_date = parser.parse(cleaned_time)

        now = datetime.now(news_date.tzinfo or timezone.utc)
        if news_date.tzinfo is None:
            now = datetime.now()

        diff = now - news_date
        logger.debug(f"时间检查: {news_time} -> {news_date} | Now: {now} | Diff days: {diff.days}")

        # 在指定天数内，且不能是未来的新闻（允许少量误差）
        return 0 <= diff.days <= max_days

    except Exception as e:
        logger.warning(f"解析新闻时间失败 '{news_time}': {e}")
        return False


def calculate_education_relevance(title: str, desc: str, keywords: List[str]) -> float:
    """教育相关性系数（0-1）：强留学词 0.8-1.0 / 弱教育词 0.3-0.5 / 无命中 0.1。"""
    text = (title + ' ' + desc).lower()

    # 泛科技内容且无强留学词 → 降为 0.1
    if any(kw in text for kw in RELEVANCE_TECH_IRRELEVANT):
        if not any(kw in text for kw in RELEVANCE_STRONG_KEYWORDS):
            logger.debug(f"⚠️ 泛科技内容，降低相关性: {title[:40]}")
            return 0.1

    strong_match = sum(1 for kw in RELEVANCE_STRONG_KEYWORDS if kw in text)
    if strong_match >= 3:
        return 1.0
    elif strong_match >= 1:
        return 0.8

    weak_match = sum(1 for kw in RELEVANCE_WEAK_KEYWORDS if kw in text)
    if weak_match >= 2:
        return 0.5
    elif weak_match >= 1:
        return 0.3

    return 0.1


def classify_signal_level(news: Dict) -> int:
    """信号等级：1=事实变更（政策/签证/截止日期）2=权威解读 3=泛资讯。"""
    title = news.get('title', '').lower()
    source = str(news.get('source', '')).lower()
    url = news.get('url', '').lower()

    if any(d in url for d in SIGNAL_LEVEL1_DOMAINS):
        return 1
    if any(kw in title for kw in SIGNAL_LEVEL1_KEYWORDS):
        return 1

    if any(s in source for s in SIGNAL_LEVEL2_SOURCES):
        return 2
    if any(kw in title for kw in SIGNAL_LEVEL2_KEYWORDS):
        return 2

    return 3


def calculate_news_quality(news: Dict, topic_keywords: List[str]) -> float:
    """
    新闻质量分（0-100+）。副作用：往 news 里写 education_relevance / signal_level。

    构成：相关性硬闸（<0.3 → 0）| 标题长度 15 | 描述 10 | 高价值词+主题词 ≤25+
    | 来源分层 20-35（泛科技×相关性打折）| 时效 20 | 负面词 -20 | 信号等级 ×1.2/×1.5
    """
    score = 0.0

    title = news.get('title', '')
    description = news.get('description', '')

    relevance = calculate_education_relevance(title, description, topic_keywords)
    news['education_relevance'] = relevance  # 保存用于调试

    # 硬闸：相关性 < 0.3 直接淘汰
    if relevance < 0.3:
        logger.debug(f"❌ 相关性过低({relevance:.2f})，淘汰: {title[:40]}")
        return 0

    # 1. 标题质量（15分）
    title_len = len(title)
    if 20 <= title_len <= 100:
        score += 15
    elif 10 <= title_len < 20 or 100 < title_len <= 150:
        score += 8

    # 2. 描述质量（10分）
    if len(description) > 50:
        score += 10
    elif len(description) > 20:
        score += 5

    # 3. 关键词相关度（≤25分）+ 高价值词加分
    title_lower = title.lower()
    desc_lower = description.lower()
    keyword_matches = 0

    for hw in HIGH_VALUE_KEYWORDS:
        if keyword_in_text(hw, title_lower):
            score += 5  # 标题每匹配到一个高价值词 +5
        elif keyword_in_text(hw, desc_lower):
            score += 2  # 描述每匹配到一个高价值词 +2

    for keyword in topic_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            keyword_matches += 3
        if keyword_lower in desc_lower:
            keyword_matches += 1
    score += min(keyword_matches * 5, 25)

    # 4. 来源可信度（20-35分，词表：config.SOURCE_TIERS）
    source = str(news.get('source', '') or '').lower()

    if any(s in source for s in SOURCE_TIERS['education']):
        score += 35  # 教育专业媒体最高分
        logger.debug(f"✅ 教育专业媒体: {source}")
    elif any(s in source for s in SOURCE_TIERS['academic']):
        score += 30  # 学术权威
        logger.debug(f"📚 学术权威媒体: {source}")
    elif any(s in source for s in SOURCE_TIERS['tech']):
        # 泛科技媒体按相关性打折
        adjusted_score = 25 * relevance
        score += adjusted_score
        logger.debug(f"⚖️ 泛科技媒体打折: {source} (基础25 × 相关性{relevance:.2f} = {adjusted_score:.1f})")
    elif any(s in source for s in SOURCE_TIERS['quality']):
        score += 20  # 优质媒体
        logger.debug(f"📰 优质媒体: {source}")
    elif news.get('source'):
        score += 10 * relevance  # 其他来源也打折
        logger.debug(f"🔍 其他来源: {source} (10 × {relevance:.2f} = {10 * relevance:.1f})")

    # 5. 时效性（20分）
    try:
        from dateutil import parser
        from datetime import datetime

        cleaned_time = clean_rss_time(news.get('time', ''))
        if cleaned_time:
            news_date = parser.parse(cleaned_time)
            if news_date.tzinfo is None:
                now = datetime.now()
            else:
                now = datetime.now(news_date.tzinfo)

            days = (now - news_date).days
            if days < 1:
                score += 20
            elif days < 2:
                score += 15
            elif days < 3:
                score += 10
            elif days < 7:
                score += 5
    except Exception:
        pass  # 解析失败不加分

    # 6. 负面关键词惩罚（-20分）。词表单一真相源 config.NEGATIVE_KEYWORDS；
    # fetch_news 管线里含负面词的新闻已被 contains_negative_keywords 一票否决，
    # 此处惩罚是对直接调用本评分函数场景的兜底。
    text_lower = (title + ' ' + description).lower()
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw.lower() in text_lower:
            score -= 20
            logger.debug(f"⚠️ 负面关键词惩罚(-20): {neg_kw} | {title[:40]}")
            break  # 只惩罚一次

    # 7. 信号等级加权
    signal_level = classify_signal_level(news)
    news['signal_level'] = signal_level

    if signal_level == 1:
        score *= 1.5
        logger.debug(f"✨ 一级信号加权(×1.5): {title[:40]}")
    elif signal_level == 2:
        score *= 1.2
        logger.debug(f"📊 二级信号加权(×1.2): {title[:40]}")

    return max(score, 0)
