"""Opt-in routing and predecessor preservation; no new numerical acceptance gates."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import model_code_conformance as audit
from resolve_runtime import resolve_runtime
import reading_plan_evidence as evidence
import test_reading_plan_evidence as predecessor_tests
from test_model_code_conformance import fixture, declare, save, bytes_in


def previous_a1_schema(schema):
    """Remove only the exact A2 additions and verify all prior fields byte-semantically."""
    schema=deepcopy(schema)
    assert schema['version']=='8.2.0'
    schema['version']='8.1.0'
    for name in ('implementation_conformance_policy','conformance_delivery','conformance_acceptance'):
        schema['$defs'].pop(name)
    schema['properties']['subproblems']['additionalProperties']['properties'].pop('implementation_conformance_policy')
    slot=schema['$defs']['solver_stage_execution']
    slot['properties'].pop('conformance_delivery');slot['properties'].pop('conformance_acceptance')
    assert slot['dependentRequired'].pop('conformance_acceptance')==['conformance_delivery']
    expected=[{'if':{'required':['conformance_delivery'],'properties':{
        'conformance_delivery':{'properties':{'applicability':{'const':'current'}}}}},
        'then':{'required':['bundle_sha256']}},
        {'if':{'required':['conformance_acceptance'],'properties':{
        'conformance_acceptance':{'properties':{'applicability':{'const':'current'}}}}},
        'then':{'required':['validated_bundle_sha256']}}]
    assert slot.pop('allOf')==expected
    normalized=json.dumps(schema,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    assert hashlib.sha256(normalized.encode()).hexdigest()=="43b1477f453e1006373fc3b70a3294cbc0a21c0cf2424e8cfbbe52744423955b"
    return schema


class OptInTests(unittest.TestCase):
    def test_new_route_is_readonly_and_does_not_generate_numerical_artifacts(self):
        plan = resolve_runtime("conformance_audit")
        self.assertEqual(plan["modules"], [])
        self.assertEqual([gate["name"] for gate in plan["pre_delivery_gates"]], ["model_code_conformance"])
        self.assertEqual(plan["terminal_outputs"], ["conformance_report"])
        self.assertFalse(plan["task_code_execution_allowed"])
        self.assertNotIn("--write", plan["pre_delivery_gates"][0]["command"])

    def test_standard_routes_do_not_load_conformance(self):
        for intent in ("new_problem_design", "code_and_solution", "latex", "figures", "editable_mechanism_diagram", "returned_workbook_validation"):
            plan = resolve_runtime(intent, objective="optimization")
            self.assertNotIn("core/model_code_conformance_contract.yaml", plan["load_order"])
            self.assertNotIn("model_code_conformance", [gate["name"] for gate in plan["pre_delivery_gates"]])

    def test_schema_change_is_optional_and_existing_definitions_are_preserved(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        schema = previous_a1_schema(schema)
        self.assertEqual(schema["version"], "8.1.0")
        schema["version"] = "8.0.0"
        for name in ("conformance_model_ref", "conformance_anchor", "conformance_mapping", "conformance_reverse",
                     "implementation_conformance_record", "implementation_conformance"):
            schema["$defs"].pop(name)
        schema["properties"]["subproblems"]["additionalProperties"]["properties"].pop("implementation_conformance")
        normalized = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), "8179efd6b79959daa64b504824d78e34170a62d45d5f3c647c011b02219efa05")

    def test_a1_carrier_changes_are_visible_but_no_future_version_is_waived(self):
        old, new = predecessor_tests.AuditClosureProjectionTests().pair()
        new["version"] = "10.2.0"
        projected, changes = evidence.approved_a1_carrier_change("facts_current", old, new)
        self.assertEqual(projected, old)
        self.assertEqual(next(row for row in changes if row["path"] == "version")["candidate"], "10.2.0")
        for key, value in (("version", "10.3.0"),):
            unknown = deepcopy(new); unknown[key] = value
            self.assertEqual(evidence.approved_a1_carrier_change("facts_current", old, unknown), (unknown, []))
        self.assertEqual(evidence.approved_a1_carrier_change("unknown", old, new), (new, []))

    def test_a1_carrier_projection_preserves_unapproved_qualifications(self):
        old, new = predecessor_tests.AuditClosureProjectionTests().pair()
        new["version"] = "10.2.0"
        for key, value in (("environment_verified", True), ("selection_complete", False), ("extra", "unexpected")):
            changed = deepcopy(new); changed["solver_backend"][key] = value
            projected, _ = evidence.approved_a1_carrier_change("facts_current", old, changed)
            self.assertNotEqual(projected, old)
            self.assertEqual(projected["solver_backend"][key], value)

    def test_policy_bytes_mutation_is_rejected_not_just_project_mutation(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as skill:
            root, copied = Path(project), Path(skill)
            state, _, _ = fixture(root)
            declare(root, state)
            for relative in audit.POLICY_SOURCES:
                destination = copied / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            original = audit._mapping_issues
            def concurrent(*args, **kwargs):
                result = original(*args, **kwargs)
                path = copied / audit.CONTRACT
                path.write_bytes(path.read_bytes() + b"\n# changed during inspection\n")
                return result
            with patch.object(audit, "ROOT", copied), patch.object(audit, "_mapping_issues", side_effect=concurrent):
                report = audit.inspect_project(root, "Q1", "primary")
            self.assertEqual(report["status"], "blocked", report)

    def test_matlab_nested_functions_are_not_silently_treated_as_flat(self):
        with tempfile.TemporaryDirectory() as project:
            root = Path(project)
            state, _, _ = fixture(root, "matlab", extra="function z = outer(x)\nfunction y = inner(x)\ny = x;\nend\nz = inner(x);\nend\n")
            report = audit.inspect_project(root, "Q1", "primary", inventory=True)
            self.assertEqual(report["status"], "not_assessed", report)
            self.assertTrue(any("nested" in item for item in report["review_required"]))
            anchor = next(row for row in report["source_symbols"] if row["symbol"] == "<module>")
            mappings = [{"id": f"MC{i}", "model_ref": selector, "relation": "direct", "rationale": "synthetic unknown structure",
                         "anchors": [{k:anchor[k] for k in ("path", "symbol", "sha256")}]} for i,selector in enumerate(report["model_selectors"],1)]
            state["subproblems"]["Q1"]["implementation_conformance"] = {"primary": {
                "protocol_version":"1.0.0","question":"Q1","stage":"primary",**report["binding"],"mappings":mappings,"reverse_review":[]}}
            save(root,state)
            self.assertEqual(audit.inspect_project(root,"Q1","primary")["status"], "needs_review")

    def test_current_sib_change_cannot_be_hidden_by_rebinding_only_source(self):
        with tempfile.TemporaryDirectory() as project:
            root = Path(project)
            state, _, _ = fixture(root)
            declare(root, state)
            path=root/"模型论文框架.md"
            path.write_text(path.read_text(encoding="utf-8").replace("x_i in {0,1}", "x_i >= 0"),encoding="utf-8")
            self.assertEqual(audit.inspect_project(root,"Q1","primary")["status"],"blocked")

    def test_config_uses_captured_source_bytes_not_a_second_unbound_file_read(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as project:
                root=Path(project); state,_,_=fixture(root,backend); declare(root,state)
                with patch.object(audit.stage_code, "parse_stage_config", side_effect=AssertionError("unexpected second source-config read")):
                    report=audit.inspect_project(root,"Q1","primary")
                self.assertEqual(report["status"],"structure_verified",report)

    def test_nonexecutable_is_an_explicit_mathematical_review_boundary(self):
        with tempfile.TemporaryDirectory() as project:
            root=Path(project); state,_,_=fixture(root); record=declare(root,state)
            record["mappings"][0].update(relation="non_executable",anchors=[],rationale="source assumption, not executable")
            save(root,state); before=bytes_in(root)
            report=audit.inspect_project(root,"Q1","primary")
            self.assertEqual(report["status"],"needs_review",report)
            self.assertEqual(before,bytes_in(root))


if __name__ == "__main__":
    unittest.main()
