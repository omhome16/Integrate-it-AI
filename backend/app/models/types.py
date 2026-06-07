from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

AgentName = Literal["discovery", "mapping", "codegen", "walkthrough"]
AgentStatus = Literal["idle", "running", "done", "error"]
SSEEventType = Literal[
    "agent_start",
    "agent_token",
    "agent_done",
    "agent_error",
    "pipeline_done",
    "log",
]


class PipelineRequest(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=500)


class ApiEndpoint(TypedDict, total=False):
    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    description: str
    params: dict[str, str]


class ApiInfo(TypedDict):
    name: str
    baseUrl: str
    auth: Literal["OAuth2", "API Key", "Bearer Token", "Basic Auth"]
    endpoints: list[ApiEndpoint]


class DiscoveryResult(TypedDict):
    source: ApiInfo
    target: ApiInfo


class FieldMapping(TypedDict):
    sourceField: str
    sourceType: Literal["string", "number", "boolean", "date", "object", "array"]
    targetField: str
    targetType: Literal["string", "number", "boolean", "date", "object", "array"]
    transformation: Literal["direct", "format", "compute", "skip", "split", "merge"]
    confidence: float
    notes: str


class MappingResult(TypedDict):
    mappings: list[FieldMapping]
    unmappedSource: list[str]
    unmappedTarget: list[str]
    totalFields: int
    mappedPercent: int


class EnvVar(TypedDict):
    key: str
    description: str
    required: bool

class WalkthroughStep(TypedDict):
    title: str
    description: str
    codeSnippet: str

class WalkthroughResult(TypedDict):
    overview: str
    prerequisites: list[EnvVar]
    steps: list[WalkthroughStep]
    executionCommand: str

class PipelineResults(TypedDict, total=False):
    discovery: DiscoveryResult
    mapping: MappingResult
    codegen: str
    walkthrough: WalkthroughResult


SSEPayload = dict[str, Any]
