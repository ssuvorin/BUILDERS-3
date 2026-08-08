"""Single-session lease broker for the shared demo voice agent.

Root-cause fix for parallel agents talking over each other: the browser
cannot coordinate sessions across devices, so the backend owns the truth.
A client must hold the lease to run a conversation; the lease expires
unless heartbeats arrive, so a crashed/closed tab frees the slot on its own.
"""
import os
import secrets
import time
from dataclasses import dataclass

LEASE_TTL_SECONDS = float(os.getenv("VOICE_LEASE_TTL", "45"))


@dataclass
class _Lease:
    lease_id: str
    expires_at: float


_current: _Lease | None = None


def _expired(lease: _Lease) -> bool:
    return time.monotonic() >= lease.expires_at


def acquire() -> str | None:
    """Grant the lease if free (or the holder went silent). None = busy."""
    global _current
    if _current is not None and not _expired(_current):
        return None
    _current = _Lease(secrets.token_urlsafe(16), time.monotonic() + LEASE_TTL_SECONDS)
    return _current.lease_id


def heartbeat(lease_id: str) -> bool:
    """Extend the lease. False = lease lost (expired or superseded)."""
    if _current is None or _current.lease_id != lease_id or _expired(_current):
        return False
    _current.expires_at = time.monotonic() + LEASE_TTL_SECONDS
    return True


def release(lease_id: str) -> None:
    global _current
    if _current is not None and _current.lease_id == lease_id:
        _current = None
