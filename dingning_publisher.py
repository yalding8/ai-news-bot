"""
跨项目发布器：把每日早咖啡 MDX 提交到 dingning-ai 仓库，触发 Vercel 自动部署。

设计原则：
- 失败不抛异常 —— 调用方应在文本消息里降级到通用 /coffee 入口
- 凭据走环境变量 —— GITHUB_TOKEN 仅存服务器 .env 或 GitHub Secrets，不进代码
- MDX 内容走"轻量索引"模式 —— 中文标题 + 短摘要（punch）+ 显眼原文链接，
  不复制原文长摘要，降低法律风险

GitHub Contents API 文档：
https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents
"""

import base64
import json
from datetime import datetime
from typing import Optional

import requests

from config import (
    DINGNING_GITHUB_TOKEN,
    DINGNING_REPO,
    DINGNING_BASE_URL,
    get_logger,
)

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _build_mdx(top_news: list, poster_items: list, today: datetime) -> str:
    """从 top_news（原始新闻）+ poster_items（AI 中文化结构）生成 MDX 文本。

    poster_items 字段：title_zh / title_en / summary / punch / source
    top_news[i] 字段：title / url / source 等

    MDX 内容只保留：中文标题 + punch（≤30 字）+ 原文链接。
    不收录长 summary，规避"市场替代"型版权风险。
    """
    date_iso = today.strftime("%Y-%m-%d")
    title = f"异乡早咖啡 · {date_iso}"
    n_items = min(len(poster_items), len(top_news))
    description = f"国际教育每日要闻 · {n_items} 条精选 · AI 辅助生成"

    lines = [
        "---",
        f'title: "{title}"',
        f'date: "{date_iso}"',
        f'slug: "{date_iso}"',
        f'description: "{description}"',
        "published: true",
        "---",
        "",
        "国际教育每日要闻 · AI 辅助生成 · 每日早 7:00 推送至社群",
        "",
        "## 今日要闻",
        "",
    ]

    for idx in range(n_items):
        item = poster_items[idx]
        news = top_news[idx]
        title_zh = (item.get("title_zh") or item.get("title_en") or news.get("title", "")).strip()
        punch = (item.get("punch") or "").strip()
        source = (item.get("source") or news.get("source") or "原文").strip()
        url = news.get("url", "").strip()

        lines.append(f"### {idx + 1}. {title_zh}")
        if punch:
            lines.append(punch)
        if url:
            lines.append(f"**[原文 →]({url})** {source}")
        lines.append("")

    return "\n".join(lines)


def _github_get_existing_sha(token: str, repo: str, path: str) -> Optional[str]:
    """检查目标文件是否已存在；存在则返回 sha（更新文件需要带 sha），否则 None。"""
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("sha")
        if resp.status_code == 404:
            return None
        logger.warning(f"⚠️ GitHub GET 异常 HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ GitHub GET 失败: {e}")
        return None


def publish_to_dingning(
    top_news: list,
    poster_items: list,
    today: Optional[datetime] = None,
) -> dict:
    """把当日 MDX 提交到 dingning-ai 仓库的 content/coffee/{date}.mdx。

    Returns:
        dict: {
            "success": bool,
            "url": str,        # 用于企微文本消息的"完整阅读"入口
            "slug": str,       # 形如 "2026-04-27"
            "error": str|None  # success=False 时附错误信息
        }
        success=False 时 url 退化为 DINGNING_BASE_URL/coffee（通用入口）。
    """
    today = today or datetime.now()
    slug = today.strftime("%Y-%m-%d")
    fallback_url = f"{DINGNING_BASE_URL}/coffee"
    target_url = f"{DINGNING_BASE_URL}/coffee/{slug}"

    if not DINGNING_GITHUB_TOKEN:
        logger.warning("⚠️ DINGNING_GITHUB_TOKEN 未设置，跳过 dingning.ai 同步")
        return {"success": False, "url": fallback_url, "slug": slug, "error": "no_token"}

    if not poster_items or not top_news:
        logger.warning("⚠️ poster_items 或 top_news 为空，跳过 dingning.ai 同步")
        return {"success": False, "url": fallback_url, "slug": slug, "error": "empty_input"}

    try:
        mdx = _build_mdx(top_news, poster_items, today)
    except Exception as e:
        logger.error(f"❌ MDX 构造失败: {e}")
        return {"success": False, "url": fallback_url, "slug": slug, "error": f"mdx_build:{e}"}

    path = f"content/coffee/{slug}.mdx"
    sha = _github_get_existing_sha(DINGNING_GITHUB_TOKEN, DINGNING_REPO, path)

    payload = {
        "message": f"feat(coffee): 异乡早咖啡 {slug}",
        "content": base64.b64encode(mdx.encode("utf-8")).decode("ascii"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha
        logger.info(f"📝 dingning.ai 已存在 {slug}.mdx，将覆盖更新（sha={sha[:7]}）")

    api_url = f"{GITHUB_API_BASE}/repos/{DINGNING_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {DINGNING_GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        resp = requests.put(api_url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        logger.error(f"❌ dingning.ai 提交异常: {e}")
        return {"success": False, "url": fallback_url, "slug": slug, "error": f"network:{e}"}

    if resp.status_code in (200, 201):
        commit_sha = (resp.json().get("commit") or {}).get("sha", "")[:7]
        logger.info(f"✅ dingning.ai MDX 已提交 (commit={commit_sha}) → {target_url}")
        return {"success": True, "url": target_url, "slug": slug, "error": None}

    logger.error(
        f"❌ dingning.ai 提交失败 HTTP {resp.status_code}: {resp.text[:300]}"
    )
    return {
        "success": False,
        "url": fallback_url,
        "slug": slug,
        "error": f"http_{resp.status_code}",
    }
