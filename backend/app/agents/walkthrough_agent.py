from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.types import DiscoveryResult, MappingResult, WalkthroughResult
from app.services.groq_service import stream_groq
from app.utils.parse_json import extract_json

AgentStream = AsyncIterator[tuple[str, Any]]

SYSTEM = """You are a Developer Experience (DX) Engineer. Your job is to analyze generated integration code
and produce a clear, educational walkthrough guide.
Return ONLY valid JSON matching this schema:
{
  "overview": "Short explanation of how the connector works",
  "prerequisites": [{"key": "ENV_VAR_NAME", "description": "What this is", "required": true}],
  "steps": [
    {"title": "Step 1...", "description": "Explanation", "codeSnippet": "relevant code chunk"}
  ],
  "executionCommand": "python connector.py"
}"""


async def run_walkthrough_agent(
    discovery: DiscoveryResult,
    mapping: MappingResult,
    code: str,
) -> AgentStream:
    source = discovery["source"]["name"]
    target = discovery["target"]["name"]
    yield ("log", f"Analyzing generated code to build a walkthrough for {source} to {target}...")

    prompt = f"""Create a technical walkthrough for this generated integration.

Source: {source}
Target: {target}

Generated code to analyze:
{code[:6000]}

Explain the authentication strategy, the core data mapping logic, and provide exact execution instructions."""

    raw = ""
    async for kind, value in stream_groq(
        system_prompt=SYSTEM,
        user_prompt=prompt,
        agent="walkthrough",
        temperature=0.2,
        max_tokens=3000,
    ):
        if kind == "token":
            raw += value
        yield (kind, value)

    yield ("result", cast(WalkthroughResult, extract_json(raw)))
