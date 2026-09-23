from pathlib import Path
from types import SimpleNamespace

from inspect_ai.scorer import Score

from modelwatch.flatten import RESULT_COLUMNS, _row, flatten_run


FIXTURE = Path(__file__).parent / "fixtures" / "hello.eval"


def test_flattens_eval_fixture(tmp_path: Path) -> None:
    run_folder = tmp_path / "run"
    run_folder.mkdir()
    (run_folder / "hello.eval").write_bytes(FIXTURE.read_bytes())
    ndjson = tmp_path / "results.ndjson"
    sqlite = tmp_path / "results.sqlite"

    rows = flatten_run(run_folder, ndjson, sqlite)

    assert len(rows) == 3
    assert [row["task_id"] for row in rows] == ["hello.1", "hello.2", "hello.3"]
    assert all(list(row) == RESULT_COLUMNS for row in rows)
    assert len(ndjson.read_text(encoding="utf-8").splitlines()) == 3


def test_flatten_is_idempotent_for_same_log(tmp_path: Path) -> None:
    run_folder = tmp_path / "run"
    run_folder.mkdir()
    (run_folder / "hello.eval").write_bytes(FIXTURE.read_bytes())
    ndjson = tmp_path / "results.ndjson"
    sqlite = tmp_path / "results.sqlite"

    assert len(flatten_run(run_folder, ndjson, sqlite)) == 3
    assert flatten_run(run_folder, ndjson, sqlite) == []


def test_judge_metadata_is_flattened() -> None:
    log = SimpleNamespace(
        eval=SimpleNamespace(
            metadata={"modelwatch_run_id": "run", "provider": "anthropic", "area": "voice"},
            run_id="run", created="2026-09-23T00:00:00+02:00", model="anthropic/model",
            model_generate_config=SimpleNamespace(temperature=0.0, seed=1), task_version="1.0.0",
        )
    )
    sample = SimpleNamespace(
        id="voice.one", epoch=1, metadata={"item_version": "1.0.0"}, model_usage=None,
        total_time=1.0, scores={"judge": Score(value=0.85, metadata={
            "judge_model": "openai/judge", "notes": "judge_position_disagreement",
            "pass_threshold": 0.8,
        })},
    )
    row = _row(log, sample)
    assert row["pass"] is True
    assert row["judge_model"] == "openai/judge"
    assert row["notes"] == "unpriced;judge_position_disagreement"


def test_sample_error_is_recorded_in_notes() -> None:
    log = SimpleNamespace(
        status="error",
        eval=SimpleNamespace(
            metadata={"modelwatch_run_id": "run", "provider": "anthropic", "area": "voice"},
            run_id="run", created="2026-09-23T00:00:00+02:00", model="anthropic/model",
            model_generate_config=SimpleNamespace(temperature=0.0, seed=1), task_version="1.0.0",
        ),
    )
    sample = SimpleNamespace(
        id="voice.one", epoch=1, metadata={"item_version": "1.0.0"}, model_usage=None,
        total_time=1.0, scores=None, error=SimpleNamespace(message="judge failed"),
    )
    row = _row(log, sample)
    assert row["pass"] is False
    assert row["notes"] == "unpriced;sample_error:judge failed"
