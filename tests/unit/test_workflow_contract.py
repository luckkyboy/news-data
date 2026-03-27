from pathlib import Path


def test_daily_fetch_workflow_exists_and_uses_cli_entrypoint() -> None:
    workflow = Path(".github/workflows/daily-fetch.yml")

    assert workflow.exists()

    content = workflow.read_text(encoding="utf-8")
    assert "concurrency:" in content
    assert "schedule:" in content
    assert "*/10 16-23,0-2 * * *" in content
    assert "workflow_dispatch:" in content
    assert "date:" in content
    assert "python -m app.entrypoints.run_daily_job" in content
    assert "id: run_job" in content
    assert "WECHAT_TOKEN" in content
    assert "WECHAT_COOKIE" in content
    assert "python -m playwright install --with-deps chromium" in content
    assert "permissions:" in content
    assert "contents: write" in content
    assert "git config --local user.email" in content
    assert "git config --local user.name" in content
    assert "git add static/news static/images" in content
    assert "git push" in content
    assert "actions:news:update" in content
