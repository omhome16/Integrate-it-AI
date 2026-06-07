from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.types import PipelineRequest, PipelineResults, ReportInfo
from app.services.result_normalizer import to_display_string

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
REPORTS_DIR = PROJECT_DIR / "result"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:48] or "integration"


def _table_cell(value: Any) -> str:
    text = to_display_string(value, "").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("|", "\\|").replace("\n", "<br>")


def _bullet_list(items: list[str], empty: str = "None") -> str:
    clean_items = [item for item in items if item]
    if not clean_items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in clean_items)


def _code_fence(value: str, language: str = "") -> str:
    fence = "````" if "```" in value else "```"
    return f"{fence}{language}\n{value.strip()}\n{fence}"


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_object(object_id: int, value: bytes) -> bytes:
    return f"{object_id} 0 obj\n".encode("ascii") + value + b"\nendobj\n"


def _wrap_pdf_text(value: str, width: int) -> list[str]:
    clean = value.replace("\t", "    ").replace("<br>", " ")
    return textwrap.wrap(clean, width=width, replace_whitespace=True, drop_whitespace=True) or [""]


def _parse_markdown_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[dict[str, Any]] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        if line.startswith("```"):
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            blocks.append({"type": "code", "lines": code})
            index += 1
            continue

        if re.match(r"^#{1,4}\s+", line):
            level = len(line.split(" ", 1)[0])
            blocks.append({"type": "heading", "level": level, "text": re.sub(r"^#{1,4}\s+", "", line).strip()})
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", lines[index + 1]):
            rows: list[list[str]] = []
            rows.append([cell.strip().replace("\\|", "|") for cell in line.strip("|").split("|")])
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([cell.strip().replace("\\|", "|") for cell in lines[index].strip("|").split("|")])
                index += 1
            blocks.append({"type": "table", "rows": rows})
            continue

        if line.startswith("- "):
            items: list[str] = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append(lines[index][2:].strip())
                index += 1
            blocks.append({"type": "list", "items": items})
            continue

        paragraph = [line.strip()]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].startswith("```")
            and not lines[index].startswith("|")
            and not lines[index].startswith("- ")
            and not re.match(r"^#{1,4}\s+", lines[index])
        ):
            paragraph.append(lines[index].strip())
            index += 1
        blocks.append({"type": "paragraph", "text": " ".join(paragraph)})

    return blocks


def _pdf_line(text: str, font: str = "F1", size: int = 10, indent: int = 0) -> dict[str, Any]:
    return {"text": text, "font": font, "size": size, "indent": indent}


def markdown_to_pdf_bytes(markdown: str) -> bytes:
    page_width = 612
    page_height = 792
    margin_x = 46
    top_y = 750
    bottom_y = 46
    lines: list[dict[str, Any]] = []

    for block in _parse_markdown_blocks(markdown):
        block_type = block["type"]
        if block_type == "heading":
            level = int(block["level"])
            size = 18 if level == 1 else 14 if level == 2 else 12
            lines.append(_pdf_line(block["text"], "F2", size))
            lines.append(_pdf_line("", "F1", 5))
        elif block_type == "paragraph":
            for wrapped in _wrap_pdf_text(block["text"], 92):
                lines.append(_pdf_line(wrapped, "F1", 10))
            lines.append(_pdf_line("", "F1", 5))
        elif block_type == "list":
            for item in block["items"]:
                wrapped_items = _wrap_pdf_text(item, 86)
                for wrapped_index, wrapped in enumerate(wrapped_items):
                    prefix = "- " if wrapped_index == 0 else "  "
                    lines.append(_pdf_line(f"{prefix}{wrapped}", "F1", 10, 10))
            lines.append(_pdf_line("", "F1", 5))
        elif block_type == "code":
            for code_line in block["lines"]:
                for wrapped in _wrap_pdf_text(code_line, 84):
                    lines.append(_pdf_line(wrapped, "F3", 8, 10))
            lines.append(_pdf_line("", "F1", 5))
        elif block_type == "table":
            rows = block["rows"]
            if rows:
                header = " | ".join(rows[0])
                for wrapped in _wrap_pdf_text(header, 86):
                    lines.append(_pdf_line(wrapped, "F2", 8))
                for row in rows[1:]:
                    row_text = " | ".join(row)
                    for wrapped in _wrap_pdf_text(row_text, 86):
                        lines.append(_pdf_line(wrapped, "F1", 8, 8))
                lines.append(_pdf_line("", "F1", 5))

    pages: list[list[dict[str, Any]]] = []
    current_page: list[dict[str, Any]] = []
    current_y = top_y
    for line in lines or [_pdf_line("No report content.", "F1", 10)]:
        line_height = max(9, int(line["size"]) + 4)
        if current_page and current_y - line_height < bottom_y:
            pages.append(current_page)
            current_page = []
            current_y = top_y
        current_page.append(line)
        current_y -= line_height
    if current_page:
        pages.append(current_page)

    objects: list[bytes] = []
    objects.append(_pdf_object(1, b"<< /Type /Catalog /Pages 2 0 R >>"))

    page_object_ids = [3 + index * 2 for index in range(len(pages))]
    kids = " ".join(f"{object_id} 0 R" for object_id in page_object_ids)
    objects.append(_pdf_object(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_ids)} >>".encode("ascii")))

    for index, page_lines in enumerate(pages):
        page_object_id = 3 + index * 2
        content_object_id = page_object_id + 1
        text_commands: list[str] = []
        y = top_y
        for line in page_lines:
            line_height = max(9, int(line["size"]) + 4)
            if line["text"]:
                x = margin_x + int(line["indent"])
                text_commands.append(f"BT /{line['font']} {line['size']} Tf {x} {y} Td ({_pdf_escape(line['text'])}) Tj ET")
            y -= line_height
        stream = "\n".join(text_commands).encode("utf-8")

        objects.append(
            _pdf_object(
                page_object_id,
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                    f"/Resources << /Font << /F1 {3 + len(pages) * 2} 0 R "
                    f"/F2 {4 + len(pages) * 2} 0 R /F3 {5 + len(pages) * 2} 0 R >> >> "
                    f"/Contents {content_object_id} 0 R >>"
                ).encode("ascii"),
            )
        )
        objects.append(
            _pdf_object(
                content_object_id,
                f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
            )
        )

    font_object_id = 3 + len(pages) * 2
    objects.append(_pdf_object(font_object_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))
    objects.append(_pdf_object(font_object_id + 1, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"))
    objects.append(_pdf_object(font_object_id + 2, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for item in objects:
        offsets.append(len(pdf))
        pdf.extend(item)

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def _endpoint_table(api: dict[str, Any]) -> str:
    rows = ["| Method | Endpoint | Description |", "| --- | --- | --- |"]
    for endpoint in api.get("endpoints", []):
        rows.append(
            "| "
            f"{_table_cell(endpoint.get('method'))} | "
            f"{_table_cell(endpoint.get('path'))} | "
            f"{_table_cell(endpoint.get('description'))} |"
        )
    if len(rows) == 2:
        rows.append("| Not specified | Not specified | No endpoints were returned. |")
    return "\n".join(rows)


def _mapping_table(results: PipelineResults) -> str:
    mapping = results.get("mapping", {})
    rows = [
        "| Source Field | Target Field | Transformation | Confidence | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in mapping.get("mappings", []):
        confidence = item.get("confidence", 0)
        try:
            confidence_text = f"{round(float(confidence) * 100)}%"
        except (TypeError, ValueError):
            confidence_text = "n/a"
        rows.append(
            "| "
            f"{_table_cell(item.get('sourceField'))} | "
            f"{_table_cell(item.get('targetField'))} | "
            f"{_table_cell(item.get('transformation'))} | "
            f"{confidence_text} | "
            f"{_table_cell(item.get('notes'))} |"
        )
    if len(rows) == 2:
        rows.append("| Not specified | Not specified | Not specified | n/a | No mappings were returned. |")
    return "\n".join(rows)


def _walkthrough_sections(results: PipelineResults) -> str:
    walkthrough = results.get("walkthrough", {})
    prerequisites = walkthrough.get("prerequisites", [])
    steps = walkthrough.get("steps", [])

    lines = [
        "## Walkthrough",
        "",
        to_display_string(walkthrough.get("overview"), "No walkthrough overview was returned."),
        "",
        "### Prerequisites",
        "",
        "| Key | Required | Description |",
        "| --- | --- | --- |",
    ]

    if prerequisites:
        for env in prerequisites:
            lines.append(
                "| "
                f"{_table_cell(env.get('key'))} | "
                f"{'Yes' if env.get('required') else 'No'} | "
                f"{_table_cell(env.get('description'))} |"
            )
    else:
        lines.append("| None | No | No prerequisites were returned. |")

    lines.extend(["", "### Steps", ""])
    if steps:
        for index, step in enumerate(steps, start=1):
            lines.extend(
                [
                    f"#### {index}. {to_display_string(step.get('title'), f'Step {index}')}",
                    "",
                    to_display_string(step.get("description"), ""),
                    "",
                ]
            )
            code = to_display_string(step.get("codeSnippet"), "")
            if code:
                lines.extend([_code_fence(code), ""])
    else:
        lines.extend(["No walkthrough steps were returned.", ""])

    command = to_display_string(walkthrough.get("executionCommand"), "")
    if command:
        lines.extend(["### Execution", "", _code_fence(command, "bash"), ""])
    return "\n".join(lines).strip()


def build_markdown_report(
    request: PipelineRequest,
    results: PipelineResults,
    logs: list[str],
    generated_at: str,
    status: str,
    error_message: str | None = None,
) -> str:
    discovery = results.get("discovery", {})
    source = discovery.get("source", {})
    target = discovery.get("target", {})
    mapping = results.get("mapping", {})
    draft_code = results.get("codegen", "")
    reviewed_code = results.get("review", "")
    code = reviewed_code or draft_code
    raw_snapshot = {key: value for key, value in results.items() if key != "report"}

    source_name = to_display_string(source.get("name"), request.source)
    target_name = to_display_string(target.get("name"), request.target)

    lines = [
        f"# Integration Report: {source_name} to {target_name}",
        "",
        f"- Generated: {generated_at}",
        f"- Status: {status}",
        f"- Source: {request.source}",
        f"- Target: {request.target}",
        f"- Prompt: {request.prompt}",
        "",
    ]

    if error_message:
        lines.extend(["## Run Error", "", error_message, ""])

    lines.extend(
        [
            "## API Discovery",
            "",
            f"### Source API: {source_name}",
            "",
            f"- Base URL: {to_display_string(source.get('baseUrl'), 'Not specified')}",
            f"- Authentication: {to_display_string(source.get('auth'), 'Not specified')}",
            "",
            _endpoint_table(source),
            "",
            f"### Target API: {target_name}",
            "",
            f"- Base URL: {to_display_string(target.get('baseUrl'), 'Not specified')}",
            f"- Authentication: {to_display_string(target.get('auth'), 'Not specified')}",
            "",
            _endpoint_table(target),
            "",
            "## Field Mapping",
            "",
            f"- Mapped fields: {len(mapping.get('mappings', []))}",
            f"- Total fields: {mapping.get('totalFields', 0)}",
            f"- Mapped percent: {mapping.get('mappedPercent', 0)}%",
            "",
            _mapping_table(results),
            "",
            "### Unmapped Source Fields",
            "",
            _bullet_list(mapping.get("unmappedSource", [])),
            "",
            "### Unmapped Target Fields",
            "",
            _bullet_list(mapping.get("unmappedTarget", [])),
            "",
            "## Reviewed Connector Code",
            "",
            _code_fence(to_display_string(code, ""), "python") if code else "No connector code was returned.",
            "",
            _walkthrough_sections(results),
            "",
            "## Run Log",
            "",
            _bullet_list(logs),
            "",
            "## Raw Result Snapshot",
            "",
            _code_fence(json.dumps(raw_snapshot, indent=2, ensure_ascii=False), "json"),
            "",
        ]
    )

    return "\n".join(lines)


def save_markdown_report(
    request: PipelineRequest,
    results: PipelineResults,
    logs: list[str],
    status: str = "complete",
    error_message: str | None = None,
) -> ReportInfo:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    file_name = f"{timestamp}_{_slug(request.source)}_to_{_slug(request.target)}.md"
    report_path = REPORTS_DIR / file_name
    markdown = build_markdown_report(request, results, logs, generated_at, status, error_message)
    report_path.write_text(markdown, encoding="utf-8")

    return {
        "fileName": file_name,
        "path": str(report_path),
        "url": f"/api/pipeline/reports/{file_name}",
        "pdfUrl": f"/api/pipeline/reports/{file_name}/pdf",
        "generatedAt": generated_at,
    }
