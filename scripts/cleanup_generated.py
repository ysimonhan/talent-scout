from __future__ import annotations

import argparse
from pathlib import Path


def iter_cleanup_targets(generated_dir: Path) -> list[Path]:
    targets: list[Path] = []
    if not generated_dir.exists():
        return targets

    for path in generated_dir.rglob("*"):
        if path.name == "README.md":
            continue
        targets.append(path)
    return sorted(targets, key=lambda path: len(path.parts), reverse=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove generated harness artifacts.")
    parser.add_argument("--generated-dir", default="docs/generated")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_dir = Path(args.generated_dir)
    targets = iter_cleanup_targets(generated_dir)
    if args.check:
        if targets:
            print("Generated artifacts present:")
            for target in targets:
                print(target)
            raise SystemExit(1)
        print("No generated artifacts found.")
        return

    for target in targets:
        if target.is_file():
            target.unlink()
        elif target.is_dir():
            target.rmdir()
    print(f"Removed {len(targets)} generated artifacts from {generated_dir}")


if __name__ == "__main__":
    main()
