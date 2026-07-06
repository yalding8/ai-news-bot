"""news_fetcher 纯函数单元测试（AUDIT 2026-07-05 行动项 #5）。

覆盖评估中零测试的核心管线纯函数：URL 规范化去重键、RSS 时间清洗、
时效判断、教育相关性系数、信号分级、相似度、来源多样性过滤。
全部无网络、无文件 IO（NewsFetcher() 构造仅建缓存目录）。
"""
import unittest
from datetime import datetime, timedelta, timezone

from news_fetcher import NewsFetcher


class TestNormalizeUrl(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_strips_utm_and_tracking_params(self):
        url = "https://Example.com/news/?utm_source=x&utm_medium=y&gclid=abc&id=7"
        self.assertEqual(self.f._normalize_url(url), "https://example.com/news?id=7")

    def test_drops_fragment_and_default_port(self):
        self.assertEqual(
            self.f._normalize_url("https://example.com:443/a#section"),
            "https://example.com/a",
        )
        self.assertEqual(
            self.f._normalize_url("http://example.com:80/a"),
            "http://example.com/a",
        )

    def test_strips_trailing_slash_except_root(self):
        self.assertEqual(self.f._normalize_url("https://e.com/path/"), "https://e.com/path")
        self.assertEqual(self.f._normalize_url("https://e.com/"), "https://e.com/")

    def test_sorts_query_pairs(self):
        a = self.f._normalize_url("https://e.com/p?b=2&a=1")
        b = self.f._normalize_url("https://e.com/p?a=1&b=2")
        self.assertEqual(a, b)

    def test_non_url_passthrough(self):
        self.assertEqual(self.f._normalize_url("  plain-guid-123  "), "plain-guid-123")
        self.assertEqual(self.f._normalize_url(""), "")

    def test_same_article_different_tracking_dedup_key_equal(self):
        u1 = "https://thepienews.com/news/uk-visa/?utm_campaign=rss"
        u2 = "https://thepienews.com/news/uk-visa"
        self.assertEqual(self.f._normalize_url(u1), self.f._normalize_url(u2))


class TestCanonicalId(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_url_like_id_normalized(self):
        self.assertEqual(
            self.f._canonical_id("HTTPS://E.com/p?utm_source=x"),
            "https://e.com/p",
        )

    def test_opaque_guid_stripped_only(self):
        self.assertEqual(self.f._canonical_id(" guid-42 "), "guid-42")
        self.assertEqual(self.f._canonical_id(""), "")


class TestCleanRssTime(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_chinese_date_format(self):
        self.assertEqual(self.f.clean_rss_time("2025年12月16日"), "2025-12-16")

    def test_chinese_weekday_replaced(self):
        self.assertIn("Tue", self.f.clean_rss_time("星期二, 16 Dec 2025"))
        self.assertIn("Fri", self.f.clean_rss_time("周五 10:00"))

    def test_empty_passthrough(self):
        self.assertEqual(self.f.clean_rss_time(""), "")


class TestIsNewsRecent(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_now_is_recent(self):
        t = datetime.now(timezone.utc).isoformat()
        self.assertTrue(self.f.is_news_recent(t, max_days=7))

    def test_ten_days_ago_not_recent(self):
        t = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        self.assertFalse(self.f.is_news_recent(t, max_days=7))

    def test_future_news_rejected(self):
        t = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        self.assertFalse(self.f.is_news_recent(t, max_days=7))

    def test_empty_time_rejected(self):
        self.assertFalse(self.f.is_news_recent("", max_days=7))

    def test_unparseable_time_rejected(self):
        self.assertFalse(self.f.is_news_recent("not a date at all", max_days=7))


class TestEducationRelevance(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_three_strong_keywords_full_relevance(self):
        r = self.f._calculate_education_relevance(
            "Visa rules tighten for international students", "scholarship cuts hit study abroad plans", []
        )
        self.assertEqual(r, 1.0)

    def test_one_strong_keyword(self):
        r = self.f._calculate_education_relevance("New visa fee announced", "", [])
        self.assertEqual(r, 0.8)

    def test_weak_keywords_only(self):
        self.assertEqual(
            self.f._calculate_education_relevance("University opens new campus", "college news", []),
            0.5,
        )
        self.assertEqual(
            self.f._calculate_education_relevance("University opens new campus", "", []),
            0.3,
        )

    def test_pure_tech_content_floored(self):
        r = self.f._calculate_education_relevance("新一代大模型开源，算力成本下降", "芯片竞争加剧", [])
        self.assertEqual(r, 0.1)

    def test_tech_content_with_strong_edu_word_not_floored(self):
        r = self.f._calculate_education_relevance("大模型进课堂：留学申请文书检测上线", "", [])
        self.assertGreaterEqual(r, 0.8)

    def test_unrelated_content_minimal(self):
        self.assertEqual(self.f._calculate_education_relevance("本地餐厅推出新菜单", "", []), 0.1)


class TestClassifySignalLevel(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_gov_domain_is_level_1(self):
        news = {"title": "Weekly update", "source": "x", "url": "https://www.gov.uk/government/news/1"}
        self.assertEqual(self.f.classify_signal_level(news), 1)

    def test_policy_title_is_level_1(self):
        news = {"title": "新签证政策发布", "source": "x", "url": "https://e.com/1"}
        self.assertEqual(self.f.classify_signal_level(news), 1)

    def test_authority_source_is_level_2(self):
        news = {"title": "campus life feature", "source": "The PIE News", "url": "https://e.com/2"}
        self.assertEqual(self.f.classify_signal_level(news), 2)

    def test_report_keyword_is_level_2(self):
        news = {"title": "2026 student mobility report published", "source": "x", "url": "https://e.com/3"}
        self.assertEqual(self.f.classify_signal_level(news), 2)

    def test_default_is_level_3(self):
        news = {"title": "startup raises funding", "source": "x", "url": "https://e.com/4"}
        self.assertEqual(self.f.classify_signal_level(news), 3)


class TestCalculateSimilarity(unittest.TestCase):
    def setUp(self):
        self.f = NewsFetcher()

    def test_identical_news_is_1(self):
        n = {"title": "UK visa rules updated for students", "description": "A long enough description here."}
        self.assertEqual(self.f.calculate_similarity(n, dict(n)), 1.0)

    def test_unrelated_news_low(self):
        a = {"title": "UK visa rules updated", "description": ""}
        b = {"title": "本地餐厅推出新菜单", "description": ""}
        self.assertLess(self.f.calculate_similarity(a, b), 0.3)

    def test_short_descriptions_fall_back_to_title_only(self):
        a = {"title": "Same title here", "description": "short"}
        b = {"title": "Same title here", "description": "tiny"}
        self.assertEqual(self.f.calculate_similarity(a, b), 1.0)


class TestDiversityFilter(unittest.TestCase):
    def test_caps_two_per_source(self):
        f = NewsFetcher()
        news = [
            {"title": f"t{i}", "source": "A" if i < 4 else "B"} for i in range(6)
        ]
        out = f.apply_diversity_filter(news, max_per_source=2)
        sources = [n["source"] for n in out]
        self.assertEqual(sources.count("A"), 2)
        self.assertEqual(sources.count("B"), 2)
        # 保序：先到先得
        self.assertEqual([n["title"] for n in out], ["t0", "t1", "t4", "t5"])
