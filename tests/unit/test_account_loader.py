from pathlib import Path

from app.infrastructure.config import load_accounts


def test_load_accounts_filters_disabled_and_sorts_by_priority(tmp_path: Path) -> None:
    accounts_file = tmp_path / "accounts.yaml"
    accounts_file.write_text(
        """
accounts:
  - name: low
    wechat_id: low_id
    fake_id: low_fake
    query: low query
    enabled: true
    priority: 10
  - name: disabled
    wechat_id: disabled_id
    fake_id: disabled_fake
    query: disabled query
    enabled: false
    priority: 999
  - name: high
    wechat_id: high_id
    fake_id: high_fake
    query: high query
    enabled: true
    priority: 20
""".strip(),
        encoding="utf-8",
    )

    accounts = load_accounts(accounts_file)

    assert [account.name for account in accounts] == ["high", "low"]
    assert all(account.enabled for account in accounts)
