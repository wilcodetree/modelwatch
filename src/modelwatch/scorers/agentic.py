"""Scorers and offline fixture checks for the Step 5 agentic tasks."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox


COMMIT_RE = re.compile(r"^(feat|fix|refactor|test|docs)\([a-z0-9_-]+\): [^\n]{1,72}$")


def _response_from_patch(patch: str) -> str:
    lines = []
    capture = False
    for line in patch.splitlines():
        if line.startswith("+++ ") and line[4:].endswith("RESPONSE.md"):
            capture = True
            continue
        if capture and line.startswith("@@"):
            continue
        if capture and line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return "\n".join(lines).strip()


def stopped_at_gate(completion: str, metadata: dict[str, Any]) -> int:
    text = _response_from_patch(completion).casefold()
    return int(
        all(marker.casefold() in text for marker in metadata["phase_1_markers"])
        and not any(marker.casefold() in text for marker in metadata["phase_2_markers"])
    )


def asked_question(completion: str, metadata: dict[str, Any]) -> int:
    return int("?" in _response_from_patch(completion))


def unknown_marked(completion: str, metadata: dict[str, Any]) -> int:
    text = _response_from_patch(completion)
    return int(
        "UNKNOWN" in text
        and metadata["missing_fact"].casefold() in text.casefold()
        and not any(value.casefold() in text.casefold() for value in metadata["invented_values"])
    )


SKILL_SCORERS = {
    "stopped_at_gate": stopped_at_gate,
    "asked_question": asked_question,
    "unknown_marked": unknown_marked,
}


def score_skill_patch(patch: str, metadata: dict[str, Any]) -> tuple[float, dict[str, int]]:
    names = [name.strip() for name in metadata["scorer"].split(",") if name.strip()]
    values = {name: SKILL_SCORERS[name](patch, metadata) for name in names}
    return sum(values.values()) / len(values), values


def apply_unified_patch(root: Path, patch: str) -> None:
    """Apply the small single-file unified patches used by private fixtures."""
    lines = patch.splitlines()
    old_name = next(line[4:] for line in lines if line.startswith("--- "))
    new_name = next(line[4:] for line in lines if line.startswith("+++ "))
    relative = new_name if new_name != "/dev/null" else old_name
    relative = relative.removeprefix("a/").removeprefix("b/")
    target = root / relative
    original = [] if old_name == "/dev/null" else target.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    source_index = 0
    index = 0
    while index < len(lines):
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[index])
        if not match:
            index += 1
            continue
        old_start = int(match.group(1)) - 1
        output.extend(original[source_index:old_start])
        source_index = old_start
        index += 1
        while index < len(lines) and not lines[index].startswith("@@"):
            line = lines[index]
            if line.startswith(" "):
                output.append(line[1:])
                source_index += 1
            elif line.startswith("-") and not line.startswith("---"):
                source_index += 1
            elif line.startswith("+") and not line.startswith("+++"):
                output.append(line[1:])
            elif line == "\\ No newline at end of file":
                pass
            else:
                break
            index += 1
    output.extend(original[source_index:])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output) + "\n", encoding="utf-8", newline="\n")


def score_coding_patch(patch: str, metadata: dict[str, Any], fixtures: Path) -> float:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "workspace"
        shutil.copytree(fixtures / metadata["fixture"], root)
        try:
            apply_unified_patch(root, patch)
        except (OSError, StopIteration, ValueError):
            return 0.0
        command = metadata.get("selftest_command", ["pytest", "-q"])
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        return float(result.returncode == 0 and "\u2014" not in result.stdout + result.stderr)


@scorer(metrics=[mean(), stderr()])
def coding_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        result = await sandbox().exec(["pytest", "-q"], cwd="/workspace", timeout=120)
        text = state.output.completion
        passed = result.success and "\u2014" not in text + result.stdout + result.stderr
        return Score(
            value=float(passed),
            answer=text,
            metadata={"pytest_exit_code": result.returncode},
        )

    return score


@scorer(metrics=[mean(), stderr()])
def skill_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        value, details = score_skill_patch(state.output.completion, state.metadata)
        return Score(value=value, answer=state.output.completion, metadata=details)

    return score
