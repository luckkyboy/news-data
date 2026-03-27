from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.domain.models import JobRunResult
from app.infrastructure.clock import BEIJING_TZ
from app.infrastructure.config import get_image_base_url, load_accounts
from app.infrastructure.logging import configure_logging
from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl
from app.infrastructure.wechat.mp_client import WeChatMPClient


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily WeChat fetch job")
    parser.add_argument("--date", type=str, default=None, help="Target date in YYYY-MM-DD")
    parser.add_argument(
        "--accounts-file",
        type=Path,
        default=Path("config/accounts.yaml"),
        help="Path to the accounts configuration file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("static/news"),
        help="Directory for generated JSON documents",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("static/images"),
        help="Directory for generated PNG images",
    )
    parser.add_argument(
        "--template-path",
        type=Path,
        default=Path("app/infrastructure/render/template.html"),
        help="Path to the image render HTML template",
    )
    return parser.parse_args(argv)


def build_service(args: argparse.Namespace) -> DailyJobService:
    token, cookie = _read_credentials()
    accounts = load_accounts(args.accounts_file)
    repository = StaticAssetsRepositoryImpl(
        json_dir=args.output_dir,
        image_dir=args.image_dir,
        image_base_url=get_image_base_url(),
    )
    return DailyJobService(
        source_client=WeChatMPClient(token=token, cookie=cookie),
        parser=WeChatArticleParser(),
        repository=repository,
        accounts=accounts,
        image_renderer=PlaywrightImageRenderer(template_path=args.template_path),
    )


def write_github_output(output_path: Path, result: JobRunResult) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"status={result.status}\n")
        handle.write(f"target_date={result.target_date}\n")


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    try:
        args = parse_args(argv)
        target_date = args.date or _today_beijing()
        service = build_service(args)
        try:
            result = service.run(target_date)
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                write_github_output(Path(github_output), result)
        finally:
            service.close()
        return 0
    except Exception:
        logging.getLogger(__name__).exception("daily job failed")
        return 1


def _read_credentials() -> tuple[str, str]:
    token = os.environ.get("WECHAT_TOKEN")
    cookie = os.environ.get("WECHAT_COOKIE")
    if not token or not cookie:
        raise RuntimeError("WECHAT_TOKEN and WECHAT_COOKIE are required")
    return token, cookie


def _today_beijing() -> str:
    return datetime.now(BEIJING_TZ).date().isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
