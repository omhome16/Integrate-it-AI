from __future__ import annotations

import json
import re
from typing import Any


def extract_json(raw: str) -> Any:
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    cleaned = fence_match.group(1).strip() if fence_match else raw.strip()

    first_positions = [pos for pos in (cleaned.find("{"), cleaned.find("[")) if pos >= 0]
    if not first_positions:
        raise ValueError(f"No JSON object found in LLM output: {raw[:200]}")

    first = min(first_positions)
    last = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if last < first:
        raise ValueError(f"No JSON object found in LLM output: {raw[:200]}")

    return json.loads(cleaned[first : last + 1])
