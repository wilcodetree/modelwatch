"""Private voice anchor task."""

from inspect_ai import Task, task

from modelwatch.scorers.judge import position_swapped_judge
from modelwatch.tasks.common import samples


@task
def voice() -> Task:
    return Task(
        dataset=samples("voice"),
        scorer=position_swapped_judge(),
        version="1.0.0",
        metadata={"area": "voice"},
    )
