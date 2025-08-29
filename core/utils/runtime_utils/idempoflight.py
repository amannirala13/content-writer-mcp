# idempoflight.py
"""
Idempotency + singleflight in one tiny file.

Features
- In-memory TTL cache using a monotonic clock
- Concurrent call collapse (singleflight) per key
- Async-first design with safe sync wrappers
- Stable SHA-256 key builder

Notes on sync usage
- Sync wrappers cannot be executed from inside an already running event loop.
  If you need this, call the async function version or move the call out of the loop.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import inspect
import time
from typing import Any, Callable, Dict, Optional, Tuple, Union, Awaitable


__all__ = [
    "idempotent",
    "singleflight",
    "make_key",
    "InMemoryResultCache",
    "SingleflightGroup",
]


# -------------------------
# Utilities
# -------------------------

def make_key(namespace: str, *parts: Union[str, bytes]) -> str:
    """
    Build a stable SHA-256 key from a namespace and ordered parts.

    Example:
        key = make_key("content-structure", topic_str)
    """
    h = hashlib.sha256(namespace.encode("utf-8"))
    for p in parts:
        if isinstance(p, str):
            p = p.encode("utf-8")
        h.update(b"\x00")
        h.update(p)
    return h.hexdigest()

def topic_key(
    class_name: str,
    fallback_id: str,
    request_id: str | None,
    topic: str
) -> str:
    """
    Build a consistent idempotency key for topic-based tools.

    Priority:
      1. Use explicit request_id if provided
      2. Otherwise derive a SHA256 hash of (class_name.fallback_id, topic)

    Example:
        key = topic_key("ContentStrategist", "generate_content", None, "EV analytics")
    """
    if request_id:
        return request_id
    return make_key(f"{class_name}.{fallback_id}", topic)


def _args_key(fn: Any, args: tuple, kwargs: dict) -> str:
    """
    Default key function based on fully qualified name + repr of args and kwargs.
    Uses getattr to satisfy strict type checkers.
    """
    module = getattr(fn, "__module__", "unknown")
    qualname = getattr(fn, "__qualname__", getattr(fn, "__name__", "callable"))
    name = f"{module}.{qualname}"
    h = hashlib.sha256(name.encode("utf-8"))
    for a in args:
        h.update(b"\x01")
        h.update(repr(a).encode("utf-8"))
    for k in sorted(kwargs.keys()):
        h.update(b"\x02")
        h.update(k.encode("utf-8"))
        h.update(repr(kwargs[k]).encode("utf-8"))
    return h.hexdigest()


# -------------------------
# Cache
# -------------------------

class InMemoryResultCache:
    """
    Simple in-memory TTL cache guarded by an asyncio.Lock.
    Uses time.monotonic for TTL accuracy across clock changes.

    This cache is safe for async usage. Sync wrappers coordinate by creating
    a short-lived loop when needed.
    """

    def __init__(self, ttl_seconds: float = 60.0, maxsize: int = 4096) -> None:
        self.ttl = float(ttl_seconds)
        self.maxsize = int(maxsize)
        self._lock = asyncio.Lock()
        self._store: Dict[str, Tuple[float, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        async with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            exp, val = item
            if exp <= now:
                self._store.pop(key, None)
                return None
            return val

    async def put(self, key: str, value: Any) -> None:
        now = time.monotonic()
        async with self._lock:
            self._prune_locked(now)
            if len(self._store) >= self.maxsize:
                # FIFO eviction
                # keep a local reference to avoid any shadowing warnings on pop
                store = self._store
                oldest = next(iter(store.keys()))
                store.pop(oldest, None)
            self._store[key] = (now + self.ttl, value)

    def _prune_locked(self, now: float) -> None:
        store = self._store
        expired = [k for k, (exp, _) in store.items() if exp <= now]
        for k in expired:
            store.pop(k, None)


# -------------------------
# Singleflight
# -------------------------

class SingleflightGroup:
    """
    Collapses concurrent calls to the same key into one producer execution.
    Other callers await the same Future and receive the same result or exception.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._inflight: Dict[str, asyncio.Future] = {}

    async def do(self, key: str, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        """
        Run or join a single in-flight coroutine for 'key'.
        'coro_factory' must return an Awaitable each time it is called.
        """
        async with self._lock:
            inflight = self._inflight
            fut = inflight.get(key)
            if fut is None:
                fut = asyncio.get_event_loop().create_future()
                inflight[key] = fut

                async def _runner() -> None:
                    try:
                        result = await coro_factory()
                        fut.set_result(result)
                    except Exception as e:
                        fut.set_exception(e)
                    finally:
                        async with self._lock:
                            # use local ref again to avoid any shadowing confusion
                            inflight_local = self._inflight
                            inflight_local.pop(key, None)

                asyncio.create_task(_runner())

        return await fut


# -------------------------
# Decorators
# -------------------------

def idempotent(
    ttl: float = 60.0,
    cache: Optional[InMemoryResultCache] = None,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Cache results for 'ttl' seconds keyed by args or a custom key_func.
    Works best with async functions. Sync functions are supported when called
    outside of a running event loop.
    """
    local_cache = cache or InMemoryResultCache(ttl_seconds=ttl)

    def decorator(fn: Callable[..., Any]):
        is_async = inspect.iscoroutinefunction(fn)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else _args_key(fn, args, kwargs)
            cached = await local_cache.get(key)
            if cached is not None:
                return cached
            result = await fn(*args, **kwargs)
            await local_cache.put(key, result)
            return result

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            # Running inside an active loop is not supported for sync wrappers.
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, safe to create a temporary one.
                pass
            else:
                raise RuntimeError(
                    "Sync idempotent wrapper called inside a running event loop. "
                    "Use the async function or call from a non-async context."
                )

            async def _runner():
                key = key_func(*args, **kwargs) if key_func else _args_key(fn, args, kwargs)
                cached = await local_cache.get(key)
                if cached is not None:
                    return cached
                res = await asyncio.to_thread(fn, *args, **kwargs)
                await local_cache.put(key, res)
                return res

            return asyncio.run(_runner())

        return async_wrapper if is_async else sync_wrapper

    return decorator


def singleflight(
    group: Optional[SingleflightGroup] = None,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Collapse concurrent calls for the same key into a single execution.
    """
    sf = group or SingleflightGroup()

    def decorator(fn: Callable[..., Any]):
        is_async = inspect.iscoroutinefunction(fn)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else _args_key(fn, args, kwargs)

            async def _produce():
                return await fn(*args, **kwargs)

            return await sf.do(key, _produce)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            # Running inside an active loop is not supported for sync wrappers.
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, safe to create a temporary one.
                pass
            else:
                raise RuntimeError(
                    "Sync singleflight wrapper called inside a running event loop. "
                    "Use the async function or call from a non-async context."
                )

            async def _produce():
                return await asyncio.to_thread(fn, *args, **kwargs)

            key = key_func(*args, **kwargs) if key_func else _args_key(fn, args, kwargs)
            return asyncio.run(sf.do(key, _produce))

        return async_wrapper if is_async else sync_wrapper

    return decorator