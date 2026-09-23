"""Current-state migration references and pure framework memory patching."""
from __future__ import annotations

from copy import deepcopy
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import sync_project  # noqa: E402
from test_sync_project import setup_project  # noqa: E402


def reference(migration_id: str, *, digest: str = "a" * 64) -> dict[str, str]:
    return {
        "manifest": f"state/backend_history/{migration_id}/manifest.json",
        "sha256": digest,
        "report": f"state/backend_migration_reports/{migration_id}.yaml",
        "report_sha256": "b" * 64,
    }


class ProjectBackendHistorySchemaTests(unittest.TestCase):
    def setUp(self):
        self.syncer = sync_project
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        setup_project(
            self.root, status="designed", phase="model_design",
            include_solution=False, include_analysis=False, include_analysis_code=False,
        )
        self.state = yaml.safe_load((self.root / "state/project_state.yaml").read_text(encoding="utf-8"))
        self.assertEqual(self.syncer.STATE_VALIDATION.validate_state_payload(
            self.state, project_root=self.root,
        ), [])
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(schema)

    def schema_issues(self, candidate):
        return list(self.validator.iter_errors(candidate))

    def test_optional_history_accepts_complete_references(self):
        self.assertEqual(self.schema_issues(self.state), [])
        self.state["execution"]["backend_migration_history"] = [reference("a" * 32), reference("b" * 32)]
        self.assertEqual(self.schema_issues(self.state), [])

    def test_history_rejects_partial_paths_duplicates_and_extra_keys(self):
        item = reference("a" * 32)
        invalid = [
            [],
            [{key: value for key, value in item.items() if key != "report_sha256"}],
            [{**item, "extra": "current"}],
            [{**item, "manifest": "../state/backend_history/" + "a" * 32 + "/manifest.json"}],
            [{**item, "manifest": "state/backend_history/" + "A" * 32 + "/manifest.json"}],
            [{**item, "report": "state/backend_history/" + "a" * 32 + "/report.yaml"}],
            [{**item, "sha256": "bad"}],
            [{**item, "report_sha256": "bad"}],
            [item, deepcopy(item)],
        ]
        for history in invalid:
            with self.subTest(history=history):
                candidate = deepcopy(self.state)
                candidate["execution"]["backend_migration_history"] = history
                self.assertTrue(self.schema_issues(candidate))

    def test_history_append_guard_preserves_order_and_id(self):
        before = deepcopy(self.state)
        before["execution"]["backend_migration_history"] = [reference("a" * 32)]
        after = deepcopy(before)
        after["execution"]["backend_migration_history"].append(reference("b" * 32))
        self.assertEqual(self.syncer.backend_history_append_issues(before, after), [])
        dropped = deepcopy(after)
        dropped["execution"]["backend_migration_history"] = [reference("b" * 32)]
        self.assertTrue(self.syncer.backend_history_append_issues(before, dropped))
        replaced = deepcopy(after)
        replaced["execution"]["backend_migration_history"][0]["sha256"] = "c" * 64
        self.assertTrue(self.syncer.backend_history_append_issues(before, replaced))
        duplicate = deepcopy(after)
        duplicate["execution"]["backend_migration_history"].append(reference("b" * 32, digest="c" * 64))
        self.assertTrue(self.syncer.backend_history_append_issues(before, duplicate))
        mismatch = deepcopy(after)
        mismatch["execution"]["backend_migration_history"][1]["report"] = reference("c" * 32)["report"]
        self.assertTrue(self.syncer.backend_history_append_issues(before, mismatch))

    def test_framework_memory_is_pure_idempotent_and_staged_valid(self):
        original = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        candidate = deepcopy(self.state)
        rendered = self.syncer.render_project_backend_memory(original, candidate)
        self.assertIn("### 全项目数值实现", rendered)
        self.assertIn("- 项目求解后端：`python`", rendered)
        self.assertIn("Whole-problem fixture", rendered)
        self.assertEqual(self.syncer.render_project_backend_memory(rendered, candidate), rendered)
        self.assertEqual((self.root / "模型论文框架.md").read_text(encoding="utf-8"), original)
        staged = self.root / "staged-framework.md"
        staged.write_text(rendered, encoding="utf-8")
        candidate["paper_framework"]["sha256"] = self.syncer.FRAMEWORK_VALIDATION.sha256_text(rendered)
        self.assertEqual(self.syncer.STATE_VALIDATION.validate_state_payload(
            candidate, project_root=self.root, framework_path_override=staged,
        ), [])
        self.assertEqual(self.syncer.FRAMEWORK_VALIDATION.validate_framework_text(
            rendered, state=candidate, project_root=self.root,
        ), [])

    def test_known_legacy_field_keeps_accepted_section_identity(self):
        original = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        old = "### Q1\n\n- 已选求解后端 / 选择理由 / 依赖核验：MATLAB；原理由与许可证记录\n- Solver：保留现有算法\n"
        text = original.replace("### Q1\n", old).replace("\n", "\r\n")
        rendered = self.syncer.render_project_backend_memory(text, self.state)
        self.assertIn("- 已选求解后端 / 选择理由 / 依赖核验：MATLAB；原理由与许可证记录", rendered)
        self.assertIn("- 逐问旧已选后端/理由为迁移前历史记录，当前取项目根。", rendered)
        self.assertIn("- Solver：保留现有算法", rendered)
        self.assertNotIn("\n", rendered.replace("\r\n", ""))
        before_path = self.root / "before-framework.md"
        after_path = self.root / "after-framework.md"
        before_path.write_bytes(text.encode("utf-8"))
        after_path.write_bytes(rendered.encode("utf-8"))
        self.assertEqual(
            self.syncer.framework_section_hash(before_path, "### Q1"),
            self.syncer.framework_section_hash(after_path, "### Q1"),
        )
        self.assertEqual(self.syncer.render_project_backend_memory(rendered, self.state), rendered)

    def test_ambiguous_legacy_or_global_fields_fail_closed(self):
        original = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        ambiguous = [
            original.replace("### Q1\n", "### Q1\n- 已选求解后端：MATLAB\n"),
            original.replace("### Q1\n", "### Q1\n- 已选求解后端 / 选择理由 / 依赖核验：a\n- 已选求解后端 / 选择理由 / 依赖核验：b\n"),
            original.replace("## 当前有效口径\n", "## 当前有效口径\n### 全项目数值实现\n### 全项目数值实现\n"),
        ]
        for text in ambiguous:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    self.syncer.render_project_backend_memory(text, self.state)


if __name__ == "__main__":
    unittest.main()
