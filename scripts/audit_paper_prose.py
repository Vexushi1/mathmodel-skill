#!/usr/bin/env python3
"""Conservative prose/structure/BibTeX audit for HSK LaTeX papers.

Severity follows writing governance:
- blocking: deterministic Hard failure;
- review_required: Default deviation requiring a reason;
- warning: Recommendation/style risk.

The audit never rewrites paper text and never infers mathematical correctness, formula
source validity, parameter optimality, theorem applicability, citation semantics, or
unregistered terminology equivalence.
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
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^{}]+)\}")
CITE_RE = re.compile(r"\\(?:cite|citep|citet|parencite|textcite)\*?(?:\[[^\]]*\])?\{([^{}]+)\}")
NOCITE_ALL_RE = re.compile(r"\\nocite\{\*\}")
REF_TEMPLATE = r"\\(?:ref|eqref|autoref|cref|Cref)\{{{label}\}}"
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
BIB_ENTRY_RE = re.compile(r"(?ms)^\s*@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,")
FIGURE_ENV_RE = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", flags=re.S)
TABLE_ENV_RE = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", flags=re.S)
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", flags=re.S)
ABSTRACT_ENV_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", flags=re.S)
KEYWORDS_RE = re.compile(r"\\(?:keywords|keyword)\s*\{([^{}]+)\}", flags=re.I)
DECIMAL_RE = re.compile(r"(?<![\w.])[-+]?\d+\.(\d+)(?!\w)")
TERM_ID_RE = re.compile(r"^T[1-9][0-9]*$")
METRIC_ID_RE = re.compile(r"^N[1-9][0-9]*$")


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
    text = re.sub(r"\\(?:label|ref|eqref|autoref|cref|Cref|cite|citep|citet|parencite|textcite)\{[^{}]*\}", " ", text)
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
                "warning", "dense_formula_run",
                "连续多个展示公式之间解释文字很少；请人工确认核心关系的来源、关键推理和后续用途。", excerpt,
            )
    return None


def _citation_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for group in CITE_RE.findall(tex):
        keys.update(item.strip() for item in group.split(",") if item.strip())
    return keys


def _markdown_table_rows(text: str, heading: str, id_pattern: re.Pattern[str]) -> list[list[str]]:
    start = text.find(heading)
    if start < 0:
        return []
    tail = text[start + len(heading):]
    match = re.search(r"(?m)^#{1,3}\s+", tail)
    block = tail[:match.start()] if match else tail
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and id_pattern.fullmatch(cells[0]):
            rows.append(cells)
    return rows


def _split_aliases(value: str) -> set[str]:
    return {item.strip() for item in re.split(r"[/、,，;；]", value) if item.strip() and item.strip() not in {"无", "-", "—"}}


def audit_framework_semantics(tex_text: str, framework_text: str | None) -> list[Finding]:
    findings: list[Finding] = []
    if framework_text is None:
        return findings
    prose = _remove_non_prose_blocks(_main_text_before_appendix(_document_body(tex_text)))

    term_rows = _markdown_table_rows(framework_text, "### Terminology Registry", TERM_ID_RE)
    alias_owner: dict[str, str] = {}
    for row in term_rows:
        if len(row) < 9:
            continue
        canonical = row[1]
        discouraged = _split_aliases(row[5])
        confusable = _split_aliases(row[6])
        for alias in _split_aliases(row[4]) | discouraged:
            owner = alias_owner.get(alias)
            if owner and owner != canonical:
                findings.append(Finding("blocking", "terminology_alias_collision", f"Terminology Registry 中别名“{alias}”同时映射到不同标准术语。", alias))
            alias_owner[alias] = canonical
        used_discouraged = sorted(alias for alias in discouraged if alias and alias in prose)
        if used_discouraged:
            findings.append(Finding("warning", "registered_terminology_drift", f"正文出现 {row[0]} 的不推荐别名，请统一回标准术语“{canonical}”。", ", ".join(used_discouraged[:6])))
        if canonical and canonical in prose:
            for other in confusable:
                for match in re.finditer(re.escape(canonical), prose):
                    window = prose[max(0, match.start() - 250): min(len(prose), match.end() + 250)]
                    if other in window:
                        findings.append(Finding("warning", "local_confusable_terms", f"标准术语“{canonical}”与易混术语“{other}”在局部同时出现，请确认定义、分母/单位或样本口径没有混用。", f"{canonical} / {other}"))
                        break

    metric_rows = _markdown_table_rows(framework_text, "### Numeric Profile", METRIC_ID_RE)
    for row in metric_rows:
        if len(row) < 10:
            continue
        metric = row[1]
        required = row[5]
        basis = row[9]
        digits = [int(x) for x in re.findall(r"\d+", required)]
        if not metric or not digits:
            continue
        min_digits = min(digits)
        for match in re.finditer(re.escape(metric), prose):
            window = prose[match.end(): min(len(prose), match.end() + 120)]
            decimal = DECIMAL_RE.search(window)
            if not decimal:
                continue
            actual = len(decimal.group(1))
            if actual < min_digits:
                verified = bool(re.search(r"已核验|官方|题面明确|评分口径", basis))
                severity = "blocking" if verified else "warning"
                code = "scoring_result_precision_loss" if verified else "numeric_precision_anomaly"
                findings.append(Finding(severity, code, f"指标“{metric}”邻近数值仅保留 {actual} 位小数，低于 Numeric Profile 声明的至少 {min_digits} 位。", decimal.group(0)))
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


def _audit_reference_closure(main: str) -> list[Finding]:
    findings: list[Finding] = []
    labels = LABEL_ANY_RE.findall(main)
    label_set = set(labels)
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    for label in duplicates:
        findings.append(Finding("blocking", "duplicate_label", f"正文存在重复 LaTeX label：{label}", label))

    ref_targets = [target.strip() for target in REF_RE.findall(main)]
    for target in sorted(set(ref_targets) - label_set):
        findings.append(Finding("blocking", "missing_ref_target", f"正文交叉引用目标不存在：{target}", target))

    for label in sorted(label_set):
        refs = list(re.finditer(REF_TEMPLATE.format(label=re.escape(label)), main))
        if not refs:
            kind = "图/表" if label.startswith(("fig:", "tab:")) else "公式/章节/命题或其他对象"
            findings.append(Finding("warning", "unused_label", f"{kind} label {label} 未被正文显式引用，请确认编号是否有必要。", label))
            continue
        label_match = re.search(rf"\\label\{{{re.escape(label)}\}}", main)
        if label_match:
            nearest = min(abs(ref.start() - label_match.start()) for ref in refs)
            if label.startswith(("fig:", "tab:")) and nearest > 2500:
                findings.append(Finding("warning", "distant_figure_table_reference", f"图表 {label} 的最近正文引用距离较远，请确认图表与解释仍形成局部证据闭环。", f"distance={nearest}"))
    return findings


def _audit_float_structure(main: str) -> list[Finding]:
    findings: list[Finding] = []
    for env in FIGURE_ENV_RE.findall(main):
        caption = re.search(r"\\caption", env)
        graphic = re.search(r"\\includegraphics", env)
        if caption and graphic and caption.start() < graphic.start():
            findings.append(Finding("review_required", "figure_caption_before_graphic", "检测到图题位于图片命令之前；当前论文规范默认图题置于图下。"))
        for text in CAPTION_RE.findall(env):
            plain = re.sub(r"\\[A-Za-z]+|[{}]", "", text).strip()
            if len(plain) > 90:
                findings.append(Finding("warning", "long_figure_caption", "图题较长，请确认没有把正文解释塞入 caption。", plain[:120]))
    for env in TABLE_ENV_RE.findall(main):
        caption = re.search(r"\\caption", env)
        tabular = re.search(r"\\begin\{(?:tabular|tabularx|longtable)\}", env)
        if caption and tabular and caption.start() > tabular.start():
            findings.append(Finding("review_required", "table_caption_after_table", "检测到表题位于表格主体之后；当前论文规范默认表题置于表上。"))
        for text in CAPTION_RE.findall(env):
            plain = re.sub(r"\\[A-Za-z]+|[{}]", "", text).strip()
            if len(plain) > 90:
                findings.append(Finding("warning", "long_table_caption", "表题较长，请确认没有把结果解释塞入 caption。", plain[:120]))
    return findings


def _audit_abstract_and_keywords(main: str) -> list[Finding]:
    findings: list[Finding] = []
    abstract = ABSTRACT_ENV_RE.search(main)
    if abstract:
        content = abstract.group(1)
        if re.search(r"\\begin\{(?:figure|table)\*?\}|\\includegraphics|\\\[|\$\$|\\begin\{(?:equation|align|gather)", content):
            findings.append(Finding("review_required", "abstract_contains_float_or_display_formula", "摘要中检测到图、表、图片或展示公式；数学建模摘要默认只保留文字和必要行内符号。"))
    keyword_match = KEYWORDS_RE.search(main)
    if keyword_match:
        raw = keyword_match.group(1)
        keywords = [item.strip() for item in re.split(r"[,，;；、]", raw) if item.strip()]
        if not 3 <= len(keywords) <= 6:
            findings.append(Finding("review_required", "keyword_count", f"检测到关键词数量为 {len(keywords)}；当前默认范围为 3--6 个。", raw[:120]))
    return findings


def audit_text(text: str) -> list[Finding]:
    body = _document_body(text)
    main = _main_text_before_appendix(body)
    findings: list[Finding] = []

    findings.extend(_audit_reference_closure(main))
    findings.extend(_audit_float_structure(main))
    findings.extend(_audit_abstract_and_keywords(main))

    # Default structure checks: review_required, not absolute Hard failures.
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

    # Paragraph Necessity is deliberately heuristic-only: flag generic material, never auto-delete.
    generic_hits = sum(prose.count(phrase) for phrase in ("算法最早由", "广泛应用于", "具有收敛速度快", "具有较强鲁棒性", "具有重要意义"))
    if generic_hits >= 3:
        findings.append(Finding("warning", "possible_redundant_paragraph", "检测到较多算法百科/通用价值类表达；请执行 Paragraph Necessity Test，确认删除后是否真的损失题意、机制、数学关系、求解依据、结果证据或必要边界。", f"{generic_hits} generic phrases"))

    return findings


def audit_file(
    path: Path, *, bib_path: Path | None = None, framework_path: Path | None = None
) -> list[Finding]:
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    findings = audit_text(text)
    bib_text = None
    if bib_path is not None:
        if bib_path.is_file():
            bib_text = bib_path.read_text(encoding="utf-8-sig", errors="strict")
    elif (path.parent / "references.bib").is_file():
        bib_text = (path.parent / "references.bib").read_text(encoding="utf-8-sig", errors="strict")
    findings.extend(audit_bibliography(text, bib_text))

    framework_text = None
    if framework_path is not None and framework_path.is_file():
        framework_text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
    findings.extend(audit_framework_semantics(text, framework_text))
    return findings


def overall_status(findings: Iterable[Finding]) -> str:
    status = "pass"
    for finding in findings:
        if SEVERITY_ORDER[finding.severity] > SEVERITY_ORDER[status]:
            status = finding.severity
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit final LaTeX prose, structure, project semantics and BibTeX closure.")
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
