from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    def __init__(self, min_delay_seconds: float = 2.5) -> None:
        self.min_delay_seconds = min_delay_seconds
        self._lock = asyncio.Lock()
        self._last_start = 0.0

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self._lock.acquire()
        elapsed = time.monotonic() - self._last_start
        if elapsed < self.min_delay_seconds:
            await asyncio.sleep(self.min_delay_seconds - elapsed)
        self._last_start = time.monotonic()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._lock.release()


groq_limiter = AsyncRateLimiter(2.5)
