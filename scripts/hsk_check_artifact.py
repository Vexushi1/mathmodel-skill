#!/usr/bin/env python3
"""Check HSK v6.2.1 project structure and Python/MATLAB ownership."""
from __future__ import annotations
import argparse, re
from pathlib import Path

CN_NUM = "一二三四五六七八九十"
FIG_EXT = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff"}
PY_PLOT_TOKENS = ("matplotlib", "seaborn", "savefig(", "plt.show(")


def check_code(root: Path) -> list[str]:
    issues: list[str] = []
    py_dir, m_dir = root / "Python求解", root / "MATLAB绘图"
    if not py_dir.exists(): issues.append("missing: Python求解/")
    if not m_dir.exists(): issues.append("missing: MATLAB绘图/")
    for f in py_dir.rglob("*.py") if py_dir.exists() else []:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if any(token in text for token in PY_PLOT_TOKENS):
            issues.append(f"Python formal-plot ownership violation: {f.relative_to(root)}")
        if "if __name__" not in text and any(k in f.stem for k in ("求解", "敏感性", "鲁棒性")):
            issues.append(f"Python main script lacks entry point: {f.relative_to(root)}")
    return issues


def check_results(root: Path) -> list[str]:
    issues: list[str] = []
    base = root / "结果数据表"
    if not base.exists(): return ["missing: 结果数据表/"]
    questions = [p for p in base.iterdir() if p.is_dir() and re.fullmatch(rf"问题[{CN_NUM}]+", p.name)]
    if not questions: return ["missing: no 结果数据表/问题X/ directories"]
    for q in questions:
        d = q / f"{q.name}结果数据"
        if not d.exists():
            issues.append(f"missing: {d.relative_to(root)}"); continue
        for filename in (f"{q.name}求解结果.xlsx", f"{q.name}敏感性与鲁棒性结果.xlsx"):
            if not (d / filename).is_file(): issues.append(f"missing: {(d/filename).relative_to(root)}")
    return issues


def check_figures(root: Path) -> list[str]:
    issues: list[str] = []
    for dirname in ("figures", "figures_editable"):
        d = root / dirname
        if not d.exists(): continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in FIG_EXT and any(ord(c) >= 128 for c in f.name):
                issues.append(f"figure filename should be ASCII: {f.relative_to(root)}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--mode", choices=["full", "code", "data", "figures"], default="full")
    a = ap.parse_args(); root = Path(a.project).resolve(); issues: list[str] = []
    if a.mode in {"full", "code"}: issues += check_code(root)
    if a.mode in {"full", "data"}: issues += check_results(root)
    if a.mode in {"full", "figures"}: issues += check_figures(root)
    if issues:
        print("HSK artifact check: ISSUES FOUND")
        for item in issues: print("-", item)
        return 1
    print("HSK artifact check: PASS"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
