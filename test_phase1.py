#!/usr/bin/env python3
"""
Phase 1 测试脚本
验证评分模型改进效果
"""

from news_fetcher import NewsFetcher
from config import TOPIC_KEYWORDS

def test_scoring_model():
    """测试评分模型"""
    fetcher = NewsFetcher()
    keywords = TOPIC_KEYWORDS.get('study_abroad', [])

    test_cases = [
        {
            'name': '相关新闻（哈佛招生）',
            'news': {
                'title': '哈佛大学宣布2025年秋季招生截止日期延期',
                'description': '哈佛大学招生办公室今日宣布，由于签证政策变化，2025年秋季入学申请截止日期将延期至3月1日。国际学生应及时关注。',
                'source': '芥末堆',
                'url': 'https://example.com/1',
                'time': '2026-01-12'
            },
            'expected_min_score': 80,
            'expected_relevance': 0.8
        },
        {
            'name': '不相关新闻（煤炭港股）',
            'news': {
                'title': '36氪独家：某煤炭企业港股上市，市值达100亿',
                'description': '某煤炭企业今日在香港上市，首日股价上涨10%，市值突破100亿。',
                'source': '36kr',
                'url': 'https://example.com/2',
                'time': '2026-01-12'
            },
            'expected_score': 0,  # 应被淘汰
            'expected_relevance': 0.1
        },
        {
            'name': '弱相关新闻（AI教育）',
            'news': {
                'title': 'OpenAI推出新模型，或将改变教育行业',
                'description': 'OpenAI最新发布的GPT-5模型在教育领域表现出色，可能改变国际学生的学习方式。',
                'source': 'techcrunch',
                'url': 'https://example.com/3',
                'time': '2026-01-12'
            },
            'expected_min_score': 20,
            'expected_max_score': 50
        },
        {
            'name': '负面关键词惩罚测试',
            'news': {
                'title': '某教育科技公司A股上市，股价大涨',
                'description': '某教育科技公司今日在A股上市，首日涨停，市值达50亿。',
                'source': '虎嗅',
                'url': 'https://example.com/4',
                'time': '2026-01-12'
            },
            'expected_score': 0,  # 应被负面关键词惩罚或相关性过低
        }
    ]

    print('='*70)
    print('Phase 1 测试：评分模型验证')
    print('='*70)

    passed = 0
    failed = 0

    for i, case in enumerate(test_cases, 1):
        print(f'\n测试案例 {i}: {case["name"]}')
        print(f'标题: {case["news"]["title"]}')
        print(f'来源: {case["news"]["source"]}')

        news = case['news'].copy()
        score = fetcher.calculate_news_quality(news, keywords)
        relevance = news.get('education_relevance', 0)
        signal_level = news.get('signal_level', 3)

        print(f'教育相关性: {relevance:.2f}')
        print(f'信号等级: {signal_level}级')
        print(f'最终得分: {score:.1f}')

        # 验证结果
        test_passed = True

        if 'expected_score' in case:
            if score != case['expected_score']:
                print(f'❌ 失败：期望得分 {case["expected_score"]}，实际得分 {score:.1f}')
                test_passed = False

        if 'expected_min_score' in case:
            if score < case['expected_min_score']:
                print(f'❌ 失败：得分 {score:.1f} 低于最低期望 {case["expected_min_score"]}')
                test_passed = False

        if 'expected_max_score' in case:
            if score > case['expected_max_score']:
                print(f'❌ 失败：得分 {score:.1f} 高于最高期望 {case["expected_max_score"]}')
                test_passed = False

        if 'expected_relevance' in case:
            if abs(relevance - case['expected_relevance']) > 0.3:
                print(f'⚠️ 警告：相关性 {relevance:.2f} 与期望 {case["expected_relevance"]:.2f} 差异较大')

        if test_passed:
            print('✅ 通过')
            passed += 1
        else:
            failed += 1

        print('-'*70)

    print(f'\n测试总结：')
    print(f'✅ 通过: {passed}/{len(test_cases)}')
    print(f'❌ 失败: {failed}/{len(test_cases)}')

    return failed == 0

if __name__ == '__main__':
    success = test_scoring_model()
    exit(0 if success else 1)
