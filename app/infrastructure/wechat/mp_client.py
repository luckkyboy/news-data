from __future__ import annotations

from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.domain.models import CandidateArticle

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 "
    "Safari/604.1 MicroMessenger/8.0.54(0x18003637) NetType/WIFI Language/zh_CN"
)


class WeChatFetchError(RuntimeError):
    pass


class WeChatAuthError(WeChatFetchError):
    pass


@dataclass(slots=True)
class _ResponseEnvelope:
    ret: int
    err_msg: str


class WeChatMPClient:
    def __init__(self, token: str, cookie: str, user_agent: str | None = None) -> None:
        self._token = token
        self._cookie = cookie
        self._user_agent = user_agent or _DEFAULT_USER_AGENT
        self._client = httpx.Client(timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        response = self._request(
            "https://mp.weixin.qq.com/cgi-bin/appmsg",
            params={
                "token": self._token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
                "action": "list_ex",
                "fakeid": fake_id,
                "query": query,
                "type": "9",
                "begin": "0",
                "count": str(count),
                "is_t": "0",
            },
        )
        payload = response.json()
        self._raise_for_base_resp(payload)
        articles = payload.get("app_msg_list") or []
        return [
            CandidateArticle(
                title=str(item.get("title") or ""),
                link=str(item.get("link") or ""),
                cover=str(item.get("cover") or ""),
                create_ts=int(item.get("create_time", 0) or 0),
                update_ts=int(item.get("update_time", 0) or 0),
            )
            for item in articles
        ]

    def fetch_article_html(self, link: str) -> str:
        normalized_link = link.replace("http://", "https://", 1)
        response = self._request(
            normalized_link,
            referer=normalized_link,
            include_x_requested_with=False,
            accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        return response.text

    def _request(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        referer: str = "https://mp.weixin.qq.com/",
        include_x_requested_with: bool = True,
        accept: str | None = None,
    ) -> httpx.Response:
        return self._request_with_retry(
            url,
            params=params,
            referer=referer,
            include_x_requested_with=include_x_requested_with,
            accept=accept,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    def _request_with_retry(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        referer: str = "https://mp.weixin.qq.com/",
        include_x_requested_with: bool = True,
        accept: str | None = None,
    ) -> httpx.Response:
        response = self._client.get(
            url,
            params=params,
            headers=self._headers(
                referer,
                include_x_requested_with=include_x_requested_with,
                accept=accept,
            ),
            follow_redirects=True,
        )
        if response.status_code >= 400:
            raise WeChatFetchError(f"http {response.status_code} for {url}")
        return response

    def _headers(
        self,
        referer: str,
        *,
        include_x_requested_with: bool = True,
        accept: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "Cookie": self._cookie,
            "Referer": referer,
            "User-Agent": self._user_agent,
        }
        if include_x_requested_with:
            headers["X-Requested-With"] = "XMLHttpRequest"
        if accept:
            headers["Accept"] = accept
        return headers

    def _raise_for_base_resp(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise WeChatFetchError("invalid response payload")

        base_resp = payload.get("base_resp") or {}
        if not isinstance(base_resp, dict):
            raise WeChatFetchError("invalid response payload")

        envelope = _ResponseEnvelope(
            ret=int(base_resp.get("ret", 0) or 0),
            err_msg=str(base_resp.get("err_msg", "") or base_resp.get("msg", "") or ""),
        )
        if envelope.ret == 0:
            return

        message = envelope.err_msg or f"wechat fetch failed: ret={envelope.ret}"
        if "invalid session" in message.lower():
            raise WeChatAuthError(message)
        raise WeChatFetchError(message)
