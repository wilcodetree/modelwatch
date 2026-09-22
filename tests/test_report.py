import pytest

from modelwatch.report import area_statistics, paired_differences


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
