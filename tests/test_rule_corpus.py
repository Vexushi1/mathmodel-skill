from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import rule_corpus as corpus


def digest(data):
    return hashlib.sha256(data).hexdigest()


class RegisteredCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.volumes = corpus.build_corpus(ROOT)
        cls.sources = {source["path"]: source for source in cls.catalog["sources"]}

    def test_canonical_sources_and_independent_byte_reassembly(self):
        for record in self.catalog["volumes"]:
            data = self.volumes[record["path"]]
            self.assertEqual((len(data), digest(data)), (record["bytes"], record["sha256"]))
            self.assertLessEqual(len(data), corpus.VOLUME_BYTES)
            data.decode("utf-8")
        for name, row in self.sources.items():
            with self.subTest(source=name):
                original = (ROOT / name).read_bytes()
                identity = hashlib.sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
                self.assertEqual((row["bytes"], row["sha256"], row["git_blob_sha1"]),
                                 (len(original), digest(original), identity))
                previous = 0
                for part in row["parts"]:
                    self.assertGreaterEqual(part["start"], previous)
                    start, end = part["start"], part["end"]
                    volume = self.volumes[part["volume"]]
                    self.assertIn(f"(../../../{name}#L{part['line_start']})".encode(),
                                  volume[:part["volume_start"]])
                    body = volume[part["volume_start"]:part["volume_end"]]
                    self.assertEqual(body, original[start:end])
                    self.assertEqual(digest(body), part["sha256"])
                    self.assertEqual(part["line_start"], 1 + original[:start].count(b"\n"))
                    self.assertEqual(part["line_end"], 1 + original[:end-1].count(b"\n"))
                    previous = end
                for alias in row["aliases"]:
                    self.assertEqual((ROOT / alias).read_bytes(), original)
        # Discover expected full-source families from the physical tree, not from the corpus.
        required = set()
        for directory, pattern in (("core", "*.yaml"), ("config", "*"),
                                   ("packs", "**/*.md"), ("templates/review", "*")):
            required.update(p.relative_to(ROOT).as_posix() for p in (ROOT / directory).glob(pattern) if p.is_file() and p.relative_to(ROOT).as_posix() != corpus.REGISTRY_PATH)
        required.update(("assets/nature_figure/README.md", "assets/figure_assets.yaml",
                         "knowledge/case_memory/schema.yaml", "knowledge/case_memory/README.md",
                         "docs/v8_writing_migration.md", "templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex"))
        for name in required:
            self.assertEqual(self._reconstruct(name), (ROOT / name).read_bytes(), name)

    def _reconstruct(self, name):
        return b"".join(self.volumes[p["volume"]][p["volume_start"]:p["volume_end"]]
                        for p in self.sources[name]["parts"])

    def test_delegated_ranges_preserve_parent_and_exclude_unrelated_actions(self):
        name = "docs/semantic_state_runtime_refactor_plan.md"
        text = self._reconstruct(name).decode()
        original = (ROOT / name).read_text(encoding="utf-8")
        self.assertTrue(text.startswith(original[:original.index("## 0. 修改简报")]))
        self.assertIn(original[original.index("# 4. 分阶段实施与 PR 切分"):original.index("## Phase A —")], text)
        self.assertIn(original[original.index("## Phase E —"):original.index("## Phase G —")], text)
        self.assertNotIn("## Phase D —", text)
        self.assertNotIn("## Phase G —", text)
        example = self._reconstruct("modules/05_writing/references/model_solution_reasoning_examples.md").decode()
        self.assertIn("不是当前项目的结果", example)
        self.assertNotIn("## 1.", example)
        self.assertEqual(self.sources["SKILL.md"]["aliases"], ["skills/mathmodel-skill/SKILL.md"])
        self.assertFalse(any(name.startswith(("tests/", "legacy/", "core/full_reading/")) for name in self.sources))
        self.assertNotIn(corpus.REGISTRY_PATH, self.sources)
        registry = (ROOT / corpus.REGISTRY_PATH).read_bytes()
        self.assertEqual(digest(registry), self.catalog["registry"]["sha256"])
        self.assertEqual(self.catalog["registry"]["git_blob_sha1"],
                         hashlib.sha1(b"blob " + str(len(registry)).encode() + b"\0" + registry).hexdigest())
        self.assertNotIn("MANIFEST.sha256", self.sources)
        self.assertNotIn("core/stage_reading_guide.md", self.sources)
        self.assertNotIn("knowledge/case_memory/cases.json", self.sources)


class CorpusBuilderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "core").mkdir()
        self.manifest = self.root / corpus.DECLARATION
        self.declaration = {
            "schema_version": 1, "members": {"contract": ["source.md"]}, "aliases": {"mirror.md": "source.md"},
            "excerpts": {}, "excluded": {"catalog": [corpus.DECLARATION, corpus.REGISTRY_PATH]}, "excluded_trees": {},
        }
        self._write_manifest()
        self._source("第一行\r\n" + "长字" * 7500 + "末行无换行。")

    def _write_manifest(self):
        self.manifest.write_text(f"rule_corpus: {corpus.REGISTRY_PATH}\n", encoding="utf-8")
        (self.root / corpus.REGISTRY_PATH).write_text(
            yaml.safe_dump(self.declaration, allow_unicode=True), encoding="utf-8")

    def _source(self, text):
        for name in ("source.md", "mirror.md"):
            (self.root / name).write_bytes(text.encode())

    def test_long_utf8_line_original_endings_and_non_recursive_determinism(self):
        first = corpus.generated_payloads(self.root)
        for path, content in first.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
        self.assertEqual(first, corpus.generated_payloads(self.root))
        index = json.loads(first[self.root / corpus.DIRECTORY / "manifest.json"])
        self.assertGreater(len(index["volumes"]), 2)
        self.assertEqual(len(index["sources"]), 1)
        parts = index["sources"][0]["parts"]
        pieces = []
        for part in parts:
            volume = first[self.root / part["volume"]].encode("utf-8")
            self.assertLessEqual(len(volume), corpus.VOLUME_BYTES)
            piece = volume[part["volume_start"]:part["volume_end"]]
            piece.decode("utf-8")
            pieces.append(piece)
        self.assertEqual(b"".join(pieces), (self.root / "source.md").read_bytes())

    def test_unknown_file_duplicate_role_and_physical_alias_drift_fail_closed(self):
        unknown = self.root / "core/extra-contract.yaml"
        unknown.touch()
        with self.assertRaisesRegex(ValueError, "unclassified.*extra-contract"):
            corpus.build_corpus(self.root)
        unknown.unlink()
        self.declaration["excluded"]["other"] = ["source.md"]
        self._write_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            corpus.build_corpus(self.root)
        del self.declaration["excluded"]["other"]
        self._write_manifest()
        (self.root / "mirror.md").write_text("a different rule", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "alias mirror.md"):
            corpus.build_corpus(self.root)

    def test_redirected_missing_or_recursive_registry_fails_closed(self):
        self.manifest.write_text("rule_corpus: ../elsewhere.yaml\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must point to"):
            corpus.generated_payloads(self.root)
        self.declaration["excluded"]["catalog"].remove(corpus.REGISTRY_PATH)
        self.declaration["members"]["contract"].append(corpus.REGISTRY_PATH)
        self._write_manifest()
        with self.assertRaisesRegex(ValueError, "selection metadata"):
            corpus.build_corpus(self.root)
        (self.root / corpus.REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(ValueError, "regular source file"):
            corpus.build_corpus(self.root)

    def test_missing_delegated_heading_and_ambiguous_anchors_fail(self):
        self.declaration["members"] = {}
        self.declaration["excerpts"] = {"source.md": {"role": "delegated", "ranges": [[None, "## Next"]]}}
        self._write_manifest()
        for text in ("# Start\n", "# Start\n## Next\n## Next\n"):
            with self.subTest(text=text):
                self._source(text)
                with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
                    corpus.build_corpus(self.root)

    def test_absent_registration_distinguishes_old_root_from_broken_delivery(self):
        self.manifest.unlink()
        self.assertEqual(corpus.generated_payloads(self.root), {})
        (self.root / "core/runtime_assurance_contract.yaml").write_text(
            "reading_plan:\n  formal_rule_delivery: {}\n", encoding="utf-8")
        for contents in (None, "{}"):
            if contents is not None:
                self.manifest.write_text(contents, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "formal_rule_delivery requires"):
                corpus.generated_payloads(self.root)


if __name__ == "__main__":
    unittest.main()
