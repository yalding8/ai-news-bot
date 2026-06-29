import unittest
from datetime import datetime
from unittest import mock

import bot_wecom
import dingning_publisher


# 三条候选新闻，feed 原序
TOP_NEWS = [
    {"title": "Alpha headline", "url": "https://example.com/alpha", "source": "Site A"},
    {"title": "Beta headline", "url": "https://example.com/beta", "source": "Site B"},
    {"title": "Gamma headline", "url": "https://example.com/gamma", "source": "Site C"},
]


def _make_item(title_en, title_zh, source):
    return {
        "title_en": title_en,
        "title_zh": title_zh,
        "summary": "摘要",
        "punch": "点睛",
        "source": source,
    }


class TestBuildMdxAlignment(unittest.TestCase):
    def test_title_pairs_with_matching_url_when_reordered(self):
        # LLM 把顺序打乱：Gamma 排第 1，Alpha 排第 2
        poster_items = [
            _make_item("Gamma headline", "伽马中文标题", "Site C"),
            _make_item("Alpha headline", "阿尔法中文标题", "Site A"),
        ]
        mdx = dingning_publisher._build_mdx(TOP_NEWS, poster_items, datetime(2026, 6, 29))

        # 伽马标题必须配伽马链接，而不是 top_news[0] 的 alpha 链接
        self.assertIn("### 1. 伽马中文标题", mdx)
        gamma_block = mdx.split("### 1. 伽马中文标题", 1)[1].split("###", 1)[0]
        self.assertIn("https://example.com/gamma", gamma_block)
        self.assertNotIn("https://example.com/alpha", gamma_block)

    def test_unmatched_title_en_omits_url(self):
        # title_en 在 top_news 里找不到 → 不输出任何原文链接（宁缺毋错）
        poster_items = [
            _make_item("Nonexistent headline", "无源中文标题", "Ghost Site"),
        ]
        mdx = dingning_publisher._build_mdx(TOP_NEWS, poster_items, datetime(2026, 6, 29))

        self.assertIn("### 1. 无源中文标题", mdx)
        block = mdx.split("### 1. 无源中文标题", 1)[1]
        self.assertNotIn("原文 →", block)
        # 也绝不能借用任何无关链接
        self.assertNotIn("https://example.com/", block)

    def test_item_selected_from_tail_keeps_its_link(self):
        # 复现 2026-06-29 福耀 bug：LLM 从 9 条候选选了靠后的一条作为 top-5，
        # 只要传入全集，该条仍应拿到自己的链接，输出仍限 5 条
        nine = [
            {"title": f"News {i}", "url": f"https://example.com/{i}", "source": f"S{i}"}
            for i in range(9)
        ]
        poster_items = [
            _make_item("News 7", "第七条中文", "S7"),  # 选自后段
            _make_item("News 0", "第零条中文", "S0"),
            _make_item("News 3", "第三条中文", "S3"),
        ]
        mdx = dingning_publisher._build_mdx(nine, poster_items, datetime(2026, 6, 29))
        block = mdx.split("### 1. 第七条中文", 1)[1].split("###", 1)[0]
        self.assertIn("https://example.com/7", block)
        # 输出条目数 = poster_items 数（3），不被 top_news 的 9 撑大
        self.assertEqual(mdx.count("**[原文 →]"), 3)

    def test_match_is_case_and_whitespace_insensitive(self):
        # title_en 大小写/多余空白与原始 title 不同，仍应匹配
        poster_items = [
            _make_item("  beta   HEADLINE ", "贝塔中文标题", "Site B"),
        ]
        mdx = dingning_publisher._build_mdx(TOP_NEWS, poster_items, datetime(2026, 6, 29))
        self.assertIn("https://example.com/beta", mdx)


class TestBuildPosterDataAlignment(unittest.TestCase):
    def test_hero_image_fetched_from_matching_news_url(self):
        # LLM 把 Gamma 排成头条；hero 封面图必须抓 Gamma 的 url，而非 top_news[0]=Alpha
        poster_items = [
            _make_item("Gamma headline", "伽马中文标题", "Site C"),
            _make_item("Alpha headline", "阿尔法中文标题", "Site A"),
        ]
        with mock.patch.object(bot_wecom, "fetch_article_image", return_value=None) as fetch_mock:
            data = bot_wecom.build_poster_data(TOP_NEWS, poster_items)

        fetch_mock.assert_called_once_with("https://example.com/gamma")
        self.assertEqual(data["hero"]["title_zh"], "伽马中文标题")
        # source 兜底也应来自匹配的 Gamma 新闻（Site C），不是位置 0 的 Alpha
        self.assertEqual(data["hero"]["source"], "Site C")


if __name__ == "__main__":
    unittest.main()
