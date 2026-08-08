"""Live weather via context.dev web extraction.

On any failure this returns available=False — the agent must then say it
cannot verify conditions, never assume they are fine (eval B3 #15).
"""
from dataclasses import dataclass

import httpx

from app.config import CONTEXT_DEV_API_KEY, CONTEXT_DEV_BASE_URL

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


async def fetch_weather(location: str) -> WeatherReading:
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
