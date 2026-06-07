from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pipeline")

from app.agents.codegen_agent import run_codegen_agent
from app.agents.discovery_agent import run_discovery_agent
from app.agents.mapping_agent import run_mapping_agent
from app.agents.review_agent import run_review_agent
from app.agents.walkthrough_agent import run_walkthrough_agent
from app.models.types import (
    AgentName,
    DiscoveryResult,
    MappingResult,
    WalkthroughResult,
    PipelineRequest,
    PipelineResults,
)
from app.services.report_service import REPORTS_DIR, markdown_to_pdf_bytes, save_markdown_report
from app.services.result_normalizer import (
    normalize_discovery_result,
    normalize_mapping_result,
    normalize_walkthrough_result,
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


@router.get("/reports/{file_name}")
async def get_report(file_name: str) -> FileResponse:
    if Path(file_name).name != file_name or not file_name.endswith(".md"):
        raise HTTPException(status_code=400, detail="Invalid report file name.")

    report_path = REPORTS_DIR / file_name
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")

    return FileResponse(report_path, media_type="text/markdown", filename=file_name)


@router.get("/reports/{file_name}/pdf")
async def get_report_pdf(file_name: str) -> Response:
    if Path(file_name).name != file_name or not file_name.endswith(".md"):
        raise HTTPException(status_code=400, detail="Invalid report file name.")

    report_path = REPORTS_DIR / file_name
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")

    pdf_name = f"{file_name[:-3]}.pdf"
    pdf_bytes = markdown_to_pdf_bytes(report_path.read_text(encoding="utf-8"))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
    )


@router.post("/run")
async def run_pipeline(request: PipelineRequest) -> StreamingResponse:
    async def event_stream():
        results: PipelineResults = {}
        report_logs: list[str] = []
        current_agent: AgentName = "discovery"

        try:
            current_agent = "discovery"
            logger.info(f"Starting {current_agent} agent for source={request.source}, target={request.target}")
            yield sse_event("agent_start", current_agent)
            discovery: DiscoveryResult | None = None
            async for kind, value in run_discovery_agent(request.source, request.target):
                if kind == "log":
                    report_logs.append(f"[Discovery] {value}")
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    discovery = normalize_discovery_result(value)
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
                    report_logs.append(f"[Mapping] {value}")
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    mapping = normalize_mapping_result(value)
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
                    report_logs.append(f"[Codegen] {value}")
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    code = str(value)
            if code is None:
                raise RuntimeError("Code generation agent did not return a result.")
            results["codegen"] = code
            yield sse_event("agent_done", current_agent, code)
            logger.info(f"{current_agent} agent completed.")
            await asyncio.sleep(4)

            current_agent = "review"
            logger.info(f"Starting {current_agent} agent...")
            yield sse_event("agent_start", current_agent)
            reviewed_code: str | None = None
            async for kind, value in run_review_agent(discovery, mapping, code):
                if kind == "log":
                    report_logs.append(f"[Review] {value}")
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    reviewed_code = str(value)
            if reviewed_code is None:
                raise RuntimeError("Review agent did not return a result.")
            results["review"] = reviewed_code
            yield sse_event("agent_done", current_agent, reviewed_code)
            logger.info(f"{current_agent} agent completed.")
            await asyncio.sleep(4)

            current_agent = "walkthrough"
            logger.info(f"Starting {current_agent} agent...")
            yield sse_event("agent_start", current_agent)
            walkthrough: WalkthroughResult | None = None
            async for kind, value in run_walkthrough_agent(discovery, mapping, reviewed_code):
                if kind == "log":
                    report_logs.append(f"[Walkthrough] {value}")
                    yield sse_event("log", current_agent, {"message": value})
                elif kind == "token":
                    yield sse_event("agent_token", current_agent, {"token": value})
                elif kind == "result":
                    walkthrough = normalize_walkthrough_result(value)
            if walkthrough is None:
                raise RuntimeError("Walkthrough agent did not return a result.")
            results["walkthrough"] = walkthrough
            yield sse_event("agent_done", current_agent, walkthrough)

            report = save_markdown_report(request, results, report_logs)
            results["report"] = report
            report_message = f"Markdown report saved to {report['path']}"
            report_logs.append(f"[System] {report_message}")
            yield sse_event("log", current_agent, {"message": report_message})
            logger.info(f"{current_agent} agent completed. Pipeline finished.")
            yield sse_event("pipeline_done", current_agent, results)

        except Exception as exc:
            logger.error(f"Error in {current_agent} agent: {exc}", exc_info=True)
            report = None
            if results:
                try:
                    report = save_markdown_report(
                        request,
                        results,
                        report_logs,
                        status="failed",
                        error_message=str(exc),
                    )
                    yield sse_event("log", current_agent, {"message": f"Partial markdown report saved to {report['path']}"})
                except Exception as report_exc:
                    logger.error(f"Unable to save partial markdown report: {report_exc}", exc_info=True)
            yield sse_event("agent_error", current_agent, {"message": str(exc), "report": report})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
