#!/usr/bin/env python3
"""
P0 修复的测试脚本
测试：1. AI 内容验证机制 2. 消息截断逻辑
"""

import sys
sys.path.insert(0, '.')

from ai_summarizer import AISummarizer
from bot_wecom import safe_truncate_markdown
from config import get_logger

logger = get_logger(__name__)

def test_ai_validation():
    """测试 AI 内容验证"""
    print("\n" + "="*60)
    print("测试 1: AI 内容验证机制")
    print("="*60)

    summarizer = AISummarizer()

    # 模拟新闻列表
    mock_news = [
        {'title': '留学政策更新：英国PSW签证延长至3年', 'description': '英国政府宣布...', 'url': 'https://example.com/1'},
        {'title': 'QS世界大学排名2024发布', 'description': 'QS最新排名...', 'url': 'https://example.com/2'},
        {'title': '中国留学生数量持续增长', 'description': '数据显示...', 'url': 'https://example.com/3'}
    ]

    # 测试用例1: 正常总结 (应该通过验证)
    print("\n📝 测试用例 1: 正常总结")
    normal_summary = """
    📰 今日留学资讯要闻

    1. **留学政策更新：英国PSW签证延长至3年**
       英国政府宣布将PSW签证有效期从2年延长至3年，为国际学生提供更多就业机会。

    2. **QS世界大学排名2024发布**
       QS最新排名显示，英国和美国大学继续占据前列，中国大学表现亮眼。
    """

    is_valid = summarizer._validate_summary(normal_summary, mock_news, min_length=50)
    print(f"   结果: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 测试用例2: 过短的总结 (应该失败)
    print("\n📝 测试用例 2: 过短的总结")
    short_summary = "今日无新闻"
    is_valid = summarizer._validate_summary(short_summary, mock_news, min_length=50)
    print(f"   结果: {'❌ 未通过 (预期)' if not is_valid else '⚠️ 意外通过'}")

    # 测试用例3: 包含错误的总结 (应该失败)
    print("\n📝 测试用例 3: 包含错误提示的总结")
    error_summary = "⚠️ AI总结失败：无法连接到服务器"
    is_valid = summarizer._validate_summary(error_summary, mock_news, min_length=50)
    print(f"   结果: {'❌ 未通过 (预期)' if not is_valid else '⚠️ 意外通过'}")

    # 测试降级策略
    print("\n📝 测试用例 4: 降级策略")
    fallback = summarizer._fallback_summary(mock_news, "留学资讯")
    print(f"   降级输出长度: {len(fallback)} 字符")
    print(f"   结果: {'✅ 通过' if len(fallback) > 50 else '❌ 失败'}")
    print(f"\n   降级内容预览:\n{fallback[:200]}...")

    print("\n✅ AI 内容验证测试完成")


def test_message_truncation():
    """测试消息截断逻辑"""
    print("\n" + "="*60)
    print("测试 2: 消息截断逻辑")
    print("="*60)

    # 测试用例1: 正常长度消息 (不需要截断)
    print("\n📝 测试用例 1: 正常长度消息")
    normal_message = """
📅 **异乡早咖啡 - 2026年01月12日**

📰 今日要闻：

1. **留学政策更新**
   英国政府宣布 PSW 签证延长

2. **QS排名发布**
   最新世界大学排名出炉

💡 *Powered By 异乡有你*
"""

    result = safe_truncate_markdown(normal_message, max_bytes=4000)
    print(f"   原始长度: {len(normal_message.encode('utf-8'))} 字节")
    print(f"   结果长度: {len(result.encode('utf-8'))} 字节")
    print(f"   是否被截断: {'否 ✅' if result == normal_message else '是 ⚠️'}")

    # 测试用例2: 超长消息 (需要截断)
    print("\n📝 测试用例 2: 超长消息")

    # 构造一个超过 4000 字节的消息
    long_message_parts = ["📅 **异乡早咖啡 - 2026年01月12日**\n"]
    for i in range(100):
        long_message_parts.append(f"{i+1}. **新闻标题{i+1}** - 这是一条很长的新闻描述，包含大量中文字符以增加字节数。" * 3)
    long_message = "\n".join(long_message_parts)

    original_bytes = len(long_message.encode('utf-8'))
    result = safe_truncate_markdown(long_message, max_bytes=4000)
    result_bytes = len(result.encode('utf-8'))

    print(f"   原始长度: {original_bytes} 字节")
    print(f"   结果长度: {result_bytes} 字节")
    print(f"   是否符合限制: {'✅ 是' if result_bytes <= 4000 else '❌ 否'}")
    print(f"   是否包含截断提示: {'✅ 是' if '内容过长已截断' in result else '❌ 否'}")

    # 验证 UTF-8 编码完整性
    try:
        result.encode('utf-8').decode('utf-8')
        print(f"   UTF-8 编码完整性: ✅ 通过")
    except UnicodeDecodeError:
        print(f"   UTF-8 编码完整性: ❌ 失败")

    # 验证 Markdown 格式完整性 (简单检查)
    has_broken_markdown = '**' in result and result.count('**') % 2 != 0
    print(f"   Markdown 格式完整性: {'⚠️ 可能有问题' if has_broken_markdown else '✅ 良好'}")

    print("\n✅ 消息截断测试完成")


def test_run_lock():
    """测试运行锁机制"""
    print("\n" + "="*60)
    print("测试 3: 运行锁机制")
    print("="*60)

    from bot_wecom import check_run_lock, release_run_lock
    import os

    # 清理可能存在的锁文件
    if os.path.exists('.news_bot.lock'):
        os.remove('.news_bot.lock')

    # 测试用例1: 首次运行 (应该成功)
    print("\n📝 测试用例 1: 首次运行")
    can_run_1 = check_run_lock()
    print(f"   结果: {'✅ 可以运行' if can_run_1 else '❌ 被阻止'}")

    # 测试用例2: 锁已存在 (应该被阻止)
    print("\n📝 测试用例 2: 锁已存在")
    can_run_2 = check_run_lock()
    print(f"   结果: {'⚠️ 仍可运行 (意外)' if can_run_2 else '✅ 被阻止 (预期)'}")

    # 测试用例3: 释放锁后 (应该成功)
    print("\n📝 测试用例 3: 释放锁后再次运行")
    release_run_lock()
    can_run_3 = check_run_lock()
    print(f"   结果: {'✅ 可以运行' if can_run_3 else '❌ 被阻止'}")

    # 清理
    release_run_lock()

    print("\n✅ 运行锁测试完成")


if __name__ == '__main__':
    print("\n" + "🔍 P0 修复测试套件".center(60, "="))

    try:
        test_ai_validation()
        test_message_truncation()
        test_run_lock()

        print("\n" + "="*60)
        print("✅ 所有测试完成".center(60))
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
