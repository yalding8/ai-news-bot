"""NewsFetcher RSS 文件缓存测试（AUDIT 2026-07-05 行动项 #6，发现 C4）。

要求：JSON 序列化（禁 pickle）、缓存目录在项目内（非 /tmp）、TTL 过期读不到、
陈旧文件会被清理、损坏文件不炸。
"""
import json
import os
import time
from pathlib import Path

import news_fetcher
from news_fetcher import NewsFetcher


class TestRssFileCache:
    def _fetcher_with_cache_dir(self, tmp_path, monkeypatch):
        f = NewsFetcher()
        monkeypatch.setattr(f, "cache_dir", str(tmp_path))
        return f

    def test_roundtrip(self, tmp_path, monkeypatch):
        f = self._fetcher_with_cache_dir(tmp_path, monkeypatch)
        data = [{"title": "含中文 & emoji 📰", "url": "https://e.com/1", "time": ""}]
        f._set_cache("https://feed.example/rss", data)
        assert f._get_cache("https://feed.example/rss") == data

    def test_cache_files_are_json_not_pickle(self, tmp_path, monkeypatch):
        f = self._fetcher_with_cache_dir(tmp_path, monkeypatch)
        f._set_cache("key", [{"title": "t"}])
        files = list(Path(tmp_path).iterdir())
        assert len(files) == 1
        # 文件必须能被 json 直接解析（pickle 会在这里炸）
        json.loads(files[0].read_text(encoding="utf-8"))

    def test_expired_entry_not_returned(self, tmp_path, monkeypatch):
        f = self._fetcher_with_cache_dir(tmp_path, monkeypatch)
        f._set_cache("key", [{"title": "t"}])
        cache_file = next(Path(tmp_path).iterdir())
        stale = time.time() - f.cache_ttl - 10
        os.utime(cache_file, (stale, stale))
        assert f._get_cache("key") is None

    def test_corrupt_cache_file_returns_none(self, tmp_path, monkeypatch):
        f = self._fetcher_with_cache_dir(tmp_path, monkeypatch)
        f._set_cache("key", [{"title": "t"}])
        cache_file = next(Path(tmp_path).iterdir())
        cache_file.write_text("{ not json", encoding="utf-8")
        assert f._get_cache("key") is None

    def test_default_cache_dir_inside_project_not_tmp(self):
        f = NewsFetcher()
        project_root = str(Path(news_fetcher.__file__).parent.resolve())
        assert str(Path(f.cache_dir).resolve()).startswith(project_root)

    def test_cleanup_removes_stale_files(self, tmp_path, monkeypatch):
        f = self._fetcher_with_cache_dir(tmp_path, monkeypatch)
        f._set_cache("fresh", [{"title": "f"}])
        f._set_cache("stale", [{"title": "s"}])
        # 把其中一个文件拨老到清理阈值之外
        stale_file = sorted(Path(tmp_path).iterdir())[0]
        old = time.time() - 8 * 86400
        os.utime(stale_file, (old, old))

        f._cleanup_cache()

        remaining = list(Path(tmp_path).iterdir())
        assert len(remaining) == 1
        assert remaining[0] != stale_file
