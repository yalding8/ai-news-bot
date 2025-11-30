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
    'study_abroad,edu_policy,uni_rankings,edu_market,competitors'
)

# News Topics Configuration
NEWS_TOPICS = {
    'ai': {'name': 'AI科技', 'emoji': '🤖', 'desc': 'AI领域最新动态', 'color': '#4A90E2'},
    'finance': {'name': '财经新闻', 'emoji': '💰', 'desc': '金融市场和经济动态', 'color': '#F5A623'},
    'startup': {'name': '创业投资', 'emoji': '🚀', 'desc': '创业公司和投资动态', 'color': '#7ED321'},

    # 国际教育服务行业专业主题
    'study_abroad': {'name': '留学资讯', 'emoji': '✈️', 'desc': '留学政策、签证、院校动态', 'color': '#9013FE'},
    'edu_policy': {'name': '教育政策', 'emoji': '📜', 'desc': '各国教育政策、签证政策更新', 'color': '#4A90E2'},
    'uni_rankings': {'name': '院校排名', 'emoji': '🏆', 'desc': '大学排名、院校评估动态', 'color': '#F5A623'},
    'edu_market': {'name': '教育市场', 'emoji': '📊', 'desc': '留学市场数据、行业趋势', 'color': '#7ED321'},
    'competitors': {'name': '行业动态', 'emoji': '🔍', 'desc': '竞品动态、行业资讯', 'color': '#BD10E0'},

    # 原有主题（保留）
    'education': {'name': '教育综合', 'emoji': '🎓', 'desc': '教育科技与综合资讯', 'color': '#BD10E0'},
    'pbsa': {'name': '学生公寓', 'emoji': '🏠', 'desc': 'PBSA学生公寓行业动态', 'color': '#50E3C2'},
    'uhomes': {'name': '异乡好居', 'emoji': '🏡', 'desc': '异乡好居企业动态', 'color': '#FF6B6B'}
}

# Topic Keywords (Moved from news_fetcher.py to keep config together)
TOPIC_KEYWORDS = {
    'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'ChatGPT', 'DeepSeek', '大模型', 'GPT', 'LLM', '神经网络', '自然语言处理', 'NLP', '计算机视觉', 'OpenAI', 'Google AI', '百度AI', '腾讯AI', '阿里AI'],
    'finance': ['财经', '金融', '股市', '经济', '投资'],
    'startup': ['创业', '融资', '风投', 'VC', '投资'],

    # 国际教育服务行业专业关键词
    'study_abroad': [
        # 中文关键词
        '留学', '出国', '海外留学', '留学申请', '留学中介', '留学服务',
        '美国留学', '英国留学', '澳洲留学', '加拿大留学', '欧洲留学', '新加坡留学', '香港留学',
        '澳大利亚留学', '新西兰留学',
        '英国大学', '美国大学', '澳大利亚大学', '新西兰大学', '香港高校', '英美澳港新高校',
        '本科留学', '研究生留学', 'MBA', '博士申请', '预科',
        # 英文关键词
        'study abroad', 'international students', 'overseas education',
        'college admission', 'university application', 'student visa',
        'F-1 visa', 'Tier 4 visa', 'study permit', 'international education',
        'uk student visa', 'british universities', 'us universities', 'australian universities',
        'new zealand student visa', 'hong kong university', 'hk visa',
    ],

    'edu_policy': [
        # 政策相关
        '留学政策', '签证政策', '移民政策', '工作签证', 'OPT', 'CPT', 'STEM OPT',
        '留学生政策', '国际学生', '入境政策', '移民新规', '签证申请',
        '英国签证', '美国签证', '澳大利亚签证', '新西兰签证', '香港签证',
        '英美澳港新签证', '英美澳港新移民政策',
        # 英文关键词
        'visa policy', 'immigration policy', 'study visa', 'student visa',
        'work permit', 'post-study work', 'graduate visa', 'PSW',
        'education policy', 'international education policy', 'immigration reform',
        'uk visa', 'us visa', 'australia visa', 'new zealand visa', 'hong kong visa',
    ],

    'uni_rankings': [
        # 中文关键词
        '大学排名', 'QS排名', 'THE排名', 'US News排名', '软科排名', 'ARWU',
        '世界大学排名', '专业排名', '商学院排名', '工程学院排名',
        '排名上升', '排名下降', '最佳大学',
        # 英文关键词
        'university rankings', 'QS rankings', 'THE rankings', 'world rankings',
        'best universities', 'top universities', 'college rankings',
        'academic rankings', 'QS World University Rankings',
    ],

    'edu_market': [
        # 市场数据
        '留学市场', '教育市场', '市场报告', '行业报告', '留学趋势',
        '市场规模', '留学数据', '招生数据', '国际学生数量', '留学人数',
        '市场分析', '行业分析', '增长趋势', '市场份额',
        # 英文关键词
        'education market', 'study abroad market', 'international education',
        'market report', 'enrollment data', 'student mobility',
        'market analysis', 'industry trends', 'market size', 'growth rate',
    ],

    'competitors': [
        # 主要竞品公司（根据实际情况调整）
        '新东方', '启德', '金吉列', '澳际', '威久', '学美', '前途出国',
        'EIC', 'IDP', '柳橙网', '小站教育', '啄木鸟', '天道',
        # 行业动态
        '留学机构', '教育机构', '融资', '并购', '上市', 'IPO',
        '教育投资', '教育并购', '战略合作', '合作伙伴',
        # 英文关键词
        'education company', 'study abroad agency', 'acquisition',
        'merger', 'funding', 'investment', 'partnership', 'collaboration',
    ],

    # 原有主题（保留）
    'education': ['教育', '国际教育', '教育科技', 'EdTech', '在线教育', '高等教育', '职业教育', '教育投资', 'MOOC', '慕课'],
    'pbsa': ['学生公寓', 'PBSA', '租房', '宿舍', 'student housing', 'student accommodation'],
    'uhomes': ['异乡好居', 'Uhomes', '留学生公寓', '海外租房']
}
