"""Shared storage helpers for public series importers."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from modelwatch.flatten import RESULT_COLUMNS, _rebuild_sqlite

ROOT = Path(__file__).resolve().parents[3]
NDJSON = ROOT / "results" / "results.ndjson"
SQLITE = ROOT / "results" / "results.sqlite"


def existing_rows(path: Path = NDJSON) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def external_row(
    source: str, series: str, model: str, score: float, published: str,
    endpoint: str, notes: str,
) -> dict[str, Any]:
    day = date.today().isoformat()
    return {
        "run_id": f"external-{source}-{day}", "run_date": published or day,
        "source": "external", "inspect_version": None, "taskset_version": "external",
        "roster_date": None, "task_id": f"{source}.{series}", "task_version": "1",
        "area": "external", "model_snapshot": str(model), "provider": source,
        "upstream_provider": None, "endpoint": endpoint, "effort": None,
        "temperature": None, "seed": None, "repeat": 0, "score": float(score),
        "pass": None, "tokens_in": 0, "tokens_out": 0, "tokens_reasoning": 0,
        "cost_eur": 0.0, "wall_s": 0.0, "judge_model": None, "notes": notes,
    }


def append_rows(rows: Iterable[dict[str, Any]], ndjson: Path = NDJSON, sqlite: Path = SQLITE) -> list[dict[str, Any]]:
    old = existing_rows(ndjson)
    keys = {(r["run_id"], r["task_id"], r["model_snapshot"], r["repeat"]) for r in old}
    added = []
    for row in rows:
        key = (row["run_id"], row["task_id"], row["model_snapshot"], row["repeat"])
        if key not in keys:
            keys.add(key)
            added.append(row)
    if added:
        ndjson.parent.mkdir(parents=True, exist_ok=True)
        with ndjson.open("a", encoding="utf-8", newline="\n") as handle:
            for row in added:
                handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
    _rebuild_sqlite(sqlite, old + added)
    return added
