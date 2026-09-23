"""Dated price-book costing and the per-run EUR spend guard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


class GuardStop(RuntimeError):
    """Raised after a sample takes a run to or beyond its EUR limit."""


@dataclass(frozen=True)
class Price:
    input_usd_per_million: float
    output_usd_per_million: float
    cache_write_usd_per_million: float = 0.0
    cache_read_usd_per_million: float = 0.0


@dataclass(frozen=True)
class PriceBook:
    date: str
    eur_per_usd: float
    models: dict[str, Price]

    @classmethod
    def load(cls, path: Path) -> "PriceBook":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        models = {
            name: Price(
                input_usd_per_million=float(values["input_usd_per_million"]),
                output_usd_per_million=float(values["output_usd_per_million"]),
                cache_write_usd_per_million=float(
                    values.get("cache_write_usd_per_million", 0.0)
                ),
                cache_read_usd_per_million=float(
                    values.get("cache_read_usd_per_million", 0.0)
                ),
            )
            for name, values in data.get("models", {}).items()
        }
        return cls(
            date=str(data["date"]),
            eur_per_usd=float(data["eur_per_usd"]),
            models=models,
        )

    def cost_eur(self, model: str, usage: Any) -> float | None:
        price = self.models.get(model)
        if price is None:
            return None
        usd = (
            int(getattr(usage, "input_tokens", 0) or 0)
            * price.input_usd_per_million
            + int(getattr(usage, "output_tokens", 0) or 0)
            * price.output_usd_per_million
            + int(getattr(usage, "input_tokens_cache_write", 0) or 0)
            * price.cache_write_usd_per_million
            + int(getattr(usage, "input_tokens_cache_read", 0) or 0)
            * price.cache_read_usd_per_million
        ) / 1_000_000
        return usd * self.eur_per_usd


class SpendGuard:
    def __init__(
        self,
        limit_eur: float,
        price_book: PriceBook,
        max_sample_eur: float | None = None,
    ) -> None:
        if limit_eur <= 0:
            raise ValueError("guard limit must be positive")
        self.limit_eur = limit_eur
        self.price_book = price_book
        self.max_sample_eur = max_sample_eur
        self.total_eur = 0.0

    def add_sample(self, usages: Iterable[tuple[str, Any]]) -> float:
        sample_cost = 0.0
        for model, usage in usages:
            cost = self.price_book.cost_eur(model, usage)
            if cost is None:
                raise ValueError(f"unpriced model: {model}")
            sample_cost += cost
        if self.max_sample_eur is not None and sample_cost > self.max_sample_eur:
            raise GuardStop(
                f"sample cost EUR {sample_cost:.6f} exceeds EUR "
                f"{self.max_sample_eur:.6f}"
            )
        self.total_eur += sample_cost
        if self.total_eur >= self.limit_eur:
            raise GuardStop(
                f"spend guard stopped run at EUR {self.total_eur:.6f} "
                f"(limit EUR {self.limit_eur:.6f})"
            )
        return sample_cost


def eval_log_usages(log: Any) -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    for sample in log.samples or []:
        result.extend((model, usage) for model, usage in (sample.model_usage or {}).items())
    return result
