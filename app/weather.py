"""Live weather via context.dev web extraction.

Source choice matters here, so it is documented rather than assumed.

wttr.in publishes no gust figure at all — its `current_condition` object has no
gust field. MER-SOP-021 §3 makes gusts a threshold input in their own right
("Restricted 25–33 mph gusts"), so a gust-aware verdict cannot be sourced from
it. Asking for one back would produce a number no source published, which is
forbidden action A7.

The two also disagree materially. Measured at the same site in the same minute:
wttr.in 36 °C, Open-Meteo 43.5 °C. MER-SOP-021 §4 turns at 42 °C, so that gap
is the difference between "within limits" and "elevated band, mandatory shaded
rest". Open-Meteo is therefore primary.

Both are still fetched *through* context.dev, so the retrieval path is unchanged.

On any failure this returns available=False — the agent must then say it
cannot verify conditions, never assume they are fine (eval B3 #15).
"""
from dataclasses import dataclass

import httpx

from app.config import CONTEXT_DEV_API_KEY, CONTEXT_DEV_BASE_URL

# Meridian's site: Harbour Point Tower, Dubai Marina.
SITE_COORDS = {"Dubai": (25.1857, 55.2766)}
_DEFAULT_COORDS = SITE_COORDS["Dubai"]

# Disagreement above this between primary and fallback is worth saying out loud
# rather than silently picking one.
_TEMP_DISAGREEMENT_C = 3.0

_SCHEMA = {
    "type": "object",
    "properties": {
        "wind_speed_kmh": {"type": "number", "description": "current sustained wind speed in km/h"},
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
    source: str = "context.dev live extraction of Open-Meteo"
    observed_at: str | None = None
    note: str | None = None
    error: str | None = None


def _open_meteo_url(location: str) -> str:
    lat, lon = SITE_COORDS.get(location, _DEFAULT_COORDS)
    return (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
        "wind_speed_10m,wind_gusts_10m,visibility"
        "&wind_speed_unit=kmh&timezone=Asia%2FDubai"
    )


async def _extract(client: httpx.AsyncClient, url: str) -> dict:
    """Pull a page through context.dev and return the extracted fields."""
    resp = await client.post(
        f"{CONTEXT_DEV_BASE_URL}/web/extract",
        headers={"Authorization": f"Bearer {CONTEXT_DEV_API_KEY}"},
        json={"url": url, "schema": _SCHEMA},
    )
    resp.raise_for_status()
    return resp.json().get("data") or {}


async def fetch_weather(location: str) -> WeatherReading:
    if not CONTEXT_DEV_API_KEY:
        return WeatherReading(available=False, error="CONTEXT_DEV_API_KEY is not set")

    primary_url = _open_meteo_url(location)
    fallback_url = f"https://wttr.in/{location}?format=j1"

    async with httpx.AsyncClient(timeout=45) as client:
        try:
            data = await _extract(client, primary_url)
            source = "context.dev live extraction of Open-Meteo"
        except (httpx.HTTPError, ValueError) as exc:
            primary_error = exc
            try:
                data = await _extract(client, fallback_url)
                source = "context.dev live extraction of wttr.in (fallback — no gust data)"
            except (httpx.HTTPError, ValueError):
                return WeatherReading(
                    available=False,
                    error=f"weather source unavailable: {primary_error}",
                )

        if data.get("wind_speed_kmh") is None:
            return WeatherReading(available=False, error="weather source returned no wind reading")

        reading = WeatherReading(
            available=True,
            wind_speed_kmh=float(data["wind_speed_kmh"]),
            wind_gust_kmh=float(data["wind_gust_kmh"]) if data.get("wind_gust_kmh") else None,
            temp_c=float(data["temp_c"]) if data.get("temp_c") is not None else None,
            description=data.get("description"),
            source=source,
        )

        # Cross-check against the second provider. A material disagreement about a
        # number that decides a stop/go is said out loud, not resolved silently.
        if reading.temp_c is not None and source.startswith("context.dev live extraction of Open-Meteo"):
            try:
                other = await _extract(client, fallback_url)
                other_temp = other.get("temp_c")
                if other_temp is not None:
                    delta = abs(reading.temp_c - float(other_temp))
                    if delta >= _TEMP_DISAGREEMENT_C:
                        return WeatherReading(
                            **{**reading.__dict__,
                               "note": (
                                   f"Weather sources disagree by {delta:.1f} °C "
                                   f"({reading.temp_c:g} °C vs {float(other_temp):g} °C). "
                                   "The stricter reading is used. Confirm with the site "
                                   "anemometer or your supervisor before acting."
                               )},
                        )
            except (httpx.HTTPError, ValueError):
                pass  # cross-check is best-effort; never fail the primary read on it

        return reading
