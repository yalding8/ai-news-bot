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
2. 只选择最重要的3条新闻进行总结
3. 每条新闻用2-3句话详细概括，包含关键数据和具体信息
4. 用emoji增强可读性（每条新闻前加相关emoji）
5. 如果新闻是英文的，请翻译为中文
6. 总字数控制在500字以内

请开始总结（选择3条最重要的新闻）："""
                }],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ AI总结失败: {e}")
            return f"⚠️ AI总结失败: {str(e)}"

    def summarize_daily_news(self, news_list: list, news_text: str) -> str:
        """
        生成每日新闻摘要（不分主题，统一总结）

        Args:
            news_list: 原始新闻列表
            news_text: 格式化后的新闻文本

        Returns:
            str: AI生成的总结
        """
        logger.info(f"  └─ AI正在总结 {len(news_list)} 条国际教育新闻...")

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""请总结以下国际教育行业新闻（共{len(news_list)}条）：

{news_text}

⚠️ 重要要求：
1. 只总结上述提供的真实新闻，不要添加其他内容
2. 选择最重要的5-6条新闻进行总结
3. 每条新闻用2-3句话详细概括，包含关键数据、具体信息
4. 用emoji增强可读性（每条新闻前加相关emoji）
5. 如果新闻是英文的，请翻译为中文
6. 按重要性排序
7. 总字数控制在600字以内

请开始总结："""
                }],
                max_tokens=1000,
                temperature=0.3
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ AI总结失败: {e}")
            return f"⚠️ AI总结失败: {str(e)}"
