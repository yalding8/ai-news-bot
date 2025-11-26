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
