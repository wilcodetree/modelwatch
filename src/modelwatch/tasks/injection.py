"""Private prompt-injection anchor task."""

from inspect_ai import Task, task

from modelwatch.scorers.deterministic import deterministic
from modelwatch.tasks.common import samples


@task
def injection() -> Task:
    return Task(dataset=samples("injection"), scorer=deterministic(), version="1.0.1",
                metadata={"area": "injection"})
