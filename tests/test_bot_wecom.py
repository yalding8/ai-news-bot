import unittest
from unittest import mock

import bot_wecom


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


class TestBotWecom(unittest.TestCase):
    def setUp(self):
        # 确保Webhook有值，避免函数提前返回
        bot_wecom.WECOM_WEBHOOK_URLS = ["https://example.com/webhook"]

    def test_parse_active_topics_filters_unknown(self):
        # finance/education 为合法主题；unknown 与空串应被过滤掉，保留原顺序
        raw = "finance,unknown,,education"
        topics = bot_wecom.parse_active_topics(raw)
        self.assertEqual(topics, ["finance", "education"])

    def test_send_wecom_message_success(self):
        fake_resp = FakeResponse(status_code=200, json_data={"errcode": 0})
        with mock.patch.object(bot_wecom.send_session, "post", return_value=fake_resp) as post_mock:
            ok = bot_wecom.send_wecom_message("hello")
        self.assertTrue(ok)
        post_mock.assert_called_once()

    def test_send_wecom_message_http_error(self):
        fake_resp = FakeResponse(status_code=500, text="server error")
        with mock.patch.object(bot_wecom.send_session, "post", return_value=fake_resp):
            ok = bot_wecom.send_wecom_message("hello")
        self.assertFalse(ok)

    def test_send_wecom_message_json_error(self):
        class NoJsonResp(FakeResponse):
            def json(self):
                raise ValueError("not json")

        fake_resp = NoJsonResp(status_code=200, text="bad")
        with mock.patch.object(bot_wecom.send_session, "post", return_value=fake_resp):
            ok = bot_wecom.send_wecom_message("hello")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
