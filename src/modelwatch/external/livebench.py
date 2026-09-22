"""Import the current LiveBench release from its public GitHub data files."""

from __future__ import annotations

import csv
import io
import json
import re
import httpx

from modelwatch.external.common import append_rows, external_row

CONSTANTS_URL = "https://raw.githubusercontent.com/LiveBench/new-livebench/main/src/lib/constants.js"
BASE = "https://raw.githubusercontent.com/LiveBench/new-livebench/main/public"
LICENSE = "LiveBench repository and benchmark data, Apache License 2.0; credit LiveBench."


def fetch_rows(client: httpx.Client | None = None) -> list[dict]:
    request = client or httpx
    constants = request.get(CONSTANTS_URL, timeout=30)
    constants.raise_for_status()
    releases = re.findall(r'"(\d{4}-\d{2}-\d{2})"', constants.text)
    if not releases:
        raise RuntimeError("LiveBench constants did not document a release")
    release = releases[-1]
    stamp = release.replace("-", "_")
    table_url = f"{BASE}/table_{stamp}.csv"
    categories_url = f"{BASE}/categories_{stamp}.json"
    table = request.get(table_url, timeout=30)
    categories = request.get(categories_url, timeout=30)
    table.raise_for_status()
    categories.raise_for_status()
    category_map = categories.json()
    records = list(csv.DictReader(io.StringIO(table.text)))
    rows: list[dict] = []
    for record in records:
        model = record.get("model")
        if not model:
            continue
        metrics = [("overall", [key for key in record if key != "model"])]
        metrics.extend(category_map.items())
        for series, columns in metrics:
            values = [float(record[column]) for column in columns if record.get(column) not in (None, "")]
            if values:
                value = sum(values) / len(values) / 100
                rows.append(external_row("livebench", series, model, value, release, table_url,
                    f"{LICENSE} Source: {table_url}; category map: {categories_url}"))
    return rows


def import_rows() -> list[dict]:
    return append_rows(fetch_rows())
