from __future__ import annotations

import os
import json
from collections.abc import AsyncIterator

import httpx

from app.models.types import AgentName
from app.services.rate_limiter import groq_limiter

MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def has_groq_key() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())


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

    async with groq_limiter:
        yield ("log", f"Starting Groq call with {MODEL}")
        token_count = 0
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
