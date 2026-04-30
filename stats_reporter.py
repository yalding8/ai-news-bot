"""
统计报告模块：查询 dingning.ai 阅读数据，格式化后推送运维企微群。

设计原则：
- 完全解耦，任何异常只 log 不抛出，不影响日报主流程
- send_stats_report() 是唯一对外接口
"""

import requests
from datetime import datetime, timedelta, timezone

from config import get_logger, DINGNING_BASE_URL

logger = get_logger(__name__)

_STATS_TIMEOUT = 10


def send_stats_report(ops_webhook_url: str) -> bool:
    if not ops_webhook_url:
        logger.info("ℹ️ WECOM_OPS_WEBHOOK_URL 未配置，跳过统计报告")
        return False

    try:
        data = _fetch_stats()
    except Exception as e:
        logger.warning(f"⚠️ 统计数据获取失败，跳过报告: {e}")
        return False

    report = _format_report(data)

    try:
        resp = requests.post(
            ops_webhook_url,
            json={"msgtype": "markdown", "markdown": {"content": report}},
            timeout=_STATS_TIMEOUT,
        )
        result = resp.json()
        if result.get("errcode") == 0:
            logger.info("✅ 统计报告已发送到运维群")
            return True
        logger.error(f"❌ 统计报告发送失败 errcode={result.get('errcode')}")
        return False
    except Exception as e:
        logger.error(f"❌ 统计报告发送异常: {e}")
        return False


def _fetch_stats() -> dict:
    url = f"{DINGNING_BASE_URL}/api/stats/coffee?days=8"
    resp = requests.get(url, timeout=_STATS_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _format_report(data: dict) -> str:
    items = data.get("items", [])
    weekly_avg = data.get("weekly_avg", 0)
    yesterday = data.get("yesterday", {})
    yesterday_views = yesterday.get("views", 0)
    yesterday_slug = yesterday.get("slug", "昨日")

    if weekly_avg > 0:
        ratio = yesterday_views / weekly_avg
        if ratio >= 1.2:
            trend = "✅ 高于均值"
        elif ratio >= 0.5:
            trend = "➡️ 接近均值"
        else:
            trend = "⚠️ 低于均值"
    else:
        trend = "➡️ 暂无均值"

    today_slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    chart_items = [i for i in items if i["slug"] not in (today_slug, yesterday_slug)]
    chart_items = sorted(chart_items, key=lambda x: x["slug"])[-6:]
    chart_items.append({"slug": yesterday_slug, "views": yesterday_views})

    max_views = max((i["views"] for i in chart_items), default=1) or 1
    bar_lines = []
    for item in chart_items:
        bar_len = max(1, round(item["views"] / max_views * 12)) if item["views"] else 0
        bar = "▓" * bar_len
        month_day = item["slug"][5:] if len(item["slug"]) == 10 else item["slug"]
        suffix = " ← 昨日" if item["slug"] == yesterday_slug else ""
        bar_lines.append(f"`{month_day}  {bar:<12} {item['views']}{suffix}`")

    lines = [
        "📊 **异乡早咖啡 · 昨日阅读数据**",
        "",
        f"昨日（{yesterday_slug}）：**{yesterday_views} 次阅读** {trend}",
        f"近 7 日均值：{weekly_avg} 次",
        "",
        "📈 近 7 日趋势：",
        *bar_lines,
        "",
        "_dingning.ai · Upstash Redis_",
    ]
    return "\n".join(lines)
