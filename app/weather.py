"""Live weather via context.dev web extraction.

Architecture: acquisition is decoupled from the voice path. A background
refresher (see app.main lifespan) keeps the latest reading warm; the tool
answers from the in-memory snapshot in milliseconds and reports the
reading's age. A reading older than the staleness budget (10 minutes,
per the user-flows spec) is treated as unavailable — the agent must then
say it cannot verify conditions, never assume they are fine (eval B3 #15).
"""
import os
import time
from dataclasses import dataclass

import httpx

from app.config import CONTEXT_DEV_API_KEY, CONTEXT_DEV_BASE_URL

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
    source: str = "context.dev live extraction of wttr.in"
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


async def _fetch_weather_live(location: str) -> WeatherReading:
    if not CONTEXT_DEV_API_KEY:
        return WeatherReading(available=False, error="CONTEXT_DEV_API_KEY is not set")
    url = f"https://wttr.in/{location}?format=j1"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{CONTEXT_DEV_BASE_URL}/web/extract",
                headers={"Authorization": f"Bearer {CONTEXT_DEV_API_KEY}"},
                json={"url": url, "schema": _SCHEMA},
            )
            resp.raise_for_status()
            data = resp.json().get("data") or {}
    except (httpx.HTTPError, ValueError) as exc:
        return WeatherReading(available=False, error=f"weather source unavailable: {exc}")
    if data.get("wind_speed_kmh") is None:
        return WeatherReading(available=False, error="weather source returned no wind reading")
    return WeatherReading(
        available=True,
        wind_speed_kmh=float(data["wind_speed_kmh"]),
        wind_gust_kmh=float(data["wind_gust_kmh"]) if data.get("wind_gust_kmh") else None,
        temp_c=float(data["temp_c"]) if data.get("temp_c") is not None else None,
        description=data.get("description"),
    )
