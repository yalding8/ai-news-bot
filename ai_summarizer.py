from openai import OpenAI
from config import DEEPSEEK_API_KEY, NEWS_TOPICS, get_logger

logger = get_logger(__name__)

class AISummarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

    def summarize_news(self, topic_key: str, news_list: list, news_text: str) -> str:
        """
        使用AI总结新闻
        
        Args:
            topic_key: 主题键值
            news_list: 原始新闻列表
            news_text: 格式化后的新闻文本
            
        Returns:
            str: AI生成的总结
        """
        topic_info = NEWS_TOPICS.get(topic_key)
        if not topic_info:
            return "未知主题"

        logger.info(f"  └─ AI正在总结{topic_info['name']}新闻...")
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""请总结以下{topic_info['name']}的真实新闻（共{len(news_list)}条）：

{news_text}

⚠️ 重要要求：
1. 只总结上述提供的真实新闻，不要添加其他内容
2. 如果新闻超过5条，请挑选3-5条最重要、最有价值的新闻进行重点总结
3. 每条新闻用2-3句话概括关键信息和亮点
4. 保持新闻来源信息（在括号中注明）
5. 使用简洁的文本格式
6. 用emoji增强可读性（每条新闻前加相关emoji）
7. 按重要性排序，最重要的新闻放在最前面

请开始总结（重点提炼）："""
                }],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ AI总结失败: {e}")
            return f"⚠️ AI总结失败: {str(e)}"
