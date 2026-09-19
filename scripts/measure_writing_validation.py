#!/usr/bin/env python3
"""Measure the writing-validation call graph and candidate costs for W0.

This is maintenance-only evidence for docs/writing_readability_validation_slimming_plan.md.
It is read-only, creates no project state, changes no severity, and defines no production
threshold. Timing is descriptive only and must not be used as a gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
RUNTIME = ROOT / "core" / "writing_runtime_contract.yaml"
FORMAL_AUDIT = ROOT / "scripts" / "audit_paper_prose.py"
SURFACE_AUDIT = ROOT / "scripts" / "audit_v8_writing_surface.py"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_module(name: str, path: Path):
    scripts = str(path.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _question(index: int, *, extra_paragraphs: int = 0) -> str:
    filler = "\n\n".join(
        f"第{j + 1}段说明当前对象、边界条件、数值证据和下游用途，避免把计算步骤写成软件流水账。"
        for j in range(extra_paragraphs)
    )
    return rf"""
\section{{问题{index}模型建立及求解}}
\subsection{{模型建立}}
根据题目条件定义状态变量，并由守恒关系得到当前问题的控制方程。
\begin{{equation}}
u_{{{index}}}(t+1)=u_{{{index}}}(t)+\Delta t\,f_{{{index}}}(u,t)
\end{{equation}}
该关系确定后续计算结构与边界解释。
{filler}
\subsection{{模型求解}}
当前模型包含约束、边界和离散状态，因此采用与该计算结构一致的数值推进方法。
\subsection{{求解结果}}
得到本问的关键结果，并说明其对设问的直接含义。
\subsection{{结果验证}}
针对离散误差和边界扰动复核主结论是否改变。
"""


def _fixture(question_count: int, extra_paragraphs: int) -> str:
    body = "\n".join(
        _question(i + 1, extra_paragraphs=extra_paragraphs)
        for i in range(question_count)
    )
    return "\\begin{document}\n" + body + "\n\\end{document}\n"


def timing_fixtures() -> dict[str, str]:
    return {
        "small": _fixture(1, 1),
        "medium": _fixture(3, 5),
        "large": _fixture(6, 12),
    }


def candidate_snapshots() -> list[dict[str, Any]]:
    return [
        {
            "id": "many_independent_subsections",
            "audit": "formal",
            "target_code": "question_subsection_granularity",
            "expect_present": True,
            "text": r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{状态变量定义}
定义状态变量并说明量纲与边界。
\subsection{边界条件构造}
根据题面边界给出独立边界条件。
\subsection{控制方程}
由守恒关系得到控制方程并说明适用范围。
\subsection{数值求解}
当前模型具有非线性约束和离散状态，因此采用相应数值推进方法。
\subsection{求解结果}
给出结果并回答设问。
\end{document}
""",
            "interpretation": "五个二级小节均承担独立任务；仅按数量触发 review_required 是 W3 候选。",
        },
        {
            "id": "mechanical_subsection_split",
            "audit": "formal",
            "target_code": "possible_mechanical_model_subsection_split",
            "expect_present": True,
            "text": r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{决策变量}
定义变量。
\subsection{目标函数}
给出目标。
\subsection{约束条件}
给出约束。
\subsection{核心模型汇总}
重复汇总前述短定义。
\subsection{求解结果}
给出结果。
\end{document}
""",
            "interpretation": "机械拆分有独立表面证据，不应依赖小节总数本身。",
        },
        {
            "id": "result_validation_without_bridge",
            "audit": "surface",
            "target_code": "result_validation_bridge_risk",
            "expect_present": True,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{求解结果}
得到最优方案与目标值。
\subsection{敏感性分析}
改变参数并重新计算。
""",
            "interpretation": "缺少待检验风险说明，保留 review_required 有正例依据。",
        },
        {
            "id": "result_validation_with_bridge",
            "audit": "surface",
            "target_code": "result_validation_bridge_risk",
            "expect_present": False,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{求解结果}
得到最优方案与目标值。该结果仍可能受边界参数扰动影响，因此进一步检验方案排序是否保持稳定。
\subsection{敏感性分析}
改变参数并重新计算。
""",
            "interpretation": "有明确风险桥时同一检查不误报。",
        },
        {
            "id": "solver_first_without_structure",
            "audit": "surface",
            "target_code": "solver_first_narrative",
            "expect_present": True,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{模型求解}
采用遗传算法进行求解，并利用其全局搜索能力得到结果。
\subsection{求解结果}
给出结果。
""",
            "interpretation": "算法先于模型结构，保留 review_required 有正例依据。",
        },
        {
            "id": "solver_with_structure",
            "audit": "surface",
            "target_code": "solver_first_narrative",
            "expect_present": False,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{模型求解}
当前目标函数非凸且可行域包含离散约束，因此采用遗传算法搜索候选解。
\subsection{求解结果}
给出结果。
""",
            "interpretation": "先说明模型结构后不应触发 solver-first 风险。",
        },
        {
            "id": "stage_order_inverted",
            "audit": "surface",
            "target_code": "question_stage_order_risk",
            "expect_present": True,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{求解结果}
先给出结果。
\subsection{模型求解}
随后才说明求解方法。
""",
            "interpretation": "明确功能标题倒置，保留 review_required 有正例依据。",
        },
        {
            "id": "stage_order_valid",
            "audit": "surface",
            "target_code": "question_stage_order_risk",
            "expect_present": False,
            "text": r"""
\section{问题一模型建立及求解}
\subsection{模型建立}
先闭合模型。
\subsection{模型求解}
再说明求解。
\subsection{求解结果}
最后给出结果。
""",
            "interpretation": "正常顺序不应触发次序风险。",
        },
    ]


def _time_call(fn: Callable[[str], Any], text: str, repeats: int, warmup: int) -> dict[str, float]:
    for _ in range(warmup):
        fn(text)
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        fn(text)
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, int(round(0.95 * len(ordered))) - 1))
    return {
        "median_ms": round(float(statistics.median(samples)), 4),
        "min_ms": round(float(min(samples)), 4),
        "p95_ms": round(float(ordered[p95_index]), 4),
        "max_ms": round(float(max(samples)), 4),
    }


def _surface_preprocess_calls(surface: Any, text: str) -> int:
    original = surface.strip_comments_and_blocks
    calls = 0

    def wrapped(value: str) -> str:
        nonlocal calls
        calls += 1
        return original(value)

    surface.strip_comments_and_blocks = wrapped
    try:
        surface.audit_text(text)
    finally:
        surface.strip_comments_and_blocks = original
    return calls


def _formal_nested_surface_calls(formal: Any, text: str) -> int:
    original = formal.audit_v8_surface_text
    calls = 0

    def wrapped(value: str):
        nonlocal calls
        calls += 1
        return original(value)

    formal.audit_v8_surface_text = wrapped
    try:
        formal.audit_text(text)
    finally:
        formal.audit_v8_surface_text = original
    return calls


def _runtime_call_graph(root: Path) -> dict[str, Any]:
    runtime = yaml.safe_load((root / "core" / "writing_runtime_contract.yaml").read_text(encoding="utf-8"))
    stages = runtime["template_first_progressive_authoring"]["stages"]
    by_id = {stage["id"]: stage for stage in stages}
    draft = by_id["draft_semantic_review"]
    latex = by_id["latex_assembly_audit_and_compile"]
    return {
        "draft_semantic_review": {
            "run_now": draft.get("run_now", []),
            "surface_audit_direct": "scripts/audit_v8_writing_surface.py" in draft.get("run_now", []),
            "input_stage": "draft_before_cleanup",
        },
        "latex_assembly_audit_and_compile": {
            "run_now": latex.get("run_now", []),
            "formal_entry": "scripts/audit_latex_project.py",
            "formal_delegate": "scripts/audit_paper_prose.py",
            "nested_surface_delegate": "scripts/audit_v8_writing_surface.py",
            "input_stage": "post_cleanup_assembled_latex",
        },
        "reuse_adjudication": {
            "same_input": False,
            "reason": "AI Cleanup and LaTeX assembly occur between draft surface audit and formal audit.",
            "cross_stage_cache_allowed": False,
        },
    }


def collect(root: Path = ROOT, *, repeats: int = 25, warmup: int = 3) -> dict[str, Any]:
    if repeats <= 0 or warmup < 0:
        raise ValueError("repeats must be positive and warmup nonnegative")
    root = root.resolve()
    surface = _load_module("w0_surface_audit", root / "scripts" / "audit_v8_writing_surface.py")
    formal = _load_module("w0_formal_prose_audit", root / "scripts" / "audit_paper_prose.py")

    fixtures = timing_fixtures()
    timing_rows = []
    for name, text in fixtures.items():
        direct_surface = _time_call(surface.audit_text, text, repeats, warmup)
        nested_calls = _formal_nested_surface_calls(formal, text)
        preprocess_calls = _surface_preprocess_calls(surface, text)

        original_nested = formal.audit_v8_surface_text
        formal_without_surface = None
        try:
            formal.audit_v8_surface_text = lambda _text: []
            formal_without_surface = _time_call(formal.audit_text, text, repeats, warmup)
        finally:
            formal.audit_v8_surface_text = original_nested
        formal_with_surface = _time_call(formal.audit_text, text, repeats, warmup)

        timing_rows.append({
            "fixture": name,
            "bytes": len(text.encode("utf-8")),
            "lines": len(text.splitlines()),
            "sha256": _sha256_text(text),
            "surface_audit": direct_surface,
            "formal_prose_with_nested_surface": formal_with_surface,
            "formal_prose_without_nested_surface": formal_without_surface,
            "surface_preprocess_calls_per_direct_audit": preprocess_calls,
            "nested_surface_calls_per_formal_audit": nested_calls,
        })

    snapshot_rows = []
    for case in candidate_snapshots():
        module = formal if case["audit"] == "formal" else surface
        findings = module.audit_text(case["text"])
        codes = {item.code: item.severity for item in findings}
        present = case["target_code"] in codes
        snapshot_rows.append({
            "id": case["id"],
            "audit": case["audit"],
            "target_code": case["target_code"],
            "expect_present": case["expect_present"],
            "observed_present": present,
            "observed_severity": codes.get(case["target_code"]),
            "expectation_matches": present == case["expect_present"],
            "all_finding_codes": sorted(codes),
            "input_sha256": _sha256_text(case["text"]),
            "input_bytes": len(case["text"].encode("utf-8")),
            "interpretation": case["interpretation"],
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "writing_validation_w0_maintenance_evidence_only",
        "source_commit": None,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "timer": "time.perf_counter_ns",
            "repeats": repeats,
            "warmup": warmup,
            "timing_is_gate": False,
        },
        "call_graph": _runtime_call_graph(root),
        "timing": timing_rows,
        "candidate_snapshots": snapshot_rows,
        "invariants": {
            "changes_severity": False,
            "changes_runtime_or_gate": False,
            "creates_cache_or_trust_token": False,
            "hard_error_detection_reduction_claimed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--repeats", type=int, default=25)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect(args.root, repeats=args.repeats, warmup=args.warmup)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
