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
    return download_to_cache(img_url)


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
