from app.domain.models import DailyNewsDocument, JobRunResult


def test_job_run_result_defaults_to_no_document() -> None:
    result = JobRunResult(status="skipped", target_date="2026-03-27")

    assert result.status == "skipped"
    assert result.target_date == "2026-03-27"
    assert result.document is None


def test_job_run_result_accepts_document() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条"],
        cover="",
        title="每天60秒读懂世界｜3月27日",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    result = JobRunResult(
        status="updated",
        target_date="2026-03-27",
        document=document,
    )

    assert result.document == document
