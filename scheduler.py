#!/usr/bin/env python3
"""
定时推送调度器
支持按配置文件自动推送新闻到企业微信/Telegram
"""

import os
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_schedule_config(config_file: str = 'schedule_config.json') -> dict:
    """加载调度配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"✅ 成功加载配置文件: {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"❌ 配置文件不存在: {config_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ 配置文件格式错误: {e}")
        return None


def send_news_wecom(topics: list, schedule_name: str = ""):
    """使用企业微信发送新闻"""
    try:
        # 动态导入 bot_wecom 模块
        import bot_wecom

        logger.info(f"📱 使用企业微信推送，任务名: {schedule_name}")

        for topic in topics:
            logger.info(f"📡 正在获取 {topic} 新闻...")
            news = bot_wecom.get_news(topic)
            success = bot_wecom.send_wecom_message(news)

            if success:
                logger.info(f"✅ {topic} 新闻推送成功")
            else:
                logger.error(f"❌ {topic} 新闻推送失败")

        return True
    except Exception as e:
        logger.error(f"❌ 企业微信推送失败: {e}")
        return False


def send_news_telegram(topics: list, schedule_name: str = ""):
    """使用Telegram发送新闻"""
    try:
        logger.info(f"📱 使用Telegram推送，任务名: {schedule_name}")
        logger.warning("⚠️ Telegram自动推送暂未实现，请手动使用 bot_deepseek.py")
        return False
    except Exception as e:
        logger.error(f"❌ Telegram推送失败: {e}")
        return False


def execute_schedule(schedule: dict, platform: str = "wecom"):
    """执行单个调度任务"""
    name = schedule.get('name', '未命名任务')
    topics = schedule.get('topics', [])

    if not topics:
        logger.warning(f"⚠️ 任务 '{name}' 没有配置主题，跳过")
        return False

    logger.info("=" * 60)
    logger.info(f"🚀 开始执行任务: {name}")
    logger.info(f"📋 推送主题: {', '.join(topics)}")
    logger.info(f"🕐 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 根据平台选择发送方式
    if platform == "wecom":
        success = send_news_wecom(topics, name)
    elif platform == "telegram":
        success = send_news_telegram(topics, name)
    else:
        logger.error(f"❌ 不支持的平台: {platform}")
        success = False

    if success:
        logger.info(f"✅ 任务 '{name}' 执行成功")
    else:
        logger.error(f"❌ 任务 '{name}' 执行失败")

    return success


def run_now(config_file: str = 'schedule_config.json', platform: str = "wecom", schedule_name: str = None):
    """立即运行指定的调度任务"""
    config = load_schedule_config(config_file)
    if not config:
        return False

    schedules = config.get('schedules', [])

    if schedule_name:
        # 运行指定名称的任务
        schedule = next((s for s in schedules if s['name'] == schedule_name), None)
        if schedule:
            if schedule.get('enabled', True):
                return execute_schedule(schedule, platform)
            else:
                logger.warning(f"⚠️ 任务 '{schedule_name}' 已被禁用")
                return False
        else:
            logger.error(f"❌ 找不到任务: {schedule_name}")
            return False
    else:
        # 运行所有启用的任务
        executed = 0
        for schedule in schedules:
            if schedule.get('enabled', True):
                execute_schedule(schedule, platform)
                executed += 1

        logger.info(f"✅ 共执行了 {executed} 个任务")
        return executed > 0


def check_schedule_time(config_file: str = 'schedule_config.json'):
    """检查当前时间是否匹配任何调度任务（用于cron调用）"""
    config = load_schedule_config(config_file)
    if not config:
        return

    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_weekday = now.weekday()  # 0=周一, 6=周日

    logger.info(f"🕐 当前时间: {current_time}, 星期{current_weekday + 1}")

    schedules = config.get('schedules', [])
    matched = False

    for schedule in schedules:
        if not schedule.get('enabled', True):
            continue

        schedule_time = schedule.get('time', '')
        schedule_weekday = schedule.get('weekday', None)

        # 检查时间匹配
        time_match = (schedule_time == current_time)

        # 检查星期匹配（如果设置了weekday）
        weekday_match = (schedule_weekday is None or schedule_weekday == current_weekday)

        if time_match and weekday_match:
            logger.info(f"⏰ 匹配到任务: {schedule['name']}")
            execute_schedule(schedule, platform="wecom")
            matched = True

    if not matched:
        logger.info("💤 当前时间没有匹配的任务")


def list_schedules(config_file: str = 'schedule_config.json'):
    """列出所有调度任务"""
    config = load_schedule_config(config_file)
    if not config:
        return

    schedules = config.get('schedules', [])

    print("\n" + "=" * 70)
    print("📋 定时推送任务列表")
    print("=" * 70)

    for i, schedule in enumerate(schedules, 1):
        status = "✅ 启用" if schedule.get('enabled', True) else "❌ 禁用"
        name = schedule.get('name', '未命名')
        time = schedule.get('time', '')
        weekday = schedule.get('weekday', None)
        topics = ', '.join(schedule.get('topics', []))
        desc = schedule.get('description', '')

        print(f"\n{i}. {name} [{status}]")
        print(f"   ⏰ 时间: {time}" + (f" (每周{weekday + 1})" if weekday is not None else " (每天)"))
        print(f"   📰 主题: {topics}")
        print(f"   📝 说明: {desc}")

    print("\n" + "=" * 70)
    print(f"💡 配置文件: {config_file}")
    print("=" * 70 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='新闻机器人定时推送调度器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有任务
  python scheduler.py --list

  # 立即运行所有启用的任务
  python scheduler.py --now

  # 运行指定名称的任务
  python scheduler.py --now --name "早间AI新闻"

  # 检查当前时间是否有任务需要执行（用于cron）
  python scheduler.py --check

  # 指定配置文件
  python scheduler.py --list --config my_config.json
        """
    )

    parser.add_argument('--list', '-l', action='store_true',
                        help='列出所有调度任务')
    parser.add_argument('--now', '-n', action='store_true',
                        help='立即运行调度任务')
    parser.add_argument('--check', '-c', action='store_true',
                        help='检查当前时间是否有任务需要执行（用于cron）')
    parser.add_argument('--name', type=str,
                        help='指定要运行的任务名称')
    parser.add_argument('--config', default='schedule_config.json',
                        help='配置文件路径 (默认: schedule_config.json)')
    parser.add_argument('--platform', '-p', choices=['wecom', 'telegram'],
                        default='wecom',
                        help='推送平台 (默认: wecom)')

    args = parser.parse_args()

    # 至少要指定一个操作
    if not (args.list or args.now or args.check):
        parser.print_help()
        return

    # 列出任务
    if args.list:
        list_schedules(args.config)

    # 立即运行
    if args.now:
        run_now(args.config, args.platform, args.name)

    # 检查时间匹配
    if args.check:
        check_schedule_time(args.config)


if __name__ == '__main__':
    main()
