"""Go/no-go composition: live reading + time of day vs the parsed policy."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.policy import WeatherPolicy
from app.weather import WeatherReading

_MPH_PER_KMH = 0.621371
_SHEET_WORDS = {"sheet", "sheets", "sheeting", "panel", "panels", "formwork", "shuttering"}
_SITE_TZ = ZoneInfo("Asia/Dubai")


def _midday_break_active(policy: WeatherPolicy, now: datetime) -> bool:
    date_key = (now.month, now.day)
    if not (policy.midday_from <= date_key <= policy.midday_to):
        return False
    hhmm = now.strftime("%H:%M")
    return policy.midday_start <= hhmm < policy.midday_end


def assess(
    reading: WeatherReading,
    activity: str,
    policy: WeatherPolicy | None,
    now: datetime | None = None,
) -> dict:
    if not reading.available:
        result = {
            "verdict": "unknown",
            "reason": "Cannot verify current conditions — the weather source is unavailable. "
            "Do NOT assume conditions are fine. Check with the site supervisor.",
            "error": reading.error,
        }
        if policy is not None:
            result["policy_thresholds_still_valid"] = {
                "note": "The thresholds come from the SOP and are always available — give "
                "the worker the limit, withhold only the comparison with live conditions.",
                "restricted_from_mph": policy.restricted_wind_mph,
                "suspended_from_mph": policy.suspended_wind_mph,
                "sheet_stop_mph": policy.sheet_stop_mph,
                "heat_suspended_c": policy.heat_suspended_c,
                "source": policy.source_doc,
            }
        return result
    if policy is None:
        return {"verdict": "unknown", "reason": "No weather policy found in the loaded SOPs."}

    now = now or datetime.now(_SITE_TZ)
    wind_mph = reading.wind_speed_kmh * _MPH_PER_KMH
    gust_mph = (reading.wind_gust_kmh or 0) * _MPH_PER_KMH
    temp = reading.temp_c
    reasons, verdict = [], "go"

    if _midday_break_active(policy, now):
        verdict = "no-go"
        reasons.append(
            f"Summer midday break: external work prohibited between {policy.midday_start} "
            f"and {policy.midday_end} — company-wide rule, not subject to supervisor discretion."
        )
    if temp is not None and temp >= policy.heat_suspended_c:
        verdict = "no-go"
        reasons.append(f"Temperature {temp:g} °C is above the {policy.heat_suspended_c:g} °C "
                       "suspension threshold: all external work stops.")
    elif temp is not None and temp >= policy.heat_elevated_c:
        reasons.append(f"Temperature {temp:g} °C is in the elevated band "
                       f"({policy.heat_elevated_c:g}–{policy.heat_suspended_c:g} °C): mandatory "
                       "15-min shaded rest per hour, buddy system, no lone working outdoors.")
    if wind_mph >= policy.suspended_wind_mph or gust_mph >= policy.suspended_gust_mph:
        verdict = "no-go"
        reasons.append(f"Wind (sustained {wind_mph:.0f} mph, gusts {gust_mph:.0f} mph) is in the "
                       f"suspended band (above {policy.suspended_wind_mph:g} mph sustained or "
                       f"{policy.suspended_gust_mph:g} mph gusts): all external work stops.")
    elif wind_mph >= policy.restricted_wind_mph or gust_mph >= policy.restricted_gust_mph:
        if verdict == "go":
            verdict = "restricted"
        reasons.append(f"Wind (sustained {wind_mph:.0f} mph, gusts {gust_mph:.0f} mph) is in the "
                       f"restricted band (from {policy.restricted_wind_mph:g} mph sustained or "
                       f"{policy.restricted_gust_mph:g} mph gusts): no work above 6 m, no "
                       "sheeting, panel handling or material hoisting.")
    if _is_sheet_work(activity) and wind_mph >= policy.sheet_stop_mph:
        verdict = "no-go"
        reasons.append(f"Sheet/panel handling stops at {policy.sheet_stop_mph:g} mph sustained, "
                       f"any height — current sustained wind is {wind_mph:.0f} mph.")
    if not reasons:
        reasons.append("Conditions are within all policy limits for external work.")

    return {
        "verdict": verdict,
        "activity": activity,
        "wind_sustained_mph": round(wind_mph, 1),
        "wind_gust_mph": round(gust_mph, 1),
        "wind_sustained_kmh": reading.wind_speed_kmh,
        "temp_c": temp,
        "reasons": reasons,
        "policy_source": policy.source_doc,
        "weather_source": reading.source,
        "reminder": "The supervisor applies these thresholds and makes the stop/go call; "
        "the Site Manager authorises resumption after a suspension.",
    }


def _is_sheet_work(activity: str) -> bool:
    return bool(_SHEET_WORDS & set(re.findall(r"[a-z]+", activity.lower())))
