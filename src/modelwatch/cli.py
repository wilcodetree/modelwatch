"""Command line interface for modelwatch."""

from __future__ import annotations

import json
import os
import sqlite3
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("LOCALAPPDATA", str(ROOT / ".local-appdata"))
os.environ.setdefault("INSPECT_TRACE_FILE", str(ROOT / ".inspect-trace.log"))

from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelCost, get_model_info

from modelwatch.flatten import flatten_run
from modelwatch.external import aa, epoch, livebench, metr
from modelwatch.guard import GuardStop, PriceBook, SpendGuard, eval_log_usages


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
        "voice": [(Path("src/modelwatch/tasks/voice.py"), "voice")],
        "dutch": [(Path("src/modelwatch/tasks/dutch.py"), "dutch")],
        "step4": [
            (Path("src/modelwatch/tasks/voice.py"), "voice"),
            (Path("src/modelwatch/tasks/dutch.py"), "dutch"),
        ],
        "coding": [(Path("src/modelwatch/tasks/coding.py"), "coding")],
        "skills": [(Path("src/modelwatch/tasks/skills.py"), "skills")],
        "step5": [
            (Path("src/modelwatch/tasks/coding.py"), "coding"),
            (Path("src/modelwatch/tasks/skills.py"), "skills"),
        ],
        "anchor": [
            (Path("src/modelwatch/tasks/hub_edits.py"), "hub_edits"),
            (Path("src/modelwatch/tasks/injection.py"), "injection"),
        ],
    }
    if task not in task_files:
        raise typer.BadParameter(
            "task must be hello, hub_edits, injection, voice, dutch, step4, coding, "
            "skills, step5, or anchor"
        )
    roster_path = roster if roster.is_absolute() else ROOT / roster
    roster_data = _load_yaml(roster_path)
    key_by_provider = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
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
    if task in {"voice", "dutch", "step4"}:
        from modelwatch.scorers.judge import judge_for_provider, load_judge_config

        judge_config = load_judge_config()
        judge_providers = {
            judge_for_provider(entry["provider"], judge_config).split("/", 1)[0]
            for entry in roster_data["models"]
        }
        missing_keys.extend(
            key_by_provider[provider]
            for provider in sorted(judge_providers)
            if provider in key_by_provider
            and not os.environ.get(key_by_provider[provider])
            and key_by_provider[provider] not in missing_keys
        )
    if missing_keys:
        raise typer.BadParameter(
            "missing environment variables: " + ", ".join(missing_keys)
        )
    if any(entry["provider"] == "anthropic" for entry in roster_data["models"]) or (
        task in {"voice", "dutch", "step4"} and "anthropic" in judge_providers
    ):
        if not os.environ.get("ANTHROPIC_WORKSPACE_ID"):
            raise typer.BadParameter("missing environment variable: ANTHROPIC_WORKSPACE_ID")
    taskset_version = (ROOT / "tasks" / "VERSION").read_text(encoding="utf-8").strip()
    defaults = roster_data["defaults"]
    settings = tomllib.loads((ROOT / "config" / "settings.toml").read_text(encoding="utf-8"))
    agentic = task in {"coding", "skills", "step5"}
    limits = settings["run"]["coding"] if agentic else defaults
    price_book = PriceBook.load(ROOT / "config" / "prices.yaml")
    spend_guard = SpendGuard(
        float(settings["guard"]["eur_per_run"]),
        price_book,
        max_sample_eur=2.0 if agentic else None,
    )
    model_cost_config = {
        model: ModelCost(
            input=price.input_usd_per_million,
            output=price.output_usd_per_million,
            input_cache_write=price.cache_write_usd_per_million,
            input_cache_read=price.cache_read_usd_per_million,
        )
        for model, price in price_book.models.items()
    }
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
            sample_ids: list[str | None] = [None]
            if agentic:
                from modelwatch.tasks.common import records

                sample_ids = [record["id"] for record in records(area)]
            for sample_id in sample_ids:
                inspect_cost = model_cost_config.get(entry["snapshot"])
                inspect_knows_cost_model = get_model_info(entry["snapshot"]) is not None
                logs = inspect_eval(
                    tasks=str(task_file),
                    model=entry["snapshot"],
                    model_args=model_args,
                    metadata={
                        "modelwatch_run_id": run_id,
                        "taskset_version": taskset_version,
                        "roster_date": str(roster_data["date"]),
                        "price_date": price_book.date,
                        "area": area,
                        "provider": entry["provider"],
                        "upstream_provider": entry.get("upstream_provider"),
                        "endpoint": entry.get("endpoint"),
                        "effort": entry.get("effort"),
                    },
                    log_dir=str(run_folder),
                    log_format="eval",
                    display="plain",
                    sample_id=sample_id,
                    max_samples=1 if agentic else None,
                    sandbox_cleanup=True,
                    epochs=repeats or int(defaults["repeats"]),
                    temperature=float(defaults["temperature"]),
                    seed=int(defaults["seed"]),
                    token_limit=int(limits["token_limit_per_sample"]),
                    time_limit=int(limits["time_limit_s"]),
                    message_limit=int(limits["message_limit"]) if agentic else None,
                    cost_limit=(
                        2.0 / price_book.eur_per_usd
                        if agentic and inspect_knows_cost_model
                        else None
                    ),
                    model_cost_config=(
                        {entry["snapshot"]: inspect_cost}
                        if agentic and inspect_knows_cost_model and inspect_cost
                        else None
                    ),
                    effort=entry.get("effort") if entry["provider"] != "anthropic" else None,
                    extra_headers=extra_headers,
                )
                try:
                    for log in logs:
                        spend_guard.add_sample(eval_log_usages(log))
                except GuardStop as exc:
                    typer.echo(str(exc), err=True)
                    typer.echo(str(run_folder), err=True)
                    raise typer.Exit(3) from exc
    typer.echo(f"{run_folder} EUR {spend_guard.total_eur:.6f}")


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
        from modelwatch.scorers.judge import fixture_score, judge_for_provider, load_judge_config
        from modelwatch.tasks.common import records

        from modelwatch.scorers.agentic import score_coding_patch, score_skill_patch

        for area in ("hub_edits", "injection", "voice", "dutch", "coding", "skills"):
            for record in records(area):
                task_count += 1
                metadata = record["metadata"]
                if area in {"voice", "dutch"}:
                    ratings = metadata["fixture_ratings"]
                    good = fixture_score(metadata["known_good"], metadata, ratings["known_good"])
                    bad = fixture_score(metadata["known_bad"], metadata, ratings["known_bad"])
                    good_details = bad_details = metadata["scorer"]
                elif area in {"hub_edits", "injection"}:
                    good, good_details = score_completion(metadata["known_good"], metadata)
                    bad, bad_details = score_completion(metadata["known_bad"], metadata)
                elif area == "coding":
                    good = score_coding_patch(metadata["known_good"], metadata, ROOT / "tasks")
                    bad = score_coding_patch(metadata["known_bad"], metadata, ROOT / "tasks")
                    good_details = bad_details = metadata["scorer"]
                else:
                    good, good_details = score_skill_patch(metadata["known_good"], metadata)
                    bad, bad_details = score_skill_patch(metadata["known_bad"], metadata)
                if good <= 0.8:
                    errors.append(f"{record['id']} known_good={good}: {good_details}")
                if bad >= 0.4:
                    errors.append(f"{record['id']} known_bad={bad}: {bad_details}")
        if task_count != 30:
            errors.append(f"expected 30 anchor tasks, found {task_count}")
        judge_config = load_judge_config()
        for provider in ("anthropic", "openrouter"):
            try:
                judge_for_provider(provider, judge_config)
            except ValueError as exc:
                errors.append(str(exc))

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)
    suffix = f", {task_count} task pairs" if tasks else ""
    typer.echo(f"ok: {len(rows)} result rows{suffix}")


@app.command()
def calibrate(
    read: bool = typer.Option(False, "--read"),
    path: Path | None = typer.Option(None, "--path"),
    run_folder: Path | None = typer.Option(None, "--run-folder"),
) -> None:
    """Write a calibration sheet or record its completed human scores."""
    from modelwatch.calibration import (
        append_calibration_log,
        read_calibration,
        select_calibration_rows,
        write_calibration,
    )

    calibration_path = path or Path("reports") / f"calibration_{datetime.now().astimezone():%Y-%m-%d}.md"
    calibration_path = calibration_path if calibration_path.is_absolute() else ROOT / calibration_path
    if read:
        result = read_calibration(calibration_path)
        append_calibration_log(result, ROOT / "03_logs" / "calibration.ndjson")
        typer.echo(
            f"agreement: {result['agreement_count']}/{result['item_count']} ({result['status']})"
        )
        if result["agreement_count"] < 8:
            raise typer.Exit(2 if result["agreement_count"] < 6 else 1)
        return

    folder = run_folder or _latest_run_folder()
    folder = folder if folder.is_absolute() else ROOT / folder
    rows = select_calibration_rows(folder)
    typer.echo(str(write_calibration(rows, calibration_path, folder.name)))


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
