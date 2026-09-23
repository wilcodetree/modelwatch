"""Dated word lists used by deterministic writing checks."""

from __future__ import annotations

import re


HUMANIZE_SOURCE_DATE = "2026-09-23"
AI_VOCABULARY = (
    "delve", "intricate", "tapestry", "pivotal", "underscore", "landscape",
    "foster", "testament", "robust", "leverage", "enhance", "crucial",
    "navigate", "realm", "multifaceted", "seamless", "vibrant", "nuanced",
    "garner", "myriad", "harness", "elevate", "unlock", "embark",
    "ever-evolving",
)


def banned_words(text: str) -> list[str]:
    """Return humanize catalog words present in text, case-insensitively."""
    found = []
    for term in AI_VOCABULARY:
        escaped = re.escape(term).replace(r"\-", "[- ]")
        if re.search(rf"(?<!\w){escaped}(?!\w)", text, re.IGNORECASE):
            found.append(term)
    return found
