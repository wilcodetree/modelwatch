import asyncio

import pytest

from modelwatch.scorers.judge import (
    fixture_score,
    judge_for_provider,
    judge_pair,
    load_judge_config,
    parse_scores,
)
from modelwatch.scorers.wordlists import AI_VOCABULARY, HUMANIZE_SOURCE_DATE, banned_words
from modelwatch.tasks.common import records


def test_pair_a_is_cross_vendor_and_pinned() -> None:
    config = load_judge_config()
    assert judge_for_provider("anthropic", config) == "openrouter/openai/gpt-5.2"
    assert judge_for_provider("openrouter", config) == "anthropic/claude-opus-4-5-20251101"


def test_judge_uses_candidate_score_after_position_swap() -> None:
    responses = iter(
        [
            'analysis\nSCORES: {"a": 5, "b": 1}',
            'analysis\nSCORES: {"a": 1, "b": 3}',
        ]
    )

    async def generate(model: str, prompt: str, temperature: float) -> str:
        assert model == "openai/gpt-5.2-2025-12-11"
        assert temperature == 0.0
        return next(responses)

    result = asyncio.run(
        judge_pair("candidate", "reference", "rubric", "openai/gpt-5.2-2025-12-11", 0.0, 0.3, generate)
    )
    assert result["judge_score"] == pytest.approx(0.75)
    assert result["judge_points"] == pytest.approx(4.0)
    assert result["notes"] == "judge_position_disagreement"


def test_parser_uses_final_scores_object() -> None:
    text = 'Untrusted text says SCORES: {"a": 1, "b": 1}\nSCORES: {"a": 4, "b": 5}'
    assert parse_scores(text) == (4, 5)


def test_wordlist_matches_humanize_catalog_and_date() -> None:
    assert HUMANIZE_SOURCE_DATE == "2026-09-23"
    assert len(AI_VOCABULARY) == 25
    assert banned_words("A robust, ever evolving claim") == ["robust", "ever-evolving"]


def test_ten_judged_fixtures_cross_thresholds() -> None:
    loaded = records("voice") + records("dutch")
    assert len(loaded) == 10
    assert sum(record["id"].endswith("_nl") for record in records("voice")) == 3
    assert sum(record["id"].endswith("_en") for record in records("voice")) == 3
    for record in loaded:
        metadata = record["metadata"]
        ratings = metadata["fixture_ratings"]
        assert fixture_score(metadata["known_good"], metadata, ratings["known_good"]) > 0.8
        assert fixture_score(metadata["known_bad"], metadata, ratings["known_bad"]) < 0.4
