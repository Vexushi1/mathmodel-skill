"""D1 generated metadata on isolated copies; no canonical index is required."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import case_memory as memory  # noqa: E402

CASE_INDEX = Path("knowledge/case_memory/index.json")
OUTPUTS = {
    "BOOTSTRAP": "core/bootstrap.yaml",
    "SKILL_INDEX": "SKILL_FILE_INDEX.md",
    "TEMPLATE_INDEX": "TEMPLATE_INDEX.md",
    "LEGACY_SKILL_INDEX": "HSK_SKILL_FILE_INDEX_V622.md",
    "LEGACY_TEMPLATE_INDEX": "HSK_TEMPLATE_INDEX_V622.md",
    "MANIFEST": "MANIFEST.sha256",
}


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "case_memory_generated_test", ROOT / "scripts/generate_indexes.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CaseMemoryGeneratedTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bootstrap = self.root / OUTPUTS["BOOTSTRAP"]
        self.bootstrap.parent.mkdir()
        self.bootstrap.write_text("skill_version: 10.16.0\n", encoding="utf-8")
        self.module = load_generator()
        replacements = {name: self.root / relative for name, relative in OUTPUTS.items()}
        replacements["ROOT"] = self.root
        patcher = patch.multiple(self.module, **replacements)
        patcher.start()
        self.addCleanup(patcher.stop)

    def install_corpus(self, *, registered: bool = True) -> Path:
        corpus = self.root / "knowledge/case_memory"
        shutil.copytree(ROOT / "knowledge/case_memory", corpus,
                        ignore=shutil.ignore_patterns("index.json", "__pycache__"))
        if registered:
            self.bootstrap.write_text(
                "skill_version: 10.16.0\nauthoritative_sources:\n"
                "  case_memory: knowledge/case_memory/schema.yaml\n", encoding="utf-8",
            )
        return corpus

    def case_payload(self, payloads: dict[Path, str]) -> dict:
        return json.loads(payloads[self.root / CASE_INDEX])

    def test_missing_case_index_is_generated_in_skill_index_and_manifest_without_writing(self):
        self.install_corpus()
        before = snapshot(self.root)
        payloads = self.module.generated_payloads()
        self.assertFalse((self.root / CASE_INDEX).exists())
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(len(payloads), 6)
        self.assertIn(f"`{CASE_INDEX.as_posix()}`", payloads[self.module.SKILL_INDEX])
        digest = hashlib.sha256(payloads[self.root / CASE_INDEX].encode("utf-8")).hexdigest()
        self.assertIn(f"{digest}  {CASE_INDEX.as_posix()}\n", payloads[self.module.MANIFEST])
        self.assertEqual(self.case_payload(payloads)["protocol_version"], "1.0.0")
        # An obsolete on-disk index cannot override the admitted source payload.
        (self.root / CASE_INDEX).write_text("obsolete index\n", encoding="utf-8")
        stale_before = snapshot(self.root)
        self.assertEqual(self.module.generated_payloads(), payloads)
        self.assertEqual(snapshot(self.root), stale_before)

    def test_source_revision_changes_generated_case_identity_and_manifest(self):
        corpus = self.install_corpus()
        before = self.module.generated_payloads()
        sources = json.loads((corpus / "sources.json").read_text(encoding="utf-8"))
        cases = json.loads((corpus / "cases.json").read_text(encoding="utf-8"))
        source = sources["sources"][0]
        anchor = next(iter(source["sections"]))
        source["sections"][anchor] += " Additional independently authored synthetic context."
        for case in cases["cases"]:
            if case["source"]["id"] == source["id"]:
                case["source"]["sha256"] = memory.source_sha256(source)
        write_json(corpus / "sources.json", sources)
        write_json(corpus / "cases.json", cases)
        after = self.module.generated_payloads()
        self.assertNotEqual(self.case_payload(before)["corpus_sha256"],
                            self.case_payload(after)["corpus_sha256"])
        self.assertNotEqual(before[self.root / CASE_INDEX], after[self.root / CASE_INDEX])
        self.assertNotEqual(before[self.module.MANIFEST], after[self.module.MANIFEST])

    def test_case_retirement_changes_generated_index_and_manifest(self):
        corpus = self.install_corpus()
        before = self.module.generated_payloads()
        cases = json.loads((corpus / "cases.json").read_text(encoding="utf-8"))
        retired = next(case for case in cases["cases"] if case["status"] == "reviewed")
        retired["status"] = "retired"
        retired["status_reason"] = "Retired for this isolated generated metadata regression."
        write_json(corpus / "cases.json", cases)
        after = self.module.generated_payloads()
        prior, current = self.case_payload(before), self.case_payload(after)
        self.assertEqual(current["counts"]["reviewed_cases"], prior["counts"]["reviewed_cases"] - 1)
        self.assertFalse(any(retired["id"] in group["case_ids"] for group in current["groups"]))
        self.assertNotEqual(before[self.root / CASE_INDEX], after[self.root / CASE_INDEX])
        self.assertNotEqual(before[self.module.MANIFEST], after[self.module.MANIFEST])

    def test_blocked_corpus_cannot_be_published_as_generated_metadata(self):
        corpus = self.install_corpus()
        sources = json.loads((corpus / "sources.json").read_text(encoding="utf-8"))
        sources["sources"][0]["kind"] = "third_party"
        write_json(corpus / "sources.json", sources)
        before = snapshot(self.root)
        with self.assertRaises(ValueError):
            self.module.generated_payloads()
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / CASE_INDEX).exists())

    def test_unregistered_existing_corpus_is_still_validated_and_generated(self):
        self.install_corpus(registered=False)
        payloads = self.module.generated_payloads()
        self.assertIn(self.root / CASE_INDEX, payloads)

    def test_old_root_without_case_pointer_keeps_original_five_outputs(self):
        before = snapshot(self.root)
        payloads = self.module.generated_payloads()
        self.assertEqual(set(payloads), {self.root / relative
                                       for name, relative in OUTPUTS.items() if name != "BOOTSTRAP"})
        self.assertNotIn(CASE_INDEX.as_posix(), payloads[self.module.SKILL_INDEX])
        self.assertNotIn(CASE_INDEX.as_posix(), payloads[self.module.MANIFEST])
        self.assertEqual(snapshot(self.root), before)

    def test_registered_but_missing_corpus_fails_without_emitting_an_index(self):
        self.bootstrap.write_text(
            "skill_version: 10.16.0\nauthoritative_sources:\n"
            "  case_memory: knowledge/case_memory/schema.yaml\n", encoding="utf-8",
        )
        before = snapshot(self.root)
        with self.assertRaises(ValueError):
            self.module.generated_payloads()
        self.assertEqual(snapshot(self.root), before)

    def test_generator_loaded_alone_can_import_case_dependency(self):
        self.install_corpus()
        code = """
import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('isolated_generator', sys.argv[2])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.ROOT = root
for name, relative in {
    'BOOTSTRAP': 'core/bootstrap.yaml', 'SKILL_INDEX': 'SKILL_FILE_INDEX.md',
    'TEMPLATE_INDEX': 'TEMPLATE_INDEX.md', 'MANIFEST': 'MANIFEST.sha256',
    'LEGACY_SKILL_INDEX': 'HSK_SKILL_FILE_INDEX_V622.md',
    'LEGACY_TEMPLATE_INDEX': 'HSK_TEMPLATE_INDEX_V622.md',
}.items():
    setattr(module, name, root / relative)
assert root / 'knowledge/case_memory/index.json' in module.generated_payloads()
"""
        result = subprocess.run(
            [sys.executable, "-I", "-c", code, str(self.root), str(ROOT / "scripts/generate_indexes.py")],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / CASE_INDEX).exists())


if __name__ == "__main__":
    unittest.main()
