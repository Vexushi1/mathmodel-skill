from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from tests.test_sync_project import load_syncer, setup_project
from tests.test_v712_runtime_assurance import load_runtime
from tests.test_v900_semantic_governance import (
    SEMANTIC,
    base_state,
    framework,
    identity_payload,
    write_project,
)
from tests.test_v900_state_transitions import CONTRACT as STATE_TRANSITION_CONTRACT
from tests.test_v900_state_transitions import TRANSITIONS

CASE = yaml.safe_load(
    (ROOT / "tests/fixtures/question_runtime_three_question.yaml").read_text(encoding="utf-8")
)


def build_three_question_project(root: Path) -> tuple[Path, Path]:
    """Create a synthetic, SIB-backed Q1/Q2/Q3 project using existing test authorities."""
    state = base_state()
    prototype = deepcopy(state["subproblems"]["Q1"])
    state["subproblems"] = {}
    sections: list[str] = []

    for question, specification in CASE["questions"].items():
        dependencies = deepcopy(specification["depends_on"])
        entry = deepcopy(prototype)
        entry["classification"] = {
            "objective": specification["objective"],
            "structures": list(specification["structures"]),
        }
        entry["capabilities"] = {}
        entry["depends_on"] = dependencies
        entry["framework_section"] = f"### {question}：第一问"
        state["subproblems"][question] = entry

        payload = identity_payload()
        payload["question"] = question
        payload["dependencies"] = dependencies
        section = framework(payload, question=question).split(
            "## 各问模型与结果\n", 1
        )[1]
        sections.append(section)

    state["project"] = {
        "competition": "CUMCM",
        "problem": "A",
        "current_phase": "solve_validate",
    }
    state["execution"] = {
        "solver_backend": "python",
        "solver_backend_selection_reason": "fixed three-question integration fixture",
    }
    state["preprocessing"] = {"decision": "not_needed", "status": "not_applicable"}
    framework_text = "# 模型论文框架\n## 各问模型与结果\n" + "\n".join(sections)
    state_path = write_project(root, state, framework_text)
    framework_path = root / "模型论文框架.md"

    report = SEMANTIC.validate_project(root, write=True, strict=True)
    if report["status"] != "passed":
        raise AssertionError(f"synthetic semantic fixture did not validate: {report}")

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    for entry in state["subproblems"].values():
        entry.update(
            model_challenge_status="passed",
            human_model_approval_status="approved",
            approved_semantic_revision=entry["validated_semantic_revision"],
            approved_semantic_identity_hash=entry["validated_semantic_identity_hash"],
        )
    state_path.write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return state_path, framework_path


def add_unfinished_questions_to_sync_project(root: Path) -> None:
    state_path = root / "state" / "project_state.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    prototype = state["subproblems"]["Q1"]

    for question in ("Q2", "Q3"):
        specification = CASE["questions"][question]
        entry = deepcopy(prototype)
        for field in (
            "code",
            "primary_code_sha256",
            "solver_execution",
            "solution_workbook",
            "result_analysis_code",
            "analysis_code_sha256",
            "result_analysis_workbook",
        ):
            entry.pop(field, None)
        entry.update(
            status="designed",
            classification={
                "objective": specification["objective"],
                "structures": list(specification["structures"]),
            },
            capabilities={},
            depends_on=deepcopy(specification["depends_on"]),
            framework_section=f"### {question}",
            primary_execution_status="awaiting_user_execution",
            result_quality_status="pending",
            result_analysis_status="pending",
            validation_status="pending",
            result_summary_status="pending",
            result_summary_anchor="",
            artifact_hashes={},
            validated_artifact_hashes={},
            stale_layers=[],
            artifacts_stale=False,
        )
        state["subproblems"][question] = entry
        numeral = "二" if question == "Q2" else "三"
        (root / f"问题{numeral}求解").mkdir(parents=True, exist_ok=True)

    state_path.write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    framework_path = root / "模型论文框架.md"
    text = framework_path.read_text(encoding="utf-8")
    insertion = "### Q2\n\n待设计。\n\n### Q3\n\n待设计。\n\n## 图表证据链"
    if "## 图表证据链" not in text:
        raise AssertionError("sync fixture is missing its expected framework insertion anchor")
    framework_path.write_text(
        text.replace("## 图表证据链", insertion, 1),
        encoding="utf-8",
    )


class QuestionRuntimeCharacterizationTests(unittest.TestCase):
    def test_unscoped_resolver_aggregates_distinct_question_classifications(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()

            unscoped = runtime.resolve_runtime("problem_analysis", project_root=root)
            self.assertIsNone(unscoped["assurance"]["context"]["question"])
            self.assertEqual(unscoped["assurance"]["status"], "review_required")
            self.assertTrue(
                any(
                    "scoped subproblems do not share one objective/structures/capabilities"
                    in item
                    for item in unscoped["assurance"]["context"]["ambiguities"]
                ),
                unscoped["assurance"]["context"]["ambiguities"],
            )

            scoped = runtime.resolve_runtime(
                "problem_analysis", project_root=root, question="Q1"
            )
            self.assertEqual(scoped["assurance"]["context"]["question"], "Q1")
            self.assertEqual(scoped["assurance"]["status"], "pass")
            self.assertEqual(scoped["classification"]["objective"], "optimization")

    def test_semantic_governance_currently_has_no_question_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, framework_path = build_three_question_project(root)
            self.assertNotIn(
                "question", inspect.signature(SEMANTIC.validate_project).parameters
            )

            text = framework_path.read_text(encoding="utf-8")
            q2_start = text.index("### Q2：第一问")
            q3_start = text.index("### Q3：第一问")
            framework_path.write_text(text[:q2_start] + text[q3_start:], encoding="utf-8")

            report = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(report["status"], "failed", report)
            self.assertIn("Q1", report["semantic_identity_hashes"])
            self.assertTrue(
                any("Q2" in issue and "缺少对应" in issue for issue in report["issues"]),
                report["issues"],
            )

    def test_sync_currently_observes_all_registered_questions_for_code_scope(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(
                root,
                status="designed",
                phase="solve_validate",
                include_solution=False,
                include_analysis=False,
                include_analysis_code=False,
            )
            add_unfinished_questions_to_sync_project(root)

            self.assertNotIn("question", inspect.signature(syncer.synchronize).parameters)
            report = syncer.synchronize(root, write=False, delivery_scope="code")

            self.assertEqual(set(report["questions"]), {"Q1", "Q2", "Q3"})
            self.assertTrue(report["questions"]["Q1"]["primary_code"])
            self.assertFalse(report["questions"]["Q2"]["primary_code"])
            self.assertFalse(report["questions"]["Q3"]["primary_code"])
            self.assertTrue(
                any("正式交付缺少标准主求解脚本" in issue for issue in report["issues"]),
                report["issues"],
            )

    def test_result_dependency_is_reported_but_not_yet_an_execution_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()

            plan = runtime.resolve_runtime(
                "full_solution", project_root=root, question="Q2"
            )
            diagnostics = plan["assurance"]["context"]["dependency_diagnostics"]
            result_edge = next(
                row
                for row in diagnostics["result_dependencies"]
                if row["question"] == "Q2" and row["upstream"] == "Q1"
            )

            self.assertNotEqual(result_edge["status"], "verified", result_edge)
            self.assertIn(
                "code_delivery", plan["runtime_plan"]["pre_delivery_gate_names"]
            )
            self.assertEqual(
                plan["assurance"]["status"],
                "pass",
                "the current contract treats dependency diagnostics as read-only observations",
            )

    def test_typed_result_change_propagates_to_q2_without_staling_independent_q3(self):
        def entry(depends_on=None):
            return {
                "status": "validated",
                "depends_on": list(depends_on or []),
                "model_challenge_status": "passed",
                "human_model_approval_status": "approved",
                "primary_execution_status": "accepted",
                "analysis_execution_status": "accepted",
                "result_quality_status": "passed",
                "result_analysis_status": "passed",
                "validation_status": "passed",
                "result_summary_status": "current",
                "artifacts_stale": False,
                "stale_layers": [],
            }

        state = {
            "subproblems": {
                "Q1": entry(),
                "Q2": entry([{"question": "Q1", "kind": "result"}]),
                "Q3": entry(),
            }
        }
        report = TRANSITIONS.apply_transition(
            state,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=STATE_TRANSITION_CONTRACT,
        )

        self.assertEqual(report["affected_questions"], ["Q1", "Q2"])
        self.assertNotIn("Q3", report["affected_questions"])
        self.assertFalse(state["subproblems"]["Q3"]["artifacts_stale"])


if __name__ == "__main__":
    unittest.main()
