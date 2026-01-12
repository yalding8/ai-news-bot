#!/usr/bin/env python3
"""
测试泛科技内容过滤
验证AI大模型等不相关新闻能否被正确过滤
"""

from news_fetcher import NewsFetcher
from config import TOPIC_KEYWORDS

def test_agi_filter():
    """测试AI/AGI相关新闻过滤"""
    fetcher = NewsFetcher()
    keywords = TOPIC_KEYWORDS.get('study_abroad', [])

    test_cases = [
        {
            'name': 'AI大模型新闻（应被过滤）',
            'news': {
                'title': '唐杰/杨植麟/林俊旸/姚顺雨罕见同台，"基模四杰"开聊中国AGI',
                'description': '2026年1月10日，在清华大学基础模型北京市重点实验室与智谱AI发起的AGI-Next前沿峰会上，中国大模型领域的四位核心人物罕见同台。',
                'source': '量子位',
                'url': 'https://example.com/agi',
                'time': '2026-01-10'
            },
            'should_filter': True
        },
        {
            'name': 'AI用于留学申请（应保留）',
            'news': {
                'title': 'OpenAI推出留学申请AI助手，帮助国际学生撰写文书',
                'description': 'OpenAI最新发布的GPT-5模型专门针对留学申请场景优化，可以帮助国际学生撰写个人陈述和推荐信。',
                'source': 'techcrunch',
                'url': 'https://example.com/ai-study',
                'time': '2026-01-12'
            },
            'should_filter': False
        },
        {
            'name': '芯片行业新闻（应被过滤）',
            'news': {
                'title': '英伟达发布新一代AI芯片，算力提升10倍',
                'description': '英伟达在CES 2026上发布了新一代GPU芯片，专门用于AI训练和推理，算力相比上一代提升10倍。',
                'source': '虎嗅',
                'url': 'https://example.com/chip',
                'time': '2026-01-12'
            },
            'should_filter': True
        }
    ]

    print('='*70)
    print('测试：泛科技内容过滤')
    print('='*70)

    passed = 0
    failed = 0

    for i, case in enumerate(test_cases, 1):
        print(f'\n测试案例 {i}: {case["name"]}')
        print(f'标题: {case["news"]["title"]}')

        news = case['news'].copy()
        score = fetcher.calculate_news_quality(news, keywords)
        relevance = news.get('education_relevance', 0)

        print(f'教育相关性: {relevance:.2f}')
        print(f'最终得分: {score:.1f}')

        is_filtered = (score == 0)

        if case['should_filter']:
            if is_filtered:
                print('✅ 正确过滤')
                passed += 1
            else:
                print(f'❌ 应该过滤但未过滤，得分: {score:.1f}')
                failed += 1
        else:
            if not is_filtered:
                print('✅ 正确保留')
                passed += 1
            else:
                print('❌ 不应该过滤但被过滤了')
                failed += 1

        print('-'*70)

    print(f'\n测试总结：')
    print(f'✅ 通过: {passed}/{len(test_cases)}')
    print(f'❌ 失败: {failed}/{len(test_cases)}')

    return failed == 0

if __name__ == '__main__':
    success = test_agi_filter()
    exit(0 if success else 1)
