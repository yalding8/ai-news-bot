import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_logger(name: str):
    return logging.getLogger(name)

# API Keys and Configuration
# API Keys and Configuration
_webhook_url = os.getenv('WECOM_WEBHOOK_URL', '')
WECOM_WEBHOOK_URLS = [url.strip() for url in _webhook_url.split(',') if url.strip()]
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
TIANAPI_KEY = os.getenv('TIANAPI_KEY')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')



# Active Topics
# 默认仅推送国际教育相关主题；如需扩展可通过 ACTIVE_TOPICS 环境变量覆盖
ACTIVE_TOPICS_ENV = os.getenv(
    'ACTIVE_TOPICS',
    'study_abroad,market_data,industry_news,edu_policy,uni_rankings'
)

# News Topics Configuration
NEWS_TOPICS = {
    'ai': {'name': 'AI科技', 'emoji': '🤖', 'desc': 'AI领域最新动态', 'color': '#4A90E2'},
    'finance': {'name': '财经新闻', 'emoji': '💰', 'desc': '金融市场和经济动态', 'color': '#F5A623'},
    'startup': {'name': '创业投资', 'emoji': '🚀', 'desc': '创业公司和投资动态', 'color': '#7ED321'},

    # 国际教育服务行业专业主题
    'study_abroad': {'name': '留学资讯', 'emoji': '✈️', 'desc': '留学政策、签证、院校动态', 'color': '#9013FE'},
    'market_data': {'name': '数据趋势', 'emoji': '📊', 'desc': '留学市场宏观数据、行业报告', 'color': '#7ED321'},
    'industry_news': {'name': '行业动态', 'emoji': '🏢', 'desc': '教育企业动态、投融资、战略合作', 'color': '#BD10E0'},
    'uni_rankings': {'name': '院校排名', 'emoji': '🏆', 'desc': '大学排名、院校评估动态', 'color': '#F5A623'},
    'edu_policy': {'name': '教育政策', 'emoji': '📜', 'desc': '各国教育政策、签证政策更新', 'color': '#4A90E2'},

    # 原有主题（保留）
    'education': {'name': '教育综合', 'emoji': '🎓', 'desc': '教育科技与综合资讯', 'color': '#BD10E0'},
    'pbsa': {'name': '学生公寓', 'emoji': '🏠', 'desc': 'PBSA学生公寓行业动态', 'color': '#50E3C2'},
    'uhomes': {'name': '异乡好居', 'emoji': '🏡', 'desc': '异乡好居企业动态', 'color': '#FF6B6B'}
}

# Topic Keywords (Moved from news_fetcher.py to keep config together)
TOPIC_KEYWORDS = {
    'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'ChatGPT', 'DeepSeek', '大模型'],
    'finance': ['财经', '金融', '股市', '经济', '投资'],
    'startup': ['创业', '融资', '风投', 'VC', '投资'],

    'study_abroad': [
        '留学', '出国', '海外留学', '留学申请', '留学中介', '留学服务',
        'study abroad', 'international students', 'overseas education'
    ],
    
    'market_data': [
        '留学市场', '教育市场', '市场报告', '行业报告', '留学趋势', '市场规模', '招生数据',
        'education market', 'study abroad market', 'student mobility', 'market report'
    ],

    'industry_news': [
        '留学机构', '教育机构', '融资', '并购', '上市', 'IPO', '战略合作',
        '新东方', '好未来', '高途', '多知网', '鲸媒体', '芥末堆',
        'education company', 'edtech', 'acquisition', 'funding', 'investment'
    ],

    'edu_policy': [
        '留学政策', '签证政策', '移民政策', '工作签证', 'PSW',
        'visa policy', 'immigration policy', 'international education policy'
    ],
    
    'uni_rankings': [
        '大学排名', 'QS排名', 'THE排名', 'US News排名',
        'university rankings', 'world rankings'
    ],

    # 原有主题关键字保留...
    'education': ['教育', '国际教育', '教育科技'],
    'pbsa': ['学生公寓', 'PBSA', '租房'],
    'uhomes': ['异乡好居', 'Uhomes']
}
