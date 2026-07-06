"""NewsCache 行为测试（AUDIT 2026-07-05 行动项 #5）。

覆盖：已推送标记 / 24h 窗口过滤 / 过期重推 / 持久化往返 / 过期清理。
全部走 tmp_path 独立缓存文件，不碰仓库根的 .news_cache.json。
"""
from datetime import datetime, timedelta

from news_cache import NewsCache


def _news(title: str, url: str = "") -> dict:
    return {"title": title, "url": url or f"https://e.com/{title}"}


class TestMarkAndFilter:
    def test_unsent_news_passes_filter(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        batch = [_news("a"), _news("b")]
        assert cache.filter_unsent_news("t", batch) == batch

    def test_sent_news_filtered_within_window(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        batch = [_news("a"), _news("b")]
        cache.mark_news_sent("t", batch[:1])
        out = cache.filter_unsent_news("t", batch)
        assert out == batch[1:]

    def test_same_title_different_url_is_different_news(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        n1 = _news("same", "https://e.com/1")
        n2 = _news("same", "https://e.com/2")
        cache.mark_news_sent("t", [n1])
        assert cache.filter_unsent_news("t", [n2]) == [n2]

    def test_topics_are_isolated(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        n = _news("a")
        cache.mark_news_sent("topic1", [n])
        assert cache.filter_unsent_news("topic2", [n]) == [n]


class TestWindowExpiry:
    def test_sent_beyond_window_can_resend(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        n = _news("a")
        cache.mark_news_sent("t", [n])
        # 手动把时间戳拨回 25 小时前
        h = cache._get_news_hash(n)
        cache.cache_data["sent_news"]["t"][h] = (
            datetime.now() - timedelta(hours=25)
        ).isoformat()
        assert not cache.is_news_sent("t", n, hours=24)

    def test_corrupt_timestamp_treated_as_unsent(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        n = _news("a")
        cache.mark_news_sent("t", [n])
        h = cache._get_news_hash(n)
        cache.cache_data["sent_news"]["t"][h] = "not-a-timestamp"
        assert not cache.is_news_sent("t", n, hours=24)


class TestPersistence:
    def test_roundtrip_across_instances(self, tmp_path):
        path = str(tmp_path / "c.json")
        NewsCache(cache_file=path).mark_news_sent("t", [_news("a")])
        reloaded = NewsCache(cache_file=path)
        assert reloaded.is_news_sent("t", _news("a"), hours=24)

    def test_corrupt_cache_file_starts_fresh(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text("{ not json")
        cache = NewsCache(cache_file=str(path))
        assert cache.filter_unsent_news("t", [_news("a")]) == [_news("a")]


class TestCleanup:
    def test_old_records_removed_recent_kept(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        old, recent = _news("old"), _news("recent")
        cache.mark_news_sent("t", [old, recent])
        h_old = cache._get_news_hash(old)
        cache.cache_data["sent_news"]["t"][h_old] = (
            datetime.now() - timedelta(days=8)
        ).isoformat()

        cache.cleanup_old_cache(days=7)

        assert not cache.is_news_sent("t", old, hours=24)
        assert cache.is_news_sent("t", recent, hours=24)

    def test_emptied_topic_dropped(self, tmp_path):
        cache = NewsCache(cache_file=str(tmp_path / "c.json"))
        n = _news("a")
        cache.mark_news_sent("t", [n])
        cache.cache_data["sent_news"]["t"][cache._get_news_hash(n)] = (
            datetime.now() - timedelta(days=8)
        ).isoformat()
        cache.cleanup_old_cache(days=7)
        assert "t" not in cache.cache_data["sent_news"]
