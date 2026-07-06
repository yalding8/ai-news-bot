import os
import logging
from dotenv import load_dotenv

# Load environment variables.
# override=True: .env 是 webhook / LLM 路由的唯一真相源，覆盖宿主进程里可能残留的
# 陈旧 export（2026-06-02 事故：长命 shell 残留 WECOM_WEBHOOK_URL/LLM_* 盖住 .env，
# 导致手动运行发错群 / 打错 LLM endpoint）。.env 未定义的 key（如 CI secrets）不受影响。
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_logger(name: str):
    return logging.getLogger(name)

# API Keys and Configuration
_webhook_url = os.getenv('WECOM_WEBHOOK_URL', '')
WECOM_WEBHOOK_URLS = [url.strip() for url in _webhook_url.split(',') if url.strip()]
WECOM_OPS_WEBHOOK_URL = os.getenv('WECOM_OPS_WEBHOOK_URL', '').strip()
DEEPSEEK_API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
TIANAPI_KEY = os.getenv('TIANAPI_KEY')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')

# LLM 接入（OpenAI 兼容）。默认走阿里云百炼上的 DeepSeek v4-pro；
# 切回火山方舟 Ark：LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 LLM_MODEL=deepseek-v3-2-251201
# 切回 DeepSeek 官方：LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-chat
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-v4-pro')



# Active Topics
# 默认仅推送国际教育相关主题；如需扩展可通过 ACTIVE_TOPICS 环境变量覆盖。
# DEFAULT 同时是 bot_wecom.main() 在 ACTIVE_TOPICS 全为未知主题时的兜底值。
ACTIVE_TOPICS_DEFAULT = 'study_abroad,market_data,industry_news,edu_policy,uni_rankings'
ACTIVE_TOPICS_ENV = os.getenv('ACTIVE_TOPICS', ACTIVE_TOPICS_DEFAULT)

# Topic Aliases (backward compatibility for old env values)
TOPIC_ALIASES = {
    # legacy/previous naming
    'edu_market': 'market_data',
    'competitors': 'industry_news',
}

# If enabled, still send a digest even when no new items are found
SEND_WHEN_NO_NEW = os.getenv('SEND_WHEN_NO_NEW', '0').strip().lower() in ('1', 'true', 'yes', 'y', 'on')

# ========== dingning.ai 跨项目发布 ==========
# 每日早咖啡 MDX 通过 GitHub Contents API 提交到 dingning-ai 仓库，
# Vercel 检测到 push 后自动重新构建部署。
# GITHUB_TOKEN: classic PAT 或 fine-grained PAT，需对 yalding8/dingning-ai 仓库有 contents:write 权限
DINGNING_GITHUB_TOKEN = os.getenv('DINGNING_GITHUB_TOKEN', '').strip()
DINGNING_REPO = os.getenv('DINGNING_REPO', 'yalding8/dingning-ai').strip()
DINGNING_BASE_URL = os.getenv('DINGNING_BASE_URL', 'https://dingning.ai').strip().rstrip('/')
# Vercel 部署等待秒数：MDX commit 后等多久再推企微文本，确保用户点链接时页面已就绪。
# bot_wecom.send_daily_news 会扣减"海报渲染+发送"的已耗时，实际 sleep = wait_sec - elapsed。
DINGNING_DEPLOY_WAIT_SEC = int(os.getenv('DINGNING_DEPLOY_WAIT_SEC', '60'))

# News Topics Configuration
NEWS_TOPICS = {
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

# 负面关键词（一票否决；抓取层 contains_negative_keywords 与评分层
# calculate_news_quality 的 -20 惩罚共用这份单一真相源）
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

# ========== 评分/分级关键词表（单一真相源，供 news_scoring 使用） ==========

# 高价值关键词：标题命中 +5 / 描述命中 +2。
# THE 排名必须写全称：裸 'the' 会命中几乎所有英文标题（AUDIT 2026-07-05 C1）
HIGH_VALUE_KEYWORDS = [
    'visa', 'policy', 'visa policy', 'breaking', 'ranking', 'qs',
    'times higher education', 'immigration', 'urgent',
    '签证', '政策', '排名', '最新', '发布',
]

# 来源可信度分层（education 固定 35 / academic 30 / quality 20 / tech 25×相关性打折）
SOURCE_TIERS = {
    'education': [
        'inside higher ed', 'the pie news', 'icef',
        'jiemodui', '芥末堆', 'duozhi', '多知',
        'study international', 'university business',
        'university affairs', 'wonkhe', 'campus review',
    ],
    'academic': ['nature', 'science', 'mit technology review'],
    'tech': [
        'techcrunch', '36kr', 'venturebeat',
        'latepost', '晚点', 'caixin', '财新',
    ],
    'quality': [
        'qs', 'topuniversities', 'higher ed dive',
        'bloomberg', 'reuters',
    ],
}

# 教育相关性系数：泛科技话题（无强留学词时降为 0.1）
RELEVANCE_TECH_IRRELEVANT = [
    '大模型', 'agi', 'llm', 'gpt', '算力', '芯片', '半导体',
    '开源', 'transformer', '推理', '训练', 'token',
]
# 强相关词（留学核心）：≥3 个 → 1.0，≥1 个 → 0.8
RELEVANCE_STRONG_KEYWORDS = [
    'study abroad', 'international students', 'overseas education',
    'visa', 'admissions', 'scholarship', 'tuition', 'immigration',
    '留学', '签证', '招生', '申请', '移民', '奖学金',
]
# 弱相关词（泛教育）：≥2 个 → 0.5，≥1 个 → 0.3
RELEVANCE_WEAK_KEYWORDS = ['education', 'university', 'student', 'college', '教育', '大学', '学生']

# 信号分级：1=事实变更（政策/签证/截止日期）2=权威解读 3=泛资讯
SIGNAL_LEVEL1_DOMAINS = ['.gov', '.edu', 'gov.uk', 'state.gov', 'uscis.gov', 'homeaffairs.gov.au']
SIGNAL_LEVEL1_KEYWORDS = [
    'policy', 'regulation', 'visa update', 'deadline', 'application open',
    '政策', '新规', '签证', '截止日期', '开放申请', '放榜', '录取',
]
SIGNAL_LEVEL2_SOURCES = [
    'pie news', 'icef', 'inside higher ed',
    '芥末堆', 'university affairs', 'wonkhe', 'campus review',
    'qs', 'topuniversities', 'higher ed dive',
]
SIGNAL_LEVEL2_KEYWORDS = [
    'report', 'statistics', 'survey', 'white paper', 'data release',
    '报告', '数据', '统计', '调查', '白皮书', '趋势分析',
]

# ========== 新闻源（主题 → 源，与 NEWS_TOPICS/TOPIC_KEYWORDS 同处一文件） ==========

# 天行数据接口映射（不同主题对应不同接口）
TIANAPI_ENDPOINTS = {
    'finance': '/caijing/index',   # 财经新闻专用接口
    'startup': '/guonei/index',    # 其余主题：国内新闻+关键词
    'study_abroad': '/guonei/index',
    'edu_policy': '/guonei/index',
    'uni_rankings': '/guonei/index',
    'market_data': '/guonei/index',
    'industry_news': '/guonei/index',
    'education': '/guonei/index',
    'pbsa': '/guonei/index',
    'uhomes': '/guonei/index',
}

# RSS 订阅源
RSS_FEEDS = {
    'finance': [
        'https://www.36kr.com/feed',              # 36氪
        'http://dedicated.wallstreetcn.com/rss.xml', # 华尔街见闻
    ],
    'startup': [
        'http://www.cyzone.cn/rss/',              # 创业邦
        'https://www.36kr.com/feed',              # 36氪
        'https://hnrss.org/newest?q=startup',     # Hacker News Startup
    ],
    'study_abroad': [
        'https://thepienews.com/feed/',              # The PIE News
        'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
        'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
        'https://universitybusiness.com/feed/',      # University Business
        'https://monitor.icef.com/feed/',            # ICEF Monitor
        'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
        'https://www.jiemodui.com/rss.xml',          # 芥末堆
    ],
    'edu_policy': [
        'https://thepienews.com/feed/',              # The PIE News
        'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
        'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
        'https://monitor.icef.com/feed/',            # ICEF Monitor
        'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
        'https://www.jiemodui.com/rss.xml',          # 芥末堆
        'https://www.gov.uk/government/organisations/uk-visas-and-immigration.atom',  # UKVI
        'https://www.gov.uk/government/organisations/home-office.atom',               # Home Office
        'https://www.gov.uk/government/organisations/department-for-education.atom',  # DfE
        'https://www.gov.uk/government/organisations/office-for-students.atom',       # OfS
    ],
    'uni_rankings': [
        'https://monitor.icef.com/feed/',            # ICEF Monitor
        'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
        'https://wonkhe.com/feed/',                  # WonkHE (UK HE policy)
        'https://thepienews.com/feed/',              # The PIE News
    ],
    'market_data': [
        'https://monitor.icef.com/feed/',            # ICEF Monitor
        'https://thepienews.com/feed/',              # The PIE News
        'https://www.jiemodui.com/rss.xml',          # 芥末堆
    ],
    'industry_news': [
        'https://www.jiemodui.com/rss.xml',          # 芥末堆
        # 36氪通用 feed 已移除：泛商业科技快讯污染国际教育主题
        'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
    ],
    'education': [
        'https://www.jiemodui.com/rss.xml',          # 芥末堆
        # 36氪通用 feed 已移除：泛商业科技快讯污染国际教育主题
        'https://www.insidehighered.com/rss.xml',    # Inside Higher Ed
        'https://www.highereddive.com/feeds/news/',  # Higher Ed Dive
    ],
    'pbsa': [
        'https://www.36kr.com/feed',
    ],
    'uhomes': [
        'https://www.36kr.com/feed',
    ],
}
