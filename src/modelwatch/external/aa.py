"""Import Artificial Analysis free language-model data."""

from __future__ import annotations

import os
import httpx

from modelwatch.external.common import append_rows, external_row

URL = "https://artificialanalysis.ai/api/v2/language/models/free"
LICENSE = "Artificial Analysis API data, internal use only, no redistribution; credit Artificial Analysis."


def fetch_rows(client: httpx.Client | None = None, api_key: str | None = None) -> list[dict]:
    key = api_key or os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    if not key:
        raise RuntimeError("ARTIFICIAL_ANALYSIS_API_KEY is not set")
    request = client or httpx
    rows: list[dict] = []
    page = 1
    while True:
        response = request.get(URL, params={"page": page}, headers={"x-api-key": key}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("data", []):
            model = item.get("name") or item.get("slug")
            published = (item.get("release_date") or "")[:10]
            if not model:
                continue
            evaluations = item.get("evaluations") or {}
            metrics = [
                ("Intelligence Index", evaluations.get("artificial_analysis_intelligence_index")),
                ("cost per index task", (item.get("artificial_analysis_intelligence_index_cost") or {}).get("cost_per_task", {}).get("total_cost")),
                ("output tokens per second", (item.get("performance") or {}).get("median_output_tokens_per_second")),
            ]
            for series, value in metrics:
                if value is not None:
                    rows.append(external_row("aa", series, model, float(value), published,
                        URL, f"{LICENSE} Source: {URL}"))
        pagination = payload.get("pagination") or {}
        if not pagination.get("has_more"):
            break
        page += 1
    return rows


def import_rows() -> list[dict]:
    return append_rows(fetch_rows())
