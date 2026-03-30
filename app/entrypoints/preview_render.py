from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.render import TEMPLATE_PATH
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a preview image from one JSON file")
    parser.add_argument("--json-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--template-path", type=Path, default=TEMPLATE_PATH)
    args = parser.parse_args(argv)

    try:
        document = DailyNewsDocument.model_validate_json(
            args.json_path.read_text(encoding="utf-8")
        )
        renderer = PlaywrightImageRenderer(template_path=args.template_path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(renderer.render(document))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("preview render failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
