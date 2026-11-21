"""Measure four v11 P1 cases against a checkout; this does not run project gates.

    python tests/v11_reading_baseline.py [--checkout PATH] [--case NAME]

The default run succeeds when the controls work, even if the historical gap is
still visible. --require-target also checks the selected interface observations.
For a replacement API or versioned workbook protocol, add tests at its actual
entry point; legacy interfaces need not change to demonstrate a downstream fix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook


def checkout_git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def measure_review(root, project, commit):
    from resolve_runtime import resolve_runtime

    def framework_read(intent, request):
        plan = resolve_runtime(intent, request=request, competition="CUMCM",
                               project_root=project, question="Q1")
        reading = plan["reading_plan"]
        ranges = [interval for row in reading["read_now"]
                  if row["origin"] == "project" and row["path"] == "模型论文框架.md"
                  for interval in row["ranges"]]
        return {"assurance": plan["assurance"]["status"], "ranges": ranges}

    control = framework_read("framework_sync", "仅同步已验收结果摘要，不修改模型。")
    final = framework_read("review", "请对论文全文进行终审。")
    total = len((project / "模型论文框架.md").read_bytes().decode("utf-8").splitlines())
    covered = {n for a, b in final["ranges"] for n in range(a, b + 1)}
    return {
        "interface": "resolve_runtime -> reading_plan.read_now (project framework)",
        "controls": {"current_framework_readable": bool(control["ranges"]) and total > 0,
                     "project_assurance": control["assurance"] == final["assurance"] == "pass"},
        "observed": {"full_framework_in_initial_read": covered == set(range(1, total + 1))},
        "target": {"full_framework_in_initial_read": True},
        "evidence": {"framework_lines": total, "review": final, "scoped_sync": control},
    }


def measure_figures(root, project, commit):
    from resolve_runtime import resolve_runtime

    mechanism = "templates/figure/mechanism_contract.md"
    result = "templates/figure/result_figure_contract.md"

    def figure_sources(request):
        plan = resolve_runtime("figures", request=request, competition="CUMCM",
                               project_root=project, question="Q1")
        reading = plan["reading_plan"]
        evidence = {"profile": reading["profile"], "assurance": plan["assurance"]["status"]}
        for channel in ("read_now", "conditional"):
            evidence[channel] = sorted({row["path"] for row in reading[channel]} & {mechanism, result})
        return evidence

    single_mechanism = figure_sources("为问题一绘制机理图。")
    single_result = figure_sources("绘制一张误差分布结果图。")
    mixed = figure_sources("为问题一绘制机理图和误差分布图。")
    return {
        "interface": "resolve_runtime -> reading_plan (rule selection, not figure approval)",
        "controls": {"mechanism_alone_selected": mechanism in single_mechanism["read_now"],
                     "result_alone_selected": result in single_result["read_now"],
                     "project_assurance": all(x["assurance"] == "pass" for x in
                                              (single_mechanism, single_result, mixed))},
        "observed": {"both_in_initial_read": {mechanism, result}.issubset(mixed["read_now"])},
        "target": {"both_in_initial_read": True},
        "evidence": {"mechanism": single_mechanism, "result": single_result, "mixed": mixed},
    }


def measure_transport(root, project, commit):
    from reading_plan import validate_chunk_coverage

    path = "core/bootstrap.yaml"
    blob = checkout_git(root, "rev-parse", f"{commit}:{path}").decode().strip()
    source = checkout_git(root, "cat-file", "blob", blob)
    lines = source.decode("utf-8").splitlines(keepends=True)[:2]
    full = "".join(lines)
    shortened = lines[0] + lines[1].rstrip()[:len(lines[1].rstrip()) // 2]
    chunk = {"path": path, "source_commit": commit, "source_sha256": hashlib.sha256(source).hexdigest(),
             "source_blob_sha": blob, "start_line": 1, "end_line": 2}

    def coverage(text):
        return validate_chunk_coverage([[1, 2]], [dict(chunk, text=text)])["complete"]

    return {
        "interface": "reading_plan.validate_chunk_coverage (transport only)",
        "controls": {"intact_accepted": coverage(full), "missing_line_rejected": not coverage(lines[0]),
                     "damage_within_line": len(full.splitlines()) == len(shortened.splitlines()) == 2
                     and 0 < len(shortened) < len(full)},
        "observed": {"damaged_rejected": not coverage(shortened)},
        "target": {"damaged_rejected": True},
        "evidence": {"source_blob": blob, "selected_range": [1, 2],
                     "expected_utf8_bytes": len(full.encode()), "shortened_utf8_bytes": len(shortened.encode())},
    }


def measure_workbook(root, project, commit):
    from templates.code.hsk_pipeline.result_io import validate_workbook_file

    def validate(parameters):
        path = project / "问题一结果深化分析.xlsx"
        book = Workbook()
        config = book.active
        config.title = "运行配置"
        config.append(["项目", "值"])
        config.append(["stage", "analysis"])
        design = book.create_sheet("分析设计")
        design.append(["风险来源", "分析问题", "方法", "指标", "通过标准", "输入", "检验ID"])
        summary = book.create_sheet("结论稳定性汇总")
        summary.append(["核心结论", "分析方法", "稳定范围", "是否保持", "检验ID", "证据工作表"])
        for key in ("a", "b"):
            design.append(["参数扰动", f"改变 {key} 是否影响目标", "参数敏感性",
                           "成本差", "成本差为零", key, key])
            summary.append([f"扰动 {key} 时成本相同", "参数敏感性", "0 到 1", True, key, "参数敏感性"])
        detail = book.create_sheet("参数敏感性")
        detail.append(["参数", "基准值", "变化值", "结果指标", "检验ID"])
        for key in parameters:
            detail.append([key, 0, 1, 0, key])
        book.save(path)
        book.close()
        try:
            validate_workbook_file(path, "result_analysis", analysis_methods=["参数敏感性"])
        except ValueError as exc:
            return {"structurally_valid": False, "reason": str(exc)}
        return {"structurally_valid": True}

    complete = validate(["a", "b"])
    partial = validate(["a"])
    empty = validate([])
    return {
        "interface": "validate_workbook_file (ordinary 03B structure, no run receipt or state write)",
        "controls": {"both_details_accepted": complete["structurally_valid"],
                     "empty_detail_rejected": not empty["structurally_valid"]},
        "observed": {"missing_experiment_rejected": not partial["structurally_valid"]},
        "target": {"missing_experiment_rejected": True},
        "evidence": {"design_ids": ["a", "b"], "with_a_and_b": complete, "with_a_only": partial,
                     "no_detail": empty},
    }


CASES = {"review": measure_review, "figures": measure_figures,
         "transport": measure_transport, "workbook": measure_workbook}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--require-target", action="store_true")
    args = parser.parse_args()
    root = args.checkout.resolve()
    commit = checkout_git(root, "rev-parse", "HEAD").decode().strip()
    tracked_changes = bool(checkout_git(root, "status", "--porcelain", "--untracked-files=no").strip())
    sys.path[:0] = [str(root / "scripts"), str(root / "tests"), str(root)]
    names = [args.case] if args.case else list(CASES)
    results = {}
    with TemporaryDirectory() as temp:
        project = Path(temp)
        if any(name in {"review", "figures"} for name in names):
            from reading_plan_cases import build_project
            build_project(root, project, "current")
        for name in names:
            results[name] = CASES[name](root, project, commit)
    controls_ok = all(all(case["controls"].values()) for case in results.values())
    targets_met = all(case["observed"] == case["target"] for case in results.values())
    print(json.dumps({"checkout_head": commit, "tracked_worktree_modified": tracked_changes,
                      "cases": results}, indent=2))
    return int(not controls_ok or (args.require_target and not targets_met))


if __name__ == "__main__":
    raise SystemExit(main())
