from __future__ import annotations

import os
import json
import asyncio
from collections.abc import AsyncIterator

import httpx

from app.models.types import AgentName
from app.services.rate_limiter import groq_limiter

MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MAX_RETRIES = 3
GROQ_429_BACKOFF_SECONDS = 30.0


def has_groq_key() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())


def retry_after_seconds(response: httpx.Response) -> float:
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return GROQ_429_BACKOFF_SECONDS
    try:
        return max(float(retry_after), 1.0)
    except ValueError:
        return GROQ_429_BACKOFF_SECONDS


async def stream_groq(
    *,
    system_prompt: str,
    user_prompt: str,
    agent: AgentName,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> AsyncIterator[tuple[str, str]]:
    if not has_groq_key():
        raise RuntimeError("GROQ_API_KEY is not configured.")

    payload = {
        "model": MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, GROQ_MAX_RETRIES + 2):
        token_count = 0
        try:
            async with groq_limiter:
                attempt_text = f" attempt {attempt}" if attempt > 1 else ""
                yield ("log", f"Starting Groq call with {MODEL}{attempt_text}")

                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", GROQ_URL, headers=headers, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue

                            data = line.removeprefix("data: ").strip()
                            if not data or data == "[DONE]":
                                continue

                            chunk = json.loads(data)
                            token = chunk["choices"][0].get("delta", {}).get("content", "")
                            if token:
                                token_count += 1
                                yield ("token", token)

                yield ("log", f"Streamed {token_count} chunks.")
                return
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt > GROQ_MAX_RETRIES:
                raise

            delay = retry_after_seconds(exc.response) * attempt
            yield ("log", f"Groq rate limit hit. Waiting {delay:.0f}s before retry {attempt + 1}.")
            await asyncio.sleep(delay)
