from modelwatch.scorers.deterministic import score_completion
from modelwatch.tasks.common import records


def test_all_known_completions_calibrate() -> None:
    loaded = records("hub_edits") + records("injection")
    assert len(loaded) == 12
    for record in loaded:
        metadata = record["metadata"]
        assert score_completion(metadata["known_good"], metadata)[0] == 1.0, record["id"]
        assert score_completion(metadata["known_bad"], metadata)[0] < 0.5, record["id"]


def test_records_have_required_contract_fields() -> None:
    for record in records("hub_edits") + records("injection"):
        assert set(("id", "version", "area", "input", "target", "metadata")) <= set(record)
        assert record["version"] == "1.0.0"
        assert record["metadata"]["known_good"]
        assert record["metadata"]["known_bad"]
