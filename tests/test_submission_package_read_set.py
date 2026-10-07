"""Submission success must bind the bytes consumed even without B2 enabled."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from tests.test_audit_package_completeness import (
    PACK, VALIDATOR, archive, compile_fixture, complete_project, profile, save_state,
)
import project_transaction
import submission_requirements


class SubmissionPackageReadSetTests(unittest.TestCase):
    @contextmanager
    def finish_change(self, root, change):
        """Change a fixture exactly after consumption, before the final recheck."""
        original = project_transaction._check_read_set
        changed = False

        def check(base, expected):
            nonlocal changed
            if base.resolve() == root.resolve() and not changed:
                changed = True
                change()
            return original(base, expected)

        with patch.object(project_transaction, "_check_read_set", side_effect=check):
            yield
        self.assertTrue(changed, "validator must reach the final read-set check")

    def assert_read_conflict(self, report, relative):
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(any("读集冲突" in item and relative in item
                            for item in report["issues"]), report["issues"])

    @staticmethod
    def official_archive(root, profile_path, *, files=None):
        state = VALIDATOR.load_yaml(root / "state/project_state.yaml")
        with patch.object(PACK, "COMPETITION_PROFILES", profile_path):
            _files, metadata = PACK.official_files(root, "DEMO")
        return archive(root, files=files or [root / state["artifacts"]["compiled_pdf"]],
                       kind="official", metadata=metadata)

    def test_stable_b2_off_input_passes_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            package = archive(root)
            paths = [root / "state/project_state.yaml", package, root / "final_latex/main.pdf"]
            before = {path: path.read_bytes() for path in paths}
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report["issues"])
            self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_b2_off_rejects_archived_payload_changed_before_finish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            package = archive(root)
            payload = root / "模型论文框架.md"
            with self.finish_change(root, lambda: payload.write_bytes(b"changed framework")):
                report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, "模型论文框架.md")

    def test_current_pdf_is_observed_when_archive_contains_only_matching_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            pdf = root / "final_latex/main.pdf"
            copy = root / "submission-copy.pdf"
            copy.write_bytes(pdf.read_bytes())
            profile_path = profile(root, [copy.name])
            package = self.official_archive(root, profile_path, files=[copy])
            with patch.object(VALIDATOR, "COMPETITION_PROFILES", profile_path):
                stable = VALIDATOR.validate_package(root, package)
                self.assertEqual(stable["status"], "passed", stable["issues"])
                with self.finish_change(root, lambda: pdf.write_bytes(b"changed compiled PDF")):
                    report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, "final_latex/main.pdf")

    def test_official_profile_in_project_fixture_is_observed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            profile_path = profile(root, ["final_latex/main.pdf"])
            package = self.official_archive(root, profile_path)
            original = profile_path.read_bytes()
            with (patch.object(VALIDATOR, "COMPETITION_PROFILES", profile_path),
                  self.finish_change(root, lambda: profile_path.write_bytes(original + b"\n# changed\n"))):
                report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, profile_path.name)

    def test_official_profile_under_skill_root_is_observed(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as authority:
            root, skill = Path(temp), Path(authority)
            complete_project(root)
            profile_path = profile(skill, ["final_latex/main.pdf"])
            package = self.official_archive(root, profile_path)
            original = profile_path.read_bytes()
            with (patch.object(VALIDATOR, "SKILL_ROOT", skill),
                  patch.object(VALIDATOR, "COMPETITION_PROFILES", profile_path)):
                stable = VALIDATOR.validate_package(root, package)
                self.assertEqual(stable["status"], "passed", stable["issues"])
                with self.finish_change(root, lambda: profile_path.write_bytes(original + b"\n# changed\n")):
                    report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, profile_path.name)

    def test_requirements_authority_retains_its_first_raw_observation(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as authority:
            root, skill = Path(temp), Path(authority)
            complete_project(root)
            contract = skill / "core/output_contract.yaml"
            contract.parent.mkdir()
            original = submission_requirements.OUTPUT_CONTRACT.read_bytes()
            contract.write_bytes(original)
            with patch.object(submission_requirements, "OUTPUT_CONTRACT", contract):
                package = archive(root)
                with patch.object(VALIDATOR, "SKILL_ROOT", skill):
                    stable = VALIDATOR.validate_package(root, package)
                    self.assertEqual(stable["status"], "passed", stable["issues"])
                    actual_requirements = VALIDATOR.reproducibility_requirements

                    def consume(project, state, *, observe):
                        changed = False

                        def observe_and_change(path, payload):
                            nonlocal changed
                            observe(path, payload)
                            if path == contract and not changed:
                                changed = True
                                contract.write_bytes(original + b"\n# changed after first read\n")

                        return actual_requirements(project, state, observe=observe_and_change)

                    with patch.object(VALIDATOR, "reproducibility_requirements", side_effect=consume):
                        report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, "core/output_contract.yaml")

    def test_b2_off_observes_consumed_compile_report_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            compile_fixture(root, state)
            package = archive(root)
            stable = VALIDATOR.validate_package(root, package)
            self.assertEqual(stable["status"], "passed", stable["issues"])
            report_input = root / "final_latex/compile_report.yaml"
            original = report_input.read_bytes()
            actual_requirements = VALIDATOR.reproducibility_requirements

            def consume(project, current, *, observe):
                changed = False

                def observe_and_change(path, payload):
                    nonlocal changed
                    observe(path, payload)
                    if path == report_input and not changed:
                        changed = True
                        report_input.write_bytes(original + b"\n# report changed after observation\n")

                return actual_requirements(project, current, observe=observe_and_change)

            with patch.object(VALIDATOR, "reproducibility_requirements", side_effect=consume):
                report = VALIDATOR.validate_package(root, package)
            self.assert_read_conflict(report, "final_latex/compile_report.yaml")

    def test_state_and_zip_keep_their_existing_finish_protection(self):
        for target in ("state/project_state.yaml", "submission/fixture.zip"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                complete_project(root)
                package = archive(root)
                path = root / target
                original = path.read_bytes()
                if target.endswith(".zip"):
                    original_hash = VALIDATOR._sha256_stream
                    calls = 0

                    def hash_and_change(current):
                        nonlocal calls
                        if current == package:
                            calls += 1
                            if calls == 2:
                                path.write_bytes(original + b"\nchanged\n")
                        return original_hash(current)

                    with patch.object(VALIDATOR, "_sha256_stream", side_effect=hash_and_change):
                        report = VALIDATOR.validate_package(root, package)
                    self.assertEqual(calls, 2)
                else:
                    with self.finish_change(root, lambda: path.write_bytes(original + b"\nchanged\n")):
                        report = VALIDATOR.validate_package(root, package)
                self.assertEqual(report["status"], "failed", report)
                # The package diagnostic intentionally differs from a project-source path.
                self.assertTrue(any(("提交ZIP" in item if target.endswith(".zip") else target in item)
                                    for item in report["issues"]), report["issues"])

    def test_b2_c2_merge_preserves_first_hash_and_absolute_relative_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            state["review_receipt_policy"] = {"protocol_version": "1.0.0", "mode": "enforce_scoped",
                                              "requirements": []}
            save_state(root, state)
            package = archive(root)
            path = root / "模型论文框架.md"
            first = hashlib.sha256(path.read_bytes()).hexdigest()
            state_hash = hashlib.sha256((root / "state/project_state.yaml").read_bytes()).hexdigest()
            claim = {"status": "not_enabled", "issues": [], "observed_sources": {
                "project": {"state/project_state.yaml": state_hash, str(path.resolve()): first}, "skill": {},
            }}

            def changed_review(*_args, **_kwargs):
                path.write_bytes(b"C2 consumed a changed source")
                return {"status": "passed", "issues": [], "observed_sources": {
                    "project": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()},
                    "skill": {},
                }}

            with (patch("claim_consumption.formal_text_gate", return_value=claim),
                  patch("review_receipt_consumption.evaluate_gate", side_effect=changed_review)):
                report = VALIDATOR.validate_package(root, package)
            self.assertTrue(any("首次观察与后续读集冲突" in item and path.name in item
                                for item in report["issues"]), report["issues"])
            self.assert_read_conflict(report, path.name)

    def test_unconsumed_file_change_does_not_reject_stable_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            package = archive(root)
            note = root / "unrelated-note.txt"
            note.write_text("outside this package and its input closure", encoding="utf-8")
            with self.finish_change(root, lambda: note.write_text("changed note", encoding="utf-8")):
                report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report["issues"])

    def test_handpacked_inactive_analysis_cannot_use_archive_path_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            old = root / "问题一求解/问题一结果深化分析.py"
            old.write_bytes(b"inactive legacy analysis")
            base = archive(root)
            with zipfile.ZipFile(base) as bundle:
                payloads = {name: bundle.read(name) for name in bundle.namelist()
                            if name != VALIDATOR.MANIFEST_NAME}
                base_manifest = yaml.safe_load(bundle.read(VALIDATOR.MANIFEST_NAME))
            for alias in (str(old.resolve()), old.relative_to(root).as_posix().replace("/", "\\")):
                with self.subTest(alias=alias):
                    manifest = dict(base_manifest)
                    manifest["files"] = [*base_manifest["files"], {
                        "path": alias, "sha256": hashlib.sha256(old.read_bytes()).hexdigest(),
                        "size": old.stat().st_size,
                    }]
                    package = root / "submission/manual-alias.zip"
                    with zipfile.ZipFile(package, "w") as bundle:
                        for name, payload in payloads.items():
                            bundle.writestr(name, payload)
                        bundle.writestr(alias, old.read_bytes())
                        bundle.writestr(VALIDATOR.MANIFEST_NAME, yaml.safe_dump(manifest, allow_unicode=True))
                    report = VALIDATOR.validate_package(root, package)
                    self.assertEqual(report["status"], "failed", report)
                    self.assertTrue(any("manifest路径无效" in item and alias in item
                                        for item in report["issues"]), report["issues"])

    def test_bad_state_yaml_and_artifacts_return_controlled_failure(self):
        for content in (b"artifacts: [", b"artifacts: [main.pdf]\n"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "state").mkdir()
                (root / "state/project_state.yaml").write_bytes(content)
                report = VALIDATOR.validate_package(root, root / "submission/missing.zip")
                self.assertEqual(report["status"], "failed", report)
                self.assertTrue(any("无法读取当前项目State" in item for item in report["issues"]), report)

    def test_bad_requirements_yaml_returns_controlled_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            package = archive(root)
            contract = root / "fixture-output-contract.yaml"
            contract.write_bytes(b"per_question: [")
            with patch.object(submission_requirements, "OUTPUT_CONTRACT", contract):
                report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any("无法读取当前完整复现包要求" in item
                                for item in report["issues"]), report["issues"])

    def test_b2_bad_compile_yaml_returns_controlled_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            report_path, _report = compile_fixture(root, state)
            package = archive(root)
            state_hash = hashlib.sha256((root / "state/project_state.yaml").read_bytes()).hexdigest()
            gate = {"status": "passed", "issues": [], "observed_sources": {
                "project": {"state/project_state.yaml": state_hash}, "skill": {},
            }}
            report_path.write_bytes(b"source_files: [")
            with patch("claim_consumption.formal_text_gate", return_value=gate):
                report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any("B2编译证明输入无法复核" in item
                                for item in report["issues"]), report["issues"])


if __name__ == "__main__":
    unittest.main()
