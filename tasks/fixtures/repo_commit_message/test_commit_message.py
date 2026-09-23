import re
from pathlib import Path


def test_commit_message_matches_house_format() -> None:
    message = Path("COMMIT_MESSAGE.txt").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"(feat|fix|refactor|test|docs)\([a-z0-9_-]+\): [^\n]{1,72}", message)
    assert "\u2014" not in message
