from __future__ import annotations

import json
import time
from typing import Any

from app.models.types import AgentName, SSEEventType


def sse_event(event_type: SSEEventType, agent: AgentName, data: Any = None) -> str:
    payload = {
        "type": event_type,
        "agent": agent,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
