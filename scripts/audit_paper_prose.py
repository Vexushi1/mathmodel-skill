#!/usr/bin/env python3
"""Conservative prose/structure/BibTeX/framework audit for HSK LaTeX papers.

Severity follows writing governance:
- blocking: deterministic Hard failure;
- review_required: Default deviation requiring a reason;
- warning: Recommendation/style risk.

The audit never rewrites paper text and never infers mathematical correctness, formula
source validity, parameter optimality, theorem applicability, terminology equivalence,
physical/statistical accuracy from decimal places, or citation semantics.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SEVERITY_ORDER = {"pass": 0, "warning": 1, "review_required": 2, "blocking": 3}
CONTRAST_RE = re.compile(r"但(?:是)?|然而|不过|并非|不是|不能|只能|而不是|却")
PARAGRAPH_START_RE = re.compile(r"^(?:本文|本问|该模型)(?:认为|采用|建立|使用|通过|将|对|在|根据|从|以|中|所)?")
QUESTION_SECTION_RE = re.compile(r"\\section\{问题[一二三四五六七八九十百0-9]+模型建立及求解\}")
SECTION_RE = re.compile(r"\\section\{([^{}]+)\}")
LABEL_ANY_RE = re.compile(r"\\label\{([^{}]+)\}")
FIGTAB_LABEL_RE = re.compile(r"\\label\{((?:fig|tab):[^{}]+)\}")
REF_RE = re.compile(r"\\(?:ref|autoref|cref|Cref|eqref)\{([^{}]+)\}")
CITE_RE = re.compile(r"\\(?:cite|citep|citet|parencite|textcite)\*?(?:\[[^\]]*\])?\{([^{}]+)\}")
NOCITE_ALL_RE = re.compile(r"\\nocite\{\*\}")
REF_TEMPLATE = r"\\(?:ref|autoref|cref|Cref|eqref)\{{{label}\}}"
DERIVATION_STOCK_PATTERNS = ("进一步可得", "同理可得", "容易得到", "不难得到")
META_NAV_PATTERNS = ("本节主要", "下面将", "下文将", "为了便于", "为了更好地")
PARAM_ASSIGN_RE = re.compile(
    r"(?:取|设置|设定|令)\s*(?:\\\([^\n]{0,60}?\\\)|[A-Za-z][A-Za-z0-9_{}^\\-]{0,30})\s*(?:=|为)\s*[-+]?\d+(?:\.\d+)?"
)
PARAM_EVIDENCE_HINT_RE = re.compile(r"题目|给定|规定|收敛|误差|稳定|验证|交叉验证|试验|敏感|置信|AIC|BIC|网格|步长|标准误|残差|依据|范围")
FORMULA_BLOCK_RE = re.compile(
    r"\\begin\{(?:equation|align|gather)\*?\}.*?\\end\{(?:equation|align|gather)\*?\}|\\\[.*?\\\]|\$\$.*?\$\$",
    flags=re.S,
)
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?")
BIB_ENTRY_RE = re.compile(r"(?ms)^\s*@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,")
ABSTRACT_ENV_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", flags=re.S)
FIGURE_ENV_RE = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", flags=re.S)
TABLE_ENV_RE = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", flags=re.S)
KEYWORD_COMMAND_RE = re.compile(r"\\keywords?\{([^{}]+)\}", flags=re.I)
KEYWORD_ENV_RE = re.compile(r"\\begin\{keywords?\}(.*?)\\end\{keywords?\}", flags=re.I | re.S)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""


def _strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        out: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            out.append(char)
            if char == "\\":
                escaped = not escaped
            else:
                escaped = False
        lines.append("".join(out))
    return "\n".join(lines)


def _document_body(text: str) -> str:
    text = _strip_comments(text)
    match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", text, flags=re.S)
    return match.group(1) if match else text


def _remove_non_prose_blocks(text: str) -> str:
    result = text
    for env in (
        "verbatim", "lstlisting", "minted", "equation", "equation*", "align", "align*",
        "gather", "gather*", "table", "table*", "figure", "figure*",
    ):
        result = re.sub(
            rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
            "\n",
            result,
            flags=re.S,
        )
    result = re.sub(r"\\\[.*?\\\]", " ", result, flags=re.S)
    result = re.sub(r"\$\$.*?\$\$", " ", result, flags=re.S)
    result = re.sub(r"\$[^$]*\$", " ", result)
    return result


def _plain_paragraphs(body: str) -> list[str]:
    text = _remove_non_prose_blocks(body)
    text = re.sub(r"\\(?:section|subsection|subsubsection|paragraph)\*?\{[^{}]*\}", "\n\n", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", "\n", text)
    text = re.sub(r"\\(?:label|ref|autoref|cref|Cref|eqref|cite|citep|citet|parencite|textcite)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in paragraphs if len(p) >= 20]


def _main_text_before_appendix(body: str) -> str:
    return body.split("\\appendix", 1)[0]


def _section_content(body: str, title: str) -> str | None:
    marker = re.search(rf"\\section\{{{re.escape(title)}\}}", body)
    if not marker:
        return None
    tail = body[marker.end():]
    next_section = SECTION_RE.search(tail)
    return tail[: next_section.start()] if next_section else tail


def _subsection_content(text: str, title: str) -> str | None:
    marker = re.search(rf"\\subsection\{{{re.escape(title)}\}}", text)
    if not marker:
        return None
    tail = text[marker.end():]
    next_sub = re.search(r"\\subsection\{", tail)
    return tail[: next_sub.start()] if next_sub else tail


def _question_sections(body: str) -> Iterable[tuple[str, str]]:
    matches = list(QUESTION_SECTION_RE.finditer(body))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        next_generic = SECTION_RE.search(body, match.end(), end)
        if next_generic:
            end = next_generic.start()
        yield match.group(0), body[match.end():end]


def _formula_run_warning(main: str) -> Finding | None:
    matches = list(FORMULA_BLOCK_RE.finditer(main))
    if len(matches) < 3:
        return None
    run_start = 0
    for i in range(1, len(matches)):
        gap = main[matches[i - 1].end():matches[i].start()]
        gap_plain = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", gap)
        gap_plain = re.sub(r"\s+", "", gap_plain)
        if len(gap_plain) > 45:
            run_start = i
        if i - run_start + 1 >= 3:
            excerpt = re.sub(r"\s+", " ", main[matches[run_start].start():matches[i].end()])[:180]
            return Finding(
                "warning",
                "dense_formula_run",
                "连续多个展示公式之间解释文字很少；请人工确认核心关系的来源、关键推理和后续用途。",
                excerpt,
            )
    return None


def _citation_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for group in CITE_RE.findall(tex):
        keys.update(item.strip() for item in group.split(",") if item.strip())
    return keys


def _ref_keys(tex: str) -> list[str]:
    keys: list[str] = []
    for group in REF_RE.findall(tex):
        keys.extend(item.strip() for item in group.split(",") if item.strip())
    return keys


def _find_reference_position(text: str, label: str) -> list[int]:
    pattern = re.compile(REF_TEMPLATE.format(label=re.escape(label)))
    return [match.start() for match in pattern.finditer(text)]


def _audit_cross_references(main: str) -> list[Finding]:
    findings: list[Finding] = []
    labels = LABEL_ANY_RE.findall(main)
    label_set = set(labels)
    for ref in sorted(set(_ref_keys(main)) - label_set):
        findings.append(Finding("blocking", "missing_ref_label", f"正文交叉引用指向不存在的 label：{ref}", ref))

    for label in sorted(label_set):
        refs = _find_reference_position(main, label)
        if not refs and (label.startswith(("fig:", "tab:", "eq:", "prop:", "thm:"))):
            findings.append(Finding("warning", "unreferenced_label", f"编号对象 {label} 未在正文显式引用；请确认该编号是否必要。", label))

    for label in FIGTAB_LABEL_RE.findall(main):
        label_match = re.search(rf"\\label\{{{re.escape(label)}\}}", main)
        ref_positions = _find_reference_position(main, label)
        if not label_match or not ref_positions:
            continue
        first_ref = min(ref_positions)
        if first_ref > label_match.start() + 800:
            findings.append(Finding("warning", "figure_table_first_reference_after_object", f"{label} 首次正文引用明显晚于图表出现位置；请确认图表是否先被说明再出现。", label))
        distance = min(abs(position - label_match.start()) for position in ref_positions)
        if distance > 3000:
            findings.append(Finding("warning", "figure_table_reference_distance", f"{label} 与最近正文引用距离较大；请确认核心证据解释是否足够邻近。", f"{label}: {distance} chars"))
    return findings


def _audit_float_caption_positions(main: str) -> list[Finding]:
    findings: list[Finding] = []
    for env in FIGURE_ENV_RE.findall(main):
        caption = env.find("\\caption")
        graphic = env.find("\\includegraphics")
        if caption >= 0 and graphic >= 0 and caption < graphic:
            findings.append(Finding("review_required", "figure_caption_before_graphic", "检测到图题位于图片之前；默认图题应放在图下。", re.sub(r"\s+", " ", env)[:140]))
            break
    for env in TABLE_ENV_RE.findall(main):
        caption = env.find("\\caption")
        tabular = env.find("\\begin{tabular")
        if caption >= 0 and tabular >= 0 and caption > tabular:
            findings.append(Finding("review_required", "table_caption_after_tabular", "检测到表题位于表格主体之后；默认表题应放在表上。", re.sub(r"\s+", " ", env)[:140]))
            break
    return findings


def _audit_abstract_and_keywords(body: str) -> list[Finding]:
    findings: list[Finding] = []
    match = ABSTRACT_ENV_RE.search(body)
    if match:
        abstract = match.group(1)
        if re.search(r"\\begin\{(?:figure|table)\*?\}|\\includegraphics", abstract):
            findings.append(Finding("review_required", "abstract_contains_figure_or_table", "摘要中检测到图或表；默认摘要只保留文本和高精度核心结果。"))
        if re.search(r"\\begin\{(?:equation|align|gather)\*?\}|\\\[|\$\$", abstract):
            findings.append(Finding("review_required", "abstract_contains_display_math", "摘要中检测到展示公式；如无特殊必要，移到正文。"))

    keyword_text = ""
    command = KEYWORD_COMMAND_RE.search(body)
    environment = KEYWORD_ENV_RE.search(body)
    if command:
        keyword_text = command.group(1)
    elif environment:
        keyword_text = environment.group(1)
    if keyword_text:
        plain = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", keyword_text)
        items = [item.strip() for item in re.split(r"[，,；;、]", plain) if item.strip()]
        if not 3 <= len(items) <= 6:
            findings.append(Finding("review_required", "keyword_count", f"检测到关键词数量约为 {len(items)}；中文国赛默认 3--6 个。", ", ".join(items[:8])))
    return findings


def _caption_length_warnings(main: str) -> list[Finding]:
    findings: list[Finding] = []
    captions = re.findall(r"\\caption\{([^{}]{1,500})\}", main)
    for caption in captions:
        plain = re.sub(r"\\[A-Za-z@]+|[$\\{}]", "", caption)
        if len(plain.strip()) > 90:
            findings.append(Finding("warning", "long_caption", "检测到较长图表题注；请确认正式 caption 只承担编号与核心语义，详细解释留在正文。", plain.strip()[:120]))
            break
    return findings


def audit_bibliography(tex_text: str, bib_text: str | None) -> list[Finding]:
    findings: list[Finding] = []
    cite_keys = _citation_keys(_strip_comments(tex_text))
    if bib_text is None:
        if cite_keys:
            findings.append(Finding("blocking", "bibliography_missing", "正文存在 citation，但未提供可检查的 references.bib。"))
        return findings

    entries = [key.strip() for _, key in BIB_ENTRY_RE.findall(bib_text)]
    seen: set[str] = set()
    duplicate: set[str] = set()
    for key in entries:
        if key in seen:
            duplicate.add(key)
        seen.add(key)
    for key in sorted(duplicate):
        findings.append(Finding("blocking", "duplicate_bib_key", f"references.bib 存在重复 citation key：{key}", key))

    bib_keys = set(entries)
    for key in sorted(cite_keys - bib_keys):
        findings.append(Finding("blocking", "missing_bib_key", f"正文 citation key 在 references.bib 中不存在：{key}", key))

    unused = sorted(bib_keys - cite_keys)
    if unused:
        preview = ", ".join(unused[:10]) + (" ..." if len(unused) > 10 else "")
        findings.append(Finding("warning", "unused_bib_entries", f"检测到 {len(unused)} 个未在正文引用的 BibTeX 条目；请确认是否为必要保留。", preview))

    if NOCITE_ALL_RE.search(tex_text):
        findings.append(Finding("warning", "nocite_all", "检测到 \\nocite{*}；正式论文应确认不是为了批量填充参考文献。"))
    return findings


def _framework_section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n#{1,4}\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def _split_cell_list(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped or stripped in {"—", "-", "无", "none", "None"}:
        return []
    return [item.strip() for item in re.split(r"[，,；;/]", stripped) if item.strip()]


def _markdown_rows(section: str, prefix_pattern: str) -> list[list[str]]:
    rows: list[list[str]] = []
    pattern = re.compile(prefix_pattern)
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and pattern.fullmatch(cells[0]):
            rows.append(cells)
    return rows


def _decimal_places(token: str) -> int | None:
    raw = token.rstrip("%")
    if "e" in raw.lower() or "." not in raw:
        return None
    return len(raw.split(".", 1)[1])


def _audit_terminology_from_framework(tex_text: str, framework_text: str) -> list[Finding]:
    findings: list[Finding] = []
    section = _framework_section(framework_text, "### Terminology Registry")
    rows = _markdown_rows(section, r"T[1-9][0-9]*")
    body = _remove_non_prose_blocks(_document_body(tex_text))
    alias_owner: dict[str, str] = {}
    for cells in rows:
        if len(cells) < 10:
            continue
        term_id, canonical = cells[0], cells[1]
        allowed = _split_cell_list(cells[4])
        discouraged = _split_cell_list(cells[5])
        confusable = _split_cell_list(cells[6])
        for alias in [*allowed, *discouraged]:
            prior = alias_owner.get(alias)
            if prior and prior != term_id:
                findings.append(Finding("blocking", "terminology_alias_collision", f"Terminology Registry 中别名“{alias}”映射到多个标准术语。", f"{prior}, {term_id}"))
            alias_owner[alias] = term_id
        for alias in discouraged:
            count = body.count(alias)
            if count:
                findings.append(Finding("warning", "discouraged_terminology_alias", f"正文出现 Terminology Registry 中不建议使用的别名“{alias}” {count} 次；请核对是否应统一为“{canonical}”。", term_id))
        for other in confusable:
            for match in re.finditer(re.escape(canonical), body):
                window = body[max(0, match.start() - 180): min(len(body), match.end() + 180)]
                if other and other in window:
                    findings.append(Finding("warning", "confusable_terms_nearby", f"易混术语“{canonical}”与“{other}”在局部同时出现；请确认定义、量纲和符号没有跨量混用。", term_id))
                    break
    return findings


def _audit_numeric_profile(tex_text: str, framework_text: str) -> list[Finding]:
    findings: list[Finding] = []
    section = _framework_section(framework_text, "### Numeric Profile")
    rows = _markdown_rows(section, r"N[1-9][0-9]*")
    body = _document_body(tex_text)
    abstract_match = ABSTRACT_ENV_RE.search(body)
    abstract = abstract_match.group(1) if abstract_match else ""
    plain_body = _remove_non_prose_blocks(body)
    plain_abstract = _remove_non_prose_blocks(abstract)
    for cells in rows:
        if len(cells) < 10:
            continue
        metric_id, metric, _, unit, display_form = cells[:5]
        expected_abstract = cells[5]
        expected_body = cells[6]
        expected_table = cells[7]
        basis = cells[9]
        expected = None
        match = re.search(r"\d+", expected_abstract)
        if match:
            expected = int(match.group(0))
        if expected is not None and metric:
            for metric_match in re.finditer(re.escape(metric), plain_abstract):
                window = plain_abstract[max(0, metric_match.start() - 120): min(len(plain_abstract), metric_match.end() + 120)]
                numbers = NUMBER_RE.findall(window)
                for token in numbers:
                    places = _decimal_places(token)
                    if places is not None and places < expected:
                        findings.append(Finding("warning", "numeric_precision_drift", f"摘要中“{metric}”附近数值的小数位少于 Numeric Profile 声明的 {expected} 位；若该数值就是核心答案，请恢复评分所需高精度。", f"{metric_id}: {token}; basis={basis}"))
                        break
                break
        if display_form == "percent" and metric and metric in plain_body:
            index = plain_body.find(metric)
            window = plain_body[max(0, index - 100): min(len(plain_body), index + len(metric) + 100)]
            tokens = NUMBER_RE.findall(window)
            if tokens and not any(token.endswith("%") for token in tokens):
                findings.append(Finding("warning", "percent_representation_drift", f"“{metric}”在 Numeric Profile 中声明为 percent，但邻近正文未检测到百分号；请确认是否误用比例值。", metric_id))
        if unit and unit not in {"—", "-", "无"}:
            compact_pattern = re.compile(rf"\d(?:\.\d+)?{re.escape(unit)}\b")
            match = compact_pattern.search(plain_body)
            if match:
                findings.append(Finding("warning", "unit_spacing", f"检测到数值与登记单位“{unit}”直接相连；请按项目单位格式检查是否需要空格。", match.group(0)))
        _ = expected_body, expected_table  # retained for future profile-aware checks without semantic guessing
    return findings


def audit_framework_consistency(tex_text: str, framework_text: str | None) -> list[Finding]:
    if not framework_text:
        return []
    findings = _audit_terminology_from_framework(tex_text, framework_text)
    findings.extend(_audit_numeric_profile(tex_text, framework_text))
    return findings


def audit_text(text: str) -> list[Finding]:
    body = _document_body(text)
    main = _main_text_before_appendix(body)
    findings: list[Finding] = []

    labels = LABEL_ANY_RE.findall(main)
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    for label in duplicates:
        findings.append(Finding("blocking", "duplicate_label", f"正文存在重复 LaTeX label：{label}", label))
    findings.extend(_audit_cross_references(main))
    findings.extend(_audit_float_caption_positions(main))
    findings.extend(_audit_abstract_and_keywords(body))
    findings.extend(_caption_length_warnings(main))

    if re.search(r"\\section\{结论\}", main):
        findings.append(Finding("review_required", "standalone_conclusion", "中文国赛默认不设置全文独立“结论”一级章；若比赛模板或当前论文确需，请保留明确理由。"))
    if re.search(r"\\section\{模型假设与符号说明\}", main):
        findings.append(Finding("review_required", "merged_assumption_symbol_section", "默认将“模型假设”和“符号说明”拆开；若特殊模板要求合并，请说明依据。"))
    if re.search(r"(?:^|[\s；;。])(?:H|A)\d+[\.、：:]", _remove_non_prose_blocks(main), flags=re.M):
        findings.append(Finding("warning", "visible_assumption_contract_id", "正文出现 H1/A1 等内部合同编号，请确认是否误把内部标识带入终稿。"))

    restatement = _section_content(main, "问题重述")
    if restatement is not None:
        if "\\subsection{问题背景}" not in restatement:
            findings.append(Finding("review_required", "missing_problem_background", "中文国赛默认“问题重述”包含“问题背景”；特殊结构需说明理由。"))
        if "\\subsection{问题提出}" not in restatement:
            findings.append(Finding("review_required", "missing_problem_statement", "中文国赛默认“问题重述”包含“问题提出”；特殊结构需说明理由。"))
        if "\\subsection{问题要求}" in restatement:
            findings.append(Finding("review_required", "legacy_problem_requirement", "中文国赛默认使用“问题提出”而非“问题要求”；若沿用当届模板请说明。"))
        background = _subsection_content(restatement, "问题背景")
        if background is not None:
            bg_paragraphs = _plain_paragraphs(background)
            if len(bg_paragraphs) > 2:
                findings.append(Finding("warning", "long_problem_background", "“问题背景”超过 2 个自然段，请确认每段都推进研究对象而非扩写通用背景。", f"{len(bg_paragraphs)} paragraphs"))
            if len(bg_paragraphs) >= 2 and re.search(r"全文|后文|章节|依次|本文结构|文章结构", bg_paragraphs[1]):
                findings.append(Finding("warning", "background_management_paragraph", "问题背景后段出现较多文章结构管理信息；请确认该段仍在收束研究对象。", bg_paragraphs[1][:120]))

    analysis = _section_content(main, "问题分析")
    if analysis is not None and re.search(r"\\begin\{(?:equation|align|gather)\*?\}|\\\[|\$[^$]+\$", analysis):
        findings.append(Finding("review_required", "formula_in_problem_analysis", "默认不在“问题分析”中放正式数学公式；若特殊题型需要极简定义，请人工确认。"))

    question_count = 0
    for heading, content in _question_sections(main):
        question_count += 1
        if not re.search(r"\\subsection\{核心模型汇总\}", content):
            findings.append(Finding("warning", "no_named_core_model_summary", f"{heading} 未检测到名为“核心模型汇总”的小节；该问可能为 inline/not_applicable，请与框架中的自适应状态核对。", heading))
        if not re.search(r"\\subsection\{求解结果\}", content):
            findings.append(Finding("warning", "missing_solution_result_section", f"{heading} 未检测到默认“求解结果”小节，请确认是否为简单问题或题型特定结构。", heading))
    if QUESTION_SECTION_RE.search(main) and question_count == 0:
        findings.append(Finding("warning", "question_section_parse", "检测到问题模型章节但未能完成逐问结构解析。"))

    for label in FIGTAB_LABEL_RE.findall(main):
        refs = len(_find_reference_position(main, label))
        if refs == 0:
            kind = "图" if label.startswith("fig:") else "表"
            findings.append(Finding("warning", "unreferenced_figure_table", f"正文{kind}标签 {label} 没有显式交叉引用；核心图表应在邻近正文中解释。", label))

    formula_finding = _formula_run_warning(main)
    if formula_finding:
        findings.append(formula_finding)

    prose_main = _remove_non_prose_blocks(main)
    for phrase in DERIVATION_STOCK_PATTERNS:
        count = prose_main.count(phrase)
        limit = 3 if phrase == "进一步可得" else 2
        if count > limit:
            findings.append(Finding("warning", "repeated_derivation_connector", f"推导连接语“{phrase}”出现 {count} 次；请确认它没有替代真正的机制/推理说明。", phrase))
            break

    meta_count = sum(prose_main.count(phrase) for phrase in META_NAV_PATTERNS)
    if meta_count >= 4:
        findings.append(Finding("warning", "repeated_meta_navigation", "“本节主要/下面将/为了便于”等管理型元话语较多，建议直接进入对象、关系或证据。", f"{meta_count} occurrences"))

    for match in PARAM_ASSIGN_RE.finditer(main):
        left = max(0, match.start() - 180)
        right = min(len(main), match.end() + 180)
        context = _remove_non_prose_blocks(main[left:right])
        if not PARAM_EVIDENCE_HINT_RE.search(context):
            findings.append(Finding("warning", "numeric_parameter_evidence", "检测到疑似直接指定数值参数，但邻近正文未出现题面来源、收敛/误差/验证等依据。", re.sub(r"\s+", " ", match.group(0))[:100]))
            break

    paragraphs = _plain_paragraphs(main)
    contrast_flags = [bool(CONTRAST_RE.search(p)) for p in paragraphs]
    for i in range(max(0, len(contrast_flags) - 2)):
        if all(contrast_flags[i:i + 3]):
            excerpt = " | ".join(p[:45] for p in paragraphs[i:i + 3])
            findings.append(Finding("warning", "consecutive_contrast_paragraphs", "连续 3 个自然段均使用明显否定/转折结构，请确认是否存在真实逻辑冲突。", excerpt))
            break
    for paragraph in paragraphs:
        if len(CONTRAST_RE.findall(paragraph)) >= 3:
            findings.append(Finding("warning", "dense_contrast_paragraph", "单个自然段中否定/转折较密，请复查是否存在不必要的先否定再肯定。", paragraph[:120]))
            break

    start_flags = [bool(PARAGRAPH_START_RE.search(p)) for p in paragraphs]
    if len(paragraphs) >= 6 and sum(start_flags) / len(paragraphs) >= 0.35:
        findings.append(Finding("warning", "repeated_paper_subject_start", "“本文/本问/该模型”作为段首主语的比例偏高。", f"{sum(start_flags)}/{len(paragraphs)} paragraphs"))
    for i in range(max(0, len(start_flags) - 2)):
        if all(start_flags[i:i + 3]):
            findings.append(Finding("warning", "consecutive_paper_subject_start", "连续 3 段以“本文/本问/该模型”起句，句法同构风险较高。"))
            break

    template_patterns = {
        "本文不是…而是…": re.compile(r"本文不是.{0,60}?而是"),
        "由于…因此本文不能…": re.compile(r"由于.{0,80}?因此本文不能"),
        "不能…只能…": re.compile(r"不能.{0,60}?只能"),
    }
    prose = "\n".join(paragraphs)
    for name, pattern in template_patterns.items():
        count = len(pattern.findall(prose))
        if count >= 2:
            findings.append(Finding("warning", "repeated_negation_template", f"“{name}”结构重复出现 {count} 次，建议改为对象/条件→处理→结论边界。", name))

    phrase_limits = {"由图可知": 2, "由表可知": 2, "见表": 4, "首先": 3, "其次": 3, "最后": 3}
    for phrase, limit in phrase_limits.items():
        count = prose.count(phrase)
        if count > limit:
            findings.append(Finding("warning", "repeated_stock_phrase", f"固定短语“{phrase}”出现 {count} 次，超过建议复查阈值 {limit}。", phrase))

    for i in range(max(0, len(paragraphs) - 1)):
        left_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}", paragraphs[i]))
        right_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}", paragraphs[i + 1]))
        union = left_tokens | right_tokens
        if union and len(left_tokens & right_tokens) / len(union) >= 0.72 and min(len(paragraphs[i]), len(paragraphs[i + 1])) >= 70:
            findings.append(Finding("warning", "possible_redundant_paragraph", "相邻段落词项高度重复；请执行 Paragraph Necessity Test，确认是否可删除、合并或移附录。", paragraphs[i][:90]))
            break

    return findings


def audit_file(
    path: Path,
    *,
    bib_path: Path | None = None,
    framework_path: Path | None = None,
) -> list[Finding]:
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    findings = audit_text(text)
    bib_text = None
    if bib_path is not None:
        if bib_path.is_file():
            bib_text = bib_path.read_text(encoding="utf-8-sig", errors="strict")
        else:
            bib_text = None
    elif (path.parent / "references.bib").is_file():
        bib_text = (path.parent / "references.bib").read_text(encoding="utf-8-sig", errors="strict")
    findings.extend(audit_bibliography(text, bib_text))

    framework_text = None
    if framework_path is not None and framework_path.is_file():
        framework_text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
    findings.extend(audit_framework_consistency(text, framework_text))
    return findings


def overall_status(findings: Iterable[Finding]) -> str:
    status = "pass"
    for finding in findings:
        if SEVERITY_ORDER[finding.severity] > SEVERITY_ORDER[status]:
            status = finding.severity
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit final LaTeX prose, structure, BibTeX and registered paper semantics.")
    parser.add_argument("tex", type=Path, help="LaTeX main file to audit")
    parser.add_argument("--bib", type=Path, help="Optional references.bib path; defaults to tex directory/references.bib when present")
    parser.add_argument("--framework", type=Path, help="Optional 模型论文框架.md for Terminology/Numeric Profile checks")
    parser.add_argument("--strict", action="store_true", help="Return exit code 1 for blocking or review_required findings")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    if not args.tex.is_file():
        raise SystemExit(f"LaTeX file not found: {args.tex}")

    findings = audit_file(args.tex, bib_path=args.bib, framework_path=args.framework)
    status = overall_status(findings)

    if args.json:
        print(json.dumps({"status": status, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"Paper prose audit: {status}")
        for item in findings:
            suffix = f" | {item.evidence}" if item.evidence else ""
            print(f"- [{item.severity}] {item.code}: {item.message}{suffix}")

    return 1 if args.strict and status in {"blocking", "review_required"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
