#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md", "core/hsk_core_policy.md", "core/workflow_router.yaml",
    "core/module_manifest.yaml", "core/output_contract.yaml",
    "modules/01_problem_audit.md", "modules/02_model_design.md",
    "modules/03_solve_validate.md", "modules/04_figure_evidence.md",
    "modules/05_latex_compile_quality.md", "modules/05_writing/docx.md",
    "modules/05_writing/latex.md", "modules/05_writing/ai_cleanup.md",
    "modules/06_review_delivery.md", "templates/code/hsk_pipeline/result_io.py",
    "templates/matlab/hsk_read_result_workbooks.m", "templates/matlab/plot_from_workbook.m",
    "templates/latex/cumcm/cumcmthesis/cumcmthesis.cls",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts"]
BAD = [r"references/hsk_stage_", r"feedback_layer[1-4]", r"data_output/problem", r"data_output/", r"plot_results\("]
errors: list[str] = []
for rel in REQUIRED:
    if not (ROOT / rel).exists(): errors.append(f"missing required: {rel}")
for top in ACTIVE_DIRS:
    for f in (ROOT / top).rglob("*"):
        if not f.is_file() or f.suffix.lower() not in {".md", ".yaml", ".py", ".m"}: continue
        if f.resolve() == Path(__file__).resolve():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for pat in BAD:
            if re.search(pat, text): errors.append(f"obsolete active pattern: {f.relative_to(ROOT)} -> {pat}")
for rel in ["SKILL.md", "README.md", "core/hsk_core_policy.md", "PROJECT_INSTRUCTIONS_HSK_V621.md", "HSK_RUNTIME_ROUTER_V621.md"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "6.2.1" not in text: errors.append(f"version missing in {rel}")
router = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
if "modules/05_latex_compile_quality.md" not in router: errors.append("LaTeX compile module not routed")
if errors:
    print("HSK skill lint failed:")
    for e in sorted(set(errors)): print("-", e)
    sys.exit(1)
print("HSK skill lint passed.")
