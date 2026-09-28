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
LEGACY_MACRO_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand|def|gdef|edef|xdef|"
    r"newenvironment|renewenvironment)\b"
)
SELECTED_MACRO_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|"
    r"newrobustcmd|renewrobustcmd|providerobustcmd|"
    r"NewDocumentCommand|RenewDocumentCommand|ProvideDocumentCommand|DeclareDocumentCommand|"
    r"NewExpandableDocumentCommand|RenewExpandableDocumentCommand|"
    r"ProvideExpandableDocumentCommand|DeclareExpandableDocumentCommand|"
    r"def|gdef|edef|xdef|newenvironment|renewenvironment|"
    r"NewDocumentEnvironment|RenewDocumentEnvironment|ProvideDocumentEnvironment|"
    r"DeclareDocumentEnvironment)\b"
)
LEGACY_COMMAND_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\*?\s*"
    r"(?:\{\s*\\(?P<braced>[A-Za-z@]+)\s*\}|\\(?P<bare>[A-Za-z@]+))"
    r"|\\(?:def|gdef|edef|xdef)\s*\\(?P<direct>[A-Za-z@]+)\b"
)
SELECTED_COMMAND_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|"
    r"newrobustcmd|renewrobustcmd|providerobustcmd|"
    r"NewDocumentCommand|RenewDocumentCommand|ProvideDocumentCommand|DeclareDocumentCommand|"
    r"NewExpandableDocumentCommand|RenewExpandableDocumentCommand|"
    r"ProvideExpandableDocumentCommand|DeclareExpandableDocumentCommand)\*?\s*"
    r"(?:\{\s*\\(?P<braced>[A-Za-z@]+)\s*\}|\\(?P<bare>[A-Za-z@]+))"
    r"|\\(?:def|gdef|edef|xdef)\s*\\(?P<direct>[A-Za-z@]+)\b"
)
LEGACY_ENVIRONMENT_DEFINITION = re.compile(
    r"\\(?:newenvironment|renewenvironment)\*?\s*\{(?P<name>[A-Za-z@]+)\}"
)
SELECTED_ENVIRONMENT_DEFINITION = re.compile(
    r"\\(?:newenvironment|renewenvironment|NewDocumentEnvironment|"
    r"RenewDocumentEnvironment|ProvideDocumentEnvironment|DeclareDocumentEnvironment)"
    r"\*?\s*\{(?P<name>[A-Za-z@]+)\}"
)
COMMAND_USE = re.compile(r"\\(?P<name>[A-Za-z@]+)\b")
SELECTED_COMMAND_USE = re.compile(r"\\(?P<name>[A-Za-z@][A-Za-z0-9@:_]*)")
ENVIRONMENT_USE = re.compile(r"\\begin\s*\{(?P<name>[A-Za-z@]+)\}")
SELECTED_ENVIRONMENT_USE = re.compile(r"\\begin\s*\{(?P<name>[A-Za-z@]+\*?)\}")
SELECTED_ALIAS_DEFINITION = re.compile(
    r"\\(?P<operator>let|futurelet)\b\s*\\(?P<name>[A-Za-z@]+)"
    r"(?:\s*=?\s*\\(?P<target>[A-Za-z@]+))?"
)
SELECTED_EXPL3_DEFINITION = re.compile(
    r"\\cs_(?P<operator>(?:new|set|gset)(?:_protected|_eq)?)\s*:[A-Za-z]+"
    r"\s*\\(?P<name>[A-Za-z@:_]+)"
)
SELECTED_EXPL3_DEFINITION_OPERATOR = re.compile(
    r"\\cs_(?:new|set|gset)(?:_[A-Za-z_]+)?\s*:[A-Za-z]+"
)
SELECTED_EXPL3_MUTATION_OPERATOR = re.compile(
    r"\\cs_(?:set|gset|undefine|gundefine|generate_variant)"
    r"(?:_[A-Za-z_]+)?\s*:[A-Za-z]+"
)
SELECTED_REDEFINITION_OPERATOR = re.compile(
    r"\\(?:renewcommand|DeclareRobustCommand|renewrobustcmd|DeclareDocumentCommand|"
    r"RenewDocumentCommand|DeclareExpandableDocumentCommand|"
    r"RenewExpandableDocumentCommand|def|gdef|edef|xdef|renewenvironment|"
    r"RenewDocumentEnvironment|DeclareDocumentEnvironment|let|futurelet)\b"
)
SELECTED_GLOBAL_RENDERING_ASSIGNMENT = re.compile(
    r"\\(?:everypar|everyhbox|everyvbox|everymath|everydisplay|output)\b|"
    r"\\(?:hoffset|voffset|hsize|vsize|textwidth|textheight|paperwidth|paperheight|"
    r"oddsidemargin|evensidemargin|topmargin|headheight|headsep|footskip|columnwidth|"
    r"linewidth)\b\s*(?:=\s*)?(?=[-+]?(?:\d|\.)|\\)"
)
SELECTED_ENDINPUT = re.compile(r"\\endinput\b")
SELECTED_CARET_NOTATION = re.compile(r"\^\^(?:[0-9A-Fa-f]{2}|[^\r\n])")
DYNAMIC_LET_INCLUDE = re.compile(r"\\let\s*\\[A-Za-z@]+\s*=?\s*\\(?:input|include)\b")
LITERAL_TARGET = re.compile(r"[A-Za-z0-9_./-]+\Z")
LOCAL_SUPPORT_DECLARATION = re.compile(
    r"\\(?P<command>usepackage|RequirePackage|documentclass|LoadClass)\*?"
    r"\s*(?:\[[^\]\r\n]*\]\s*)?\{(?P<targets>[^{}]+)\}"
)
LOCAL_SUPPORT_INPUT = re.compile(r"\\(?:input|include)\s*\{(?P<target>[^{}]+)\}")
SELECTED_RENDERING_MACRO = re.compile(
    r"\\(?P<name>phantom|hphantom|vphantom|texorpdfstring|invisible|visible|"
    r"uncover|only|alt|onslide|color|textcolor)\b", re.I,
)
SELECTED_DYNAMIC_MUTATION = re.compile(
    r"\\(?:csdef|csgdef|csedef|csxdef|cslet|csletcs|@namedef|@nameuse|"
    r"patchcmd|pretocmd|apptocmd|"
    r"robustify|g@addto@macro|AddToHook|AddToHookNext|RemoveFromHook|"
    r"ClearHookRule|DeclareHookRule|(?:AtBegin|AtEnd|BeforeBegin|AfterEnd)[A-Za-z@]*|"
    r"afterassignment|aftergroup)\b"
)
SELECTED_LITERAL_BODY_COMMANDS = {
    "begin", "end", "input", "include",
    "includegraphics", "caption", "label", "ref", "pageref", "autoref", "eqref",
    "cite", "citep", "citet", "nocite",
    "textbf", "textit", "texttt", "textsf", "textrm", "textsl", "textsc",
    "emph", "underline", "mbox",
    "section", "section*", "subsection", "subsection*", "subsubsection",
    "subsubsection*", "paragraph", "paragraph*", "subparagraph", "subparagraph*",
    "item", "centering", "raggedright", "raggedleft",
    "newline", "linebreak", "pagebreak", "newpage", "clearpage", "cleardoublepage",
    "par", "smallskip", "medskip", "bigskip",
    "frac", "dfrac", "tfrac", "sqrt", "mathrm", "mathbf", "mathit", "mathsf",
    "mathtt", "mathcal", "mathbb", "mathfrak", "operatorname", "text",
    "times", "cdot", "pm", "mp", "leq", "geq", "neq", "approx", "sim",
}
SELECTED_LITERAL_ENVIRONMENTS = {
    "document", "abstract", "figure", "figure*", "table", "table*", "center",
    "flushleft", "flushright", "itemize", "enumerate", "description", "quote",
    "quotation", "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "cases", "tabular", "tabular*", "tabularx", "longtable",
    "minipage", "theorem", "lemma", "proposition", "corollary", "proof",
}
SELECTED_LITERAL_PREAMBLE_COMMANDS = {
    "documentclass", "usepackage", "RequirePackage", "LoadClass",
    "ProvidesPackage", "ProvidesClass", "NeedsTeXFormat",
    "input", "include", "graphicspath", "DeclareGraphicsExtensions",
    "title", "author", "date", "thanks",
    "bibliography", "bibliographystyle", "addbibresource",
    "makeatletter", "makeatother", "ExplSyntaxOn", "ExplSyntaxOff",
    "newcommand", "providecommand", "newenvironment",
    "NewDocumentCommand", "ProvideDocumentCommand",
    "NewExpandableDocumentCommand", "ProvideExpandableDocumentCommand",
    "NewDocumentEnvironment", "ProvideDocumentEnvironment",
}
SELECTED_NONPROSE_ARGUMENT = re.compile(
    r"\\(?P<name>label|ref|pageref|autoref|eqref|cite|citep|citet|nocite|"
    r"includegraphics)\*?(?![A-Za-z@])"
)


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


def _balanced_group(text: str, start: int, opener: str, closer: str) -> tuple[int, int] | None:
    """Return the content bounds of one literal balanced group."""
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != opener:
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char not in {opener, closer}:
            continue
        previous = index - 1
        backslashes = 0
        while previous >= 0 and text[previous] == "\\":
            previous -= 1
            backslashes += 1
        if backslashes % 2:
            continue
        if char == opener:
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start + 1, index
            if depth < 0:
                return None
    return None


def _definition_body(text: str, match: re.Match[str], *, environment: bool = False) -> str:
    """Recover literal custom-definition bodies without evaluating TeX."""
    cursor = match.end()
    if "DocumentCommand" in match.group(0) or "DocumentEnvironment" in match.group(0):
        specification = _balanced_group(text, cursor, "{", "}")
        if specification is None:
            return ""
        cursor = specification[1] + 1
    # newcommand/newenvironment may declare argument count and a default value.
    for _ in range(2):
        optional = _balanced_group(text, cursor, "[", "]")
        if optional is None:
            break
        cursor = optional[1] + 1
    body = _balanced_group(text, cursor, "{", "}")
    if body is None:
        # Primitive \def syntax may put #1... between the name and body.
        brace = text.find("{", cursor, min(len(text), cursor + 4096))
        body = _balanced_group(text, brace, "{", "}") if brace >= 0 else None
    if body is None:
        return ""
    pieces = [text[body[0]:body[1]]]
    if environment:
        ending = _balanced_group(text, body[1] + 1, "{", "}")
        if ending is not None:
            pieces.append(text[ending[0]:ending[1]])
    return "\n".join(pieces)


def _rendering_macro_end(text: str, match: re.Match[str], segment_end: int) -> int:
    """Bound a known rendering macro's literal argument/effect interval."""
    name = match.group("name").lower()
    if name == "color":
        return segment_end  # Declaration form affects the remaining local source span.
    cursor = match.end()
    for _ in range(2):
        optional = _balanced_group(text, cursor, "[", "]")
        if optional is None:
            break
        cursor = optional[1] + 1
    required = 2 if name in {"texorpdfstring", "alt", "textcolor"} else 1
    found = False
    for _ in range(required):
        argument = _balanced_group(text, cursor, "{", "}")
        if argument is None:
            return segment_end
        found = True
        cursor = argument[1] + 1
    return cursor if found else segment_end


def _opaque_macro_end(text: str, match: re.Match[str], segment_end: int) -> int:
    """Bound literal arguments of an unknown body command without evaluating it."""
    cursor = match.end()
    if cursor < segment_end and text[cursor] == "*":
        cursor += 1
    for _ in range(2):
        optional = _balanced_group(text, cursor, "[", "]")
        if optional is None or optional[1] >= segment_end:
            break
        cursor = optional[1] + 1
    found = False
    for _ in range(4):
        argument = _balanced_group(text, cursor, "{", "}")
        if argument is None or argument[1] >= segment_end:
            break
        found = True
        cursor = argument[1] + 1
    if found:
        return cursor
    # An unknown unbraced macro can consume any arity or act as a declaration.
    # Its effect therefore remains uncertain through the active source segment.
    return segment_end


def _mask_nonrendered_arguments(text: str) -> str:
    """Blank source-only command arguments while preserving offsets and lines."""
    chars = list(text)
    for match in SELECTED_NONPROSE_ARGUMENT.finditer(text):
        if not _active_command(text, match.start()):
            continue
        cursor = match.end()
        option_ranges: list[tuple[int, int]] = []
        for _ in range(2):
            optional = _balanced_group(text, cursor, "[", "]")
            if optional is None:
                break
            option_ranges.append((optional[0] - 1, optional[1] + 1))
            cursor = optional[1] + 1
        required = _balanced_group(text, cursor, "{", "}")
        if required is None:
            continue
        # Citation prenotes/postnotes can render; only their database key is
        # source-only.  Graphics options and paths never form visible prose.
        if match.group("name").lower() == "includegraphics":
            for start, end in option_ranges:
                _blank(chars, start, end)
        _blank(chars, required[0] - 1, required[1] + 1)
    return "".join(chars)


def scan_static_latex(project_root: Path, main_tex: Path, *,
                      selected_carrier: bool = False) -> dict[str, Any]:
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
        "status": "scanned", "active_files": [], "files": {}, "segments": [],
        "custom_definitions": [], "issues": [],
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

    def issue(code: str, path: Path | None = None, offset: int = 0, *,
              blocked: bool = False, advisory: bool = False, **details: Any) -> None:
        relative = path.relative_to(root).as_posix() if path is not None and path.is_relative_to(root) else str(path or main)
        entry = report["files"].get(relative)
        line = source_location(report["files"], relative, offset)["line"] if entry else 1
        report["issues"].append({"code": code, "path": relative, "line": line,
                                 "char_offset": offset, **details})
        if blocked:
            report["status"] = "blocked"
        elif not advisory and report["status"] == "scanned":
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
        graph_patterns = [(UNSUPPORTED, "unsupported_active_graph"),
                          (DYNAMIC_LET_INCLUDE, "dynamic_include_macro")]
        if selected_carrier:
            graph_patterns.extend((
                (SELECTED_DYNAMIC_MUTATION, "unsupported_local_support_mutation"),
                (SELECTED_ENDINPUT, "unsupported_endinput"),
                (SELECTED_CARET_NOTATION, "unsupported_tex_character_notation"),
            ))
        for pattern, code in graph_patterns:
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
    if selected_carrier and report["status"] == "scanned":
        # Literal local packages/classes are part of the selected carrier's
        # macro source closure, but they are never paper-text segments. System
        # packages remain outside this bounded scanner.
        paper_graph_paths = {segment["path"] for segment in report["segments"]}
        paper_graph_paths.add(main.relative_to(root).as_posix())
        support_queue = list(report["files"])
        scanned_supports: set[str] = set()
        while support_queue and report["status"] == "scanned":
            relative = support_queue.pop(0)
            if relative in scanned_supports:
                continue
            scanned_supports.add(relative)
            code = report["files"][relative]["masked"]
            parent = root / relative
            if relative not in paper_graph_paths:
                depths, unmatched = _group_depths(code)
                if unmatched:
                    issue("unbalanced_group", parent)
                for pattern, code_name in (
                    (UNSUPPORTED, "unsupported_local_support_graph"),
                    (DYNAMIC_LET_INCLUDE, "dynamic_include_macro"),
                    (SELECTED_DYNAMIC_MUTATION, "unsupported_local_support_mutation"),
                    (SELECTED_ENDINPUT, "unsupported_endinput"),
                    (SELECTED_CARET_NOTATION, "unsupported_tex_character_notation"),
                ):
                    match = next((found for found in pattern.finditer(code)
                                  if _active_command(code, found.start())), None)
                    if match:
                        issue(code_name, parent, match.start())
                for command in CONTROL.finditer(code):
                    if (not _active_command(code, command.start())
                            or command.group(1) not in {"input", "include"}):
                        continue
                    tail = code[command.end():]
                    argument = re.match(r"\s*\{([^{}]*)\}", tail)
                    if argument is None or depths[command.start()] > 0:
                        issue("dynamic_local_support", parent, command.start())
                        break
                if report["status"] != "scanned":
                    break
            discoveries: list[tuple[re.Match[str], str, str]] = []
            for declaration in LOCAL_SUPPORT_DECLARATION.finditer(code):
                if not _active_command(code, declaration.start()):
                    continue
                suffix = (".sty" if declaration.group("command") in
                          {"usepackage", "RequirePackage"} else ".cls")
                for raw_target in declaration.group("targets").split(","):
                    discoveries.append((declaration, raw_target.strip(), suffix))
            for declaration in LOCAL_SUPPORT_INPUT.finditer(code):
                if _active_command(code, declaration.start()):
                    discoveries.append((declaration, declaration.group("target").strip(), ".tex"))
            for declaration, token, suffix in discoveries:
                if not LITERAL_TARGET.fullmatch(token) or token in {".", ".."}:
                    issue("dynamic_local_support", parent, declaration.start())
                    break
                target = Path(token)
                if not target.suffix:
                    target = target.with_suffix(suffix)
                candidate = latex_root / target
                if _has_link_component(candidate, latex_root):
                    issue("local_support_symlink_unsupported", parent,
                          declaration.start(), blocked=True)
                    break
                resolved = candidate.resolve()
                if not resolved.is_relative_to(latex_root) or not resolved.is_relative_to(root):
                    issue("local_support_outside_project", parent,
                          declaration.start(), blocked=True)
                    break
                if not resolved.is_file() or resolved in seen:
                    continue
                if len(seen) >= MAX_FILES:
                    issue("include_budget_exceeded", parent, declaration.start())
                    break
                try:
                    raw = resolved.read_bytes()
                except OSError:
                    issue("source_unreadable", resolved, blocked=True)
                    break
                if len(raw) > MAX_FILE_BYTES or total_bytes + len(raw) > MAX_TOTAL_BYTES:
                    issue("source_budget_exceeded", resolved)
                    break
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeError:
                    issue("source_invalid_utf8", resolved, blocked=True)
                    break
                masked, masking_issues = _mask_nonprose(text)
                support_relative = resolved.relative_to(root).as_posix()
                report["files"][support_relative] = {
                    "text": text, "masked": masked,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bom_bytes": 3 if raw.startswith(b"\xef\xbb\xbf") else 0,
                }
                raw_by_path[resolved] = raw
                seen.add(resolved)
                total_bytes += len(raw)
                support_queue.append(support_relative)
                for code_name, issue_offset in masking_issues:
                    issue(code_name, resolved, issue_offset)
                if report["status"] != "scanned":
                    break
    macro_definition_pattern = (SELECTED_MACRO_DEFINITION if selected_carrier
                                else LEGACY_MACRO_DEFINITION)
    command_definition_pattern = (SELECTED_COMMAND_DEFINITION if selected_carrier
                                  else LEGACY_COMMAND_DEFINITION)
    environment_definition_pattern = (SELECTED_ENVIRONMENT_DEFINITION if selected_carrier
                                      else LEGACY_ENVIRONMENT_DEFINITION)
    defined_commands: set[str] = set()
    defined_environments: set[str] = set()
    for relative, entry in report["files"].items():
        code = entry["masked"]
        command_matches = [match for match in command_definition_pattern.finditer(code)
                           if _active_command(code, match.start())]
        environment_matches = [match for match in environment_definition_pattern.finditer(code)
                               if _active_command(code, match.start())]
        for match in command_matches:
            if _active_command(code, match.start()):
                name = next(name for name in match.groups() if name is not None)
                defined_commands.add(name)
                report["custom_definitions"].append({
                    "kind": "command", "name": name, "path": relative,
                    "char_offset": match.start(), "body": _definition_body(code, match),
                })
        for match in environment_matches:
            name = match.group("name")
            defined_environments.add(name)
            report["custom_definitions"].append({
                "kind": "environment", "name": name, "path": relative,
                "char_offset": match.start(),
                "body": _definition_body(code, match, environment=True),
            })
        if selected_carrier:
            recognized_definition_starts = {
                match.start() for match in command_matches + environment_matches
            }
            for match in SELECTED_MACRO_DEFINITION.finditer(code):
                if (_active_command(code, match.start())
                        and match.start() not in recognized_definition_starts):
                    issue("unsupported_definition_form", root / relative, match.start(),
                          advisory=True, end_offset=match.end())
            for match in SELECTED_REDEFINITION_OPERATOR.finditer(code):
                if _active_command(code, match.start()):
                    issue("unbounded_redefinition", root / relative, match.start(),
                          advisory=True, end_offset=match.end())
            exact_expl3_starts = {
                match.start() for match in SELECTED_EXPL3_DEFINITION.finditer(code)
                if _active_command(code, match.start())
            }
            for match in SELECTED_EXPL3_DEFINITION_OPERATOR.finditer(code):
                if (_active_command(code, match.start())
                        and match.start() not in exact_expl3_starts):
                    issue("unsupported_definition_form", root / relative, match.start(),
                          advisory=True, end_offset=match.end())
            for match in SELECTED_EXPL3_MUTATION_OPERATOR.finditer(code):
                if _active_command(code, match.start()):
                    issue("unbounded_redefinition", root / relative, match.start(),
                          advisory=True, end_offset=match.end())
            depths, _ = _group_depths(code)
            for match in SELECTED_GLOBAL_RENDERING_ASSIGNMENT.finditer(code):
                if _active_command(code, match.start()) and depths[match.start()] == 0:
                    issue("global_rendering_assignment", root / relative, match.start(),
                          advisory=True, end_offset=match.end())
            for match in SELECTED_ALIAS_DEFINITION.finditer(code):
                if not _active_command(code, match.start()):
                    continue
                name = match.group("name")
                defined_commands.add(name)
                target = match.group("target")
                report["custom_definitions"].append({
                    "kind": "command", "name": name, "path": relative,
                    "char_offset": match.start(),
                    # A literal \let alias can be followed through by the
                    # consumer.  \futurelet depends on the future input token,
                    # so an empty body intentionally remains fail closed.
                    "body": ("\\" + target
                             if match.group("operator") == "let" and target else ""),
                })
            for match in SELECTED_EXPL3_DEFINITION.finditer(code):
                if not _active_command(code, match.start()):
                    continue
                name = match.group("name")
                defined_commands.add(name)
                report["custom_definitions"].append({
                    "kind": "command", "name": name, "path": relative,
                    "char_offset": match.start(), "body": "",
                })
    if selected_carrier:
        definition_bodies: dict[str, list[str]] = {}
        for definition in report["custom_definitions"]:
            if definition.get("kind") == "command":
                definition_bodies.setdefault(str(definition.get("name")), []).append(
                    str(definition.get("body") or ""))

        rendering_cache: dict[str, bool] = {}

        def rendering_sensitive(name: str, trail: frozenset[str] = frozenset()) -> bool:
            if name in rendering_cache:
                return rendering_cache[name]
            if name in trail:
                return True
            bodies = definition_bodies.get(name, [])
            if not bodies:
                return True
            nested_trail = trail | {name}
            for body in bodies:
                if (not body or SELECTED_RENDERING_MACRO.search(body)
                        or SELECTED_GLOBAL_RENDERING_ASSIGNMENT.search(body)
                        or SELECTED_DYNAMIC_MUTATION.search(body)):
                    rendering_cache[name] = True
                    return True
                references = [match.group("name") for match in SELECTED_COMMAND_USE.finditer(body)]
                if any((reference in definition_bodies
                        and rendering_sensitive(reference, nested_trail))
                       or (reference not in definition_bodies
                           and reference not in SELECTED_LITERAL_BODY_COMMANDS)
                       for reference in references):
                    rendering_cache[name] = True
                    return True
            rendering_cache[name] = False
            return False

        preamble_ranges = [
            (segment["path"], segment["start"], segment["end"])
            for segment in report["segments"] if not segment["in_document"]
        ]
        segmented_paths = {segment["path"] for segment in report["segments"]}
        preamble_ranges.extend(
            (relative, 0, len(entry["masked"]))
            for relative, entry in report["files"].items()
            if relative not in segmented_paths
        )
        for relative, start, end in preamble_ranges:
            code = report["files"][relative]["masked"]
            depths, _ = _group_depths(code)
            rendering_names = {
                match.group("name")
                for match in SELECTED_RENDERING_MACRO.finditer(code, start, end)
                if _active_command(code, match.start()) and depths[match.start()] == 0
            }
            for match in SELECTED_RENDERING_MACRO.finditer(code, start, end):
                if _active_command(code, match.start()) and depths[match.start()] == 0:
                    issue("preamble_rendering_effect", root / relative,
                          match.start(), advisory=True, name=match.group("name"),
                          end_offset=_rendering_macro_end(code, match, end))
            for use in SELECTED_COMMAND_USE.finditer(code, start, end):
                if not _active_command(code, use.start()) or depths[use.start()] != 0:
                    continue
                name = use.group("name")
                if name in definition_bodies:
                    if rendering_sensitive(name):
                        issue("preamble_custom_macro_effect", root / relative,
                              use.start(), advisory=True, name=name,
                              end_offset=_opaque_macro_end(code, use, end))
                    continue
                if (name in SELECTED_LITERAL_PREAMBLE_COMMANDS
                        or name.lower() in {value.lower() for value in rendering_names}
                        or SELECTED_GLOBAL_RENDERING_ASSIGNMENT.match(code, use.start())):
                    continue
                issue("opaque_macro_in_preamble", root / relative, use.start(),
                      advisory=True, name=name,
                      end_offset=_opaque_macro_end(code, use, end))
            for use in SELECTED_ENVIRONMENT_USE.finditer(code, start, end):
                if _active_command(code, use.start()) and depths[use.start()] == 0:
                    issue("preamble_environment_unsupported", root / relative,
                          use.start(), advisory=True, name=use.group("name"),
                          end_offset=end)
    for segment in report["segments"]:
        if segment["in_document"]:
            code = report["files"][segment["path"]]["masked"]
            definition_patterns = [macro_definition_pattern]
            if selected_carrier:
                definition_patterns.extend((SELECTED_ALIAS_DEFINITION,
                                            SELECTED_EXPL3_DEFINITION))
            match = min((found for pattern in definition_patterns
                         for found in pattern.finditer(code, segment["start"], segment["end"])
                         if _active_command(code, found.start())),
                        key=lambda found: found.start(), default=None)
            if match:
                issue("body_macro_definition", root / segment["path"], match.start())
            command_use_pattern = SELECTED_COMMAND_USE if selected_carrier else COMMAND_USE
            for pattern, names, kind in ((command_use_pattern, defined_commands, "command"),
                                         (ENVIRONMENT_USE, defined_environments, "environment")):
                uses = [found for found in pattern.finditer(code, segment["start"], segment["end"])
                        if _active_command(code, found.start()) and found.group("name") in names]
                if not selected_carrier:
                    uses = uses[:1]
                if len(uses) > 512:
                    issue("custom_macro_use_budget_exceeded", root / segment["path"],
                          uses[512].start())
                    uses = uses[:512]
                for use in uses:
                    issue("custom_macro_in_body", root / segment["path"], use.start(),
                          advisory=selected_carrier, name=use.group("name"),
                          custom_kind=kind,
                          end_offset=(_opaque_macro_end(code, use, segment["end"])
                                      if selected_carrier else use.end()))
            if selected_carrier:
                for use in SELECTED_RENDERING_MACRO.finditer(
                        code, segment["start"], segment["end"]):
                    if _active_command(code, use.start()):
                        issue("rendering_macro_in_body", root / segment["path"],
                              use.start(), advisory=True, name=use.group("name"),
                              end_offset=_rendering_macro_end(code, use, segment["end"]))
                rendering_names = {
                    use.group("name").lower()
                    for use in SELECTED_RENDERING_MACRO.finditer(
                        code, segment["start"], segment["end"])
                    if _active_command(code, use.start())
                }
                for use in SELECTED_COMMAND_USE.finditer(
                        code, segment["start"], segment["end"]):
                    if not _active_command(code, use.start()):
                        continue
                    name = use.group("name")
                    if (name in defined_commands or name.lower() in rendering_names
                            or name in SELECTED_LITERAL_BODY_COMMANDS):
                        continue
                    issue("opaque_macro_in_body", root / segment["path"],
                          use.start(), advisory=True, name=name,
                          end_offset=_opaque_macro_end(code, use, segment["end"]))
                for use in SELECTED_ENVIRONMENT_USE.finditer(
                        code, segment["start"], segment["end"]):
                    if (not _active_command(code, use.start())
                            or use.group("name") in defined_environments
                            or use.group("name") in SELECTED_LITERAL_ENVIRONMENTS):
                        continue
                    issue("opaque_environment_in_body", root / segment["path"],
                          use.start(), advisory=True, name=use.group("name"),
                          end_offset=segment["end"])
    if report["status"] == "scanned" and (begin_count != 1 or end_count != 1):
        issue("missing_document_boundary", main)
    if selected_carrier:
        for entry in report["files"].values():
            entry["prose"] = _mask_nonrendered_arguments(entry["masked"])
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
