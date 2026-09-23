"""A confirmed v10 migration needs a full project, original bytes, and recovery.

The accepted numerical fixture runs the repository's real Python micro solver.
Its Model Approval fields describe this synthetic test model only.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import project_solver_backend as backend
import project_transaction as transaction
import semantic_identity
import validate_model_approval as approval
import validate_model_paper_framework as framework_validator
import validate_project_state as state_validator
from instantiate_model_paper_framework import instantiate
from solver_backend_mixed_smoke import python_primary
from test_project_backend_migration_preview import synthetic_python_analysis
from test_solver_backend_end_to_end import save_state


REASON = "Reviewed whole-project numerical implementation requirements"
SECTION = "### Q1：测试问题"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state(root: Path) -> dict:
    return yaml.safe_load((root / transaction.STATE_RELATIVE_PATH).read_text(encoding="utf-8"))


def project_files(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): digest(path)
            for path in root.rglob("*") if path.is_file()}


def make_unselected_project(root: Path) -> dict:
    """Use every required current Schema field and a validated current framework."""
    root.mkdir(parents=True, exist_ok=True)
    state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
    state["requirements"].update(total=1, completed=["Q1"], pending=[])
    state["data"]["sources"] = [{"name": "fixture", "path": "input.json", "role": "raw input"}]
    state["subproblems"]["Q1"]["framework_section"] = SECTION
    state["paper_framework"]["terminology_registry"] = [
        {"id": "T1", "canonical_term": "测试变量", "definition": "迁移夹具的测试变量", "status": "current"}
    ]
    state["paper_framework"]["numeric_profile"] = [
        {"id": "N1", "metric": "测试指标", "display_form": "decimal", "status": "current"}
    ]
    framework = instantiate(mode="compact")
    framework = framework.replace("### Q1：__QUESTION_NAME__", SECTION)
    framework = framework.replace(
        "| T1 |  |  |  |  |  |  |  |  | current / stale |",
        "| T1 | 测试变量 | 迁移夹具的测试变量 | 无量纲 |  |  |  | x | Q1 | current |",
    ).replace(
        "| N1 |  |  |  | decimal / percent / scientific / interval |  |  |  |  | prompt / official / reviewer / model_resolution |",
        "| N1 | 测试指标 | x | 无量纲 | decimal | 2 | 2 | 2 | 2 | model_resolution |",
    )
    identity = {
        "schema_version": "1.0.0", "question": "Q1", "research_object": "求解标量线性方程",
        "data_scope": [{"id": "D1", "source": "input.json", "role": "原始输入"}],
        "variables": [{"id": "V1", "symbol": "x", "role": "求解变量", "domain": "real"}],
        "parameters": [{"id": "P1", "symbol": "a", "role": "系数"},
                       {"id": "P2", "symbol": "b", "role": "右端项"}],
        "assumptions": [{"id": "A1", "statement": "a 不为零"}],
        "objective": {"kind": "solve", "expression": "a*x=b"},
        "constraints": [{"id": "C1", "expression": "a*x=b"}],
        "preprocessing_decision": "not_needed",
        "algorithm_semantics": {"model_family": "scalar_division", "solver_role": "direct"},
        "dependencies": [],
    }
    sib = ("#### 当前模型口径\n\n<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->\n```yaml\n"
           + yaml.safe_dump(identity, allow_unicode=True, sort_keys=False)
           + "```\n<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->\n")
    framework = framework.replace("#### 当前模型口径\n", sib, 1)
    state["paper_framework"]["sha256"] = framework_validator.sha256_text(framework)
    (root / "模型论文框架.md").write_text(framework, encoding="utf-8")
    shutil.copyfile(ROOT / "tests/fixtures/solver_backends/input.json", root / "input.json")
    save_state(root, state)
    assert state_validator.validate_state_payload(state, project_root=root) == []
    assert framework_validator.validate_framework_text(framework, state=state, project_root=root) == []
    return state


def make_historical_accepted_project(root: Path) -> dict:
    """Retain real 1.1 source/receipt bytes in a complete former stage-choice state."""
    original = make_unselected_project(root)
    current = deepcopy(original)
    current["execution"].update(
        solver_backend="python", solver_backend_selection_reason="Synthetic source execution"
    )
    save_state(root, current)
    python_primary(root, "问题一", False)
    executed = load_state(root)["subproblems"]["Q1"]
    entry = original["subproblems"]["Q1"]
    complete_capabilities = deepcopy(entry["capabilities"])
    complete_capabilities.update(has_explicit_constraints=False,
                                 requires_feasibility_check=False,
                                 requires_equilibrium_residual=True)
    entry.update(executed)
    entry["capabilities"] = complete_capabilities
    entry.update(status="solved", result_summary_status="current", result_summary_anchor=SECTION)
    entry["solver_execution"]["primary"].update(
        backend="python", selection_reason="Historical v9 per-stage choice"
    )
    section_hash = state_validator._framework_section_hash(root / "模型论文框架.md", SECTION)
    entry["artifact_hashes"].update(primary_code=entry["primary_code_sha256"], framework=section_hash)
    entry["validated_artifact_hashes"]["framework"] = section_hash
    inspected = semantic_identity.inspect_question_semantics(
        semantic_identity.question_sections((root / "模型论文框架.md").read_text(encoding="utf-8"))["Q1"], "Q1",
    )
    assert inspected["mode"] == "semantic_identity_v1"
    identity = inspected["semantic_identity_hash"]
    entry.update(
        human_model_approval_status="approved", approved_semantic_revision=entry["semantic_revision"],
        semantic_identity_schema_version="1.0.0", semantic_text_hash=inspected["semantic_text_hash"],
        semantic_identity_hash=identity, validated_semantic_identity_hash=identity,
        approved_semantic_identity_hash=identity,
    )
    assert approval.validate_question("Q1", entry) == []
    save_state(root, original)
    # Legacy stage selectors are intentionally read-only; the same bytes and
    # complete records become current-Schema valid after canonical root selection.
    canonical = deepcopy(original)
    canonical["execution"].update(solver_backend="python", solver_backend_selection_reason=REASON)
    canonical_stage = canonical["subproblems"]["Q1"]["solver_execution"]["primary"]
    canonical_stage.pop("backend")
    canonical_stage.pop("selection_reason")
    assert state_validator.validate_state_payload(canonical, project_root=root) == []
    for target in ("python", "matlab"):
        report = backend.preview_migration(root, target_backend=target, reason=REASON)
        assert report["status"] == "ready_for_review", report["issues"]
    return original


def preview(root: Path, target: str, *, reason: str = REASON) -> dict:
    report = backend.preview_migration(root, target_backend=target, reason=reason)
    assert report["status"] == "ready_for_review", report["issues"]
    return report


def confirmed_kwargs(report: dict) -> dict:
    return dict(
        target_backend=report["target_backend"], reason=report["reason"],
        expected_generation=report["state_snapshot"]["state_generation"],
        expected_state_sha256=report["state_snapshot"]["sha256"],
        confirmed_preview_sha256=report["preview_sha256"],
        confirmed_effects_sha256=report["effects_sha256"],
        confirm_migration=True, migration_id=report["migration_id"],
    )


class CompleteMigrationFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.state = make_unselected_project(self.root)

    def test_unselected_fixture_is_current_schema_and_framework_valid(self):
        self.assertEqual(state_validator.validate_state_payload(load_state(self.root), project_root=self.root), [])
        self.assertEqual(framework_validator.validate_framework_text(
            (self.root / "模型论文框架.md").read_text(encoding="utf-8"),
            state=load_state(self.root), project_root=self.root,
        ), [])
        self.assertNotIn("solver_backend", self.state["execution"])

    def test_preview_binds_exact_state_effects_and_project_without_writing(self):
        before = project_files(self.root)
        report = preview(self.root, "python")
        self.assertEqual(project_files(self.root), before)
        self.assertEqual(report["state_snapshot"]["sha256"], before[transaction.STATE_RELATIVE_PATH])
        self.assertEqual(report["project_root"], str(self.root.resolve()))
        self.assertEqual(report["effects_sha256"], hashlib.sha256(json.dumps(
            report["effects"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest())
        self.assertFalse(report["execution_authorized"])

    def test_explicit_api_commit_archives_raw_state_and_publishes_report_reference(self):
        make_historical_accepted_project(self.root)
        report = preview(self.root, "python")
        old_state = (self.root / transaction.STATE_RELATIVE_PATH).read_bytes()
        old_framework = (self.root / "模型论文框架.md").read_bytes()
        old_input = (self.root / "input.json").read_bytes()
        result = backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(result["status"], "committed")
        saved = load_state(self.root)
        self.assertEqual(saved["project"]["state_generation"], 1)
        self.assertEqual(saved["execution"]["solver_backend"], "python")
        self.assertEqual(state_validator.validate_state_payload(saved, project_root=self.root), [])
        ref = saved["execution"]["backend_migration_history"][-1]
        self.assertEqual(result["archive"], {key: ref[key] for key in ("manifest", "sha256")})
        self.assertEqual(result["report"], ref["report"])
        self.assertEqual(digest(self.root / ref["report"]), ref["report_sha256"])
        transaction.verify_history_archive(self.root, {key: ref[key] for key in ("manifest", "sha256")})
        archive = (self.root / ref["manifest"]).parent / "files"
        self.assertEqual((archive / transaction.STATE_RELATIVE_PATH).read_bytes(), old_state)
        self.assertEqual((archive / "模型论文框架.md").read_bytes(), old_framework)
        self.assertEqual((archive / "input.json").read_bytes(), old_input)
        self.assertFalse(result["execution_authorized"])

    def test_unconfirmed_or_mismatched_digest_cannot_write(self):
        make_historical_accepted_project(self.root)
        report = preview(self.root, "python")
        before = project_files(self.root)
        for change in ({"confirm_migration": False},
                       {"confirmed_preview_sha256": "0" * 64},
                       {"confirmed_effects_sha256": "0" * 64},
                       {"expected_state_sha256": "0" * 64}):
            with self.subTest(change=change):
                kwargs = confirmed_kwargs(report)
                kwargs.update(change)
                with self.assertRaises(backend.ProjectBackendMigrationError):
                    backend.migrate_project_backend(self.root, **kwargs)
                self.assertEqual(project_files(self.root), before)

    def test_target_or_reason_change_cannot_reuse_confirmation(self):
        make_historical_accepted_project(self.root)
        report = preview(self.root, "python")
        before = project_files(self.root)
        for change in ({"target_backend": "matlab"}, {"reason": "Different rationale"}):
            with self.subTest(change=change):
                kwargs = confirmed_kwargs(report)
                kwargs.update(change)
                with self.assertRaises(backend.ProjectBackendMigrationError):
                    backend.migrate_project_backend(self.root, **kwargs)
                self.assertEqual(project_files(self.root), before)

    def test_same_generation_raw_state_rewrite_requires_new_preview(self):
        make_historical_accepted_project(self.root)
        report = preview(self.root, "python")
        path = self.root / transaction.STATE_RELATIVE_PATH
        path.write_bytes(path.read_bytes() + b"\n# changed bytes at generation zero\n")
        before = project_files(self.root)
        with self.assertRaises(backend.ProjectBackendMigrationError):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)

    def test_cli_preview_requires_separate_confirmation_for_write(self):
        make_historical_accepted_project(self.root)
        script = ROOT / "scripts/project_solver_backend.py"
        args = [sys.executable, str(script), "inspect", "--project-root", str(self.root),
                "--migration-target", "python", "--reason", REASON]
        before = project_files(self.root)
        read = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(read.returncode, 0, read.stderr)
        report = yaml.safe_load(read.stdout)
        self.assertEqual(report["status"], "ready_for_review")
        self.assertEqual(project_files(self.root), before)
        command = [sys.executable, str(script), "migrate", "--project-root", str(self.root),
                   "--target-backend", "python", "--reason", REASON,
                   "--expected-generation", "0", "--expected-state-sha256", report["state_snapshot"]["sha256"],
                   "--confirmed-preview-sha256", report["preview_sha256"],
                   "--confirmed-effects-sha256", report["effects_sha256"],
                   "--migration-id", report["migration_id"]]
        missing_confirmation = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertNotEqual(missing_confirmation.returncode, 0)
        self.assertEqual(project_files(self.root), before)
        committed = subprocess.run([*command, "--confirm-migration"], capture_output=True,
                                   text=True, encoding="utf-8", check=False)
        self.assertEqual(committed.returncode, 0, committed.stderr + committed.stdout)
        self.assertEqual(yaml.safe_load(committed.stdout)["status"], "committed")

    def test_unselected_project_uses_select_not_migrate(self):
        report = preview(self.root, "python")
        before = project_files(self.root)
        with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "select"):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)
        selected = backend.select_project_backend(
            self.root, backend="python", reason=REASON, expected_generation=0,
        )
        self.assertEqual(selected["status"], "committed")
        saved = load_state(self.root)
        self.assertEqual(saved["execution"]["solver_backend"], "python")
        self.assertNotIn("backend_migration_history", saved["execution"])
        self.assertFalse((self.root / "state/backend_history").exists())


class HistoricalAcceptedMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.base_tmp.name) / "base"
        make_historical_accepted_project(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.base_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        shutil.copytree(self.base, self.root)

    def test_same_language_keeps_rechecked_accepted_source_and_workbook(self):
        report = preview(self.root, "python")
        self.assertEqual(report["stages"][0]["action"], "retain_candidate")
        before = load_state(self.root)["subproblems"]["Q1"]
        source = before["code"]
        workbook = before["solution_workbook"]
        original = {relative: (self.root / relative).read_bytes() for relative in (source, workbook)}
        backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        saved = load_state(self.root)
        entry = saved["subproblems"]["Q1"]
        self.assertEqual(entry["primary_execution_status"], "accepted")
        self.assertEqual(entry["solution_workbook"], workbook)
        self.assertEqual(entry["solver_execution"]["primary"]["validated_bundle_sha256"],
                         before["solver_execution"]["primary"]["validated_bundle_sha256"])
        self.assertNotIn("backend", entry["solver_execution"]["primary"])
        for relative, content in original.items():
            self.assertEqual((self.root / relative).read_bytes(), content)
        self.assertEqual(state_validator.validate_state_payload(saved, project_root=self.root), [])

    def test_preview_blocks_framework_drift_outside_question_sib(self):
        framework_path = self.root / "模型论文框架.md"
        original = framework_path.read_text(encoding="utf-8")
        original_section = semantic_identity.question_sections(original)["Q1"]
        original_identity = semantic_identity.inspect_question_semantics(original_section, "Q1")
        original_section_hash = state_validator._framework_section_hash(framework_path, SECTION)
        framework_path.write_text(original + "\n<!-- unrelated trailing framework edit -->\n", encoding="utf-8")
        current_section = semantic_identity.question_sections(framework_path.read_text(encoding="utf-8"))["Q1"]
        self.assertEqual(semantic_identity.inspect_question_semantics(current_section, "Q1"),
                         original_identity)
        self.assertEqual(state_validator._framework_section_hash(framework_path, SECTION),
                         original_section_hash)
        before = project_files(self.root)
        report = backend.preview_migration(self.root, target_backend="python", reason=REASON)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("paper_framework.sha256" in issue for issue in report["issues"]))
        self.assertEqual(project_files(self.root), before)
        self.assertFalse((self.root / transaction.JOURNAL_RELATIVE_PATH).exists())

    def test_legacy_missing_framework_hash_remains_previewable(self):
        state = load_state(self.root)
        state["paper_framework"].pop("sha256")
        save_state(self.root, state)
        before = project_files(self.root)
        report = backend.preview_migration(self.root, target_backend="python", reason=REASON)
        self.assertEqual(report["status"], "ready_for_review", report["issues"])
        self.assertEqual(project_files(self.root), before)

    def test_unapproved_delivered_source_cannot_become_current_by_migration(self):
        state = load_state(self.root)
        entry = state["subproblems"]["Q1"]
        entry.pop("solution_workbook")
        for name in ("artifact_hashes", "validated_artifact_hashes"):
            entry[name].pop("solution_workbook", None)
        entry["solver_execution"]["primary"].pop("validated_bundle_sha256")
        entry.update(status="designed", primary_execution_status="awaiting_user_execution",
                     result_quality_status="pending", result_summary_status="pending",
                     human_model_approval_status="pending")
        entry.pop("approved_semantic_revision", None)
        entry.pop("approved_semantic_identity_hash", None)
        save_state(self.root, state)
        report = preview(self.root, "python")
        self.assertEqual(report["stages"][0]["action"], "retain_candidate")
        before = project_files(self.root)
        with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "Model Approval"):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)

    def test_accepted_source_with_revoked_approval_cannot_be_retained(self):
        state = load_state(self.root)
        state["subproblems"]["Q1"]["human_model_approval_status"] = "pending"
        save_state(self.root, state)
        report = preview(self.root, "python")
        self.assertEqual(report["stages"][0]["action"], "retain_candidate")
        before = project_files(self.root)
        with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "Model Approval"):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)

    def test_state_only_approved_hash_does_not_replace_framework_sib(self):
        state = load_state(self.root)
        entry = state["subproblems"]["Q1"]
        fake = hashlib.sha256(b"state-only identity unrelated to current Q1 framework").hexdigest()
        entry.update(semantic_identity_hash=fake, validated_semantic_identity_hash=fake,
                     approved_semantic_identity_hash=fake)
        self.assertEqual(approval.validate_question("Q1", entry), [])
        save_state(self.root, state)
        report = preview(self.root, "python")
        before = project_files(self.root)
        with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "framework SIB"):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)

    def test_retained_analysis_without_necessity_plan_is_blocked(self):
        synthetic_python_analysis(self.root)
        state = load_state(self.root)
        entry = state["subproblems"]["Q1"]
        entry.pop("result_analysis_workbook", None)
        for name in ("artifact_hashes", "validated_artifact_hashes"):
            entry[name].pop("result_analysis_workbook", None)
        entry["solver_execution"]["analysis"].pop("validated_bundle_sha256", None)
        entry.update(status="solved", analysis_execution_status="awaiting_user_execution",
                     result_analysis_status="pending")
        entry.pop("result_analysis_requirement_reason", None)
        entry["analysis_methods"] = []
        save_state(self.root, state)
        report = preview(self.root, "python")
        analysis = next(row for row in report["stages"] if row["stage"] == "analysis")
        self.assertEqual(analysis["action"], "retain_candidate")
        before = project_files(self.root)
        with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "Analysis Necessity Gate"):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertEqual(project_files(self.root), before)

    def test_cross_language_retires_bindings_but_keeps_original_bytes(self):
        report = preview(self.root, "matlab")
        self.assertEqual(report["effects"]["retired_stages"], [{"question": "Q1", "stage": "primary"}])
        before = load_state(self.root)["subproblems"]["Q1"]
        source, workbook = before["code"], before["solution_workbook"]
        original = {relative: (self.root / relative).read_bytes() for relative in (source, workbook)}
        old_input = (self.root / "input.json").read_bytes()
        result = backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        saved = load_state(self.root)
        entry = saved["subproblems"]["Q1"]
        self.assertEqual(saved["execution"]["solver_backend"], "matlab")
        self.assertEqual(result["affected_questions"], ["Q1"])
        self.assertNotIn("code", entry)
        self.assertNotIn("solution_workbook", entry)
        self.assertEqual(entry["primary_execution_status"], "pending")
        for relative, content in original.items():
            self.assertEqual((self.root / relative).read_bytes(), content)
            self.assertEqual((self.root / report["archive_directory"] / "files" / relative).read_bytes(), content)
        self.assertEqual((self.root / report["archive_directory"] / "files/input.json").read_bytes(), old_input)
        self.assertEqual(state_validator.validate_state_payload(saved, project_root=self.root), [])

    def test_prepared_transaction_rolls_forward_only_after_explicit_recovery(self):
        for boundary in ("after_journal_prepared", "after_replace:模型论文框架.md",
                         "after_replace:state/project_state.yaml", "after_replace:report"):
            with self.subTest(boundary=boundary):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "project"
                    shutil.copytree(self.base, root)
                    report = preview(root, "matlab")
                    if boundary == "after_replace:report":
                        actual_boundary = "after_replace:" + report["report_path"]
                    else:
                        actual_boundary = boundary

                    def crash(point):
                        if point == actual_boundary:
                            raise RuntimeError("simulated migration interruption")

                    with self.assertRaises(backend.ProjectBackendMigrationError):
                        backend.migrate_project_backend(root, **confirmed_kwargs(report), failure_hook=crash)
                    journal = root / transaction.JOURNAL_RELATIVE_PATH
                    self.assertTrue(journal.is_file())
                    inspect = subprocess.run(
                        [sys.executable, str(ROOT / "scripts/project_solver_backend.py"),
                         "inspect", "--project-root", str(root)],
                        capture_output=True, text=True, encoding="utf-8", check=False,
                    )
                    self.assertEqual(inspect.returncode, 2)
                    self.assertEqual(yaml.safe_load(inspect.stdout)["status"], "recovery_required")
                    self.assertTrue(journal.is_file())
                    recovered = transaction.recover_project_transaction(root)
                    self.assertIn(recovered["status"], ("rolled_forward", "committed_cleanup"))
                    self.assertFalse(journal.exists())
                    saved = load_state(root)
                    self.assertEqual(saved["project"]["state_generation"], 1)
                    self.assertEqual(saved["execution"]["solver_backend"], "matlab")
                    self.assertEqual(state_validator.validate_state_payload(saved, project_root=root), [])
                    ref = saved["execution"]["backend_migration_history"][-1]
                    transaction.verify_history_archive(root, {key: ref[key] for key in ("manifest", "sha256")})
                    self.assertEqual(digest(root / ref["report"]), ref["report_sha256"])

    def test_candidate_failure_after_archive_leaves_live_files_unchanged(self):
        report = preview(self.root, "matlab")
        old_state = (self.root / transaction.STATE_RELATIVE_PATH).read_bytes()
        old_framework = (self.root / "模型论文框架.md").read_bytes()
        report_path = self.root / report["report_path"]
        with patch.object(state_validator, "validate_state_payload", return_value=["injected staged candidate failure"]):
            with self.assertRaises(backend.ProjectBackendMigrationError) as error:
                backend.migrate_project_backend(self.root, **confirmed_kwargs(report))
        self.assertIn("injected staged candidate failure", str(error.exception.__cause__))
        self.assertEqual((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(), old_state)
        self.assertEqual((self.root / "模型论文框架.md").read_bytes(), old_framework)
        self.assertFalse(report_path.exists())
        self.assertFalse((self.root / transaction.JOURNAL_RELATIVE_PATH).exists())
        manifest = self.root / report["archive_directory"] / "manifest.json"
        self.assertTrue(manifest.is_file())
        transaction.verify_history_archive(self.root, {
            "manifest": manifest.relative_to(self.root).as_posix(), "sha256": digest(manifest),
        })
        self.assertEqual((manifest.parent / "files" / transaction.STATE_RELATIVE_PATH).read_bytes(), old_state)

    def test_corrupt_previous_history_blocks_a_second_migration(self):
        first_preview = preview(self.root, "python")
        backend.migrate_project_backend(self.root, **confirmed_kwargs(first_preview))
        saved = load_state(self.root)
        old_reference = saved["execution"]["backend_migration_history"][-1]
        second_preview = preview(self.root, "matlab")
        old_member = (self.root / old_reference["manifest"]).parent / "files" / transaction.STATE_RELATIVE_PATH
        old_member.write_bytes(b"corrupt original state")
        blocked = backend.preview_migration(self.root, target_backend="matlab", reason=REASON)
        self.assertEqual(blocked["status"], "blocked")
        self.assertTrue(any("archived content changed" in item for item in blocked["issues"]))
        old_state = (self.root / transaction.STATE_RELATIVE_PATH).read_bytes()
        old_framework = (self.root / "模型论文框架.md").read_bytes()
        with self.assertRaises(backend.ProjectBackendMigrationError):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(second_preview))
        self.assertEqual((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(), old_state)
        self.assertEqual((self.root / "模型论文框架.md").read_bytes(), old_framework)
        self.assertFalse((self.root / second_preview["report_path"]).exists())
        self.assertFalse((self.root / transaction.JOURNAL_RELATIVE_PATH).exists())

    def test_select_reason_revision_rechecks_every_old_archive_member(self):
        first_preview = preview(self.root, "python")
        backend.migrate_project_backend(self.root, **confirmed_kwargs(first_preview))
        saved = load_state(self.root)
        old_reference = saved["execution"]["backend_migration_history"][-1]
        old_member = (self.root / old_reference["manifest"]).parent / "files" / "input.json"
        old_member.write_bytes(b"damaged historical input")
        before = ((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(),
                  (self.root / "模型论文框架.md").read_bytes())
        with self.assertRaisesRegex(backend.ProjectBackendSelectionError, "archive"):
            backend.select_project_backend(
                self.root, backend="python", reason="Reviewed numerical policy again",
                expected_generation=1,
            )
        self.assertEqual(((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(),
                          (self.root / "模型论文框架.md").read_bytes()), before)
        self.assertFalse((self.root / transaction.JOURNAL_RELATIVE_PATH).exists())

    def test_old_archive_extra_file_after_new_archive_blocks_commit(self):
        first_preview = preview(self.root, "python")
        backend.migrate_project_backend(self.root, **confirmed_kwargs(first_preview))
        old_reference = load_state(self.root)["execution"]["backend_migration_history"][-1]
        old_extra = (self.root / old_reference["manifest"]).parent / "unlisted.txt"
        second_preview = preview(self.root, "matlab")
        before = ((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(),
                  (self.root / "模型论文框架.md").read_bytes())
        original_prepare = transaction.prepare_history_archive

        def add_old_archive_member(*args, **kwargs):
            reference = original_prepare(*args, **kwargs)
            old_extra.write_text("unlisted historical content", encoding="utf-8")
            return reference

        with patch.object(transaction, "prepare_history_archive", side_effect=add_old_archive_member):
            with self.assertRaisesRegex(backend.ProjectBackendMigrationError, "previous migration archive changed"):
                backend.migrate_project_backend(self.root, **confirmed_kwargs(second_preview))
        self.assertTrue((self.root / second_preview["archive_directory"] / "manifest.json").is_file())
        self.assertEqual(((self.root / transaction.STATE_RELATIVE_PATH).read_bytes(),
                          (self.root / "模型论文框架.md").read_bytes()), before)
        self.assertFalse((self.root / second_preview["report_path"]).exists())
        self.assertFalse((self.root / transaction.JOURNAL_RELATIVE_PATH).exists())

    def test_prepared_recovery_rejects_new_member_in_previous_history(self):
        first_preview = preview(self.root, "python")
        backend.migrate_project_backend(self.root, **confirmed_kwargs(first_preview))
        old_reference = load_state(self.root)["execution"]["backend_migration_history"][-1]
        old_extra = (self.root / old_reference["manifest"]).parent / "unlisted.txt"
        second_preview = preview(self.root, "matlab")

        def crash(point):
            if point == "after_journal_prepared":
                raise RuntimeError("simulated interruption after prepared journal")

        with self.assertRaises(backend.ProjectBackendMigrationError):
            backend.migrate_project_backend(self.root, **confirmed_kwargs(second_preview), failure_hook=crash)
        journal = self.root / transaction.JOURNAL_RELATIVE_PATH
        self.assertTrue(journal.is_file())
        self.assertEqual(yaml.safe_load(journal.read_text(encoding="utf-8"))["version"],
                         transaction.ARCHIVE_JOURNAL_VERSION)
        old_extra.write_text("unlisted historical content", encoding="utf-8")
        with self.assertRaisesRegex(transaction.TransactionRecoveryError, "archive"):
            transaction.recover_project_transaction(self.root)
        self.assertTrue(journal.is_file())
        self.assertEqual(load_state(self.root)["project"]["state_generation"], 1)
        old_extra.unlink()
        recovered = transaction.recover_project_transaction(self.root)
        self.assertEqual(recovered["status"], "rolled_forward")
        saved = load_state(self.root)
        self.assertEqual(saved["project"]["state_generation"], 2)
        self.assertEqual(saved["execution"]["solver_backend"], "matlab")
        for reference in saved["execution"]["backend_migration_history"]:
            transaction.verify_history_archive(
                self.root, {key: reference[key] for key in ("manifest", "sha256")},
            )
            self.assertEqual(digest(self.root / reference["report"]), reference["report_sha256"])


if __name__ == "__main__":
    unittest.main()
