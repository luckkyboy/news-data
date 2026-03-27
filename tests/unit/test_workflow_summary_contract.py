from pathlib import Path


def test_daily_fetch_workflow_writes_summary_with_status_and_target_date() -> None:
    content = Path(".github/workflows/daily-fetch.yml").read_text(encoding="utf-8")

    assert "GITHUB_STEP_SUMMARY" in content
    assert "Write workflow summary" in content
    assert "status:" in content
    assert "target_date:" in content
    assert "always()" in content
