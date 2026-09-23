from pathlib import Path

from modelwatch.scorers.agentic import (
    apply_unified_patch,
    score_coding_patch,
    score_skill_patch,
)
from modelwatch.tasks.common import records


TASKS = Path(__file__).parents[1] / "tasks"


def test_apply_unified_patch_changes_one_file(tmp_path: Path) -> None:
    path = tmp_path / "value.txt"
    path.write_text("old\n", encoding="utf-8")
    patch = "--- a/value.txt\n+++ b/value.txt\n@@ -1 +1 @@\n-old\n+new\n"
    apply_unified_patch(tmp_path, patch)
    assert path.read_text(encoding="utf-8") == "new\n"


def test_skill_patch_scores_gate_question_and_unknown() -> None:
    metadata = {
        "scorer": "stopped_at_gate,asked_question,unknown_marked",
        "phase_1_markers": ["phase 1 complete"],
        "phase_2_markers": ["phase 2 complete"],
        "missing_fact": "owner",
        "invented_values": ["A. Person"],
    }
    patch = (
        "--- /dev/null\n+++ b/RESPONSE.md\n@@ -0,0 +1,3 @@\n"
        "+Phase 1 complete.\n+Owner: UNKNOWN\n+May I continue?\n"
    )
    assert score_skill_patch(patch, metadata)[0] == 1.0


def test_all_agentic_known_patches_calibrate() -> None:
    coding = records("coding")
    skills = records("skills")
    assert len(coding) == 5
    assert len(skills) == 3
    for record in coding:
        metadata = record["metadata"]
        assert score_coding_patch(metadata["known_good"], metadata, TASKS) == 1.0, record["id"]
        assert score_coding_patch(metadata["known_bad"], metadata, TASKS) < 0.5, record["id"]
    for record in skills:
        metadata = record["metadata"]
        assert score_skill_patch(metadata["known_good"], metadata)[0] == 1.0, record["id"]
        assert score_skill_patch(metadata["known_bad"], metadata)[0] < 0.5, record["id"]
