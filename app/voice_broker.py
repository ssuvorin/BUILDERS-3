"""Voice session lease broker — capacity-based, Redis-backed.

Root-cause design: the browser cannot coordinate sessions across tabs and
devices, so the backend owns the truth about who may talk to the agent.

- Up to VOICE_MAX_SESSIONS concurrent conversations (testing: N, demo: 1).
- Each session holds a lease that expires unless heartbeats arrive, so a
  crashed or closed tab frees its slot by TTL on its own.
- State lives in Redis (atomic acquire via Lua, native expiry semantics,
  shared across processes/replicas). When Redis is unreachable the broker
  degrades to a single-process in-memory store so the demo never dies.
"""
import logging
import os
import secrets
import time

import redis.asyncio as aioredis
from redis.exceptions import RedisError

logger = logging.getLogger("heatsafe.voice_broker")

MAX_SESSIONS = int(os.getenv("VOICE_MAX_SESSIONS", "3"))
LEASE_TTL_SECONDS = float(os.getenv("VOICE_LEASE_TTL", "45"))
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
_ZSET_KEY = "heatsafe:voice:leases"

# prune expired members, then add the new lease only if capacity remains
_ACQUIRE_LUA = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
if redis.call('ZCARD', KEYS[1]) < tonumber(ARGV[2]) then
  redis.call('ZADD', KEYS[1], ARGV[3], ARGV[4])
  return 1
end
return 0
"""

# extend only a lease that still exists and has not expired
_HEARTBEAT_LUA = """
if redis.call('ZSCORE', KEYS[1], ARGV[1]) and
   tonumber(redis.call('ZSCORE', KEYS[1], ARGV[1])) > tonumber(ARGV[2]) then
  redis.call('ZADD', KEYS[1], ARGV[3], ARGV[1])
  return 1
end
return 0
"""


class InMemoryBroker:
    """Single-process fallback with identical semantics."""

    def __init__(self, max_sessions: int = MAX_SESSIONS, ttl: float = LEASE_TTL_SECONDS):
        self._max = max_sessions
        self._ttl = ttl
        self._leases: dict[str, float] = {}

    def _prune(self) -> None:
        now = time.time()
        self._leases = {k: exp for k, exp in self._leases.items() if exp > now}

    async def acquire(self) -> str | None:
        self._prune()
        if len(self._leases) >= self._max:
            return None
        lease_id = secrets.token_urlsafe(16)
        self._leases[lease_id] = time.time() + self._ttl
        return lease_id

    async def heartbeat(self, lease_id: str) -> bool:
        self._prune()
        if lease_id not in self._leases:
            return False
        self._leases[lease_id] = time.time() + self._ttl
        return True

    async def release(self, lease_id: str) -> None:
        self._leases.pop(lease_id, None)

    async def active(self) -> int:
        self._prune()
        return len(self._leases)


class RedisBroker:
    def __init__(self, client: aioredis.Redis, max_sessions: int = MAX_SESSIONS,
                 ttl: float = LEASE_TTL_SECONDS):
        self._redis = client
        self._max = max_sessions
        self._ttl = ttl
        self._acquire = client.register_script(_ACQUIRE_LUA)
        self._heartbeat = client.register_script(_HEARTBEAT_LUA)

    async def acquire(self) -> str | None:
        lease_id = secrets.token_urlsafe(16)
        now = time.time()
        granted = await self._acquire(
            keys=[_ZSET_KEY], args=[now, self._max, now + self._ttl, lease_id]
        )
        return lease_id if granted else None

    async def heartbeat(self, lease_id: str) -> bool:
        now = time.time()
        return bool(await self._heartbeat(
            keys=[_ZSET_KEY], args=[lease_id, now, now + self._ttl]
        ))

    async def release(self, lease_id: str) -> None:
        await self._redis.zrem(_ZSET_KEY, lease_id)

    async def active(self) -> int:
        await self._redis.zremrangebyscore(_ZSET_KEY, "-inf", time.time())
        return await self._redis.zcard(_ZSET_KEY)


class Broker:
    """Facade: Redis when reachable, sticky in-memory fallback otherwise."""

    def __init__(self):
        self._impl: RedisBroker | InMemoryBroker | None = None

    async def _backend(self) -> RedisBroker | InMemoryBroker:
        if self._impl is None:
            try:
                client = aioredis.from_url(
                    REDIS_URL, decode_responses=True, socket_connect_timeout=1,
                    socket_timeout=1,
                )
                await client.ping()
                self._impl = RedisBroker(client)
                logger.info("voice broker: redis backend (%s), max_sessions=%s",
                            REDIS_URL, MAX_SESSIONS)
            except (RedisError, OSError) as exc:
                self._impl = InMemoryBroker()
                logger.warning("voice broker: redis unavailable (%s) — in-memory fallback", exc)
        return self._impl

    async def acquire(self) -> str | None:
        return await (await self._backend()).acquire()

    async def heartbeat(self, lease_id: str) -> bool:
        return await (await self._backend()).heartbeat(lease_id)

    async def release(self, lease_id: str) -> None:
        await (await self._backend()).release(lease_id)

    async def active(self) -> int:
        return await (await self._backend()).active()


broker = Broker()
