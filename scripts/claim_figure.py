"""Bounded, read-only Figure registry and static LaTeX source inspection.

These helpers establish only literal source structure. They do not open an image,
execute a plotting script, qualify a workbook, render a PDF, or decide whether a
caption or nearby prose supports a scientific claim. Unsupported TeX structure
stays ``not_assessed``. Callers must supply the current Framework text and a
fresh, successful ``claim_tex.scan_static_latex`` result; no files are read here.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from claim_tex import source_location

MAX_FRAMEWORK_CHARS = 2 * 1024 * 1024
MAX_TABLE_ROWS = 512
MAX_TABLE_LINE = 16 * 1024
MAX_FILES = 256
MAX_SEGMENTS = 4096
MAX_SOURCE_CHARS = 8 * 1024 * 1024
MAX_FIGURES = 512
MAX_FIGURE_CHARS = 256 * 1024
MAX_FIGURE_COMMANDS = 128
MAX_LABEL_REF_COMMANDS = 8192

HEADERS = (
    "图号", "DOCX/LaTeX 图注", "图型/作用", "源工作簿", "工作表/精确唯一表头",
    "绘图程序", "导出文件", "正文支撑判断", "正文引用位置",
)
FIELDS = (
    "figure_id", "paper_caption", "figure_role", "workbook", "worksheet_headers",
    "plotting_program", "export_file", "body_support", "body_reference",
)
SECTION = re.compile(r"(?m)^## 图表证据链[ \t]*\r?$")
NEXT_SECTION = re.compile(r"(?m)^#{1,2} [^\r\n]+\r?$")
SEPARATOR = re.compile(r":?-{3,}:?")
ENV = re.compile(r"\\(?P<kind>begin|end)\s*\{(?P<name>[A-Za-z]+\*?)\}")
COMMAND = re.compile(r"\\(?P<name>label|caption|includegraphics|ref)\b")
ALL_COMMANDS = re.compile(r"\\(?P<name>[A-Za-z@]+)\b")
GRAPHICS_PATH = re.compile(r"\\graphicspath\b")
LITERAL_LABEL = re.compile(r"[A-Za-z0-9:._/-]+\Z")
LITERAL_IMAGE = re.compile(r"[\w./-]+\Z")
SAFE_FIGURE_COMMANDS = {"begin", "end", "centering", "label", "caption", "includegraphics"}


def _cells(line: str) -> list[str]:
    """Split only literal Markdown pipes; an escaped pipe is part of its cell."""
    line = line.strip()
    if len(line) > MAX_TABLE_LINE or not line.startswith("|") or not line.endswith("|"):
        raise ValueError("Figure registry table line is malformed or oversized")
    cells: list[str] = []
    current: list[str] = []
    for index, char in enumerate(line[1:-1], 1):
        if char == "|" and (index == 0 or line[index - 1] != "\\"):
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return [cell.replace(r"\|", "|") for cell in cells]


def _cell_value(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def parse_framework_figure_rows(framework_text: str) -> dict[str, dict[str, str]]:
    """Return the one canonical nine-column Figure registry keyed by Figure ID.

    An all-empty template row is ignored. Other incomplete rows are returned for
    the caller's binding policy to reject; malformed tables and duplicate IDs
    raise ``ValueError`` rather than selecting a convenient row.
    """
    if not isinstance(framework_text, str) or len(framework_text) > MAX_FRAMEWORK_CHARS:
        raise ValueError("Framework text is missing or oversized")
    matches = list(SECTION.finditer(framework_text))
    if len(matches) != 1:
        raise ValueError("Framework requires exactly one ## 图表证据链 section")
    section = framework_text[matches[0].end():]
    following = NEXT_SECTION.search(section)
    if following:
        section = section[:following.start()]
    groups: list[list[str]] = []
    current: list[str] = []
    for line in section.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    if len(groups) != 1 or len(groups[0]) < 2 or len(groups[0]) > MAX_TABLE_ROWS + 2:
        raise ValueError("Figure registry requires exactly one bounded Markdown table")
    table = [_cells(line) for line in groups[0]]
    if table[0] != list(HEADERS) or len(table[1]) != len(HEADERS) or not all(
        SEPARATOR.fullmatch(cell) for cell in table[1]
    ):
        raise ValueError("Figure registry headers or separator differ from the nine-column contract")
    rows: dict[str, dict[str, str]] = {}
    for cells in table[2:]:
        if len(cells) != len(HEADERS):
            raise ValueError("Figure registry row must have nine columns")
        values = [_cell_value(cell) for cell in cells]
        if not any(values):
            continue
        figure_id = values[0]
        if not figure_id or figure_id in rows:
            raise ValueError("Figure registry row has missing or duplicate Figure ID")
        rows[figure_id] = dict(zip(FIELDS, values))
    return rows


def _active_command(text: str, offset: int) -> bool:
    count = 0
    offset -= 1
    while offset >= 0 and text[offset] == "\\":
        count += 1
        offset -= 1
    return count % 2 == 0


def _location(files: Mapping[str, Mapping[str, Any]], path: str, offset: int) -> dict[str, Any]:
    return {"source_file": path, "char_offset": offset, **source_location(files, path, offset)}


def _braced(text: str, start: int, end: int) -> tuple[str, int] | None:
    """Read one simple literal brace argument; nested groups are unsupported."""
    while start < end and text[start].isspace():
        start += 1
    if start >= end or text[start] != "{":
        return None
    close = text.find("}", start + 1, end)
    if close < 0 or "{" in text[start + 1:close]:
        return None
    return text[start + 1:close], close + 1


def _command_arguments(text: str, match: re.Match[str], end: int) -> tuple[str, int] | None:
    cursor = match.end()
    if cursor < end and text[cursor] == "*":
        return None
    if match.group("name") in {"caption", "includegraphics"}:
        while cursor < end and text[cursor].isspace():
            cursor += 1
        if cursor < end and text[cursor] == "[":
            closing = text.find("]", cursor + 1, end)
            if closing < 0 or "[" in text[cursor + 1:closing]:
                return None
            cursor = closing + 1
    return _braced(text, cursor, end)


def _figure_record(files: Mapping[str, Mapping[str, Any]], path: str, segment: Mapping[str, Any],
                   begin: int, end: int | None, nested: bool, mismatched: bool) -> dict[str, Any]:
    text = files[path]["masked"]
    stop = end if end is not None else segment["end"]
    record: dict[str, Any] = {
        "status": "not_assessed", "source_file": path,
        "begin_offset": begin, "end_offset": stop,
        "begin_location": _location(files, path, begin),
        "end_location": _location(files, path, stop), "label": None, "caption": None,
        "image": None, "label_location": None, "caption_location": None,
        "image_location": None, "body_ref_locations": [], "issues": [],
    }
    if end is None:
        record["issues"].append("figure_not_closed_in_same_segment")
    if nested:
        record["issues"].append("nested_figure_structure")
    if mismatched:
        record["issues"].append("mismatched_figure_environment")
    if stop - begin > MAX_FIGURE_CHARS:
        record["issues"].append("figure_source_budget_exceeded")
        return record
    body_start = ENV.match(text, begin).end() if ENV.match(text, begin) else begin
    ranges: list[tuple[int, int]] = []
    for index, command in enumerate(COMMAND.finditer(text, body_start, stop)):
        if index >= MAX_FIGURE_COMMANDS:
            record["issues"].append("figure_command_budget_exceeded")
            break
        if not _active_command(text, command.start()):
            continue
        name = command.group("name")
        if name == "ref":
            continue
        parsed = _command_arguments(text, command, stop)
        if parsed is None:
            record["issues"].append("dynamic_or_malformed_" + name)
            continue
        value, command_end = parsed
        if any(start <= command.start() < past for start, past in ranges):
            continue
        ranges.append((command.start(), command_end))
        if files[path]["text"][command.start():command_end] != text[command.start():command_end] or (
            not value
        ) or (name == "label" and not LITERAL_LABEL.fullmatch(value)) or (
            name == "includegraphics" and not LITERAL_IMAGE.fullmatch(value)
        ) or (name == "caption" and "\\" in value):
            record["issues"].append("dynamic_or_malformed_" + name)
            continue
        key = "image" if name == "includegraphics" else name
        if record[key] is not None:
            record["issues"].append("multiple_" + key)
            continue
        record[key] = value
        record[key + "_location"] = _location(files, path, command.start())
    for index, command in enumerate(ALL_COMMANDS.finditer(text, body_start, stop)):
        if index >= MAX_FIGURE_COMMANDS:
            record["issues"].append("figure_command_budget_exceeded")
            break
        if not _active_command(text, command.start()):
            continue
        if any(start < command.start() < past for start, past in ranges):
            continue
        if command.group("name") not in SAFE_FIGURE_COMMANDS:
            record["issues"].append("unsupported_figure_command")
            break
    for key in ("label", "caption", "image"):
        if record[key] is None:
            record["issues"].append("missing_literal_" + key)
    record["issues"] = sorted(set(record["issues"]))
    return record


def inspect_static_figures(scan: Mapping[str, Any]) -> dict[str, Any]:
    """Inventory literal figures in a proven active static LaTeX scan.

    A located record has one label, caption, and image in one file and one active
    document segment, a unique label across active body source, and a literal
    ``\\ref`` outside every figure. This says nothing about rendered output.
    """
    result: dict[str, Any] = {"status": "not_assessed", "figures": [], "issues": []}
    if scan.get("status") != "scanned":
        result["issues"].append("latex_graph_not_scanned")
        return result
    files = scan.get("files", {})
    segments = scan.get("segments", [])
    if not isinstance(files, Mapping) or not isinstance(segments, list) or len(files) > MAX_FILES or (
        len(segments) > MAX_SEGMENTS
    ) or sum(len(entry.get("masked", "")) for entry in files.values()) > MAX_SOURCE_CHARS:
        result["issues"].append("figure_scan_budget_exceeded")
        return result
    for segment in segments:
        path = segment["path"]
        if path not in files or not isinstance(files[path].get("masked"), str):
            result["issues"].append("invalid_figure_scan_segment")
            return result
        text = files[path]["masked"]
        start, end = segment["start"], segment["end"]
        if not 0 <= start <= end <= len(text):
            result["issues"].append("invalid_figure_scan_segment")
            return result
        if any(_active_command(text, found.start()) for found in GRAPHICS_PATH.finditer(text, start, end)):
            result["issues"].append("active_graphicspath_unsupported")
    body = [segment for segment in segments if segment.get("in_document")]
    intervals: dict[str, list[tuple[int, int]]] = {}
    label_ref_count = 0
    for segment in body:
        path = segment["path"]
        text = files[path]["masked"]
        start, end = segment["start"], segment["end"]
        figure_begin: int | None = None
        figure_names: list[str] = []
        nested = False
        mismatched = False
        for environment in ENV.finditer(text, start, end):
            if not _active_command(text, environment.start()):
                continue
            kind, name = environment.group("kind", "name")
            if name not in {"figure", "figure*"}:
                if figure_begin is not None:
                    nested = True
                continue
            if kind == "begin":
                if figure_begin is None:
                    figure_begin = environment.start()
                else:
                    nested = True
                figure_names.append(name)
            elif figure_begin is None:
                result["issues"].append("figure_end_without_begin_in_segment")
            else:
                mismatched |= figure_names.pop() != name
                if not figure_names:
                    result["figures"].append(_figure_record(files, path, segment, figure_begin,
                                                              environment.start(), nested, mismatched))
                    intervals.setdefault(path, []).append((figure_begin, environment.end()))
                    figure_begin = None
                    nested = False
                    mismatched = False
                    if len(result["figures"]) > MAX_FIGURES:
                        result["issues"].append("figure_scan_budget_exceeded")
                        return result
        if figure_begin is not None:
            result["figures"].append(_figure_record(files, path, segment, figure_begin,
                                                     None, nested, mismatched))
            intervals.setdefault(path, []).append((figure_begin, end))
    labels: dict[str, list[tuple[str, int]]] = {}
    refs: dict[str, list[dict[str, Any]]] = {}
    for segment in body:
        path = segment["path"]
        text = files[path]["masked"]
        for match in COMMAND.finditer(text, segment["start"], segment["end"]):
            if match.group("name") not in {"label", "ref"} or not _active_command(text, match.start()):
                continue
            label_ref_count += 1
            if label_ref_count > MAX_LABEL_REF_COMMANDS:
                result["issues"].append("figure_reference_budget_exceeded")
                return result
            parsed = _command_arguments(text, match, segment["end"])
            if parsed is None or not LITERAL_LABEL.fullmatch(parsed[0]):
                continue
            if match.group("name") == "label":
                labels.setdefault(parsed[0], []).append((path, match.start()))
            elif not any(start <= match.start() < end for start, end in intervals.get(path, [])):
                refs.setdefault(parsed[0], []).append(_location(files, path, match.start()))
    for record in result["figures"]:
        label = record["label"]
        if label is not None:
            if len(labels.get(label, [])) != 1:
                record["issues"].append("figure_label_not_unique_in_active_body")
            record["body_ref_locations"] = refs.get(label, [])
            if not record["body_ref_locations"]:
                record["issues"].append("missing_literal_body_ref")
        record["issues"] = sorted(set(record["issues"]))
        if not record["issues"]:
            record["status"] = "located"
    result["issues"] = sorted(set(result["issues"]))
    result["status"] = "scanned" if not result["issues"] and all(
        row["status"] == "located" for row in result["figures"]
    ) else "not_assessed"
    return result
