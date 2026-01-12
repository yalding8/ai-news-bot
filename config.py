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

# Topic Aliases (backward compatibility for old env values)
TOPIC_ALIASES = {
    # legacy/previous naming
    'edu_market': 'market_data',
    'competitors': 'industry_news',
}

# If enabled, still send a digest even when no new items are found
SEND_WHEN_NO_NEW = os.getenv('SEND_WHEN_NO_NEW', '0').strip().lower() in ('1', 'true', 'yes', 'y', 'on')

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

# Keywords to keep daily digest focused on international education content.
EDUCATION_RELEVANT_KEYWORDS = [
    '国际教育', '留学', '留学生', '出国', '海外留学', '申请', '录取', '录取率',
    '院校', '大学', '高校', '高等教育', '学费', '奖学金', '签证', '移民',
    '招生', '申请季', '排名', 'QS', 'THE', 'US News',
    'study abroad', 'international student', 'university', 'college',
    'higher education', 'tuition', 'admissions', 'visa', 'scholarship'
]

# Extra-weighted keywords for policy/admissions/visa emphasis.
EDUCATION_PRIORITY_KEYWORDS = [
    '政策', '法案', '规则', '法规', '监管', '审批',
    '签证', '移民', '留学签证', '学生签证', '工签', 'PSW',
    '招生', '录取', '申请', '申请季', '录取率', '截止',
    'admissions', 'acceptance', 'application', 'deadline',
    'visa', 'immigration', 'policy', 'regulation'
]

# Topic Keywords (Moved from news_fetcher.py to keep config together)
TOPIC_KEYWORDS = {
    'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'ChatGPT', 'DeepSeek', '大模型'],
    'finance': ['财经', '金融', '股市', '经济', '投资'],
    'startup': ['创业', '融资', '风投', 'VC', '投资'],

    'study_abroad': [
        '留学', '出国', '海外留学', '留学申请', '留学中介',        # 英文关键词
        'study abroad', 'international students', 'overseas education',
        'acceptance rate', 'waitlist', 'rejection', 'offer', 'deadline', # 新增招生动态词
        'released', 'decision', 'application portal', # 新增招生动态词
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

# ========== Phase 1 扩展：关键词库 ==========

# 1. 硬过滤词（必须命中，否则淘汰）
HARD_FILTER_KEYWORDS = [
    # 留学核心
    'study abroad', 'international students', 'overseas education',
    'visa', 'admissions', 'scholarship', 'tuition', 'immigration',
    '留学', '签证', '招生', '申请', '移民', '奖学金',

    # 政策核心
    'policy', 'regulation', 'deadline', 'application portal',
    '政策', '新规', '截止日期', '申请系统',

    # 招生核心
    'acceptance', 'offer', 'waitlist', 'rejection', 'decision',
    '录取', 'offer', '候补名单', '拒信', '放榜',

    # 数据核心
    'report', 'statistics', 'survey', 'white paper', 'ranking',
    '报告', '数据', '统计', '白皮书', '排名'
]

# 2. 负面关键词（一票否决）
NEGATIVE_KEYWORDS = [
    # K12教育（不需要）
    '早教', '幼教', '幼儿园', '托育', '保育',             # Early Education
    'K12', '中小学', '义务教育', '双减', '中考', '高考',   # Domestic K12
    '少儿英语', '素质教育', '编程', '奥数', '学区房',      # Specific domestic sectors
    '职业教育', '职教', '技校', '职高',                   # Vocational (domestic)
    '辅导机构', '补课', '培训班', '冬令营', '夏令营',      # General noise
    '研学', '营地教育', '研学旅行',                      # Specialized domestic noise

    # 国内考试（不需要）
    '考研', '公务员', '公考', '事业单位',

    # ========== Phase 1 新增：金融类（噪音） ==========
    '港股', 'A股', '证券', '基金', '煤炭', '钢铁', '房地产', '地产',
    'IPO', '上市公司', '财报', '市值', '股价', '股东',

    # ========== Phase 1 新增：娱乐类（噪音） ==========
    '游戏', '电竞', '直播', '网红', '带货', '短视频', '主播',

    # ========== Phase 1 新增：技术类（不相关） ==========
    '漏洞', '渗透测试', 'SQL注入', 'CISO', '安全漏洞', '黑客',

    # 特定品牌（噪音）
    '金宝贝', '美吉姆', '猿辅导', '作业帮', '火花思维', '编程猫',
]

# 3. 软过滤辅助词（加分项）
PRIORITY_KEYWORDS = {
    'policy': ['visa policy', 'immigration', 'regulation', '签证政策', '新规', '政策发布'],
    'admissions': ['admissions', 'deadline', 'acceptance rate', '录取率', '申请截止'],
    'data': ['report', 'statistics', 'survey', 'white paper', '报告', '数据', '白皮书'],
    'official': ['official', 'government', 'ministry', '官方', '教育部', '移民局']
}

# ================================================
