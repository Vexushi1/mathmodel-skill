from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_indexes as GENERATOR


class LifecycleNavigationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "core").mkdir()
        (self.root / "core/bootstrap.yaml").write_text("skill_version: 10.22.0\n", encoding="utf-8")
        self.router_path = self.root / "core/workflow_router.yaml"
        self.writing_path = self.root / "core/writing_runtime_contract.yaml"
        self.router = {
            "reading_policy": {
                "common_reads": [{"path": "core/bootstrap.yaml"}],
                "profiles": {"independent_profile_name": {
                    "read_now": [{"path": "modules/profile.md"}],
                }},
            },
            "routing": {
                "new_solve_route": {
                    "load": ["modules/source.md"],
                    "then": ["packs/artifact/code.md"],
                    "boundary_roles": ["primary_execution"],
                    "pause_for_user_execution": True,
                    "pre_delivery_gates": ["gate_value_must_stay_at_its_authority"],
                },
            },
            "runtime_segments": {
                "pending_numeric": {
                    "role": "primary_execution", "canonical_route": "new_solve_route",
                    "stage_module": "solve_validate", "stop_before_module": "result_analysis",
                    "pause_state": "awaiting_fixture_execution",
                    "satisfied_when": {"any": ["fixture_accepted_value_is_not_qualification"]},
                    "required_load": ["modules/source.md"],
                    "pre_delivery_gates": ["another_original_gate_value"],
                },
            },
            "project_memory_contract": {
                "project_file": "当前框架.md", "numeric_fact_source": "accepted_workbooks",
                "machine_state_source": "state/project_state.yaml",
                "read_before_modules": ["solve_validate"],
                "targeted_read_sections": ["relevant_question"],
                "full_read_when": ["cross_chat_handoff"],
            },
        }
        self.writing = {"template_first_progressive_authoring": {"stages": [
            {"id": "fixture_chapter", "read_now": ["modules/chapter.md"]},
        ]}}
        self.write_sources()
        patcher = mock.patch.multiple(
            GENERATOR, ROOT=self.root, BOOTSTRAP=self.root / "core/bootstrap.yaml",
            SKILL_INDEX=self.root / "SKILL_FILE_INDEX.md",
            TEMPLATE_INDEX=self.root / "TEMPLATE_INDEX.md",
            LEGACY_SKILL_INDEX=self.root / "HSK_SKILL_FILE_INDEX_V622.md",
            LEGACY_TEMPLATE_INDEX=self.root / "HSK_TEMPLATE_INDEX_V622.md",
            MANIFEST=self.root / "MANIFEST.sha256",
            STAGE_GUIDE=self.root / "core/stage_reading_guide.md",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_sources(self):
        self.router_path.write_text(yaml.safe_dump(self.router, sort_keys=False), encoding="utf-8")
        self.writing_path.write_text(yaml.safe_dump(self.writing, sort_keys=False), encoding="utf-8")

    def test_new_route_and_boundary_are_derived_without_a_second_registry(self):
        original = GENERATOR.stage_reading_guide_text()
        self.router["routing"]["later_route"] = {
            "load": ["modules/later.md"], "boundary_roles": ["later_role"],
            "conditional_stage": {
                "when": "fixture_decision == shared", "module": "shared_preprocessing",
                "insert_before": "modules/later.md", "pause_state": "awaiting_shared_fixture",
            },
            "load_classified_task_packs": True,
            "load_competition_pack": True,
        }
        self.router["runtime_segments"]["later_boundary"] = {
            "role": "later_role", "canonical_route": "later_route",
            "stage_module": "later_module", "stop_before_module": "final_stage",
        }
        self.write_sources()
        updated = GENERATOR.stage_reading_guide_text()
        self.assertNotIn("#routing.later_route", original)
        self.assertIn("core/workflow_router.yaml#routing.later_route", updated)
        self.assertIn("core/workflow_router.yaml#runtime_segments.later_boundary", updated)
        self.assertIn("fixture_decision == shared", updated)
        self.assertIn("awaiting_shared_fixture", updated)
        self.assertIn("load_classified_task_packs=`true`", updated)
        self.assertIn("load_competition_pack=`true`", updated)
        # Raw resources stay in the original route, not a duplicated read-set.
        self.assertNotIn("modules/later.md", updated.replace("insert_before=`modules/later.md`", ""))

    def test_recovery_changes_follow_the_current_memory_authority(self):
        first = GENERATOR.stage_reading_guide_text()
        self.router["project_memory_contract"]["full_read_when"] = ["fresh_recovery_event"]
        self.router["project_memory_contract"]["project_file"] = "修订后的框架.md"
        self.router["project_memory_contract"]["numeric_fact_source"] = "accepted_numeric_fixture"
        self.write_sources()
        changed = GENERATOR.stage_reading_guide_text()
        self.assertIn("cross_chat_handoff", first)
        self.assertNotIn("cross_chat_handoff", changed)
        for expected in ("fresh_recovery_event", "修订后的框架.md", "accepted_numeric_fixture"):
            self.assertIn(expected, changed)
        self.assertIn("does not detect context compression", changed.replace("\n", " "))

    def test_generation_keeps_pause_gates_and_evidence_conditions_at_the_authority(self):
        before = {path: path.read_bytes() for path in (self.router_path, self.writing_path)}
        declared = copy.deepcopy(self.router)
        guide = GENERATOR.stage_reading_guide_text()
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.assertEqual(yaml.safe_load(self.router_path.read_text(encoding="utf-8")), declared)
        self.assertIn("awaiting_fixture_execution", guide)
        self.assertNotIn("gate_value_must_stay_at_its_authority", guide)
        self.assertNotIn("another_original_gate_value", guide)
        self.assertNotIn("fixture_accepted_value_is_not_qualification", guide)
        self.assertIn("not the effective `read_now`", guide)
        self.assertIn("`reading_plan.reasons`", guide)
        self.assertIn("do not invent resolver output", guide)
        self.assertIn("does not compute a profile or a gate list", guide)
        self.assertIn("### independent_profile_name", guide)
        self.assertIn("### fixture_chapter", guide)

    def test_existing_route_names_are_not_assumed_to_be_profile_names(self):
        self.router["routing"] = {"figures": {"load": ["modules/figure.md"]}}
        self.write_sources()
        guide = GENERATOR.stage_reading_guide_text()
        row = next(line for line in guide.splitlines() if line.startswith("| `figures` |"))
        self.assertIn("#routing.figures", row)
        self.assertNotIn("independent_profile_name", row)
        self.assertNotIn("full", row)

    def test_old_root_without_lifecycle_sections_retains_existing_guide_surfaces(self):
        for key in ("routing", "runtime_segments", "project_memory_contract"):
            self.router.pop(key)
        self.write_sources()
        guide = GENERATOR.stage_reading_guide_text()
        self.assertNotIn("## Whole-workflow navigation", guide)
        for heading in ("## Common source selectors", "## Routing profiles", "## CUMCM writing stages"):
            self.assertIn(heading, guide)
        self.assertIn("### independent_profile_name", guide)
        self.assertIn("### fixture_chapter", guide)

    def test_absent_lifecycle_sections_are_independently_compatible(self):
        for retained in ("routing", "runtime_segments", "project_memory_contract"):
            with self.subTest(retained=retained):
                router = {"reading_policy": self.router["reading_policy"], retained: self.router[retained]}
                self.router_path.write_text(yaml.safe_dump(router), encoding="utf-8")
                self.assertIn("## Whole-workflow navigation", GENERATOR.stage_reading_guide_text())

    def test_registered_root_derives_current_routes_segments_and_recovery_events(self):
        (self.root / "core/bootstrap.yaml").write_text(
            "skill_version: 10.22.0\nauthoritative_sources:\n  routing: core/workflow_router.yaml\n",
            encoding="utf-8",
        )
        before = GENERATOR.stage_reading_guide_text()
        self.router["routing"]["registered_later_route"] = {"load": ["modules/later.md"]}
        self.router["runtime_segments"]["registered_later_boundary"] = {"stage_module": "later_stage"}
        self.router["project_memory_contract"]["full_read_when"] = ["registered_recovery_change"]
        self.write_sources()
        after = GENERATOR.stage_reading_guide_text()
        for key in ("#routing.registered_later_route", "#runtime_segments.registered_later_boundary",
                    "registered_recovery_change"):
            self.assertNotIn(key, before)
            self.assertIn(key, after)
        self.assertNotIn("cross_chat_handoff", after)

    def test_registered_router_cannot_lose_or_empty_a_lifecycle_section(self):
        (self.root / "core/bootstrap.yaml").write_text(
            "skill_version: 10.22.0\nauthoritative_sources:\n  routing: core/workflow_router.yaml\n",
            encoding="utf-8",
        )
        for key in ("routing", "runtime_segments", "project_memory_contract"):
            for action in ("remove", "empty"):
                with self.subTest(key=key, action=action):
                    damaged = copy.deepcopy(self.router)
                    if action == "remove":
                        del damaged[key]
                    else:
                        damaged[key] = {}
                    self.router_path.write_text(yaml.safe_dump(damaged), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, f"registered routing.*{key}"):
                        GENERATOR.stage_reading_guide_text()

    def test_missing_bootstrap_keeps_standalone_fake_root_compatibility(self):
        (self.root / "core/bootstrap.yaml").unlink()
        self.assertIn("#routing.new_solve_route", GENERATOR.stage_reading_guide_text())
        for key in ("routing", "runtime_segments", "project_memory_contract"):
            self.router.pop(key)
        self.write_sources()
        guide = GENERATOR.stage_reading_guide_text()
        self.assertIn("### fixture_chapter", guide)
        self.assertNotIn("## Whole-workflow navigation", guide)

    def test_existing_malformed_bootstrap_cannot_hide_registration(self):
        for source in (
            "", "[]\n", "null\n", "authoritative_sources: []\n",
            "authoritative_sources: null\n", "authoritative_sources:\n  routing: null\n",
            "authoritative_sources:\n  routing: ''\n", "authoritative_sources:\n  routing: 7\n",
            "entrypoints: []\n", "entrypoints: null\n", "entrypoints:\n  read_stage: null\n",
            "entrypoints:\n  read_stage: ''\n", "entrypoints:\n  read_stage: 7\n",
            "authoritative_sources: [unterminated\n",
        ):
            with self.subTest(source=source):
                (self.root / "core/bootstrap.yaml").write_text(source, encoding="utf-8")
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    GENERATOR.stage_reading_guide_text()

    def test_present_malformed_lifecycle_sections_fail_instead_of_disappearing(self):
        for key in ("routing", "runtime_segments", "project_memory_contract"):
            for invalid in (None, [], "summary only"):
                with self.subTest(key=key, invalid=invalid):
                    damaged = copy.deepcopy(self.router)
                    damaged[key] = invalid
                    self.router_path.write_text(yaml.safe_dump(damaged), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, key):
                        GENERATOR.stage_reading_guide_text()

    def test_malformed_declared_rows_or_recovery_events_fail_closed(self):
        damaged_routers = []
        for key, value in (
            ("routing", {"invalid_route": None}),
            ("runtime_segments", {"invalid_boundary": []}),
            ("routing", {"invalid_route": {"load": "not a resource list"}}),
            ("routing", {"invalid_route": {"conditional_stage": {"when": "missing target"}}}),
            ("routing", {"invalid_route": {"pause_for_user_execution": "approved"}}),
            ("runtime_segments", {"invalid_boundary": {"satisfied_when": ["accepted"]}}),
            ("runtime_segments", {"invalid_boundary": {"satisfied_when": {"all_groups": ["bad group"]}}}),
        ):
            damaged = copy.deepcopy(self.router)
            damaged[key] = value
            damaged_routers.append(damaged)
        for value in ("not a list", [None]):
            damaged = copy.deepcopy(self.router)
            damaged["project_memory_contract"]["full_read_when"] = value
            damaged_routers.append(damaged)
        damaged = copy.deepcopy(self.router)
        del damaged["project_memory_contract"]["full_read_when"]
        damaged_routers.append(damaged)
        for index, damaged in enumerate(damaged_routers):
            with self.subTest(index=index):
                self.router_path.write_text(yaml.safe_dump(damaged), encoding="utf-8")
                with self.assertRaises(ValueError):
                    GENERATOR.stage_reading_guide_text()

    def test_missing_original_source_cannot_be_presented_as_a_current_guide(self):
        self.writing_path.unlink()
        with self.assertRaises(FileNotFoundError):
            GENERATOR.stage_reading_guide_text()
        # Historical roots without the complete old input pair keep the old
        # generated-output contract and do not invent a replacement guide.
        payloads = GENERATOR.generated_payloads()
        self.assertNotIn(self.root / "core/stage_reading_guide.md", payloads)
        manifest = payloads[self.root / "MANIFEST.sha256"]
        self.assertNotIn("  core/stage_reading_guide.md", manifest)

    def test_registered_body_interface_requires_each_guide_source_before_generation(self):
        (self.root / "core/bootstrap.yaml").write_text(
            "skill_version: 10.22.0\nauthoritative_sources:\n  routing: core/workflow_router.yaml\n"
            "entrypoints:\n  read_stage: python scripts/read_stage.py\n", encoding="utf-8",
        )
        payloads = GENERATOR.generated_payloads()
        guide = payloads[self.root / "core/stage_reading_guide.md"]
        self.assertIn("#routing.new_solve_route", guide)
        self.assertIn("#runtime_segments.pending_numeric", guide)
        self.assertIn("cross_chat_handoff", guide)
        for path in (self.router_path, self.writing_path):
            with self.subTest(missing=path.name):
                self.write_sources()
                path.unlink()
                with self.assertRaisesRegex(FileNotFoundError, f"registered read_stage.*{path.name}"):
                    GENERATOR.generated_payloads()

    def test_historical_routing_registration_without_body_reader_keeps_missing_source_compatibility(self):
        (self.root / "core/bootstrap.yaml").write_text(
            "skill_version: 10.22.0\nauthoritative_sources:\n  routing: core/workflow_router.yaml\n",
            encoding="utf-8",
        )
        for path in (self.router_path, self.writing_path):
            with self.subTest(missing=path.name):
                self.write_sources()
                path.unlink()
                payloads = GENERATOR.generated_payloads()
                self.assertNotIn(self.root / "core/stage_reading_guide.md", payloads)
                self.assertNotIn("  core/stage_reading_guide.md", payloads[self.root / "MANIFEST.sha256"])


if __name__ == "__main__":
    unittest.main()
