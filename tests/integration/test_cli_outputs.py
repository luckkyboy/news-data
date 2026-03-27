from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from app.domain.models import JobRunResult
from app.entrypoints import run_daily_job as module


def test_write_github_output_writes_status_and_target_date(tmp_path: Path) -> None:
    output_path = tmp_path / "github_output.txt"
    result = JobRunResult(status="updated", target_date="2026-03-27")

    module.write_github_output(output_path, result)

    content = output_path.read_text(encoding="utf-8")
    assert "status=updated" in content
    assert "target_date=2026-03-27" in content


def test_main_writes_github_output_when_env_is_set(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "github_output.txt"
    service_calls: list[str] = []

    class FakeService:
        def run(self, target_date: str) -> JobRunResult:
            service_calls.append(target_date)
            return JobRunResult(status="skipped", target_date=target_date)

        def close(self) -> None:
            service_calls.append("close")

    monkeypatch.setattr(module, "configure_logging", lambda: None)
    monkeypatch.setattr(module, "parse_args", lambda argv=None: Namespace(date="2026-03-27"))
    monkeypatch.setattr(module, "build_service", lambda args: FakeService())
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    exit_code = module.main([])

    assert exit_code == 0
    assert service_calls == ["2026-03-27", "close"]
    content = output_path.read_text(encoding="utf-8")
    assert "status=skipped" in content
    assert "target_date=2026-03-27" in content


def test_main_returns_non_zero_when_job_fails(monkeypatch) -> None:
    class BrokenService:
        def run(self, target_date: str) -> JobRunResult:
            raise RuntimeError("boom")

        def close(self) -> None:
            return None

    monkeypatch.setattr(module, "configure_logging", lambda: None)
    monkeypatch.setattr(module, "parse_args", lambda argv=None: Namespace(date="2026-03-27"))
    monkeypatch.setattr(module, "build_service", lambda args: BrokenService())

    exit_code = module.main([])

    assert exit_code == 1
