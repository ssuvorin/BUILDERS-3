"""Thin async client for context.dev endpoints."""
import httpx

from app.config import CONTEXT_DEV_API_KEY, CONTEXT_DEV_BASE_URL


class ContextDevError(Exception):
    """Raised when context.dev is unreachable, errors out, or is unconfigured."""


async def post(path: str, payload: dict) -> dict:
    """POST to context.dev and return the response's `data` object."""
    if not CONTEXT_DEV_API_KEY:
        raise ContextDevError("CONTEXT_DEV_API_KEY is not set")
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{CONTEXT_DEV_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {CONTEXT_DEV_API_KEY}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("data") or {}
    except (httpx.HTTPError, ValueError) as exc:
        raise ContextDevError(str(exc)) from exc
