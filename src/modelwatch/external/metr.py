"""Import METR's published Time Horizon 1.1 YAML feed."""

from __future__ import annotations

import httpx
import yaml

from modelwatch.external.common import append_rows, external_row

URL = "https://metr.org/assets/benchmark_results_1_1.yaml"
LICENSE = "METR eval-analysis-public data; cite METR, Measuring AI Ability to Complete Long Tasks (2025), and follow the repository license terms."


def parse_text(text: str) -> list[dict]:
    payload = yaml.safe_load(text)
    benchmark = payload.get("benchmark_name", "METR-Horizon-v1.1")
    rows: list[dict] = []
    for key, item in (payload.get("results") or {}).items():
        model = item.get("display_name") or item.get("model_name") or key
        published = str(item.get("release_date") or "")[:10]
        metrics = item.get("metrics") or {}
        for series, field in (("50% time horizon", "p50_horizon_length"), ("80% time horizon", "p80_horizon_length")):
            value = (metrics.get(field) or {}).get("estimate")
            if value is not None:
                rows.append(external_row("metr", series, model, float(value), published, URL,
                    f"{LICENSE} Source: {URL}; benchmark: {benchmark}"))
    return rows


def fetch_rows(client: httpx.Client | None = None) -> list[dict]:
    response = (client or httpx).get(URL, timeout=30)
    response.raise_for_status()
    return parse_text(response.text)


def import_rows() -> list[dict]:
    return append_rows(fetch_rows())
