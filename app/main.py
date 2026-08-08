"""HeatSafe Voice Copilot — webhook backend for the ElevenLabs agent."""
import asyncio
import contextlib
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import asklog, context_dev, sops, voice_broker, weather, websearch
from app.config import ROOT_DIR, SITE_LOCATION
from app.policy import extract_policy
from app.verdict import assess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("heatsafe")


async def _weather_refresher() -> None:
    """Keep the site reading warm so the voice path never waits on context.dev."""
    while True:
        try:
            reading = await weather.refresh(SITE_LOCATION)
            if not reading.available:
                logger.warning("weather refresh failed: %s", reading.error)
        except Exception:
            logger.exception("weather refresher crashed; retrying next cycle")
        await asyncio.sleep(weather.REFRESH_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_weather_refresher())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="HeatSafe Voice Copilot tools", lifespan=lifespan)


@app.middleware("http")
async def log_tool_timing(request: Request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - started
    if request.url.path.startswith("/tools/"):
        logger.info("%s took %.2fs", request.url.path, elapsed)
    return response

_CHUNKS = sops.load_chunks()
_POLICY = extract_policy(_CHUNKS)


class SearchRequest(BaseModel):
    query: str


class WeatherRequest(BaseModel):
    activity: str = "working on scaffolding"
    location: str | None = None


class LookupRequest(BaseModel):
    url: str


class LeaseRequest(BaseModel):
    lease_id: str


@app.post("/api/voice-lease")
async def voice_lease_acquire(response: Response) -> dict:
    """Acquire a session slot (up to VOICE_MAX_SESSIONS concurrent)."""
    lease_id = await voice_broker.broker.acquire()
    active = await voice_broker.broker.active()
    if lease_id is None:
        response.status_code = 409
        return {"granted": False, "reason": "all voice session slots are busy",
                "active": active, "max": voice_broker.MAX_SESSIONS}
    return {"granted": True, "lease_id": lease_id,
            "heartbeat_seconds": max(1, int(voice_broker.LEASE_TTL_SECONDS // 3)),
            "active": active, "max": voice_broker.MAX_SESSIONS}


@app.post("/api/voice-lease/heartbeat")
async def voice_lease_heartbeat(req: LeaseRequest, response: Response) -> dict:
    if not await voice_broker.broker.heartbeat(req.lease_id):
        response.status_code = 410
        return {"ok": False, "reason": "lease lost"}
    return {"ok": True}


@app.post("/api/voice-lease/release")
async def voice_lease_release(req: LeaseRequest) -> dict:
    await voice_broker.broker.release(req.lease_id)
    return {"ok": True}


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "sop_docs": len({c.filename for c in _CHUNKS}),
        "policy_loaded": _POLICY is not None,
    }


@app.get("/analytics/learn-list")
def learn_list() -> dict:
    """Supervisor-facing: most-asked topics (onboarding / toolbox-talk
    material) and questions no company document covers (SOP gaps)."""
    return asklog.learn_list()


@app.post("/tools/search_sops")
def search_sops(req: SearchRequest) -> dict:
    """Retrieve SOP chunks with source attribution. Empty results mean the
    agent moves down the source hierarchy (web_lookup), never invents."""
    results = sops.search(req.query, _CHUNKS)
    topic = f"{results[0]['source']} — {results[0]['section']}" if results else None
    asklog.record("procedure", req.query, topic, covered=bool(results))
    return {
        "results": results,
        "guidance": "No company SOP covers this — say so, then offer official "
        "guidance via web_lookup (flag it as not company policy). Refuse and "
        "defer only if that finds nothing. Do not invent."
        if not results
        else "Answer from these chunks only; name the source document aloud.",
    }


class WebSearchRequest(BaseModel):
    query: str


@app.post("/tools/web_search")
async def web_search(req: WebSearchRequest) -> dict:
    """Live web search via context.dev. Official sources ranked first.
    The agent picks a result and fetches it with web_lookup."""
    try:
        results = await websearch.search(req.query)
    except context_dev.ContextDevError as exc:
        return {"available": False, "error": str(exc), "results": []}
    asklog.record("web_search", req.query, f"web: {req.query.lower().strip()}",
                  covered=bool(results))
    return {
        "available": True,
        "results": results,
        "guidance": "Pick the most authoritative result (regulator/manufacturer "
        "first), fetch it with web_lookup, and answer from what the page says. "
        "Name the source aloud and flag it as not company policy."
        if results
        else "Nothing relevant found on the live web either — now refuse and "
        "defer to the supervisor.",
    }


@app.post("/tools/check_weather")
async def check_weather(req: WeatherRequest, request: Request) -> dict:
    """Site conditions vs the policy bands. Answers from the warm snapshot;
    blocks on a live fetch only when there is no fresh reading to serve
    (first boot, or a stale location the background refresher doesn't cover)."""
    location = req.location or SITE_LOCATION
    reading, age = weather.snapshot(location)
    if not reading.available:
        reading = await weather.refresh(location)
        age = 0.0 if reading.available else None
    result = assess(reading, req.activity, _POLICY)
    if age is not None:
        result["reading_age_seconds"] = int(age)
    if "x-heatsafe-ui" not in request.headers:  # UI page-load polls aren't worker questions
        asklog.record("conditions", req.activity, f"conditions: {req.activity.lower().strip()}",
                      covered=result.get("verdict") != "unknown")
    return result


@app.post("/tools/web_lookup")
async def web_lookup(req: LookupRequest) -> dict:
    """Fetch official guidance / manufacturer docs as markdown via context.dev.
    Results rank BELOW company SOPs in source precedence."""
    try:
        data = await context_dev.post("/web/scrape/markdown", {"url": req.url})
    except context_dev.ContextDevError as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "source": req.url,
        "markdown": data.get("markdown", "")[:6000],
        "guidance": "External source — outranked by company SOPs. Name it and flag "
        "it is not company policy.",
    }


app.mount("/static", StaticFiles(directory=Path(ROOT_DIR) / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(ROOT_DIR) / "static" / "index.html")


@app.get("/test")
def test_console() -> FileResponse:
    return FileResponse(Path(ROOT_DIR) / "static" / "test.html")


@app.get("/flow")
def architecture_flow() -> FileResponse:
    """The architecture and decision-flow diagram, rendered.

    Lives in docs/ because it is documentation, but GitHub serves .html as
    source rather than rendering it — so it gets a route.
    """
    return FileResponse(Path(ROOT_DIR) / "docs" / "architecture-flow.html")
