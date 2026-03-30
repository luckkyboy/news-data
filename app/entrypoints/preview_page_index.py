from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_preview_index(
    *,
    news_dir: Path,
    image_dir: Path,
    json_prefix: str = "./static/news",
    image_prefix: str = "./static/images",
) -> dict[str, object]:
    items: list[dict[str, str]] = []
    for json_path in sorted(news_dir.glob("*.json")):
        date = json_path.stem
        image_path = image_dir / f"{date}.png"
        if not image_path.exists():
            continue
        items.append(
            {
                "date": date,
                "json_path": f"{json_prefix}/{date}.json",
                "image_path": f"{image_prefix}/{date}.png",
            }
        )
    latest = items[-1]["date"] if items else ""
    return {"latest": latest, "items": items}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build GitHub Pages preview index")
    parser.add_argument("--news-dir", type=Path, default=Path("pages/static/news"))
    parser.add_argument("--image-dir", type=Path, default=Path("pages/static/images"))
    parser.add_argument("--output", type=Path, default=Path("pages/data/index.json"))
    args = parser.parse_args(argv)

    payload = build_preview_index(news_dir=args.news_dir, image_dir=args.image_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
