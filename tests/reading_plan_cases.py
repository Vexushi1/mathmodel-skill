"""Small synthetic reading-scope cases; acceptance flags are test fixtures, never real receipts."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import yaml

CASES = (
    ("facts_current", "framework_sync", "仅同步已验收结果摘要，不修改模型。", "current"),
    ("facts_unscoped", "framework_sync", "仅同步已验收结果摘要，不修改模型。", None),
    ("facts_model_change", "framework_sync", "修改物性公式和假设并同步结果摘要。", "current"),
    ("facts_ambiguous", "framework_sync", "更新框架。", "current"),
    ("facts_stale_framework", "framework_sync", "仅同步已验收结果摘要，不修改模型。", "stale_framework"),
    ("facts_hash_drift", "framework_sync", "仅同步已验收结果摘要，不修改模型。", "data_drift"),
    ("facts_identity_drift", "framework_sync", "仅同步已验收结果摘要，不修改模型。", "identity_drift"),
    ("facts_stale_dependency", "framework_sync", "仅同步已验收结果摘要，不修改模型。", "stale_dependency"),
    ("new_field", "figures", "为时空含水率设计结果图。", None),
    ("style_current", "figures", "只改现有图的配色与线宽，保持数据和坐标口径不变。", "current"),
    ("style_unscoped", "figures", "只改配色和线宽。", None),
    ("style_data_change", "figures", "只改配色，同时对数据平滑。", "current"),
    ("style_figure_drift", "figures", "只改配色和线宽。", "figure_drift"),
    ("style_no_approval", "figures", "只改配色和线宽。", "no_figure_approval"),
    ("mechanism", "editable_mechanism_diagram", "绘制可编辑机理图。", None),
    ("project_sync", "project_sync", "检查产物一致性。", None),
    ("receipt", "returned_workbook_validation", "验收返回工作簿。", None),
    ("mixed", ["figures", "framework_sync"], "绘图并修改框架。", "current"),
    ("cumcm_writing", "latex", "修改摘要措辞。", None),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_current_solver_project(root: Path, state: dict) -> None:
    """Give synthetic accepted results a current Python 1.1 source identity."""
    q = state["subproblems"]["Q1"]
    folder = root / "问题一求解"
    accepted_primary = q["validated_artifact_hashes"]["solution_workbook"]
    from artifact_fingerprint import combined_hash
    data = root / "data.csv"
    data.write_text("x,y\n1,2\n", encoding="utf-8")
    data_hash = combined_hash([data], root)
    q.update(data_hash=data_hash, validated_data_hash=data_hash)
    q["solver_execution"] = {}
    for stage, filename, code_field, hash_field in (
        ("primary", "问题一求解.py", "code", "primary_code_sha256"),
        ("analysis", "问题一结果深化分析.py", "result_analysis_code", "analysis_code_sha256"),
    ):
        config = {
            "stage": stage, "problem_name": "问题一", "solver_backend": "python",
            "data_paths": ["data.csv"], "data_sha256": data_hash, "solver": "direct",
            "random_seed": 2026, "tolerance": 1e-8, "iteration_or_time_limit": "direct",
            "expected_workbook": "问题一求解结果.xlsx" if stage == "primary" else "问题一结果深化分析.xlsx",
            "run_receipt_protocol_version": "1.1.0", "code_dependencies": [],
        }
        if stage == "primary":
            config["primary_quality_protocol_version"] = "1.0.0"
        else:
            config["primary_workbook_sha256"] = accepted_primary
        source = folder / filename
        source.write_text(
            f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n\n"
            "if __name__ == '__main__':\n    main()\n", encoding="utf-8",
        )
        relative = source.relative_to(root).as_posix()
        entry_hash = digest(source)
        bundle = hashlib.sha256(relative.encode("utf-8") + b"\0" + bytes.fromhex(entry_hash)).hexdigest()
        q.update({code_field: relative, hash_field: entry_hash})
        q["solver_execution"][stage] = {
            "bundle_sha256": bundle, "validated_bundle_sha256": bundle,
        }
        layer = "primary_code" if stage == "primary" else "analysis_code"
        for field in ("artifact_hashes", "validated_artifact_hashes"):
            q.setdefault(field, {})[layer] = entry_hash
    for field in ("artifact_hashes", "validated_artifact_hashes"):
        q.setdefault(field, {})["data"] = data_hash
    state["execution"] = {
        "solver_backend": "python", "solver_backend_selection_reason": "Synthetic whole-problem review",
    }


def build_project(repo: Path, root: Path, mode: str) -> None:
    path = repo / "tests" / "optimization_baseline.py"
    spec = importlib.util.spec_from_file_location("p2_existing_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing P1 fixture is unavailable")
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    helper.build_project(repo, root, "identity_drift" if mode == "identity_drift" else "approved")
    framework = root / "模型论文框架.md"
    text = framework.read_text(encoding="utf-8")
    text = text.replace("### Q1", "## 当前有效口径\n已锁定的测试模型。\n\n## 各问模型与结果\n\n### Q1", 1)
    text += "\n## 图表证据链\n登记图与工作簿对应关系。\n\n## 待办与缺口\n当前测试无待办。\n"
    framework.write_text(text, encoding="utf-8")
    state_path = root / "state/project_state.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    q = state["subproblems"]["Q1"]
    folder = root / "问题一求解"
    folder.mkdir()
    # These binding tests exercise file provenance only, not numerical workbook acceptance.
    for field, name in (("solution_workbook", "问题一求解结果.xlsx"),
                        ("result_analysis_workbook", "问题一结果深化分析.xlsx")):
        path = folder / name
        path.write_bytes(b"synthetic previously-accepted binding fixture, not numerical data\n")
        q[field] = str(path.relative_to(root))
        q.setdefault("validated_artifact_hashes", {})[field] = digest(path)
    q.update(primary_execution_status="accepted", result_quality_status="passed",
             analysis_execution_status="accepted", result_analysis_status="passed")
    bind_current_solver_project(root, state)
    script = folder / "q1_plot.m"
    script.write_text("% synthetic rendering source, never executed\n", encoding="utf-8")
    figure = folder / "test.svg"
    figure.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', encoding="utf-8")
    from artifact_fingerprint import combined_hash
    q["matlab_script"] = str(script.relative_to(root))
    q["validated_artifact_hashes"].update(matlab_script=digest(script), figure_bundle=combined_hash([figure], root))
    state["artifacts"] = {"approved_figures": [str(figure.relative_to(root))]}
    state["paper_framework"] = {"sync_status": "current", "sha256": digest(framework)}
    if mode == "stale_framework":
        state["paper_framework"]["sync_status"] = "stale"
    elif mode == "data_drift":
        (root / q["solution_workbook"]).write_bytes(b"different input after acceptance")
    elif mode == "figure_drift":
        figure.write_text("changed after visual approval", encoding="utf-8")
    elif mode == "no_figure_approval":
        state["artifacts"]["approved_figures"] = []
    elif mode == "stale_dependency":
        q["depends_on"] = [{"question": "Q2", "kind": "result", "note": "test dependency"}]
        state["subproblems"]["Q2"] = {"artifacts_stale": True}
    elif mode not in {"current", "identity_drift"}:
        raise ValueError(f"Unknown reading fixture: {mode}")
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
