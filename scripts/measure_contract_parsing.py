#!/usr/bin/env python3
"""Short GitHub-only parser microbenchmark; excludes disk I/O and gate execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
import subprocess
from time import perf_counter

import yaml
import safe_yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ("core/project_state.schema.yaml", "core/output_contract.yaml",
             "core/workbook_schema.yaml")


def measure(root: Path = ROOT, repeats: int = 3) -> dict:
    if not 1 <= repeats <= 20:
        raise ValueError("repeats must be between 1 and 20")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()
    rows = []
    for relative in CONTRACTS:
        raw = (root / relative).read_bytes()
        text = raw.decode("utf-8")
        expected = yaml.safe_load(text)
        timings = {}
        for mode, use_c, cache in (("safe_python", False, False),
                                   ("safe_c", True, False), ("safe_c_cached", True, True)):
            safe_yaml.clear_cache()
            if cache:
                safe_yaml.safe_load(text, use_c=use_c, cache=True)  # Explicit warm cache.
            samples = []
            for _ in range(repeats):
                start = perf_counter()
                value = safe_yaml.safe_load(text, use_c=use_c, cache=cache)
                samples.append(perf_counter() - start)
                if value != expected:
                    raise ValueError(f"parser result differs for {relative}: {mode}")
            timings[mode] = {"loader": safe_yaml.loader_name(use_c=use_c),
                             "warm_cache": cache, "seconds": samples,
                             "median_seconds": median(samples)}
        rows.append({"path": relative, "source_bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest(), "timings": timings})
    safe_yaml.clear_cache()
    return {"schema_version": 1, "measurement": "contract_parsing_microbenchmark",
            "scope": "in_memory_parse_hash_and_copy_only_not_full_regression_or_solver",
            "head": head, "python": platform.python_version(), "platform": platform.platform(),
            "pyyaml": yaml.__version__, "c_extension_available": hasattr(yaml, "CSafeLoader"),
            "repeats": repeats, "contracts": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = measure(repeats=args.repeats)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
