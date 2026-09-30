import pytest

import modelwatch.report as report
from modelwatch.report import (
    area_statistics,
    coverage_summary,
    paired_area_differences,
    paired_differences,
)


def _row(area: str, model: str, task: str, repeat: int, score: float) -> dict:
    return {"area": area, "model_snapshot": model, "task_id": task,
            "repeat": repeat, "score": score}


def test_area_standard_error_uses_repeat_means() -> None:
    rows = [
        _row("hub_edits", "a", "one", 1, 1.0),
        _row("hub_edits", "a", "two", 1, 1.0),
        _row("hub_edits", "a", "one", 2, 0.0),
        _row("hub_edits", "a", "two", 2, 0.0),
    ]
    result = area_statistics(rows)[0]
    assert result["mean"] == 0.5
    assert result["se"] == 0.5


def test_area_statistics_excludes_sample_errors() -> None:
    rows = [
        _row("hub_edits", "a", "one", 1, 1.0),
        {
            **_row("hub_edits", "a", "one", 2, 0.0),
            "notes": "sample_error:provider failure",
        },
    ]

    result = area_statistics(rows)[0]

    assert result["mean"] == 1.0
    assert result["n_repeats"] == 1


def test_paired_difference_and_standard_error() -> None:
    rows = [
        _row("injection", "a", "one", 1, 1.0),
        _row("injection", "b", "one", 1, 0.0),
        _row("injection", "a", "one", 2, 0.5),
        _row("injection", "b", "one", 2, 0.0),
        _row("injection", "a", "one", 3, 0.5),
        _row("injection", "b", "one", 3, 0.5),
    ]
    result = paired_differences(rows)[0]
    assert result["difference"] == pytest.approx(0.5)
    assert result["se"] == pytest.approx(0.288675, rel=1e-5)
    assert result["larger_than_one_se"] is True


def test_paired_area_difference_selects_top_two_models() -> None:
    rows = [
        _row("voice", "a", "one", 1, 1.0),
        _row("voice", "a", "two", 1, 0.8),
        _row("voice", "a", "one", 2, 0.8),
        _row("voice", "a", "two", 2, 0.6),
        _row("voice", "b", "one", 1, 0.6),
        _row("voice", "b", "two", 1, 0.6),
        _row("voice", "b", "one", 2, 0.4),
        _row("voice", "b", "two", 2, 0.4),
        _row("voice", "c", "one", 1, 0.0),
        _row("voice", "c", "one", 2, 0.0),
    ]

    result = paired_area_differences(rows)[0]

    assert result["model_a"] == "a"
    assert result["model_b"] == "b"
    assert result["difference"] == pytest.approx(0.3)
    assert result["se"] == pytest.approx(0.0, abs=1e-12)
    assert result["larger_than_one_se"] is True


def test_coverage_summary_marks_interrupted_partial_run() -> None:
    rows = [
        _row("voice", "a", "one", 1, 1.0),
        _row("voice", "a", "one", 2, 1.0),
        _row("voice", "b", "one", 1, 0.5),
        {
            **_row("voice", "b", "one", 2, 0.0),
            "notes": "sample_error:provider failure",
        },
    ]
    manifest = {
        "status": "error",
        "error": "KeyboardInterrupt: ",
        "models": [{"snapshot": "a"}, {"snapshot": "b"}],
    }

    result = coverage_summary(rows, manifest)

    assert result["observed"] == 3
    assert result["expected"] == 4
    assert result["complete"] is False
    assert result["models"] == [
        {"model_snapshot": "a", "observed": 2, "expected": 2},
        {"model_snapshot": "b", "observed": 1, "expected": 2},
    ]


def test_run_report_wraps_dense_tables_for_responsive_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    rows = []
    for model, score in (("a", 1.0), ("b", 0.5)):
        row = _row("voice", model, "one", 1, score)
        row.update({
            "run_id": "run",
            "run_date": "2026-09-24",
            "source": "private",
            "inspect_version": "test",
            "taskset_version": "test",
            "roster_date": "2026-09-24",
            "cost_eur": 0.0,
            "wall_s": 1.0,
        })
        rows.append(row)
    monkeypatch.setattr(report, "existing_rows", lambda: rows)
    monkeypatch.setattr(
        report,
        "_run_manifest",
        lambda _run_id: {
            "status": "complete",
            "guard_status": "within_limit",
            "models": [
                {"snapshot": "a", "cost_eur": 0.0, "wall_s": 1.0},
                {"snapshot": "b", "cost_eur": 0.0, "wall_s": 1.0},
            ],
        },
    )

    output = tmp_path / "report.html"
    report.render_run_report(run_id="run", output=output)
    document = output.read_text(encoding="utf-8")

    assert "class='table-scroll external'" in document
    assert document.count("class='table-scroll'") == 3
