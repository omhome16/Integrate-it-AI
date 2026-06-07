from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, cast

from duckduckgo_search import DDGS

from app.models.types import DiscoveryResult
from app.services.groq_service import stream_groq
from app.utils.parse_json import extract_json

AgentStream = AsyncIterator[tuple[str, Any]]

SYSTEM = """You are an API Discovery Agent specializing in enterprise SaaS integration.
Given two service names and their real-world documentation context, return a comprehensive JSON object describing both APIs.
Use the provided ground truth context to generate realistic endpoint paths and auth methods.
Return ONLY valid JSON with source and target objects.
Each API must include name, baseUrl, auth, and 5-8 endpoints with method, path, description, and optional params."""

def search_docs(query: str, max_results: int = 3) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No documentation found."
            return "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
    except Exception as e:
        return f"Search failed: {e}"


async def run_discovery_agent(source: str, target: str) -> AgentStream:
    yield ("log", f"Searching web for real API documentation for {source} and {target}...")
    
    # Run synchronous search in a thread to avoid blocking the event loop
    source_context = await asyncio.to_thread(search_docs, f"{source} API documentation endpoints reference", 3)
    target_context = await asyncio.to_thread(search_docs, f"{target} API documentation endpoints reference", 3)
    
    yield ("log", "Deep thinking on optimal integration path based on search results...")

    prompt = (
        f'Discover and document the APIs for "{source}" as source and "{target}" '
        "as target. Focus on endpoints needed for real-time data synchronization.\n\n"
        f"--- GROUND TRUTH CONTEXT FOR {source.upper()} ---\n{source_context}\n\n"
        f"--- GROUND TRUTH CONTEXT FOR {target.upper()} ---\n{target_context}\n\n"
        "Ensure all endpoints are accurate and based on the context provided."
    )
    raw = ""
    async for kind, value in stream_groq(
        system_prompt=SYSTEM,
        user_prompt=prompt,
        agent="discovery",
        temperature=0.15,
        max_tokens=3000,
    ):
        if kind == "token":
            raw += value
        yield (kind, value)

    result = cast(DiscoveryResult, extract_json(raw))
    if "source" not in result or "target" not in result:
        raise ValueError("Discovery agent returned an invalid structure.")
    yield ("result", result)
