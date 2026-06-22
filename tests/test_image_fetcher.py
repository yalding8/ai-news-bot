"""
图片质量门测试：拒绝 logo/图标类 og:image，避免被当成头条封面铺满顶部 banner。

背景：36氪对约一半无独立配图的文章，统一返回 240×240 的品牌 logo
(img.36krcdn.com/20191024/v2_1571894049839_img_jpg) 作为 og:image。
旧逻辑不加校验直接铺成 1080×560 的 hero banner → 顶部出现糊掉的 "36Kr" logo。
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

import image_fetcher


def _make_image(path: Path, w: int, h: int, color=(120, 140, 255)) -> Path:
    Image.new("RGB", (w, h), color).save(path, "JPEG")
    return path


def _make_logo_collage(path: Path, w: int, h: int) -> Path:
    """白底 + 两个并排小 logo 色块（模拟 PIE News M&A 报道的 og:image）。"""
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([w * 0.10, h * 0.35, w * 0.32, h * 0.65], fill=(40, 120, 200))
    d.rectangle([w * 0.62, h * 0.35, w * 0.84, h * 0.65], fill=(200, 60, 40))
    im.save(path, "JPEG")
    return path


class TestIsUsableCover:
    def test_rejects_small_square_logo(self, tmp_path):
        # 36氪默认图实际尺寸 240×240
        p = _make_image(tmp_path / "logo.jpg", 240, 240)
        assert image_fetcher._is_usable_cover(p) is False

    def test_accepts_landscape_cover_600x400(self, tmp_path):
        p = _make_image(tmp_path / "cover.jpg", 600, 400)
        assert image_fetcher._is_usable_cover(p) is True

    def test_accepts_wide_cover(self, tmp_path):
        p = _make_image(tmp_path / "wide.jpg", 1053, 495)
        assert image_fetcher._is_usable_cover(p) is True

    def test_rejects_narrow_low_width(self, tmp_path):
        # 宽度不足，铺到 1080px banner 会被严重放大糊掉
        p = _make_image(tmp_path / "narrow.jpg", 320, 480)
        assert image_fetcher._is_usable_cover(p) is False

    def test_rejects_large_square_logo(self, tmp_path):
        # 即使尺寸够大，接近正方形也大概率是 logo/头像，不适合横向 banner
        p = _make_image(tmp_path / "bigsquare.jpg", 800, 800)
        assert image_fetcher._is_usable_cover(p) is False

    def test_rejects_corrupt_file(self, tmp_path):
        p = tmp_path / "broken.jpg"
        p.write_bytes(b"not an image")
        assert image_fetcher._is_usable_cover(p) is False

    def test_rejects_wide_logo_collage_on_white(self, tmp_path):
        # PIE News M&A 报道 og:image：宽幅 + 尺寸大 + 非正方，躲过尺寸/正方门，
        # 但白底占比高（~88%）应被新增的白底门拦下（Crizac×ForeignAdmits 案例）。
        p = _make_logo_collage(tmp_path / "collage.jpg", 1200, 630)
        assert image_fetcher._is_usable_cover(p) is False

    def test_accepts_photo_like_non_white(self, tmp_path):
        # 真实照片：满幅非白内容，白底占比低，应放行。
        p = _make_image(tmp_path / "photo.jpg", 1200, 630, color=(70, 110, 90))
        assert image_fetcher._is_usable_cover(p) is True


class TestFetchArticleImageGate:
    def test_logo_cover_rejected_returns_none(self, tmp_path, monkeypatch):
        logo = _make_image(tmp_path / "dl.jpg", 240, 240)
        monkeypatch.setattr(image_fetcher, "fetch_og_image_url", lambda url: "http://x/og.jpg")
        monkeypatch.setattr(image_fetcher, "download_to_cache", lambda url: logo)
        assert image_fetcher.fetch_article_image("http://article") is None

    def test_real_cover_passes_through(self, tmp_path, monkeypatch):
        cover = _make_image(tmp_path / "dl.jpg", 1053, 495)
        monkeypatch.setattr(image_fetcher, "fetch_og_image_url", lambda url: "http://x/og.jpg")
        monkeypatch.setattr(image_fetcher, "download_to_cache", lambda url: cover)
        assert image_fetcher.fetch_article_image("http://article") == cover
