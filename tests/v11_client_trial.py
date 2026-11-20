"""Prepare blank, blinded maintenance records. This utility never runs a client."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import re
import secrets
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from v11_web_app_packet import CATALOG, FIXTURES, export_packet, packet_bytes

RUBRIC = FIXTURES / "v11_web_app_rubric.yaml"
CLIENTS = ("web", "native")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def prepare(candidate, output):
    if not re.fullmatch("[0-9a-f]{40}", candidate):
        raise ValueError("supply the exact candidate Git commit")
    if output.exists():
        raise ValueError("use a new trial directory")
    rubric = yaml.safe_load(RUBRIC.read_bytes())
    cases = rubric["cases"]
    repeats = rubric["trial_design"]["repeats_per_client_group_case"]
    root = FIXTURES.parents[1]
    packet_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    candidate_commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"], cwd=root, text=True
    ).strip()
    if candidate_commit != candidate:
        raise ValueError("candidate must identify an existing commit")
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "tests/fixtures", "tests/v11_client_trial.py",
                       "tests/v11_web_app_packet.py"], cwd=root).returncode:
        raise ValueError("commit the maintenance packet and reference before freezing trials")
    with TemporaryDirectory(dir=output.parent) as staging:
        trial = Path(staging) / "trial"
        packets = trial / "packets"
        packets.mkdir(parents=True)
        turns = {}
        turn_counts = {c["id"]: len(c["turns"]) for c in cases}
        for case in cases:
            for number, turn in enumerate(case["turns"], 1):
                key = f"{case['id']}-{number}"
                filename = key + ".zip"
                turns[key] = {
                    "packet": filename, "sha256": export_packet(case["id"], number, packets / filename),
                    "criteria": list(turn["criteria"]),
                }
        schedule = []
        scores = []
        for case, client, group, repeat in itertools.product(cases, CLIENTS, "ABC", range(1, repeats + 1)):
            blind_id = secrets.token_hex(12)
            schedule.append({"id": blind_id, "case": case["id"], "client": client, "group": group,
                             "repeat": repeat})
            for number, turn in enumerate(case["turns"], 1):
                scores.append({
                    "id": blind_id, "case": case["id"], "turn": number, "response_locator": None,
                    "criterion_observations": {key: {"status": None, "evidence": None}
                                               for key in turn["criteria"]},
                    "prohibited_events": None, "judgment": None, "judgment_evidence": None,
                })
        rng = random.SystemRandom()
        rng.shuffle(scores)
        rng.shuffle(schedule)
        schedule.sort(key=lambda row: row["group"] == "C")
        write_json(trial / "private_schedule.json", {
            "packet_commit": packet_commit, "catalog_sha256": digest(CATALOG), "rubric_sha256": digest(RUBRIC),
            "baseline": rubric["baseline_commit"], "candidate": candidate, "repeats": repeats,
            "turns": turns, "sessions": schedule,
        })
        write_json(trial / "blind_scores.json", scores)
        for client in CLIENTS:
            rows = []
            for session in schedule:
                if session["client"] != client:
                    continue
                rows.append({
                    "id": session["id"], "state": "not_run", "client_build": None, "model": None,
                    "settings_tools": None, "session_locator": None, "exposure_or_failure": None,
                    "turns": [{
                        "request_time_utc": None, "first_correct_seconds": None, "response_locator": None,
                        "read_bytes": None, "read_attempts": None, "extra_user_actions": None,
                        "evidence_locators": [],
                    } for _ in range(turn_counts[session["case"]])],
                })
            write_json(trial / f"{client}_observations.json", rows)
        trial.rename(output)


def verify_schedule(trial, schedule):
    """Compare the working schedule and packet files with the frozen fixture design."""
    root = FIXTURES.parents[1]
    pin = schedule.get("packet_commit")
    if not isinstance(pin, str) or not re.fullmatch("[0-9a-f]{40}", pin):
        raise ValueError("missing frozen packet commit")
    sources = {}
    for path, key in ((RUBRIC, "rubric_sha256"), (CATALOG, "catalog_sha256")):
        raw = subprocess.check_output(["git", "--no-replace-objects", "cat-file", "blob",
                                       f"{pin}:{path.relative_to(root).as_posix()}"], cwd=root)
        if hashlib.sha256(raw).hexdigest() != schedule.get(key) or path.read_bytes() != raw:
            raise ValueError("use the frozen rubric and catalog recorded at preparation")
        sources[path] = yaml.safe_load(raw)
    rubric = sources[RUBRIC]
    if schedule.get("baseline") != rubric["baseline_commit"]:
        raise ValueError("baseline commit differs from the frozen design")
    cases = rubric["cases"]
    counts = {case["id"]: len(case["turns"]) for case in cases}
    catalog_counts = {case["id"]: len(case["turns"]) for case in sources[CATALOG]["cases"]}
    repeats = rubric["trial_design"]["repeats_per_client_group_case"]
    if (counts != catalog_counts or not counts or min(counts.values()) < 1
            or type(schedule.get("repeats")) is not int or schedule["repeats"] != repeats):
        raise ValueError("scenario, turn or repeat counts differ from the frozen design")

    slots = set(itertools.product(CLIENTS, "ABC", counts, range(1, repeats + 1)))
    sessions = schedule["sessions"]
    seen_ids = set()
    for session in sessions:
        key = (session["client"], session["group"], session["case"], session["repeat"])
        blind_id = session["id"]
        if (type(session["repeat"]) is not int or key not in slots or not isinstance(blind_id, str)
                or not blind_id or blind_id in seen_ids):
            raise ValueError("unexpected or duplicate preregistered client/group/case/repeat or blind ID")
        slots.remove(key)
        seen_ids.add(blind_id)
    if slots:
        raise ValueError("missing preregistered client/group/case/repeat")

    expected_turns = {f"{case}-{n}" for case, count in counts.items() for n in range(1, count + 1)}
    if set(schedule["turns"]) != expected_turns:
        raise ValueError("missing or unexpected preregistered packet turn")
    for case in cases:
        for number, turn in enumerate(case["turns"], 1):
            key = f"{case['id']}-{number}"
            filename = key + ".zip"
            expected_digest = hashlib.sha256(packet_bytes(case["id"], number)).hexdigest()
            entry = {"packet": filename, "sha256": expected_digest, "criteria": list(turn["criteria"])}
            if schedule["turns"][key] != entry or digest(trial / "packets" / filename) != expected_digest:
                raise ValueError(f"{key}: packet or assessment criteria differ from the frozen design")
    return counts


def lock_budget(trial, client):
    """Archive A/B timing observations for this client before evaluating C."""
    schedule_path = trial / "private_schedule.json"
    schedule_bytes = schedule_path.read_bytes()
    schedule = json.loads(schedule_bytes)
    counts = verify_schedule(trial, schedule)
    rows = json.loads((trial / f"{client}_observations.json").read_bytes())
    records = {row["id"]: row for row in rows}
    expected = [s for s in schedule["sessions"] if s["client"] == client]
    if len(records) != len(rows) or records.keys() != {s["id"] for s in expected}:
        raise ValueError("duplicate, missing or unexpected client observation")
    values = {}
    sources = []
    for session in expected:
        row = records[session["id"]]
        case = session["case"]
        if len(row["turns"]) != counts[case]:
            raise ValueError("wrong number of turns")
        if session["group"] == "C":
            observed_turn = any(
                value is not None and value != [] for turn in row["turns"] for value in turn.values()
            )
            if row["state"] != "not_run" or row["session_locator"] or row.get("exposure_or_failure") or observed_turn:
                raise ValueError("candidate observations already started")
            continue
        if row["state"] not in ("completed", "failed") or not row["session_locator"]:
            raise ValueError("A/B require real, located trials before budget freeze")
        if row["state"] == "failed" and not row["exposure_or_failure"]:
            raise ValueError("record the observed failure")
        sources.append(row)
        for number, turn in enumerate(row["turns"], 1):
            seconds = turn["first_correct_seconds"]
            by_group = values.setdefault(f"{case}-{number}", {"A": [], "B": []})
            if seconds is None:
                continue
            if (type(seconds) not in (float, int) or not math.isfinite(seconds) or seconds < 0
                    or not turn["request_time_utc"] or not turn["response_locator"]):
                raise ValueError("a time must be finite, nonnegative and traceable to request and response")
            by_group[session["group"]].append(seconds)
    budgets = {}
    for key, by_group in values.items():
        if not by_group["A"] or not by_group["B"]:
            raise ValueError(f"{key}: both A and B need a measurable first correct response before freezing")
        times = by_group["A"] + by_group["B"]
        budgets[key] = {"limit_seconds": max(times), "measured": len(times),
                        "scheduled": 2 * schedule["repeats"]}
    write_json(trial / f"{client}_budget.json", {
        "schedule_sha256": hashlib.sha256(schedule_bytes).hexdigest(), "client": client, "source_AB_observations": sources,
        "per_turn": budgets,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("prepare")
    init.add_argument("--candidate", required=True)
    init.add_argument("--output", type=Path, required=True)
    freeze = commands.add_parser("lock-budget")
    freeze.add_argument("trial", type=Path)
    freeze.add_argument("--client", choices=CLIENTS, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.candidate, args.output)
        else:
            lock_budget(args.trial, args.client)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
