"""Offline dashboard and private-run report renderer."""

from __future__ import annotations

import html
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from modelwatch.external.common import ROOT, existing_rows

STATIC = ROOT / "src" / "modelwatch" / "static"
REPORTS = ROOT / "reports"
AREA_NAMES = {
    "hub_edits": "Hub edits",
    "injection": "Prompt injection",
    "voice": "Voice",
    "dutch": "Dutch precision",
    "coding": "Agentic coding",
    "skills": "Skill following",
}


def _se(values: list[float]) -> float:
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0


def _is_scored_result(row: dict[str, Any]) -> bool:
    return "sample_error:" not in str(row.get("notes") or "")


def area_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute model-area means and SE across repeat-level area means."""
    samples: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for row in rows:
        if not _is_scored_result(row):
            continue
        samples[(row["area"], row["model_snapshot"], int(row["repeat"]))].append(
            float(row["score"])
        )
    repeats: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (area, model, _repeat), scores in samples.items():
        repeats[(area, model)].append(statistics.mean(scores))
    return [
        {
            "area": area,
            "model_snapshot": model,
            "mean": statistics.mean(values),
            "se": _se(values),
            "n_repeats": len(values),
        }
        for (area, model), values in sorted(repeats.items())
    ]


def coverage_summary(
    rows: list[dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, Any]:
    """Summarize observed coverage against the fullest model-area evidence."""
    scored_rows = [row for row in rows if _is_scored_result(row)]
    counts = Counter((row["model_snapshot"], row["area"]) for row in scored_rows)
    areas = sorted({row["area"] for row in rows})
    expected_by_area = {
        area: max(
            (count for (model, candidate), count in counts.items() if candidate == area),
            default=0,
        )
        for area in areas
    }
    manifest_models = [model["snapshot"] for model in manifest.get("models", [])]
    models = manifest_models or sorted({row["model_snapshot"] for row in rows})
    expected_per_model = sum(expected_by_area.values())
    model_rows = [
        {
            "model_snapshot": model,
            "observed": sum(counts[(model, area)] for area in areas),
            "expected": expected_per_model,
        }
        for model in models
    ]
    observed = len(scored_rows)
    expected = expected_per_model * len(models)
    complete = manifest.get("status") == "complete" and observed == expected
    return {
        "recorded": len(rows),
        "excluded": len(rows) - observed,
        "observed": observed,
        "expected": expected,
        "complete": complete,
        "models": model_rows,
    }


def paired_differences(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute per-item paired differences when exactly two models are supplied."""
    models = sorted({row["model_snapshot"] for row in rows})
    if len(models) != 2:
        return []
    values = {
        (row["task_id"], row["model_snapshot"], int(row["repeat"])): float(row["score"])
        for row in rows
        if _is_scored_result(row)
    }
    result = []
    for task_id in sorted({row["task_id"] for row in rows}):
        repeats = sorted({repeat for item, _model, repeat in values if item == task_id})
        differences = [
            values[(task_id, models[0], repeat)] - values[(task_id, models[1], repeat)]
            for repeat in repeats
            if (task_id, models[0], repeat) in values
            and (task_id, models[1], repeat) in values
        ]
        if differences:
            difference = statistics.mean(differences)
            se = _se(differences)
            result.append(
                {
                    "task_id": task_id,
                    "model_a": models[0],
                    "model_b": models[1],
                    "difference": difference,
                    "se": se,
                    "larger_than_one_se": abs(difference) > se,
                    "n_pairs": len(differences),
                }
            )
    return result


def paired_area_differences(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare the two highest-mean models in each area, paired by repeat."""
    stats = area_statistics(rows)
    result: list[dict[str, Any]] = []
    for area in sorted({row["area"] for row in rows}):
        ranked = sorted(
            (row for row in stats if row["area"] == area),
            key=lambda row: (-row["mean"], row["model_snapshot"]),
        )
        if len(ranked) < 2:
            continue
        model_a, model_b = ranked[0]["model_snapshot"], ranked[1]["model_snapshot"]
        repeat_scores: dict[tuple[str, int], list[float]] = defaultdict(list)
        for row in rows:
            if (
                _is_scored_result(row)
                and row["area"] == area
                and row["model_snapshot"] in {model_a, model_b}
            ):
                repeat_scores[(row["model_snapshot"], int(row["repeat"]))].append(
                    float(row["score"])
                )
        repeats = sorted(
            {repeat for model, repeat in repeat_scores if model == model_a}
            & {repeat for model, repeat in repeat_scores if model == model_b}
        )
        differences = [
            statistics.mean(repeat_scores[(model_a, repeat)])
            - statistics.mean(repeat_scores[(model_b, repeat)])
            for repeat in repeats
        ]
        if differences:
            difference = statistics.mean(differences)
            se = _se(differences)
            result.append(
                {
                    "area": area,
                    "model_a": model_a,
                    "model_b": model_b,
                    "difference": difference,
                    "se": se,
                    "larger_than_one_se": abs(difference) > se,
                    "n_pairs": len(differences),
                }
            )
    return result


def _dot_whisker(area: str, rows: list[dict[str, Any]]) -> str:
    ranked = sorted(rows, key=lambda row: (-row["mean"], row["model_snapshot"]))
    width, left, plot_width, row_height = 960, 360, 560, 30
    height = 55 + row_height * len(ranked)
    marks = []
    for index, row in enumerate(ranked):
        y = 42 + index * row_height
        low = max(0.0, row["mean"] - row["se"])
        high = min(1.0, row["mean"] + row["se"])
        x, x1, x2 = (left + plot_width * value for value in (row["mean"], low, high))
        label = html.escape(row["model_snapshot"])
        marks.append(
            f"<text x='0' y='{y + 5}'>{label}</text>"
            f"<line x1='{x1:.1f}' x2='{x2:.1f}' y1='{y}' y2='{y}' class='whisker'/>"
            f"<line x1='{x1:.1f}' x2='{x1:.1f}' y1='{y - 5}' y2='{y + 5}' class='whisker'/>"
            f"<line x1='{x2:.1f}' x2='{x2:.1f}' y1='{y - 5}' y2='{y + 5}' class='whisker'/>"
            f"<circle cx='{x:.1f}' cy='{y}' r='5'/><text x='{x + 9:.1f}' y='{y + 5}' "
            f"class='value'>{row['mean']:.3f}</text>"
        )
    ticks = "".join(
        f"<line x1='{left + plot_width * tick / 4}' x2='{left + plot_width * tick / 4}' "
        f"y1='20' y2='{height - 10}' class='grid'/><text x='{left + plot_width * tick / 4}' "
        f"y='15' text-anchor='middle'>{tick / 4:.2f}</text>"
        for tick in range(5)
    )
    return (
        f"<section><h3>{html.escape(AREA_NAMES.get(area, area))}</h3>"
        f"<svg viewBox='0 0 {width} {height}' role='img' "
        f"aria-label='{html.escape(AREA_NAMES.get(area, area))} mean and standard error'>"
        f"{ticks}{''.join(marks)}</svg></section>"
    )


def _run_manifest(run_id: str) -> dict[str, Any]:
    path = ROOT / "runs" / run_id / "run.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _what_moved(all_private: list[dict[str, Any]], selected_id: str) -> list[str]:
    ids = list(dict.fromkeys(row["run_id"] for row in all_private))
    selected_rows = [row for row in all_private if row["run_id"] == selected_id]
    selected_areas = {row["area"] for row in selected_rows}
    selected_models = {row["model_snapshot"] for row in selected_rows}
    eligible = []
    for candidate in ids:
        candidate_rows = [row for row in all_private if row["run_id"] == candidate]
        if (
            candidate != selected_id
            and ids.index(candidate) < ids.index(selected_id)
            and {row["area"] for row in candidate_rows} == selected_areas == set(AREA_NAMES)
            and {row["model_snapshot"] for row in candidate_rows} == selected_models
        ):
            eligible.append(candidate)
    if selected_id not in ids or not eligible:
        return []
    previous_id = eligible[-1]
    current = {(row["area"], row["model_snapshot"]): row for row in area_statistics(
        [row for row in all_private if row["run_id"] == selected_id]
    )}
    previous = {(row["area"], row["model_snapshot"]): row for row in area_statistics(
        [row for row in all_private if row["run_id"] == previous_id]
    )}
    changes = []
    for key in current.keys() & previous.keys():
        delta = current[key]["mean"] - previous[key]["mean"]
        changes.append((abs(delta), key, delta))
    return [
        f"{AREA_NAMES.get(area, area)}, {model}: {delta:+.3f}"
        for _absolute, (area, model), delta in sorted(changes, reverse=True)[:5]
    ]


def render_run_report(run_id: str | None = None, output: Path | None = None) -> str:
    all_rows = existing_rows()
    private = [
        row for row in all_rows
        if row.get("source") == "private" and row.get("area") in AREA_NAMES
    ]
    if not private:
        raise ValueError("no private anchor runs found")
    selected_id = run_id or private[-1]["run_id"]
    rows = [row for row in private if row["run_id"] == selected_id]
    if not rows:
        raise ValueError(f"run not found: {selected_id}")
    manifest = _run_manifest(selected_id)
    coverage = coverage_summary(rows, manifest)
    stats = area_statistics(rows)
    charts = "".join(
        _dot_whisker(area, [row for row in stats if row["area"] == area])
        for area in AREA_NAMES
        if any(row["area"] == area for row in stats)
    )
    pairs = paired_area_differences(rows)
    pair_rows = "".join(
        f"<tr><td>{html.escape(AREA_NAMES.get(row['area'], row['area']))}</td>"
        f"<td>{html.escape(row['model_a'])}</td><td>{html.escape(row['model_b'])}</td>"
        f"<td>{row['difference']:+.4f}</td><td>{row['se']:.4f}</td>"
        f"<td>{'yes' if row['larger_than_one_se'] else 'no'}</td>"
        f"<td>{row['n_pairs']}</td></tr>"
        for row in pairs
    )
    model_totals: dict[str, dict[str, float]] = {}
    for model in manifest.get("models", []):
        model_totals[model["snapshot"]] = {
            "cost": float(model.get("cost_eur") or 0.0),
            "wall": float(model.get("wall_s") or 0.0),
        }
    if not model_totals:
        model_totals = defaultdict(lambda: {"cost": 0.0, "wall": 0.0})
        for row in rows:
            model_totals[row["model_snapshot"]]["cost"] += float(row.get("cost_eur") or 0.0)
            model_totals[row["model_snapshot"]]["wall"] += float(row.get("wall_s") or 0.0)
    cost_rows = "".join(
        f"<tr><td>{html.escape(model)}</td><td>{values['cost']:.4f}</td>"
        f"<td>{values['wall']:.1f}</td></tr>"
        for model, values in sorted(model_totals.items())
    )
    coverage_rows = "".join(
        f"<tr><td>{html.escape(row['model_snapshot'])}</td>"
        f"<td>{row['observed']}</td><td>{row['expected']}</td>"
        f"<td>{'complete' if row['observed'] == row['expected'] else 'partial'}</td></tr>"
        for row in coverage["models"]
    )
    latest_external: dict[tuple[str, str], dict[str, Any]] = {}
    for row in (row for row in all_rows if row.get("source") == "external"):
        key = (row["task_id"], row["model_snapshot"])
        if key not in latest_external or row["run_date"] >= latest_external[key]["run_date"]:
            latest_external[key] = row
    external_rows = "".join(
        f"<tr><td>{html.escape(' '.join(str(row['task_id']).split()))}</td>"
        f"<td>{html.escape(' '.join(str(row['model_snapshot']).split()))}</td>"
        f"<td>{html.escape(str(row['run_date']))}</td><td>{float(row['score']):.4f}</td></tr>"
        for row in sorted(latest_external.values(), key=lambda item: (item["task_id"], item["model_snapshot"]))
    )
    moved = "".join(f"<li>{html.escape(item)}</li>" for item in _what_moved(private, selected_id))
    inspect_versions = ", ".join(sorted({str(row.get("inspect_version")) for row in rows}))
    task_versions = ", ".join(sorted({str(row.get("taskset_version")) for row in rows}))
    roster_dates = ", ".join(sorted({str(row.get("roster_date")) for row in rows}))
    guard = manifest.get("guard_status", "unknown")
    status = manifest.get("status", "unknown")
    error = str(manifest.get("error") or "").strip()
    warning = ""
    if not coverage["complete"]:
        detail = f" Run error: {html.escape(error)}." if error else ""
        warning = (
            "<div class='warning'><strong>Incomplete run.</strong> "
            f"The store contains {coverage['recorded']} recorded samples; "
            f"{coverage['observed']} usable scores are included and {coverage['excluded']} "
            f"sample errors are excluded. The plan expected {coverage['expected']} samples."
            f"{detail} Rankings and paired differences are provisional.</div>"
        )
    document = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>Modelwatch private run {html.escape(selected_id)}</title><style>
body{{font:15px system-ui;max-width:1500px;margin:2rem auto;color:#18202a}}h1,h2,h3{{line-height:1.2}}
.columns{{display:grid;grid-template-columns:minmax(0,2fr) minmax(320px,1fr);gap:2rem;align-items:start}}
.columns>*{{min-width:0}}.table-scroll{{max-width:100%;overflow:auto}}.table-scroll.external{{max-height:70vh}}
table{{border-collapse:collapse;width:max-content;min-width:100%}}td,th{{padding:.4rem .6rem;border-bottom:1px solid #d8dde3;text-align:left}}
svg{{display:block;width:100%;max-width:100%;min-height:180px;overflow:hidden}}svg text{{font:12px system-ui}}circle{{fill:#176b87}}.whisker{{stroke:#176b87;stroke-width:2}}
.grid{{stroke:#e4e8ec;stroke-width:1}}.value{{fill:#334}}.warning{{background:#fff4d6;border-left:5px solid #b96d00;padding:1rem;margin:1rem 0}}
footer{{margin-top:3rem;border-top:1px solid #bbc3cc;padding-top:1rem}}
@media(max-width:900px){{.columns{{grid-template-columns:1fr}}}}
</style></head><body><h1>Private run {html.escape(selected_id)}</h1>{warning}
<div class='columns'><main><h2>Private means and standard errors</h2>{charts}</main>
<aside><h2>Latest external values</h2><div class='table-scroll external'><table><thead><tr><th>Series</th><th>Model</th><th>Date</th><th>Value</th></tr></thead>
<tbody>{external_rows}</tbody></table></div></aside></div>
<h2>Paired difference between the top two models per area</h2><div class='table-scroll'><table><thead><tr><th>Area</th><th>First</th><th>Second</th>
<th>Difference</th><th>SE</th><th>Above one SE</th><th>Pairs</th></tr></thead><tbody>{pair_rows}</tbody></table></div>
<h2>Coverage</h2><div class='table-scroll'><table><thead><tr><th>Model</th><th>Observed</th><th>Expected</th><th>Status</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>
<h2>Cost and wall time</h2><div class='table-scroll'><table><thead><tr><th>Model</th><th>EUR</th><th>Wall seconds</th></tr></thead><tbody>{cost_rows}</tbody></table></div>
<h2>What moved</h2><ul>{moved}</ul>
<footer>Inspect {html.escape(inspect_versions)} | task set {html.escape(task_versions)} | roster {html.escape(roster_dates)} | run {html.escape(str(status))} | guard {html.escape(str(guard))}</footer>
</body></html>"""
    destination = output or REPORTS / f"{selected_id}.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    return str(destination)


def render_post_draft(run_id: str | None = None, output: Path | None = None) -> str:
    private = [
        row for row in existing_rows()
        if row.get("source") == "private" and row.get("area") in AREA_NAMES
    ]
    if not private:
        raise ValueError("no private anchor runs found")
    selected_id = run_id or private[-1]["run_id"]
    rows = [row for row in private if row["run_id"] == selected_id]
    pairs = sorted(paired_area_differences(rows), key=lambda row: abs(row["difference"]), reverse=True)
    observations = []
    for row in pairs[:3]:
        observations.append(
            f"- {AREA_NAMES.get(row['area'], row['area'])}: {row['model_a']} led "
            f"{row['model_b']} by {abs(row['difference']):.3f}, with SE {row['se']:.3f}."
        )
    manifest = _run_manifest(selected_id)
    coverage = coverage_summary(rows, manifest)
    costs: dict[str, float] = defaultdict(float)
    for row in rows:
        costs[row["model_snapshot"]] += float(row.get("cost_eur") or 0.0)
    total_cost = float(manifest.get("cost_eur") or sum(costs.values()))
    cheapest = min(costs.items(), key=lambda item: item[1]) if costs else ("unknown", 0.0)
    if not coverage["complete"]:
        caveat = (
            f"The run ended with status {manifest.get('status', 'unknown')} and contains "
            f"{coverage['observed']} usable scores from {coverage['recorded']} recorded samples, "
            f"against {coverage['expected']} expected. All comparisons are provisional."
        )
        cost_observation = f"The interrupted run recorded EUR {total_cost:.2f}."
    else:
        caveat = "Five repeats leave meaningful uncertainty around close results. Treat gaps within one SE as unresolved."
        cost_observation = (
            f"The run cost EUR {total_cost:.2f}. The lowest-cost model was "
            f"{cheapest[0]} at EUR {cheapest[1]:.2f}."
        )
    text = (
        f"# Modelwatch run {selected_id}\n\n"
        "The clearest differences were:\n\n"
        + "\n".join(observations)
        + f"\n\n{cost_observation}\n\n"
        + f"Caveat: {caveat}\n"
    )
    run_date = rows[0]["run_date"] if rows else selected_id[:8]
    destination = output or REPORTS / f"post_draft_{run_date}.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return str(destination)


def render_dashboard(output: Path = REPORTS / "dashboard.html") -> str:
    rows = existing_rows()
    external = [row for row in rows if row.get("source") == "external"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in external:
        groups[row["provider"]].append(row)
    charts = []
    scripts = []
    chart_index = 0
    for source in ("epoch", "aa", "livebench", "metr"):
        source_rows = groups.get(source, [])
        datasets = []
        for pos, task_id in enumerate(sorted({row["task_id"] for row in source_rows})):
            values = [row for row in source_rows if row["task_id"] == task_id]
            datasets.append({
                "label": task_id,
                "borderColor": f"hsl({(pos * 67) % 360} 65% 40%)",
                "fill": False,
                "data": [{"x": row["run_date"], "y": row["score"]} for row in values],
            })
        charts.append(f'<section><h2>{html.escape(source)}</h2><canvas id="chart{chart_index}"></canvas></section>')
        scripts.append(_chart_script(chart_index, datasets))
        chart_index += 1
    private = [row for row in rows if row.get("source") == "private" and row.get("area") in AREA_NAMES]
    points: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in dict.fromkeys(row["run_id"] for row in private):
        run_rows = [row for row in private if row["run_id"] == run]
        run_date = run_rows[0]["run_date"]
        for stat in area_statistics(run_rows):
            points[(stat["area"], stat["model_snapshot"])].append(
                {"x": run_date, "y": stat["mean"]}
            )
    private_sets = [
        {
            "label": f"{AREA_NAMES.get(area, area)} | {model}",
            "borderColor": f"hsl({(pos * 43) % 360} 65% 40%)",
            "fill": False,
            "data": values,
        }
        for pos, ((area, model), values) in enumerate(sorted(points.items()))
    ]
    charts.append(f'<section><h2>Private areas</h2><canvas id="chart{chart_index}"></canvas></section>')
    scripts.append(_chart_script(chart_index, private_sets))
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in external:
        key = (row["task_id"], row["model_snapshot"])
        if key not in latest or row["run_date"] >= latest[key]["run_date"]:
            latest[key] = row
    table = "".join(
        f"<tr><td>{html.escape(' '.join(str(row['task_id']).split()))}</td>"
        f"<td>{html.escape(' '.join(str(row['model_snapshot']).split()))}</td>"
        f"<td>{html.escape(str(row['run_date']))}</td><td>{row['score']}</td></tr>"
        for row in sorted(latest.values(), key=lambda item: (item["task_id"], item["model_snapshot"]))
    )
    chartjs = (STATIC / "chart.umd.min.js").read_text(encoding="utf-8")
    document = (
        "<!doctype html><html><head><meta charset='utf-8'><title>Modelwatch dashboard</title>"
        "<style>body{font:16px system-ui;max-width:1400px;margin:2rem auto}section{margin:2rem 0}"
        "canvas{min-height:360px}table{border-collapse:collapse}td,th{padding:.35rem .6rem;border-bottom:1px solid #ddd}</style>"
        f"</head><body><h1>Modelwatch dashboard</h1>{''.join(charts)}<h2>Latest external values</h2>"
        f"<table><thead><tr><th>Series</th><th>Model</th><th>Date</th><th>Value</th></tr></thead><tbody>{table}</tbody></table>"
        f"<script>{chartjs}</script><script>{''.join(scripts)}</script></body></html>"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return str(output)


def _chart_script(index: int, datasets: list[dict[str, Any]]) -> str:
    return (
        f"new Chart(document.getElementById('chart{index}'),"
        f"{{type:'line',data:{{datasets:{json.dumps(datasets)}}},options:{{parsing:false,"
        "plugins:{legend:{position:'right'}},scales:{x:{type:'category'},y:{beginAtZero:false}}}}});"
    )
