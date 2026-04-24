from openai import OpenAI
from config import DEEPSEEK_API_KEY, LLM_BASE_URL, LLM_MODEL, NEWS_TOPICS, get_logger

logger = get_logger(__name__)

class AISummarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL

    def summarize_news(self, topic_key: str, news_list: list, news_text: str) -> str:
        """
        使用AI总结新闻 (增强版 - 带内容验证)

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
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""请严格基于以下{topic_info['name']}的真实新闻生成摘要（共{len(news_list)}条）：

{news_text}

⚠️ 重要要求：
1. 只总结上述提供的真实新闻，不要添加其他内容
2. 只选择最重要的3条新闻进行总结
3. 每条新闻用2-3句话详细概括，包含关键数据和具体信息
4. 用emoji增强可读性（每条新闻前加相关emoji）
5. 如果新闻是英文的，请翻译为中文
6. 标题必须与列表中的原始标题完全一致（逐字复制）
7. 总字数控制在500字以内

输出格式（必须严格一致）：
1. 📰 标题：<原始标题>
   摘要：<2-3句话>
2. 📰 标题：<原始标题>
   摘要：<2-3句话>
3. 📰 标题：<原始标题>
   摘要：<2-3句话>

请开始总结（选择3条最重要的新闻）："""
                }],
                max_tokens=800,
                temperature=0.3
            )

            summary = response.choices[0].message.content

            # ✅ 新增: 内容验证
            if not self._validate_summary(summary, news_list, min_title_matches=2):
                logger.error("❌ AI总结验证失败，使用降级策略")
                return self._fallback_summary(news_list, topic_info['name'])

            logger.info(f"✅ AI总结验证通过 (长度: {len(summary)} 字符)")
            return summary

        except Exception as e:
            logger.error(f"❌ AI总结失败: {e}")
            return self._fallback_summary(news_list, topic_info['name'])

    def summarize_daily_news(self, news_list: list, news_text: str) -> str:
        """
        生成每日新闻摘要（不分主题，统一总结，增强版 - 带内容验证）

        Args:
            news_list: 原始新闻列表
            news_text: 格式化后的新闻文本

        Returns:
            str: AI生成的总结
        """
        logger.info(f"  └─ AI正在总结 {len(news_list)} 条国际教育新闻...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""请严格基于以下国际教育行业新闻生成摘要（共{len(news_list)}条）：

{news_text}

⚠️ 重要要求：
1. 只总结上述提供的真实新闻，不要添加其他内容
2. 选择最重要的5-6条新闻进行总结
3. 每条新闻用2-3句话详细概括，包含关键数据、具体信息
4. 用emoji增强可读性（每条新闻前加相关emoji）
5. 如果新闻是英文的，请翻译为中文
6. 标题必须与列表中的原始标题完全一致（逐字复制）
7. 不要输出任何解释、免责声明、注释、括号说明或额外段落
8. 按重要性排序
9. 总字数控制在600字以内

输出格式（必须严格一致，只允许下列条目）：
1. 📰 标题：<原始标题>
   摘要：<2-3句话>
2. 📰 标题：<原始标题>
   摘要：<2-3句话>
...

请开始总结："""
                }],
                max_tokens=1000,
                temperature=0.3
            )

            summary = response.choices[0].message.content

            # ✅ 新增: 内容验证
            required_title_matches = min(3, len(news_list))
            if not self._validate_summary(
                summary,
                news_list,
                min_length=120,
                min_title_matches=required_title_matches
            ):
                logger.error("❌ 每日新闻总结验证失败，使用降级策略")
                return self._fallback_summary(news_list, "国际教育新闻")

            logger.info(f"✅ 每日新闻总结验证通过 (长度: {len(summary)} 字符)")
            return summary

        except Exception as e:
            logger.error(f"❌ AI总结失败: {e}")
            return self._fallback_summary(news_list, "国际教育新闻")

    def _validate_summary(
        self,
        summary: str,
        news_list: list,
        min_length: int = 50,
        min_title_matches: int = 0
    ) -> bool:
        """
        验证 AI 总结质量

        Args:
            summary: AI 生成的总结
            news_list: 原始新闻列表
            min_length: 最小字符数

        Returns:
            bool: 验证是否通过
        """
        # 1. 检查是否为空或过短
        if not summary or len(summary.strip()) < min_length:
            logger.warning(f"⚠️ 总结过短: {len(summary) if summary else 0} 字符 (最低要求: {min_length})")
            return False

        # 2. 检查是否包含明显错误提示或多余说明
        import re
        error_patterns = [
            r'^⚠️',
            r'AI总结失败',
            r'AI 总结失败',
            r'总结失败',
            r'服务暂时不可用',
            r'无法连接',
            r'请求失败',
            r'接口错误',
            r'API(?:调用)?失败',
            r'error\s*:',
            r'failed\s*:',
            r'exception',
            r'^\s*[（(]?\s*注[:：]',
            r'免责声明',
            r'仅从提供的',
            r'根据您的要求'
        ]
        if any(re.search(pattern, summary, re.IGNORECASE | re.MULTILINE) for pattern in error_patterns):
            logger.warning("⚠️ 总结包含错误提示")
            return False

        # 3. 检查是否包含足够的标题匹配（避免泛化总结）
        if min_title_matches > 0:
            titles = [n.get('title', '') for n in news_list if n.get('title')]
            title_matches = sum(1 for t in titles if t and t in summary)
            if title_matches < min_title_matches:
                logger.warning(
                    f"⚠️ 总结标题匹配不足 (匹配标题: {title_matches}/{min_title_matches})"
                )
                return False

        # 4. 检查是否与原文相关 (使用简单的关键词匹配)
        # 提取原文标题中的关键词
        from collections import Counter
        import re

        # 提取所有新闻标题中的有效词汇
        all_words = []
        for news in news_list[:5]:  # 只检查前5条
            title = news.get('title', '')
            # 提取中英文词汇 (长度>=2的词)
            words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', title)
            all_words.extend(words)

        if not all_words:
            # 如果无法提取关键词，跳过此检查
            return True

        # 统计高频词 (前10个)
        word_freq = Counter(all_words)
        top_keywords = [word for word, _ in word_freq.most_common(10)]

        # 检查总结中是否包含至少2个关键词
        matches = sum(1 for kw in top_keywords if kw.lower() in summary.lower())
        if matches < 2:
            logger.warning(f"⚠️ 总结与原文相关度过低 (匹配关键词: {matches}/10)")
            # 不强制返回False，因为可能是翻译问题
            # return False

        logger.debug(f"✅ 总结验证通过: 长度={len(summary)}, 关键词匹配={matches}")
        return True

    def _fallback_summary(self, news_list: list, topic_name: str = "新闻") -> str:
        """
        降级策略: 简单格式化新闻列表

        Args:
            news_list: 原始新闻列表
            topic_name: 主题名称

        Returns:
            str: 格式化的新闻列表
        """
        if not news_list:
            return f"⚠️ 今日暂无{topic_name}"

        lines = [f"📰 **今日{topic_name}要闻**\n"]

        for i, news in enumerate(news_list[:5], 1):
            title = news.get('title', '无标题')
            description = news.get('description', '')

            # 格式化每条新闻
            lines.append(f"{i}. **{title}**")

            if description and len(description) > 20:
                # 截取描述前80字符
                desc_preview = description[:80] + '...' if len(description) > 80 else description
                lines.append(f"   {desc_preview}")

            lines.append("")  # 空行

        lines.append("💡 *AI 总结服务暂时不可用，以上为原始新闻摘要*")

        return "\n".join(lines)
