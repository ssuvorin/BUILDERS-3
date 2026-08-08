"""Go/no-go composition: weather reading vs SOP threshold."""
from app.sops import Threshold, match_threshold
from app.weather import WeatherReading

_MPH_PER_KMH = 0.621371


def _limit_in_mph(threshold: Threshold) -> float:
    if threshold.unit == "km/h":
        return threshold.limit_value * _MPH_PER_KMH
    return threshold.limit_value


def assess(reading: WeatherReading, activity: str, thresholds: list[Threshold]) -> dict:
    """Compare a live reading against the SOP threshold for an activity."""
    if not reading.available:
        return {
            "verdict": "unknown",
            "reason": "Cannot verify current conditions — the weather source is unavailable. "
            "Do NOT assume conditions are fine. Check with the site supervisor.",
            "error": reading.error,
        }
    threshold = match_threshold(activity, thresholds)
    if threshold is None:
        return {
            "verdict": "unknown",
            "reason": "No wind threshold found in the loaded SOPs for this activity.",
            "weather": reading.__dict__,
        }
    limit_mph = _limit_in_mph(threshold)
    effective_wind = max(reading.wind_speed_mph, reading.wind_gust_mph or 0)
    over = effective_wind >= limit_mph
    return {
        "verdict": "no-go" if over else "go",
        "activity": threshold.activity,
        "wind_speed_mph": reading.wind_speed_mph,
        "wind_gust_mph": reading.wind_gust_mph,
        "temp_c": reading.temp_c,
        "limit_mph": limit_mph,
        "threshold_source": threshold.source_doc,
        "threshold_quote": threshold.quote,
        "weather_source": reading.source,
        "note": "Gusts count against the limit per MC-POL-014."
        if reading.wind_gust_mph
        else None,
        "reminder": "The site supervisor makes the final stop/go call.",
    }
