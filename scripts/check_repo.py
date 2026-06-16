from __future__ import annotations

import re
import tomllib
from pathlib import Path


LEVELS = ("core", "integration", "service", "critical")
IGNORED_PARTS = {
    ".venv",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
}

REQUIRED_PATHS = {
    "core": (
        "AGENTS.md",
        "README.md",
        "docs/index.md",
        "docs/architecture.md",
        "docs/reliability.md",
        "docs/quality-score.md",
        "docs/golden-principles.md",
        "docs/bootstrap-checklist.md",
        "docs/references/README.md",
        "docs/references/integration-status.md",
        "docs/generated/README.md",
        "docs/change-reviews/README.md",
        "evals/README.md",
        "evals/smoke/README.md",
        "scripts/preflight.py",
        "scripts/check_repo.py",
        "scripts/cleanup_generated.py",
    ),
    "integration": (
        "docs/integration-guardrails.md",
        "tests/fixtures/README.md",
        "scripts/capture_fixture.py",
    ),
    "service": (
        ".github/workflows/ci.yml",
        "docs/PLANS.md",
        "docs/exec-plans/template.md",
        "docs/exec-plans/active/README.md",
        "docs/exec-plans/completed/README.md",
        "scripts/run_harness.py",
    ),
    "critical": (),
}


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return start


def load_harness_level(repo_root: Path) -> str:
    level = load_harness_config(repo_root).get("level", "core")
    if level not in LEVELS:
        raise SystemExit(f"Unsupported harness level: {level}")
    return level


def load_harness_config(repo_root: Path) -> dict[str, str]:
    data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8-sig"))
    return data.get("tool", {}).get("repo_harness", {})


def required_paths_for_level(level: str) -> list[Path]:
    required: list[Path] = []
    for candidate in LEVELS:
        required.extend(Path(path) for path in REQUIRED_PATHS[candidate])
        if candidate == level:
            break
    return required


def iter_markdown_files(repo_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repo_root.rglob("*.md")
        if not any(part in IGNORED_PARTS for part in path.relative_to(repo_root).parts)
    )


def extract_local_links(markdown_path: Path) -> list[str]:
    content = markdown_path.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", content)
    return [link for link in links if not link.startswith(("http://", "https://", "mailto:", "#"))]


def check_local_links(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for markdown_path in iter_markdown_files(repo_root):
        for raw_link in extract_local_links(markdown_path):
            link = raw_link.split("#", maxsplit=1)[0]
            if not link:
                continue
            target = (markdown_path.parent / link).resolve()
            if not target.exists():
                errors.append(
                    f"Broken link in {markdown_path.relative_to(repo_root)} -> {raw_link}"
                )
    return errors


def check_required_paths(repo_root: Path, level: str) -> list[str]:
    errors: list[str] = []
    for relative_path in required_paths_for_level(level):
        if not (repo_root / relative_path).exists():
            errors.append(f"Missing required path: {relative_path}")
    return errors


def has_smoke_case(smoke_dir: Path) -> bool:
    return (
        any(path.suffix == ".json" for path in smoke_dir.iterdir()) if smoke_dir.exists() else False
    )


def has_real_fixture(fixtures_dir: Path) -> bool:
    if not fixtures_dir.exists():
        return False
    return any(path.is_file() and path.name != "README.md" for path in fixtures_dir.iterdir())


def check_smoke_coverage(smoke_dir: Path) -> list[str]:
    if has_smoke_case(smoke_dir):
        return []
    return [f"Expected at least one smoke case in {smoke_dir.as_posix()}."]


def check_integration_evidence(
    repo_root: Path, level: str, smoke_dir: Path, fixtures_dir: Path
) -> list[str]:
    if LEVELS.index(level) < LEVELS.index("integration"):
        return []

    errors: list[str] = []
    integration_status = repo_root / "docs/references/integration-status.md"
    status_text = (
        integration_status.read_text(encoding="utf-8") if integration_status.exists() else ""
    )
    if not has_real_fixture(fixtures_dir) and "No external integrations yet." not in status_text:
        errors.append(
            "Expected at least one real fixture in tests/fixtures or an explicit no-integrations note."
        )
    return errors


def main() -> None:
    repo_root = find_repo_root(Path.cwd())
    config = load_harness_config(repo_root)
    level = load_harness_level(repo_root)
    smoke_dir = repo_root / config.get("smoke_dir", "evals/smoke")
    fixtures_dir = repo_root / config.get("fixture_dir", "tests/fixtures")

    errors = []
    errors.extend(check_required_paths(repo_root, level))
    errors.extend(check_local_links(repo_root))
    errors.extend(check_smoke_coverage(smoke_dir))
    errors.extend(check_integration_evidence(repo_root, level, smoke_dir, fixtures_dir))

    if errors:
        print(f"Repository checks failed for harness level '{level}':")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Repository checks passed for harness level '{level}'.")


if __name__ == "__main__":
    main()
