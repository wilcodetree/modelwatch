"""Offline dashboard renderer for external series."""

from __future__ import annotations

import html
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from modelwatch.external.common import NDJSON, ROOT, existing_rows

STATIC = ROOT / "src" / "modelwatch" / "static"
REPORTS = ROOT / "reports"


def _se(values: list[float]) -> float:
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0


def area_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute model-area means and SE across repeat-level area means."""
    samples: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for row in rows:
        samples[(row["area"], row["model_snapshot"], int(row["repeat"]))].append(float(row["score"]))
    repeats: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (area, model, _repeat), scores in samples.items():
        repeats[(area, model)].append(statistics.mean(scores))
    return [
        {"area": area, "model_snapshot": model, "mean": statistics.mean(values),
         "se": _se(values), "n_repeats": len(values)}
        for (area, model), values in sorted(repeats.items())
    ]


def paired_differences(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute paired model differences per item, pairing on repeat number."""
    models = sorted({row["model_snapshot"] for row in rows})
    if len(models) != 2:
        return []
    values = {(row["task_id"], row["model_snapshot"], int(row["repeat"])): float(row["score"])
              for row in rows}
    task_ids = sorted({row["task_id"] for row in rows})
    result = []
    for task_id in task_ids:
        repeats = sorted({repeat for item, _model, repeat in values if item == task_id})
        differences = [values[(task_id, models[0], repeat)] - values[(task_id, models[1], repeat)]
                       for repeat in repeats
                       if (task_id, models[0], repeat) in values and (task_id, models[1], repeat) in values]
        if not differences:
            continue
        difference = statistics.mean(differences)
        se = _se(differences)
        result.append({"task_id": task_id, "model_a": models[0], "model_b": models[1],
                       "difference": difference, "se": se,
                       "larger_than_one_se": abs(difference) > se,
                       "n_pairs": len(differences)})
    return result


def render_run_report(run_id: str | None = None, output: Path | None = None) -> str:
    private = [row for row in existing_rows() if row.get("source") == "private" and row.get("area") in {"hub_edits", "injection"}]
    if not private:
        raise ValueError("no private anchor runs found")
    selected_id = run_id or private[-1]["run_id"]
    rows = [row for row in private if row["run_id"] == selected_id]
    if not rows:
        raise ValueError(f"run not found: {selected_id}")
    area_rows = "".join(
        f"<tr><td>{html.escape(row['area'])}</td><td>{html.escape(row['model_snapshot'])}</td>"
        f"<td>{row['mean']:.4f}</td><td>{row['se']:.4f}</td><td>{row['n_repeats']}</td></tr>"
        for row in area_statistics(rows)
    )
    pair_rows = "".join(
        f"<tr><td>{html.escape(row['task_id'])}</td><td>{row['difference']:.4f}</td>"
        f"<td>{row['se']:.4f}</td><td>{'yes' if row['larger_than_one_se'] else 'no'}</td>"
        f"<td>{row['n_pairs']}</td></tr>" for row in paired_differences(rows)
    )
    document = (
        "<!doctype html><html><head><meta charset='utf-8'><title>Modelwatch private run</title>"
        "<style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}table{border-collapse:collapse}"
        "td,th{padding:.4rem .7rem;border-bottom:1px solid #ddd;text-align:left}</style></head><body>"
        f"<h1>Private run {html.escape(selected_id)}</h1><h2>Area means with standard errors</h2>"
        "<table><thead><tr><th>Area</th><th>Model</th><th>Mean</th><th>SE</th><th>Repeats</th></tr></thead>"
        f"<tbody>{area_rows}</tbody></table><h2>Paired differences by item</h2>"
        "<table><thead><tr><th>Item</th><th>Difference</th><th>SE</th><th>Above one SE</th><th>Pairs</th></tr></thead>"
        f"<tbody>{pair_rows}</tbody></table></body></html>"
    )
    destination = output or REPORTS / f"{selected_id}.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    return str(destination)


def render_dashboard(output: Path = REPORTS / "dashboard.html") -> str:
    rows = [row for row in existing_rows() if row.get("source") == "external"]
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["provider"], []).append(row)
    order = ["epoch", "aa", "livebench", "metr"]
    charts = []
    scripts = []
    for index, source in enumerate(order):
        source_rows = groups.get(source, [])
        series = sorted({row["task_id"] for row in source_rows})
        datasets = []
        for pos, task_id in enumerate(series):
            values = [row for row in source_rows if row["task_id"] == task_id]
            datasets.append({"label": task_id, "borderColor": f"hsl({(pos * 67) % 360} 65% 40%)",
                "fill": False, "data": [{"x": row["run_date"], "y": row["score"]} for row in values]})
        charts.append(f'<section><h2>{html.escape(source)}</h2><canvas id="chart{index}"></canvas></section>')
        scripts.append(f"new Chart(document.getElementById('chart{index}'), {{type:'line',data:{{datasets:{json.dumps(datasets)}}},options:{{parsing:false,plugins:{{legend:{{position:'right'}}}},scales:{{x:{{type:'category'}},y:{{beginAtZero:false}}}}}}}});")
    latest: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["task_id"], row["model_snapshot"])
        if key not in latest or row["run_date"] >= latest[key]["run_date"]:
            latest[key] = row
    table = "".join(f"<tr><td>{html.escape(row['task_id'])}</td><td>{html.escape(row['model_snapshot'])}</td><td>{row['run_date']}</td><td>{row['score']}</td></tr>" for row in sorted(latest.values(), key=lambda r: (r['task_id'], r['model_snapshot'])))
    chartjs = (STATIC / "chart.umd.min.js").read_text(encoding="utf-8")
    body = "\n".join(charts) or "<p>No external rows yet.</p>"
    if not any(row.get("source") == "private" for row in existing_rows()):
        body += '<section><h2>Private runs</h2><p>no private runs yet</p></section>'
    document = f"<!doctype html><html><head><meta charset='utf-8'><title>Modelwatch dashboard</title><style>body{{font:16px system-ui;max-width:1400px;margin:2rem auto}}section{{margin:2rem 0}}canvas{{min-height:360px}}table{{border-collapse:collapse}}td,th{{padding:.35rem .6rem;border-bottom:1px solid #ddd}}</style></head><body><h1>Modelwatch external dashboard</h1>{body}<h2>Latest values</h2><table><thead><tr><th>Series</th><th>Model</th><th>Date</th><th>Value</th></tr></thead><tbody>{table}</tbody></table><script>{chartjs}</script><script>{''.join(scripts)}</script></body></html>"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return str(output)
