"""Exact, source-hash-bound G1A span-shift tests; historical approval fixture remains immutable."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_measurement():
    spec = importlib.util.spec_from_file_location(
        "v10280_measurement", ROOT / "tests/v10270_runtime_measurement.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V10280ApprovedSourceSpanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurement = load_measurement()
        cls.fixture = ROOT / "tests/fixtures/v1110_w3_proposition_source_spans.json"
        cls.frozen_w2 = ROOT / "tests/fixtures/v1110_w2_numeric_source_spans.json"
        cls.frozen_w1_draft = ROOT / "tests/fixtures/v1110_writing_draft_source_spans.json"
        cls.frozen_v1110 = ROOT / "tests/fixtures/v1110_release_source_spans.json"
        cls.frozen_v11 = ROOT / "tests/fixtures/v11_candidate_source_spans.json"
        cls.frozen_v10353 = ROOT / "tests/fixtures/v10353_approved_source_spans.json"
        cls.frozen_v10352 = ROOT / "tests/fixtures/v10352_approved_source_spans.json"
        cls.frozen_v10351 = ROOT / "tests/fixtures/v10351_approved_source_spans.json"
        cls.frozen_v10350 = ROOT / "tests/fixtures/v10350_approved_source_spans.json"
        cls.frozen_v10340 = ROOT / "tests/fixtures/v10340_approved_source_spans.json"
        cls.frozen_v10330 = ROOT / "tests/fixtures/v10330_approved_source_spans.json"
        cls.frozen_v10322 = ROOT / "tests/fixtures/v10322_approved_source_spans.json"
        cls.frozen_v10321 = ROOT / "tests/fixtures/v10321_approved_source_spans.json"
        cls.frozen_v10320 = ROOT / "tests/fixtures/v10320_approved_source_spans.json"
        cls.frozen_v10310 = ROOT / "tests/fixtures/v10310_approved_source_spans.json"
        cls.frozen_v10300 = ROOT / "tests/fixtures/v10300_approved_source_spans.json"
        cls.frozen_v10290 = ROOT / "tests/fixtures/v10290_approved_source_spans.json"
        cls.frozen_v10280 = ROOT / "tests/fixtures/v10280_approved_source_spans.json"

    def test_frozen_v10280_approval_is_preserved_not_rewritten(self):
        legacy = json.loads(self.frozen_v10280.read_text(encoding="utf-8"))
        self.assertEqual(legacy["scope"], "v10.28.0_p1_source_only_read_ranges")
        self.assertEqual(legacy["version"], "10.28.0")
        self.assertEqual(legacy["migrations"][0]["candidate_sha256"],
                         "47177e0208cb4a4993efdb189126e76ff2503cb079b7bf9fcfd6237f16c76cc1")
        self.assertEqual(legacy["migrations"][0]["old_ranges"], [[416, 416], [419, 430]])
        self.assertEqual(legacy["migrations"][0]["new_ranges"], [[424, 424], [427, 438]])
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10280)

    def test_v10290_source_migration_remains_immutable(self):
        legacy = json.loads(self.frozen_v10290.read_text(encoding="utf-8"))
        self.assertEqual(legacy["scope"], "v10.29.0_p2_exact_literature_intake_migration")
        self.assertEqual(legacy["version"], "10.29.0")
        self.assertEqual(legacy["migrations"][0]["candidate_sha256"],
                         "0428f7cc4fd52009b43e9f2071d818bcb091dcadcba8d171b202129e93464311")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10290)

    def test_v10300_source_migration_remains_immutable(self):
        previous = json.loads(self.frozen_v10300.read_text(encoding="utf-8"))
        self.assertEqual(previous["scope"], "v10.30.0_p3_metadata_only_adapter_carrier")
        self.assertEqual(previous["version"], "10.30.0")
        self.assertEqual(previous["migrations"][0]["candidate_sha256"],
                         "7d6ce78333078ecc08d4751248c53e694a9a737b455c1d4fe0fb9c6cda39872e")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10300)

    def test_v10310_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10310.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.31.0_p4_optional_research_snapshot_carrier")
        self.assertEqual(prior["version"], "10.31.0")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "cddf0099e6d1353af0b522006dbb30c0e9bd4b098f931e5955fd52cb3c3a4a24")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10310)

    def test_v10320_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10320.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.32.0_p6_maintenance_only_eval_carrier")
        self.assertEqual(prior["version"], "10.32.0")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "2fd8706d2413068e2e5443c9ea478aa7daaab395ce567ea395a38e5d8a38fc66")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10320)

    def test_v10321_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10321.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.32.1_preprocessing_redelivery")
        self.assertEqual(prior["version"], "10.32.1")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "b019e1f70439ef9c78a9fa46c5e902e9fff1c6b7cca514725460114ffd1ffd0d")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10321)

    def test_v10322_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10322.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.32.2_question_delivery_scope")
        self.assertEqual(prior["version"], "10.32.2")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "66e720144171471a4a1b4c9db5abef60e60ca807e4453a4f98ab85ee34f3c199")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10322)

    def test_v10330_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10330.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.33.0_upstream_dependency_diagnostics")
        self.assertEqual(prior["version"], "10.33.0")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "5ba885794caeaa59eaaba1523cca3164e1921ff8b8bd593b6eb13e8478273f70")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10330)

    def test_v10340_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10340.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.34.0_primary_quality_approval_binding")
        self.assertEqual(prior["version"], "10.34.0")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "d311599dafb2fcfcbf88a56301233d19692497368cd3e91c28314451ebf6f41c")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10340)

    def test_v10350_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10350.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.35.0_execution_scale_commitments")
        self.assertEqual(prior["version"], "10.35.0")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "f40471fa5a19753167d8b4b085423fd030f86ecf568f2d043c363f13a66ecdfb")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10350)

    def test_v10351_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10351.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.35.1_ordinary_analysis_coverage")
        self.assertEqual(prior["version"], "10.35.1")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "36e633857d349a1b60fb1be20d5027ac4b52b8bffbfa270caa4574deca7b5b12")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10351)

    def test_v10352_approval_source_spans_remain_frozen(self):
        prior = json.loads(self.frozen_v10352.read_text(encoding="utf-8"))
        self.assertEqual(prior["scope"], "v10.35.2_affirmative_full_workflow")
        self.assertEqual(prior["version"], "10.35.2")
        self.assertEqual(prior["migrations"][0]["candidate_sha256"],
                         "4b27e6cecbfe84cf5ba41e9e4678b7423cb668ef87c623e65a1c022006572ca4")
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10352)

    def test_v10353_release_migration_remains_frozen(self):
        self.assertEqual(self.measurement.digest(self.frozen_v10353.read_bytes()),
                         '01fd0de70c1d96623a1aec114e3bd4d4dd811f08699d4b96e409cbb88303d41c')
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10353)

    def test_v11_original_candidate_remains_frozen_and_rejected_after_release(self):
        original = json.loads(self.frozen_v11.read_text(encoding="utf-8"))
        self.assertEqual(original["version"], "11.0.0")
        self.assertEqual(original["scope"], "v11_candidate_legacy_stage_scoped_spans")
        # A new Skill release cannot inherit source-byte approval for v11.0.0.
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v11)

    def test_v1110_release_w1_w2_fixtures_remain_frozen(self):
        for path, expected_scope in (
            (self.frozen_v1110, "v11_1_0_release_legacy_stage_scoped_spans"),
            (self.frozen_w1_draft, "v11_1_0_writing_draft_legacy_stage_scoped_spans"),
            (self.frozen_w2, "v11_1_0_w2_numeric_display_source_spans"),
        ):
            previous = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(previous["scope"], expected_scope)
            self.assertEqual(previous["version"], "11.1.0")
            with self.assertRaisesRegex(ValueError, "source span migration candidate bytes changed"):
                self.measurement.approved_source_span_migrations(path)

        w2 = json.loads(self.frozen_w2.read_text(encoding="utf-8"))
        current = self.measurement.approved_source_span_migrations(self.fixture)
        self.assertEqual(current["scope"], "v11_1_0_w3_proposition_cap_source_spans")
        for field in ("required_case_ids", "model_intake", "pqs_full_source_spans"):
            self.assertEqual(current[field], w2[field])
        self.assertEqual(current["migrations"][:3], w2["migrations"][:3])
        design = current["migrations"][-1]
        self.assertEqual(design["path"], "modules/02_model_design.md")
        self.assertEqual(design["candidate_sha256"], "ca5c299e4cbeea9caff80fbbaba2e3711262081ffe258ef5ca51e0ee7fcaf306")
        self.assertEqual(design["new_ranges"], [[1, 715]])
        self.assertEqual(current["output_read_shift"]["cases"][0]["current_ranges"], [[468, 514]])
        self.assertEqual(current["output_read_shift"]["cases"][1]["current_ranges"], [[1, 637]])
        self.assertEqual(current["output_conditional_shift"]["current_ranges"], [[1, 637]])
        self.assertEqual(current["output_read_shift"]["candidate_sha256"], "11a647712355a29de942062fa26c09d21baa5bfe3360c79df90d34021a78be05")
        protocol = next(x for x in current["legacy_profile_read_shifts"]
                        if x["path"] == "modules/05_writing/paper_writing_protocol.md")
        self.assertEqual(protocol["candidate_sha256"], "09994c876bc02cacd320d6898429eb95e4e2c095cb2900739dc815ab8deb0094")
        self.assertEqual(protocol["spans"][1]["after"], [[1, 763]])
        reasoning = current["legacy_profile_read_shifts"][-1]
        self.assertEqual(reasoning["candidate_sha256"], "56246364a74bb8a5ec014d1882e9ae2ad12f13d183815a0f5ee6f6a9a029c2e6")
        self.assertEqual(reasoning["spans"], [{"before": [[1, 1950]], "after": [[1, 1729]]}])
        cleanup = next(x for x in current["legacy_profile_read_shifts"]
                       if x["path"] == "modules/05_writing/ai_cleanup.md")
        self.assertEqual(cleanup["candidate_sha256"],
                         "10f5e9b6c8a315bb888893eca03fecb9a772a0f4397cedbee669e8b2014fecf6")
        self.assertEqual(cleanup["spans"], [{"before": [[1, 51]], "after": [[1, 52]]}])

    def test_writing_draft_cleanup_g2_full_read_projects_only_pinned_span(self):
        fixture = self.measurement.approved_source_span_migrations(self.fixture)
        approvals = self.measurement.approved_changes(
            ROOT / "tests/fixtures/v10270_g2_approved_deltas.json")
        case_id = "natural_language_two_actions_probe"
        transition = next(row for row in approvals
                          if row["case_id"] == case_id and row["path"] == "read_now")
        rule = next(row for row in fixture["legacy_profile_read_shifts"]
                    if row["path"] == "modules/05_writing/ai_cleanup.md")
        approved_row = next(row for row in transition["after"] if row["path"] == rule["path"])
        self.assertEqual(approved_row["ranges"], [[1, 51]])
        self.assertEqual(rule["spans"], [{"before": [[1, 51]], "after": [[1, 52]]}])
        current = {**approved_row, "ranges": [[1, 52]]}
        old = {
            "id": case_id,
            "behavior": {"read_now": deepcopy(transition["before"])},
            "source_identity": {"sources": [{"path": rule["path"],
                                            "sha256": rule["baseline_sha256"]}]},
        }
        new = {
            "id": case_id,
            "behavior": {"read_now": [deepcopy(current)]},
            "source_identity": {"sources": [{"path": rule["path"],
                                            "sha256": rule["candidate_sha256"]}]},
        }
        observed = deepcopy(new["behavior"])
        evidence = self.measurement._project_approved_read_spans(
            old, new, observed, [rule], {"read_now": transition})
        self.assertEqual(observed["read_now"], [approved_row])
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["group"], "read_now")
        self.assertEqual(evidence[0]["source_sha256"], rule["candidate_sha256"])
        self.assertEqual(new["behavior"]["read_now"], [current])

        changed = deepcopy(new)
        changed["behavior"]["read_now"][0]["selectors"] = {"yaml_paths": ["unapproved"]}
        observed = deepcopy(changed["behavior"])
        evidence = self.measurement._project_approved_read_spans(
            old, changed, observed, [rule], {"read_now": transition})
        self.assertEqual(evidence, [])
        self.assertEqual(observed, changed["behavior"])

        changed = deepcopy(new)
        changed["source_identity"]["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source span identity drift"):
            self.measurement._project_approved_read_spans(
                old, changed, deepcopy(changed["behavior"]), [rule],
                {"read_now": transition})

    def test_writing_draft_reasoning_range_projects_only_exact_identity(self):
        fixture, old, new = self.cases()
        rule = fixture["legacy_profile_read_shifts"][-1]
        original = {"origin": "skill", "path": rule["path"],
                    "resolution": "exact", "ranges": [[1, 1950]],
                    "selectors": {}, "when": None}
        current = {**original, "ranges": [[1, 1729]]}
        for case, row, key in ((old, original, "baseline_sha256"),
                               (new, current, "candidate_sha256")):
            case["behavior"]["read_now"].append(deepcopy(row))
            case["source_identity"]["sources"].append({"path": rule["path"], "sha256": rule[key]})
        projected, _ = self.measurement.project_exact_approved_source_spans(old, new, fixture)
        self.assertEqual(projected["read_now"][-1], original)
        new["behavior"]["read_now"][-1]["selectors"] = {"yaml_paths": ["unreviewed"]}
        projected, _ = self.measurement.project_exact_approved_source_spans(old, new, fixture)
        self.assertEqual(projected["read_now"][-1], new["behavior"]["read_now"][-1])
        new["source_identity"]["sources"][-1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source span identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def cases(self):
        manifest = self.measurement.approved_source_span_migrations(self.fixture)
        before = {"id": "pure_model_design", "behavior": {"read_now": [], "load_order": []},
                  "source_identity": {"skill_version": "10.27.0", "sources": []}}
        after = {"id": "pure_model_design", "behavior": {"read_now": [], "load_order": []},
                 "source_identity": {"skill_version": "11.1.0", "sources": []}}
        for item in manifest["migrations"]:
            original = {
                "origin": "skill", "path": item["path"],
                "ranges": deepcopy(item["old_ranges"]),
                "selectors": {}, "when": None, "resolution": "exact",
            }
            current = deepcopy(original)
            current["ranges"] = deepcopy(item["new_ranges"])
            before["behavior"]["read_now"].append(original)
            after["behavior"]["read_now"].append(current)
            before["source_identity"]["sources"].append({
                "path": item["path"], "sha256": item["baseline_sha256"]})
            after["source_identity"]["sources"].append({
                "path": item["path"], "sha256": item["candidate_sha256"]})
        for item in manifest["model_intake"]["resources"]:
            path = item["path"]
            after["behavior"]["load_order"].append(path)
            after["behavior"]["read_now"].append({
                "origin": "skill", "path": path,
                "ranges": deepcopy(item["ranges"]),
                "selectors": {}, "when": None, "resolution": "exact",
            })
        return manifest, before, after

    def test_exact_current_bytes_and_spans_project_without_mutating_actual_evidence(self):
        fixture, old, new = self.cases()
        self.assertEqual(fixture["version"], "11.1.0")
        preserved = deepcopy(new)
        projected, evidence = self.measurement.project_exact_approved_source_spans(
            old, new, fixture)
        self.assertEqual(projected["read_now"], old["behavior"]["read_now"])
        self.assertEqual(new, preserved)
        self.assertEqual(len(evidence), 6)
        self.assertTrue(all(entry["source_sha256"] for entry in evidence))

    def test_pqs_full_extent_projection_preserves_other_read_semantics(self):
        fixture, old, new = self.cases()
        rule = fixture["pqs_full_source_spans"][0]
        before = {
            "origin": "skill", "path": rule["path"], "ranges": [[1, rule["old_last_line"]]],
            "selectors": {"yaml_paths": ["solver_backends"]}, "when": None, "resolution": "exact",
        }
        after = {**before, "ranges": [[1, rule["new_last_line"]]]}
        for case, row, hash_key in ((old, before, "baseline_sha256"), (new, after, "candidate_sha256")):
            case["behavior"]["read_now"].append(row)
            case["source_identity"]["sources"].append({"path": rule["path"], "sha256": rule[hash_key]})
        saved = deepcopy(new)
        projected, evidence = self.measurement.project_exact_approved_source_spans(old, new, fixture)
        self.assertEqual(projected["read_now"][-1], before)
        self.assertEqual(new, saved)
        self.assertEqual(evidence[-1]["group"], "read_now")

        new["behavior"]["read_now"][-1]["selectors"] = {"yaml_paths": ["unreviewed"]}
        projected, _ = self.measurement.project_exact_approved_source_spans(old, new, fixture)
        self.assertEqual(projected["read_now"][-1]["ranges"], [[1, rule["new_last_line"]]])
        new["source_identity"]["sources"][-1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source span identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_full_span_restores_an_exact_g2_added_read(self):
        fixture = self.measurement.approved_source_span_migrations(self.fixture)
        approvals = self.measurement.approved_changes(
            ROOT / "tests/fixtures/v10270_g2_approved_deltas.json")
        case_id = "natural_language_two_actions_probe"
        transition = next(item for item in approvals
                          if item["case_id"] == case_id and item["path"] == "read_now")
        rule = next(item for item in fixture["pqs_full_source_spans"]
                    if item["path"] == "core/workbook_schema.yaml")
        old = {"id": case_id, "behavior": {"read_now": deepcopy(transition["before"])},
               "source_identity": {"sources": []}}
        approved_row = next(item for item in transition["after"] if item["path"] == rule["path"])
        candidate_row = {**approved_row, "ranges": [[1, rule["new_last_line"]]]}
        candidate = {"id": case_id, "behavior": {"read_now": [candidate_row]},
                     "source_identity": {"sources": []}}
        observed = deepcopy(candidate["behavior"])
        evidence = self.measurement._project_approved_read_spans(
            old, candidate, observed, [rule], {"read_now": transition},
        )
        self.assertEqual(observed["read_now"], [approved_row])
        self.assertEqual(evidence[0]["group"], "read_now")
        self.assertEqual(candidate["behavior"]["read_now"][0]["ranges"], [[1, rule["new_last_line"]]])

        old["behavior"]["read_now"].append({"path": "unreviewed.md"})
        observed = deepcopy(candidate["behavior"])
        evidence = self.measurement._project_approved_read_spans(
            old, candidate, observed, [rule], {"read_now": transition},
        )
        self.assertEqual(evidence, [])
        self.assertEqual(observed, candidate["behavior"])

    def test_reject_changed_ranges_even_if_source_sha_matches(self):
        fixture, old, new = self.cases()
        new["behavior"]["read_now"][0]["ranges"] = [[1, 999]]
        with self.assertRaisesRegex(ValueError, "physical span drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_reject_changed_selector_or_unauthorized_source_provenance(self):
        fixture, old, new = self.cases()
        new["behavior"]["read_now"][0]["selectors"] = {"yaml_paths": ["wrong"]}
        with self.assertRaisesRegex(ValueError, "reading semantics"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)
        _, old, new = self.cases()
        new["source_identity"]["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_literature_intake_must_have_exact_pair_and_no_out_of_scope_leak(self):
        fixture, old, new = self.cases()
        new["behavior"]["load_order"].remove("core/literature_research_contract.yaml")
        with self.assertRaisesRegex(ValueError, "literature intake load identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)
        _, old, new = self.cases()
        new["id"] = "pure_python_figures"
        with self.assertRaisesRegex(ValueError, "literature intake escaped"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_exact_output_read_shift_and_prohibited_selector_drift(self):
        fixture, before, after = self.cases()
        before["id"] = after["id"] = "review_word_readonly"
        lit = {row["path"] for row in fixture["model_intake"]["resources"]}
        after["behavior"]["load_order"] = [
            p for p in after["behavior"]["load_order"] if p not in lit
        ]
        after["behavior"]["read_now"] = [
            row for row in after["behavior"]["read_now"] if row["path"] not in lit
        ]
        shift = fixture["output_read_shift"]
        sample = shift["cases"][0]
        row = {"origin": "skill", "path": shift["path"],
               "ranges": deepcopy(sample["current_ranges"]),
               "selectors": deepcopy(sample["selectors"]), "when": None,
               "resolution": "exact"}
        after["behavior"]["read_now"].append(row)
        before["behavior"]["read_now"].append({
            **deepcopy(row), "ranges": deepcopy(sample["historical_ranges"]),
        })
        after["source_identity"]["sources"].append({
            "path": shift["path"], "sha256": shift["candidate_sha256"],
        })
        # review_word_readonly also consumes the conditional output scope.
        # Construct the complete, separately pinned source read before
        # verifying the targeted read_now selector. Do not weaken the
        # production fail-closed conditional-read check for an incomplete test.
        conditional = fixture["output_conditional_shift"]
        self.assertIn("review_word_readonly", conditional["case_ids"])
        self.assertEqual(conditional["path"], shift["path"])
        self.assertEqual(conditional["candidate_sha256"], shift["candidate_sha256"])
        conditional_now = {
            "path": conditional["path"],
            "ranges": deepcopy(conditional["current_ranges"]),
            "selectors": {}, "when": conditional["when"],
            "origin": "skill", "resolution": "exact",
        }
        after["behavior"]["conditional"] = [conditional_now]
        before["behavior"]["conditional"] = [{
            **deepcopy(conditional_now),
            "ranges": deepcopy(conditional["historical_ranges"]),
        }]
        saved = deepcopy(after)
        projected, records = self.measurement.project_exact_approved_source_spans(
            before, after, fixture)
        self.assertEqual(projected["read_now"], before["behavior"]["read_now"])
        self.assertEqual(projected["conditional"], before["behavior"]["conditional"])
        self.assertEqual(after, saved)
        self.assertTrue(any(x.get("case_id") == "review_word_readonly" for x in records))
        after["behavior"]["read_now"][-1]["selectors"] = {}
        with self.assertRaisesRegex(ValueError, "output read shift physical span or selector drift"):
            self.measurement.project_exact_approved_source_spans(before, after, fixture)
        after["behavior"]["read_now"][-1]["selectors"] = deepcopy(sample["selectors"])
        after["behavior"]["conditional"].clear()
        with self.assertRaisesRegex(ValueError, "conditional output source span or selector drift"):
            self.measurement.project_exact_approved_source_spans(before, after, fixture)

    def test_p4_conditional_output_range_requires_exact_source_and_selector(self):
        fixture, old, new = self.cases()
        old["id"] = new["id"] = "pure_python_figures"
        literature = {row["path"] for row in fixture["model_intake"]["resources"]}
        new["behavior"]["load_order"] = [
            item for item in new["behavior"]["load_order"] if item not in literature
        ]
        new["behavior"]["read_now"] = [
            item for item in new["behavior"]["read_now"] if item["path"] not in literature
        ]
        rule = fixture["output_conditional_shift"]
        row = {"path": rule["path"], "ranges": deepcopy(rule["current_ranges"]),
               "selectors": {}, "when": rule["when"], "origin": "skill", "resolution": "exact"}
        old["behavior"]["conditional"] = [
            {**deepcopy(row), "ranges": deepcopy(rule["historical_ranges"])}]
        new["behavior"]["conditional"] = [row]
        new["source_identity"]["sources"].append({
            "path": rule["path"], "sha256": rule["candidate_sha256"]})
        original = deepcopy(new)
        projected, evidence = self.measurement.project_exact_approved_source_spans(
            old, new, fixture)
        self.assertEqual(projected["conditional"], old["behavior"]["conditional"])
        self.assertEqual(new, original)
        self.assertTrue(any(x.get("actual_conditional_ranges") for x in evidence))
        new["behavior"]["conditional"][0]["when"] = "wrong_condition"
        with self.assertRaisesRegex(ValueError, "conditional output source span or selector drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_candidate_scoped_section_requires_the_same_selector_and_hash(self):
        fixture, old, new = self.cases()
        rule = next(item for item in fixture["legacy_profile_read_shifts"]
                    if item["path"] == "modules/05_writing/paper_writing_protocol.md")
        span = next(span for span in rule["spans"] if span["before"] == [[1, 6], [174, 218]])
        old_row = {"origin": "skill", "path": rule["path"], "resolution": "exact",
                   "ranges": span["before"], "when": "current_cumcm_modular_latex_review",
                   "selectors": {"headings": ["## 5A. Cross-File Chapter Handoff"]}}
        new_row = {**old_row, "ranges": span["after"]}
        for case, row, key in ((old, old_row, "baseline_sha256"), (new, new_row, "candidate_sha256")):
            case["behavior"]["conditional"] = [deepcopy(row)]
            case["source_identity"]["sources"].append({"path": rule["path"], "sha256": rule[key]})
        projected, _ = self.measurement.project_exact_approved_source_spans(old, new, fixture)
        self.assertEqual(projected["conditional"], [old_row])
        for field, value in (("selectors", {}), ("when", "wrong_condition"),
                             ("ranges", [[1, 1]])):
            with self.subTest(field=field):
                altered = deepcopy(new)
                altered["behavior"]["conditional"][0][field] = value
                projected, _ = self.measurement.project_exact_approved_source_spans(old, altered, fixture)
                self.assertEqual(projected["conditional"], altered["behavior"]["conditional"])
        new["source_identity"]["sources"][-1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source span identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_w3_state_schema_span_projects_direct_conditional_and_g2_reads(self):
        fixture = self.measurement.approved_source_span_migrations(self.fixture)
        path = "core/project_state.schema.yaml"
        rule = next(item for item in fixture["legacy_profile_read_shifts"]
                    if item["path"] == path)
        self.assertEqual(rule, {
            "path": path,
            "baseline_sha256": "348e981de6a66f028f742e56f9e0cd872567baf685b4f507ff62cfff435ccd73",
            "candidate_sha256": "5ab0e1b5897e70e2ce04d1de7f684a6003d9a97ad1e45201e734ae5360c722c1",
            "spans": [{"before": [[1, 2055]], "after": [[1, 2059]]}],
        })
        approvals = self.measurement.approved_changes(
            ROOT / "tests/fixtures/v10270_g2_approved_deltas.json")
        mixed_id = "natural_language_two_actions_probe"
        transition = next(item for item in approvals
                          if item["case_id"] == mixed_id and item["path"] == "read_now")
        for case_id, group, when in (
            ("pure_model_design", "read_now", None),
            ("full_workflow_boundary", "read_now", None),
            ("analysis_stage_request", "read_now", None),
            ("pure_python_figures", "conditional", "machine_gate_or_state_conflict_needs_field_definition"),
            ("two_carrier_legacy_protected", "conditional", "machine_gate_or_state_conflict_needs_field_definition"),
            ("explicit_figure_scope", "conditional", "machine_gate_or_state_conflict_needs_field_definition"),
            (mixed_id, "read_now", None),
        ):
            with self.subTest(case_id=case_id, group=group):
                historical = {"origin": "skill", "path": path, "ranges": [[1, 2055]],
                              "resolution": "exact", "selectors": {}, "when": when}
                current = {**historical, "ranges": [[1, 2059]]}
                if case_id == mixed_id:
                    self.assertIn(historical, transition["after"])
                    prior_rows = deepcopy(transition["before"])
                    read_approvals = {group: transition}
                else:
                    prior_rows = [deepcopy(historical)]
                    read_approvals = {}
                old = {"id": case_id, "behavior": {group: prior_rows},
                       "source_identity": {"sources": [
                           {"path": path, "sha256": rule["baseline_sha256"]}]}}
                new = {"id": case_id, "behavior": {group: [deepcopy(current)]},
                       "source_identity": {"sources": [
                           {"path": path, "sha256": rule["candidate_sha256"]}]}}
                saved = deepcopy(new)
                observed = deepcopy(new["behavior"])
                evidence = self.measurement._project_approved_read_spans(
                    old, new, observed, [rule], read_approvals)
                self.assertEqual(observed[group], [historical])
                self.assertEqual(new, saved)
                self.assertEqual(len(evidence), 1)
                self.assertEqual(evidence[0]["group"], group)
                self.assertEqual(evidence[0]["actual_ranges"], [[1, 2059]])
                self.assertEqual(evidence[0]["historical_ranges"], [[1, 2055]])
                self.assertEqual(evidence[0]["source_sha256"], rule["candidate_sha256"])

                for field, value in (("selectors", {"yaml_paths": ["unreviewed"]}),
                                     ("when", "unreviewed"), ("ranges", [[1, 2058]])):
                    altered = deepcopy(new)
                    altered["behavior"][group][0][field] = value
                    observed = deepcopy(altered["behavior"])
                    evidence = self.measurement._project_approved_read_spans(
                        old, altered, observed, [rule], read_approvals)
                    self.assertEqual(observed, altered["behavior"])
                    self.assertEqual(evidence, [])

                for identities in ([], [{"path": path, "sha256": "0" * 64}]):
                    altered = deepcopy(new)
                    altered["source_identity"]["sources"] = identities
                    with self.assertRaisesRegex(ValueError, "source span identity drift"):
                        self.measurement._project_approved_read_spans(
                            old, altered, deepcopy(altered["behavior"]), [rule], read_approvals)

    def test_w3_state_schema_manifest_rejects_missing_partial_and_wrong_hash(self):
        original = json.loads(self.fixture.read_text(encoding="utf-8"))
        path = "core/project_state.schema.yaml"
        for mutation, message in (
            ("missing", "legacy profile source paths differ"),
            ("partial", "W3 State Schema must bind the exact full source extent"),
            ("hash", "legacy profile candidate bytes changed"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                data = deepcopy(original)
                rules = data["legacy_profile_read_shifts"]
                rule = next(item for item in rules if item["path"] == path)
                if mutation == "missing":
                    rules.remove(rule)
                elif mutation == "partial":
                    rule["spans"][0]["after"] = [[1, 2058]]
                else:
                    rule["candidate_sha256"] = "0" * 64
                snapshot = Path(folder) / "candidate.json"
                snapshot.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    self.measurement.approved_source_span_migrations(snapshot)

    def test_w3_snapshot_rejects_mutated_authority_identity(self):
        manifest = self.measurement.approved_source_span_migrations(self.fixture)
        rule = next(x for x in manifest["legacy_profile_read_shifts"]
                    if x["path"] == "core/writing_reasoning_contract.yaml")
        self.assertEqual(rule["candidate_sha256"], "56246364a74bb8a5ec014d1882e9ae2ad12f13d183815a0f5ee6f6a9a029c2e6")
        mutated = json.loads(self.fixture.read_text(encoding="utf-8"))
        next(x for x in mutated["legacy_profile_read_shifts"]
             if x["path"] == "core/writing_reasoning_contract.yaml")["candidate_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as root:
            snapshot = Path(root) / "candidate.json"
            snapshot.write_text(json.dumps(mutated), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "legacy profile candidate bytes changed"):
                self.measurement.approved_source_span_migrations(snapshot)

    def test_manifest_fails_if_candidate_source_bytes_or_paths_change(self):
        data = json.loads(self.fixture.read_text(encoding="utf-8"))
        data["migrations"][0]["candidate_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "span.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
                self.measurement.approved_source_span_migrations(p)
        data["migrations"][0]["path"] = "core/unrelated.yaml"
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "span.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved sources"):
                self.measurement.approved_source_span_migrations(p)


if __name__ == "__main__":
    unittest.main()
