from __future__ import annotations

from pathlib import Path

from app.application.daily_job import DailyJobService
from app.entrypoints.run_daily_job import build_service, parse_args


def test_build_service_wires_static_assets_repository_and_renderer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    accounts_file = tmp_path / "accounts.yaml"
    accounts_file.write_text(
        """
accounts:
  - name: main
    wechat_id: wechat-1
    fake_id: fake-1
    query: 读懂世界
    enabled: true
    priority: 10
""".strip(),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, token: str, cookie: str) -> None:
            captured["client"] = (token, cookie)

    class FakeParser:
        def __init__(self) -> None:
            captured["parser"] = True

    class FakeRepository:
        def __init__(self, *, json_dir: Path, image_dir: Path, image_base_url: str) -> None:
            captured["repository"] = (json_dir, image_dir, image_base_url)

    class FakeRenderer:
        def __init__(self, *, template_path: Path) -> None:
            captured["renderer"] = template_path

    module = __import__("app.entrypoints.run_daily_job", fromlist=["dummy"])
    monkeypatch.setattr(module, "WeChatMPClient", FakeClient)
    monkeypatch.setattr(module, "WeChatArticleParser", FakeParser)
    monkeypatch.setattr(module, "StaticAssetsRepositoryImpl", FakeRepository)
    monkeypatch.setattr(module, "PlaywrightImageRenderer", FakeRenderer)
    monkeypatch.setattr(module, "get_image_base_url", lambda: "https://cdn.example.com/static/images/")
    monkeypatch.setenv("WECHAT_TOKEN", "token-123")
    monkeypatch.setenv("WECHAT_COOKIE", "cookie-456")

    args = parse_args(
        [
            "--accounts-file",
            str(accounts_file),
            "--output-dir",
            str(tmp_path / "60s"),
            "--image-dir",
            str(tmp_path / "images"),
            "--template-path",
            str(tmp_path / "template.html"),
        ]
    )
    service = build_service(args)

    assert isinstance(service, DailyJobService)
    assert captured["client"] == ("token-123", "cookie-456")
    assert captured["parser"] is True
    assert captured["repository"] == (
        tmp_path / "60s",
        tmp_path / "images",
        "https://cdn.example.com/static/images/",
    )
    assert captured["renderer"] == tmp_path / "template.html"
