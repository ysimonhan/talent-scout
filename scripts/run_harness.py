from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SmokeCase:
    path: Path
    name: str
    command: list[str]
    cwd: str
    expect_exit_code: int
    expect_stdout_contains: list[str]


@dataclass(frozen=True)
class SmokeResult:
    case: SmokeCase
    passed: bool
    returncode: int
    stdout: str
    stderr: str
    reason: str


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return start


def load_harness_config(repo_root: Path) -> dict[str, str]:
    data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8-sig"))
    return data.get("tool", {}).get("repo_harness", {})


def parse_case(path: Path) -> SmokeCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    return SmokeCase(
        path=path,
        name=data["name"],
        command=data["command"],
        cwd=data.get("cwd", "."),
        expect_exit_code=data.get("expect_exit_code", 0),
        expect_stdout_contains=data.get("expect_stdout_contains", []),
    )


def load_cases(smoke_dir: Path) -> list[SmokeCase]:
    return [parse_case(path) for path in sorted(smoke_dir.glob("*.json"))]


def resolve_command(command: list[str]) -> list[str]:
    if command and command[0] == "python":
        return [sys.executable, *command[1:]]
    return command


def run_case(case: SmokeCase, repo_root: Path) -> SmokeResult:
    completed = subprocess.run(
        resolve_command(case.command),
        cwd=repo_root / case.cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    reason = ""
    passed = completed.returncode == case.expect_exit_code
    if not passed:
        reason = f"Expected exit code {case.expect_exit_code}, got {completed.returncode}."
    else:
        for expected in case.expect_stdout_contains:
            if expected not in completed.stdout:
                passed = False
                reason = f"Missing expected stdout fragment: {expected!r}."
                break

    return SmokeResult(
        case=case,
        passed=passed,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        reason=reason or "ok",
    )


def render_summary(results: list[SmokeResult]) -> str:
    lines = ["# Harness Summary", ""]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            (
                f"## {status}: {result.case.name}",
                f"- Case file: {result.case.path.name}",
                f"- Exit code: {result.returncode}",
                f"- Reason: {result.reason}",
                "",
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def write_summary(repo_root: Path, generated_dir: str, content: str) -> Path:
    output_dir = repo_root / generated_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "harness-summary.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run smoke harness scenarios.")
    parser.add_argument("--smoke-dir")
    parser.add_argument("--write-summary", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd())
    config = load_harness_config(repo_root)
    smoke_dir = repo_root / (args.smoke_dir or config.get("smoke_dir", "evals/smoke"))
    cases = load_cases(smoke_dir)
    if not cases:
        raise SystemExit(f"No smoke cases found in {smoke_dir}")

    results = [run_case(case, repo_root) for case in cases]
    summary = render_summary(results)
    print(summary, end="")

    if args.write_summary:
        summary_path = write_summary(
            repo_root, config.get("generated_dir", "docs/generated"), summary
        )
        print(f"Wrote summary to {summary_path}")

    if any(not result.passed for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
