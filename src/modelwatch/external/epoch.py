"""Import Epoch AI Benchmarking Hub CSV data."""

from __future__ import annotations

import csv
import io
import zipfile

import httpx

from modelwatch.external.common import append_rows, external_row

URL = "https://epoch.ai/data/benchmark_data.zip"
LICENSE = "Epoch AI data, Creative Commons Attribution 4.0 (CC BY 4.0); credit Epoch AI."
FILES = {
    "gpqa_diamond.csv": "GPQA Diamond",
    "frontiermath_tier_4.csv": "FrontierMath Tier 4",
    "swe_bench_verified.csv": "SWE-bench Verified",
}


def _number(row: dict[str, str]) -> float | None:
    for key in ("mean_score", "Best score (across scorers)", "Score"):
        if row.get(key) not in (None, ""):
            value = float(row[key])
            return value / 100 if value > 1 and key == "Score" and value <= 100 else value
    return None


def parse_archive(content: bytes) -> list[dict]:
    rows = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for filename, series in FILES.items():
            with archive.open(filename) as handle:
                for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")):
                    score = _number(row)
                    if score is not None and row.get("Model version") and row.get("Release date"):
                        rows.append(external_row("epoch", series, row["Model version"], score,
                            row["Release date"], URL, f"{LICENSE} Source: {URL}"))
        with archive.open("epoch_capabilities_index/eci_scores.csv") as handle:
            for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")):
                if row.get("Model") and row.get("eci") and row.get("date"):
                    rows.append(external_row("epoch", "ECI", row["Model"], float(row["eci"]),
                        row["date"], URL, f"{LICENSE} Source: {URL}"))
    return rows


def fetch_rows(client: httpx.Client | None = None) -> list[dict]:
    response = (client or httpx).get(URL, timeout=60)
    response.raise_for_status()
    return parse_archive(response.content)


def import_rows() -> list[dict]:
    return append_rows(fetch_rows())
