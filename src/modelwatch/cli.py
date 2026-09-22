"""Command line interface for modelwatch."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("LOCALAPPDATA", str(ROOT / ".local-appdata"))
os.environ.setdefault("INSPECT_TRACE_FILE", str(ROOT / ".inspect-trace.log"))

from inspect_ai import eval as inspect_eval

from modelwatch.flatten import flatten_run
from modelwatch.external import aa, epoch, livebench, metr


app = typer.Typer(no_args_is_help=True)
RUNS_DIR = ROOT / "runs"
RESULTS_DIR = ROOT / "results"
os.environ.setdefault("INSPECT_LOG_DIR", str(RUNS_DIR))


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _latest_run_folder() -> Path:
    folders = [path for path in RUNS_DIR.iterdir() if path.is_dir()]
    if not folders:
        raise typer.BadParameter("no run folders found")
    return max(folders, key=lambda path: path.stat().st_mtime)


@app.command()
def run(
    task: str = typer.Option(..., "--task"),
    roster: Path = typer.Option(Path("config/roster.yaml"), "--roster"),
    repeats: int | None = typer.Option(None, "--repeats", min=1),
) -> None:
    """Run one task against every model in a roster."""
    task_files = {
        "hello": [(Path("tasks") / "hello.py", "hello")],
        "hub_edits": [(Path("src/modelwatch/tasks/hub_edits.py"), "hub_edits")],
        "injection": [(Path("src/modelwatch/tasks/injection.py"), "injection")],
        "anchor": [
            (Path("src/modelwatch/tasks/hub_edits.py"), "hub_edits"),
            (Path("src/modelwatch/tasks/injection.py"), "injection"),
        ],
    }
    if task not in task_files:
        raise typer.BadParameter("task must be hello, hub_edits, injection, or anchor")
    roster_path = roster if roster.is_absolute() else ROOT / roster
    roster_data = _load_yaml(roster_path)
    key_by_provider = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    missing_keys = sorted(
        {
            key_by_provider[entry["provider"]]
            for entry in roster_data["models"]
            if entry["provider"] in key_by_provider
            and not os.environ.get(key_by_provider[entry["provider"]])
        }
    )
    if missing_keys:
        raise typer.BadParameter(
            "missing environment variables: " + ", ".join(missing_keys)
        )
    if any(entry["provider"] == "anthropic" for entry in roster_data["models"]):
        if not os.environ.get("ANTHROPIC_WORKSPACE_ID"):
            raise typer.BadParameter("missing environment variable: ANTHROPIC_WORKSPACE_ID")
    taskset_version = (ROOT / "tasks" / "VERSION").read_text(encoding="utf-8").strip()
    defaults = roster_data["defaults"]
    run_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    run_folder = RUNS_DIR / run_id
    run_folder.mkdir(parents=True, exist_ok=False)

    for entry in roster_data["models"]:
        for task_file, area in task_files[task]:
            model_args: dict[str, Any] = {}
            if entry["provider"] == "openrouter":
                model_args["provider"] = {
                    "only": [entry["upstream_provider"]],
                    "allow_fallbacks": False,
                }
            extra_headers = None
            if entry["provider"] == "anthropic":
                extra_headers = {
                    "anthropic-workspace-id": os.environ["ANTHROPIC_WORKSPACE_ID"]
                }
            inspect_eval(
                tasks=str(task_file),
                model=entry["snapshot"],
                model_args=model_args,
                metadata={
                    "modelwatch_run_id": run_id,
                    "taskset_version": taskset_version,
                    "roster_date": str(roster_data["date"]),
                    "area": area,
                    "provider": entry["provider"],
                    "upstream_provider": entry.get("upstream_provider"),
                    "endpoint": entry.get("endpoint"),
                    "effort": entry.get("effort"),
                },
                log_dir=str(run_folder),
                log_format="eval",
                display="plain",
                epochs=repeats or int(defaults["repeats"]),
                temperature=float(defaults["temperature"]),
                seed=int(defaults["seed"]),
                token_limit=int(defaults["token_limit_per_sample"]),
                time_limit=int(defaults["time_limit_s"]),
                effort=entry.get("effort") if entry["provider"] != "anthropic" else None,
                extra_headers=extra_headers,
            )
    typer.echo(str(run_folder))


@app.command("import")
def import_data(all_sources: bool = typer.Option(False, "--all")) -> None:
    """Import public benchmark data."""
    if not all_sources:
        raise typer.BadParameter("Step 2 requires --all")
    if not os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY"):
        raise typer.BadParameter("ARTIFICIAL_ANALYSIS_API_KEY is not set; restart the terminal after setting it")
    added = []
    for name, importer in (("epoch", epoch.import_rows), ("aa", aa.import_rows),
                           ("livebench", livebench.import_rows), ("metr", metr.import_rows)):
        rows = importer()
        added.extend(rows)
        typer.echo(f"{name}: added {len(rows)} rows")
    typer.echo(f"total added {len(added)} rows")


@app.command()
def flatten(run_folder: Path | None = typer.Option(None, "--run-folder")) -> None:
    """Append a run folder to NDJSON and rebuild SQLite."""
    folder = run_folder or _latest_run_folder()
    folder = folder if folder.is_absolute() else ROOT / folder
    rows = flatten_run(
        folder,
        RESULTS_DIR / "results.ndjson",
        RESULTS_DIR / "results.sqlite",
    )
    typer.echo(f"added {len(rows)} rows")


@app.command()
def report(
    dashboard: bool = typer.Option(False, "--dashboard"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Render the dashboard or a private run report."""
    from modelwatch.report import render_dashboard, render_run_report
    typer.echo(render_dashboard() if dashboard else render_run_report(run_id=run_id))


@app.command()
def selftest(
    roster: Path = typer.Option(Path("config/roster.yaml"), "--roster"),
    tasks: bool = typer.Option(False, "--tasks"),
) -> None:
    """Check the Step 1 configuration and result stores."""
    errors: list[str] = []
    roster_path = roster if roster.is_absolute() else ROOT / roster
    roster_text = roster_path.read_text(encoding="utf-8")
    if "VERIFY" in roster_text:
        errors.append("roster contains VERIFY")

    ndjson_path = RESULTS_DIR / "results.ndjson"
    rows: list[dict[str, Any]] = []
    if ndjson_path.exists():
        try:
            rows = [json.loads(line) for line in ndjson_path.read_text(encoding="utf-8").splitlines() if line]
        except json.JSONDecodeError as exc:
            errors.append(f"results.ndjson does not parse: {exc}")

    sqlite_path = RESULTS_DIR / "results.sqlite"
    sqlite_count = 0
    if sqlite_path.exists():
        try:
            with sqlite3.connect(sqlite_path) as connection:
                sqlite_count = connection.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        except sqlite3.Error as exc:
            errors.append(f"results.sqlite is invalid: {exc}")
    elif rows:
        errors.append("results.sqlite is missing")
    if sqlite_count != len(rows):
        errors.append(f"store counts differ: ndjson={len(rows)}, sqlite={sqlite_count}")

    log_dir = Path(os.environ["INSPECT_LOG_DIR"]).resolve()
    try:
        log_dir.relative_to(RUNS_DIR.resolve())
    except ValueError:
        errors.append("INSPECT_LOG_DIR is outside runs")

    task_count = 0
    if tasks:
        from modelwatch.scorers.deterministic import score_completion
        from modelwatch.tasks.common import records

        for area in ("hub_edits", "injection"):
            for record in records(area):
                task_count += 1
                metadata = record["metadata"]
                good, good_details = score_completion(metadata["known_good"], metadata)
                bad, bad_details = score_completion(metadata["known_bad"], metadata)
                if good != 1.0:
                    errors.append(f"{record['id']} known_good={good}: {good_details}")
                if bad >= 0.5:
                    errors.append(f"{record['id']} known_bad={bad}: {bad_details}")
        if task_count != 12:
            errors.append(f"expected 12 anchor tasks, found {task_count}")

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)
    suffix = f", {task_count} task pairs" if tasks else ""
    typer.echo(f"ok: {len(rows)} result rows{suffix}")


@app.command()
def roster(
    path: Path = typer.Option(Path("config/roster.yaml"), "--path"),
) -> None:
    """Show the dated model roster."""
    roster_path = path if path.is_absolute() else ROOT / path
    data = _load_yaml(roster_path)
    typer.echo(f"date: {data['date']}")
    for model in data["models"]:
        typer.echo(model["snapshot"])
