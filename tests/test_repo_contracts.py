from pathlib import Path

from scripts.check_repo import (
    check_integration_evidence,
    check_local_links,
    check_smoke_coverage,
    required_paths_for_level,
)


def test_required_paths_for_service_include_execplans_and_ci() -> None:
    required = {path.as_posix() for path in required_paths_for_level("service")}

    assert "docs/PLANS.md" in required
    assert ".github/workflows/ci.yml" in required
    assert "scripts/run_harness.py" in required


def test_check_local_links_reports_missing_relative_target(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[tool.repo_harness]\nlevel = 'core'\n", encoding="utf-8"
    )
    (docs_dir / "index.md").write_text("[missing](missing.md)\n", encoding="utf-8")

    errors = check_local_links(tmp_path)

    expected = f"Broken link in {Path('docs') / 'index.md'} -> missing.md"
    assert errors == [expected]


def test_integration_evidence_accepts_explicit_no_integrations_note(tmp_path: Path) -> None:
    evals_dir = tmp_path / "evals" / "smoke"
    evals_dir.mkdir(parents=True)
    (evals_dir / "hello.json").write_text("{}", encoding="utf-8")
    references_dir = tmp_path / "docs" / "references"
    references_dir.mkdir(parents=True)
    (references_dir / "integration-status.md").write_text(
        "Status: none\n\nNo external integrations yet.\n",
        encoding="utf-8",
    )
    fixtures_dir = tmp_path / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True)

    errors = check_integration_evidence(tmp_path, "integration", evals_dir, fixtures_dir)

    assert errors == []


def test_smoke_coverage_requires_a_json_case(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "evals" / "smoke"
    smoke_dir.mkdir(parents=True)

    errors = check_smoke_coverage(smoke_dir)

    assert len(errors) == 1
    assert errors[0].endswith("evals/smoke.")
