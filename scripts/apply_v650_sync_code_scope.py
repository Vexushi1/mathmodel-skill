#!/usr/bin/env python3
"""Add the formal code-delivery scope to sync_project without executing task code."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "sync_project.py"


def replace(old: str, new: str) -> None:
    text = PATH.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"missing sync_project anchor: {old[:120]!r}")
    PATH.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def main() -> int:
    replace(
        '''PHASE_SCOPE = {
    "problem_audit": "design", "model_design": "design",
    "solve_validate": "results", "result_analysis": "results",
''',
        '''PHASE_SCOPE = {
    "problem_audit": "design", "model_design": "design",
    "solve_validate": "code", "result_analysis": "code",
''',
    )
    helper = '''def _code_delivery_artifact_issues(
    root: Path,
    snapshots: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    """Check a code handoff by files and reports only; never import task code."""
    issues: list[str] = []
    if not any(snapshot.get("code_files") for snapshot in snapshots.values()):
        issues.append("代码交付缺少问题求解或结果深化Python脚本")
    configs = sorted(
        {
            *root.glob("问题*完整运行配置.yaml"),
            *root.glob("问题*结果深化完整运行配置.yaml"),
        },
        key=lambda item: item.name,
    )
    if not configs:
        issues.append("代码交付缺少完整运行配置")
    for config in configs:
        instruction = config.with_name(
            config.name.replace("完整运行配置.yaml", "本地运行说明.md")
        )
        if not instruction.is_file():
            issues.append(f"代码交付缺少本地运行说明: {instruction.name}")
    if not configs and not any(root.glob("问题*本地运行说明.md")):
        issues.append("代码交付缺少本地运行说明")
    report_path = root / "code_delivery_report.yaml"
    if not report_path.is_file():
        issues.append("代码交付缺少code_delivery_report.yaml")
    else:
        report = load_json_or_yaml(report_path)
        if str(report.get("status", "")).lower() != "passed":
            issues.append("code_delivery_report未通过")
        if report.get("task_code_executed") is not False:
            issues.append("code_delivery_report必须声明task_code_executed=false")
        checked = {Path(str(item)).name for item in report.get("checked_configs", [])}
        missing = [config.name for config in configs if config.name not in checked]
        if missing:
            issues.append(f"code_delivery_report未覆盖配置: {missing}")
    return issues


'''
    replace(
        '''def _scope_artifact_issues(
''',
        helper + '''def _scope_artifact_issues(
''',
    )
    replace(
        '''    required = set(stage_requirements(scope, load_yaml(DEFAULT_OUTPUT_CONTRACT_PATH)))
    issues = _formal_state_issues(required, state)
    if "python_code" in required and not any(snapshot.get("code_files") for snapshot in snapshots.values()):
        issues.append("结果交付缺少问题求解Python脚本")
''',
        '''    required = set(stage_requirements(scope, load_yaml(DEFAULT_OUTPUT_CONTRACT_PATH)))
    issues = _formal_state_issues(required, state)
    if required.intersection({"full_run_config", "execution_instructions", "code_delivery_report"}):
        issues.extend(_code_delivery_artifact_issues(root, snapshots))
    elif "python_code" in required and not any(snapshot.get("code_files") for snapshot in snapshots.values()):
        issues.append("正式交付缺少问题求解Python脚本")
''',
    )
    replace(
        '''    if scope not in {"design", "results", "figures", "docx", "latex", "submission"}:
''',
        '''    if scope not in {"design", "code", "results", "figures", "docx", "latex", "submission"}:
''',
    )
    replace(
        '''        choices=["design", "results", "figures", "docx", "latex", "submission"],
''',
        '''        choices=["design", "code", "results", "figures", "docx", "latex", "submission"],
''',
    )
    print("sync_project formal code scope added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
