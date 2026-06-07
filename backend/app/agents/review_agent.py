from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Any

from app.models.types import DiscoveryResult, MappingResult
from app.services.groq_service import stream_groq

AgentStream = AsyncIterator[tuple[str, Any]]

SYSTEM = """You are a senior production API integration reviewer and rewrite engineer.
Your job is to audit draft connector code, find real-world integration failures,
and return a corrected production-ready Python connector.

Review for:
1. Correct authentication for both services; never use client IDs as bearer tokens.
2. Correct data-read endpoints; avoid schema/metadata endpoints for record syncs.
3. Pagination for both source and target APIs.
4. Rate limiting and retry/backoff behavior.
5. Idempotent writes/upserts; no always-create duplicate behavior.
6. Required target payload fields and business-semantic correctness.
7. Per-record error isolation with ok/failed counters.
8. No mutable default arguments.
9. Explicit mapping functions; no fragile field-mapping if/elif loops.
10. Environment configuration with clear required variables.
11. Async client lifecycle using one shared httpx.AsyncClient context manager.
12. Safe CLI behavior, including dry-run where practical.

Return ONLY raw Python code. Do not include markdown fences or explanations."""


def strip_code_fence(raw: str) -> str:
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", raw)
    return (match.group(1) if match else raw).strip()


async def run_review_agent(
    discovery: DiscoveryResult,
    mapping: MappingResult,
    draft_code: str,
) -> AgentStream:
    source = discovery["source"]["name"]
    target = discovery["target"]["name"]
    yield ("log", f"Reviewing and hardening connector code for {source} to {target}.")

    prompt = f"""Audit and rewrite this connector for real-world readiness.

Source API discovery:
{discovery['source']}

Target API discovery:
{discovery['target']}

Field mappings:
{mapping['mappings']}

Draft connector code:
{draft_code[:12000]}

Production requirements:
- Preserve the intended integration direction: {source} as source, {target} as target.
- If a mapping is semantically unsafe, omit that sync path and leave a code comment explaining why.
- Include retries, pagination, rate-limit handling, idempotent upserts, per-record error isolation, and strict env var loading.
- Use async httpx, standard logging, clear type hints, and a __name__ == "__main__" guard.
- Prefer raw dict payloads unless schemas are truly known from discovery context.
- Return only the complete corrected Python file."""

    raw = ""
    async for kind, value in stream_groq(
        system_prompt=SYSTEM,
        user_prompt=prompt,
        agent="review",
        temperature=0.1,
        max_tokens=7000,
    ):
        if kind == "token":
            raw += value
        yield (kind, value)

    yield ("result", strip_code_fence(raw))
