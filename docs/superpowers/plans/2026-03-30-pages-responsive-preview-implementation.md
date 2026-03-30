# Pages Responsive Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Pages preview fully responsive so desktop keeps image and JSON visible together while mobile prioritizes the image in the first screen and keeps JSON in a scrollable lower panel.

**Architecture:** Keep the Pages app static and data-driven, but rebuild the layout into breakpoint-specific workspace modes. Desktop remains split-view, tablet compresses controls and content, and mobile becomes a stacked layout with a fixed-height image stage and a separate scrollable JSON panel.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, pytest contract tests

---

### Task 1: Add responsive layout contract tests

**Files:**
- Modify: `tests/unit/test_render_template_exists.py`

- [ ] **Step 1: Add failing assertions for responsive shell behavior**

```python
def test_pages_preview_shell_exists() -> None:
    html = Path("pages/index.html").read_text(encoding="utf-8")
    css = Path("pages/styles.css").read_text(encoding="utf-8")

    assert 'class="workspace"' in html
    assert 'class="stage-meta"' in html
    assert "height: 100vh;" in css
    assert "object-fit: contain;" in css
    assert "@media (max-width: 768px)" in css
    assert "grid-template-rows: auto minmax(280px, 52vh) minmax(220px, 1fr);" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: FAIL because the current layout is not yet responsive in the required way.

### Task 2: Restructure the page shell for responsive states

**Files:**
- Modify: `pages/index.html`

- [ ] **Step 1: Add a compact metadata block for mobile and tablet**

```html
<div class="stage-meta">
  <p class="eyebrow">正式产物</p>
  <h2 id="stage-date-label">-</h2>
</div>
```

- [ ] **Step 2: Keep navigation and original-resource links grouped for narrow screens**

```html
<div class="stage-actions">
  <button id="prev-button" type="button">上一天</button>
  <button id="next-button" type="button">下一天</button>
  <a id="open-image-link" ...>原图</a>
  <a id="open-json-link" ...>原始 JSON</a>
</div>
```

- [ ] **Step 3: Run the contract test to confirm HTML shape**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: CSS assertions still fail, HTML assertions pass.

### Task 3: Implement responsive CSS breakpoints

**Files:**
- Modify: `pages/styles.css`

- [ ] **Step 1: Lock desktop to a split workspace**

```css
.workspace {
  height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 360px;
}
```

- [ ] **Step 2: Add tablet layout that keeps image and JSON visible**

```css
@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 180px minmax(0, 1fr) 300px;
  }
}
```

- [ ] **Step 3: Add mobile layout that prioritizes the image in the first screen**

```css
@media (max-width: 768px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(280px, 52vh) minmax(220px, 1fr);
  }
}
```

- [ ] **Step 4: Ensure image and JSON panels behave correctly**

```css
.stage-frame,
.inspector-body {
  min-height: 0;
}

#preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
```

- [ ] **Step 5: Run the contract test**

Run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-project --with pytest python -m pytest -q tests/unit/test_render_template_exists.py::test_pages_preview_shell_exists
```

Expected: PASS

### Task 4: Verify interaction code still works with the new shell

**Files:**
- Modify: `pages/app.js` (only if selectors or labels need updates)

- [ ] **Step 1: Keep date label, resource links, and navigation selectors aligned**

```javascript
document.getElementById("stage-date-label").textContent = date;
document.getElementById("open-image-link").href = item.image_path;
document.getElementById("open-json-link").href = item.json_path;
```

- [ ] **Step 2: Keep empty/error handling intact**

```javascript
renderError("没有可预览的数据");
```

- [ ] **Step 3: Run focused tests**

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
