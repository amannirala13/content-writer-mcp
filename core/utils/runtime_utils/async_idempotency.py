# idempotency.py
from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any, Awaitable, Callable, Dict, Tuple, Optional

TCallable = Callable[[], Awaitable[Any]]

class AsyncIdempotency:
    """
    In-memory async idempotency with TTL and singleflight.
    - Uses monotonic clock for TTL.
    - Collapses concurrent calls for the same key.
    - Optional maxsize with simple FIFO eviction.
    """

    def __init__(self, ttl_seconds: float = 60.0, maxsize: int = 2048) -> None:
        self._ttl = float(ttl_seconds)
        self._maxsize = int(maxsize)
        self._lock = asyncio.Lock()
        # key -> (expires_at, value)
        self._done: Dict[str, Tuple[float, Any]] = {}
        # key -> Future in flight
        self._inflight: Dict[str, asyncio.Future] = {}

    @staticmethod
    def derive_key(namespace: str, payload: str) -> str:
        h = hashlib.sha256()
        h.update(namespace.encode("utf-8"))
        h.update(b"\x00")
        h.update(payload.encode("utf-8"))
        return h.hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        async with self._lock:
            item = self._done.get(key)
            if item and item[0] > now:
                return item[1]
            if item:
                # expired
                self._done.pop(key, None)
            return None

    async def put(self, key: str, value: Any) -> None:
        now = time.monotonic()
        async with self._lock:
            # prune expired
            self._prune_locked(now)
            # enforce maxsize
            if len(self._done) >= self._maxsize:
                # simple FIFO eviction
                oldest_key = next(iter(self._done.keys()))
                self._done.pop(oldest_key, None)
            self._done[key] = (now + self._ttl, value)

    async def run(self, key: str, fn: TCallable) -> Any:
        """
        Return cached result if fresh.
        If an identical call is already running, await it.
        Otherwise run fn(), cache it, and return the result.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        async with self._lock:
            # double-check after acquiring
            cached = await self.get(key)
            if cached is not None:
                return cached
            fut = self._inflight.get(key)
            if fut is None:
                fut = asyncio.get_event_loop().create_future()
                self._inflight[key] = fut

        try:
            result = await fn()
            await self.put(key, result)
            fut.set_result(result)
            return result
        except Exception as e:
            fut.set_exception(e)
            raise
        finally:
            async with self._lock:
                self._inflight.pop(key, None)

    def _prune_locked(self, now: float) -> None:
        expired = [k for k, (exp, _) in self._done.items() if exp <= now]
        for k in expired:
            self._done.pop(k, None)