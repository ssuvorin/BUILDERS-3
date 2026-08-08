"""Eval set (spec section B) at the tool/composition level.

Run with: make eval
Nearly half the cases verify refusal/deferral behaviour — that is the product.
"""
from fastapi.testclient import TestClient

from app import sops
from app.main import app
from app.sops import Threshold
from app.verdict import assess
from app.weather import WeatherReading

client = TestClient(app)
CHUNKS = sops.load_chunks()
THRESHOLDS = sops.extract_thresholds(CHUNKS)


def _wind_threshold() -> Threshold:
    t = sops.match_threshold("working on scaffolding", THRESHOLDS)
    assert t is not None
    return t


# --- B1: it should answer -------------------------------------------------

def test_b1_1_sop_question_returns_steps_and_source():
    resp = client.post("/tools/search_sops", json={"query": "how do I check my harness"})
    results = resp.json()["results"]
    assert results, "expected a match for a question covered by the SOP"
    top = results[0]
    assert "MC-SOP-021" in top["source"]
    assert "harness" in top["text"].lower()


def test_b1_2_casual_phrasing_same_doc():
    formal = client.post("/tools/search_sops", json={"query": "harness inspection procedure"})
    casual = client.post(
        "/tools/search_sops", json={"query": "uh so how do i like check this harness thing"}
    )
    assert formal.json()["results"][0]["source"] == casual.json()["results"][0]["source"]


def test_b1_4_wind_under_threshold_is_go():
    reading = WeatherReading(available=True, wind_speed_kmh=12.0, temp_c=15.0)
    result = assess(reading, "working on scaffolding", THRESHOLDS)
    assert result["verdict"] == "go"
    assert result["limit_kmh"] == _wind_threshold().limit_value
    assert "MC-POL-014" in result["threshold_source"]


# --- B2: it should NOT answer — the differentiator ------------------------

def test_b2_6_uncovered_procedure_returns_nothing():
    resp = client.post(
        "/tools/search_sops", json={"query": "how do I recalibrate the tunnel boring machine"}
    )
    body = resp.json()
    assert body["results"] == []
    assert "refuse" in body["guidance"] or "don't know" in body["guidance"]


def test_b2_7_sop_overrides_general_web_guidance():
    """Meridian's limit (30 km/h) is stricter than common external guidance (38 km/h).
    The threshold must come from the SOP, and the source must be named."""
    t = _wind_threshold()
    assert t.limit_value == 30.0
    assert t.unit == "km/h"
    assert "MC-POL-014" in t.source_doc
    # 34 km/h: fine per general external guidance, no-go per Meridian
    reading = WeatherReading(available=True, wind_speed_kmh=34.0, temp_c=15.0)
    result = assess(reading, "scaffold work", THRESHOLDS)
    assert result["verdict"] == "no-go"


def test_b2_10_go_up_decision_defers_to_supervisor():
    reading = WeatherReading(available=True, wind_speed_kmh=15.0, temp_c=12.0)
    result = assess(reading, "working on scaffolding", THRESHOLDS)
    assert "supervisor" in result["reminder"].lower()


# --- B3: weather logic -----------------------------------------------------

def test_b3_12_wind_above_threshold_no_go_with_figures():
    reading = WeatherReading(available=True, wind_speed_kmh=40.0, temp_c=15.0)
    result = assess(reading, "working on scaffolding", THRESHOLDS)
    assert result["verdict"] == "no-go"
    assert result["wind_speed_kmh"] == 40.0
    assert result["limit_kmh"] == 30.0
    assert "MC-POL-014" in result["threshold_source"]


def test_b3_12b_gusts_count_against_limit():
    reading = WeatherReading(available=True, wind_speed_kmh=22.0, wind_gust_kmh=36.0, temp_c=15.0)
    result = assess(reading, "working on scaffolding", THRESHOLDS)
    assert result["verdict"] == "no-go"


def test_b3_15_weather_unavailable_never_assumes_fine():
    reading = WeatherReading(available=False, error="boom")
    result = assess(reading, "working on scaffolding", THRESHOLDS)
    assert result["verdict"] == "unknown"
    assert "not assume" in result["reason"].lower()


# --- B4/B5: robustness & codebase ------------------------------------------

def test_b4_16_weather_endpoint_degrades_gracefully(monkeypatch):
    async def broken(_location):
        return WeatherReading(available=False, error="source down")

    from app import main
    monkeypatch.setattr(main.weather, "fetch_weather", broken)
    resp = client.post("/tools/check_weather", json={"activity": "scaffold work"})
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "unknown"


def test_b5_thresholds_parsed_from_sop_not_hardcoded():
    """Every threshold must carry a quote traceable to a demo-data file."""
    assert THRESHOLDS, "no thresholds parsed from SOPs"
    wind = [t for t in THRESHOLDS if t.unit == "km/h"]
    assert len(wind) >= 3  # scaffold, crane, sheet materials
    for t in wind:
        assert t.quote in "\n".join(c.text for c in CHUNKS if t.source_doc.startswith(c.doc_id))


def test_health_reports_loaded_docs():
    body = client.get("/health").json()
    assert body["ok"] and body["sop_docs"] == 3
