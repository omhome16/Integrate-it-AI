from __future__ import annotations

import json
from typing import Any, cast

from app.models.types import DiscoveryResult, MappingResult, WalkthroughResult

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
FIELD_TYPES = {"string", "number", "boolean", "date", "object", "array"}
TRANSFORMATIONS = {"direct", "format", "compute", "skip", "split", "merge"}


def to_display_string(value: Any, fallback: str = "Unknown") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [to_display_string(item, "") for item in value]
        return ", ".join(part for part in parts if part).strip() or fallback
    if isinstance(value, dict):
        for key in ("name", "label", "title", "type", "value", "key", "method", "path", "url", "baseUrl"):
            if key in value:
                return to_display_string(value[key], fallback)
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(value)
    return str(value).strip() or fallback


def _as_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "endpoints", "mappings", "steps", "prerequisites"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _auth(value: Any) -> str:
    text = to_display_string(value, "API Key").lower().replace("_", " ").replace("-", " ")
    if "oauth" in text:
        return "OAuth2"
    if "bearer" in text or "token" in text:
        return "Bearer Token"
    if "basic" in text:
        return "Basic Auth"
    return "API Key"


def _method(value: Any) -> str:
    text = to_display_string(value, "GET").upper()
    for method in HTTP_METHODS:
        if method in text:
            return method
    return "GET"


def _field_type(value: Any) -> str:
    text = to_display_string(value, "string").lower()
    return text if text in FIELD_TYPES else "string"


def _transformation(value: Any) -> str:
    text = to_display_string(value, "direct").lower()
    return text if text in TRANSFORMATIONS else "direct"


def _confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.75
    if confidence > 1:
        confidence = confidence / 100
    return max(0, min(confidence, 1))


def _params(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {to_display_string(key): to_display_string(item, "") for key, item in value.items()}


def normalize_endpoint(value: Any) -> dict[str, Any]:
    endpoint = _as_object(value)
    path = to_display_string(endpoint.get("path") or endpoint.get("url") or endpoint.get("route"), "/")
    if path and not path.startswith("/") and not path.startswith("http"):
        path = f"/{path}"
    return {
        "path": path or "/",
        "method": _method(endpoint.get("method") or endpoint.get("type")),
        "description": to_display_string(endpoint.get("description") or endpoint.get("summary"), "Endpoint"),
        "params": _params(endpoint.get("params") or endpoint.get("parameters")),
    }


def normalize_api_info(value: Any, fallback_name: str) -> dict[str, Any]:
    api = _as_object(value)
    endpoints = [normalize_endpoint(item) for item in _as_list(api.get("endpoints"))]
    return {
        "name": to_display_string(api.get("name") or api.get("service"), fallback_name),
        "baseUrl": to_display_string(api.get("baseUrl") or api.get("base_url") or api.get("url"), "Not specified"),
        "auth": _auth(api.get("auth") or api.get("authentication")),
        "endpoints": endpoints,
    }


def normalize_discovery_result(value: Any) -> DiscoveryResult:
    discovery = _as_object(value)
    return cast(
        DiscoveryResult,
        {
            "source": normalize_api_info(discovery.get("source"), "Source API"),
            "target": normalize_api_info(discovery.get("target"), "Target API"),
        },
    )


def normalize_mapping_result(value: Any) -> MappingResult:
    raw = _as_object(value)
    raw_mappings = _as_list(raw.get("mappings") if raw else value)
    mappings = []
    for item in raw_mappings:
        mapping = _as_object(item)
        mappings.append(
            {
                "sourceField": to_display_string(mapping.get("sourceField") or mapping.get("source_field"), "source.field"),
                "sourceType": _field_type(mapping.get("sourceType") or mapping.get("source_type")),
                "targetField": to_display_string(mapping.get("targetField") or mapping.get("target_field"), "target.field"),
                "targetType": _field_type(mapping.get("targetType") or mapping.get("target_type")),
                "transformation": _transformation(mapping.get("transformation")),
                "confidence": _confidence(mapping.get("confidence")),
                "notes": to_display_string(mapping.get("notes") or mapping.get("description"), ""),
            }
        )

    unmapped_source = [to_display_string(item, "") for item in _as_list(raw.get("unmappedSource") or raw.get("unmapped_source"))]
    unmapped_target = [to_display_string(item, "") for item in _as_list(raw.get("unmappedTarget") or raw.get("unmapped_target"))]
    unmapped_source = [item for item in unmapped_source if item]
    unmapped_target = [item for item in unmapped_target if item]
    total = len(mappings) + len(unmapped_source) + len(unmapped_target)

    return cast(
        MappingResult,
        {
            "mappings": mappings,
            "unmappedSource": unmapped_source,
            "unmappedTarget": unmapped_target,
            "totalFields": total,
            "mappedPercent": round((len(mappings) / total * 100)) if total > 0 else 0,
        },
    )


def normalize_walkthrough_result(value: Any) -> WalkthroughResult:
    raw = _as_object(value)
    prerequisites = []
    for item in _as_list(raw.get("prerequisites")):
        env = _as_object(item)
        prerequisites.append(
            {
                "key": to_display_string(env.get("key") or env.get("name"), "ENV_VAR"),
                "description": to_display_string(env.get("description"), ""),
                "required": bool(env.get("required", True)),
            }
        )

    steps = []
    for index, item in enumerate(_as_list(raw.get("steps")), start=1):
        step = _as_object(item)
        steps.append(
            {
                "title": to_display_string(step.get("title"), f"Step {index}"),
                "description": to_display_string(step.get("description"), ""),
                "codeSnippet": to_display_string(step.get("codeSnippet") or step.get("code_snippet"), ""),
            }
        )

    return cast(
        WalkthroughResult,
        {
            "overview": to_display_string(raw.get("overview"), "Integration walkthrough"),
            "prerequisites": prerequisites,
            "steps": steps,
            "executionCommand": to_display_string(raw.get("executionCommand") or raw.get("execution_command"), "python connector.py"),
        },
    )
