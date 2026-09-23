"""Private skill-following anchors."""

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.tool import bash, python

from modelwatch.scorers.agentic import skill_scorer
from modelwatch.tasks.common import agentic_samples


@task
def skills() -> Task:
    return Task(
        dataset=agentic_samples("skills"),
        solver=react(tools=[bash(timeout=120), python(timeout=120)]),
        scorer=skill_scorer(),
        version="1.0.0",
        metadata={"area": "skills"},
        token_limit=60000,
        time_limit=900,
        message_limit=40,
    )
