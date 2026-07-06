#!/usr/bin/env python3
"""
新闻API集成模块
支持多个新闻源，获取真实新闻数据（API + RSS）
"""
import os
import re
import requests
import feedparser
import logging
from typing import List, Dict, Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from dotenv import load_dotenv
from config import TOPIC_KEYWORDS, NEGATIVE_KEYWORDS
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

        # 天行数据API配置
        self.tianapi_key = os.getenv('TIANAPI_KEY')
        self.tianapi_base = "http://api.tianapi.com"

        # 天行数据API接口映射（不同主题对应不同的接口）
        self.tianapi_endpoints = {
            'finance': '/caijing/index',   # 财经新闻专用接口
            'startup': '/guonei/index',    # 创业新闻使用国内新闻+关键词

            # 国际教育服务行业专业主题
            'study_abroad': '/guonei/index',  # 留学资讯使用国内新闻+关键词
            'edu_policy': '/guonei/index',    # 教育政策使用国内新闻+关键词
            'uni_rankings': '/guonei/index',  # 院校排名使用国内新闻+关键词
            'market_data': '/guonei/index',    # 市场数据使用国内新闻+关键词
            'industry_news': '/guonei/index',   # 行业动态使用国内新闻+关键词

            # 原有主题
            'education': '/guonei/index',  # 教育新闻使用国内新闻+关键词
            'pbsa': '/guonei/index',       # PBSA新闻使用国内新闻+关键词
            'uhomes': '/guonei/index'      # Uhomes新闻使用国内新闻+关键词
        }

        # NewsAPI配置
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.newsapi_base = "https://newsapi.org/v2"
        
        # RSS 结果文件缓存：JSON 存项目内 assets/cache/rss/（已 gitignore）。
        # 不用 /tmp + pickle：共享主机 /tmp 可被其他本地用户预植恶意 pickle
        # （反序列化即代码执行），且旧实现从不清理（AUDIT 2026-07-05 C4）
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'assets', 'cache', 'rss'
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_ttl = 3600  # 1小时缓存
        self._cleanup_cache()

        # RSS订阅源配置
        self.rss_feeds = {
            'finance': [
                'https://www.36kr.com/feed',              # 36氪
                'http://dedicated.wallstreetcn.com/rss.xml', # 华尔街见闻
            ],
            'startup': [
                'http://www.cyzone.cn/rss/',              # 创业邦
                'https://www.36kr.com/feed',              # 36氪
                'https://hnrss.org/newest?q=startup',     # Hacker News Startup
            ],
            'study_abroad': [
                'https://thepienews.com/feed/',              # The PIE News
                'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
                'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
                'https://universitybusiness.com/feed/',      # University Business
                'https://monitor.icef.com/feed/',            # ICEF Monitor
                'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
            ],
            'edu_policy': [
                'https://thepienews.com/feed/',              # The PIE News
                'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
                'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
                'https://monitor.icef.com/feed/',            # ICEF Monitor
                'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                'https://www.gov.uk/government/organisations/uk-visas-and-immigration.atom',  # UKVI
                'https://www.gov.uk/government/organisations/home-office.atom',               # Home Office
                'https://www.gov.uk/government/organisations/department-for-education.atom',  # DfE
                'https://www.gov.uk/government/organisations/office-for-students.atom',       # OfS
            ],
            'uni_rankings': [
                'https://monitor.icef.com/feed/',            # ICEF Monitor
                'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
                'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
                'https://thepienews.com/feed/',              # The PIE News
            ],
            'market_data': [
                'https://monitor.icef.com/feed/',            # ICEF Monitor
                'https://thepienews.com/feed/',              # The PIE News
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
            ],
            'industry_news': [
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                # 36氪通用 feed 已移除：泛商业科技快讯污染国际教育主题（见 _is_low_value_url）
                'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
            ],
            'education': [
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                # 36氪通用 feed 已移除：泛商业科技快讯污染国际教育主题（见 _is_low_value_url）
                'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
                'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
            ],
            'pbsa': [
                'https://www.36kr.com/feed',
            ],
            'uhomes': [
                'https://www.36kr.com/feed',
            ],
        }

    def _is_low_value_url(self, url: str) -> bool:
        """判定低价值/不可核验链接，抓取阶段直接丢弃。

        目前针对 36氪快讯（`/newsflashes/<纯数字>`）：slug 是无意义数字 ID，
        既是泛商业噪音、又无法事后按 slug 语义核验/去重。常规文章页
        （如 `36kr.com/p/<id>`）不受影响。
        """
        if not url:
            return False
        return "/newsflashes/" in url.lower()

    def _normalize_url(self, url: str) -> str:
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

    def _canonical_id(self, value: str) -> str:
        """把 guid/id 规范成可比对的去重键（如果像URL则走URL规范化）。"""
        if not value:
            return ""
        raw = str(value).strip()
        if raw.lower().startswith(("http://", "https://")):
            return self._normalize_url(raw)
        return raw

    def fetch_tianapi_news(self, topic: str, keyword: str = None, num: int = 5) -> List[Dict]:
        """
        从天行数据获取新闻（支持多个主题接口）

        Args:
            topic: 新闻主题（ai/finance/startup/education/pbsa/uhomes）
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

    def calculate_similarity(self, news1: Dict, news2: Dict) -> float:
        """
        计算新闻相似度 (Phase 2 Task 2.1)
        
        Args:
            news1: 新闻1
            news2: 新闻2
            
        Returns:
            float: 相似度 (0-1)
        """
        from difflib import SequenceMatcher
        
        # 计算标题相似度 (权重 70%)
        title_sim = SequenceMatcher(None, news1.get('title', ''), news2.get('title', '')).ratio()
        
        # 计算描述相似度 (权重 30%)，如果描述很少，降低权重
        desc1 = news1.get('description', '')
        desc2 = news2.get('description', '')
        
        if len(desc1) > 10 and len(desc2) > 10:
            desc_sim = SequenceMatcher(None, desc1, desc2).ratio()
            return title_sim * 0.7 + desc_sim * 0.3
        else:
            return title_sim

    @staticmethod
    def _keyword_in_text(keyword: str, text: str) -> bool:
        """关键词匹配（AUDIT 2026-07-05 C1）。

        纯 ASCII 词要求命中位置在词首边界（允许复数等后缀）：杀掉
        'qs'→'faqs'、'the'→'weather' 这类词中误命中，同时保留旧子串行为里
        'ranking'→'rankings'、'visa'→'visas' 的合理命中。
        含中文的关键词按子串匹配（中文无词边界可用）。
        """
        if keyword.isascii():
            return re.search(rf"\b{re.escape(keyword)}", text) is not None
        return keyword in text

    def calculate_news_quality(self, news: Dict, topic_keywords: List[str]) -> float:
        """
        计算新闻质量分数（升级版 - Phase 1）

        Args:
            news: 新闻字典
            topic_keywords: 主题关键词列表

        Returns:
            质量分数（0-100）
        """
        score = 0.0

        # ========== Phase 1 新增：教育相关性检查 ==========
        title = news.get('title', '')
        description = news.get('description', '')

        relevance = self._calculate_education_relevance(title, description, topic_keywords)
        news['education_relevance'] = relevance  # 保存用于调试

        # 强制检查：相关性 < 0.3 直接淘汰
        if relevance < 0.3:
            logger.debug(f"❌ 相关性过低({relevance:.2f})，淘汰: {title[:40]}")
            return 0
        # ================================================

        # 1. 标题质量（15分）- 调整权重
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

        # 3. 关键词相关度（25分）
        title_lower = title.lower()
        desc_lower = description.lower()
        keyword_matches = 0
        
        # 高价值关键词加分（如政策、签证、突发）。
        # THE 排名必须写全称：裸 'the' 会命中几乎所有英文标题（AUDIT 2026-07-05 C1）
        high_value_keywords = ['visa', 'policy', 'visa policy', 'breaking', 'ranking', 'qs', 'times higher education', 'immigration', 'urgent', '签证', '政策', '排名', '最新', '发布']
        for hw in high_value_keywords:
            if self._keyword_in_text(hw, title_lower):
                score += 5 # 标题每匹配到一个高价值词 +5
            elif self._keyword_in_text(hw, desc_lower):
                score += 2 # 描述每匹配到一个高价值词 +2
        
        for keyword in topic_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title_lower:
                keyword_matches += 3 # 提升标题关键词权重
            if keyword_lower in desc_lower:
                keyword_matches += 1
        score += min(keyword_matches * 5, 25)

        # ========== Phase 1 修改：动态来源评分 ==========
        # 4. 来源可信度（30分）
        source = str(news.get('source', '') or '').lower()

        # 教育专业媒体：固定高分（35分）
        education_sources = [
            'inside higher ed', 'the pie news', 'icef',
            'jiemodui', '芥末堆', 'duozhi', '多知',
            'study international', 'university business',
            'university affairs', 'wonkhe', 'campus review',
        ]

        # 泛科技媒体：基础分 × 相关性系数（25分基础）
        tech_sources = [
            'techcrunch', '36kr', 'venturebeat',
            'latepost', '晚点', 'caixin', '财新'
        ]

        # 学术权威媒体：固定高分（30分）
        academic_sources = ['nature', 'science', 'mit technology review']

        # 其他优质媒体：固定中等分（20分）
        quality_sources = [
            'qs', 'topuniversities', 'higher ed dive',
            'bloomberg', 'reuters',
        ]

        if any(s in source for s in education_sources):
            score += 35  # 教育媒体最高分
            logger.debug(f"✅ 教育专业媒体: {source}")
        elif any(s in source for s in academic_sources):
            score += 30  # 学术权威
            logger.debug(f"📚 学术权威媒体: {source}")
        elif any(s in source for s in tech_sources):
            # ✨ 关键改动：泛科技媒体打折
            base_score = 25
            adjusted_score = base_score * relevance
            score += adjusted_score
            logger.debug(f"⚖️ 泛科技媒体打折: {source} (基础{base_score} × 相关性{relevance:.2f} = {adjusted_score:.1f})")
        elif any(s in source for s in quality_sources):
            score += 20  # 优质媒体
            logger.debug(f"📰 优质媒体: {source}")
        elif news.get('source'):
            score += 10 * relevance  # 其他来源也打折
            logger.debug(f"🔍 其他来源: {source} (10 × {relevance:.2f} = {10 * relevance:.1f})")
        # ================================================

        # 5. 时效性评分 (20分) - 新增
        try:
            from dateutil import parser
            from datetime import datetime
            
            # 使用现有方法检查，但这里我们计算具体天数给分
            cleaned_time = self.clean_rss_time(news.get('time', ''))
            if cleaned_time:
                news_date = parser.parse(cleaned_time)
                # 统一时区处理，避免报错
                if news_date.tzinfo is None:
                    now = datetime.now()
                else:
                    now = datetime.now(news_date.tzinfo)
                    
                diff = now - news_date
                days = diff.days
                
                if days < 1:  # 24小时内
                    score += 20
                elif days < 2: # 48小时内
                    score += 15
                elif days < 3: # 3天内
                    score += 10
                elif days < 7: # 一周内
                    score += 5
        except Exception:
            pass # 解析失败不加分

        # 6. 负面关键词惩罚（-20分）。词表单一真相源 config.NEGATIVE_KEYWORDS；
        # fetch_news 管线里含负面词的新闻已被 contains_negative_keywords 一票否决，
        # 此处惩罚是对直接调用本评分函数场景的兜底。
        text_lower = (title + ' ' + description).lower()
        for neg_kw in NEGATIVE_KEYWORDS:
            if neg_kw.lower() in text_lower:
                score -= 20
                logger.debug(f"⚠️ 负面关键词惩罚(-20): {neg_kw} | {title[:40]}")
                break  # 只惩罚一次

        # ========== Phase 1 新增：信号等级加权 ==========
        signal_level = self.classify_signal_level(news)
        news['signal_level'] = signal_level  # 保存标签

        if signal_level == 1:
            score *= 1.5
            logger.debug(f"✨ 一级信号加权(×1.5): {title[:40]}")
        elif signal_level == 2:
            score *= 1.2
            logger.debug(f"📊 二级信号加权(×1.2): {title[:40]}")
        # ================================================

        return max(score, 0)  # 确保不为负数

    def _calculate_education_relevance(self, title: str, desc: str, keywords: List[str]) -> float:
        """
        计算教育相关性系数（0-1）

        核心逻辑：
        - 强相关词命中 → 系数 0.8-1.0
        - 弱相关词命中 → 系数 0.3-0.5
        - 无关键词命中 → 系数 0.1-0.2

        Args:
            title: 新闻标题
            desc: 新闻描述
            keywords: 主题关键词列表

        Returns:
            float: 相关性系数（0-1）
        """
        text = (title + ' ' + desc).lower()

        # ========== 新增：排除泛科技内容 ==========
        # 如果包含这些词，且没有强留学词，则降低相关性
        tech_irrelevant = [
            '大模型', 'agi', 'llm', 'gpt', '算力', '芯片', '半导体',
            '开源', 'transformer', '推理', '训练', 'token'
        ]

        if any(kw in text for kw in tech_irrelevant):
            # 检查是否有强留学词
            strong_edu = ['留学', '签证', '招生', '申请', 'study abroad', 'visa', 'admissions', 'international students']
            if not any(kw in text for kw in strong_edu):
                logger.debug(f"⚠️ 泛科技内容，降低相关性: {title[:40]}")
                return 0.1  # 泛科技但无留学词，降低相关性
        # ==========================================

        # 1. 强相关词（留学核心）
        strong_keywords = [
            'study abroad', 'international students', 'overseas education',
            'visa', 'admissions', 'scholarship', 'tuition', 'immigration',
            '留学', '签证', '招生', '申请', '移民', '奖学金'
        ]

        strong_match = sum(1 for kw in strong_keywords if kw in text)

        if strong_match >= 3:
            return 1.0  # 非常相关
        elif strong_match >= 1:
            return 0.8  # 较相关

        # 2. 弱相关词（泛教育）
        weak_keywords = ['education', 'university', 'student', 'college', '教育', '大学', '学生']
        weak_match = sum(1 for kw in weak_keywords if kw in text)

        if weak_match >= 2:
            return 0.5  # 弱相关
        elif weak_match >= 1:
            return 0.3  # 很弱相关

        return 0.1  # 基本不相关

    def classify_signal_level(self, news: Dict) -> int:
        """
        分类新闻信号等级（1-3）

        Returns:
            1: 一级信号（事实变更：政策、签证、招生截止日期）
            2: 二级信号（权威解读：数据报告、行业分析）
            3: 三级信号（泛资讯：融资、观点、合作）
        """
        title = news.get('title', '').lower()
        source = str(news.get('source', '')).lower()
        url = news.get('url', '').lower()

        # 一级信号判断
        level1_domains = ['.gov', '.edu', 'gov.uk', 'state.gov', 'uscis.gov', 'homeaffairs.gov.au']
        level1_keywords = [
            'policy', 'regulation', 'visa update', 'deadline', 'application open',
            '政策', '新规', '签证', '截止日期', '开放申请', '放榜', '录取'
        ]

        if any(d in url for d in level1_domains):
            return 1
        if any(kw in title for kw in level1_keywords):
            return 1

        # 二级信号判断
        level2_sources = [
            'pie news', 'icef', 'inside higher ed',
            '芥末堆', 'university affairs', 'wonkhe', 'campus review',
            'qs', 'topuniversities', 'higher ed dive',
        ]
        level2_keywords = [
            'report', 'statistics', 'survey', 'white paper', 'data release',
            '报告', '数据', '统计', '调查', '白皮书', '趋势分析'
        ]

        if any(s in source for s in level2_sources):
            return 2
        if any(kw in title for kw in level2_keywords):
            return 2

        # 三级信号
        return 3

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

    def contains_negative_keywords(self, title: str, description: str = "") -> bool:
        """
        检查是否包含负面关键词（需要过滤的内容）
        
        Args:
            title: 新闻标题
            description: 新闻描述
            
        Returns:
            bool: 是否包含负面关键词
        """
        text = (title + " " + str(description)).lower()
        
        for keyword in NEGATIVE_KEYWORDS:
            if keyword.lower() in text:
                logger.debug(f"    -> 匹配负面关键词: {keyword}")
                return True
                
        return False

    
    def clean_rss_time(self, time_str: str) -> str:
        """
        清洗RSS时间字符串，处理中文日期等问题
        
        Args:
            time_str: 原始时间字符串
            
        Returns:
            str: 清洗后的时间字符串
        """
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

    def is_news_recent(self, news_time: str, max_days: int = 7) -> bool:
        """
        检查新闻是否在指定天数内
        
        Args:
            news_time: 新闻时间字符串
            max_days: 最大天数
            
        Returns:
            bool: 是否为最近新闻
        """
        if not news_time:
            # 修改：如果没有时间信息，为了保守起见，认为是过期的（除非明确不需要时间过滤）
            # 或者可以尝试从其他字段提取，但这里简单设为False以避免旧闻
            return False 
            
        try:
            from dateutil import parser
            from datetime import datetime, timezone
            
            # 解析新闻时间
            # 先进行清洗
            cleaned_time = self.clean_rss_time(news_time)
            news_date = parser.parse(cleaned_time)
            
            #以此为基准：当前时间（带时区）
            now = datetime.now(news_date.tzinfo or timezone.utc)
            
            # 如果news_date也没时区，就都转为无时区
            if news_date.tzinfo is None:
                now = datetime.now()

            # 计算时间差
            diff = now - news_date
            
            logger.debug(f"时间检查: {news_time} -> {news_date} | Now: {now} | Diff days: {diff.days}")
            
            # 检查是否在指定天数内，且不能是未来的新闻（允许少量误差）
            return 0 <= diff.days <= max_days

            
        except Exception as e:
            logger.warning(f"解析新闻时间失败 '{news_time}': {e}")
            return False  # 修改：解析失败时默认认为是过期的

    def apply_diversity_filter(self, news_list: List[Dict], max_per_source: int = 2) -> List[Dict]:
        """
        应用多样性过滤器：限制每个来源的新闻数量
        
        Args:
            news_list: 已排序的新闻列表
            max_per_source: 每个来源允许的最大数量
            
        Returns:
            List[Dict]: 过滤后的新闻列表
        """
        source_counts = {}
        filtered_news = []
        
        for news in news_list:
            source = news.get('source', 'Unknown')
            # 简化来源名称以进行归一化（例如 "IT之家 RSS" -> "IT之家"）
            # 这里简单处理，直接使用完整source字符串
            
            count = source_counts.get(source, 0)
            if count < max_per_source:
                filtered_news.append(news)
                source_counts[source] = count + 1
            else:
                logger.debug(f"🔍 过滤掉同源新闻: {news['title']} (来源: {source})")
                
        return filtered_news

    def fetch_news(self, topic: str, keywords: List[str], num: int = 10) -> List[Dict]:
        """
        获取新闻（从所有源合并：API + RSS，并行处理）

        Args:
            topic: 主题名称（ai/finance/startup等）
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
                # NewsAPI也可以并行，但这里简单起见，只对关键词并行（如果有多个）
                # 或者直接串行，因为NewsAPI限制通常较严
                for keyword in keywords:
                    news = self.fetch_newsapi_news(keyword, num=3)
                    results.extend(news)
                    if news: # 只要获取到了就停止，避免过多请求
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

        # 去重和时间过滤（按标题去重，只保留最近7天的新闻）
        seen_urls = set()
        seen_ids = set()
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = str(news.get('title') or '').strip()
            description = news.get('description', '')
            news_time = news.get('time', '')

            canonical_id = self._canonical_id(news.get('id') or news.get('guid') or '')
            normalized_url = self._normalize_url(news.get('url', ''))

            if canonical_id and canonical_id in seen_ids:
                logger.debug(f"❌ 去重(id/guid): {title[:50]}...")
                continue
            if normalized_url and normalized_url in seen_urls:
                logger.debug(f"❌ 去重(url): {title[:50]}...")
                continue
            
            # 检查是否包含负面关键词
            if self.contains_negative_keywords(title, description):
                logger.debug(f"🗑️ 过滤无关新闻: {title[:50]}... (包含负面关键词)")
                continue

            # 检查是否重复和是否为最近新闻
            # 检查是否重复（使用智能相似度去重）
            is_duplicate = False
            for existing_news in unique_news:
                # 如果从 seen_titles 中找不到（说明之前没直接匹配上），但相似度很高
                similarity = self.calculate_similarity(news, existing_news)
                if similarity > 0.75: # 相似度阈值
                    logger.debug(f"❌ 智能去重: '{title[:30]}...' 与 '{existing_news['title'][:30]}...' 相似度 {similarity:.2f}")
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue

            if title not in seen_titles and self.is_news_recent(news_time, max_days=7):
                seen_titles.add(title)
                unique_news.append(news)
                if normalized_url:
                    seen_urls.add(normalized_url)
                if canonical_id:
                    seen_ids.add(canonical_id)
                logger.debug(f"✅ 保留新闻: {title[:50]}... (时间: {news_time})")
            elif title in seen_titles:
                logger.debug(f"❌ 去重(标题匹配): {title[:50]}...")
            else:
                logger.debug(f"❌ 过时: {title[:50]}... (时间: {news_time})")

        # 质量评分和排序
        for news in unique_news:
            news['quality_score'] = self.calculate_news_quality(news, keywords)

        # 按质量分数降序排序
        unique_news.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

        logger.info(f"📰 {topic}: 从所有源获取{len(unique_news)}条真实新闻，已按质量排序")

        # 应用多样性过滤器（每个来源最多2条）
        diverse_news = self.apply_diversity_filter(unique_news, max_per_source=2)
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
