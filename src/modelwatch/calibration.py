"""Write and read human calibration sheets without exposing task prompts."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from inspect_ai.log import read_eval_log


def _score_data(sample: Any) -> tuple[float, dict[str, Any]]:
    if not sample.scores:
        raise ValueError(f"sample {sample.id} has no judge score")
    score = next(iter(sample.scores.values()))
    metadata = score.metadata or {}
    if "judge_points" not in metadata or "rubric" not in metadata:
        raise ValueError(f"sample {sample.id} was not scored by the Step 4 judge")
    return float(metadata["judge_points"]), metadata


def select_calibration_rows(run_folder: Path) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for eval_path in sorted(run_folder.rglob("*.eval")):
        log = read_eval_log(str(eval_path))
        for sample in log.samples or []:
            points, metadata = _score_data(sample)
            by_task.setdefault(str(sample.id), []).append(
                {
                    "task_id": str(sample.id),
                    "model": log.eval.model,
                    "judge_model": metadata["judge_model"],
                    "judge_score": points,
                    "rubric": metadata["rubric"],
                    "completion": sample.output.completion,
                }
            )
    if len(by_task) != 10:
        raise ValueError(f"expected 10 judged tasks, found {len(by_task)}")
    rows = []
    for index, task_id in enumerate(sorted(by_task)):
        candidates = sorted(by_task[task_id], key=lambda row: row["model"])
        rows.append(candidates[index % len(candidates)])
    return rows


def write_calibration(rows: list[dict[str, Any]], path: Path, run_id: str) -> Path:
    lines = [
        "# Modelwatch judge calibration",
        "",
        f"Date: {date.today().isoformat()}",
        f"Run: {run_id}",
        "",
        "Score each completion from 1 to 5 using its rubric. Leave the judge score unchanged.",
        "Task prompts are intentionally excluded.",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## {index}. {row['task_id']}",
                "",
                f"Model: `{row['model']}`",
                f"Judge model: `{row['judge_model']}`",
                f"Judge score: {row['judge_score']:.2f}",
                "Human score:",
                "",
                f"Rubric: {row['rubric']}",
                "",
                "Completion:",
                "",
                "````text",
                row["completion"],
                "````",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def read_calibration(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^## \d+\. ", text)[1:]
    if len(blocks) != 10:
        raise ValueError(f"expected 10 calibration items, found {len(blocks)}")
    items = []
    for block in blocks:
        task_id = block.splitlines()[0].strip()
        judge_match = re.search(r"(?m)^Judge score:\s*([1-5](?:\.\d+)?)\s*$", block)
        human_match = re.search(r"(?m)^Human score:\s*([1-5](?:\.\d+)?)\s*$", block)
        if not judge_match or not human_match:
            raise ValueError(f"missing score for {task_id}")
        judge_score = float(judge_match.group(1))
        human_score = float(human_match.group(1))
        within_one = abs(judge_score - human_score) <= 1.0
        items.append(
            {
                "task_id": task_id,
                "judge_score": judge_score,
                "human_score": human_score,
                "within_one": within_one,
            }
        )
    agreement_count = sum(item["within_one"] for item in items)
    status = "pass" if agreement_count >= 8 else "rubric_changes_required" if agreement_count < 6 else "recalibrate"
    return {
        "date": date.today().isoformat(),
        "recorded_at": datetime.now().astimezone().isoformat(),
        "calibration_file": str(path.resolve()),
        "agreement_count": agreement_count,
        "item_count": len(items),
        "agreement_rate": agreement_count / len(items),
        "status": status,
        "items": items,
    }


def append_calibration_log(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=True, separators=(",", ":")) + "\n")
