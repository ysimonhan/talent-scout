from pathlib import Path

from scripts.capture_fixture import next_fixture_path, render_metadata
from scripts.cleanup_generated import iter_cleanup_targets
from scripts.run_harness import SmokeCase, run_case


def test_run_case_passes_when_stdout_matches(tmp_path: Path) -> None:
    script = tmp_path / "hello.py"
    script.write_text("print('hello harness')\n", encoding="utf-8")
    case = SmokeCase(
        path=tmp_path / "case.json",
        name="hello",
        command=["python", str(script)],
        cwd=".",
        expect_exit_code=0,
        expect_stdout_contains=["hello harness"],
    )

    result = run_case(case, tmp_path)

    assert result.passed is True
    assert result.reason == "ok"


def test_next_fixture_path_increments_suffix(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    first = next_fixture_path(fixtures_dir, "Upstream Timeout", ".json")
    first.write_text("{}", encoding="utf-8")

    second = next_fixture_path(fixtures_dir, "Upstream Timeout", ".json")

    assert first.name == "upstream-timeout.json"
    assert second.name == "upstream-timeout-2.json"


def test_render_metadata_mentions_provider() -> None:
    content = render_metadata(
        Path("capture.json"),
        Path("tests/fixtures/capture.json"),
        "openai",
        "Captured from staging.",
    )

    assert "Provider: openai" in content
    assert "Captured from staging." in content


def test_iter_cleanup_targets_skips_readme(tmp_path: Path) -> None:
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    (generated_dir / "README.md").write_text("keep", encoding="utf-8")
    (generated_dir / "summary.md").write_text("delete", encoding="utf-8")

    targets = iter_cleanup_targets(generated_dir)

    assert targets == [generated_dir / "summary.md"]
