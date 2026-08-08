"""Parse working limits out of the Meridian adverse-weather SOP text.

Every number used in a go/no-go verdict is read from the document —
never hardcoded (forbidden action A7).
"""
import re
from dataclasses import dataclass

from app.sops import Chunk


@dataclass(frozen=True)
class WeatherPolicy:
    restricted_wind_mph: float       # at/above: no work above 6 m
    suspended_wind_mph: float        # at/above: all external work stops
    restricted_gust_mph: float
    suspended_gust_mph: float
    sheet_stop_mph: float            # sheet/panel handling stops, any height
    heat_elevated_c: float           # at/above: mandatory rest breaks, buddy system
    heat_suspended_c: float          # at/above: all external work stops
    midday_start: str                # "12:30"
    midday_end: str                  # "15:00"
    midday_from: tuple[int, int]     # (month, day) e.g. (6, 15)
    midday_to: tuple[int, int]       # (9, 15)
    source_doc: str


_RESTRICTED = re.compile(
    r"\|\s*Restricted\s*\|\s*(?P<s_lo>\d+)[–-](?P<s_hi>\d+)\s*mph[^|]*\|"
    r"\s*(?P<g_lo>\d+)[–-](?P<g_hi>\d+)\s*mph"
)
_SHEET = re.compile(r"stop at\s*\**(?P<mph>\d+)\s*mph sustained", re.IGNORECASE)
_HEAT = re.compile(r"\|\s*Elevated\s*\|\s*(?P<lo>\d+)[–-](?P<hi>\d+)\s*°C")
_MIDDAY_HOURS = re.compile(r"prohibited between\s*\**(\d{1,2}:\d{2})\**\s*and\s*\**(\d{1,2}:\d{2})")
_MIDDAY_DATES = re.compile(r"[Bb]etween\s*\**(\d{1,2})\s+(\w+)\**\s+and\s+\**(\d{1,2})\s+(\w+)")

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june",
     "july", "august", "september", "october", "november", "december"])}


def extract_policy(chunks: list[Chunk]) -> WeatherPolicy | None:
    body, source = "", ""
    for chunk in chunks:
        if "Restricted" in chunk.text and "mph" in chunk.text:
            source = f"{chunk.doc_id} — {chunk.doc_title}"
            body = "\n".join(c.text for c in chunks if c.doc_id == chunk.doc_id)
            break
    if not body:
        return None
    wind = _RESTRICTED.search(body)
    sheet = _SHEET.search(body)
    heat = _HEAT.search(body)
    hours = _MIDDAY_HOURS.search(body)
    dates = _MIDDAY_DATES.search(body)
    if not (wind and sheet and heat and hours and dates):
        return None
    return WeatherPolicy(
        restricted_wind_mph=float(wind.group("s_lo")),
        suspended_wind_mph=float(wind.group("s_hi")),
        restricted_gust_mph=float(wind.group("g_lo")),
        suspended_gust_mph=float(wind.group("g_hi")),
        sheet_stop_mph=float(sheet.group("mph")),
        heat_elevated_c=float(heat.group("lo")),
        heat_suspended_c=float(heat.group("hi")),
        midday_start=hours.group(1),
        midday_end=hours.group(2),
        midday_from=(_MONTHS[dates.group(2).lower()], int(dates.group(1))),
        midday_to=(_MONTHS[dates.group(4).lower()], int(dates.group(3))),
        source_doc=source,
    )
