"""B2 opt-in policy pairing and state reference validation."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_project_state as state_validator
from tests.claim_fixture import record


def framework():
    return {
        "claim_evidence": record(),
        "claim_consumption_policy": {
            "protocol_version": "1.0.0",
            "mode": "observe",
            "required_consumptions": [
                {"claim_id": "gain_claim", "fragment_kinds": ["abstract_claim", "question_result_text"]},
            ],
        },
        "paper_fragments": [
            {"id": "paper.abstract.q1", "kind": "abstract_claim", "scope": "Q1",
             "depends_on": ["claim:gain_claim"], "anchor": "cost reduction", "status": "current"},
            {"id": "paper.result.q1", "kind": "question_result_text", "scope": "Q1",
             "depends_on": ["claim:gain_claim"], "anchor": "cost reduction result", "status": "current"},
        ],
    }


class ClaimConsumptionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.policy_validator = Draft202012Validator({
            "$ref": "#/$defs/claim_consumption_policy", "$defs": cls.schema["$defs"],
        })

    def test_optional_closed_policy_pairs_and_bounded_obligations(self):
        self.assertEqual(self.schema["version"], "8.5.0")
        paper = self.schema["properties"]["paper_framework"]
        self.assertNotIn("claim_consumption_policy", paper["required"])
        self.assertEqual(paper["properties"]["claim_consumption_policy"],
                         {"$ref": "#/$defs/claim_consumption_policy"})
        valid = framework()["claim_consumption_policy"]
        self.assertTrue(self.policy_validator.is_valid(valid))
        propagate = {**valid, "protocol_version": "1.1.0", "mode": "propagate"}
        self.assertTrue(self.policy_validator.is_valid(propagate))
        for bad in (None, {}, {**valid, "mode": "enforce"},
                    {**valid, "mode": "propagate"},
                    {**valid, "protocol_version": "1.1.0"},
                    {**valid, "mode": None},
                    {**valid, "protocol_version": None},
                    {key: value for key, value in valid.items() if key != "mode"},
                    {key: value for key, value in valid.items() if key != "protocol_version"},
                    {**valid, "protocol_version": "2.0.0"},
                    {**propagate, "mode": "enforce"},
                    {**propagate, "required_consumptions": []},
                    {**valid, "source_format": "modular_latex"},
                    {**valid, "required_consumptions": []},
                    {**valid, "required_consumptions": [valid["required_consumptions"][0]] * 513},
                    {**valid, "required_consumptions": [{"claim_id": "gain_claim", "fragment_kinds": []}]},
                    {**valid, "required_consumptions": [{"claim_id": "gain_claim", "fragment_kinds": ["abstract_claim"] * 2}]},
                    {**valid, "required_consumptions": [{"claim_id": "gain_claim", "fragment_kinds": ["invented"]}]},
                    {**valid, "required_consumptions": [{"claim_id": "bad:id", "fragment_kinds": ["abstract_claim"]}]}):
            with self.subTest(bad=bad):
                self.assertFalse(self.policy_validator.is_valid(bad))

    def test_fragment_schema_accepts_real_project_relative_tex_source(self):
        validator = Draft202012Validator({
            "$ref": "#/$defs/paper_fragment_entry", "$defs": self.schema["$defs"],
        })
        fragment = deepcopy(framework()["paper_fragments"][0])
        fragment["source_file"] = "final_latex/frontmatter/abstract.tex"
        self.assertTrue(validator.is_valid(fragment))
        fragment["source_file"] = "outside/abstract.tex"
        self.assertFalse(validator.is_valid(fragment))

    def test_old_state_without_policy_keeps_legacy_reference_behavior(self):
        old = framework()
        old.pop("claim_consumption_policy")
        old["paper_fragments"][0]["depends_on"] = ["claim:legacy_unchecked"]
        self.assertEqual(state_validator._validate_claim_consumption_policy(old), [])
        self.assertEqual(state_validator._validate_paper_fragments(old)[0], [])

    def test_relation_validator_rejects_malformed_or_mismatched_policy(self):
        base = framework()
        for policy in (None, {}, {"mode": "observe"},
                       {**base["claim_consumption_policy"], "mode": "propagate"},
                       {**base["claim_consumption_policy"], "protocol_version": "1.1.0"},
                       {**base["claim_consumption_policy"], "mode": "other"}):
            with self.subTest(policy=policy):
                changed = deepcopy(base)
                changed["claim_consumption_policy"] = policy
                self.assertTrue(state_validator._validate_claim_consumption_policy(changed))
        good = deepcopy(base)
        good["claim_consumption_policy"].update(protocol_version="1.1.0", mode="propagate")
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])

    def test_opt_in_references_and_claim_ids_must_be_unique_and_known(self):
        good = framework()
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])
        duplicate = deepcopy(good)
        duplicate["claim_evidence"]["claims"].append(deepcopy(duplicate["claim_evidence"]["claims"][0]))
        self.assertTrue(any("duplicate claim IDs" in issue for issue in
                            state_validator._validate_claim_consumption_policy(duplicate)))
        duplicate = deepcopy(good)
        duplicate["claim_consumption_policy"]["required_consumptions"].append(
            {"claim_id": "gain_claim", "fragment_kinds": ["title_claim"]})
        self.assertTrue(any("duplicate claim obligations" in issue for issue in
                            state_validator._validate_claim_consumption_policy(duplicate)))
        missing = deepcopy(good)
        missing["paper_fragments"][0]["depends_on"] = ["claim:unknown"]
        self.assertTrue(any("unknown claim" in issue for issue in
                            state_validator._validate_claim_consumption_policy(missing)))
        missing = deepcopy(good)
        missing["claim_consumption_policy"]["required_consumptions"][0]["claim_id"] = "unknown"
        self.assertTrue(any("unknown claim" in issue for issue in
                            state_validator._validate_claim_consumption_policy(missing)))

    def test_question_scope_conflict_and_global_fragment(self):
        good = framework()
        good["paper_fragments"][0]["scope"] = "global"
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])
        bad = deepcopy(good)
        bad["paper_fragments"][1]["scope"] = "Q2"
        self.assertTrue(any("scope Q2 conflicts with claim gain_claim scope Q1" in issue for issue in
                            state_validator._validate_claim_consumption_policy(bad)))

    def test_bad_fragment_graph_and_resource_budget_are_rejected(self):
        bad = framework()
        bad["paper_fragments"][0]["depends_on"].append("paper.result.q1")
        bad["paper_fragments"][1]["depends_on"].append("paper.abstract.q1")
        self.assertTrue(any("cycle" in issue for issue in
                            state_validator._validate_claim_consumption_policy(bad)))
        bad = framework()
        bad["paper_fragments"] *= 257
        self.assertTrue(any("fragment budget" in issue for issue in
                            state_validator._validate_claim_consumption_policy(bad)))

    def test_maximum_allowed_acyclic_fragment_chain_is_safe(self):
        item = framework()
        item["paper_fragments"] = [
            {"id": f"paper.f{index:03d}", "kind": "question_result_text", "scope": "Q1",
             "depends_on": [f"paper.f{index + 1:03d}" if index < 511 else "claim:gain_claim"],
             "anchor": "result", "status": "current"}
            for index in range(512)
        ]
        self.assertEqual(state_validator._validate_claim_consumption_policy(item), [])

    def test_project_validator_enables_opt_in_only(self):
        state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        state["paper_framework"].update(framework())
        self.assertEqual(state_validator.validate_state_payload(state, project_root=ROOT), [])
        state["paper_framework"]["paper_fragments"][0]["depends_on"] = ["claim:unknown"]
        issues = state_validator.validate_state_payload(state, project_root=ROOT)
        self.assertTrue(any("references unknown claim" in issue for issue in issues), issues)
        state["paper_framework"].pop("claim_consumption_policy")
        self.assertEqual(state_validator.validate_state_payload(state, project_root=ROOT), [])

    def test_contract_keeps_original_authorities_and_limits_writer_to_propagate(self):
        contract = yaml.safe_load((ROOT / "core/claim_consumption_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "1.1.0")
        self.assertEqual(contract["authority"]["numerical_qualification"], "core/claim_evidence_contract.yaml")
        self.assertEqual(contract["authority"]["claim_strength"],
                         "core/writing_reasoning_contract.yaml#claim_strength_calibration")
        self.assertEqual(contract["activation"]["supported_policies"], [
            {"protocol_version": "1.0.0", "mode": "observe", "stale_writer": "none"},
            {"protocol_version": "1.1.0", "mode": "propagate", "stale_writer": "existing_project_transaction_only"},
        ])
        self.assertTrue(contract["activation"]["audit_route_read_only_in_all_modes"])
        self.assertEqual(contract["activation"]["project_writer"],
                         "existing_project_transaction_for_propagate_only")
        self.assertFalse(contract["activation"]["automatic_existing_gate_insertion"])
        propagation = contract["stale_propagation"]
        self.assertEqual(propagation["activation"], "explicit_propagate_protocol_1.1.0_only")
        self.assertEqual(propagation["seed_edges"], "claim:<id> dependencies of paper_fragments")
        self.assertEqual(propagation["transitive_edges"], "paper_fragment_ID_dependencies")
        self.assertEqual(propagation["merge"], "union_with_existing_question_and_artifact_stale")
        self.assertEqual(propagation["status_change"], "current_to_stale_only_never_clear_stale")
        self.assertEqual(propagation["persistence"],
                         "State_and_Framework_fragment_rows_in_one_existing_project_transaction")
        self.assertEqual(propagation["audit_route"], "report_only_in_both_modes")


if __name__ == "__main__":
    unittest.main()
