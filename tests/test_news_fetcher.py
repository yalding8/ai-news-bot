import unittest

from news_fetcher import NewsFetcher


class TestNewsFetcher(unittest.TestCase):
    def test_format_news_for_ai(self):
        fetcher = NewsFetcher()
        news_list = [
            {
                "title": "AI 模型发布",
                "source": "测试媒体",
                "description": "这是一段关于AI模型发布的描述。" * 3,
                "url": "https://example.com/1",
            },
            {
                "title": "教育科技趋势",
                "source": "测试媒体2",
                "description": "教育科技正在快速发展。" * 3,
                "url": "https://example.com/2",
            },
        ]
        formatted = fetcher.format_news_for_ai(news_list)
        self.assertIn("1. AI 模型发布", formatted)
        self.assertIn("2. 教育科技趋势", formatted)
        self.assertIn("来源: 测试媒体", formatted)
        self.assertIn("链接: https://example.com/1", formatted)


if __name__ == "__main__":
    unittest.main()


class TestThirtySixKrNoiseFilter(unittest.TestCase):
    def test_36kr_removed_from_education_topics(self):
        f = NewsFetcher()
        for topic in ("education", "industry_news"):
            joined = " ".join(f.rss_feeds.get(topic, []))
            self.assertNotIn("36kr", joined, f"{topic} should not pull the general 36kr feed")

    def test_36kr_kept_in_non_education_topics(self):
        # pbsa / uhomes rely solely on 36kr — must not be emptied
        f = NewsFetcher()
        for topic in ("pbsa", "uhomes"):
            self.assertTrue(f.rss_feeds.get(topic), f"{topic} should still have feeds")

    def test_newsflash_url_is_low_value(self):
        f = NewsFetcher()
        self.assertTrue(f._is_low_value_url("https://36kr.com/newsflashes/3869918356395264?f=rss"))
        self.assertTrue(f._is_low_value_url("https://www.36kr.com/newsflashes/123"))

    def test_real_article_url_is_not_low_value(self):
        f = NewsFetcher()
        self.assertFalse(f._is_low_value_url("https://thepienews.com/some-real-article/"))
        self.assertFalse(f._is_low_value_url("https://36kr.com/p/2987654321"))
        self.assertFalse(f._is_low_value_url(""))
