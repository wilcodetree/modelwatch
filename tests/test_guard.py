from types import SimpleNamespace

import pytest

from modelwatch.guard import GuardStop, Price, PriceBook, SpendGuard


def _book() -> PriceBook:
    return PriceBook(
        date="2026-09-23",
        eur_per_usd=0.8,
        models={"provider/model": Price(2.0, 10.0)},
    )


def test_price_book_costs_usage_in_eur() -> None:
    usage = SimpleNamespace(
        input_tokens=100_000,
        output_tokens=20_000,
        input_tokens_cache_write=0,
        input_tokens_cache_read=0,
    )
    assert _book().cost_eur("provider/model", usage) == pytest.approx(0.32)


def test_deliberately_low_guard_threshold_fires() -> None:
    guard = SpendGuard(0.000001, _book())
    usage = SimpleNamespace(
        input_tokens=1,
        output_tokens=1,
        input_tokens_cache_write=0,
        input_tokens_cache_read=0,
    )
    with pytest.raises(GuardStop, match="spend guard stopped run"):
        guard.add_sample([("provider/model", usage)])


def test_per_sample_ceiling_fires() -> None:
    guard = SpendGuard(10.0, _book(), max_sample_eur=0.1)
    usage = SimpleNamespace(
        input_tokens=100_000,
        output_tokens=20_000,
        input_tokens_cache_write=0,
        input_tokens_cache_read=0,
    )
    with pytest.raises(GuardStop, match="sample cost"):
        guard.add_sample([("provider/model", usage)])
