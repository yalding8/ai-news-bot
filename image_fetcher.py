"""
抓取文章封面图（Open Graph og:image）并缓存到本地。
供海报生成器的头条配图使用。

流程：
    article_url → GET → 从 HTML 抽 og:image → 下载到 assets/cache/
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).parent.resolve()
CACHE_DIR = ROOT / "assets" / "cache" / "article_images"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# og:image meta 两种顺序都接（property 在 content 前 / content 在 property 前）
_OG_A = re.compile(
    r'<meta\s+[^>]*property=["\']og:image(?::secure_url|:url)?["\']\s+[^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_B = re.compile(
    r'<meta\s+[^>]*content=["\']([^"\']+)["\']\s+[^>]*property=["\']og:image(?::secure_url|:url)?["\']',
    re.IGNORECASE,
)
# twitter:image 作为退路
_TW = re.compile(
    r'<meta\s+[^>]*name=["\']twitter:image(?::src)?["\']\s+[^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

# hero banner 实际渲染为 1080×560 横图（cover）。低于此宽度会被严重放大糊掉；
# 接近正方形的图基本是站点 logo / 头像 / 图标——典型例子：36氪对约半数无配图文章
# 统一返回 240×240 品牌 logo (img.36krcdn.com/20191024/v2_1571894049839_img_jpg) 当 og:image。
# 这道门对所有来源通用，不只挡 36氪。拦下后海报自动走"大数字装饰"兜底。
_MIN_COVER_WIDTH = 600
_MIN_COVER_HEIGHT = 300
_SQUARE_RATIO_LO = 0.8   # 宽高比落在 [LO, HI] 视为"接近正方形"
_SQUARE_RATIO_HI = 1.25
_SQUARE_SAFE_WIDTH = 1000  # 接近正方形但宽度 ≥ 此值时，可能是真实大图，放行


def _is_usable_cover(path: Path) -> bool:
    """判断下载到的图片是否适合做头条封面 banner（挡掉 logo/图标类）。"""
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
    except Exception as e:
        logger.warning(f"cover image unreadable, rejected [{path}]: {e}")
        return False

    if w < _MIN_COVER_WIDTH or h < _MIN_COVER_HEIGHT:
        logger.info(f"cover rejected (too small {w}x{h}): {path}")
        return False

    ratio = w / h if h else 0
    if _SQUARE_RATIO_LO <= ratio <= _SQUARE_RATIO_HI and w < _SQUARE_SAFE_WIDTH:
        logger.info(f"cover rejected (logo-like square {w}x{h}): {path}")
        return False

    return True


def _extract_cover_image(html: str) -> Optional[str]:
    """从 HTML 抽封面图 URL：og:image 优先，twitter:image 兜底。"""
    for pat in (_OG_A, _OG_B, _TW):
        m = pat.search(html)
        if m:
            return m.group(1).strip()
    return None


def fetch_og_image_url(article_url: str, timeout: float = 8.0) -> Optional[str]:
    """抓文章页 HTML，提取 og:image URL。失败返回 None。"""
    try:
        r = requests.get(article_url, headers={"User-Agent": _UA}, timeout=timeout)
        r.raise_for_status()
        return _extract_cover_image(r.text)
    except Exception as e:
        logger.warning(f"og:image fetch failed [{article_url}]: {e}")
        return None


def download_to_cache(img_url: str, timeout: float = 10.0) -> Optional[Path]:
    """下载图片到本地缓存；以 URL hash 做文件名，已存在复用。"""
    key = hashlib.sha1(img_url.encode()).hexdigest()[:16]
    ext_m = re.search(r"\.(jpg|jpeg|png|webp|gif)(?:$|\?|#)", img_url, re.IGNORECASE)
    ext = (ext_m.group(1).lower() if ext_m else "jpg")
    if ext == "jpeg":
        ext = "jpg"
    cache_path = CACHE_DIR / f"{key}.{ext}"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path
    try:
        r = requests.get(img_url, headers={"User-Agent": _UA}, timeout=timeout, stream=True)
        r.raise_for_status()
        cache_path.write_bytes(r.content)
        return cache_path
    except Exception as e:
        logger.warning(f"image download failed [{img_url}]: {e}")
        return None


def fetch_article_image(article_url: str) -> Optional[Path]:
    """一步到位：抓文章 og:image + 下载到本地缓存。"""
    if not article_url:
        return None
    img_url = fetch_og_image_url(article_url)
    if not img_url:
        return None
    path = download_to_cache(img_url)
    if not path:
        return None
    if not _is_usable_cover(path):
        # 删掉不可用的缓存（logo/图标），避免下次按 URL hash 命中复用
        try:
            path.unlink()
        except OSError:
            pass
        return None
    return path


if __name__ == "__main__":
    # 冒烟测试：抓一篇公开文章的封面图
    import sys

    logging.basicConfig(level=logging.INFO)
    url = sys.argv[1] if len(sys.argv) > 1 else "https://thepienews.com/news/"
    print(f"Fetching: {url}")
    path = fetch_article_image(url)
    if path:
        print(f"✅ Saved: {path} ({path.stat().st_size / 1024:.1f} KB)")
    else:
        print("❌ No image found")
