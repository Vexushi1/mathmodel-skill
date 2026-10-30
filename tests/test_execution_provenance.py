import hashlib
import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import execution_provenance as PROVENANCE
import validate_project_state as STATE
from artifact_fingerprint import combined_hash, framework_section_hash


def load_syncer():
    spec = importlib.util.spec_from_file_location("sync_project", ROOT / "scripts/sync_project.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    previous = sys.modules.get(spec.name)
    try:
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(spec.name, None)
        else:
            sys.modules[spec.name] = previous
    return module


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_receipt_workbook(path: Path, config: dict[str, object]) -> str:
    book = Workbook()
    sheet = book.active
    sheet.title = "运行配置"
    sheet.append(["项目", "值"])
    for key, value in config.items():
        sheet.append([key, json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value])
    book.save(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accepted_primary_entry(workbook: Path, workbook_hash: str, data_hash: str, code_hash: str, bundle_hash: str):
    root = workbook.parents[1]
    framework_path = root / "模型论文框架.md"
    framework_path.write_text("## Q1\nAccepted framework content.\n", encoding="utf-8")
    framework_hash = framework_section_hash(framework_path, "## Q1")
    return {
        "status": "solved",
        "framework_section": "## Q1",
        "semantic_identity_hash": sha("validated semantic identity"),
        "validated_semantic_identity_hash": sha("validated semantic identity"),
        "approved_semantic_identity_hash": sha("validated semantic identity"),
        "primary_execution_status": "accepted",
        "result_quality_status": "passed",
        "solution_workbook": workbook.relative_to(workbook.parents[1]).as_posix(),
        "data_hash": data_hash,
        "validated_data_hash": data_hash,
        "artifact_hashes": {
            "data": data_hash,
            "primary_code": code_hash,
            "solution_workbook": workbook_hash,
            "framework": framework_hash,
        },
        "validated_artifact_hashes": {
            "data": data_hash,
            "primary_code": code_hash,
            "solution_workbook": workbook_hash,
            "framework": framework_hash,
        },
        "stale_layers": [],
        "artifacts_stale": False,
        "solver_execution": {
            "primary": {
                "bundle_sha256": bundle_hash,
                "validated_bundle_sha256": bundle_hash,
            }
        },
    }


class ExecutionProvenanceTests(unittest.TestCase):
    def test_read_only_consumption_requires_fully_verified_semantics(self):
        entry = {
            "status": "solved",
            "primary_execution_status": "awaiting_user_execution",
            "result_quality_status": "passed",
            "solution_workbook": "result.xlsx",
            "validated_artifact_hashes": {"solution_workbook": sha("workbook")},
            "stale_layers": [],
            "artifacts_stale": False,
        }
        self.assertFalse(PROVENANCE.can_consume_accepted_result(entry, "primary"))
        semantic_hash = sha("validated semantic identity")
        entry["semantic_identity_hash"] = semantic_hash
        entry["validated_semantic_identity_hash"] = semantic_hash
        entry["approved_semantic_identity_hash"] = semantic_hash
        self.assertTrue(PROVENANCE.can_consume_accepted_result(entry, "primary"))

    def test_source_only_hash_drift_is_not_numerical_result_staleness(self):
        old_code, new_code = sha("old source"), sha("cleaned source")
        state = {
            "artifact_hashes": {
                "data": sha("data"),
                "primary_code": new_code,
                "solution_workbook": sha("workbook"),
                "framework": sha("framework"),
            },
            "validated_artifact_hashes": {
                "data": sha("data"),
                "primary_code": old_code,
                "solution_workbook": sha("workbook"),
                "framework": sha("framework"),
            },
            "stale_layers": [],
            "artifacts_stale": False,
        }
        issues = STATE._validate_hashes("Q1", state, "solved")
        self.assertFalse(any("artifacts_stale must be true" in item for item in issues), issues)
        self.assertFalse(any("validated result artifact hashes are stale" in item for item in issues), issues)

        missing_current_source = {
            "artifact_hashes": {
                "data": sha("data"),
                "solution_workbook": sha("workbook"),
                "framework": sha("framework"),
            },
            "validated_artifact_hashes": {
                "data": sha("data"),
                "primary_code": old_code,
                "solution_workbook": sha("workbook"),
                "framework": sha("framework"),
            },
            "stale_layers": [],
            "artifacts_stale": False,
        }
        readonly_issues = STATE._validate_hashes(
            "Q1", missing_current_source, "solved", allow_read_only_source_drift=True,
        )
        strict_issues = STATE._validate_hashes("Q1", missing_current_source, "solved")
        self.assertFalse(any("missing current=['primary_code']" in item for item in readonly_issues), readonly_issues)
        self.assertTrue(any("missing current=['primary_code']" in item for item in strict_issues), strict_issues)

    def test_read_only_cleanup_suppresses_only_code_transition(self):
        syncer = load_syncer()
        old_code, new_code = sha("old source"), sha("cleaned source")
        old_bundle, new_bundle = sha("old bundle"), sha("new bundle")
        entry = {
            "code": "问题一求解/问题一求解.py",
            "primary_code_sha256": old_code,
            "artifact_hashes": {"primary_code": old_code},
            "validated_artifact_hashes": {"primary_code": old_code},
            "solver_execution": {
                "primary": {
                    "bundle_sha256": old_bundle,
                    "validated_bundle_sha256": old_bundle,
                }
            },
        }
        snapshot = {
            "primary_code": entry["code"],
            "primary_code_sha256": new_code,
            "analysis_code_sha256": None,
            "project_backend": "python",
            "artifact_hashes": {"primary_code": new_code},
            "solver_execution_observed": {
                "primary": {
                    "backend": "python",
                    "entrypoint": entry["code"],
                    "entry_sha256": new_code,
                    "bundle_sha256": new_bundle,
                }
            },
            "accepted_result_source_drift": ["primary"],
        }
        cleanup_events = syncer._snapshot_transition_events(
            entry, snapshot, delivery_scope="figures", current_phase="figure_evidence"
        )
        strict_events = syncer._snapshot_transition_events(
            entry, snapshot, delivery_scope="code", current_phase="solve_validate"
        )
        wrong_phase_events = syncer._snapshot_transition_events(
            entry, snapshot, delivery_scope="figures", current_phase="solve_validate"
        )
        self.assertNotIn("primary_code_changed", cleanup_events)
        self.assertIn("primary_code_changed", strict_events)
        self.assertIn("primary_code_changed", wrong_phase_events)

    def test_real_input_drift_is_not_suppressed_by_source_cleanup(self):
        syncer = load_syncer()
        old_code, new_code = sha("old source"), sha("cleaned source")
        data_old, data_new = sha("old data"), sha("new data")
        entry = {
            "code": "问题一求解/问题一求解.py",
            "primary_code_sha256": old_code,
            "artifact_hashes": {"data": data_old, "primary_code": old_code},
            "validated_artifact_hashes": {"data": data_old, "primary_code": old_code},
            "solver_execution": {"primary": {"bundle_sha256": sha("old bundle"), "validated_bundle_sha256": sha("old bundle")}},
        }
        snapshot = {
            "primary_code": entry["code"],
            "primary_code_sha256": new_code,
            "analysis_code_sha256": None,
            "project_backend": "python",
            "artifact_hashes": {"data": data_new, "primary_code": new_code},
            "solver_execution_observed": {
                "primary": {"backend": "python", "entrypoint": entry["code"], "bundle_sha256": sha("new bundle")}
            },
            "accepted_result_source_drift": ["primary"],
        }
        events = syncer._snapshot_transition_events(
            entry, snapshot, delivery_scope="figures", current_phase="figure_evidence"
        )
        self.assertIn("data_changed", events)
        self.assertNotIn("primary_code_changed", events)

    def test_accepted_workbook_is_bound_to_old_bundle_not_current_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_dir = root / "问题一求解"
            result_dir.mkdir()
            workbook = result_dir / "问题一求解结果.xlsx"
            data_file = root / "data.csv"
            data_file.write_text("x,y\n1,2\n", encoding="utf-8")
            data_hash = combined_hash([data_file], root)
            code_hash, old_bundle, new_bundle = sha("accepted code"), sha("accepted bundle"), sha("cleaned bundle")
            config = {
                "stage": "primary",
                "run_receipt_protocol_version": "1.1.0",
                "run_receipt_version": "1.1.0",
                "code_sha256": code_hash,
                "code_bundle_sha256": old_bundle,
                "data_paths": ["data.csv"],
                "data_identity_mode": "combined",
                "data_sha256": data_hash,
            }
            workbook_hash = write_receipt_workbook(workbook, config)
            entry = accepted_primary_entry(workbook, workbook_hash, data_hash, code_hash, old_bundle)
            entry["solver_execution"]["primary"]["bundle_sha256"] = new_bundle
            state = {"subproblems": {"Q1": entry}}
            issues, warnings = PROVENANCE.accepted_result_issues(root, state, entry, "primary")
            self.assertEqual(issues, [])
            self.assertTrue(any("current source bundle differs" in warning for warning in warnings), warnings)

            data_file.write_text("x,y\n1,999\n", encoding="utf-8")
            issues, _ = PROVENANCE.accepted_result_issues(root, state, entry, "primary")
            self.assertTrue(any("input" in issue.lower() for issue in issues), issues)

    def test_changed_accepted_workbook_bytes_block_consumption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_dir = root / "问题一求解"
            result_dir.mkdir()
            workbook = result_dir / "问题一求解结果.xlsx"
            data_file = root / "data.csv"
            data_file.write_text("x,y\n1,2\n", encoding="utf-8")
            data_hash = combined_hash([data_file], root)
            code_hash, bundle_hash = sha("accepted code"), sha("accepted bundle")
            workbook_hash = write_receipt_workbook(workbook, {
                "stage": "primary",
                "run_receipt_protocol_version": "1.1.0",
                "run_receipt_version": "1.1.0",
                "code_sha256": code_hash,
                "code_bundle_sha256": bundle_hash,
                "data_paths": ["data.csv"],
                "data_identity_mode": "combined",
                "data_sha256": data_hash,
            })
            entry = accepted_primary_entry(workbook, workbook_hash, data_hash, code_hash, bundle_hash)
            state = {"subproblems": {"Q1": entry}}
            with workbook.open("ab") as handle:
                handle.write(b"tampered")
            issues, _ = PROVENANCE.accepted_result_issues(root, state, entry, "primary")
            self.assertTrue(any("bytes differ" in issue for issue in issues), issues)

    def test_framework_section_change_blocks_accepted_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_dir = root / "问题一求解"
            result_dir.mkdir()
            workbook = result_dir / "问题一求解结果.xlsx"
            data_file = root / "data.csv"
            data_file.write_text("x,y\n1,2\n", encoding="utf-8")
            data_hash = combined_hash([data_file], root)
            code_hash, bundle_hash = sha("accepted code"), sha("accepted bundle")
            workbook_hash = write_receipt_workbook(workbook, {
                "stage": "primary",
                "run_receipt_protocol_version": "1.1.0",
                "run_receipt_version": "1.1.0",
                "code_sha256": code_hash,
                "code_bundle_sha256": bundle_hash,
                "data_paths": ["data.csv"],
                "data_identity_mode": "combined",
                "data_sha256": data_hash,
            })
            entry = accepted_primary_entry(workbook, workbook_hash, data_hash, code_hash, bundle_hash)
            state = {"subproblems": {"Q1": entry}}
            (root / "模型论文框架.md").write_text("## Q1\nA changed framework claim.\n", encoding="utf-8")
            issues, _ = PROVENANCE.accepted_result_issues(root, state, entry, "primary")
            self.assertTrue(any("framework section differs" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
