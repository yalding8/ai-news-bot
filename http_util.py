"""共享 HTTP 会话构建（AUDIT 2026-07-05 行动项 #8）。

news_fetcher（抓取）与 bot_wecom（企微发送）此前各自内联一份完全相同的
Session + Retry 装配，参数漂移风险；收口到这里。
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def make_retry_session(allowed_methods=frozenset({"GET", "POST"})) -> requests.Session:
    """带指数退避重试的 requests.Session（429/5xx 重试 3 次）。"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=set(allowed_methods),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
