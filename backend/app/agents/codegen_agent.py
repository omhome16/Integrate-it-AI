from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Any

from app.models.types import DiscoveryResult, MappingResult
from app.services.groq_service import stream_groq

AgentStream = AsyncIterator[tuple[str, Any]]

SYSTEM = """You are a senior Python integration engineer. Generate production-minded
Python connector code for the provided API integration. Include async HTTP calls,
mapping logic, webhook signature verification, retries/backoff notes in comments,
and clear environment variable usage. Return code only."""


def strip_code_fence(raw: str) -> str:
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", raw)
    return (match.group(1) if match else raw).strip()


async def run_codegen_agent(discovery: DiscoveryResult, mapping: MappingResult) -> AgentStream:
    source = discovery["source"]["name"]
    target = discovery["target"]["name"]
    yield ("log", f"Generating Python connector code for {source} to {target}.")

    prompt = f"""Generate production-grade Python connector code for syncing {source} to {target}.

Source API:
{discovery['source']}

Target API:
{discovery['target']}

Field mappings:
{mapping['mappings']}

REQUIREMENTS for real-world tech standards:
1. Use `httpx.AsyncClient` for async HTTP requests.
2. Use `pydantic` models for strict data validation of source payloads.
3. Use `tenacity` (@retry) for exponential backoff and rate-limit handling.
4. Implement standard `logging` for observability.
5. Use strict Python type hints (PEP 585/604).
6. Ensure idempotent upserts to the target system.
7. Pull credentials securely from `os.getenv`.

Return only the raw Python code. Do not include markdown formatting or explanations."""

    raw = ""
    async for kind, value in stream_groq(
        system_prompt=SYSTEM,
        user_prompt=prompt,
        agent="codegen",
        temperature=0.15,
        max_tokens=4200,
    ):
        if kind == "token":
            raw += value
        yield (kind, value)

    yield ("result", strip_code_fence(raw))
