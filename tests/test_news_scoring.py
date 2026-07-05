"""calculate_news_quality 评分回归测试（AUDIT 2026-07-05 发现 C1）。

背景：高价值词表曾包含裸子串 'the'，按子串匹配会命中几乎所有英文标题
（the/them/weather/theory…），系统性给英文源新闻无差别 +5，扭曲中英文源排序；
'qs' 同理会误命中 'faqs'。本文件锁定修复后的匹配语义与关键评分行为。
"""
import unittest

from news_fetcher import NewsFetcher


class TestKeywordInText(unittest.TestCase):
    """ASCII 关键词按词首边界匹配（允许复数等后缀）；中文关键词按子串匹配。"""

    def test_qs_does_not_match_inside_faqs(self):
        self.assertFalse(NewsFetcher._keyword_in_text("qs", "university faqs updated for students"))

    def test_qs_matches_at_word_start(self):
        self.assertTrue(NewsFetcher._keyword_in_text("qs", "qs world university rankings released"))

    def test_the_does_not_match_inside_weather(self):
        self.assertFalse(NewsFetcher._keyword_in_text("the", "weather delays hit campuses"))

    def test_plural_suffix_still_matches(self):
        # 旧子串行为里 'ranking' 能命中 'rankings'，词边界化后不能丢掉这类命中
        self.assertTrue(NewsFetcher._keyword_in_text("ranking", "world university rankings released"))
        self.assertTrue(NewsFetcher._keyword_in_text("visa", "student visas delayed this year"))

    def test_cjk_keyword_uses_substring(self):
        self.assertTrue(NewsFetcher._keyword_in_text("签证", "英国学生签证政策更新"))


class TestHighValueKeywordScoring(unittest.TestCase):
    def setUp(self):
        self.fetcher = NewsFetcher()

    @staticmethod
    def _news(title: str) -> dict:
        return {
            "title": title,
            # description 含强留学词，保证教育相关性系数 ≥ 0.3（不触发一票淘汰）
            "description": "New study abroad rules affect admissions for students planning overseas education.",
            "source": "",
            "url": "",
            "time": "",  # 无时间 → 时效分恒为 0，测试确定性
        }

    def test_generic_english_the_gets_no_bonus(self):
        """仅相差普通冠词 the 的两个标题必须同分（修复前 the 版 +5）。"""
        with_the = self._news("UK universities expand the student housing supply")
        without_the = self._news("UK universities expand new student housing supply")
        score_a = self.fetcher.calculate_news_quality(with_the, [])
        score_b = self.fetcher.calculate_news_quality(without_the, [])
        self.assertEqual(score_a, score_b)

    def test_faqs_gets_no_qs_bonus(self):
        """faqs 词中的 qs 不得触发 QS 排名加分。"""
        with_faqs = self._news("University FAQs for international arrivals updated")
        without_faqs = self._news("University tips for international arrivals updated")
        score_a = self.fetcher.calculate_news_quality(with_faqs, [])
        score_b = self.fetcher.calculate_news_quality(without_faqs, [])
        self.assertEqual(score_a, score_b)


class TestScoreSnapshot(unittest.TestCase):
    """整分快照：锁定评分公式，任何改动评分权重的提交都应显式更新此处。"""

    def setUp(self):
        self.fetcher = NewsFetcher()

    def test_full_score_snapshot_education_policy_news(self):
        news = {
            "title": "UK visa policy update for international students",
            "description": (
                "New study abroad visa rules affect tuition and admissions "
                "for students planning to study in the UK."
            ),
            "source": "The PIE News",
            "url": "https://thepienews.com/news/uk-visa",
            "time": "",
        }
        # 分解：标题长度带 +15 | 描述>50 字 +10 | 高价值词 visa/policy/'visa policy' +15
        # | 主题词 visa(题3+述1)+policy(题3) → min(7×5,25)=25 | 教育媒体源 +35
        # | 时效 0 | 相关性 1.0（strong≥3）| 标题含 policy → 一级信号 ×1.5
        # (15+10+15+25+35) × 1.5 = 150
        score = self.fetcher.calculate_news_quality(news, ["visa", "policy"])
        self.assertEqual(score, 150.0)
        self.assertEqual(news["signal_level"], 1)
        self.assertEqual(news["education_relevance"], 1.0)

    def test_irrelevant_tech_news_scores_zero(self):
        news = {
            "title": "新一代大模型发布，算力芯片竞争加剧",
            "description": "多家公司发布开源大模型，推理训练成本下降。",
            "source": "36kr",
            "url": "https://36kr.com/p/123",
            "time": "",
        }
        score = self.fetcher.calculate_news_quality(news, [])
        self.assertEqual(score, 0)
