"""Private smoke task for validating the evaluation pipeline."""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import exact


def _text(values: list[int]) -> str:
    return bytes(values).decode("ascii")


_ONE_WORD = [
    32, 82, 101, 112, 108, 121, 32, 119, 105, 116, 104, 32, 111, 110, 108,
    121, 32, 111, 110, 101, 32, 119, 111, 114, 100, 46,
]


@task
def hello() -> Task:
    return Task(
        dataset=[
            Sample(
                id="hello.1",
                input=_text([87, 104, 97, 116, 32, 105, 115, 32, 50, 43, 50, 63] + _ONE_WORD),
                target=_text([102, 111, 117, 114]),
            ),
            Sample(
                id="hello.2",
                input=_text([87, 104, 97, 116, 32, 99, 111, 108, 111, 114, 32, 105, 115, 32, 115, 110, 111, 119, 63] + _ONE_WORD),
                target=_text([119, 104, 105, 116, 101]),
            ),
            Sample(
                id="hello.3",
                input=_text([87, 104, 97, 116, 32, 97, 110, 105, 109, 97, 108, 32, 115, 97, 121, 115, 32, 109, 101, 111, 119, 63] + _ONE_WORD),
                target=_text([99, 97, 116]),
            ),
        ],
        scorer=exact(),
        version="1.0.0",
        metadata={"area": "hello"},
    )
