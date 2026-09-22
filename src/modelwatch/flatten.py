"""Flatten Inspect evaluation logs into the modelwatch result stores."""

from __future__ import annotations

import importlib.metadata
import json
import sqlite3
from pathlib import Path
from typing import Any

from inspect_ai.log import EvalLog, EvalSample, read_eval_log


RESULT_COLUMNS = [
    "run_id", "run_date", "source", "inspect_version", "taskset_version",
    "roster_date", "task_id", "task_version", "area", "model_snapshot",
    "provider", "upstream_provider", "endpoint", "effort", "temperature",
    "seed", "repeat", "score", "pass", "tokens_in", "tokens_out",
    "tokens_reasoning", "cost_eur", "wall_s", "judge_model", "notes",
]


def _score_value(sample: EvalSample) -> float:
    if not sample.scores:
        return 0.0
    value = next(iter(sample.scores.values())).value
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    normalized = str(value).strip().upper()
    return 1.0 if normalized in {"C", "CORRECT", "PASS", "TRUE", "1"} else 0.0


def _usage(sample: EvalSample) -> Any | None:
    if not sample.model_usage:
        return None
    return next(iter(sample.model_usage.values()))


def _row(log: EvalLog, sample: EvalSample) -> dict[str, Any]:
    metadata = log.eval.metadata or {}
    usage = _usage(sample)
    score = _score_value(sample)
    model_config = log.eval.model_generate_config
    created = log.eval.created
    run_date = created[:10] if isinstance(created, str) else str(created)[:10]
    return {
        "run_id": metadata.get("modelwatch_run_id", log.eval.run_id),
        "run_date": run_date,
        "source": "private",
        "inspect_version": importlib.metadata.version("inspect-ai"),
        "taskset_version": metadata.get("taskset_version"),
        "roster_date": metadata.get("roster_date"),
        "task_id": str(sample.id),
        "task_version": str((sample.metadata or {}).get("item_version", log.eval.task_version)),
        "area": metadata.get("area", "hello"),
        "model_snapshot": log.eval.model,
        "provider": metadata.get("provider"),
        "upstream_provider": metadata.get("upstream_provider"),
        "endpoint": metadata.get("endpoint"),
        "effort": metadata.get("effort"),
        "temperature": getattr(model_config, "temperature", None),
        "seed": getattr(model_config, "seed", None),
        "repeat": sample.epoch,
        "score": score,
        "pass": score == 1.0,
        "tokens_in": getattr(usage, "input_tokens", 0) or 0,
        "tokens_out": getattr(usage, "output_tokens", 0) or 0,
        "tokens_reasoning": getattr(usage, "reasoning_tokens", 0) or 0,
        "cost_eur": 0.0,
        "wall_s": sample.total_time or 0.0,
        "judge_model": None,
        "notes": "unpriced",
    }


def rows_from_eval(path: Path) -> list[dict[str, Any]]:
    log = read_eval_log(str(path))
    return [_row(log, sample) for sample in (log.samples or [])]


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _rebuild_sqlite(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    definitions = ", ".join(
        f'"{column}" {"REAL" if column in {"score", "cost_eur", "wall_s"} else "INTEGER" if column in {"repeat", "pass", "tokens_in", "tokens_out", "tokens_reasoning", "seed"} else "TEXT"}'
        for column in RESULT_COLUMNS
    )
    placeholders = ", ".join("?" for _ in RESULT_COLUMNS)
    names = ", ".join(f'"{column}"' for column in RESULT_COLUMNS)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE IF EXISTS results")
        connection.execute(
            f"CREATE TABLE results ({definitions}, UNIQUE(run_id, task_id, model_snapshot, repeat))"
        )
        connection.executemany(
            f"INSERT INTO results ({names}) VALUES ({placeholders})",
            [[row.get(column) for column in RESULT_COLUMNS] for row in rows],
        )


def flatten_run(run_folder: Path, ndjson_path: Path, sqlite_path: Path) -> list[dict[str, Any]]:
    existing = _read_ndjson(ndjson_path)
    keys = {
        (row["run_id"], row["task_id"], row["model_snapshot"], row["repeat"])
        for row in existing
    }
    added: list[dict[str, Any]] = []
    for eval_path in sorted(run_folder.rglob("*.eval")):
        for row in rows_from_eval(eval_path):
            key = (row["run_id"], row["task_id"], row["model_snapshot"], row["repeat"])
            if key not in keys:
                keys.add(key)
                added.append(row)
    ndjson_path.parent.mkdir(parents=True, exist_ok=True)
    if added:
        with ndjson_path.open("a", encoding="utf-8", newline="\n") as handle:
            for row in added:
                handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
    _rebuild_sqlite(sqlite_path, existing + added)
    return added
