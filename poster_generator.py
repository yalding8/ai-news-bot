"""
海报生成器：Jinja2 HTML → Playwright 截图 PNG。

对应 DESIGN §11.1（字体加载时序）+ §11.3（图输出 ≤ 2MB）。
"""
from __future__ import annotations

import base64
import mimetypes
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from playwright.sync_api import sync_playwright


# 自动高亮正则：百分比 / 数字+量词 / N 成 / 数字倍 / 排序词
# 用 named pattern 便于未来扩展；按贪婪度从长到短排列，避免短模式抢先匹配
_HL_PATTERNS = [
    # 百分比（支持小数）
    r"\d+(?:\.\d+)?%",
    # 数字 + 常见量词/单位（教育语境）
    r"\d+(?:\.\d+)?\s*(?:亿美元|亿元|亿|万美元|万元|万|千|百万|所|家|间|位|名|起|次|倍|年|月|日|个|国|州)",
    # N 成 / 过半
    r"\d+\s*成",
    # 英文数字+单位（保守，避免把正文的 2026 这种年份误染）
    r"\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s?(?:%|billion|million|thousand)\b",
]
_HL_COMBINED = re.compile("|".join(f"(?:{p})" for p in _HL_PATTERNS))


def _highlight(text: str) -> Markup:
    """把文本里的数字/量词短语包成 <span class=hl>...</span>，返回安全 Markup。"""
    if not text:
        return Markup("")
    safe = str(escape(text))
    highlighted = _HL_COMBINED.sub(
        lambda m: f'<span class="hl">{m.group(0)}</span>', safe
    )
    return Markup(highlighted)


def _extract_stat(*texts: str) -> str:
    """从候选文本里抽第一个高亮模式匹配（通常是 '60%' / '七成' 这类），作为 hero 大数字装饰。"""
    for t in texts:
        if not t:
            continue
        m = _HL_COMBINED.search(t)
        if m:
            return m.group(0)
    return ""

ROOT = Path(__file__).parent.resolve()
TEMPLATES_DIR = ROOT / "assets" / "templates"
ASSETS_DIR = ROOT / "assets"
QR_UHOMES = ASSETS_DIR / "qrcodes" / "uhomes_qr.png"
QR_PAY = ASSETS_DIR / "qrcodes" / "pay_qr.jpg"
LOGO_UHOMES = ASSETS_DIR / "logos" / "uhomes_logo.png"
LOGO_PAY = ASSETS_DIR / "logos" / "pay_logo.png"
LOGO_COMBO = ASSETS_DIR / "logos" / "combo_logo.png"


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


class Theme(TypedDict):
    name: str            # 'uhomes' | 'pay' | 'white'
    primary: str         # hero 背景色
    accent: str          # section-bar / news-num / 强调色
    hero_fg: str         # hero 文字主色
    hero_rule: str       # hero 分割线半透明色（rgba 字符串）
    hero_hl: str         # hero 内数字/关键词高亮色
    label: str           # 日志用标签


THEMES: dict[str, Theme] = {
    "uhomes": {
        "name": "uhomes",
        "primary":   "#FF5A5F",
        "accent":    "#FF5A5F",
        "hero_fg":   "#FFFFFF",
        "hero_rule": "rgba(255,255,255,0.35)",
        "hero_hl":   "#FFE45A",   # 红底上亮黄
        "label": "异乡好居色",
    },
    "pay": {
        "name": "pay",
        "primary":   "#1890F8",
        "accent":    "#1890F8",
        "hero_fg":   "#FFFFFF",
        "hero_rule": "rgba(255,255,255,0.38)",
        "hero_hl":   "#FFE45A",   # 蓝底上亮黄
        "label": "异乡缴费色",
    },
    "white": {
        "name": "white",
        "primary":   "#F5F1EA",   # 奶白/米底
        "accent":    "#FF5A5F",   # 白日用品牌红做强调，避免全素
        "hero_fg":   "#1A1D1F",
        "hero_rule": "rgba(26,29,31,0.16)",
        "hero_hl":   "#FF5A5F",   # 米底上品牌红
        "label": "留白日",
    },
}


def theme_for(d: date) -> Theme:
    """按周几轮换：一三五 → 好居红，二四 → 缴费蓝，六日 → 留白日。"""
    wd = d.weekday()  # 0=Mon .. 6=Sun
    if wd in (0, 2, 4):
        return THEMES["uhomes"]
    if wd in (1, 3):
        return THEMES["pay"]
    return THEMES["white"]


class HeroData(TypedDict, total=False):
    # total=False: image_path 可缺省。其余字段在 fixture/生产链路里都应提供。
    title_zh: str
    title_en: str
    summary: str
    punch: str
    source: str
    image_path: str        # 本地封面图路径；缺省则走"大数字装饰"兜底


class ItemData(TypedDict):
    title_zh: str
    title_en: str
    summary: str
    source: str


class PosterData(TypedDict):
    date_str: str       # 2026年04月24日
    date_str_en: str    # APR 24 · 2026
    issue_no: str       # No.042
    theme: Theme        # 主题色（hero 背景 / 编号色 / section-bar）
    hero: HeroData
    items: list[ItemData]


def render_html(data: PosterData) -> str:
    tpl = _env.get_template("daily_digest.html.j2")

    hero = data["hero"]
    image_path = hero.get("image_path", "")
    hero_image_uri = ""
    if image_path:
        p = Path(image_path)
        if p.exists():
            hero_image_uri = _data_uri(p)

    ctx = {
        **data,
        "qr_uhomes": _data_uri(QR_UHOMES) if QR_UHOMES.exists() else "",
        "qr_pay": _data_uri(QR_PAY) if QR_PAY.exists() else "",
        "logo_uhomes": _data_uri(LOGO_UHOMES) if LOGO_UHOMES.exists() else "",
        "logo_pay": _data_uri(LOGO_PAY) if LOGO_PAY.exists() else "",
        "logo_combo": _data_uri(LOGO_COMBO) if LOGO_COMBO.exists() else "",
        "hero_image": hero_image_uri,
        # 无图时从 title/summary 抽第一个数字做巨型装饰；有图时不显示
        "hero_stat": "" if hero_image_uri else _extract_stat(
            hero.get("title_zh", ""), hero.get("summary", ""), hero.get("punch", "")
        ),
        "hero_title_html": _highlight(hero.get("title_zh", "")),
        "hero_summary_html": _highlight(hero.get("summary", "")),
        "hero_punch_html": _highlight(hero.get("punch", "")),
        "items_html": [
            {
                **it,
                "title_zh_html": _highlight(it["title_zh"]),
                "summary_html": _highlight(it["summary"]),
            }
            for it in data["items"]
        ],
    }
    return tpl.render(**ctx)


def render_png(data: PosterData, out_path: Path) -> Path:
    """渲染 HTML 并用 Playwright 截图为 PNG，返回 PNG 路径。"""
    html = render_html(data)

    # Write HTML to temp file inside templates dir so relative ../fonts paths resolve
    tmp_html = TEMPLATES_DIR / "_render_tmp.html"
    tmp_html.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1080, "height": 100},
                                          device_scale_factor=2)
            page = context.new_page()
            page.goto(f"file://{tmp_html}")
            # §11.1: wait for fonts before screenshot
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(200)

            # Locate .poster element and shoot exactly that
            poster = page.locator(".poster")
            poster.screenshot(path=str(out_path), type="png", omit_background=False)
            browser.close()
    finally:
        try:
            tmp_html.unlink()
        except FileNotFoundError:
            pass

    # §11.3: verify size under 2MB; JPEG fallback if needed
    size_bytes = out_path.stat().st_size
    if size_bytes > 2 * 1024 * 1024:
        from PIL import Image
        jpg_path = out_path.with_suffix(".jpg")
        Image.open(out_path).convert("RGB").save(jpg_path, "JPEG", quality=85, optimize=True)
        out_path.unlink()
        return jpg_path

    return out_path


if __name__ == "__main__":
    # Minimal smoke: use fixture data
    from datetime import datetime

    today = datetime(2026, 4, 24)
    fixture: PosterData = {
        "date_str": today.strftime("%Y年%m月%d日"),
        "date_str_en": today.strftime("%b %d · %Y").upper(),
        "issue_no": "No.042",
        "theme": theme_for(today.date()),
        "hero": {
            "title_zh": "密歇根两所旗舰公立大学面临州拨款 60% 削减",
            "title_en": "Michigan State, University of Michigan face over 60% cut under state funding bill",
            "summary": "密歇根州立法机构提出的拨款法案将对 MSU 与 UMich 两所旗舰公立大学削减超过 60% 的州级拨款，直接冲击奖学金池与国际招生预算。州校奖学金覆盖面或收窄，中国留学生家庭的成本账需要重新算。",
            "punch": "公立校财务压力再加剧，留学申请季家长需关注州校奖学金供给变化",
            "source": "Higher Ed Dive",
        },
        "items": [
            {
                "title_zh": "印度 TNE 跨国教育推进暴露人才短板",
                "title_en": "India's TNE push is exposing a workforce challenge universities are not addressing",
                "summary": "印度跨国教育蓬勃发展中，高校在开设海外分校时普遍忽视了人才队伍建设的实践问题。",
                "source": "The PIE News",
            },
            {
                "title_zh": "IDP 业务拓展至马来西亚，学生偏好正在迁移",
                "title_en": "IDP expands into Malaysia amid shifting student preferences",
                "summary": "长期聚焦美英澳加的 IDP 将业务拓展至马来西亚，应对学生偏好转向。",
                "source": "The PIE News",
            },
            {
                "title_zh": "英国七成高校国际研究生入学下滑，签证拒签是主因",
                "title_en": "UK: 7 in 10 universities report declining international postgraduate enrolments",
                "summary": "英国大学国际联合会调查显示，签证拒签率上升是国际研究生减少的重要因素。",
                "source": "The PIE News",
            },
            {
                "title_zh": "美国 Anna Maria 学院宣布关停",
                "title_en": "Anna Maria College Announces Closure",
                "summary": "美国部分小型私立学院在招生与财务方面持续承压，关停案例再添一例。",
                "source": "Higher Ed Dive",
            },
        ],
    }

    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)

    # 生成三种主题的对照图（红 / 蓝 / 白）—— 无图 + 大数字兜底
    for name, theme in THEMES.items():
        suffix = "" if theme == fixture["theme"] else f"_{name}"
        fname = f"poster_mock{suffix}.png" if suffix else "poster_mock.png"
        out = out_dir / fname
        data: PosterData = {**fixture, "theme": theme}
        result = render_png(data, out)
        print(f"✅ Rendered: {result.name} ({result.stat().st_size / 1024:.1f} KB, {theme['label']})")

    # 如果存在测试封面图，生成一张"有图版"做布局参考
    sample_img = ROOT / "assets" / "cache" / "article_images" / "sample_fixture.jpg"
    if sample_img.exists():
        with_image: PosterData = {
            **fixture,
            "hero": {**fixture["hero"], "image_path": str(sample_img)},
        }
        out = out_dir / "poster_mock_with_image.png"
        result = render_png(with_image, out)
        print(f"✅ Rendered: {result.name} ({result.stat().st_size / 1024:.1f} KB, 有图版演示)")
