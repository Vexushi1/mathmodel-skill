from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one match, found {count}: {old[:100]!r}")
    write(relative, text.replace(old, new, 1))


def ensure_contains(relative: str, token: str) -> None:
    if token not in read(relative):
        raise RuntimeError(f"{relative}: missing required token {token!r}")


# Phase A/B: release-state closure and historical evaluation semantics.
v860 = "docs/v860_model_construction_solution_rationale_evaluation.md"
replace_once(
    v860,
    "本文是 v8.6.0 候选分支的非运行时验收记录，不是新的数学建模 Authority，不是论文句式模板，也不用于作者身份或 AI 使用判断。正式规则仍由 `core/writing_reasoning_contract.yaml`、`modules/02_model_design.md`、`modules/05_writing/paper_writing_protocol.md` 及其既有 consumers 承担。\n",
    "本文保存 v8.6.0 从候选分支到正式 release 的实现/验收证据，不是新的数学建模 Authority，不是论文句式模板，也不用于作者身份或 AI 使用判断。正式规则仍由 `core/writing_reasoning_contract.yaml`、`modules/02_model_design.md`、`modules/05_writing/paper_writing_protocol.md` 及其既有 consumers 承担。候选阶段的失败与待办继续保留为历史快照，但不能覆盖下述 Final Release Status。\n\n"
    "## 0. Final Release Status\n\n"
    "- Document role：v8.6.0 implementation/evaluation record；runtime authority = none。\n"
    "- Release version：`8.6.0`。\n"
    "- Merged PR：#110。\n"
    "- Merge commit：`41373e1a0ce3472df2c5afc15a3f4c0b9db379fa`。\n"
    "- Final PR validation：HSK Skill CI #2383 全矩阵通过后进入合并。\n"
    "- Post-merge validation：`main` 上 HSK Skill CI #2384 对 merge commit 完成并 `success`；generated-metadata verification 同步完成。\n"
    "- Release carriers：正式合并时已同步到 `8.6.0`。\n"
    "- Current verdict for v8.6.0：`released / merged / superseded only by a later release`。\n"
    "- 下文 #2348 等失败记录属于 candidate-stage historical observations，不应解释为当前仓库仍处于 Draft、pending 或未发布状态。\n",
)
replace_once(
    v860,
    "- PR：#110，当前保持 Draft；在全量 CI 与 release-carrier synchronization 完成前不进入合并判定。",
    "- Candidate-stage PR：#110；在本评估快照形成时仍为 Draft，当时要求全量 CI 与 release-carrier synchronization 完成后才进入合并判定。",
)
replace_once(v860, "## 7. 当前 CI 观察", "## 7. Candidate-stage CI 历史观察")
replace_once(
    v860,
    "因此当前状态是：**v8.6 语义/回归问题已从前一轮 16 个失败收敛到 release-carrier synchronization；尚不能宣称 full CI green。**",
    "因此在该候选 head 当时的状态是：**v8.6 语义/回归问题已从前一轮 16 个失败收敛到 release-carrier synchronization；当时尚不能宣称 full CI green。** 该结论只描述 #2348 候选快照；最终 release 状态以第 0 节为准。",
)
replace_once(v860, "## 8. 当前未完成项", "## 8. Candidate-stage 当时未完成项")
replace_once(
    v860,
    "正式把 PR #110 从 Draft 推到 Ready for Review 前仍需：",
    "在该候选阶段，把 PR #110 从 Draft 推到 Ready for Review 前当时仍需：",
)
replace_once(v860, "## 9. 当前结论", "## 9. Candidate-stage 当时结论与最终收口")
replace_once(
    v860,
    "但 release-carrier synchronization 与最终全绿 CI 尚未完成，所以当前 verdict 只能是：\n\n```text\nimplementation_semantics = ready_for_release_sync\nrelease_status = pending\npr_status = draft\nmerge_status = forbidden_until_final_green_ci\n```",
    "但在该候选快照形成时，release-carrier synchronization 与最终全绿 CI 尚未完成，所以**当时的 candidate verdict** 只能是：\n\n```text\nimplementation_semantics = ready_for_release_sync\nrelease_status = pending\npr_status = draft\nmerge_status = forbidden_until_final_green_ci\n```\n\n该历史 verdict 后续已被第 0 节记录的最终事实闭合。v8.6.0 的 release closure 为：\n\n```text\nimplementation_semantics = released\nrelease_status = released\npr_status = merged\nmerge_commit = 41373e1a0ce3472df2c5afc15a3f4c0b9db379fa\npost_merge_ci = HSK Skill CI #2384 success\n```",
)

v850 = "docs/v850_author_reasoning_voice_evaluation.md"
replace_once(
    v850,
    "# v8.5.0 Author Reasoning Voice Evaluation\n",
    "# v8.5.0 Author Reasoning Voice Evaluation\n\n"
    "> Document role：historical implementation/evaluation record；runtime authority = none。  \n"
    "> Evaluated release：v8.5.0。  \n"
    "> Snapshot status：下方 checklist 与 release-decision 文案保留当时验收语境，不代表当前 `main` 仍未发布 v8.5.0。  \n"
    "> Current repository status：v8.5.0 已发布，随后由 v8.6.0 及后续版本取代；当前规则以 active Authority 为准。\n",
)
replace_once(
    v850,
    "最终发布需要结合自动测试、语义审查和 PR review 共同确认。",
    "历史快照中的最终发布判定需要结合当时的自动测试、语义审查和 PR review 共同确认；该句不表示当前仓库仍在等待 v8.5.0 发布。",
)

v840 = "docs/v840_author_reasoning_evaluation.md"
replace_once(
    v840,
    "# v8.4 建模求解叙事：实现、保全与试写记录\n",
    "# v8.4 建模求解叙事：实现、保全与试写记录\n\n"
    "> Document role：historical implementation/evaluation record；runtime authority = none。  \n"
    "> Evaluated release：v8.4.0。  \n"
    "> Snapshot status：本文中的候选 head、当时 CI 与未完成验证只描述 v8.4 发布过程中的历史状态。  \n"
    "> Current repository status：v8.4.0 已发布并已被后续 release 取代；当前规则以 active Authority 为准。\n",
)

# Phase C/F: template-example semantic isolation and A196 provenance boundary.
manifest = "templates/latex/cumcm/hsk/template_manifest.yaml"
replace_once(
    manifest,
    "authority_boundary:\n",
    "reference_semantic_isolation:\n"
    "  a196_role: provenance_and_chapter_topology_only\n"
    "  runtime_writing_semantic_authority: false\n"
    "  runtime_internal_subsection_authority: false\n"
    "  model_or_solver_selection_authority: false\n"
    "  rule: >-\n"
    "    A196/reference materials may explain provenance and chapter topology, but runtime subsection decisions,\n"
    "    model/solver selection and prose semantics remain owned by the active Template/Writing Authorities.\n\n"
    "authority_boundary:\n",
)
replace_once(
    manifest,
    "  default_complex_question_headings:\n    - 模型建立\n    - 模型求解\n    - 求解结果\n    - 结果的分析与验证\n",
    "  default_complex_question_headings:\n    - 模型建立\n    - 模型求解\n    - 求解结果\n    - 结果的分析与验证\n"
    "  default_complex_question_headings_role: maintained_example_profile_only\n"
    "  runtime_internal_heading_policy_authority: core/writing_reasoning_contract.yaml#model_establishment_solution_narrative\n",
)
replace_once(
    manifest,
    "fixed_template_checks:\n  question_example: sections/06_question1.tex\n",
    "fixed_template_checks:\n"
    "  role: maintained_example_smoke_only\n"
    "  runtime_semantic_authority: false\n"
    "  literal_subsection_tokens_apply_to: sections/06_question1.tex\n"
    "  must_not_infer: [runtime_required_headings, fixed_runtime_subsection_count, model_or_solver_choice]\n"
    "  question_example: sections/06_question1.tex\n",
)

template_readme = "templates/latex/cumcm/hsk/README.md"
replace_once(
    template_readme,
    "只吸收结构和表达组织，不复制参考论文的正文、公式、图表、算法、参数或结果。\n",
    "只吸收结构和表达组织，不复制参考论文的正文、公式、图表、算法、参数或结果。A196 及其他 reference 文件只承担 provenance / chapter-topology 参考，不是当前写作语义、模型/solver 选择或问题内部标题的运行时 Authority；相关决策必须回到 active Template Manifest、Writing Reasoning 与 Paper Writing Protocol。\n",
)
replace_once(
    template_readme,
    "复杂问题默认形成：\n\n```text\n模型建立\n→ 模型求解\n→ 求解结果\n→ 结果的分析与验证\n```\n\n这四个名称是 canonical example，不是 Hard 的逐字标题。若题目对象更适合专业标题，例如“遮蔽几何关系建立”“多目标优化求解”“轨迹参数与有效时长结果”“离散精度与参数扰动检验”，可直接替换二级标题。\n",
    "canonical complex-question smoke 示例目前展示：\n\n```text\n模型建立\n→ 模型求解\n→ 求解结果\n→ 结果的分析与验证\n```\n\n这四个名称只属于 maintained example / LaTeX smoke profile，不是 runtime 的逐字标题要求，也不构成固定四小节数量。真正的小节拆分服从 Adaptive Subsection Separation：若题目对象更适合专业标题，例如“遮蔽几何关系建立”“多目标优化求解”“轨迹参数与有效时长结果”“离散精度与参数扰动检验”，可直接替换、合并或增加真实独立任务对应的二/三级标题。\n",
)

# Phase D: named integration pointers without duplicating reasoning semantics.
output = "core/output_contract.yaml"
replace_once(
    output,
    "  optimization_expression_contract: core/writing_reasoning_contract.yaml#optimization_model_expression\n  solver_justification_contract: core/writing_reasoning_contract.yaml#solver_justification\n",
    "  optimization_expression_contract: core/writing_reasoning_contract.yaml#optimization_model_expression\n"
    "  model_construction_rationale_contract: core/writing_reasoning_contract.yaml#model_construction_rationale\n"
    "  numerical_parameter_evidence_contract: core/writing_reasoning_contract.yaml#numerical_parameter_evidence\n"
    "  solver_justification_contract: core/writing_reasoning_contract.yaml#solver_justification\n",
)

# Phase G: raw declarative candidate surface vs effective resolver plan.
runtime_router = "RUNTIME_ROUTER.md"
replace_once(
    runtime_router,
    "机器路由以 `core/workflow_router.yaml` 为唯一事实源。本文件只解释运行时顺序，不复制完整路由表。\n",
    "机器路由以 `core/workflow_router.yaml` 为唯一事实源。本文件只解释运行时顺序，不复制完整路由表。\n\n"
    "## Declarative candidate surface 与 effective resolved plan\n\n"
    "`core/workflow_router.yaml` 的 route `terminal_outputs` 与 `core/module_manifest.yaml` 的 module outputs 描述的是**边界解析前的候选能力/可能产物表面**，不能单独解释为本次调用已经获得这些 current artifacts，更不能据此跳过 Model Approval、条件式预处理或用户执行边界。\n\n"
    "`scripts/resolve_runtime.py`（兼容层为 `scripts/resolve_workflow.py`）返回的 `modules`、`module_terminal_outputs`、`terminal_outputs`、`pause_state` 与 `pre_delivery_gates` 才是当前调用经过 Model Approval / preprocessing / user-execution boundary 后的 **effective plan**。未完成人工锁模时，effective plan 必须停在 `awaiting_model_approval`，raw manifest 中即使列有 `locked_model_spec` 也不构成 current locked artifact 或执行授权。正式 consumer 应消费 resolver 返回计划，而不是直接把 raw route/module output 列表当成已批准结果。\n",
)

# Phase E: make historical release headings machine-readable while v8.6.0 remains current during implementation.
changelog = "CHANGELOG.md"
replace_once(changelog, "## 8.5.0", "## Previous release: 8.5.0")
replace_once(changelog, "## 8.4.0", "## Previous release: 8.4.0")

# Scope-contract status now that implementation was explicitly approved.
plan = "docs/v861_active_consistency_semantic_drift_hardening_plan.md"
replace_once(
    plan,
    "> 状态：计划阶段 / implementation not started  ",
    "> 状态：用户已批准实施 / implementation in progress  ",
)
replace_once(plan, "implementation_started = false", "implementation_started = true")
replace_once(
    plan,
    "在用户明确批准实施前，只保留本计划作为后续上下文参考，不进入 Authority、runtime、template 或 release-carrier 修改。",
    "用户已明确批准实施；后续仍严格按本计划的 patch scope、停止条件与分阶段 release sync 执行。",
)

# New v8.6.1 regression file. It intentionally validates existing resolver behavior rather than changing it.
test_path = ROOT / "tests/test_v861_active_consistency_semantic_drift.py"
if test_path.exists():
    existing = test_path.read_text(encoding="utf-8")
    if "class TestV861ActiveConsistencySemanticDrift" not in existing:
        raise RuntimeError("unexpected pre-existing v8.6.1 test file")
else:
    test_path.write_text(
        '''from __future__ import annotations\n\nimport importlib.util\nimport json\nimport re\nimport sys\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef load_resolver():\n    spec = importlib.util.spec_from_file_location(\n        "resolve_workflow_v861", ROOT / "scripts/resolve_workflow.py"\n    )\n    module = importlib.util.module_from_spec(spec)\n    assert spec.loader is not None\n    sys.modules[spec.name] = module\n    spec.loader.exec_module(module)\n    return module\n\n\nclass TestV861ActiveConsistencySemanticDrift(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))\n        cls.output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))\n        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))\n        cls.manifest = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))\n        cls.resolver = load_resolver()\n\n    def test_v860_evaluation_closes_release_state_without_erasing_candidate_history(self):\n        text = (ROOT / "docs/v860_model_construction_solution_rationale_evaluation.md").read_text(encoding="utf-8")\n        self.assertIn("## 0. Final Release Status", text)\n        self.assertIn("41373e1a0ce3472df2c5afc15a3f4c0b9db379fa", text)\n        self.assertIn("HSK Skill CI #2384", text)\n        self.assertIn("release_status = released", text)\n        self.assertIn("Candidate-stage CI 历史观察", text)\n        self.assertIn("release_status = pending", text)\n        self.assertIn("candidate-stage historical observations", text)\n\n    def test_older_evaluations_are_explicit_historical_non_authorities(self):\n        for relative in (\n            "docs/v840_author_reasoning_evaluation.md",\n            "docs/v850_author_reasoning_voice_evaluation.md",\n        ):\n            text = (ROOT / relative).read_text(encoding="utf-8")\n            self.assertIn("historical implementation/evaluation record", text, relative)\n            self.assertIn("runtime authority = none", text, relative)\n            self.assertIn("Current repository status", text, relative)\n\n    def test_all_release_headings_are_machine_readable(self):\n        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")\n        semver_headings = [\n            line for line in text.splitlines()\n            if re.match(r"^## .*?\\b\\d+\\.\\d+\\.\\d+$", line)\n        ]\n        self.assertGreaterEqual(len(semver_headings), 3)\n        pattern = re.compile(r"^## (Current|Previous) release: (\\d+\\.\\d+\\.\\d+)$")\n        parsed = []\n        for line in semver_headings:\n            match = pattern.match(line)\n            self.assertIsNotNone(match, line)\n            parsed.append(match.groups())\n        self.assertEqual(parsed[0], ("Current", str(self.bootstrap["skill_version"])))\n        versions = [version for _, version in parsed]\n        self.assertEqual(len(versions), len(set(versions)))\n        self.assertTrue(all(kind == "Previous" for kind, _ in parsed[1:]))\n\n    def test_template_fixed_tokens_are_smoke_only_and_runtime_structure_is_adaptive(self):\n        fixed = self.manifest["fixed_template_checks"]\n        self.assertEqual(fixed["role"], "maintained_example_smoke_only")\n        self.assertFalse(fixed["runtime_semantic_authority"])\n        self.assertEqual(fixed["literal_subsection_tokens_apply_to"], "sections/06_question1.tex")\n        self.assertIn("runtime_required_headings", fixed["must_not_infer"])\n        question = self.manifest["cumcm_question_section"]\n        self.assertEqual(question["internal_structure"], "adaptive")\n        self.assertEqual(question["default_complex_question_headings_role"], "maintained_example_profile_only")\n        adaptive = self.reasoning["model_establishment_solution_narrative"]["within_question_subsection_architecture"]["adaptive_separation"]\n        self.assertIn("thin_variable_objective_constraint_fragments", adaptive["merge_when_any"])\n        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])\n\n    def test_a196_is_provenance_not_runtime_model_or_solver_authority(self):\n        isolation = self.manifest["reference_semantic_isolation"]\n        self.assertEqual(isolation["a196_role"], "provenance_and_chapter_topology_only")\n        self.assertFalse(isolation["runtime_writing_semantic_authority"])\n        self.assertFalse(isolation["runtime_internal_subsection_authority"])\n        self.assertFalse(isolation["model_or_solver_selection_authority"])\n        reasoning_text = (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8").lower()\n        router_text = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8").lower()\n        self.assertNotIn("a196", reasoning_text)\n        self.assertNotIn("a196", router_text)\n\n    def test_output_contract_exposes_v86_reasoning_owners_without_copying_rules(self):\n        policy = self.output["writing_policy"]\n        self.assertEqual(\n            policy["model_construction_rationale_contract"],\n            "core/writing_reasoning_contract.yaml#model_construction_rationale",\n        )\n        self.assertEqual(\n            policy["numerical_parameter_evidence_contract"],\n            "core/writing_reasoning_contract.yaml#numerical_parameter_evidence",\n        )\n        self.assertIn("model_construction_rationale", self.reasoning)\n        self.assertIn("numerical_parameter_evidence", self.reasoning)\n\n    def test_runtime_router_distinguishes_raw_candidate_surface_from_effective_plan(self):\n        text = (ROOT / "RUNTIME_ROUTER.md").read_text(encoding="utf-8")\n        self.assertIn("Declarative candidate surface", text)\n        self.assertIn("effective plan", text)\n        self.assertIn("raw manifest", text)\n        self.assertIn("resolver 返回计划", text)\n\n    def test_resolved_boundaries_remain_effective(self):\n        unapproved = self.resolver.resolve_workflow(\n            "full_solution", objective="optimization", preprocessing_decision="not_needed"\n        )\n        self.assertEqual(unapproved["pause_state"], "awaiting_model_approval")\n        self.assertIn("awaiting_model_approval", unapproved["terminal_outputs"])\n        self.assertNotIn("locked_model_spec", unapproved["terminal_outputs"])\n        self.assertNotIn("modules/03_solve_validate.md", unapproved["modules"])\n\n        preprocessing = self.resolver.resolve_workflow(\n            "full_solution",\n            objective="optimization",\n            preprocessing_decision="project_level",\n            available_artifacts=["locked_model_spec"],\n        )\n        self.assertEqual(preprocessing["pause_state"], "awaiting_user_preprocessing")\n        self.assertIn("modules/03_data_preprocessing.md", preprocessing["modules"])\n        self.assertNotIn("modules/03_solve_validate.md", preprocessing["modules"])\n\n        solve = self.resolver.resolve_workflow(\n            "full_solution",\n            objective="optimization",\n            preprocessing_decision="not_needed",\n            available_artifacts=["locked_model_spec"],\n        )\n        self.assertEqual(solve["pause_state"], "awaiting_user_execution")\n        self.assertIn("modules/03_solve_validate.md", solve["modules"])\n        self.assertIn("python_code", solve["terminal_outputs"])\n\n    def test_current_release_carriers_remain_in_sync_during_patch(self):\n        current = str(self.bootstrap["skill_version"])\n        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))\n        self.assertEqual(str(plugin["version"]), current)\n        for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):\n            text = (ROOT / relative).read_text(encoding="utf-8")\n            self.assertRegex(text, rf"(?m)^version:\\s*{re.escape(current)}$")\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )

# Final sanity checks for the transformation script itself.
for relative, token in (
    (v860, "## 0. Final Release Status"),
    (v850, "historical implementation/evaluation record"),
    (v840, "historical implementation/evaluation record"),
    (manifest, "maintained_example_smoke_only"),
    (output, "model_construction_rationale_contract"),
    (runtime_router, "Declarative candidate surface"),
    (changelog, "## Previous release: 8.5.0"),
    (plan, "implementation_started = true"),
):
    ensure_contains(relative, token)

print("v8.6.1 active-consistency patch applied")
