"""Load private JSONL task records without exposing them outside the harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import Sample


ROOT = Path(__file__).resolve().parents[3]


def records(area: str) -> list[dict[str, Any]]:
    folder = ROOT / "tasks" / "anchor" / area
    loaded = []
    for path in sorted(folder.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            loaded.extend(json.loads(line) for line in handle if line.strip())
    return loaded


def samples(area: str) -> list[Sample]:
    result = []
    for record in records(area):
        fixture_parts = []
        for relative in record["metadata"].get("files", []):
            path = ROOT / "tasks" / relative
            fixture_parts.append(f"\n\nFILE: {relative}\n{path.read_text(encoding='utf-8')}")
        metadata = {**record["metadata"], "item_version": record["version"]}
        result.append(Sample(id=record["id"], input=record["input"] + "".join(fixture_parts),
                             target=record["target"], metadata=metadata))
    return result
