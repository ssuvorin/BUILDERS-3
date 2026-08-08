"""Live web search via the native context.dev /web/search endpoint.

Fills the gap between "fetch this exact URL" (web_lookup) and the agent
needing to FIND a source first. Returns titles + urls + snippets so the
agent can pick an authoritative page and fetch it with web_lookup —
results still rank below company data in the source hierarchy.
"""
import os
from urllib.parse import urlparse

from app import context_dev

_COUNTRY = os.getenv("SEARCH_COUNTRY", "ae")  # localize to the site's country
_OFFICIAL_DOMAINS = ("gov.ae", "u.ae", "gov.uk", "iso.org")


def _is_official(url: str) -> bool:
    """Match the hostname, not the URL string — 'example.com/page.gov.html'
    and 'osha.gov.phish.example' must not rank as official."""
    host = (urlparse(url).hostname or "").lower()
    return host.endswith(".gov") or any(
        host == d or host.endswith("." + d) for d in _OFFICIAL_DOMAINS
    )


def rank(results: list[dict], limit: int = 5) -> list[dict]:
    """Official sources first, then engine order. Trims payload for the LLM."""
    trimmed = [
        {
            "title": r.get("title", ""),
            "url": r["url"],
            "snippet": r.get("description", ""),
            "relevance": r.get("relevance", ""),
        }
        for r in results
        if r.get("url")
    ]
    trimmed.sort(key=lambda r: not _is_official(r["url"]))  # stable: engine order kept
    return trimmed[:limit]


async def search(query: str) -> list[dict]:
    data = await context_dev.post(
        "/web/search",
        {"query": query, "numResults": 10, "country": _COUNTRY},
    )
    return rank(data.get("results") or [])
