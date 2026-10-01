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


def selected_framework(carrier="docx"):
    item = framework()
    item["paper_fragments"].append({
        "id": "paper.figure.q1", "kind": "figure_or_table_claim", "scope": "Q1",
        "depends_on": ["claim:gain_claim"], "anchor": "Accepted figure", "status": "current",
    })
    entrypoint = ("draft_docx/paper.docx" if carrier == "docx"
                  else "final_latex/main.tex")
    source_file = entrypoint if carrier == "docx" else "final_latex/sections/q1.tex"
    for fragment in item["paper_fragments"]:
        fragment["source_file"] = source_file
    locator = ({"kind": "docx_bookmark", "value": "fig_q1",
                "body_reference": "See Figure 1."}
               if carrier == "docx" else
               {"kind": "latex_label", "value": "fig:q1"})
    item["claim_consumption_policy"] = {
        "protocol_version": "1.5.0",
        "mode": "enforce_selected_paper_claim_chain",
        "paper_source": {"format": carrier, "entrypoint": entrypoint},
        "required_consumptions": [{
            "claim_id": "gain_claim",
            "fragment_kinds": ["abstract_claim", "question_result_text",
                               "figure_or_table_claim"],
        }],
        "figure_bindings": [{
            "figure_id": "Q1_F01", "fragment_id": "paper.figure.q1",
            "carrier_locator": locator, "image_path": "figures/q1.png",
            "source_bindings": [{"source_id": "baseline", "sheet": "measurements",
                                 "required_headers": ["metric", "value"]}],
        }],
    }
    return item


class ClaimConsumptionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.policy_validator = Draft202012Validator({
            "$ref": "#/$defs/claim_consumption_policy", "$defs": cls.schema["$defs"],
        })

    def test_optional_closed_policy_pairs_and_bounded_obligations(self):
        self.assertEqual(self.schema["version"], "8.16.0")
        paper = self.schema["properties"]["paper_framework"]
        self.assertNotIn("claim_consumption_policy", paper["required"])
        self.assertEqual(paper["properties"]["claim_consumption_policy"],
                         {"$ref": "#/$defs/claim_consumption_policy"})
        valid = framework()["claim_consumption_policy"]
        self.assertTrue(self.policy_validator.is_valid(valid))
        propagate = {**valid, "protocol_version": "1.1.0", "mode": "propagate"}
        self.assertTrue(self.policy_validator.is_valid(propagate))
        enforce = {**valid, "protocol_version": "1.2.0", "mode": "enforce_latex_text"}
        self.assertTrue(self.policy_validator.is_valid(enforce))
        for bad in (None, {}, {**valid, "mode": "enforce"},
                    {**valid, "mode": "propagate"},
                    {**valid, "protocol_version": "1.1.0"},
                    {**valid, "protocol_version": "1.2.0"},
                    {**valid, "mode": "enforce_latex_text"},
                    {**valid, "mode": None},
                    {**valid, "protocol_version": None},
                    {key: value for key, value in valid.items() if key != "mode"},
                    {key: value for key, value in valid.items() if key != "protocol_version"},
                    {**valid, "protocol_version": "2.0.0"},
                    {**propagate, "mode": "enforce"},
                    {**enforce, "mode": "propagate"},
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

    def test_legacy_fragments_stay_tex_only_while_exact_1_5_can_select_docx(self):
        paper_schema = deepcopy(self.schema["properties"]["paper_framework"])
        paper_schema["$defs"] = self.schema["$defs"]
        validator = Draft202012Validator(paper_schema)
        example = yaml.safe_load(
            (ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8")
        )["paper_framework"]

        legacy = deepcopy(example)
        legacy.update(framework())
        legacy["paper_fragments"][0]["source_file"] = "draft_docx/paper.docx"
        self.assertFalse(validator.is_valid(legacy))
        self.assertTrue(any("legacy final_latex TeX shape" in issue for issue in
                            state_validator._validate_claim_consumption_policy(legacy)))

        selected = deepcopy(example)
        selected.update(selected_framework("docx"))
        self.assertTrue(validator.is_valid(selected), list(validator.iter_errors(selected)))
        self.assertEqual(state_validator._validate_claim_consumption_policy(selected), [])

    def test_1_5_relation_validator_fails_closed_on_carrier_mismatches(self):
        cases = []

        missing_source = selected_framework("docx")
        missing_source["claim_consumption_policy"].pop("paper_source")
        cases.append(("missing paper_source", missing_source))

        entrypoint_mismatch = selected_framework("docx")
        entrypoint_mismatch["claim_consumption_policy"]["paper_source"]["entrypoint"] = (
            "final_latex/main.tex"
        )
        cases.append(("format entrypoint mismatch", entrypoint_mismatch))

        docx_fragment_mismatch = selected_framework("docx")
        docx_fragment_mismatch["paper_fragments"][0]["source_file"] = "draft_docx/other.docx"
        cases.append(("docx fragment mismatch", docx_fragment_mismatch))

        latex_fragment_mismatch = selected_framework("latex")
        latex_fragment_mismatch["paper_fragments"][0]["source_file"] = "draft_docx/paper.docx"
        cases.append(("latex fragment mismatch", latex_fragment_mismatch))

        docx_locator_mismatch = selected_framework("docx")
        docx_locator_mismatch["claim_consumption_policy"]["figure_bindings"][0][
            "carrier_locator"
        ] = {"kind": "latex_label", "value": "fig:q1"}
        cases.append(("docx locator mismatch", docx_locator_mismatch))

        docx_reference_missing = selected_framework("docx")
        docx_reference_missing["claim_consumption_policy"]["figure_bindings"][0][
            "carrier_locator"
        ].pop("body_reference")
        cases.append(("docx reference missing", docx_reference_missing))

        latex_reference_forbidden = selected_framework("latex")
        latex_reference_forbidden["claim_consumption_policy"]["figure_bindings"][0][
            "carrier_locator"
        ]["body_reference"] = "See Figure 1."
        cases.append(("latex reference forbidden", latex_reference_forbidden))

        for label, item in cases:
            with self.subTest(label=label):
                self.assertTrue(
                    state_validator._validate_claim_consumption_policy(item), item
                )

    def test_every_legacy_policy_rejects_docx_fragment_sources(self):
        pairs = (
            ("1.0.0", "observe"),
            ("1.1.0", "propagate"),
            ("1.2.0", "enforce_latex_text"),
            ("1.3.0", "enforce_latex_text_and_figure_chain"),
            ("1.4.0", "enforce_latex_text_and_figure_chain"),
        )
        for version, mode in pairs:
            with self.subTest(version=version):
                item = (selected_framework("latex") if version in {"1.3.0", "1.4.0"}
                        else framework())
                policy = item["claim_consumption_policy"]
                policy.update(protocol_version=version, mode=mode)
                policy.pop("paper_source", None)
                for binding in policy.get("figure_bindings", []):
                    locator = binding.pop("carrier_locator", None)
                    if locator:
                        binding["latex_label"] = locator["value"]
                for fragment in item["paper_fragments"]:
                    fragment["source_file"] = "draft_docx/paper.docx"
                issues = state_validator._validate_claim_consumption_policy(item)
                self.assertTrue(any("legacy final_latex TeX shape" in issue
                                    for issue in issues), issues)

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
                       {**base["claim_consumption_policy"], "protocol_version": "1.2.0"},
                       {**base["claim_consumption_policy"], "mode": "enforce_latex_text"},
                       {**base["claim_consumption_policy"], "mode": "other"}):
            with self.subTest(policy=policy):
                changed = deepcopy(base)
                changed["claim_consumption_policy"] = policy
                self.assertTrue(state_validator._validate_claim_consumption_policy(changed))
        good = deepcopy(base)
        good["claim_consumption_policy"].update(protocol_version="1.1.0", mode="propagate")
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])
        good["claim_consumption_policy"].update(protocol_version="1.2.0", mode="enforce_latex_text")
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

    def test_contract_keeps_original_authorities_and_limits_gates_to_explicit_scope(self):
        contract = yaml.safe_load((ROOT / "core/claim_consumption_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "1.8.0")
        self.assertEqual(contract["authority"]["numerical_qualification"], "core/claim_evidence_contract.yaml")
        self.assertEqual(contract["authority"]["claim_strength"],
                         "core/writing_reasoning_contract.yaml#claim_strength_calibration")
        self.assertEqual(contract["activation"]["supported_policies"], [
            {"protocol_version": "1.0.0", "mode": "observe", "stale_writer": "none"},
            {"protocol_version": "1.1.0", "mode": "propagate", "stale_writer": "existing_project_transaction_only"},
            {"protocol_version": "1.2.0", "mode": "enforce_latex_text", "stale_writer": "existing_project_transaction_only"},
            {"protocol_version": "1.3.0", "mode": "enforce_latex_text_and_figure_chain", "stale_writer": "existing_project_transaction_only"},
            {"protocol_version": "1.4.0", "mode": "enforce_latex_text_and_figure_chain", "stale_writer": "existing_project_transaction_only", "structured_rejection_return": "required"},
            {"protocol_version": "1.5.0", "mode": "enforce_selected_paper_claim_chain", "stale_writer": "existing_project_transaction_only", "structured_rejection_return": "required", "selected_carrier": "required"},
        ])
        self.assertTrue(contract["activation"]["audit_route_read_only_in_all_modes"])
        self.assertEqual(contract["activation"]["project_writer"],
                         "existing_project_transaction_for_propagate_or_enforce_modes")
        self.assertEqual(contract["activation"]["automatic_existing_gate_insertion"],
                         "explicit_latex_or_submission_scope_for_protocol_1.2.0_to_1.4.0_and_explicit_selected_carrier_or_submission_scope_for_protocol_1.5.0")
        self.assertEqual(contract["formal_text_gate"]["activation"],
                         "explicit_enforce_latex_text_protocol_1.2.0_and_explicit_latex_or_submission_scope")
        self.assertEqual(contract["formal_figure_gate"]["activation"],
                         "explicit_protocol_1.3.0_or_1.4.0_enforce_latex_text_and_figure_chain_and_explicit_latex_or_submission_scope")
        self.assertEqual(contract["formal_figure_gate"]["inherited_text_conditions"],
                         "recheck_1.2.0_text_conditions_in_one_live_audit_with_exact_matched_Figure_caption_scalar_exemption")
        self.assertEqual(contract["formal_text_gate"]["source_binding"],
                         "project_and_skill_read_sets_rechecked_under_existing_project_lock")
        self.assertEqual(contract["formal_text_gate"]["passing_sync"],
                         "preserve_State_and_Framework_bytes_write_only_sync_report_under_project_lock")
        propagation = contract["stale_propagation"]
        self.assertEqual(propagation["activation"],
                         "explicit_propagate_1.1.0_or_enforce_latex_text_1.2.0_or_figure_chain_1.3.0_or_structured_rejection_1.4.0_or_selected_carrier_1.5.0")
        self.assertEqual(propagation["seed_edges"], "claim:<id> dependencies of paper_fragments")
        self.assertEqual(propagation["transitive_edges"], "paper_fragment_ID_dependencies")
        self.assertEqual(propagation["merge"], "union_with_existing_question_and_artifact_stale")
        self.assertEqual(propagation["status_change"], "current_to_stale_only_never_clear_stale")
        self.assertEqual(propagation["persistence"],
                         "State_and_Framework_fragment_rows_in_one_existing_project_transaction")
        self.assertEqual(propagation["audit_route"], "report_only_in_all_modes")
        manifest = yaml.safe_load(
            (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        )
        sync_rules = " ".join(manifest["utility_gates"]["project_sync"]["rules"])
        package_rules = " ".join(
            manifest["utility_gates"]["submission_package_validation"]["rules"]
        )
        self.assertIn("1.5.0/enforce_selected_paper_claim_chain", sync_rules)
        self.assertIn("explicit docx or latex scope", sync_rules)
        self.assertIn("Exact 1.5.0 selected LaTeX packages", package_rules)
        self.assertIn("selected DOCX submission fails closed", package_rules)


if __name__ == "__main__":
    unittest.main()
