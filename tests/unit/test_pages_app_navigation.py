import json
import subprocess
from pathlib import Path


def test_next_button_disables_at_latest_available_date() -> None:
    app_js = Path("pages/app.js").read_text(encoding="utf-8").replace(
        'bootstrap().catch((error) => {\n  document.getElementById("json-panel").textContent = String(error);\n});',
        'globalThis.__bootstrapPromise = bootstrap().catch((error) => {\n  document.getElementById("json-panel").textContent = String(error);\n});',
    )
    harness = f"""
import vm from "node:vm";

const source = {json.dumps(app_js)} + "\\n;globalThis.__appTest = {{ state, renderDate, syncNavigationButtons }};";
const fetchLog = [];
const responses = new Map([
  [
    "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/news/2026-03-31.json",
    {{
      ok: true,
      json: async () => ({{
        date: "2026-03-31",
        image: "https://cdn.example.com/news/2026-03-31.png",
      }}),
    }},
  ],
]);

const elements = new Map();
function makeElement(id) {{
  return {{
    id,
    disabled: false,
    textContent: "",
    href: "",
    src: "",
    listeners: {{}},
    addEventListener(type, handler) {{
      this.listeners[type] = handler;
    }},
  }};
}}

[
  "prev-button",
  "next-button",
  "json-panel",
  "stage-date-label",
  "preview-image",
  "open-image-link",
  "open-json-link",
].forEach((id) => elements.set(id, makeElement(id)));

const RealDate = Date;
class FakeDate extends RealDate {{
  constructor(...args) {{
    if (args.length === 0) {{
      super("2026-04-01T08:00:00Z");
      return;
    }}
    super(...args);
  }}
  static now() {{
    return new RealDate("2026-04-01T08:00:00Z").getTime();
  }}
}}

const context = {{
  console,
  URL,
  URLSearchParams,
  Date: FakeDate,
  fetch: async (path) => {{
    fetchLog.push(path);
    const response = responses.get(path);
    if (!response) {{
      return {{ ok: false, json: async () => null }};
    }}
    return response;
  }},
  window: {{
    location: {{
      href: "https://luckkyboy.github.io/news-data/?date=2026-03-31",
      search: "?date=2026-03-31",
    }},
    history: {{
      replaceState(_state, _title, url) {{
        context.window.location.href = String(url);
        context.window.location.search = new URL(String(url)).search;
      }},
    }},
  }},
  document: {{
    body: {{ dataset: {{ theme: "cool" }} }},
    getElementById(id) {{
      const element = elements.get(id);
      if (!element) {{
        throw new Error(`missing element ${{id}}`);
      }}
      return element;
    }},
  }},
}};

vm.runInNewContext(source, context);
await context.__bootstrapPromise;

const result = {{
  currentDate: context.__appTest.state.currentDate,
  nextDisabled: elements.get("next-button").disabled,
  previewImageSrc: elements.get("preview-image").src,
  openImageHref: elements.get("open-image-link").href,
  openJsonHref: elements.get("open-json-link").href,
  fetchLog,
}};

if (result.currentDate !== "2026-03-31") {{
  throw new Error(`unexpected currentDate: ${{result.currentDate}}`);
}}
if (result.nextDisabled !== true) {{
  throw new Error(`expected next button disabled, got ${{result.nextDisabled}} with fetches ${{JSON.stringify(result.fetchLog)}}`);
}}
if (result.previewImageSrc !== "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/images/2026-03-31.png") {{
  throw new Error(`expected preview image from date-based CDN path, got ${{result.previewImageSrc}}`);
}}
if (result.openImageHref !== "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/images/2026-03-31.png") {{
  throw new Error(`expected open image href from date-based CDN path, got ${{result.openImageHref}}`);
}}
if (result.openJsonHref !== "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/news/2026-03-31.json") {{
  throw new Error(`expected open json href to use CDN, got ${{result.openJsonHref}}`);
}}
if (result.fetchLog.length !== 2) {{
  throw new Error(`expected two fetches for today backtrack, got ${{result.fetchLog.length}} with fetches ${{JSON.stringify(result.fetchLog)}}`);
}}
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", harness],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_pages_app_uses_beijing_timezone_for_current_date() -> None:
    app_js = Path("pages/app.js").read_text(encoding="utf-8")

    assert (
        'const JSON_CDN_BASE = "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/news"'
        in app_js
    )
    assert (
        'const IMAGE_CDN_BASE = "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/images"'
        in app_js
    )
    assert 'timeZone: "Asia/Shanghai"' in app_js
    assert "function todayInBeijing()" in app_js
    assert 'return params.get("date") || todayInBeijing();' in app_js
