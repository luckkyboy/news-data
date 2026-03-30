from pathlib import Path

from app.entrypoints import preview_render as module


def test_preview_render_writes_output(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "2026-03-27.json"
    source.write_text(
        Path("static/news/2026-03-27.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    target = tmp_path / "preview.png"

    class FakeRenderer:
        def __init__(self, *, template_path):
            self.template_path = template_path

        def render(self, document):
            return b"png"

    monkeypatch.setattr(module, "PlaywrightImageRenderer", FakeRenderer)

    exit_code = module.main(["--json-path", str(source), "--output", str(target)])

    assert exit_code == 0
    assert target.read_bytes() == b"png"
