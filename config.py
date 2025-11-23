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
WECOM_WEBHOOK_URL = os.getenv('WECOM_WEBHOOK_URL')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
TIANAPI_KEY = os.getenv('TIANAPI_KEY')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')



# Active Topics
ACTIVE_TOPICS_ENV = os.getenv('ACTIVE_TOPICS', 'ai,education')

# News Topics Configuration
NEWS_TOPICS = {
    'ai': {'name': 'AI科技', 'emoji': '🤖', 'desc': 'AI领域最新动态', 'color': '#4A90E2'},
    'finance': {'name': '财经新闻', 'emoji': '💰', 'desc': '金融市场和经济动态', 'color': '#F5A623'},
    'startup': {'name': '创业投资', 'emoji': '🚀', 'desc': '创业公司和投资动态', 'color': '#7ED321'},
    'education': {'name': '国际教育', 'emoji': '🎓', 'desc': '国际教育行业动态', 'color': '#BD10E0'},
    'pbsa': {'name': '学生公寓', 'emoji': '🏠', 'desc': 'PBSA学生公寓行业动态', 'color': '#50E3C2'},
    'uhomes': {'name': '异乡好居', 'emoji': '🏡', 'desc': '异乡好居企业动态', 'color': '#FF6B6B'}
}

# Topic Keywords (Moved from news_fetcher.py to keep config together)
TOPIC_KEYWORDS = {
    'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'ChatGPT', 'DeepSeek', '大模型', 'GPT', 'LLM', '神经网络', '自然语言处理', 'NLP', '计算机视觉', 'OpenAI', 'Google AI', '百度AI', '腾讯AI', '阿里AI'],
    'finance': ['财经', '金融', '股市', '经济', '投资'],
    'startup': ['创业', '融资', '风投', 'VC', '投资'],
    'education': ['教育', '留学', '国际教育', '教育科技', '在线教育', '高等教育', '职业教育', '教育投资', 'EdTech', 'MOOC', '教育政策'],
    'pbsa': ['学生公寓', 'PBSA', '租房', '宿舍'],
    'uhomes': ['异乡好居', 'Uhomes', '留学生公寓']
}
