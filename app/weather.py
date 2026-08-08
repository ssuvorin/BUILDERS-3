"""Live weather via context.dev web extraction.

Architecture: acquisition is decoupled from the voice path. A background
refresher (see app.main lifespan) keeps the latest reading warm; the tool
answers from the in-memory snapshot in milliseconds and reports the
reading's age. A reading older than the staleness budget (10 minutes,
per the user-flows spec) is treated as unavailable — the agent must then
say it cannot verify conditions, never assume they are fine (eval B3 #15).

Sources (docs/FINDINGS.md, Finding 1): Open-Meteo is primary — it publishes
gusts, which the policy makes a threshold input, while wttr.in does not.
wttr.in stays as fallback (it accepts place names, so it also covers ad-hoc
locations that have no configured coordinates). Every reading names the
source it came from, and both are fetched through context.dev.
"""
import os
import time
from dataclasses import dataclass
from urllib.parse import quote

from app import context_dev
from app.config import SITE_LAT, SITE_LOCATION, SITE_LON

REFRESH_INTERVAL_SECONDS = float(os.getenv("WEATHER_REFRESH_INTERVAL", "120"))
_STALE_AFTER_SECONDS = float(os.getenv("WEATHER_STALE_AFTER", "600"))
_state: dict[str, tuple[float, "WeatherReading"]] = {}

_SCHEMA = {
    "type": "object",
    "properties": {
        "wind_speed_kmh": {
            "type": "number",
            "description": "current sustained wind speed in km/h",
        },
        "wind_gust_kmh": {"type": "number", "description": "current wind gust speed in km/h"},
        "temp_c": {"type": "number", "description": "current air temperature in celsius"},
        "description": {"type": "string", "description": "short weather description"},
    },
    "required": ["wind_speed_kmh", "temp_c"],
}


@dataclass(frozen=True)
class WeatherReading:
    available: bool
    wind_speed_kmh: float | None = None
    wind_gust_kmh: float | None = None
    temp_c: float | None = None
    description: str | None = None
    source: str = "context.dev live extraction"
    error: str | None = None


async def refresh(location: str) -> WeatherReading:
    """Fetch a live reading and store it in the snapshot state."""
    reading = await _fetch_weather_live(location)
    if reading.available:
        _state[location] = (time.monotonic(), reading)
    return reading


def snapshot(location: str) -> tuple[WeatherReading, float | None]:
    """Return (reading, age_seconds) from memory without any network I/O.

    No reading yet -> (unavailable, None). Reading past the staleness
    budget -> (unavailable, age): serving it would break eval 13.
    """
    entry = _state.get(location)
    if entry is None:
        return WeatherReading(available=False, error="no weather reading yet"), None
    fetched_at, reading = entry
    age = time.monotonic() - fetched_at
    if age > _STALE_AFTER_SECONDS:
        stale = WeatherReading(
            available=False,
            error=f"last reading is {int(age)}s old — past the {int(_STALE_AFTER_SECONDS)}s "
            "staleness budget",
        )
        return stale, age
    return reading, age


def _sources(location: str) -> list[tuple[str, str]]:
    """(name, url) per source, in precedence order. Open-Meteo works on the
    configured site's coordinates; wttr.in accepts any place name."""
    sources = []
    if location == SITE_LOCATION:
        open_meteo_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={SITE_LAT}&longitude={SITE_LON}"
            "&current=temperature_2m,wind_speed_10m,wind_gusts_10m,weather_code"
            "&wind_speed_unit=kmh"
        )
        sources.append(("Open-Meteo", open_meteo_url))
    sources.append(("wttr.in", f"https://wttr.in/{quote(location)}?format=j1"))
    return sources


def _num(data: dict, key: str) -> float | None:
    return float(data[key]) if data.get(key) is not None else None


async def _fetch_weather_live(location: str) -> WeatherReading:
    errors = []
    for name, url in _sources(location):
        try:
            data = await context_dev.post("/web/extract", {"url": url, "schema": _SCHEMA})
        except context_dev.ContextDevError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if data.get("wind_speed_kmh") is None:
            errors.append(f"{name}: no wind reading")
            continue
        return WeatherReading(
            available=True,
            wind_speed_kmh=float(data["wind_speed_kmh"]),
            wind_gust_kmh=_num(data, "wind_gust_kmh"),
            temp_c=_num(data, "temp_c"),
            description=data.get("description"),
            source=f"context.dev live extraction of {name}",
        )
    return WeatherReading(
        available=False, error="weather sources unavailable — " + "; ".join(errors)
    )
