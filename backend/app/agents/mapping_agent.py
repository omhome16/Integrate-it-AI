from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.types import DiscoveryResult, MappingResult
from app.services.groq_service import stream_groq
from app.utils.parse_json import extract_json

AgentStream = AsyncIterator[tuple[str, Any]]

SYSTEM = """You are a Data Field Mapping Specialist for enterprise API integrations.
Given two API schemas, produce detailed field-level mappings. Return ONLY valid JSON:
{ "mappings": [], "unmappedSource": [], "unmappedTarget": [], "totalFields": number,
"mappedPercent": number }. Each mapping needs sourceField, sourceType, targetField,
targetType, transformation, confidence, and notes."""


async def run_mapping_agent(discovery: DiscoveryResult) -> AgentStream:
    source = discovery["source"]["name"]
    target = discovery["target"]["name"]
    yield ("log", f"Mapping fields from {source} to {target}.")

    prompt = f"""Create a field mapping for syncing data from {source} to {target}.

Source API: {source} ({discovery['source']['baseUrl']})
Key source endpoints: {', '.join(item['path'] for item in discovery['source']['endpoints'])}

Target API: {target} ({discovery['target']['baseUrl']})
Key target endpoints: {', '.join(item['path'] for item in discovery['target']['endpoints'])}

Infer realistic fields from both systems and generate at least 12 mappings."""

    raw = ""
    async for kind, value in stream_groq(
        system_prompt=SYSTEM,
        user_prompt=prompt,
        agent="mapping",
        temperature=0.2,
        max_tokens=3500,
    ):
        if kind == "token":
            raw += value
        yield (kind, value)

    result = cast(MappingResult, extract_json(raw))
    
    # Force real-world metric calculation based on actual output
    mappings = result.get("mappings", [])
    unmapped_source = result.get("unmappedSource", [])
    unmapped_target = result.get("unmappedTarget", [])
    
    total = len(mappings) + len(unmapped_source) + len(unmapped_target)
    result["totalFields"] = total
    result["mappedPercent"] = round((len(mappings) / total * 100)) if total > 0 else 0
    
    yield ("result", result)
