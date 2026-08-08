"""Webhook backend for the ElevenLabs site-assistant agent."""
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import sops, weather
from app.config import CONTEXT_DEV_API_KEY, CONTEXT_DEV_BASE_URL, ROOT_DIR, SITE_LOCATION
from app.verdict import assess

app = FastAPI(title="Meridian Site Assistant tools")

_CHUNKS = sops.load_chunks()
_THRESHOLDS = sops.extract_thresholds(_CHUNKS)


class SearchRequest(BaseModel):
    query: str


class WeatherRequest(BaseModel):
    activity: str = "working on scaffolding"
    location: str | None = None


class LookupRequest(BaseModel):
    url: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "sop_docs": len({c.filename for c in _CHUNKS}), "thresholds": len(_THRESHOLDS)}


@app.post("/tools/search_sops")
def search_sops(req: SearchRequest) -> dict:
    """Retrieve SOP chunks with source attribution. Empty results mean the
    agent must refuse, not invent."""
    results = sops.search(req.query, _CHUNKS)
    return {
        "results": results,
        "guidance": "No company SOP covers this — say you don't know and defer."
        if not results
        else "Answer from these chunks only; name the source document aloud.",
    }


@app.post("/tools/check_weather")
async def check_weather(req: WeatherRequest) -> dict:
    """Live weather vs the threshold read from the company SOP."""
    reading = await weather.fetch_weather(req.location or SITE_LOCATION)
    return assess(reading, req.activity, _THRESHOLDS)


@app.post("/tools/web_lookup")
async def web_lookup(req: LookupRequest) -> dict:
    """Fetch official guidance / manufacturer docs as markdown via context.dev.
    Results rank BELOW company SOPs in source precedence."""
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{CONTEXT_DEV_BASE_URL}/web/scrape/markdown",
                headers={"Authorization": f"Bearer {CONTEXT_DEV_API_KEY}"},
                json={"url": req.url},
            )
            resp.raise_for_status()
            markdown = resp.json().get("data", {}).get("markdown", "")
    except (httpx.HTTPError, ValueError) as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "source": req.url,
        "markdown": markdown[:6000],
        "guidance": "External source — outranked by company SOPs. Name it and flag "
        "it is not company policy.",
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(ROOT_DIR) / "static" / "index.html")
