from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "fixture"


def next_fixture_path(fixtures_dir: Path, name: str, suffix: str) -> Path:
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    base = fixtures_dir / f"{slugify(name)}{suffix}"
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = fixtures_dir / f"{slugify(name)}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def render_metadata(source: Path, destination: Path, provider: str, note: str) -> str:
    lines = [
        f"# Fixture: {destination.name}",
        "",
        f"- Captured At: {datetime.now(timezone.utc).isoformat()}",
        f"- Source Path: {source}",
        f"- Provider: {provider or 'unspecified'}",
        f"- Note: {note or 'n/a'}",
        "",
        "Use this fixture to back tests or parser assumptions.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy a durable fixture into tests/fixtures.")
    parser.add_argument("--source", required=True, help="Existing file to copy into fixtures.")
    parser.add_argument("--name", required=True, help="Human-readable fixture name.")
    parser.add_argument("--provider", default="", help="Optional provider or system name.")
    parser.add_argument(
        "--note", default="", help="Optional note describing why this fixture matters."
    )
    parser.add_argument(
        "--fixtures-dir",
        default="tests/fixtures",
        help="Destination directory for stored fixtures.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"Source fixture does not exist: {source}")

    fixtures_dir = Path(args.fixtures_dir)
    destination = next_fixture_path(fixtures_dir, args.name, source.suffix)
    shutil.copy2(source, destination)

    metadata_path = destination.with_suffix(destination.suffix + ".md")
    metadata_path.write_text(
        render_metadata(source, destination, args.provider, args.note),
        encoding="utf-8",
    )
    print(f"Captured fixture to {destination}")
    print(f"Wrote metadata to {metadata_path}")


if __name__ == "__main__":
    main()
