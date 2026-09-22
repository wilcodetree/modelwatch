from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from modelwatch.external import aa, epoch, livebench, metr
from modelwatch.external.common import append_rows

FIXTURES = Path(__file__).parent / "fixtures" / "external"


class Response:
    def __init__(self, text: str = "", content: bytes | None = None, payload=None):
        self.text = text
        self.content = content if content is not None else text.encode()
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload if self._payload is not None else json.loads(self.text)


def test_epoch_fixture_schema():
    files = {
        "gpqa_diamond.csv": "Model version,mean_score,Release date\nfixture-alpha,0.8,2026-01-02\n",
        "frontiermath_tier_4.csv": "Model version,mean_score,Release date\nfixture-alpha,0.4,2026-01-02\n",
        "swe_bench_verified.csv": "Model version,mean_score,Release date\nfixture-alpha,0.6,2026-01-02\n",
        "epoch_capabilities_index/eci_scores.csv": "Model,eci,date\nfixture-alpha,50,2026-01-02\n",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    rows = epoch.parse_archive(buffer.getvalue())
    assert len(rows) == 4
    assert all(row["source"] == "external" for row in rows)


def test_aa_fixture_schema():
    payload = json.loads((FIXTURES / "aa.json").read_text())
    rows = aa.fetch_rows(client=type("C", (), {"get": lambda *a, **k: Response(payload=payload)})(), api_key="fixture")
    assert {row["task_id"] for row in rows} == {"aa.Intelligence Index", "aa.cost per index task", "aa.output tokens per second"}


def test_livebench_fixture_schema():
    table = (FIXTURES / "livebench_table.csv").read_text()
    categories = json.loads((FIXTURES / "livebench_categories.json").read_text())
    class Client:
        def get(self, url, **kwargs):
            if url.endswith("constants.js"):
                return Response('export const RELEASES = ["2026-01-02"];')
            if "categories" in url:
                return Response(payload=categories)
            return Response(table)
    rows = livebench.fetch_rows(Client())
    assert len(rows) == 8
    assert all(row["source"] == "external" for row in rows)


def test_metr_fixture_schema():
    rows = metr.parse_text((FIXTURES / "metr.yaml").read_text())
    assert {row["task_id"] for row in rows} == {"metr.50% time horizon", "metr.80% time horizon"}


def test_external_store_is_idempotent(tmp_path: Path):
    row = epoch.external_row("epoch", "GPQA Diamond", "fixture-alpha", 0.8, "2026-01-02", "fixture", "CC BY 4.0")
    assert len(append_rows([row], tmp_path / "results.ndjson", tmp_path / "results.sqlite")) == 1
    assert append_rows([row], tmp_path / "results.ndjson", tmp_path / "results.sqlite") == []
