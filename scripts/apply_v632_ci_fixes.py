#!/usr/bin/env python3
"""Apply deterministic v6.3.2 CI and scope-semantic fixes, then remove this helper."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"target block not found: {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


validator = ROOT / "templates/code/hsk_pipeline/workbook_validation.py"
replace_once(
    validator,
    '''        required_sheets.update(_conditional_required_sheets(schema, problem_types, capabilities))
        missing = sorted(required_sheets - names)
        if missing:
            raise ValueError(f"求解工作簿缺少必需工作表: {missing}")
''',
    '''        conditional = _conditional_required_sheets(schema, problem_types, capabilities)
        required_sheets.update(conditional)
        missing = sorted(required_sheets - names)
        if missing:
            active_capabilities = sorted(
                name for name, enabled in (capabilities or {}).items() if enabled
            )
            capability_note = (
                f"；启用的capabilities: {active_capabilities}" if active_capabilities else ""
            )
            raise ValueError(f"求解工作簿缺少必需工作表: {missing}{capability_note}")
''',
)

test_v631 = ROOT / "tests/test_v631_contract_closure.py"
replace_once(
    test_v631,
    '''        tables = {
            "核心指标": pd.DataFrame({"指标": ["目标"], "数值": [1.0]}),
            "数据审计": pd.DataFrame({"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}),
        }
        with self.assertRaisesRegex(ValueError, "structure:network"):
''',
    '''        tables = {
            "核心指标": pd.DataFrame({"指标": ["目标"], "数值": [1.0]}),
            "数据审计": pd.DataFrame({"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}),
            "推荐方案": pd.DataFrame({"方案": ["A"]}),
        }
        with self.assertRaisesRegex(ValueError, "structure:network"):
''',
)

lint = ROOT / "scripts/lint_skill.py"
replace_once(
    lint,
    'VERSION_DOCS = ["SKILL.md", "README.md", "REPOSITORY_INDEX.md", "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V630.md"]',
    'VERSION_DOCS = ["SKILL.md", "README.md", "REPOSITORY_INDEX.md", "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V632.md"]',
)

sync = ROOT / "scripts/sync_project.py"
replace_once(
    sync,
    '''    if SCOPE_RANK[scope] >= SCOPE_RANK["docx"]:
        issues.extend(_approved_figure_issues(root, state))
        docx_files = _docx_artifacts(root)
        discovered["docx"] = [path.relative_to(root).as_posix() for path in docx_files]
        if not docx_files:
            issues.append("DOCX交付缺少draft_docx/*.docx")
    if SCOPE_RANK[scope] >= SCOPE_RANK["latex"]:
''',
    '''    if scope == "docx":
        issues.extend(_approved_figure_issues(root, state))
        docx_files = _docx_artifacts(root)
        discovered["docx"] = [path.relative_to(root).as_posix() for path in docx_files]
        if not docx_files:
            issues.append("DOCX交付缺少draft_docx/*.docx")
    if SCOPE_RANK[scope] >= SCOPE_RANK["latex"]:
        issues.extend(_approved_figure_issues(root, state))
''',
)
replace_once(
    sync,
    '''    if status and status not in {"passed", "pass", "success", "completed"}:
        issues.append(f"compile_report状态不是通过: {status}")
''',
    '''    if status not in {"passed", "pass", "success", "completed"}:
        issues.append(f"compile_report状态不是通过: {status or '<empty>'}")
''',
)

test_v632 = ROOT / "tests/test_v632_delivery_gate_closure.py"
replace_once(
    test_v632,
    '''            self.assertIn("draft_docx", joined)
            self.assertIn("final_latex/main.tex", joined)
''',
    '''            self.assertNotIn("draft_docx", joined)
            self.assertIn("final_latex/main.tex", joined)
''',
)
