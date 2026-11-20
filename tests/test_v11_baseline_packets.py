"""Acceptance of the maintenance packet and its separation from evaluation material."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v11_web_app_packet import CATALOG, FIXTURES, export_packet, packet_files
from v11_client_trial import CLIENTS, lock_budget, prepare


class WebAppPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = yaml.safe_load(CATALOG.read_bytes())["cases"]
        cls.rubric = yaml.safe_load((FIXTURES / "v11_web_app_rubric.yaml").read_bytes())

    def test_each_turn_has_a_distinct_evaluation_and_exportable_inputs(self):
        ids = [case["id"] for case in self.cases]
        scored_ids = [case["id"] for case in self.rubric["cases"]]
        self.assertCountEqual(ids, scored_ids)
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            scored = next(item for item in self.rubric["cases"] if item["id"] == case["id"])
            self.assertEqual(len(case["turns"]), len(scored["turns"]))
            for turn, (inputs, scoring) in enumerate(zip(case["turns"], scored["turns"]), 1):
                with self.subTest(case=case["id"], turn=turn):
                    self.assertTrue(scoring["criteria"])
                    self.assertTrue(all(isinstance(v, str) and v.strip() for v in scoring["criteria"].values()))
                    files = packet_files(case["id"], turn)
                    self.assertEqual(files["用户请求.txt"].decode().strip(), inputs["prompt"].strip())
                    self.assertFalse(any("v11_web_app_rubric" in p or p.startswith("tests/") for p in files))
                    self.assertNotIn((FIXTURES / "v11_web_app_rubric.yaml").read_bytes(), files.values())

    def test_export_is_reproducible_and_preserves_prior_packet(self):
        with TemporaryDirectory() as directory:
            first, second = (Path(directory) / n for n in ("first.zip", "second.zip"))
            for case in self.cases:
                for index in range(1, len(case["turns"]) + 1):
                    with self.subTest(case=case["id"], turn=index):
                        expected = export_packet(case["id"], index, first)
                        self.assertEqual(export_packet(case["id"], index, second), expected)
                        self.assertEqual(sha256(first.read_bytes()).hexdigest(), expected)
                        with ZipFile(first) as archive:
                            self.assertEqual({p: archive.read(p) for p in archive.namelist()}, packet_files(case["id"], index))
                        with self.assertRaises(FileExistsError):
                            export_packet(case["id"], index, first)
                        self.assertEqual(first.read_bytes(), second.read_bytes())
                        first.unlink()
                        second.unlink()

    def test_trial_schedule_is_balanced_blind_and_unmeasured(self):
        root = Path(__file__).resolve().parents[1]
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        with TemporaryDirectory() as temporary:
            folder = Path(temporary) / "new_trial"
            prepare(commit, folder)
            schedule = json.loads((folder / "private_schedule.json").read_bytes())
            sessions = schedule["sessions"]
            counts = Counter((s["client"], s["group"], s["case"]) for s in sessions)
            self.assertEqual(len(counts), len(self.cases) * len(CLIENTS) * 3)
            self.assertEqual(set(counts.values()), {self.rubric["trial_design"]["repeats_per_client_group_case"]})
            blind = json.loads((folder / "blind_scores.json").read_bytes())
            self.assertEqual({s["id"] for s in sessions}, {r["id"] for r in blind})
            self.assertTrue(all("group" not in r and "client" not in r and r["judgment"] is None for r in blind))
            self.assertTrue(all(r["state"] == "not_run" for c in CLIENTS
                                for r in json.loads((folder / f"{c}_observations.json").read_bytes())))
            with self.assertRaisesRegex(ValueError, "real, located"):
                lock_budget(folder, "web")
            self.assertFalse((folder / "web_budget.json").exists())
            with self.assertRaisesRegex(ValueError, "new trial directory"):
                prepare(commit, folder)

    def new_trial(self, directory):
        root = FIXTURES.parents[1]
        pin = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        folder = Path(directory) / "trial"
        prepare(pin, folder)
        return folder, json.loads((folder / "private_schedule.json").read_bytes())

    def test_budget_freezes_only_untouched_candidate_and_located_baseline(self):
        with TemporaryDirectory() as temporary:
            folder, schedule = self.new_trial(temporary)
            path = folder / "web_observations.json"
            rows = json.loads(path.read_bytes())
            by_id = {row["id"]: row for row in rows}
            web = [s for s in schedule["sessions"] if s["client"] == "web"]
            for session in web:
                if session["group"] == "C":
                    continue
                row = by_id[session["id"]]
                row.update(state="completed", session_locator="synthetic-test-only")
                if session["repeat"] == 3:
                    row.update(state="failed", exposure_or_failure="No correct response observed in this trial")
                    continue
                for turn in row["turns"]:
                    turn.update(first_correct_seconds=12 if session["group"] == "A" else 20,
                                request_time_utc="2026-01-01T00:00:00Z", response_locator="synthetic-test-only")
            candidate = next(by_id[s["id"]] for s in web if s["group"] == "C")
            candidate["state"] = "completed"
            path.write_text(json.dumps(rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already started"):
                lock_budget(folder, "web")
            candidate["state"] = "not_run"
            candidate["turns"][0]["first_correct_seconds"] = 0
            path.write_text(json.dumps(rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already started"):
                lock_budget(folder, "web")
            candidate["turns"][0]["first_correct_seconds"] = None
            missing = [by_id[s["id"]]["turns"][0] for s in web
                       if s["group"] == "B" and s["case"] == "intake" and s["repeat"] < 3]
            for turn in missing:
                turn["first_correct_seconds"] = None
            path.write_text(json.dumps(rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "both A and B"):
                lock_budget(folder, "web")
            self.assertFalse((folder / "web_budget.json").exists())

            for turn in missing:
                turn["first_correct_seconds"] = 20
            path.write_text(json.dumps(rows), encoding="utf-8")
            lock_budget(folder, "web")
            budget = json.loads((folder / "web_budget.json").read_bytes())
            self.assertEqual(set(budget["per_turn"]), set(schedule["turns"]))
            self.assertEqual(budget["per_turn"]["intake-1"], {"limit_seconds": 20, "measured": 4, "scheduled": 6})
            self.assertTrue(any(row["state"] == "failed" for row in budget["source_AB_observations"]))
            self.assertFalse((folder / "native_budget.json").exists())
            with self.assertRaises(FileExistsError):
                lock_budget(folder, "web")

    def test_schedule_and_matching_observations_cannot_drop_or_move_trial_slots(self):
        with TemporaryDirectory() as temporary:
            folder, original = self.new_trial(temporary)
            path = folder / "private_schedule.json"
            for client in CLIENTS:
                observations = folder / f"{client}_observations.json"
                initial = json.loads(observations.read_bytes())
                for damage in ("no_AB", "wrong_client", "missing_turn", "packet", "wrong_reference"):
                    with self.subTest(client=client, damage=damage):
                        schedule = deepcopy(original)
                        rows = deepcopy(initial)
                        if damage == "no_AB":
                            remove = {s["id"] for s in schedule["sessions"]
                                      if s["client"] == client and s["group"] in ("A", "B")}
                            schedule["sessions"] = [s for s in schedule["sessions"] if s["id"] not in remove]
                            rows = [r for r in rows if r["id"] not in remove]
                        elif damage == "wrong_client":
                            moved = next(s for s in schedule["sessions"] if s["client"] == client)
                            moved["client"] = next(other for other in CLIENTS if other != client)
                            rows = [r for r in rows if r["id"] != moved["id"]]
                        elif damage == "missing_turn":
                            schedule["turns"].pop("local_to_full-2")
                        elif damage == "packet":
                            schedule["turns"]["intake-1"]["sha256"] = "0" * 64
                        else:
                            schedule["rubric_sha256"] = "0" * 64
                        path.write_text(json.dumps(schedule), encoding="utf-8")
                        observations.write_text(json.dumps(rows), encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "preregistered|frozen"):
                            lock_budget(folder, client)
                        self.assertFalse((folder / f"{client}_budget.json").exists())

    def test_frozen_hard_and_planted_criteria_exist_in_the_corresponding_turn(self):
        criteria = {f"{c['id']}-{n}": set(t["criteria"]) for c in self.rubric["cases"]
                    for n, t in enumerate(c["turns"], 1)}
        design = self.rubric["trial_design"]
        self.assertEqual(set(design["hard_criteria"]), set(criteria))
        for key in ("hard_criteria", "planted_errors"):
            for turn, ids in design[key].items():
                self.assertEqual(len(ids), len(set(ids)))
                self.assertLessEqual(set(ids), criteria[turn])

    def test_invalid_case_or_turn_cannot_export_another_turn(self):
        for case, number in (("unknown-case", 1), ("intake", 0), ("intake", 999)):
            with self.subTest(case=case, turn=number), self.assertRaises(ValueError):
                packet_files(case, number)
