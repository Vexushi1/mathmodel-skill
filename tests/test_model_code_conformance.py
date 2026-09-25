"""A1 structural conformance tests; fixtures are declarations, never model proofs."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import model_code_conformance as conformance
import conformance_source
import stage_code
from tests.test_v900_semantic_identity_binding import identity, framework, structured_question


def save(root, state):
    (root / "state").mkdir(exist_ok=True)
    (root / "state/project_state.yaml").write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def fixture(root, backend="python", stage="primary", expression="h * (u - ambient)", extra="", helper=False):
    sib = identity()
    sib["constraints"][0]["implementation_expression"] = {"python": "h * (u - ambient)", "matlab": "h * (u - ambient)"}
    state = {"project": {"competition": "CUMCM", "problem": "synthetic"},
             "execution": {"solver_backend": backend, "solver_backend_selection_reason": "synthetic whole-task declaration"},
             "subproblems": {"Q1": structured_question(sib)},
             "preprocessing": {"decision": "question_local", "status": "not_applicable"}}
    directory = root / "问题一求解"
    directory.mkdir(exist_ok=True)
    filename = (("问题一求解.py" if stage == "primary" else "问题一结果深化分析.py") if backend == "python" else
                "q1_solver.m" if stage == "primary" else "q1_analysis.m")
    path = directory / filename
    config = {"stage": stage, "problem_name": "问题一", "solver_backend": backend,
              "run_receipt_protocol_version": "1.1.0", "data_paths": ["not_read.csv"],
              "data_sha256": "1" * 64, "code_dependencies": []}
    if helper:
        helper_path = directory / ("helper.py" if backend == "python" else "helper.m")
        helper_path.write_text("def helper(x):\n    return x\n" if backend == "python" else
                               "function y = helper(x)\ny = x;\nend\n", encoding="utf-8")
        config["code_dependencies"] = [{"path": helper_path.relative_to(root).as_posix(),
                                        "sha256": hashlib.sha256(helper_path.read_bytes()).hexdigest()}]
    if backend == "python":
        path.write_text("RUN_CONFIG = " + repr(config) + "\n" + extra +
                        "def solve(u, ambient, h):\n    return " + expression + "\n", encoding="utf-8")
    else:
        literal = json.dumps(config, ensure_ascii=False).replace("'", "''")
        path.write_text(f"function {path.stem}()\nRUN_CONFIG = jsondecode('{literal}');\nend\n" + extra +
                        f"function y = solve(u, ambient, h)\ny = {expression};\nend\n", encoding="utf-8")
    save(root, state)
    (root / "模型论文框架.md").write_text(framework(sib), encoding="utf-8")
    return state, path, sib


def declare(root, state, stage="primary", *, check_expression=False):
    inventory = conformance.inspect_project(root, "Q1", stage, inventory=True)
    if inventory["status"] != "not_assessed":
        raise AssertionError(inventory)
    anchor = next(row for row in inventory["source_symbols"] if row["symbol"] == "solve")
    mappings = []
    for i, selector in enumerate(inventory["model_selectors"], 1):
        bound = {key: anchor[key] for key in ("path", "symbol", "sha256")}
        if check_expression and selector["field"] == "constraints":
            bound.update(check_expression=True, expression_target="y")
        mappings.append({"id": f"MC{i}", "model_ref": selector, "relation": "direct",
                         "rationale": "Synthetic structural mapping; not an equivalence proof", "anchors": [bound]})
    record = {"protocol_version": "1.0.0", "question": "Q1", "stage": stage,
              **inventory["binding"], "mappings": mappings, "reverse_review": []}
    state["subproblems"]["Q1"].setdefault("implementation_conformance", {})[stage] = record
    save(root, state)
    return record


def bytes_in(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class ConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def result(self, stage="primary"):
        return conformance.inspect_project(self.root, "Q1", stage)

    def test_inventory_is_not_verification_and_does_not_read_missing_data(self):
        state, path, _ = fixture(self.root)
        before = bytes_in(self.root)
        report = self.result()
        self.assertEqual(report["status"], "not_assessed", report)
        self.assertFalse(report["execution_authorized"])
        self.assertNotIn("not_read.csv", report["observed_sources"]["project"])
        self.assertEqual(before, bytes_in(self.root))

    def test_python_structure_and_approved_reference_match_without_any_execution(self):
        state, path, _ = fixture(self.root, extra="raise RuntimeError('task execution is forbidden')\n")
        declare(self.root, state, check_expression=True)
        before = bytes_in(self.root)
        report = self.result()
        self.assertEqual(report["status"], "structure_verified", report)
        self.assertEqual(report["expression_checks"][0]["status"], "matched")
        self.assertEqual(report["mathematical_equivalence"], "not_established")
        self.assertEqual(report["independent_review"], "not_run")
        self.assertEqual(before, bytes_in(self.root))

    def test_matlab_flat_source_syntax_match_is_not_native_execution(self):
        state, _, _ = fixture(self.root, "matlab")
        declare(self.root, state, check_expression=True)
        report = self.result()
        self.assertEqual(report["status"], "structure_verified", report)
        self.assertEqual(report["native_execution"], "not_run")

    def test_constraints_are_enumerated_from_current_sib_not_author_list(self):
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        record["mappings"] = [m for m in record["mappings"] if m["model_ref"]["field"] != "constraints"]
        save(self.root, state)
        report = self.result()
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("unmapped current model object: constraints" in s for s in report["errors"]))

    def test_phantom_anchor_and_duplicate_symbol_do_not_pass(self):
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        record["mappings"][0]["anchors"][0]["symbol"] = "ghost"
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")
        state, _, _ = fixture(self.root, extra="def solve(u, ambient, h):\n    return u\n")
        declare(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_main_unchanged_helper_changes_invalidate_whole_record(self):
        state, path, _ = fixture(self.root, helper=True)
        declare(self.root, state)
        original = path.read_bytes()
        (path.parent / "helper.py").write_text("def helper(x):\n    return x + 1\n", encoding="utf-8")
        report = self.result()
        self.assertEqual(report["status"], "blocked", report)
        self.assertEqual(original, path.read_bytes())
        self.assertEqual(state["subproblems"]["Q1"]["human_model_approval_status"], "approved")

    def test_robin_to_value_boundary_changes_fail_direct_syntactic_reference(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state, _, _ = fixture(root, backend, expression="u - ambient")
                declare(root, state, check_expression=True)
                report = conformance.inspect_project(root, "Q1", "primary")
                self.assertEqual(report["status"], "blocked", report)
                self.assertEqual(report["expression_checks"][0]["status"], "different")

    def test_equivalent_transform_is_review_not_false_failure(self):
        state, _, _ = fixture(self.root, expression="(u - ambient) * h")
        record = declare(self.root, state, check_expression=True)
        for mapping in record["mappings"]:
            if mapping["model_ref"]["field"] == "constraints":
                mapping["relation"] = "equivalent_transform"
                mapping["rationale"] = "scalar commutation, subject to review of the actual domain"
        save(self.root, state)
        report = self.result()
        self.assertEqual(report["status"], "needs_review", report)
        self.assertEqual(report["errors"], [])

    def test_penalty_name_does_not_imply_model_error(self):
        state, _, _ = fixture(self.root, extra="def augmented_lagrangian_penalty(x):\n    return x * x\n")
        declare(self.root, state)
        self.assertEqual(self.result()["status"], "structure_verified")

    def test_reverse_clip_is_observation_and_requires_explicit_adjudication(self):
        state, _, _ = fixture(self.root, extra="import numpy as np\ndef clip_state(x):\n    return np.clip(x, 0, 1)\n")
        record = declare(self.root, state)
        report = self.result()
        self.assertEqual(report["status"], "needs_review", report)
        self.assertEqual(len(report["reverse_candidates"]), 1)
        candidate = report["reverse_candidates"][0]
        record["reverse_review"] = [{"operation_id": candidate["operation_id"], "model_ref": {"field": "constraints", "id": "C1"},
                                     "rationale": "Declared clipping boundary; actual activation still unproved"}]
        save(self.root, state)
        report = self.result()
        self.assertEqual(report["status"], "structure_verified", report)
        self.assertEqual(report["constraint_activation"], "not_proved")
        record["reverse_review"][0]["operation_id"] = "OP-" + "0" * 16
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_dynamic_code_is_needs_review_not_silently_executed(self):
        state, _, _ = fixture(self.root, extra="def dynamic(x):\n    return eval(x)\n")
        declare(self.root, state)
        report = self.result()
        self.assertEqual(report["status"], "needs_review", report)

    def test_analysis_record_cannot_be_replayed_for_primary(self):
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        record["stage"] = "analysis"
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_valid_analysis_needs_no_fabricated_accepted_workbook(self):
        state, _, _ = fixture(self.root, stage="analysis")
        declare(self.root, state, stage="analysis")
        report = self.result("analysis")
        self.assertEqual(report["status"], "structure_verified", report)
        self.assertEqual(report["numerical_acceptance"], "not_assessed")

    def test_backend_conflict_fails_and_does_not_change_policy(self):
        state, _, _ = fixture(self.root)
        declare(self.root, state)
        state["execution"]["solver_backend"] = "matlab"
        save(self.root, state)
        before = bytes_in(self.root)
        self.assertEqual(self.result()["status"], "blocked")
        self.assertEqual(before, bytes_in(self.root))

    def test_partial_unknown_and_false_success_records_are_rejected(self):
        for bad in (None, {}, {"primary": {}}, {"unknown": {}}, {"primary": {"passed": True}}):
            with self.subTest(bad=bad):
                state, _, _ = fixture(self.root)
                state["subproblems"]["Q1"]["implementation_conformance"] = bad
                save(self.root, state)
                self.assertEqual(self.result()["status"], "blocked")
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        record["protocol_version"] = "2.0.0"
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_all_revision_endpoints_reject_boolean_and_float(self):
        for field in ("semantic_revision", "approved_semantic_revision", "validated_semantic_revision"):
            for value in (True, 3.0, "3", None):
                with self.subTest(field=field, value=value):
                    state, _, _ = fixture(self.root)
                    state["subproblems"]["Q1"][field] = value
                    save(self.root, state)
                    self.assertEqual(self.result()["status"], "blocked")
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        record["semantic_revision"] = 3.0
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_state_framework_and_source_midread_changes_fail_without_writes(self):
        original = conformance._mapping_issues
        for relative in ("state/project_state.yaml", "模型论文框架.md", "问题一求解/问题一求解.py"):
            with self.subTest(relative=relative):
                state, _, _ = fixture(self.root)
                declare(self.root, state)
                def changing(*args, **kwargs):
                    result = original(*args, **kwargs)
                    path = self.root / relative
                    path.write_bytes(path.read_bytes() + b"\n# concurrent edit\n")
                    return result
                with patch.object(conformance, "_mapping_issues", side_effect=changing):
                    report = self.result()
                self.assertEqual(report["status"], "blocked", report)
                self.assertTrue(any("snapshot" in item for item in report["errors"]))

    def test_comment_edit_invalidates_binding_not_model_approval(self):
        state, path, _ = fixture(self.root)
        declare(self.root, state)
        path.write_text(path.read_text(encoding="utf-8") + "# wording only\n", encoding="utf-8")
        before = bytes_in(self.root)
        self.assertEqual(self.result()["status"], "blocked")
        self.assertEqual(before, bytes_in(self.root))

    def test_pending_transaction_is_not_automatically_recovered(self):
        state, _, _ = fixture(self.root)
        declare(self.root, state)
        from project_transaction import JOURNAL_RELATIVE_PATH
        path = self.root / JOURNAL_RELATIVE_PATH
        path.write_text("synthetic pending journal", encoding="utf-8")
        before = bytes_in(self.root)
        self.assertEqual(self.result()["status"], "blocked")
        self.assertEqual(before, bytes_in(self.root))

    def test_duplicate_yaml_and_alias_and_deep_mapping_are_not_silently_accepted(self):
        for suffix in ("duplicate: 1\nduplicate: 2\n", "anchor: &a [1]\nreplay: *a\n", "deep: " + "["*40 + "0" + "]"*40 + "\n"):
            state, _, _ = fixture(self.root)
            declare(self.root, state)
            path = self.root / "state/project_state.yaml"
            path.write_bytes(path.read_bytes() + suffix.encode())
            self.assertEqual(self.result()["status"], "blocked")

    def test_source_budget_is_explicit_not_truncated_success(self):
        state, path, _ = fixture(self.root)
        declare(self.root, state)
        path.write_text("#" + "a" * (2097152 + 1), encoding="utf-8")
        report = self.result()
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("budget" in value for value in report["errors"]))

    def test_source_escape_or_alias_is_rejected(self):
        state, path, _ = fixture(self.root)
        declare(self.root, state)
        state["subproblems"]["Q1"]["code"] = "../outside.py"
        save(self.root, state)
        self.assertEqual(self.result()["status"], "blocked")

    def test_duplicate_framework_scope_is_rejected(self):
        state, _, _ = fixture(self.root)
        declare(self.root, state)
        path = self.root / "模型论文框架.md"
        path.write_text(path.read_text(encoding="utf-8") * 2, encoding="utf-8")
        self.assertEqual(self.result()["status"], "blocked")

    def test_record_schema_is_closed_and_not_an_approval_store(self):
        state, _, _ = fixture(self.root)
        record = declare(self.root, state)
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        validator = Draft202012Validator({"$ref": "#/$defs/implementation_conformance_record", "$defs": schema["$defs"]})
        self.assertEqual(list(validator.iter_errors(record)), [])
        record["approved"] = True
        self.assertTrue(list(validator.iter_errors(record)))

    def test_expression_payload_cannot_execute_python(self):
        state, _, sib = fixture(self.root)
        sib["constraints"][0]["implementation_expression"]["python"] = "open('forbidden-marker', 'w').write('not executed')"
        state["subproblems"]["Q1"] = structured_question(sib)
        save(self.root, state)
        (self.root / "模型论文框架.md").write_text(framework(sib), encoding="utf-8")
        declare(self.root, state, check_expression=True)
        self.assertEqual(self.result()["status"], "needs_review")

    def test_real_cli_exit_codes_and_readonly_output(self):
        state, _, _ = fixture(self.root)
        cmd = [sys.executable, str(ROOT / "scripts/model_code_conformance.py"), str(self.root), "--question", "Q1", "--stage", "primary"]
        before = bytes_in(self.root)
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8")
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "not_assessed")
        self.assertEqual(before, bytes_in(self.root))
        record = declare(self.root, state)
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stderr)
        record["source_bundle_sha256"] = "0" * 64
        save(self.root, state)
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8")
        self.assertEqual(run.returncode, 1, run.stderr)


if __name__ == "__main__":
    unittest.main()
