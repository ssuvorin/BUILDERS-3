"""Live web search via the native context.dev /web/search endpoint.

Fills the gap between "fetch this exact URL" (web_lookup) and the agent
needing to FIND a source first. Returns titles + urls + snippets so the
agent can pick an authoritative page and fetch it with web_lookup —
results still rank below company data in the source hierarchy.
"""
import os

from app import context_dev

_COUNTRY = os.getenv("SEARCH_COUNTRY", "ae")  # localize to the site's country
_PREFERRED = ("gov.ae", "hse.gov.uk", "osha.gov", ".gov", "iso.org")


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
    official = [r for r in trimmed if any(d in r["url"] for d in _PREFERRED)]
    rest = [r for r in trimmed if r not in official]
    return (official + rest)[:limit]


async def search(query: str) -> list[dict]:
    data = await context_dev.post(
        "/web/search",
        {"query": query, "numResults": 10, "country": _COUNTRY},
    )
    return rank(data.get("results", []))
