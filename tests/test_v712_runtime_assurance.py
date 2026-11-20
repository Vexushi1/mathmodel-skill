import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from tests import test_solver_backends as solver_fixtures

ROOT = Path(__file__).resolve().parents[1]

SEMANTIC_SCOPE = """#### 当前模型口径
**题意口径合同（Problem Contract）**
- 原始对象：A
- 目标：min f(x)
"""
FRAMEWORK = f"""# 模型论文框架
## 当前有效口径
## 各问模型与结果
### Q1：第一问
{SEMANTIC_SCOPE}#### 结果摘要
待求解。
## 图表证据链
## 待办与缺口
"""


def semantic_hash() -> str:
    normalized = SEMANTIC_SCOPE.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_runtime():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "resolve_runtime", ROOT / "scripts/resolve_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV712RuntimeAssurance(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime()

    def _write_state(self, root: Path, state: dict) -> None:
        path = root / "state"
        path.mkdir(parents=True, exist_ok=True)
        (path / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (root / "模型论文框架.md").write_text(FRAMEWORK, encoding="utf-8")

    def _base_state(self) -> dict:
        current_semantic_hash = semantic_hash()
        return {
            "execution": {"solver_backend": "python",
                          "solver_backend_selection_reason": "Synthetic whole-problem review"},
            "project": {
                "competition": "CUMCM",
                "problem": "A",
                "current_phase": "solve_validate",
                "version": "current",
            },
            "preprocessing": {
                "decision": "not_needed",
                "status": "not_applicable",
            },
            "subproblems": {
                "Q1": {
                    "classification": {
                        "objective": "optimization",
                        "structures": ["stochastic"],
                    },
                    "capabilities": {
                        "has_explicit_constraints": True,
                        "requires_feasibility_check": True,
                        "requires_equilibrium_residual": False,
                        "requires_conservation_residual": False,
                        "requires_discretization_check": False,
                        "requires_convergence_diagnostic": True,
                    },
                    "model_challenge_status": "passed",
                    "human_model_approval_status": "approved",
                    "semantic_revision": 3,
                    "semantic_hash": current_semantic_hash,
                    "approved_semantic_revision": 3,
                    "approved_semantic_hash": current_semantic_hash,
                    "primary_execution_status": "pending",
                    "analysis_execution_status": "pending",
                    "result_quality_status": "pending",
                    "result_analysis_status": "pending",
                }
            },
        }

    def _bind_primary(self, root: Path, state: dict) -> None:
        (root / "问题一求解").mkdir(exist_ok=True)
        fixture = solver_fixtures.SolverBackendTests()
        fixture.root = root
        config = fixture.config("python")
        source = fixture.source(config)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        scripts = str(ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import stage_code
        bundle = stage_code.stage_code_fingerprint(root, source)["bundle_sha256"]
        question = state["subproblems"]["Q1"]
        question.update(code=source.relative_to(root).as_posix(), primary_code_sha256=digest,
                        data_hash=config["data_sha256"], validated_data_hash=config["data_sha256"])
        for field in ("artifact_hashes", "validated_artifact_hashes"):
            question.setdefault(field, {})["data"] = config["data_sha256"]
        question["solver_execution"] = {"primary": {
            "bundle_sha256": bundle, "validated_bundle_sha256": bundle}}
        question.setdefault("artifact_hashes", {})["primary_code"] = digest
        question.setdefault("validated_artifact_hashes", {})["primary_code"] = digest

    def test_default_runtime_adds_assurance_without_breaking_legacy_plan(self):
        plan = self.runtime.resolve_runtime("problem_analysis")
        current_version = yaml.safe_load(
            (ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")
        )["skill_version"]
        self.assertEqual(plan["version"], current_version)
        self.assertIn("runtime_plan", plan)
        self.assertIn("assurance", plan)
        self.assertEqual(plan["assurance"]["status"], "pass")
        self.assertEqual(
            plan["runtime_plan"]["selected_intents"], ["problem_analysis"]
        )
        self.assertEqual(
            plan["assurance"]["intent_resolution"]["mode"], "explicit"
        )

    def test_explicit_intent_is_authoritative_over_request_keywords(self):
        plan = self.runtime.resolve_runtime(
            "problem_analysis", request="请给出完整求解"
        )
        intent = plan["assurance"]["intent_resolution"]
        self.assertEqual(intent["selected_intents"], ["problem_analysis"])
        self.assertTrue(intent["inferred_candidates"])
        self.assertEqual(plan["intents"], ["problem_analysis"])

    def test_inferred_intent_prefers_specific_keyword_phrase(self):
        plan = self.runtime.resolve_runtime(
            request="请审题并建模", objective="optimization"
        )
        intent = plan["assurance"]["intent_resolution"]
        self.assertEqual(intent["selected_intents"], ["new_problem_design"])
        self.assertFalse(intent["ambiguity"])
        candidates = {item["intent"]: item for item in intent["inferred_candidates"]}
        self.assertGreater(
            candidates["new_problem_design"]["score"],
            candidates["problem_analysis"]["score"],
        )

    def test_intent_provenance_reports_true_top_score_ambiguity(self):
        router = {
            "routing": {
                "route_a": {"infer_keywords": ["同词"]},
                "route_b": {"infer_keywords": ["同词"]},
            }
        }
        selected, diagnostics = self.runtime.resolve_intent_assurance(
            [], "同词", router
        )
        self.assertEqual(selected, ["route_a", "route_b"])
        self.assertTrue(diagnostics["ambiguity"])
        self.assertEqual(diagnostics["confidence_band"], "low")

    def test_module_contract_dependency_closure_is_additive(self):
        plan = self.runtime.resolve_runtime("figures")
        closure = plan["assurance"]["dependency_closure"]
        self.assertIn("workbook", closure["required_aliases"])
        self.assertIn("core/workbook_schema.yaml", plan["contracts"])
        self.assertIn("core/workbook_schema.yaml", plan["load_order"])
        self.assertIn("core/workbook_schema.yaml", closure["added_paths"])

    def test_project_state_hydrates_classification_approval_and_preprocessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_state(root, self._base_state())
            plan = self.runtime.resolve_runtime(
                "full_solution", project_root=root, question="Q1"
            )
        self.assertEqual(plan["competition"], "CUMCM")
        self.assertEqual(plan["preprocessing_decision"], "not_needed")
        self.assertEqual(plan["classification"]["objective"], "optimization")
        self.assertIn("packs/task/optimization.md", plan["packs"])
        self.assertTrue(plan["pause_for_model_approval"])
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")
        self.assertIn("modules/02_model_design.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        assurance = plan["assurance"]
        self.assertTrue(assurance["context"]["project_state_loaded"])
        self.assertNotIn(
            "locked_model_spec",
            assurance["artifact_assurance"]["effective_artifacts"],
        )
        row = next(
            item
            for item in assurance["artifact_assurance"]["evidence"]
            if item["artifact"] == "locked_model_spec"
        )
        self.assertEqual(row["status"], "legacy_review_required")
        self.assertEqual(row["source"], "framework+project_state")
        self.assertEqual(row["path"], "模型论文框架.md")
        self.assertEqual(row["expected_sha256"], semantic_hash())
        self.assertEqual(row["actual_sha256"], semantic_hash())

    def test_missing_current_framework_never_verifies_locked_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_state(root, self._base_state())
            (root / "模型论文框架.md").unlink()
            plan = self.runtime.resolve_runtime(
                "full_solution", project_root=root, question="Q1"
            )
        assurance = plan["assurance"]
        row = next(
            item
            for item in assurance["artifact_assurance"]["evidence"]
            if item["artifact"] == "locked_model_spec"
        )
        self.assertEqual(row["status"], "missing")
        self.assertNotIn(
            "locked_model_spec",
            assurance["artifact_assurance"]["effective_artifacts"],
        )

    def test_verified_primary_workbook_allows_result_analysis_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解结果.xlsx"
            workbook.write_bytes(b"verified-workbook")
            digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
            state = self._base_state()
            self._bind_primary(root, state)
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": workbook.name,
                    "artifact_hashes": {**q1["artifact_hashes"], "solution_workbook": digest},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis", project_root=root, question="Q1"
            )
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn(
            "accepted_solution_workbook",
            plan["assurance"]["artifact_assurance"]["effective_artifacts"],
        )

    def test_known_hash_mismatch_blocks_legacy_artifact_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解结果.xlsx"
            workbook.write_bytes(b"actual")
            state = self._base_state()
            self._bind_primary(root, state)
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": workbook.name,
                    "artifact_hashes": {**q1["artifact_hashes"], "solution_workbook": "b" * 64},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis",
                project_root=root,
                question="Q1",
                available_artifacts=["accepted_solution_workbook"],
            )
        assurance = plan["assurance"]
        self.assertEqual(assurance["status"], "review_required")
        self.assertTrue(assurance["artifact_assurance"]["conflicts"])
        self.assertNotIn(
            "accepted_solution_workbook",
            assurance["artifact_assurance"]["effective_artifacts"],
        )
        self.assertIn("modules/02_model_design.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")

    def test_artifact_path_outside_project_root_is_never_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            root.mkdir()
            outside = base / "outside.xlsx"
            outside.write_bytes(b"outside")
            digest = hashlib.sha256(outside.read_bytes()).hexdigest()
            state = self._base_state()
            self._bind_primary(root, state)
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": "../outside.xlsx",
                    "artifact_hashes": {**q1["artifact_hashes"], "solution_workbook": digest},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis", project_root=root, question="Q1"
            )
        evidence = plan["assurance"]["artifact_assurance"]["evidence"]
        row = next(
            item
            for item in evidence
            if item["artifact"] == "accepted_solution_workbook"
            and item["scope"] == "Q1"
        )
        self.assertEqual(row["status"], "outside_project_root")
        self.assertNotIn(
            "accepted_solution_workbook",
            plan["assurance"]["artifact_assurance"]["effective_artifacts"],
        )
        self.assertIn("modules/02_model_design.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")


class CurrentDependencyApprovalTests(unittest.TestCase):
    def setUp(self):
        from tests.test_v900_semantic_governance import SEMANTIC, dependency_project

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = dependency_project(self.root)
        self.frame = self.root / "模型论文框架.md"
        report = SEMANTIC.validate_project(self.root, write=True, strict=True)
        self.assertEqual(report["status"], "passed", report["issues"])
        self.state = yaml.safe_load(self.path.read_bytes())
        self.entries = self.state["subproblems"]
        for entry in self.entries.values():
            entry.update(model_challenge_status="passed", human_model_approval_status="approved",
                         approved_semantic_revision=entry["validated_semantic_revision"],
                         approved_semantic_identity_hash=entry["validated_semantic_identity_hash"])

    def check_locks(self, blocked):
        from runtime_assurance import hydrate_project_context
        from validate_model_approval import validate_state

        self.path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        before = self.path.read_bytes()
        rows = hydrate_project_context(self.root)["artifact_evidence"]
        locks = {row["scope"]: row for row in rows if row["artifact"] == "locked_model_spec"}
        self.assertEqual({q for q, row in locks.items() if row["status"] != "verified"}, set(blocked), locks)
        for q in self.entries:
            errors = validate_state(self.path, [q], project_root=self.root)
            self.assertEqual(bool(errors), q in blocked, (q, errors))
        self.assertEqual(self.path.read_bytes(), before)
        return locks

    def test_dependency_mismatch_blocks_only_its_model_chain_at_read_time(self):
        self.check_locks([])
        target = self.entries["Q2"]
        for bad_edges in ([], [{"question": "Q1", "kind": "result"}], 7):
            with self.subTest(depends_on=bad_edges):
                target["depends_on"] = bad_edges
                locks = self.check_locks(["Q2", "Q3"])
                for q in ("Q2", "Q3"):
                    self.assertIn("Q2", locks[q]["reason"])
                    self.assertIn("Q1/model" if isinstance(bad_edges, list) else "depends_on", locks[q]["reason"])
        target["depends_on"] = ["Q1"]
        self.check_locks([])

    def test_scoped_resolver_waits_for_dependent_approval_only(self):
        self.entries["Q2"]["depends_on"] = []
        self.path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        runtime = load_runtime()
        for question, paused in (("Q3", True), ("Q4", False)):
            plan = runtime.resolve_runtime("full_solution", project_root=self.root, question=question)
            self.assertEqual(plan["pause_for_model_approval"], paused)
            effective = plan["assurance"]["artifact_assurance"]["effective_artifacts"]
            self.assertEqual("locked_model_spec" in effective, not paused)

    def test_unsynchronized_revision_or_identity_invalidates_only_model_approval_edges(self):
        q1 = self.entries["Q1"]
        for current, validated in ((2, 1), (1, 2)):
            with self.subTest(current=current, validated=validated):
                q1.update(semantic_revision=current, validated_semantic_revision=validated,
                          approved_semantic_revision=current)
                locks = self.check_locks(["Q1", "Q2", "Q3"])
                self.assertIn("validated_semantic_revision", locks["Q3"]["reason"])
        del q1["semantic_revision"]
        self.check_locks(["Q1", "Q2", "Q3"])
        q1.update(semantic_revision=1, validated_semantic_revision=1, approved_semantic_revision=1)
        framework = self.frame.read_text(encoding="utf-8")
        self.frame.write_text(framework.replace("当前模型说明", "新排版说明"), encoding="utf-8")
        self.check_locks([])
        self.frame.write_text(framework.replace("sense: minimize", "sense: maximize", 1), encoding="utf-8")
        self.check_locks(["Q1", "Q2", "Q3"])

    def test_old_writer_advanced_validation_while_leaving_the_previous_approval(self):
        entry = self.entries["Q1"]
        entry.update(semantic_revision=2, validated_semantic_revision=2, approved_semantic_revision=1)
        self.check_locks(["Q1", "Q2", "Q3"])
        entry.update(approved_semantic_revision=2, approved_semantic_identity_hash="0" * 64)
        self.check_locks(["Q1", "Q2", "Q3"])

    def test_established_upstream_sib_cannot_disappear_before_a_downstream_read(self):
        from tests.test_v900_semantic_governance import framework

        text = self.frame.read_text(encoding="utf-8")
        tail = text[text.index("### Q2："):]
        for remaining in (framework(None) + tail, tail):
            with self.subTest(first_line=remaining.splitlines()[0]):
                self.frame.write_text(remaining, encoding="utf-8")
                self.check_locks(["Q1", "Q2", "Q3"])
        self.frame.unlink()
        self.check_locks(self.entries)


if __name__ == "__main__":
    unittest.main()
