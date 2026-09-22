from pathlib import Path

from modelwatch.flatten import RESULT_COLUMNS, flatten_run


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
