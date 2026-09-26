"""Locate literal text in a deliberately small, static modular LaTeX graph.

This is source inspection, not TeX execution or proof of rendered PDF content.
Unsupported constructs leave the graph unassessed instead of guessing activity.
``segments`` reference character offsets in each file's original decoded ``text``;
``source_location`` converts those offsets to physical lines and raw byte offsets.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

MAX_FILES = 256
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 64
VERBATIM_START = re.compile(r"\\begin\s*\{(verbatim|Verbatim|lstlisting|minted|comment)\}")
INLINE_VERBATIM = re.compile(r"\\(?:verb|lstinline)\*?(?![A-Za-z@])")
CONTROL = re.compile(r"\\(input|include|begin|end)\b")
UNSUPPORTED = re.compile(
    r"\\(?:includeonly|InputIfFileExists|IfFileExists|csname|endcsname|catcode|newif|"
    r"else|fi|if[A-Za-z@]*|@if[A-Za-z@]*|mintinline|"
    r"import|subimport|subfile|subfileinclude|inputfrom|includefrom|"
    r"subinputfrom|subincludefrom)\b"
)
MACRO_DEFINITION = re.compile(r"\\(?:newcommand|renewcommand|providecommand|def|gdef|edef|xdef|newenvironment|renewenvironment)\b")
COMMAND_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\*?\s*"
    r"(?:\{\s*\\(?P<braced>[A-Za-z@]+)\s*\}|\\(?P<bare>[A-Za-z@]+))"
    r"|\\(?:def|gdef|edef|xdef)\s*\\(?P<direct>[A-Za-z@]+)\b"
)
ENVIRONMENT_DEFINITION = re.compile(
    r"\\(?:newenvironment|renewenvironment)\*?\s*\{(?P<name>[A-Za-z@]+)\}"
)
COMMAND_USE = re.compile(r"\\(?P<name>[A-Za-z@]+)\b")
ENVIRONMENT_USE = re.compile(r"\\begin\s*\{(?P<name>[A-Za-z@]+)\}")
DYNAMIC_LET_INCLUDE = re.compile(r"\\let\s*\\[A-Za-z@]+\s*=?\s*\\(?:input|include)\b")
LITERAL_TARGET = re.compile(r"[A-Za-z0-9_./-]+\Z")


def source_location(files: Mapping[str, Mapping[str, Any]], path: str, offset: int) -> dict[str, int]:
    """Map a decoded character offset back to a physical source line and byte offset."""
    entry = files[path]
    text = entry["text"]
    if not 0 <= offset <= len(text):
        raise ValueError("source offset outside file")
    return {
        "line": len(re.findall(r"\r\n|\r|\n", text[:offset])) + 1,
        "byte_offset": int(entry["bom_bytes"]) + len(text[:offset].encode("utf-8")),
    }


def _active_command(text: str, offset: int) -> bool:
    """A command backslash preceded by another backslash is escaped in pairs."""
    count = 0
    offset -= 1
    while offset >= 0 and text[offset] == "\\":
        count += 1
        offset -= 1
    return count % 2 == 0


def _blank(chars: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if chars[index] not in "\r\n":
            chars[index] = " "


def _mask_nonprose(text: str) -> tuple[str, list[tuple[str, int]]]:
    """Blank comments and known verbatim forms without shifting source offsets."""
    chars = list(text)
    issues: list[tuple[str, int]] = []
    index = 0
    while index < len(text):
        environment = VERBATIM_START.match(text, index)
        if environment and _active_command(text, index):
            name = environment.group(1)
            ending_pattern = re.compile(r"\\end\s*\{" + re.escape(name) + r"\}")
            ending = next((match for match in ending_pattern.finditer(text, environment.end())
                           if _active_command(text, match.start())), None)
            if ending is None:
                _blank(chars, index, len(text))
                issues.append(("unclosed_verbatim", index))
                break
            end = ending.end()
            _blank(chars, index, end)
            index = end
            continue
        inline = INLINE_VERBATIM.match(text, index)
        if inline and _active_command(text, index):
            delimiter_index = inline.end()
            if text.startswith("\\lstinline", index) and delimiter_index < len(text) and text[delimiter_index] == "[":
                issues.append(("unsupported_inline_verbatim", index))
                line_end = next((n for n in range(delimiter_index, len(text)) if text[n] in "\r\n"), len(text))
                _blank(chars, index, line_end)
                index = line_end
                continue
            if delimiter_index >= len(text) or text[delimiter_index] in "\r\n":
                issues.append(("unsupported_inline_verbatim", index))
                _blank(chars, index, len(text))
                break
            delimiter = text[delimiter_index]
            line_end = len(text)
            for newline in ("\r", "\n"):
                found = text.find(newline, delimiter_index + 1)
                if found >= 0:
                    line_end = min(line_end, found)
            end = text.find(delimiter, delimiter_index + 1, line_end)
            if end < 0:
                issues.append(("unclosed_inline_verbatim", index))
                _blank(chars, index, line_end)
                index = line_end
            else:
                _blank(chars, index, end + 1)
                index = end + 1
            continue
        if text[index] == "%":
            backslashes = 0
            previous = index - 1
            while previous >= 0 and text[previous] == "\\":
                backslashes += 1
                previous -= 1
            if backslashes % 2 == 0:
                end = index
                while end < len(text) and text[end] not in "\r\n":
                    end += 1
                _blank(chars, index, end)
                index = end
                continue
        index += 1
    return "".join(chars), issues


def _group_depths(text: str) -> tuple[list[int], bool]:
    depths = [0] * (len(text) + 1)
    depth = 0
    invalid = False
    for index, char in enumerate(text):
        depths[index] = depth
        if char not in "{}":
            continue
        previous = index - 1
        backslashes = 0
        while previous >= 0 and text[previous] == "\\":
            previous -= 1
            backslashes += 1
        if backslashes % 2:
            continue
        depth += 1 if char == "{" else -1
        if depth < 0:
            invalid = True
            depth = 0
    depths[len(text)] = depth
    return depths, invalid or depth != 0


def _has_link_component(path: Path, base: Path) -> bool:
    """Reject aliases whose target could change outside the captured read set."""
    current = path
    while current != base and current.parent != current:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            return True
        current = current.parent
    return False


def scan_static_latex(project_root: Path, main_tex: Path) -> dict[str, Any]:
    """Return a bounded read-only scan of literal, statically included TeX files.

    ``active_files`` lists occurrences in traversal order, so a repeated include is
    observable. ``segments`` omit include and document-boundary commands and retain
    source offsets; ``in_document`` follows the expanded stream across files.
    """
    root = Path(project_root).resolve()
    main = Path(main_tex)
    if not main.is_absolute():
        main = root / main
    raw_main = main
    main = main.resolve()
    report: dict[str, Any] = {
        "status": "scanned", "active_files": [], "files": {}, "segments": [], "issues": [],
    }
    latex_root = main.parent

    if _has_link_component(raw_main, root):
        report["status"] = "blocked"
        report["issues"].append({"code": "main_symlink_unsupported", "path": str(raw_main), "line": 1})
        return report
    if not main.is_relative_to(root) or main.suffix.lower() != ".tex":
        report["status"] = "blocked"
        report["issues"].append({"code": "main_outside_project", "path": str(main), "line": 1})
        return report

    seen: set[Path] = set()
    stack: list[Path] = []
    raw_by_path: dict[Path, bytes] = {}
    total_bytes = 0
    in_document = False
    begin_count = 0
    end_count = 0
    stopped = False

    def issue(code: str, path: Path | None = None, offset: int = 0, *, blocked: bool = False) -> None:
        relative = path.relative_to(root).as_posix() if path is not None and path.is_relative_to(root) else str(path or main)
        entry = report["files"].get(relative)
        line = source_location(report["files"], relative, offset)["line"] if entry else 1
        report["issues"].append({"code": code, "path": relative, "line": line})
        if blocked:
            report["status"] = "blocked"
        elif report["status"] == "scanned":
            report["status"] = "not_assessed"

    def resolve_target(token: str, parent: Path, offset: int) -> Path | None:
        if re.match(r"^(?:[A-Za-z]:[\\/]|/|\\\\)", token):
            issue("include_outside_project", parent, offset, blocked=True)
            return None
        if not LITERAL_TARGET.fullmatch(token) or token in {".", ".."}:
            issue("dynamic_include", parent, offset)
            return None
        raw = Path(token)
        if raw.is_absolute():
            issue("include_outside_project", parent, offset, blocked=True)
            return None
        if not raw.suffix:
            raw = raw.with_suffix(".tex")
        candidate = latex_root / raw
        if _has_link_component(candidate, latex_root):
            issue("include_symlink_unsupported", parent, offset, blocked=True)
            return None
        child = candidate.resolve()
        if not child.is_relative_to(latex_root) or not child.is_relative_to(root):
            issue("include_outside_project", parent, offset, blocked=True)
            return None
        if child.suffix.lower() != ".tex":
            issue("unsupported_include_suffix", parent, offset)
            return None
        if not child.is_file():
            issue("include_missing", parent, offset, blocked=True)
            return None
        return child

    def add_segment(path: Path, start: int, end: int) -> None:
        if start < end:
            report["segments"].append({
                "path": path.relative_to(root).as_posix(), "start": start, "end": end,
                "in_document": in_document,
            })

    def walk(path: Path) -> None:
        nonlocal total_bytes, in_document, begin_count, end_count, stopped
        if report["status"] == "blocked":
            return
        if path in stack:
            issue("include_cycle", path, blocked=True)
            return
        relative = path.relative_to(root).as_posix()
        report["active_files"].append(relative)
        if path in seen:
            issue("repeated_include", path)
            return
        if len(stack) >= MAX_DEPTH or len(seen) >= MAX_FILES:
            issue("include_budget_exceeded", path)
            return
        try:
            raw = path.read_bytes()
        except OSError:
            issue("source_unreadable", path, blocked=True)
            return
        if len(raw) > MAX_FILE_BYTES or total_bytes + len(raw) > MAX_TOTAL_BYTES:
            issue("source_budget_exceeded", path)
            return
        total_bytes += len(raw)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            issue("source_invalid_utf8", path, blocked=True)
            return
        masked, masking_issues = _mask_nonprose(text)
        report["files"][relative] = {
            "text": text, "masked": masked, "sha256": hashlib.sha256(raw).hexdigest(),
            "bom_bytes": 3 if raw.startswith(b"\xef\xbb\xbf") else 0,
        }
        raw_by_path[path] = raw
        seen.add(path)
        stack.append(path)
        for code, offset in masking_issues:
            issue(code, path, offset)
        depths, unmatched = _group_depths(masked)
        if unmatched:
            issue("unbalanced_group", path)
        for pattern, code in ((UNSUPPORTED, "unsupported_active_graph"),
                              (DYNAMIC_LET_INCLUDE, "dynamic_include_macro")):
            match = next((found for found in pattern.finditer(masked)
                          if _active_command(masked, found.start())), None)
            if match:
                issue(code, path, match.start())
        if path != main and re.search(r"\\documentclass\b", masked):
            issue("child_document_declaration", path, blocked=True)
        if report["status"] != "scanned":
            stack.pop()
            return
        cursor = 0
        for command in CONTROL.finditer(masked):
            if not _active_command(masked, command.start()):
                continue
            if report["status"] != "scanned":
                break
            name = command.group(1)
            start = command.start()
            if depths[start] > 0:
                if name in {"input", "include"}:
                    issue("include_inside_group", path, start)
                elif masked[command.end():].lstrip().startswith("{document}"):
                    issue("document_marker_inside_group", path, start)
                continue
            tail = masked[command.end():]
            argument = re.match(r"\s*\{([^{}]*)\}", tail)
            if name in {"input", "include"}:
                if argument is None:
                    issue("dynamic_include", path, start)
                    continue
                end = command.end() + argument.end()
                add_segment(path, cursor, start)
                cursor = end
                child = resolve_target(argument.group(1), path, start)
                if child is not None:
                    walk(child)
                continue
            if argument is None or argument.group(1) != "document":
                continue
            end = command.end() + argument.end()
            add_segment(path, cursor, start)
            cursor = end
            if path != main:
                issue("child_document_marker", path, start, blocked=True)
                break
            if name == "begin":
                begin_count += 1
                if begin_count != 1 or end_count:
                    issue("invalid_document_boundary", path, start, blocked=True)
                in_document = True
            else:
                end_count += 1
                if begin_count != 1 or end_count != 1:
                    issue("invalid_document_boundary", path, start, blocked=True)
                in_document = False
                stopped = True
                break
        if report["status"] == "scanned" and not stopped:
            add_segment(path, cursor, len(masked))
        stack.pop()

    walk(main)
    defined_commands: set[str] = set()
    defined_environments: set[str] = set()
    for relative, entry in report["files"].items():
        code = entry["masked"]
        for match in COMMAND_DEFINITION.finditer(code):
            if _active_command(code, match.start()):
                defined_commands.add(next(name for name in match.groups() if name is not None))
        for match in ENVIRONMENT_DEFINITION.finditer(code):
            if _active_command(code, match.start()):
                defined_environments.add(match.group("name"))
    for segment in report["segments"]:
        if segment["in_document"]:
            code = report["files"][segment["path"]]["masked"]
            match = next((found for found in MACRO_DEFINITION.finditer(code, segment["start"], segment["end"])
                          if _active_command(code, found.start())), None)
            if match:
                issue("body_macro_definition", root / segment["path"], match.start())
            for pattern, names in ((COMMAND_USE, defined_commands),
                                   (ENVIRONMENT_USE, defined_environments)):
                use = next((found for found in pattern.finditer(code, segment["start"], segment["end"])
                            if _active_command(code, found.start()) and found.group("name") in names), None)
                if use:
                    issue("custom_macro_in_body", root / segment["path"], use.start())
    if report["status"] == "scanned" and (begin_count != 1 or end_count != 1):
        issue("missing_document_boundary", main)
    for path, before in raw_by_path.items():
        try:
            after = path.read_bytes()
        except OSError:
            issue("source_changed_during_scan", path, blocked=True)
            break
        if hashlib.sha256(after).digest() != hashlib.sha256(before).digest():
            issue("source_changed_during_scan", path, blocked=True)
            break
    return report
