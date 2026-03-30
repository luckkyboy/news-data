# GitHub Pages Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub Pages preview site that browses existing JSON and PNG artifacts, plus a local preview command that renders images from existing JSON data.

**Architecture:** Keep a single rendering source of truth in Python. GitHub Pages serves only static assets and metadata generated from `static/news` and `static/images`; it does not reimplement template rendering in JavaScript. A small Python index generator produces `pages/data/index.json`, while a separate local entrypoint re-renders one JSON file with the existing Playwright renderer.

**Tech Stack:** Python, Jinja2/Playwright renderer, static HTML/CSS/JavaScript, GitHub Actions Pages deployment, pytest

---

### Task 1: Add failing tests for preview index generation and local preview command

**Files:**
- Create: `tests/unit/test_preview_index.py`
- Create: `tests/integration/test_preview_render_entrypoint.py`
- Modify: `tests/unit/test_workflow_contract.py`

- [ ] **Step 1: Write the failing test for preview index generation**

```python
from pathlib import Path

from app.entrypoints.preview_page_index import build_preview_index


def test_build_preview_index_returns_sorted_items(tmp_path: Path) -> None:
    news_dir = tmp_path / "news"
    images_dir = tmp_path / "images"
    news_dir.mkdir()
    images_dir.mkdir()
    (news_dir / "2026-03-27.json").write_text("{}", encoding="utf-8")
    (news_dir / "2026-03-30.json").write_text("{}", encoding="utf-8")
    (images_dir / "2026-03-27.png").write_bytes(b"png")
    (images_dir / "2026-03-30.png").write_bytes(b"png")

    payload = build_preview_index(news_dir=news_dir, image_dir=images_dir)

    assert payload["latest"] == "2026-03-30"
    assert payload["items"] == [
        {
            "date": "2026-03-27",
            "json_path": "../static/news/2026-03-27.json",
            "image_path": "../static/images/2026-03-27.png",
        },
        {
            "date": "2026-03-30",
            "json_path": "../static/news/2026-03-30.json",
            "image_path": "../static/images/2026-03-30.png",
        },
    ]
```

- [ ] **Step 2: Write the failing integration test for local preview rendering**

```python
from pathlib import Path

from app.entrypoints.preview_render import main


def test_preview_render_writes_output(tmp_path: Path) -> None:
    source = tmp_path / "2026-03-27.json"
    source.write_text(
        Path("static/news/2026-03-27.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    target = tmp_path / "preview.png"

    exit_code = main(["--json-path", str(source), "--output", str(target)])

    assert exit_code == 0
    assert target.exists()
```

- [ ] **Step 3: Extend workflow contract test with Pages workflow assertions**

```python
def test_pages_preview_workflow_exists() -> None:
    content = Path(".github/workflows/pages-preview.yml").read_text(encoding="utf-8")

    assert "actions/configure-pages" in content
    assert "actions/deploy-pages" in content
    assert "python -m app.entrypoints.preview_page_index" in content
```

- [ ] **Step 4: Run tests to verify they fail**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest --with pydantic --with httpx --with PyYAML --with tenacity --with selectolax --with playwright python -m pytest -q tests/unit/test_preview_index.py tests/integration/test_preview_render_entrypoint.py tests/unit/test_workflow_contract.py
```

Expected: FAIL because preview entrypoints and workflow do not exist yet.

### Task 2: Implement preview index generator

**Files:**
- Create: `app/entrypoints/preview_page_index.py`
- Test: `tests/unit/test_preview_index.py`

- [ ] **Step 1: Write minimal preview index implementation**

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_preview_index(*, news_dir: Path, image_dir: Path) -> dict[str, object]:
    items: list[dict[str, str]] = []
    for json_path in sorted(news_dir.glob("*.json")):
        date = json_path.stem
        image_path = image_dir / f"{date}.png"
        if not image_path.exists():
            continue
        items.append(
            {
                "date": date,
                "json_path": f"../static/news/{date}.json",
                "image_path": f"../static/images/{date}.png",
            }
        )
    latest = items[-1]["date"] if items else ""
    return {"latest": latest, "items": items}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--news-dir", type=Path, default=Path("static/news"))
    parser.add_argument("--image-dir", type=Path, default=Path("static/images"))
    parser.add_argument("--output", type=Path, default=Path("pages/data/index.json"))
    args = parser.parse_args(argv)

    payload = build_preview_index(news_dir=args.news_dir, image_dir=args.image_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run test to verify it passes**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_preview_index.py
```

Expected: PASS

### Task 3: Implement local preview render command

**Files:**
- Create: `app/entrypoints/preview_render.py`
- Modify: `tests/integration/test_preview_render_entrypoint.py`

- [ ] **Step 1: Write minimal local preview command**

```python
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.render import TEMPLATE_PATH
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one preview image from a JSON file")
    parser.add_argument("--json-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--template-path", type=Path, default=TEMPLATE_PATH)
    args = parser.parse_args(argv)

    try:
        document = DailyNewsDocument.model_validate_json(args.json_path.read_text(encoding="utf-8"))
        renderer = PlaywrightImageRenderer(template_path=args.template_path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(renderer.render(document))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("preview render failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Make the integration test safe by monkeypatching renderer**

```python
class FakeRenderer:
    def __init__(self, *, template_path):
        self.template_path = template_path

    def render(self, document):
        return b"png"
```

- [ ] **Step 3: Run test to verify it passes**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest --with pydantic --with playwright python -m pytest -q tests/integration/test_preview_render_entrypoint.py
```

Expected: PASS

### Task 4: Build the Pages static frontend

**Files:**
- Create: `pages/index.html`
- Create: `pages/app.js`
- Create: `pages/styles.css`
- Modify: `tests/unit/test_render_template_exists.py`

- [ ] **Step 1: Add a failing contract test for the Pages app shell**

```python
def test_pages_preview_shell_exists() -> None:
    html = Path("pages/index.html").read_text(encoding="utf-8")
    js = Path("pages/app.js").read_text(encoding="utf-8")

    assert 'id="date-list"' in html
    assert 'id="preview-image"' in html
    assert 'id="json-panel"' in html
    assert "new URLSearchParams" in js
```

- [ ] **Step 2: Create the static frontend files**

```html
<main class="layout">
  <aside id="date-list"></aside>
  <section class="preview-pane">
    <img id="preview-image" alt="预览图片" />
  </section>
  <section class="json-pane">
    <pre id="json-panel"></pre>
  </section>
</main>
```

```javascript
async function loadIndex() {
  const response = await fetch("./data/index.json");
  return response.json();
}
```

- [ ] **Step 3: Implement date switching and JSON/image rendering**

```javascript
function pickInitialDate(index) {
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("date");
  return index.items.find((item) => item.date === requested)?.date ?? index.latest;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py tests/unit/test_workflow_contract.py
```

Expected: PASS for the new Pages shell assertions after files are added.

### Task 5: Add GitHub Pages deployment workflow

**Files:**
- Create: `.github/workflows/pages-preview.yml`
- Test: `tests/unit/test_workflow_contract.py`

- [ ] **Step 1: Add workflow that builds index and deploys Pages**

```yaml
name: Preview Pages

on:
  push:
    branches: [main]
    paths:
      - "pages/**"
      - "static/news/**"
      - "static/images/**"
      - "app/entrypoints/preview_page_index.py"
      - ".github/workflows/pages-preview.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install .
      - run: python -m app.entrypoints.preview_page_index
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: .
      - uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Run workflow contract tests**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest --with pydantic --with httpx --with PyYAML --with tenacity --with selectolax --with playwright python -m pytest -q tests/unit/test_workflow_contract.py
```

Expected: PASS

### Task 6: Final verification and docs

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-03-30-github-pages-preview-design.md` (only if needed for consistency)

- [ ] **Step 1: Document the new preview tools**

```markdown
## Pages Preview

- GitHub Pages shows the formal PNG plus source JSON
- Local preview command:
  `python -m app.entrypoints.preview_render --json-path static/news/2026-03-30.json --output /tmp/preview.png`
```

- [ ] **Step 2: Run full test suite**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest --with pydantic --with httpx --with PyYAML --with tenacity --with selectolax --with playwright python -m pytest -q
```

Expected: PASS with the full repository suite green.

- [ ] **Step 3: Commit**

```bash
git add pages .github/workflows/pages-preview.yml app/entrypoints/preview_page_index.py app/entrypoints/preview_render.py tests README.md
git commit -m "feat: add github pages preview"
```
