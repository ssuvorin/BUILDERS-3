"""Eval set (spec section B) at the tool/composition level.

Run with: make eval
Nearly half the cases verify refusal/deferral behaviour — that is the product.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import sops
from app.main import app
from app.policy import extract_policy
from app.verdict import assess
from app.weather import WeatherReading

client = TestClient(app)
CHUNKS = sops.load_chunks()
POLICY = extract_policy(CHUNKS)
TZ = ZoneInfo("Asia/Dubai")
WINTER_NOON = datetime(2026, 1, 15, 12, 45, tzinfo=TZ)  # outside midday-break window


def _kmh(mph: float) -> float:
    return mph * 1.60934


# --- B1: it should answer -------------------------------------------------

def test_b1_1_sop_question_returns_steps_and_source():
    resp = client.post("/tools/search_sops", json={"query": "how do I inspect my harness"})
    results = resp.json()["results"]
    assert results, "expected a match for a question covered by the SOP"
    assert "MER-SOP-014" in results[0]["source"]
    assert "harness" in results[0]["text"].lower()


def test_b1_2_casual_phrasing_same_doc():
    formal = client.post("/tools/search_sops", json={"query": "harness inspection before use"})
    casual = client.post(
        "/tools/search_sops", json={"query": "uh so how do i like check this harness thing"}
    )
    assert formal.json()["results"][0]["source"] == casual.json()["results"][0]["source"]


def test_b1_4_wind_under_threshold_is_go():
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(10), temp_c=30.0)
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "go"
    assert "MER-SOP-021" in result["policy_source"]


# --- B2: it should NOT answer — the differentiator ------------------------

def test_b2_6_mewp_procedure_not_covered_returns_nothing():
    """Deliberate gap from the demo-data README: MEWP setup is not covered."""
    resp = client.post(
        "/tools/search_sops", json={"query": "set up the MEWP for the east elevation"}
    )
    body = resp.json()
    assert body["results"] == []
    assert "refuse" in body["guidance"] or "don't know" in body["guidance"]


def test_b2_7_sop_overrides_general_web_guidance():
    """The money shot: Meridian restricts work above 6 m from 17 mph sustained —
    stricter than commonly cited external guidance. Parsed from the SOP."""
    assert POLICY is not None
    assert POLICY.restricted_wind_mph == 17.0
    assert "MER-SOP-021" in POLICY.source_doc
    # 20 mph sustained: fine per general guidance, restricted per Meridian
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(20), temp_c=30.0)
    result = assess(reading, "working on the scaffold", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "restricted"
    assert any("no work above 6 m" in r.lower() for r in result["reasons"])


def test_b2_10_go_up_decision_defers_to_supervisor():
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(10), temp_c=30.0)
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    assert "supervisor" in result["reminder"].lower()


# --- B3: weather & sequencing logic -----------------------------------------

def test_b3_12_wind_suspended_band_stops_external_work():
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(25), temp_c=30.0)
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "no-go"
    assert any("suspended band" in r for r in result["reasons"])
    assert "MER-SOP-021" in result["policy_source"]


def test_b3_12b_gusts_count_against_limit():
    reading = WeatherReading(
        available=True, wind_speed_kmh=_kmh(12), wind_gust_kmh=_kmh(35), temp_c=30.0
    )
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "no-go"


def test_b3_13_sheet_handling_stops_at_lower_limit_any_height():
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(16), temp_c=30.0)
    result = assess(reading, "handling sheet materials at ground level", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "no-go"
    assert any("any height" in r for r in result["reasons"])


def test_b3_13b_sheet_words_survive_plurals_and_punctuation():
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(16), temp_c=30.0)
    for activity in ("carrying sheets up", "sheeting, then hoisting"):
        assert assess(reading, activity, POLICY, now=WINTER_NOON)["verdict"] == "no-go"


def test_b3_14_heat_bands_flagged():
    elevated = assess(
        WeatherReading(available=True, wind_speed_kmh=_kmh(5), temp_c=43.0),
        "external work", POLICY, now=WINTER_NOON,
    )
    assert elevated["verdict"] == "go"
    assert any("elevated band" in r for r in elevated["reasons"])
    suspended = assess(
        WeatherReading(available=True, wind_speed_kmh=_kmh(5), temp_c=46.0),
        "external work", POLICY, now=WINTER_NOON,
    )
    assert suspended["verdict"] == "no-go"


def test_b3_14b_summer_midday_break_prohibits_external_work():
    summer_lunch = datetime(2026, 8, 8, 13, 0, tzinfo=TZ)
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(5), temp_c=38.0)
    result = assess(reading, "external work", POLICY, now=summer_lunch)
    assert result["verdict"] == "no-go"
    assert any("midday break" in r.lower() for r in result["reasons"])
    # same conditions at 15:30 are fine
    after = assess(reading, "external work", POLICY,
                   now=datetime(2026, 8, 8, 15, 30, tzinfo=TZ))
    assert after["verdict"] == "go"


def test_b3_15_weather_unavailable_never_assumes_fine():
    reading = WeatherReading(available=False, error="boom")
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    assert result["verdict"] == "unknown"
    assert "not assume" in result["reason"].lower()


def test_b3_15b_degraded_answer_still_carries_the_threshold():
    """Cross-cutting flow 3.3: the limit comes from the SOP and is always
    available — only the comparison with live conditions is withheld."""
    reading = WeatherReading(available=False, error="boom")
    result = assess(reading, "working on scaffolding", POLICY, now=WINTER_NOON)
    fallback = result["policy_thresholds_still_valid"]
    assert fallback["restricted_from_mph"] == 17.0
    assert "MER-SOP-021" in fallback["source"]


def test_flow_e_specific_rule_beats_general_rule():
    """Sail rule: 16 mph at ground level passes the height band but formwork
    panels stop at 15 mph at any height — most restrictive rule wins."""
    reading = WeatherReading(available=True, wind_speed_kmh=_kmh(16), temp_c=30.0)
    general = assess(reading, "external work at ground level", POLICY, now=WINTER_NOON)
    assert general["verdict"] == "go"
    panels = assess(reading, "moving formwork panels on the deck", POLICY, now=WINTER_NOON)
    assert panels["verdict"] == "no-go"


# --- B4/B5: robustness & codebase ------------------------------------------

def test_b4_16_weather_endpoint_degrades_gracefully(monkeypatch):
    async def broken(_location):
        return WeatherReading(available=False, error="source down")

    from app import main
    monkeypatch.setattr(main.weather, "snapshot",
                        lambda _loc: (WeatherReading(available=False, error="none"), None))
    monkeypatch.setattr(main.weather, "refresh", broken)
    resp = client.post("/tools/check_weather", json={"activity": "scaffold work"})
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "unknown"


def test_eval13_stale_reading_is_never_served():
    """A reading past the 10-minute staleness budget must come back
    unavailable, not as a stale figure (user-flows eval 13)."""
    import time as _time

    from app import weather as w
    w._state["StaleTown"] = (
        _time.monotonic() - 3600,
        WeatherReading(available=True, wind_speed_kmh=5.0, temp_c=30.0),
    )
    reading, age = w.snapshot("StaleTown")
    assert not reading.available
    assert age is not None and age > 600
    del w._state["StaleTown"]


def test_stale_reading_triggers_a_live_refetch(monkeypatch):
    """A stale snapshot must not be a dead end: the endpoint re-fetches live
    instead of answering 'unknown' forever."""
    import time as _time

    from app import main
    from app import weather as w

    fresh = WeatherReading(available=True, wind_speed_kmh=_kmh(10), temp_c=30.0)

    async def fake_refresh(_location):
        return fresh

    monkeypatch.setitem(w._state, "StaleTown", (_time.monotonic() - 3600, fresh))
    monkeypatch.setattr(main.weather, "refresh", fake_refresh)
    resp = client.post(
        "/tools/check_weather", json={"activity": "external work", "location": "StaleTown"}
    )
    body = resp.json()
    assert body["verdict"] != "unknown"
    assert body["reading_age_seconds"] == 0


def test_b5_policy_parsed_from_sop_not_hardcoded():
    """Every figure in the verdict must be traceable to MER-SOP-021 text."""
    assert POLICY is not None
    body = "\n".join(c.text for c in CHUNKS if c.doc_id == "MER-SOP-021")
    for figure in ("17", "22", "25", "33", "15 mph", "42", "45", "12:30", "15:00"):
        assert figure in body


def test_health_reports_loaded_docs():
    body = client.get("/health").json()
    assert body["ok"] and body["sop_docs"] == 3 and body["policy_loaded"]


# --- voice session lease: one active session per deployment -----------------

def test_voice_lease_single_session(monkeypatch):
    from app import voice_broker
    monkeypatch.setattr(voice_broker, "_current", None)

    first = client.post("/api/voice-lease")
    assert first.status_code == 200 and first.json()["granted"]
    lease_id = first.json()["lease_id"]

    second = client.post("/api/voice-lease")
    assert second.status_code == 409 and not second.json()["granted"]

    assert client.post("/api/voice-lease/heartbeat", json={"lease_id": lease_id}).json()["ok"]
    client.post("/api/voice-lease/release", json={"lease_id": lease_id})
    assert client.post("/api/voice-lease").json()["granted"]


def test_voice_lease_expires_when_holder_goes_silent(monkeypatch):
    import time as _time

    from app import voice_broker
    monkeypatch.setattr(voice_broker, "_current", None)
    lease_id = voice_broker.acquire()
    assert lease_id is not None
    # simulate a crashed tab: TTL passes with no heartbeat
    voice_broker._current.expires_at = _time.monotonic() - 1
    assert not voice_broker.heartbeat(lease_id)
    assert voice_broker.acquire() is not None
