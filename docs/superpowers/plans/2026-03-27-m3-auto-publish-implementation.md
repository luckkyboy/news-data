# M3 Auto Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add GitHub Actions auto-publish so that successful daily runs can commit and push changed `static/news` and `static/images` artifacts back to the current repository main branch, using Python-emitted run results to drive publish decisions.

**Architecture:** Keep fetch, parse, render, and storage logic in Python, but add a lightweight job result model that tells the workflow what happened (`skipped`, `updated`, `backfilled_image`). Keep git operations in the workflow only, with concurrency control and a fixed commit message format.

**Tech Stack:** Python 3.12, pydantic, GitHub Actions, Playwright, pytest

---

### Task 1: Add Job Run Result Model

**Files:**
- Modify: `app/domain/models.py`
- Create: `tests/unit/test_job_run_result.py`
- Test: `tests/unit/test_job_run_result.py`

- [ ] **Step 1: Write the failing result model test**

```python
from app.domain.models import DailyNewsDocument, JobRunResult


def test_job_run_result_tracks_status_and_target_date() -> None:
    result = JobRunResult(status="updated", target_date="2026-03-27")
    assert result.status == "updated"
    assert result.target_date == "2026-03-27"


def test_job_run_result_accepts_optional_document() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A"],
        cover="",
        image="https://cdn.example.com/static/images/2026-03-27.png",
        title="title",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    result = JobRunResult(status="backfilled_image", target_date="2026-03-27", document=document)
    assert result.document == document
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_run_result.py -v`
Expected: FAIL because `JobRunResult` does not exist yet

- [ ] **Step 3: Add the result model**

```python
# app/domain/models.py
from typing import Literal

class JobRunResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["skipped", "updated", "backfilled_image"]
    target_date: str
    document: DailyNewsDocument | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_run_result.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/models.py tests/unit/test_job_run_result.py
git commit -m "feat: add job run result model"
```

### Task 2: Update Daily Job Service To Return Structured Status

**Files:**
- Modify: `app/application/daily_job.py`
- Create: `tests/integration/test_job_run_statuses.py`
- Test: `tests/integration/test_job_run_statuses.py`

- [ ] **Step 1: Write the failing status integration tests**

```python
from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


class NeverSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6):
        raise AssertionError("should not search")

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("should not fetch")


class NeverParser:
    def parse(self, html: str):
        raise AssertionError("should not parse")


class FakeRenderer:
    def render(self, document: DailyNewsDocument) -> bytes:
        return b"png"


def test_run_returns_skipped_when_json_and_png_exist(tmp_path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "news",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images",
    )
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["A"],
            cover="",
            image="https://cdn.example.com/static/images/2026-03-27.png",
            title="title",
            quote="",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )
    repository.save_image("2026-03-27", b"png")

    service = DailyJobService(
        source_client=NeverSourceClient(),
        parser=NeverParser(),
        repository=repository,
        accounts=[],
        image_renderer=FakeRenderer(),
    )

    result = service.run("2026-03-27")
    assert result.status == "skipped"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_job_run_statuses.py -v`
Expected: FAIL because `DailyJobService.run()` does not return result objects yet

- [ ] **Step 3: Update orchestration to emit statuses**

```python
# app/application/daily_job.py
# Return JobRunResult from all code paths:
# - skipped when json and image exist
# - backfilled_image when json exists but image did not
# - updated when full fetch/render path succeeds
```

Concrete expectation:

- `json_exists && image_exists` -> `JobRunResult(status="skipped", target_date=target_date)`
- `json_exists && !image_exists` -> `JobRunResult(status="backfilled_image", target_date=target_date, document=final_document)`
- full fetch/render path -> `JobRunResult(status="updated", target_date=target_date, document=final_document)`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_job_run_statuses.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/application/daily_job.py tests/integration/test_job_run_statuses.py
git commit -m "feat: return structured run statuses"
```

### Task 3: Update Existing Integration Tests For Result Objects

**Files:**
- Modify: `tests/integration/test_daily_job.py`
- Modify: `tests/integration/test_daily_job_images.py`
- Modify: `tests/integration/test_m2_backfill_and_failures.py`
- Modify: `tests/integration/test_failure_modes.py`
- Test: `tests/integration/test_daily_job.py`
- Test: `tests/integration/test_daily_job_images.py`
- Test: `tests/integration/test_m2_backfill_and_failures.py`
- Test: `tests/integration/test_failure_modes.py`

- [ ] **Step 1: Write the failing expectations**

```python
# Update tests so they assert:
# - result.status == "updated" for fresh fetch path
# - result.status == "backfilled_image" for image-only backfill
# - result.status == "skipped" for fully existing path
# - raised RuntimeError paths remain unchanged
```

- [ ] **Step 2: Run tests to verify they fail against old expectations**

Run: `pytest tests/integration/test_daily_job.py tests/integration/test_daily_job_images.py tests/integration/test_m2_backfill_and_failures.py tests/integration/test_failure_modes.py -v`
Expected: FAIL until assertions match the new result model

- [ ] **Step 3: Update the tests**

```python
# Example adjustment
result = service.run("2026-03-27")
assert result.status == "updated"
assert result.document is not None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_daily_job.py tests/integration/test_daily_job_images.py tests/integration/test_m2_backfill_and_failures.py tests/integration/test_failure_modes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_daily_job.py tests/integration/test_daily_job_images.py tests/integration/test_m2_backfill_and_failures.py tests/integration/test_failure_modes.py
git commit -m "test: align integration tests with run statuses"
```

### Task 4: Write GitHub Actions Outputs From CLI Entrypoint

**Files:**
- Modify: `app/entrypoints/run_daily_job.py`
- Create: `tests/integration/test_cli_outputs.py`
- Test: `tests/integration/test_cli_outputs.py`

- [ ] **Step 1: Write the failing CLI output test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_cli_outputs.py -v`
Expected: FAIL because the CLI does not expose GitHub output writing yet

- [ ] **Step 3: Add GitHub output writing**

```python
# app/entrypoints/run_daily_job.py
from app.domain.models import JobRunResult


def write_github_output(output_path: Path, result: JobRunResult) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"status={result.status}\n")
        handle.write(f"target_date={result.target_date}\n")


def main(argv: list[str] | None = None) -> int:
    ...
    result = service.run(target_date)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        write_github_output(Path(github_output), result)
    return 0
```

Important:

- `main()` still returns non-zero on exception
- GitHub output writing is best-effort only after a successful run

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_cli_outputs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/entrypoints/run_daily_job.py tests/integration/test_cli_outputs.py
git commit -m "feat: emit github action outputs from cli"
```

### Task 5: Update Composition Tests For Entrypoint Output Behavior

**Files:**
- Modify: `tests/integration/test_end_to_end_composition.py`
- Modify: `tests/integration/test_m2_composition.py`
- Test: `tests/integration/test_end_to_end_composition.py`
- Test: `tests/integration/test_m2_composition.py`

- [ ] **Step 1: Update composition tests to stay compatible**

```python
# Keep these tests focused on dependency wiring.
# They should still assert build_service returns DailyJobService,
# and must not assume old return shape from service.run().
```

- [ ] **Step 2: Run tests to verify they still pass**

Run: `pytest tests/integration/test_end_to_end_composition.py tests/integration/test_m2_composition.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_end_to_end_composition.py tests/integration/test_m2_composition.py
git commit -m "test: keep composition tests compatible with m3 outputs"
```

### Task 6: Add Auto-Publish Steps To Workflow

**Files:**
- Modify: `.github/workflows/daily-fetch.yml`
- Modify: `tests/unit/test_workflow_contract.py`
- Test: `tests/unit/test_workflow_contract.py`

- [ ] **Step 1: Write the failing workflow publish expectation**

```python
from pathlib import Path


def test_daily_fetch_workflow_configures_auto_publish() -> None:
    content = Path(".github/workflows/daily-fetch.yml").read_text(encoding="utf-8")
    assert "concurrency:" in content
    assert "git config --local user.email" in content
    assert "git config --local user.name" in content
    assert "actions:news:update" in content
    assert "git add static/news static/images" in content
    assert "git push" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: FAIL because the workflow does not publish yet

- [ ] **Step 3: Update workflow**

```yaml
# .github/workflows/daily-fetch.yml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  fetch:
    permissions:
      contents: write
    steps:
      ...
      - name: Run daily fetch job
        id: run_job
        ...

      - name: Commit and push assets
        if: steps.run_job.outputs.status != 'skipped'
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add static/news static/images
          if [ -n "$(git status --porcelain)" ]; then
            git commit -m "actions:news:update ${{ steps.run_job.outputs.target_date }} assets"
            git push
          else
            echo "No changes to publish"
          fi
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/daily-fetch.yml tests/unit/test_workflow_contract.py
git commit -m "feat: auto publish generated assets in workflow"
```

### Task 7: Add Workflow Summary Output

**Files:**
- Modify: `.github/workflows/daily-fetch.yml`
- Create: `tests/unit/test_workflow_summary_contract.py`
- Test: `tests/unit/test_workflow_summary_contract.py`

- [ ] **Step 1: Write the failing summary test**

```python
from pathlib import Path


def test_workflow_writes_summary() -> None:
    content = Path(".github/workflows/daily-fetch.yml").read_text(encoding="utf-8")
    assert "GITHUB_STEP_SUMMARY" in content
    assert "status" in content
    assert "target_date" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_workflow_summary_contract.py -v`
Expected: FAIL because the workflow does not write summary yet

- [ ] **Step 3: Add a summary step**

```yaml
      - name: Write workflow summary
        if: always()
        run: |
          echo "### Daily News Workflow" >> "$GITHUB_STEP_SUMMARY"
          echo "" >> "$GITHUB_STEP_SUMMARY"
          echo "- status: ${{ steps.run_job.outputs.status || 'failed' }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- target_date: ${{ steps.run_job.outputs.target_date || 'unknown' }}" >> "$GITHUB_STEP_SUMMARY"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_workflow_summary_contract.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/daily-fetch.yml tests/unit/test_workflow_summary_contract.py
git commit -m "feat: add workflow publish summary"
```

### Task 8: Verify Full M3 Baseline

**Files:**
- Test: `tests/unit/`
- Test: `tests/integration/`

- [ ] **Step 1: Run unit tests**

Run: `pytest tests/unit -v`
Expected: PASS

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/integration -v`
Expected: PASS

- [ ] **Step 3: Run full suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 4: Run lint and type checks**

Run: `ruff check .`
Expected: All checks pass

Run: `mypy app`
Expected: Success with no issues found

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "chore: finalize m3 auto publish baseline"
```

## Self-Review

Spec coverage check:

- Covered result model, service statuses, CLI GitHub outputs, workflow publish steps, concurrency, summary output, and final verification.
- Covered user requirements: workflow-driven push to current main branch and fixed commit message `actions:news:update YYYY-MM-DD assets`.

Placeholder scan:

- No `TODO`, `TBD`, or unresolved placeholders remain.

Type consistency:

- `JobRunResult` cleanly wraps the run outcome without changing existing `DailyNewsDocument` schema.
- `DailyJobService` still owns orchestration; git remains in workflow only.

Execution handoff:

Plan complete and saved to `docs/superpowers/plans/2026-03-27-m3-auto-publish-implementation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
