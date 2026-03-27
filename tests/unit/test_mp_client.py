from __future__ import annotations

import httpx
import pytest

from app.domain.models import CandidateArticle
from app.infrastructure.wechat.mp_client import (
    WeChatAuthError,
    WeChatFetchError,
    WeChatMPClient,
)


def test_search_articles_returns_candidate_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    client = WeChatMPClient(token="token", cookie="cookie", user_agent="agent")
    captured: dict[str, object] = {}

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        captured["timeout"] = timeout
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={
                "base_resp": {"ret": 0, "err_msg": "ok"},
                "app_msg_list": [
                    {
                        "title": "3月27日 读懂世界",
                        "link": "https://mp.weixin.qq.com/s/example",
                        "cover": "https://example.com/cover.png",
                        "create_time": 1774564200,
                        "update_time": 1774564500,
                    }
                ],
            },
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    articles = client.search_articles("fake-id", "读懂世界", count=6)

    assert articles == [
        CandidateArticle(
            title="3月27日 读懂世界",
            link="https://mp.weixin.qq.com/s/example",
            cover="https://example.com/cover.png",
            create_ts=1774564200,
            update_ts=1774564500,
        )
    ]
    assert captured["url"] == "https://mp.weixin.qq.com/cgi-bin/appmsg"
    assert captured["params"] == {
        "token": "token",
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "action": "list_ex",
        "fakeid": "fake-id",
        "query": "读懂世界",
        "type": "9",
        "begin": "0",
        "count": "6",
        "is_t": "0",
    }
    assert captured["headers"] == {
        "Cookie": "cookie",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://mp.weixin.qq.com/",
        "User-Agent": "agent",
    }


def test_search_articles_raises_auth_error_on_invalid_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = WeChatMPClient(token="token", cookie="cookie")

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"base_resp": {"ret": 200003, "err_msg": "invalid session"}},
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(WeChatAuthError, match="invalid session"):
        client.search_articles("fake-id", "读懂世界")


def test_search_articles_raises_fetch_error_on_nonzero_ret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = WeChatMPClient(token="token", cookie="cookie")

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"base_resp": {"ret": 1, "err_msg": "boom"}},
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(WeChatFetchError, match="boom"):
        client.search_articles("fake-id", "读懂世界")


def test_fetch_article_html_returns_html_text(monkeypatch: pytest.MonkeyPatch) -> None:
    client = WeChatMPClient(token="token", cookie="cookie")

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(200, text="<html><body>hello</body></html>", request=request)

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    html = client.fetch_article_html("https://mp.weixin.qq.com/s/example")

    assert html == "<html><body>hello</body></html>"


def test_fetch_article_html_follows_redirects_and_normalizes_http_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = WeChatMPClient(token="token", cookie="cookie")
    captured: dict[str, object] = {}

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        captured["url"] = url
        captured["headers"] = headers
        captured["follow_redirects"] = follow_redirects
        request = httpx.Request("GET", url)
        return httpx.Response(200, text="<html><body>ok</body></html>", request=request)

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    html = client.fetch_article_html("http://mp.weixin.qq.com/s/example")

    assert html == "<html><body>ok</body></html>"
    assert captured["url"] == "https://mp.weixin.qq.com/s/example"
    assert captured["follow_redirects"] is True
    assert captured["headers"] == {
        "Cookie": "cookie",
        "Referer": "https://mp.weixin.qq.com/s/example",
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 "
            "Safari/604.1 MicroMessenger/8.0.54(0x18003637) NetType/WIFI Language/zh_CN"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
