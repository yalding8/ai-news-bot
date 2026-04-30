#!/usr/bin/env python3
"""
AI新闻 企业微信群机器人版本
使用Webhook方式发送消息到企业微信群
集成真实新闻API，避免AI编造内容
"""

import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import concurrent.futures
import threading
from typing import Dict

from config import (
    WECOM_WEBHOOK_URLS, 
    NEWS_TOPICS, 
    ACTIVE_TOPICS_ENV, 
    TOPIC_ALIASES,
    SEND_WHEN_NO_NEW,
    EDUCATION_RELEVANT_KEYWORDS,
    EDUCATION_PRIORITY_KEYWORDS,
    get_logger
)
from news_fetcher import NewsFetcher, TOPIC_KEYWORDS
from ai_summarizer import AISummarizer
from news_cache import filter_new_news, mark_news_as_sent
from image_fetcher import fetch_article_image
from poster_generator import PosterData, render_png, theme_for

logger = get_logger(__name__)

# 复用新闻获取器（内置HTTP重试）
news_fetcher = NewsFetcher()

# 初始化AI总结器
ai_summarizer = AISummarizer()

# 企业微信发送使用的HTTP会话（带重试）
send_session = requests.Session()
_retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods={"POST"}
)
_adapter = HTTPAdapter(max_retries=_retries)
send_session.mount("http://", _adapter)
send_session.mount("https://", _adapter)


def parse_active_topics(raw: str) -> list:
    """从环境变量解析启用的主题列表"""
    topics = []
    for key in [t.strip() for t in raw.split(',')]:
        if not key:
            continue
        normalized = TOPIC_ALIASES.get(key, key)
        if normalized in NEWS_TOPICS:
            if normalized not in topics:
                topics.append(normalized)
            if normalized != key:
                logger.info(f"🔁 主题别名映射: {key} -> {normalized}")
        else:
            logger.warning(f"⚠️ 忽略未知主题: {key}")
    return topics

def filter_education_relevant_news(news_list: list) -> list:
    """保留国际教育强相关新闻，避免泛化资讯进入日报"""
    if not news_list:
        return []

    filtered = []
    for news in news_list:
        title = (news.get('title') or '').lower()
        description = (news.get('description') or '').lower()
        content = f"{title} {description}"
        if any(kw.lower() in content for kw in EDUCATION_RELEVANT_KEYWORDS):
            filtered.append(news)
    return filtered

def rank_education_news(news_list: list) -> list:
    """按政策/招生/签证相关度优先排序"""
    def score_news(news: dict) -> int:
        title = (news.get('title') or '').lower()
        description = (news.get('description') or '').lower()
        content = f"{title} {description}"
        score = 0
        score += sum(1 for kw in EDUCATION_RELEVANT_KEYWORDS if kw.lower() in content)
        score += 2 * sum(1 for kw in EDUCATION_PRIORITY_KEYWORDS if kw.lower() in content)
        return score

    return sorted(news_list, key=score_news, reverse=True)

def send_wecom_message(content: str, msgtype: str = "text") -> bool:
    """
    发送消息到企业微信群

    Args:
        content: 消息内容
        msgtype: 消息类型，支持 text/markdown

    Returns:
        bool: 发送是否成功
    """
    if not WECOM_WEBHOOK_URLS:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        return False

    # 构造消息体
    if msgtype == "markdown":
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    else:
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

    all_success = True
    unique_webhooks = list(dict.fromkeys(WECOM_WEBHOOK_URLS))
    if len(unique_webhooks) < len(WECOM_WEBHOOK_URLS):
        logger.info(f"🔁 去重Webhook: {len(WECOM_WEBHOOK_URLS)} -> {len(unique_webhooks)}")
    for webhook_url in unique_webhooks:
        try:
            response = send_session.post(
                webhook_url,
                json=data,
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"❌ 消息发送失败 ({webhook_url[-10:]}) HTTP {response.status_code}: {response.text[:200]}")
                all_success = False
                continue

            try:
                result = response.json()
            except ValueError:
                logger.error(f"❌ 消息发送失败，非JSON响应: {response.text[:200]}")
                all_success = False
                continue

            if result.get('errcode') == 0:
                logger.info(f"✅ 消息发送成功 ({webhook_url[-10:]})")
            else:
                logger.error(f"❌ 消息发送失败 errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
                all_success = False

        except Exception as e:
            logger.error(f"❌ 发送消息时出错 ({webhook_url[-10:]}): {e}")
            all_success = False

    return all_success


def process_topic_news(topic_key: str) -> Dict:
    """
    处理单个主题的新闻（获取 -> 总结 -> 返回结构化数据）
    """
    topic_cfg = NEWS_TOPICS.get(topic_key)
    if not topic_cfg:
        return {"success": False, "error": f"未找到主题配置: {topic_key}"}
    
    logger.info(f"🚀 开始处理主题: {topic_cfg['name']}")
    
    try:
        # 1. 获取新闻
        logger.info(f"  └─ 从所有新闻源获取真实新闻（API + RSS）...")
        keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
        all_news = news_fetcher.fetch_news(topic_key, keywords, num=15)
        
        # 2. 过滤
        logger.info(f"  └─ 过滤重复新闻...")
        real_news = filter_new_news(topic_key, all_news)

        if not real_news:
            if not all_news:
                logger.warning(f"  └─ 未获取到真实新闻")
                return {
                    "success": True,
                    "topic_key": topic_key,
                    "topic_name": topic_cfg['name'],
                    "emoji": topic_cfg['emoji'],
                    "content": "⚠️ 暂时无法获取实时新闻，可能API配额耗尽或网络问题。",
                    "news_links": []
                }
            else:
                logger.info(f"  └─ 今日{topic_cfg['name']}暂无新内容")
                return {
                    "success": True,
                    "topic_key": topic_key,
                    "topic_name": topic_cfg['name'],
                    "emoji": topic_cfg['emoji'],
                    "content": "✅ 今日暂无新内容（已自动过滤重复资讯）",
                    "news_links": []
                }

        logger.info(f"  └─ 获取到 {len(real_news)} 条真实新闻")
        news_text = news_fetcher.format_news_for_ai(real_news)

        # 3. AI 总结
        ai_summary = ai_summarizer.summarize_news(topic_key, real_news, news_text)
        logger.info(f"✅ {topic_cfg['name']} 总结完成")
        
        # 4. 标记新闻为已推送
        mark_news_as_sent(topic_key, real_news)

        # 5. 构造返回结果
        return {
            "success": True,
            "topic_key": topic_key,
            "topic_name": topic_cfg['name'],
            "emoji": topic_cfg['emoji'],
            "content": ai_summary,
            "news_links": [{"title": n['title'], "url": n['url']} for n in real_news[:3]]
        }

    except Exception as e:
        logger.error(f"❌ 处理主题 {topic_key} 失败: {e}")
        return {"success": False, "error": str(e), "topic_key": topic_key}


def build_poster_data(top_news: list, poster_items: list) -> PosterData:
    """
    把 top_news 原始新闻 + AI 结构化摘要 → PosterData。
    hero = 第 1 条（抓 og:image 作为封面），items = 第 2-5 条。
    """
    from datetime import datetime
    from pathlib import Path

    today = datetime.now()

    # hero 封面：抓文章 og:image（失败则留空，走海报的大数字兜底）
    hero_raw = top_news[0] if top_news else {}
    hero_item = poster_items[0] if poster_items else {}
    hero_image_path = ""
    if hero_raw.get("url"):
        try:
            img = fetch_article_image(hero_raw["url"])
            if img and Path(img).exists():
                hero_image_path = str(img)
                logger.info(f"🖼️  Hero 封面已缓存: {img}")
        except Exception as e:
            logger.warning(f"⚠️ Hero 封面抓取失败: {e}")

    hero: dict = {
        "title_zh": hero_item.get("title_zh", ""),
        "title_en": hero_item.get("title_en", hero_raw.get("title", "")),
        "summary": hero_item.get("summary", ""),
        "punch": hero_item.get("punch", ""),
        "source": hero_item.get("source", hero_raw.get("source", "")),
    }
    if hero_image_path:
        hero["image_path"] = hero_image_path

    items: list = []
    for it in poster_items[1:5]:
        items.append({
            "title_zh": it.get("title_zh", ""),
            "title_en": it.get("title_en", ""),
            "summary": it.get("summary", ""),
            "source": it.get("source", ""),
        })

    issue_no = f"No.{today.timetuple().tm_yday:03d}"

    return {
        "date_str": today.strftime("%Y年%m月%d日"),
        "date_str_en": today.strftime("%b %d · %Y").upper(),
        "issue_no": issue_no,
        "theme": theme_for(today.date()),
        "hero": hero,
        "items": items,
    }


def send_wecom_image(image_path: "Path") -> bool:
    """
    发送图片到企业微信群（image 消息类型：base64 + md5）。
    企微上限 2MB，超限由 poster_generator 已自动转 JPEG。
    """
    import base64
    import hashlib

    if not WECOM_WEBHOOK_URLS:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        return False

    try:
        raw = image_path.read_bytes()
    except Exception as e:
        logger.error(f"❌ 读取海报失败: {e}")
        return False

    size_kb = len(raw) / 1024
    if len(raw) > 2 * 1024 * 1024:
        logger.error(f"❌ 海报 {size_kb:.1f} KB 超过企微 2MB 上限")
        return False

    data = {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(raw).decode("ascii"),
            "md5": hashlib.md5(raw).hexdigest(),
        },
    }

    all_success = True
    unique_webhooks = list(dict.fromkeys(WECOM_WEBHOOK_URLS))
    for webhook_url in unique_webhooks:
        try:
            response = send_session.post(webhook_url, json=data, timeout=15)
            if response.status_code != 200:
                logger.error(f"❌ 海报发送失败 ({webhook_url[-10:]}) HTTP {response.status_code}")
                all_success = False
                continue
            result = response.json()
            if result.get("errcode") == 0:
                logger.info(f"✅ 海报发送成功 ({webhook_url[-10:]}, {size_kb:.1f} KB)")
            else:
                logger.error(f"❌ 海报发送失败 errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
                all_success = False
        except Exception as e:
            logger.error(f"❌ 海报发送异常 ({webhook_url[-10:]}): {e}")
            all_success = False

    return all_success


def send_daily_news(topics: list = None):
    """
    发送每日新闻汇总（合并所有主题为一条消息，去重）

    Args:
        topics: 要发送的主题列表（用于获取新闻源，但最终合并展示）
    """
    if topics is None:
        topics = list(NEWS_TOPICS.keys())

    logger.info(f"📰 开始获取新闻，涉及 {len(topics)} 个主题源")

    # 并行从所有主题获取新闻
    all_news = []
    seen_urls = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(topics), 5)) as executor:
        future_to_topic = {
            executor.submit(fetch_topic_news_raw, topic): topic
            for topic in topics
        }
        for future in concurrent.futures.as_completed(future_to_topic):
            try:
                news_list = future.result()
                # 按URL去重
                for news in news_list:
                    if news['url'] not in seen_urls:
                        seen_urls.add(news['url'])
                        all_news.append(news)
            except Exception as exc:
                logger.error(f"❌ 获取新闻异常: {exc}")

    if not all_news:
        logger.warning("⚠️ 未获取到任何新闻，取消发送日报")
        return

    logger.info(f"📊 合并去重后共 {len(all_news)} 条新闻")

    # 过滤已推送的新闻
    if SEND_WHEN_NO_NEW:
        logger.info("🟡 SEND_WHEN_NO_NEW 已启用，跳过去重过滤")
        new_news = all_news
    else:
        new_news = filter_new_news('daily_digest', all_news)
        if not new_news:
            logger.warning("⚠️ 所有新闻均已推送过，取消发送日报")
            return

    logger.info(f"📰 筛选出 {len(new_news)} 条未推送新闻")

    # 进一步收敛到国际教育相关新闻，并按政策/招生/签证倾向排序
    education_news = filter_education_relevant_news(new_news)
    if education_news:
        logger.info(f"🎯 国际教育相关过滤: {len(new_news)} -> {len(education_news)}")
        new_news = rank_education_news(education_news)
    else:
        logger.warning("⚠️ 未筛到明显国际教育相关新闻，跳过本次日报")
        return

    # 全局来源多样性：每个来源最多出现 2 次，保证最终 9 条覆盖尽量多的来源
    source_counts: dict = {}
    diverse_news = []
    for n in new_news:
        src = n.get('source', '')
        if source_counts.get(src, 0) < 2:
            diverse_news.append(n)
            source_counts[src] = source_counts.get(src, 0) + 1
    logger.info(f"🌐 全局来源多样性过滤: {len(new_news)} -> {len(diverse_news)} 条（来自 {len(source_counts)} 个来源）")
    new_news = diverse_news

    # 取前 9 条做海报候选（hero + 4 items），剩余可作链接兜底
    top_news = new_news[:9]
    news_text = news_fetcher.format_news_for_ai(top_news)

    import time
    from dingning_publisher import publish_to_dingning
    from config import DINGNING_BASE_URL, DINGNING_DEPLOY_WAIT_SEC

    # AI 摘要先做（海报和 MDX 都依赖它）
    poster_items = None
    try:
        poster_items = ai_summarizer.summarize_for_poster(top_news, news_text)
    except Exception as e:
        logger.error(f"❌ AI 海报摘要异常: {e}")

    # publish 提前到海报生成之前 —— Vercel 在后台构建时本地继续做海报，
    # 把"等部署"和"发海报"重叠，缩短海报到文本的群内可见间隔
    coffee_url = f"{DINGNING_BASE_URL}/coffee"
    publish_start = None
    if poster_items:
        publish_result = publish_to_dingning(top_news[:5], poster_items[:5])
        coffee_url = publish_result["url"]
        if publish_result["success"]:
            publish_start = time.time()
    else:
        logger.warning("⚠️ poster_items 为空，跳过 dingning.ai 同步，文本走通用入口")

    # 海报：渲染 PNG → 发图片
    if poster_items:
        try:
            poster_data = build_poster_data(top_news, poster_items)
            from pathlib import Path
            out_dir = Path(__file__).parent / "out"
            out_dir.mkdir(exist_ok=True)
            png_path = out_dir / f"poster_{datetime.now().strftime('%Y%m%d')}.png"
            final_path = render_png(poster_data, png_path)
            logger.info(f"🎨 海报已生成: {final_path.name} ({final_path.stat().st_size / 1024:.1f} KB)")
            send_wecom_image(final_path)
        except Exception as e:
            logger.error(f"❌ 海报流程异常（不影响文本发送）: {e}")

    # 标记为已推送
    mark_news_as_sent('daily_digest', top_news)

    # 等 Vercel 部署完成 —— 扣掉海报已耗时，sleep 剩余时间
    if publish_start is not None and DINGNING_DEPLOY_WAIT_SEC > 0:
        elapsed = time.time() - publish_start
        remaining = max(0, DINGNING_DEPLOY_WAIT_SEC - elapsed)
        if remaining > 0:
            logger.info(f"⏳ Vercel 部署等待剩余 {remaining:.0f}s（已发海报耗时 {elapsed:.0f}s）...")
            time.sleep(remaining)
        else:
            logger.info(f"⏩ 海报耗时 {elapsed:.0f}s 已覆盖部署等待，直接发文本")

    # 文本（极简版）：海报补充 —— 详情入口收口到 dingning.ai，自家小程序保留。
    # 小程序 schema 必须各自独占一行：同行多 schema + 分隔符会触发企微 markdown
    # 解析降级，导致小程序卡片不可点（2026-04-27 验证）。
    today_date = datetime.now().strftime("%Y年%m月%d日")
    coffee_link_text = coffee_url.replace("https://", "").replace("http://", "")
    coffee_url_utm = f"{coffee_url}?utm_source=wecom&utm_medium=group&utm_campaign=daily"
    message_parts = [
        f"📅 **异乡早咖啡 · {today_date}**",
        "更多细节见上方海报 ☝️\n",
        f"📖 **完整阅读** → [{coffee_link_text}]({coffee_url_utm})\n",
        "🏠 **异乡好居** - 留学生海外的家 [#小程序://异乡好居/vvS67rZGtrvbQIn]",
        "💰 **异乡缴费** - 比一比更省钱 [#小程序://异乡缴费/8d32ABZvjBHh1vd]",
        "\n💡 *Powered By 异乡有你，AI驱动 • 实时聚合全球国际教育资讯*",
    ]

    final_message = "\n".join(message_parts)
    byte_length = len(final_message.encode('utf-8'))
    logger.info(f"📊 文本长度: {len(final_message)} 字符, {byte_length} 字节")

    logger.info("📤 正在发送补充文本（详情入口 + 小程序）...")
    if send_wecom_message(final_message, msgtype="markdown"):
        logger.info("✅ 补充文本发送成功")
    else:
        logger.error("❌ 补充文本发送失败")

    # 发送昨日统计报告到运维群（失败不影响主流程）
    try:
        from stats_reporter import send_stats_report
        from config import WECOM_OPS_WEBHOOK_URL
        send_stats_report(WECOM_OPS_WEBHOOK_URL)
    except Exception as e:
        logger.warning(f"⚠️ 统计报告发送异常（不影响日报）: {e}")


def fetch_topic_news_raw(topic_key: str) -> list:
    """获取单个主题的原始新闻列表（不做AI总结）"""
    logger.info(f"  └─ 获取主题: {topic_key}")
    keywords = TOPIC_KEYWORDS.get(topic_key, [topic_key])
    return news_fetcher.fetch_news(topic_key, keywords, num=15)


def check_run_lock():
    """
    检查运行锁，防止重复执行

    Returns:
        bool: 是否可以运行
    """
    import os
    import time

    lock_file = ".news_bot.lock"
    lock_timeout = 3600  # 1小时超时

    # 检查锁文件是否存在
    if os.path.exists(lock_file):
        # 检查锁文件的修改时间
        lock_mtime = os.path.getmtime(lock_file)
        if time.time() - lock_mtime < lock_timeout:
            logger.warning("⚠️ 检测到其他实例正在运行，跳过本次执行")
            return False
        else:
            logger.info("🔓 清理过期的锁文件")
            os.remove(lock_file)

    # 创建锁文件
    try:
        with open(lock_file, 'w') as f:
            f.write(f"{time.time()}\n")
        logger.debug("🔒 创建运行锁")
        return True
    except Exception as e:
        logger.error(f"❌ 创建锁文件失败: {e}")
        return True  # 锁失败时仍然运行

def release_run_lock():
    """释放运行锁"""
    import os
    lock_file = ".news_bot.lock"
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            logger.debug("🔓 释放运行锁")
    except Exception as e:
        logger.warning(f"⚠️ 释放锁失败: {e}")

def main():
    """主函数"""
    if not WECOM_WEBHOOK_URLS:
        logger.error("错误：未设置 WECOM_WEBHOOK_URL")
        logger.info("请在 .env 文件中设置企业微信Webhook URL")
        return

    # ✅ 新增: 检查运行锁，防止重复执行
    if not check_run_lock():
        logger.info("⏭️ 跳过本次执行（检测到其他实例运行中）")
        return

    try:
        logger.info("🚀 企业微信新闻机器人启动")

        # 解析环境变量决定推送哪些主题
        active_topics = parse_active_topics(ACTIVE_TOPICS_ENV)
        if not active_topics:
            active_topics = ['ai', 'education']

        logger.info(f"📡 开始执行新闻任务（{len(active_topics)}个主题）...")
        send_daily_news(active_topics)

    finally:
        # ✅ 确保释放锁
        release_run_lock()

if __name__ == '__main__':
    main()
