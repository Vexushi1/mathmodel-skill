import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV717MechanismStructuralValidity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        cls.mechanism = (ROOT / "packs/task/mechanism.md").read_text(encoding="utf-8")
        cls.optimization = (ROOT / "packs/task/optimization.md").read_text(encoding="utf-8")
        cls.algorithm = (ROOT / "packs/artifact/algorithm_flow.md").read_text(encoding="utf-8")
        cls.framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        cls.taxonomy = (ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8")
        cls.numerical = (ROOT / "core/numerical_verification_contract.yaml").read_text(encoding="utf-8")
        cls.approval = (ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8")

    def test_module02_owns_conditional_structural_validity_without_new_gate(self):
        for token in (
            "### 4.8 机理/几何结构有效性（按需）",
            "Predicate Closure",
            "Event Topology / Boundary",
            "Reduction Provenance",
            "exact",
            "proven_sufficient",
            "heuristic",
            "solver applicability probe",
            "Multi-resource Composition",
            "exists-forall",
            "Surrogate / Decomposition",
            "original-model reevaluation",
            "数值一致不能替代等价性证明",
        ):
            self.assertIn(token, self.module)
        self.assertIn("本节不是新的生命周期 Gate", self.module)
        self.assertNotIn("G1.5", self.module)
        self.assertNotIn("Mechanism Gate", self.module)

    def test_existing_shared_foundation_remains_the_cross_question_authority(self):
        self.assertIn("### 4.2 共享基础与跨问增量", self.module)
        self.assertIn("writing_reasoning_contract.shared_foundation", self.module)
        self.assertIn("cross_question_progression", self.module)
        self.assertNotIn("mechanism shared kernel gate", self.module.lower())
        self.assertFalse((ROOT / "packs/task/mechanism_shared_kernel.md").exists())
        self.assertFalse((ROOT / "modules/mechanism_shared_kernel.md").exists())

    def test_mechanism_pack_closes_predicates_events_reduction_and_stage_boundary(self):
        for token in (
            "精确物理/几何判据闭合",
            "line / ray / segment",
            "量词顺序",
            "active or visible",
            "### 活动边界、临界集合与缩域依据",
            "exact",
            "proven_sufficient",
            "heuristic",
            "弃置域",
            "0→1→0",
            "bracket",
            "forall-exists",
            "exists-forall",
            "### 03A：当前主计算的内在有效性",
            "### 03B：accepted 后的结论深化",
        ):
            self.assertIn(token, self.mechanism)
        self.assertIn("参数敏感性", self.mechanism)
        self.assertIn("只在主工作簿 accepted 后进入 Module 03B", self.mechanism)
        self.assertIn("不能把 heuristic 提升为证明", self.mechanism)
        self.assertIn("与当前 locked model 同语义下", self.mechanism)
        self.assertIn("不得在 03A 借此引入替代模型/结构比较", self.mechanism)

    def test_optimization_pack_tracks_reduction_solver_and_original_model(self):
        for token in (
            "### 结构缩域的证据等级",
            "exact",
            "proven_sufficient",
            "heuristic",
            "弃置域",
            "Solver Applicability / Objective Landscape",
            "solver applicability probe",
            "### Surrogate / decomposition 与原模型回算",
            "final original-model reevaluation",
            "### 03A：当前主计算的内在有效性",
            "### 03B：accepted 后的结论深化",
        ):
            self.assertIn(token, self.optimization)
        self.assertIn("不得在 Human Approval 前由助手运行题目专属代码", self.optimization)
        self.assertIn("不能把 surrogate objective 直接当作原问题最终目标值", self.optimization)
        self.assertIn("不得设置跨赛题通用的固定比例、维数或目标阈值", self.optimization)
        self.assertIn("post-hoc 调整判据", self.optimization)
        self.assertIn("不因本 Pack 自动新增主质量门", self.optimization)

    def test_authority_boundaries_are_consumed_not_redefined(self):
        self.assertIn("explicit Human Model Approval gate", self.approval)
        self.assertIn("hidden_coupling_or_invalid_decoupling", self.approval)
        self.assertIn("local_property_misstated_as_global", self.approval)
        normalized_numerical = " ".join(self.numerical.split())
        self.assertIn(
            "single field-level authority for intrinsic numerical validity",
            normalized_numerical,
        )
        self.assertIn(
            "result analysis after the primary workbook is accepted",
            normalized_numerical,
        )
        for token in (
            "requires_equivalent_predicate_check",
            "requires_event_topology_check",
            "requires_objective_landscape_probe",
        ):
            self.assertNotIn(token, self.taxonomy)
            self.assertNotIn(token, self.numerical)
            self.assertNotIn(token, self.approval)

    def test_algorithm_flow_consumes_but_does_not_redefine_model_authority(self):
        self.assertIn("modules/02_model_design.md", self.algorithm)
        for token in (
            "exact / proven_sufficient / heuristic",
            "局部 bracket",
            "端点更新",
            "solver applicability probe",
            "original-model reevaluation",
        ):
            self.assertIn(token, self.algorithm)
        self.assertIn("本 Pack 只消费 current 语义", self.algorithm)

    def test_framework_persists_only_current_project_structural_facts(self):
        for token in (
            "**机理/几何结构有效性（按需；不适用时写 not_applicable）**",
            "Object domain 与 active / visible subset",
            "Event topology",
            "Reduction provenance",
            "Multi-resource composition",
            "Solver applicability",
            "original-model reevaluation",
            "heuristic 弃置域",
        ):
            self.assertIn(token, self.framework)
        self.assertIn("框架版本：`v0.8-project-memory`", self.framework)
        self.assertNotIn("MECHANISM_REVIEW.md", self.framework)

    def test_first_round_does_not_expand_taxonomy_or_numerical_schema(self):
        forbidden_capabilities = (
            "requires_equivalent_predicate_check",
            "requires_event_topology_check",
            "requires_objective_landscape_probe",
        )
        for token in forbidden_capabilities:
            self.assertNotIn(token, self.taxonomy)
            self.assertNotIn(token, self.numerical)

    def test_solver_probe_has_no_universal_numeric_switch_thresholds(self):
        combined = self.module + "\n" + self.optimization
        for forbidden in (
            "rho_plus <",
            "rho+ <",
            "rho_g <",
            "维数 > 20",
            "0.05 → DE",
            "0.10 → GA",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("不能只因为决策变量连续就默认局部梯度 NLP 适用", self.module)
        self.assertIn("不得在 Human Approval 前由助手运行题目专属代码", self.optimization)

    def test_no_new_standalone_mechanism_architecture_is_introduced(self):
        for relative in (
            "MECHANISM_REVIEW.md",
            "MECHANISM_STRUCTURE.md",
            "mechanism_structure.yaml",
            "state/mechanism_structure.yaml",
            "packs/task/mechanism_structure_reducer.md",
            "modules/mechanism_structure_reducer.md",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()