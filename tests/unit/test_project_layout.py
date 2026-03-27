from pathlib import Path


def test_project_layout_exists() -> None:
    assert Path("app").exists()
    assert Path("config/accounts.yaml").exists()
    assert Path("static/news").exists()
    assert Path("static/images").exists()
    assert Path("tests/fixtures").exists()
