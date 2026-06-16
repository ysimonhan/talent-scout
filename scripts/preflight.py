from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class PreflightRecord:
    title: str
    summary: str
    systems: str
    impact: str
    rollout: str
    risks: str
    containment: str
    detection: str
    verification: str
    commands: str
    rollback: str
    evidence: str
    fixtures: str
    open_questions: str
    decision: str


PROMPTS: tuple[tuple[str, str], ...] = (
    ("title", "Short change title"),
    ("summary", "What does this change do"),
    ("systems", "Which systems, users, or data paths are affected"),
    ("impact", "How will this behave once rolled out"),
    ("rollout", "How will you ship or stage it"),
    ("risks", "How could this hurt production or customers"),
    ("containment", "How is blast radius limited"),
    ("detection", "How would you detect a bad rollout quickly"),
    ("verification", "What did you verify locally or in staging"),
    ("commands", "Which commands prove the behavior"),
    ("rollback", "How would you rollback or disable it"),
    ("evidence", "What evidence backs your understanding"),
    ("fixtures", "Which fixtures, docs, or traces were reviewed"),
    ("open_questions", "What is still uncertain"),
    ("decision", "Decision: ready, ready behind a flag, or not ready"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a shipping preflight for an agent-assisted change."
    )
    for field, _ in PROMPTS:
        parser.add_argument(f"--{field.replace('_', '-')}")
    parser.add_argument(
        "--out-dir",
        default="docs/change-reviews",
        help="Directory where the markdown artifact should be written.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "change"


def prompt_for_value(label: str) -> str:
    value = input(f"{label}: ").strip()
    return value or "TBD"


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return start


def load_harness_level(repo_root: Path) -> str:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return "unknown"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8-sig"))
    return data.get("tool", {}).get("repo_harness", {}).get("level", "unknown")


def collect_record(args: argparse.Namespace) -> PreflightRecord:
    values: dict[str, str] = {}
    interactive = sys.stdin.isatty()

    for field, label in PROMPTS:
        value = getattr(args, field, None)
        if value:
            values[field] = value.strip()
            continue
        if not interactive:
            raise SystemExit(
                f"Missing required argument '--{field.replace('_', '-')}' in non-interactive mode."
            )
        values[field] = prompt_for_value(label)

    return PreflightRecord(**values)


def next_output_path(out_dir: Path, title: str, today: date) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{today.isoformat()}-{slugify(title)}.md"
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = out_dir / f"{today.isoformat()}-{slugify(title)}-{counter}.md"
        if not candidate.exists():
            return candidate
        counter += 1


def render_markdown(record: PreflightRecord, today: date, harness_level: str) -> str:
    sections = (
        ("Change Summary", record.summary),
        ("Affected Surface", record.systems),
        ("Rollout Behavior", record.impact),
        ("Rollout Plan", record.rollout),
        ("Production Risks", record.risks),
        ("Blast Radius And Containment", record.containment),
        ("Detection Signals", record.detection),
        ("Verification", record.verification),
        ("Rollback", record.rollback),
        ("Evidence Reviewed", record.evidence),
        ("Fixtures, Docs, And Traces", record.fixtures),
        ("Open Questions", record.open_questions),
        ("Decision", record.decision),
    )

    lines = [
        f"# {record.title}",
        "",
        f"- Date: {today.isoformat()}",
        f"- Harness Level: {harness_level}",
        "- Purpose: force human judgment before shipping agent-assisted changes",
        "",
    ]

    for heading, body in sections:
        lines.extend((f"## {heading}", body, ""))

    lines.extend(("## Commands Run", "```text", record.commands, "```", ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    today = date.today()
    repo_root = find_repo_root(Path.cwd())
    harness_level = load_harness_level(repo_root)
    record = collect_record(args)
    output_path = next_output_path(repo_root / args.out_dir, record.title, today)
    output_path.write_text(render_markdown(record, today, harness_level), encoding="utf-8")
    print(f"Wrote preflight review to {output_path}")


if __name__ == "__main__":
    main()
