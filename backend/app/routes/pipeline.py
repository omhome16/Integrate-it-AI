from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pipeline")

from app.agents.codegen_agent import run_codegen_agent
from app.agents.discovery_agent import run_discovery_agent
from app.agents.mapping_agent import run_mapping_agent
from app.agents.walkthrough_agent import run_walkthrough_agent
from app.models.types import (
    AgentName,
    DiscoveryResult,
    MappingResult,
    WalkthroughResult,
    PipelineRequest,
    PipelineResults,
)
from app.utils.sse import sse_event

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


async def consume_agent(agent: AgentName, stream: AsyncIterator[tuple[str, Any]]):
    result = None
    async for kind, value in stream:
        if kind == "log":
            yield sse_event("log", agent, {"message": value})
        elif kind == "token":
            yield sse_event("agent_token", agent, {"token": value})
        elif kind == "result":
            result = value
    yield sse_event("agent_done", agent, result)
    return


@router.post("/run")
async def run_pipeline(request: PipelineRequest) -> StreamingResponse:
    async def event_stream():
        results: PipelineResults = {}
        current_agent: AgentName = "discovery"

        try:
            current_agent = "discovery"
            logger.info(f"Starting {current_agent} agent for source={request.source}, target={request.target}")
            yield sse_event("agent_start", current_agent)
            discovery: DiscoveryResult | None = None
            async for kind, value in run_discovery_agent(request.source, request.target):
                if kind == "log":
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    discovery = value
            if discovery is None:
                raise RuntimeError("Discovery agent did not return a result.")
            results["discovery"] = discovery
            yield sse_event("agent_done", current_agent, discovery)
            logger.info(f"{current_agent} agent completed.")
            await asyncio.sleep(4)

            current_agent = "mapping"
            logger.info(f"Starting {current_agent} agent...")
            yield sse_event("agent_start", current_agent)
            mapping: MappingResult | None = None
            async for kind, value in run_mapping_agent(discovery):
                if kind == "log":
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    mapping = value
            if mapping is None:
                raise RuntimeError("Mapping agent did not return a result.")
            results["mapping"] = mapping
            yield sse_event("agent_done", current_agent, mapping)
            logger.info(f"{current_agent} agent completed.")
            await asyncio.sleep(4)

            current_agent = "codegen"
            logger.info(f"Starting {current_agent} agent...")
            yield sse_event("agent_start", current_agent)
            code: str | None = None
            async for kind, value in run_codegen_agent(discovery, mapping):
                if kind == "log":
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    code = value
            if code is None:
                raise RuntimeError("Code generation agent did not return a result.")
            results["codegen"] = code
            yield sse_event("agent_done", current_agent, code)
            logger.info(f"{current_agent} agent completed.")
            await asyncio.sleep(4)

            current_agent = "walkthrough"
            logger.info(f"Starting {current_agent} agent...")
            yield sse_event("agent_start", current_agent)
            walkthrough: WalkthroughResult | None = None
            async for kind, value in run_walkthrough_agent(discovery, mapping, code):
                if kind == "log":
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    walkthrough = value
            if walkthrough is None:
                raise RuntimeError("Walkthrough agent did not return a result.")
            results["walkthrough"] = walkthrough
            yield sse_event("agent_done", current_agent, walkthrough)
            logger.info(f"{current_agent} agent completed. Pipeline finished.")
            yield sse_event("pipeline_done", current_agent, results)

        except Exception as exc:
            logger.error(f"Error in {current_agent} agent: {exc}", exc_info=True)
            yield sse_event("agent_error", current_agent, {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
