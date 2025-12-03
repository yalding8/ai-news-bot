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
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
from config import TOPIC_KEYWORDS

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class NewsFetcher:
    """新闻获取器"""

    def __init__(self):
        # 统一的HTTP会话 + 重试，提升请求稳定性
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST"}
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = 10

        # 天行数据API配置
        self.tianapi_key = os.getenv('TIANAPI_KEY')
        self.tianapi_base = "http://api.tianapi.com"

        # 天行数据API接口映射（不同主题对应不同的接口）
        self.tianapi_endpoints = {
            'ai': '/ai/index',            # AI资讯专用接口
            'finance': '/caijing/index',   # 财经新闻专用接口
            'startup': '/guonei/index',    # 创业新闻使用国内新闻+关键词

            # 国际教育服务行业专业主题
            'study_abroad': '/guonei/index',  # 留学资讯使用国内新闻+关键词
            'edu_policy': '/guonei/index',    # 教育政策使用国内新闻+关键词
            'uni_rankings': '/guonei/index',  # 院校排名使用国内新闻+关键词
            'edu_market': '/guonei/index',    # 教育市场使用国内新闻+关键词
            'competitors': '/guonei/index',   # 竞品动态使用国内新闻+关键词

            # 原有主题
            'education': '/guonei/index',  # 教育新闻使用国内新闻+关键词
            'pbsa': '/guonei/index',       # PBSA新闻使用国内新闻+关键词
            'uhomes': '/guonei/index'      # Uhomes新闻使用国内新闻+关键词
        }

        # NewsAPI配置
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.newsapi_base = "https://newsapi.org/v2"

        # RSS订阅源配置（免费、高质量）
        # 为每个主题配置了更精准的RSS源，提高新闻相关性
        self.rss_feeds = {
            'ai': [
                'https://www.qbitai.com/feed',            # 量子位
                'https://www.jiqizhixin.com/rss',         # 机器之心
                'https://www.36kr.com/feed',              # 36氪科技新闻
                'https://sspai.com/feed',                 # 少数派
                'https://www.ithome.com/rss/',            # IT之家
                'https://www.huxiu.com/rss/0.xml',        # 虎嗅科技
                'https://feeds.feedburner.com/venturebeat/SZYF', # VentureBeat AI
                'https://techcrunch.com/feed/',           # TechCrunch
                'https://www.theverge.com/rss/index.xml', # The Verge
                'https://feeds.feedburner.com/oreilly/radar', # O'Reilly Radar
                'https://hnrss.org/newest?q=AI',          # Hacker News (AI topic)
                'http://feeds.arstechnica.com/arstechnica/index', # Ars Technica
                'https://www.wired.com/feed/category/science/latest/rss', # Wired Science
                'https://ai.googleblog.com/feeds/posts/default', # Google AI Blog（新增）
                'https://openai.com/blog/rss',            # OpenAI Blog（新增）
                'https://paperswithcode.com/rss.xml',     # Papers with Code（新增）
                'https://aiweekly.co/rss',                # AI Weekly（新增）
                'https://www.geekpark.net/rss',           # 极客公园（新增）
                'https://www.ifanr.com/feed',             # 爱范儿（新增）
                'https://www.pingwest.com/feed',          # PingWest品玩（新增）
            ],
            'finance': [
                'https://www.huxiu.com/rss/0.xml',        # 虎嗅财经
                'https://www.36kr.com/feed',              # 36氪（包含财经内容）
                'http://dedicated.wallstreetcn.com/rss.xml', # 华尔街见闻
            ],
            'startup': [
                'http://www.cyzone.cn/rss/',              # 创业邦
                'https://www.huxiu.com/rss/0.xml',        # 虎嗅创投
                'https://www.36kr.com/feed',              # 36氪创投
                'https://hnrss.org/newest?q=startup',     # Hacker News (Startup)
                'https://news.crunchbase.com/feed/',      # Crunchbase News（新增）
            ],
            # 国际教育服务行业专业RSS源
            'study_abroad': [
                # 留学行业权威媒体
                'https://thepienews.com/feed/',              # The PIE News（留学行业权威）
                'https://www.studyinternational.com/feed/',  # Study International
                'https://www.topuniversities.com/rss',       # QS 留学资讯
                # 官方机构
                'https://www.nafsa.org/rss.xml',             # NAFSA（美国国际教育者协会）
                # 中文留学媒体
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                'https://www.heibandongcha.com/feed',        # 黑板洞察
                'https://www.36kr.com/feed',                 # 36氪教育
            ],

            'edu_policy': [
                # 政策类RSS源
                'https://www.nafsa.org/rss.xml',             # NAFSA（美国国际教育）
                'https://thepienews.com/feed/',              # The PIE News（政策报道）
                'https://www.studyinternational.com/feed/',  # Study International
                'https://www.jiemodui.com/rss.xml',          # 芥末堆（中国教育政策）
            ],

            'uni_rankings': [
                # 排名类RSS源
                'https://www.topuniversities.com/rss',       # QS World Rankings
                'https://www.timeshighereducation.com/rss.xml', # Times Higher Education
                'https://www.universityworldnews.com/rss.php', # University World News
            ],

            'edu_market': [
                # 市场数据和分析
                'https://monitor.icef.com/feed/',            # ICEF Monitor（留学市场数据）
                'https://thepienews.com/feed/',              # The PIE News
                'https://www.jiemodui.com/rss.xml',          # 芥末堆（市场分析）
                'https://www.heibandongcha.com/feed',        # 黑板洞察
                'https://www.edsurge.com/news.rss',          # EdSurge
            ],

            'competitors': [
                # 竞品和行业动态
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                'https://www.heibandongcha.com/feed',        # 黑板洞察
                'https://www.36kr.com/feed',                 # 36氪（融资并购）
                'https://news.crunchbase.com/feed/',         # Crunchbase News
                'https://techcrunch.com/category/education/feed/', # TechCrunch教育
                'https://www.edsurge.com/news.rss',          # EdSurge
            ],

            # 原有教育主题（保留，作为综合教育资讯）
            'education': [
                'https://www.jiemodui.com/rss.xml',          # 芥末堆
                'https://www.heibandongcha.com/feed',        # 黑板洞察
                'https://www.36kr.com/feed',                 # 36氪教育
                'https://feeds.feedburner.com/EducationWeek', # Education Week
                'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
                'https://www.timeshighereducation.com/rss.xml', # Times Higher Education
                'https://www.universityworldnews.com/rss.php', # University World News
                'https://www.edsurge.com/news.rss',          # EdSurge
                'https://www.chronicle.com/section/news/6/rss', # Chronicle of Higher Ed
            ],
            'pbsa': [
                'https://www.36kr.com/feed',              # 36氪房地产科技
                'https://www.huxiu.com/rss/0.xml',        # 虎嗅地产
            ],
            'uhomes': [
                'https://www.36kr.com/feed',              # 36氪
                'https://www.huxiu.com/rss/0.xml',        # 虎嗅
            ]
        }

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

    def calculate_news_quality(self, news: Dict, topic_keywords: List[str]) -> float:
        """
        计算新闻质量分数（用于筛选和排序）

        评分标准：
        - 标题长度适中（20-100字符）：+10分
        - 有描述内容：+10分
        - 标题包含主题关键词：每个关键词+5分
        - 来源可信度：知名媒体+10分

        Args:
            news: 新闻字典
            topic_keywords: 主题关键词列表

        Returns:
            质量分数（0-100）
        """
        score = 0.0

        # 1. 标题质量（20分）
        title = news.get('title', '')
        title_len = len(title)
        if 20 <= title_len <= 100:
            score += 20
        elif 10 <= title_len < 20 or 100 < title_len <= 150:
            score += 10

        # 2. 描述质量（15分）
        description = news.get('description', '')
        if len(description) > 50:
            score += 15
        elif len(description) > 20:
            score += 8

        # 3. 关键词相关度（30分）
        title_lower = title.lower()
        desc_lower = description.lower()
        keyword_matches = 0
        for keyword in topic_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title_lower:
                keyword_matches += 2
            if keyword_lower in desc_lower:
                keyword_matches += 1
        score += min(keyword_matches * 5, 30)  # 最多30分

        # 4. 来源可信度（20分）
        trusted_sources = [
            '36kr', '36氪', 'IT之家', '虎嗅', '少数派', 'sspai',
            '新浪', '腾讯', '网易', '搜狐', '财新', '界面',
            'reuters', 'bloomberg', 'techcrunch', 'wired',
            '量子位', 'qbitai', '机器之心', 'jiqizhixin',
            'mit technology review', 'hacker news', 'ars technica',
            'google ai', 'openai', 'papers with code', 'aiweekly',
            '极客公园', 'geekpark', '爱范儿', 'ifanr', 'pingwest', '品玩',
            'edsurge', 'chronicle', 'crunchbase'
        ]
        source = str(news.get('source', '') or '').lower()
        for trusted in trusted_sources:
            if trusted in source:
                score += 20
                break

        # 5. 有URL链接（15分）
        if news.get('url', ''):
            score += 15

        return score

    def fetch_rss_news(self, topic_key: str, num: int = 5) -> List[Dict]:
        """
        从RSS订阅源获取新闻（并行处理）

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
            try:
                logger.info(f"  └─ [并行] 从RSS获取: {feed_url[:50]}...")
                
                # 使用requests获取内容，带上User-Agent以绕过反爬
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
                }
                
                try:
                    response = self.session.get(feed_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    content = response.content
                except Exception as req_err:
                    logger.warning(f"⚠️ RSS请求失败 {feed_url}: {req_err}，尝试直接解析...")
                    # 如果请求失败，尝试直接用feedparser解析（作为后备）
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
                    news_item = {
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', entry.get('description', ''))[:200],
                        'source': feed.feed.get('title', 'RSS'),
                        'url': entry.get('link', ''),
                        'time': entry.get('published', entry.get('updated', ''))
                    }
                    feed_news.append(news_item)
                
                if feed_news:
                    logger.info(f"✅ RSS获取{len(feed_news)}条新闻 ({feed_url[:30]}...)")
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

        return all_news[:num]

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
            return True  # 如果没有时间信息，默认认为是最近的
            
        try:
            from dateutil import parser
            from datetime import datetime, timedelta
            
            # 解析新闻时间
            news_date = parser.parse(news_time)
            # 移除时区信息进行比较
            if news_date.tzinfo:
                news_date = news_date.replace(tzinfo=None)
                
            # 当前时间
            now = datetime.now()
            
            # 检查是否在指定天数内
            return (now - news_date).days <= max_days
            
        except Exception as e:
            logger.warning(f"解析新闻时间失败 '{news_time}': {e}")
            return True  # 解析失败时默认认为是最近的

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
            return self.fetch_rss_news(topic, num=5)

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
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = news['title']
            news_time = news.get('time', '')
            
            # 检查是否重复和是否为最近新闻
            if title not in seen_titles and self.is_news_recent(news_time, max_days=7):
                seen_titles.add(title)
                unique_news.append(news)
                logger.debug(f"✅ 保留新闻: {title[:50]}... (时间: {news_time})")
            elif title in seen_titles:
                logger.debug(f"❌ 去重: {title[:50]}...")
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
            formatted.append(
                f"{i}. {news['title']}\n"
                f"   来源: {news['source']}\n"
                f"   摘要: {news['description'][:100]}...\n"
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
