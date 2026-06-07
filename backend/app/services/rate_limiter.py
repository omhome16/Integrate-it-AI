from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    def __init__(self, min_delay_seconds: float = 12.0) -> None:
        self.min_delay_seconds = min_delay_seconds
        self._lock = asyncio.Lock()
        self._last_release = 0.0

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self._lock.acquire()
        elapsed = time.monotonic() - self._last_release
        if elapsed < self.min_delay_seconds:
            await asyncio.sleep(self.min_delay_seconds - elapsed)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._last_release = time.monotonic()
        self._lock.release()


groq_limiter = AsyncRateLimiter(12.0)
