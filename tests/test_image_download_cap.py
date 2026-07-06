"""image_fetcher 下载大小上限测试（AUDIT 2026-07-05 行动项 #6，安全节）。

背景：download_to_cache 曾无大小上限地 r.content 全量入内存落盘，
恶意/异常源可喂数 GB 文件。锁定：Content-Length 超限拒绝、
流式累计超限中止且不留半截缓存文件、正常图片不受影响。
"""
from pathlib import Path

import image_fetcher


class FakeResponse:
    def __init__(self, chunks, headers=None, status=200):
        self._chunks = chunks
        self.headers = headers or {}
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size=None):
        yield from self._chunks

    @property
    def content(self):
        return b"".join(self._chunks)


def _patch_get(monkeypatch, response):
    monkeypatch.setattr(image_fetcher.requests, "get", lambda *a, **k: response)


def _patch_cache_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(image_fetcher, "CACHE_DIR", Path(tmp_path))


class TestDownloadSizeCap:
    def test_normal_image_downloads(self, tmp_path, monkeypatch):
        _patch_cache_dir(monkeypatch, tmp_path)
        _patch_get(monkeypatch, FakeResponse([b"x" * 1024], headers={"Content-Length": "1024"}))
        path = image_fetcher.download_to_cache("https://e.com/cover.jpg")
        assert path is not None and path.stat().st_size == 1024

    def test_oversized_content_length_rejected(self, tmp_path, monkeypatch):
        _patch_cache_dir(monkeypatch, tmp_path)
        huge = str(image_fetcher._MAX_DOWNLOAD_BYTES + 1)
        _patch_get(monkeypatch, FakeResponse([b"x"], headers={"Content-Length": huge}))
        assert image_fetcher.download_to_cache("https://e.com/huge.jpg") is None
        assert list(Path(tmp_path).iterdir()) == []

    def test_oversized_stream_without_length_aborted(self, tmp_path, monkeypatch):
        _patch_cache_dir(monkeypatch, tmp_path)
        chunk = b"x" * (1024 * 1024)
        n_chunks = image_fetcher._MAX_DOWNLOAD_BYTES // len(chunk) + 2
        _patch_get(monkeypatch, FakeResponse([chunk] * n_chunks))  # 无 Content-Length
        assert image_fetcher.download_to_cache("https://e.com/nolen.jpg") is None
        # 不留半截缓存文件
        assert list(Path(tmp_path).iterdir()) == []
