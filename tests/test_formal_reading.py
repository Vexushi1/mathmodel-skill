"""Exercise formal startup transport using real Git objects and independently received bytes."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from formal_reading import MANIFEST_PATH, PinnedCorpus
from rule_corpus import DECLARATION, REGISTRY_PATH, part_header


class FormalReadingTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.receipts = self.root / "return"
        self.receipts.mkdir()
        self.git("init", "--quiet")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "user.name", "Reading test")
        self.git("config", "user.email", "reading@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", ".git/no-hooks")
        self.source = "core/规则.md"
        self.alias = "plugin/规则.md"
        # One logical line can span transfers. Preserve the BOM, CRLF and last partial line.
        self.parts = ["\ufeff前言与适用条件\r\n" + "测" * 3050, "量" * 1000 + "\r\n例外：零有效。"]
        raw = "".join(self.parts).encode("utf-8")
        self.save(self.source, raw)
        self.save(self.alias, raw)
        self.save(DECLARATION, json.dumps({"rule_corpus": REGISTRY_PATH}).encode())
        registry = {"schema_version": 1, "members": {"contract": [self.source]},
                    "aliases": {self.alias: self.source}, "excerpts": {}, "excluded_trees": {},
                    "excluded": {"metadata": [DECLARATION, REGISTRY_PATH]}}
        registered = json.dumps(registry).encode()
        self.save(REGISTRY_PATH, registered)
        self.volumes = []
        locations = []
        offset = 0
        for i, part in enumerate(self.parts, 1):
            body = part.encode("utf-8")
            path = f"core/full_reading/volumes/{i:03}.md"
            first_line = raw[:offset].count(b"\n") + 1
            last_line = raw[:offset + len(body) - 1].count(b"\n") + 1
            header = part_header(self.source, "contract", offset, first_line)
            framed = header + body
            self.save(path, framed)
            self.volumes.append({"path": path, "bytes": len(framed), "sha256": sha256(framed).hexdigest()})
            locations.append({"volume": path, "start": offset, "end": offset + len(body), "volume_start": len(header),
                              "line_start": first_line, "line_end": last_line, "volume_end": len(framed), "sha256": sha256(body).hexdigest()})
            offset += len(body)
        self.manifest = {"schema_version": 1,
                         "registry": {"path": REGISTRY_PATH, "sha256": sha256(registered).hexdigest(),
                                      "git_blob_sha1": sha1(f"blob {len(registered)}\0".encode() + registered).hexdigest()},
                         "volumes": self.volumes, "sources": [{
            "path": self.source, "role": "contract", "aliases": [self.alias], "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "git_blob_sha1": sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest(), "parts": locations,
        }]}
        self.save(MANIFEST_PATH, json.dumps(self.manifest).encode("utf-8"))
        self.pin = self.commit()
        self.corpus = PinnedCorpus(self.root, self.pin)

    def save(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def git(self, *args):
        p = subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        return p.stdout.decode().strip()

    def commit(self):
        self.git("add", "core", "plugin")
        self.git("commit", "-qm", "Freeze corpus fixture")
        return self.git("rev-parse", "HEAD")

    def response(self, number=0):
        return self.corpus.read(self.volumes[number]["path"])

    def receive(self, filename, data):
        path = self.receipts / filename
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, action, *options, pin=None):
        command = [sys.executable, str(ROOT / "scripts/read_stage.py"), "formal", action,
                   "--root", str(self.root), "--source-commit", pin or self.pin, *map(str, options)]
        return subprocess.run(command, capture_output=True, encoding="utf-8")

    def test_pinned_cli_inventory_recovery_and_idempotent_retries(self):
        page1 = self.cli("manifest", "--limit", 1)
        self.assertEqual(page1.returncode, 0, page1.stderr)
        catalog = json.loads(page1.stdout)
        self.assertEqual(catalog["status"], "catalog_only")
        self.assertEqual(catalog["next_offset"], 1)
        page2 = self.cli("manifest", "--limit", 1, "--offset", 1)
        self.assertEqual(json.loads(page2.stdout)["volumes"], self.volumes[1:])
        alias = self.cli("manifest", "--source", self.alias, "--offset", 1)
        fragment = json.loads(alias.stdout)
        self.assertEqual(fragment["source"]["path"], self.source)
        self.assertEqual(fragment["parts"], self.manifest["sources"][0]["parts"][1:])
        first = self.cli("read", "--volume", self.volumes[0]["path"])
        self.assertEqual(first.returncode, 0, first.stderr)
        actual = json.loads(first.stdout)
        self.assertTrue(actual["text"].endswith(self.parts[0]))
        duplicate = self.receive("a.json", actual)
        partial = self.cli("verify", "--received", duplicate, duplicate)
        self.assertEqual(partial.returncode, 1, partial.stderr)
        self.assertEqual(json.loads(partial.stdout)["missing_volumes"], [self.volumes[1]["path"]])
        second = self.cli("read", "--volume", self.volumes[1]["path"])
        self.receive("b.json", json.loads(second.stdout))
        complete = self.cli("verify", "--received-dir", self.receipts, "--received", duplicate)
        self.assertEqual(complete.returncode, 0, complete.stderr)
        checked = json.loads(complete.stdout)
        self.assertEqual(checked["verified_volume_count"], 2)
        self.assertEqual(checked["gate_status"], "not_executed_by_reader")
        self.assertEqual(checked["context_retention"], "not_observable")

    def test_receiver_hashes_returned_text_even_if_sender_claims_hash_is_good(self):
        original = self.response(1)
        for body in (original["text"][:-1], original["text"].replace("零", "无"),
                     original["text"].replace("\r\n", "\n"), ""):
            with self.subTest(size=len(body)):
                file = self.receive("b.json", dict(original, text=body, sha256=self.volumes[1]["sha256"]))
                checked = self.corpus.verify([file], 0, 24)
                self.assertFalse(checked["complete"])
                self.assertEqual(checked["verified_volume_count"], 0)
                self.assertIn(self.volumes[1]["path"], checked["missing_volumes"])
                self.assertEqual(checked["issue_count"], 1)

    def test_unknown_volume_bad_pin_and_catalog_alone_do_not_count(self):
        whole = self.response()
        for changes in ({"source_commit": "0" * 40}, {"manifest_sha256": "0" * 64}, {"volume": self.source},
                        {"volume": self.volumes[1]["path"]}, {"text": None}):
            with self.subTest(changes=changes):
                file = self.receive("org.json", dict(whole, **changes))
                self.assertEqual(self.corpus.verify([file], 0, 24)["verified_volume_count"], 0)
        file = self.receive("catalog.json", self.corpus.catalog(0, 24))
        self.assertFalse(self.corpus.verify([file], 0, 24)["complete"])
        file.write_bytes(b'{"text":')
        self.assertEqual(self.corpus.verify([file], 0, 24)["issue_count"], 1)
        self.assertEqual(self.cli("read", "--volume", self.source).returncode, 2)
        self.assertEqual(self.cli("manifest", pin="main").returncode, 2)
        self.assertEqual(self.cli("manifest", pin="0" * 40).returncode, 2)

    def test_dirty_worktree_does_not_supply_expected_or_returned_bytes(self):
        self.save(self.volumes[0]["path"], b"dirty")
        self.save(MANIFEST_PATH, b"{}")
        self.assertTrue(self.response()["text"].endswith(self.parts[0]))
        self.assertEqual(PinnedCorpus(self.root, self.pin).manifest_sha256, self.corpus.manifest_sha256)

    def test_valid_json_reductions_and_invalid_offsets_cannot_shrink_required_coverage(self):
        baseline = self.manifest
        cases = []
        for omit in ("last_volume", "source", "part", "all_parts"):
            changed = deepcopy(baseline)
            if omit == "last_volume":
                changed["volumes"].pop()
            elif omit == "source":
                changed["sources"].clear()
            elif omit == "part":
                changed["sources"][0]["parts"].pop()
            else:
                changed["sources"][0]["parts"] = []
            cases.append((omit, changed))
        for field, value in (("volume_end", 999999), ("start", 1), ("end", True),
                             ("volume_start", 0), ("line_start", 0), ("volume", "other")):
            changed = deepcopy(baseline)
            changed["sources"][0]["parts"][0][field] = value
            cases.append((field, changed))
        changed = deepcopy(baseline)
        changed["volumes"][0]["path"] = f"core/full_reading/volumes/01.md"
        cases.append(("noncanonical", changed))
        for label, changed in cases:
            with self.subTest(label=label):
                self.save(MANIFEST_PATH, json.dumps(changed).encode())
                pin = self.commit()
                with self.assertRaises(ValueError):
                    PinnedCorpus(self.root, pin)

    def test_replaced_volume_with_matching_manifest_digest_still_needs_original_source_bytes(self):
        body = self.response(1)["text"].replace("零", "无").encode()
        row = self.manifest["volumes"][1]
        self.save(row["path"], body)
        row["sha256"] = sha256(body).hexdigest()
        self.save(MANIFEST_PATH, json.dumps(self.manifest).encode())
        corrupted = PinnedCorpus(self.root, self.commit())
        with self.assertRaisesRegex(ValueError, "differs from pinned manifest"):
            corrupted.read(row["path"])

    def test_stale_generated_volume_and_source_alias_block_coverage(self):
        volume = self.root / self.volumes[0]["path"]
        body = volume.read_bytes()
        volume.write_bytes(body[:-3] + "错".encode())
        pin = self.commit()
        corpus = PinnedCorpus(self.root, pin)
        with self.assertRaisesRegex(ValueError, "differs from pinned manifest"):
            corpus.read(self.volumes[0]["path"])
        claimed = self.receive("a.json", dict(self.response(), source_commit=pin))
        self.assertEqual(corpus.verify([claimed], 0, 24)["verified_volume_count"], 0)
        self.save(self.alias, b"changed alias")
        pin = self.commit()
        with self.assertRaisesRegex(ValueError, "source differs"):
            PinnedCorpus(self.root, pin)


if __name__ == "__main__":
    unittest.main()
