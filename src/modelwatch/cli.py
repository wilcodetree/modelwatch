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
) -> None:
    """Run one task against every model in a roster."""
    if task != "hello":
        raise typer.BadParameter("Step 1 supports only the hello task")
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
            tasks=str(Path("tasks") / "hello.py"),
            model=entry["snapshot"],
            model_args=model_args,
            metadata={
                "modelwatch_run_id": run_id,
                "taskset_version": taskset_version,
                "roster_date": str(roster_data["date"]),
                "area": "hello",
                "provider": entry["provider"],
                "upstream_provider": entry.get("upstream_provider"),
                "endpoint": entry.get("endpoint"),
                "effort": entry.get("effort"),
            },
            log_dir=str(run_folder),
            log_format="eval",
            display="plain",
            epochs=int(defaults["repeats"]),
            temperature=float(defaults["temperature"]),
            seed=int(defaults["seed"]),
            token_limit=int(defaults["token_limit_per_sample"]),
            time_limit=int(defaults["time_limit_s"]),
            effort=entry.get("effort") if entry["provider"] != "anthropic" else None,
            extra_headers=extra_headers,
        )
    typer.echo(str(run_folder))


@app.command("import")
def import_data() -> None:
    """Import public benchmark data in a later step."""
    typer.echo("not in this step")


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
def report() -> None:
    """Render reports in a later step."""
    typer.echo("not in this step")


@app.command()
def selftest(
    roster: Path = typer.Option(Path("config/roster.yaml"), "--roster"),
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

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)
    typer.echo(f"ok: {len(rows)} result rows")


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
