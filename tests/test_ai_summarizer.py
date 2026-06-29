import json
import unittest
from datetime import datetime
from unittest import mock

import ai_summarizer


def _fake_completion(json_payload: str):
    msg = mock.Mock()
    msg.content = json_payload
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


VALID = json.dumps({"items": [
    {"title_zh": "标题", "title_en": "Title", "summary": "摘要", "punch": "点睛", "source": "Src"}
    for _ in range(5)
]})

NEWS = [{"title": f"T{i}", "url": f"https://e.com/{i}", "source": "Src"} for i in range(5)]


class TestSummarizeForPosterPrompt(unittest.TestCase):
    def _capture_prompt(self, today):
        s = ai_summarizer.AISummarizer()
        s.client = mock.Mock()
        s.client.chat.completions.create.return_value = _fake_completion(VALID)
        s.summarize_for_poster(NEWS, "news text", today=today)
        call = s.client.chat.completions.create.call_args
        return call.kwargs["messages"][0]["content"]

    def test_prompt_includes_resolved_current_date(self):
        prompt = self._capture_prompt(datetime(2026, 6, 29))
        self.assertIn("2026-06-29", prompt)

    def test_prompt_instructs_relative_date_resolution(self):
        # 必须告诉模型把"今年/明年"等相对时间按今天换算
        prompt = self._capture_prompt(datetime(2026, 6, 29))
        self.assertIn("今年", prompt)

    def test_prompt_has_anti_fabrication_guard(self):
        # 必须禁止编造原文没有的具体日期/数字
        prompt = self._capture_prompt(datetime(2026, 6, 29))
        self.assertIn("不得", prompt)


if __name__ == "__main__":
    unittest.main()
