from pathlib import Path

import pytest

from modelwatch.calibration import read_calibration, write_calibration


def _rows() -> list[dict]:
    return [
        {
            "task_id": f"private.{index}",
            "model": "provider/model",
            "judge_model": "judge/model",
            "judge_score": 4.0,
            "rubric": "Use the stored rubric.",
            "completion": f"Completion {index}",
        }
        for index in range(10)
    ]


def test_calibration_sheet_has_blank_human_scores(tmp_path: Path) -> None:
    path = write_calibration(_rows(), tmp_path / "calibration.md", "run-1")
    text = path.read_text(encoding="utf-8")
    assert text.count("Human score:\n") == 10
    assert "Task prompts are intentionally excluded." in text
    with pytest.raises(ValueError, match="missing score"):
        read_calibration(path)


def test_calibration_read_computes_within_one_point(tmp_path: Path) -> None:
    path = write_calibration(_rows(), tmp_path / "calibration.md", "run-1")
    text = path.read_text(encoding="utf-8")
    scores = iter(["4", "5", "3", "4", "4", "5", "3", "4", "2", "1"])
    for score in scores:
        text = text.replace("Human score:\n", f"Human score: {score}\n", 1)
    path.write_text(text, encoding="utf-8")
    result = read_calibration(path)
    assert result["agreement_count"] == 8
    assert result["status"] == "pass"
