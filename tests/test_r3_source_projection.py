"""R3 source-only migrations retain exact predecessors and current rule checks."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from r3_concision_reference import (
    R3_ADDITIONAL_READ_SHIFTS, R3_APPROVED_REWRITES, R3_RANGE_TRANSITIONS,
    R3_SOURCE_IDENTITIES, prior_r3_bytes, prior_r3_schema, prior_r3_text,
)
from v10270_runtime_measurement import approved_source_span_migrations


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "tests/fixtures/v1140_r3_source_spans.json"
FROZEN = ROOT / "tests/fixtures/v1140_r2_source_spans.json"


class R3SourceProjectionTests(unittest.TestCase):
    def test_accepted_source_maps_and_manifests_remain_frozen(self):
        frozen = {
            "tests/fixtures/v1140_r2_source_spans.json": "27e02a610848dc2326bcab46b206aaac900b576fc6bb064e7594b6b049c20bb4",
            "tests/r2_answer_reference.py": "1bae224109187876c11d799c23b1c89e339cbbd5f13411befe81dbe65884455e",
            "tests/fixtures/v1130_r1_source_spans.json": "0d66985974503a19c7f6aaa24aac99b627ef0dc1893191e3bc3f915dcae57521",
            "tests/r1_continuity_reference.py": "0fef83d3da2546ee0c284a1059757c680a1c6c73d918d86654f478fedda0b046",
            "tests/fixtures/v1110_w3_proposition_source_spans.json": "522f3e96ed3c07df6a870681321e35ec03e1fb4546bb25ec4e5c164d3c76236f",
            "tests/w3_proposition_reference.py": "2b86d7b17ea240bb9f3a956be6ed983016b15861426c15ce853c5dd5abe9ce90",
        }
        for path, expected in frozen.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            approved_source_span_migrations(FROZEN)

    def test_exact_current_sources_restore_accepted_r2_bytes(self):
        self.assertEqual(set(R3_SOURCE_IDENTITIES), set(R3_APPROVED_REWRITES))
        for path, (previous, current) in R3_SOURCE_IDENTITIES.items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                self.assertNotEqual(previous, current)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), current)
                restored = prior_r3_bytes(path, raw)
                self.assertEqual(hashlib.sha256(restored).hexdigest(), previous)
                with self.assertRaisesRegex(ValueError, "R3 source bytes changed"):
                    prior_r3_bytes(path, raw + b"\n")

    def test_text_inverse_rejects_missing_or_duplicated_registered_blocks(self):
        for path, replacements in R3_APPROVED_REWRITES.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            for current, _ in replacements:
                with self.subTest(path=path, block=current[:60]):
                    self.assertTrue(current)
                    for changed in (source.replace(current, "", 1), source + current):
                        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                            prior_r3_text(path, changed)

    def test_text_inverse_preserves_unregistered_changes(self):
        extra = "\nUnreviewed source change\n"
        for path in R3_APPROVED_REWRITES:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(prior_r3_text(path, source + extra),
                                 prior_r3_text(path, source) + extra)
        self.assertEqual(prior_r3_bytes("unregistered.md", b"changed"), b"changed")

    def test_current_manifest_reconstructs_frozen_r2_exactly(self):
        frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
        current = approved_source_span_migrations(CURRENT)
        self.assertEqual(current["scope"], "v11_4_0_r3_rule_concision_source_spans")
        self.assertEqual(current["version"], "11.4.0")
        projected = deepcopy(current)
        for field in ("scope", "version", "authorizing_reason"):
            projected[field] = frozen[field]
        for extra in R3_ADDITIONAL_READ_SHIFTS:
            self.assertEqual(projected["legacy_profile_read_shifts"].count(extra), 1)
            projected["legacy_profile_read_shifts"].remove(extra)
        seen_ranges = set()

        def restore(value, parent_path=None):
            if isinstance(value, list):
                for child in value:
                    restore(child, parent_path)
            elif isinstance(value, dict):
                path = value.get("path", parent_path)
                if path in R3_SOURCE_IDENTITIES and "candidate_sha256" in value:
                    previous_sha, current_sha = R3_SOURCE_IDENTITIES[path]
                    self.assertEqual(value["candidate_sha256"], current_sha)
                    value["candidate_sha256"] = previous_sha
                for key in ("new_ranges", "current_ranges", "after", "ranges"):
                    if key not in value:
                        continue
                    matches = [before for before, after in R3_RANGE_TRANSITIONS.get(path, ())
                               if value[key] == after]
                    if matches:
                        self.assertEqual(len(matches), 1)
                        seen_ranges.add((path, json.dumps(value[key])))
                        value[key] = deepcopy(matches[0])
                if "new_last_line" in value and path in R3_RANGE_TRANSITIONS:
                    matches = [before for before, after in R3_RANGE_TRANSITIONS[path]
                               if after == [[1, value["new_last_line"]]]]
                    self.assertEqual(len(matches), 1)
                    seen_ranges.add((path, json.dumps([[1, value["new_last_line"]]])))
                    value["new_last_line"] = matches[0][0][1]
                for key, child in value.items():
                    if key not in {"new_ranges", "current_ranges", "after", "ranges"}:
                        restore(child, path)

        restore(projected)
        self.assertEqual(projected, frozen)
        self.assertEqual(seen_ranges, {
            (path, json.dumps(after))
            for path, changes in R3_RANGE_TRANSITIONS.items()
            for _, after in changes
        })

    def test_additional_shifts_require_the_registered_shape_and_full_source(self):
        manifest = approved_source_span_migrations(CURRENT)
        for extra in R3_ADDITIONAL_READ_SHIFTS:
            with self.subTest(path=extra["path"]):
                self.assertEqual(extra["spans"][0]["after"],
                                 [[1, len((ROOT / extra["path"]).read_bytes().splitlines())]])
        with tempfile.TemporaryDirectory() as folder:
            modified = deepcopy(manifest)
            path = R3_ADDITIONAL_READ_SHIFTS[0]["path"]
            row = next(row for row in modified["legacy_profile_read_shifts"] if row["path"] == path)
            row["spans"][0]["after"][0][1] -= 1
            target = Path(folder) / "modified.json"
            target.write_text(json.dumps(modified), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "R3 additional source shift differs"):
                approved_source_span_migrations(target)

    def test_schema_text_and_object_inverses_agree_independently(self):
        path = "core/project_state.schema.yaml"
        source = (ROOT / path).read_text(encoding="utf-8")
        current = yaml.safe_load(source)
        original = deepcopy(current)
        previous = prior_r3_schema(current)
        self.assertEqual(previous, yaml.safe_load(prior_r3_text(path, source)))
        self.assertEqual(current, original)
        changed = deepcopy(current)
        changed["$defs"]["claim_consumption_policy"]["properties"]["paper_source"]["description"] = "changed"
        with self.assertRaisesRegex(AssertionError, "R3 schema inverse rejected"):
            prior_r3_schema(changed)
        changed = deepcopy(current)
        changed["unreviewed_change"] = True
        self.assertTrue(prior_r3_schema(changed)["unreviewed_change"])


if __name__ == "__main__":
    unittest.main()
