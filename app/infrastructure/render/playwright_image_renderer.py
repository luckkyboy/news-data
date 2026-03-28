from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image
from playwright.sync_api import sync_playwright

from app.domain.models import DailyNewsDocument


class PlaywrightImageRenderer:
    _FONT_FILE = (
        Path(__file__).resolve().parent
        / "assets"
        / "fonts"
        / "LXGWWenKaiMono-Medium.ttf"
    )
    _PNG_COLORS = 256

    def __init__(
        self,
        *,
        template_path: Path | str,
        viewport_width: int = 1200,
        viewport_height: int = 1800,
        device_scale_factor: float = 1.0,
    ) -> None:
        self._template_path = Path(template_path)
        self._viewport_width = viewport_width
        self._viewport_height = viewport_height
        self._device_scale_factor = device_scale_factor

    def build_html(self, document: DailyNewsDocument) -> str:
        template = self._template_path.read_text(encoding="utf-8")
        payload = json.dumps(document.model_dump(), ensure_ascii=False)
        return (
            template.replace("__FONT_FACE__", self._font_face_css())
            .replace("__NEWS_DATA__", payload)
        )

    @classmethod
    def _font_face_css(cls) -> str:
        if not cls._FONT_FILE.exists():
            return ""
        return (
            "@font-face {\n"
            "  font-family: 'LXGW WenKai Mono';\n"
            f"  src: url('{cls._FONT_FILE.as_uri()}') format('truetype');\n"
            "  font-weight: 500;\n"
            "  font-style: normal;\n"
            "  font-display: swap;\n"
            "}\n"
        )

    def render(self, document: DailyNewsDocument) -> bytes:
        html = self.build_html(document)
        temp_path = self._write_temp_html(html)
        try:
            image = self._render_from_file(temp_path)
            return self._quantize_png(image, colors=self._PNG_COLORS)
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def _quantize_png(content: bytes, *, colors: int) -> bytes:
        with Image.open(BytesIO(content)) as image:
            if image.mode in ("RGBA", "LA"):
                quantized = image.convert("RGBA").quantize(
                    colors=colors,
                    method=Image.Quantize.FASTOCTREE,
                )
            else:
                quantized = image.convert("RGB").quantize(
                    colors=colors,
                    method=Image.Quantize.MEDIANCUT,
                )

            output = BytesIO()
            quantized.save(output, format="PNG", optimize=True)
            return output.getvalue()

    def _write_temp_html(self, html: str) -> Path:
        with NamedTemporaryFile(
            mode="w",
            suffix=".html",
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(html)
            return Path(temp_file.name)

    def _render_from_file(self, html_path: Path) -> bytes:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    viewport={
                        "width": self._viewport_width,
                        "height": self._viewport_height,
                    },
                    device_scale_factor=self._device_scale_factor,
                )
                page.goto(html_path.as_uri(), wait_until="load")
                locator = page.locator("#news-card")
                locator.wait_for(state="visible")
                return locator.screenshot(type="png")
            finally:
                browser.close()
