#!/usr/bin/env python3
"""
本地 smoke 脚本：不依赖网络，不真正发送 WeCom。
用途：上线前验证依赖、格式和日志输出。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# 确保可以从项目根目录导入模块
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from news_fetcher import NewsFetcher

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("smoke")


def build_fake_news():
    """构造 2 条假新闻，便于格式化验证。"""
    return [
        {
            "title": "DeepSeek 发布新一代模型，推理速度提升 2 倍",
            "description": "官方公布的基准数据显示，新模型在通用和代码任务上都有显著提升。",
            "source": "DeepSeek Blog",
            "url": "https://example.com/deepseek",
            "time": "2025-01-01",
        },
        {
            "title": "教育科技初创获 5000 万美元融资，布局个性化学习",
            "description": "投资方看好其自适应教学引擎，将加速海外市场拓展。",
            "source": "TechDaily",
            "url": "https://example.com/edtech",
            "time": "2025-01-02",
        },
    ]


def build_message(fake_news):
    """复刻 bot_wecom 的输出结构，但跳过 AI 和网络请求。"""
    today_date = datetime.now().strftime("%Y年%m月%d日")
    fetcher = NewsFetcher()
    news_text = fetcher.format_news_for_ai(fake_news)
    ai_summary = (
        "🤖 模型发布：DeepSeek 推出新一代模型，推理提速 2 倍，官方基准全面提升。"
        "\n🎓 教育科技：某初创获 5000 万美元融资，加速个性化学习和海外布局。"
    )

    news_links = "\n".join([f"• {n['title']}\n  {n['url']}" for n in fake_news])

    message = f"""🤖 AI科技 - {today_date}
📰 真实新闻 + AI智能总结（假数据，dry-run）

{ai_summary}

━━━━━━━━━━━━━━━━
🔗 新闻原文链接：

{news_links}

━━━━━━━━━━━━━━━━
✅ 本次为本地 dry-run，不会发送到企业微信
💡 摘要/链接格式与线上一致"""
    return news_text, message


def main():
    fake_news = build_fake_news()
    news_text, message = build_message(fake_news)

    logger.info("---- AI 输入格式 (format_news_for_ai) ----")
    print(news_text)
    logger.info("---- 企业微信最终消息 (dry-run) ----")
    print(message)
    logger.info("✅ smoke 结束，无实际网络请求")


if __name__ == "__main__":
    main()
