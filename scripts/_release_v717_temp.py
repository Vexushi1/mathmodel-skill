from pathlib import Path


def replace_exact(path, old, new, expected=1):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    found = text.count(old)
    if found != expected:
        raise SystemExit(
            f"{path}: expected {expected} occurrence(s) of {old!r}, found {found}"
        )
    p.write_text(text.replace(old, new), encoding="utf-8")


replace_exact("core/bootstrap.yaml", "skill_version: 7.16.0", "skill_version: 7.17.0")
replace_exact(
    ".codex-plugin/plugin.json",
    '"version": "7.16.0"',
    '"version": "7.17.0"',
)
replace_exact("core/output_contract.yaml", "version: 7.16.0", "version: 7.17.0")
replace_exact("core/module_manifest.yaml", "version: 7.16.0", "version: 7.17.0")
replace_exact("core/workflow_router.yaml", "version: 7.16.0", "version: 7.17.0")
replace_exact(
    "core/hsk_core_policy.md",
    "# HSK Core Policy v7.16.0",
    "# HSK Core Policy v7.17.0",
)

skill_summary_old = (
    "explicit Human Model Approval bound to the current semantic revision/hash, "
    "evidence-driven conditional preprocessing"
)
skill_summary_new = (
    "explicit Human Model Approval bound to the current semantic revision/hash, "
    "mechanism/geometry structural-validity closure with Predicate Closure, Event Topology, "
    "Reduction Provenance, Solver Applicability, multi-resource composition and original-model "
    "reevaluation, evidence-driven conditional preprocessing"
)
skill_flow_old = (
    "随后锁定 `preprocessing_decision`，再完成题面—数学—代码—输出语义闭环和 Complexity Sanity Check；"
)
skill_flow_new = (
    "随后锁定 `preprocessing_decision`，再完成题面—数学—代码—输出语义闭环，并按需完成机理/几何结构有效性闭合和 Complexity Sanity Check；"
)
for skill in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace_exact(skill, "version: 7.16.0", "version: 7.17.0")
    replace_exact(
        skill,
        "# HSK 数学建模模块化工作流 v7.16.0",
        "# HSK 数学建模模块化工作流 v7.17.0",
    )
    replace_exact(skill, skill_summary_old, skill_summary_new)
    replace_exact(skill, skill_flow_old, skill_flow_new)

health = Path("tests/test_v7141_skill_health.py")
health_text = health.read_text(encoding="utf-8")
if health_text.count("7.16.0") != 5:
    raise SystemExit(
        "tests/test_v7141_skill_health.py: expected 5 current-release literals, "
        f"found {health_text.count('7.16.0')}"
    )
health.write_text(health_text.replace("7.16.0", "7.17.0"), encoding="utf-8")

readme_release = """## v7.17.0：Mechanism Structural Validity Hardening

本版本面向机理、几何、连续事件与混合优化题补强 Solver 之前最容易被忽略的结构层，同时保持现有 Problem Contract、Model Challenge、Human Approval、03A/03B、Workbook Schema、Project State 和用户 full-fidelity 执行边界不变。

- Module 02 新增按需 **Predicate Closure**：明确 physical event、object domain / active-visible subset、reference frame、exact predicate、quantifier order，以及 line/ray/segment/surface/volume 的真实语义；独立等价判据可用于实现交叉复核，但数值一致不能替代数学等价证明。
- 新增 **Event Topology / Boundary** 协议：连续事件允许由多个区间组成；二分、牛顿或局部搜索必须给出有效 bracket、局部结构、端点更新、容差与 fallback，禁止把全局 `0→1→0` 事件直接当成单调区间二分。
- 新增 **Reduction Provenance**：结构缩域明确区分 `exact / proven_sufficient / heuristic`。heuristic 缩域必须记录弃置域检查与真实 claim scope，有限采样未发现反例不能升级成全域证明。
- 新增 **Solver Applicability / Objective Landscape**：先从平滑性、凸性、可行域稀疏、平台、事件跳变、维数和单次评价成本解释 Solver 适配；必要的 empirical probe 必须作为 Human Approval 后的预先定义条件分支，禁止跨赛题固定阈值和 post-hoc 判据。
- 新增 **Multi-resource Composition**：显式区分 `sum / union / intersection / max / min / forall-exists / exists-forall / custom`，避免把并集写成简单时长相加、把 `∀x∃i` 错写成 `∃i∀x` 或把真实协同错误解耦。
- 新增 **Surrogate / Decomposition → Original Model Reevaluation**：由 surrogate、pairwise capability、relaxation 或分解得到的最终候选必须回到原始目标函数和全部原始硬约束重新计算，surrogate score 不得冒充 headline result。
- mechanism / optimization Task Pack 明确 03A 只承担当前 locked model 的内在有效性；参数敏感性、压力场景、替代模型/算法、多 seed / 多初值 claim stability 与更广失效边界继续属于 accepted 后的 03B。
- `模型论文框架.md` 继续使用 `v0.8-project-memory`，只增加按需结构有效性事实与 evidence anchor，不新增 Schema、Gate、项目级报告或 taxonomy capability。
- 新增 v7.17 回归测试，锁定 Shared Foundation、Model Approval、Numerical Verification、PQS 和 03A/03B 单一 Authority 边界，防止后续 architecture creep。

"""
replace_exact("README.md", "# mathmodel-skill v7.16.0", "# mathmodel-skill v7.17.0")
replace_exact(
    "README.md",
    "语义闭环与复杂度复审",
    "语义闭环 + 按需机理/几何结构有效性闭合 + 复杂度复审",
)
replace_exact(
    "README.md",
    "## v7.16.0：Paper Writing Specification & Model Expression Closure\n\n",
    readme_release + "## v7.16.0：Paper Writing Specification & Model Expression Closure\n\n",
)

changelog_release = """## Current release: 7.17.0

- Added conditional **Mechanism / Geometry Structural Validity** closure inside Module 02 without introducing a new lifecycle gate, project-state field or task-taxonomy capability.
- Added **Predicate Closure** for object domain, active/visible subset, reference frame, exact predicate, quantifier order and line/ray/segment/surface/volume semantics; independent equivalent predicates may cross-check implementations but do not replace proof.
- Added **Event Topology / Boundary** requirements for multi-interval events, valid local brackets, endpoint update rules, tolerances and fallback logic; global bisection is rejected when event state can follow `0→1→0` or otherwise switch non-monotonically.
- Added **Reduction Provenance** with `exact / proven_sufficient / heuristic`. Heuristic reductions must retain discarded-domain audit evidence and calibrated claim scope instead of being presented as full-domain proof.
- Added **Solver Applicability / Objective Landscape** reasoning and approval-bound conditional probes. Solver families must be justified from actual mathematical/landscape structure; cross-problem fixed numeric switch thresholds and post-hoc criteria are forbidden.
- Added explicit **Multi-resource Composition** semantics, including `forall-exists` versus `exists-forall`, to prevent invalid simple summation, overlap handling and hidden-coupling removal.
- Added **Surrogate / Decomposition → Original Model Reevaluation** so final candidates return to the original objective and all original hard constraints before headline results are accepted.
- Clarified the mechanism/optimization 03A/03B boundary: current locked-model intrinsic validity remains in 03A, while parameter sensitivity, stress scenarios, alternative models/algorithms, multi-seed or multi-initial-value claim stability and broader failure-boundary exploration remain post-acceptance 03B.
- Extended the existing `v0.8-project-memory` framework with optional structural-validity facts and evidence anchors only; no framework schema migration, new project report, workbook migration or CLI migration was introduced.
- Added v7.17 regression coverage for structural validity and authority boundaries while preserving the existing Problem Contract, Model Challenge/Human Approval, Numerical Verification/PQS authority, Project State, Workbook Schema, per-question five-file layout and user-owned full-fidelity execution.

## Previous release: 7.16.0

"""
replace_exact(
    "CHANGELOG.md",
    "## Current release: 7.16.0\n\n",
    changelog_release,
)

plan_old = (
    "  - core/workflow_router.yaml\n"
    "  - core/module_manifest.yaml\n"
)
plan_new = (
    "  - core/workflow_router.yaml（语义冻结；Phase 6 仅允许顶层 version carrier 从 7.16.0 同步为 7.17.0）\n"
    "  - core/module_manifest.yaml（语义冻结；Phase 6 仅允许顶层 version carrier 从 7.16.0 同步为 7.17.0）\n"
)
replace_exact("docs/mechanism-structural-validity-hardening-plan.md", plan_old, plan_new)

root_skill = Path("SKILL.md").read_bytes()
packaged_skill = Path("skills/mathmodel-skill/SKILL.md").read_bytes()
if root_skill != packaged_skill:
    raise SystemExit("root/package SKILL parity failed after release transformation")
