from __future__ import annotations

from pathlib import Path

from app.entrypoints.run_daily_job import parse_args


def test_parse_args_supports_date_accounts_file_and_output_dir(tmp_path: Path) -> None:
    accounts_file = tmp_path / "accounts.yaml"
    output_dir = tmp_path / "out"

    args = parse_args(
        [
            "--date",
            "2026-03-27",
            "--accounts-file",
            str(accounts_file),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert args.date == "2026-03-27"
    assert args.accounts_file == accounts_file
    assert args.output_dir == output_dir
