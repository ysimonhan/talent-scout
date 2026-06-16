from datetime import date
from pathlib import Path

from scripts.preflight import (
    PreflightRecord,
    load_harness_level,
    next_output_path,
    render_markdown,
    slugify,
)


def test_slugify_keeps_names_stable() -> None:
    assert slugify("Cache retry safety!") == "cache-retry-safety"


def test_next_output_path_increments_suffix(tmp_path: Path) -> None:
    today = date(2026, 4, 1)
    out_dir = tmp_path / "reviews"
    first = next_output_path(out_dir, "Safer rollout", today)
    first.write_text("first", encoding="utf-8")

    second = next_output_path(out_dir, "Safer rollout", today)

    assert first.name == "2026-04-01-safer-rollout.md"
    assert second.name == "2026-04-01-safer-rollout-2.md"


def test_load_harness_level_reads_repo_config(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.repo_harness]
level = "service"
""".strip(),
        encoding="utf-8",
    )

    assert load_harness_level(tmp_path) == "service"


def test_render_markdown_contains_key_sections() -> None:
    record = PreflightRecord(
        title="Safer rollout",
        summary="Add a timeout to upstream calls.",
        systems="Worker queue and upstream API client.",
        impact="Requests fail fast instead of hanging forever.",
        rollout="Ship to staging first and enable behind a flag.",
        risks="Timeout too low could create false failures.",
        containment="Gate with an env var and ship to staging first.",
        detection="Watch timeout and error rates in staging logs.",
        verification="Ran pytest and staged a manual timeout scenario.",
        commands="uv run python -m pytest\nuv run python scripts/run_harness.py",
        rollback="Set the env var off or revert the deploy.",
        evidence="Official API docs and a captured timeout fixture.",
        fixtures="Captured timeout fixture and a staging trace.",
        open_questions="Need real-world latency data after rollout.",
        decision="Ready behind a flag.",
    )

    content = render_markdown(record, date(2026, 4, 1), "service")

    assert "# Safer rollout" in content
    assert "- Harness Level: service" in content
    assert "## Production Risks" in content
    assert "## Commands Run" in content
    assert "Ready behind a flag." in content
