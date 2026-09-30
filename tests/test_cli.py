import json
from pathlib import Path

import pytest

import modelwatch.cli as cli


class ExpectedEvalStop(RuntimeError):
    pass


def test_all_initializes_mixed_area_guard_before_first_eval(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for name in ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_WORKSPACE_ID"):
        monkeypatch.setenv(name, "test-value")
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(cli, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(
        cli,
        "inspect_eval",
        lambda **_kwargs: (_ for _ in ()).throw(ExpectedEvalStop("stop before paid call")),
    )

    with pytest.raises(ExpectedEvalStop, match="stop before paid call"):
        cli.run(
            task=None,
            all_tasks=True,
            roster=Path("config/roster.yaml"),
            repeats=1,
        )

    manifests = list((tmp_path / "runs").glob("*/run.json"))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["status"] == "error"
    assert manifest["active_model"] == "anthropic/claude-fable-5-1"
