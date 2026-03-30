# Pages Gallery Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Pages preview UI into a gallery-style content preview where the image is the primary exhibit, the date selector becomes a time axis, and JSON becomes secondary curatorial information.

**Architecture:** Keep the Pages app static and data-driven, but replace the current split workspace with a unified gallery canvas. The page will center around a large image stage, use a lighter information layer for metadata and raw JSON, and recast date navigation as a slim timeline.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, pytest contract tests

---

### Task 1: Update page contract tests for the gallery shell

**Files:**
- Modify: `tests/unit/test_render_template_exists.py`

- [ ] **Step 1: Add failing assertions for the gallery shell**

```python
def test_pages_preview_shell_exists() -> None:
    html = Path("pages/index.html").read_text(encoding="utf-8")
    css = Path("pages/styles.css").read_text(encoding="utf-8")

    assert 'class="gallery-shell"' in html
    assert 'class="timeline"' in html
    assert 'id="summary-panel"' in html
    assert "grid-template-areas:" in css
    assert "backdrop-filter:" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: FAIL because the current shell is still the previous workspace layout.

### Task 2: Rebuild the HTML structure into a gallery canvas

**Files:**
- Modify: `pages/index.html`

- [ ] **Step 1: Create the gallery shell and stage**

```html
<main class="gallery-shell">
  <section class="gallery-stage">...</section>
  <aside class="gallery-info">...</aside>
  <aside class="timeline">...</aside>
</main>
```

- [ ] **Step 2: Split info into summary and raw JSON**

```html
<section id="summary-panel" class="summary-panel"></section>
<details class="raw-json-block">
  <summary>原始 JSON</summary>
  <pre id="json-panel"></pre>
</details>
```

- [ ] **Step 3: Run the shell test**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: CSS assertions still fail, HTML assertions pass.

### Task 3: Replace CSS with the gallery console design

**Files:**
- Modify: `pages/styles.css`

- [ ] **Step 1: Build the unified canvas and layout areas**

```css
.gallery-shell {
  display: grid;
  grid-template-areas: "stage info timeline";
}
```

- [ ] **Step 2: Make the image stage the dominant visual region**

```css
.gallery-stage-media img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
```

- [ ] **Step 3: Style the information layer as curatorial annotation**

```css
.gallery-info {
  backdrop-filter: blur(18px);
}
```

- [ ] **Step 4: Make the timeline a slim axis instead of a big control panel**

```css
.timeline .date-link {
  writing-mode: horizontal-tb;
}
```

- [ ] **Step 5: Add responsive mobile layout with image-first priority**

```css
@media (max-width: 768px) {
  .gallery-shell {
    grid-template-areas:
      "stage"
      "info"
      "timeline";
  }
}
```

- [ ] **Step 6: Run the shell test**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: PASS

### Task 4: Update interaction code for summary and timeline

**Files:**
- Modify: `pages/app.js`

- [ ] **Step 1: Render metadata summary**

```javascript
function renderSummary(payload) {
  document.getElementById("summary-panel").innerHTML = ...
}
```

- [ ] **Step 2: Keep raw JSON available in the details block**

```javascript
document.getElementById("json-panel").textContent = JSON.stringify(payload, null, 2);
```

- [ ] **Step 3: Keep original links and date switching intact**

```javascript
document.getElementById("open-image-link").href = item.image_path;
document.getElementById("open-json-link").href = item.json_path;
```

- [ ] **Step 4: Run focused tests**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py tests/unit/test_preview_index.py
```

Expected: PASS

### Task 5: Full verification

**Files:**
- Modify: none required unless failures appear

- [ ] **Step 1: Run full test suite**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest --with pydantic --with httpx --with PyYAML --with tenacity --with selectolax --with playwright python -m pytest -q
```

Expected: PASS
