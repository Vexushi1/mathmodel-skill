from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "docs/v861_active_consistency_semantic_drift_hardening_plan.md"
text = path.read_text(encoding="utf-8")

replacements = {
    "> 状态：实现与版本同步完成 / final release CI pending  ":
        "> 状态：实现与版本同步完成；最终 PR-head CI 必须全绿后才可 Ready/merge  ",
    "> 当前文件只作为后续实施上下文与 Scope Contract；除本计划文档外，本轮尚未修改任何 active runtime / Authority / template / test。  ":
        "> 本文件保留为本轮 Scope Contract；F1–F7 已在独立分支实施，未越过既定 non-goal 与 runtime 行为边界。  ",
    "> 目标版本：若用户批准实施，预计发布为 **v8.6.1 patch**；在正式实施前仍保持仓库 release carriers 为 v8.6.0。":
        "> 目标版本：**v8.6.1 patch**；当前分支 release carriers 已统一为 v8.6.1，尚未合并 `main`。",
    "final_release_ci = pending":
        "final_release_ci = must_be_green_on_current_pr_head_before_ready_or_merge",
}

for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match for {old!r}, got {count}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("v8.6.1 plan status finalized for PR-head verification")
