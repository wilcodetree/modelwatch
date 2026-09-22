"""Private hub-edit anchor task."""

from inspect_ai import Task, task

from modelwatch.scorers.deterministic import deterministic
from modelwatch.tasks.common import samples


@task
def hub_edits() -> Task:
    return Task(dataset=samples("hub_edits"), scorer=deterministic(), version="1.0.0",
                metadata={"area": "hub_edits"})
