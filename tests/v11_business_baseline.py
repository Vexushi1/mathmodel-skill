"""Report actual v11 maintenance observations. Use --require-target to check these specific interface expectations.

Run from the repository root with the development and Python plotting requirements.
The historical expectation is documentation. Only controls form the baseline gate.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import v11_evidence_observations as paper
import v11_model_observations as model
from v11_plot_observations import plot_observations


def dependency_registered(registered, changed):
    return model.downstream_approval(registered, changed) == "allowed"


def observations(case):
    if case == "01":
        return {"independent_allows_q2": model.downstream_approval(False, True, independent=True) == "allowed",
                "registered_allows_q2": dependency_registered(True, True),
                "missing_edge_allows_q2": dependency_registered(False, True)}
    if case == "02":
        return {"independent_revision_allows_q2": model.downstream_approval(False, False, independent=True) == "allowed",
                "changed_identity_allows_q2": dependency_registered(True, True),
                "revision_only_allows_q2": dependency_registered(True, False)}
    if case == "03":
        return {mode: model.preprocessing(mode) for mode in ("valid", "missing_table", "self", "missing_field")}
    if case == "04":
        return {"valid": model.primary_receipt(), "drop_sheet": model.primary_receipt(drop_metrics=True),
                "blank": model.primary_receipt(None), "text_infinity": model.primary_receipt("Infinity"),
                "boolean": model.primary_receipt(True)}
    if case == "05":
        return {"half_m": model.residual(0.5, "m"), "500_m": model.residual(500, "m"),
                "half_km": model.residual(0.5, "km"), "half_second": model.residual(0.5, "s"),
                "50_cm": model.residual(50, "cm")}
    if case == "06":
        return {"ordered": model.primary_receipt(interval=(0, 1)),
                "reversed": model.primary_receipt(interval=(100, -100))}
    if case == "07":
        return {"holdout_last": paper.holdout_predictions(False), "holdout_first": paper.holdout_predictions(True)}
    if case == "08":
        return {"same_mean": paper.checked_claim("mean"), "total_vs_mean": paper.checked_claim("sum"),
                "permuted_mean": paper.checked_claim("mean", reverse=True)}
    if case == "09":
        return {"ordinary_adapt": paper.citation_result(False, "adapt_to_problem"),
                "retracted_reject": paper.citation_result(True, "reject"),
                "retracted_adapt": paper.citation_result(True, "adapt_to_problem") == "candidate"}
    if case == "10":
        return plot_observations()
    if case == "11":
        return paper.tex_observations()
    if case == "12":
        return paper.appendix_observations()
    if case == "13":
        return {"declared_all_pages": paper.page_coverage("manual", "passed", "Pages 1 through 3 of 3 viewed"),
                "declared_unverified": paper.page_coverage("manual", "unverifiable", "Only page 1 of 3 viewed"),
                "logs_only": paper.page_coverage("machine", "passed", "Only compilation logs; no pages viewed"),
                "partial": paper.page_coverage("manual", "passed", "Page 1 of 3 viewed; pages 2 and 3 not viewed")}
    if case == "14":
        return {"absent": model.legacy_id(None, has_column=False), "spaces": model.legacy_id(" "),
                "real_id": model.legacy_id("PQ-Q1-01"), "bound": model.legacy_id(None, force_strict=True),
                "empty_cell": model.legacy_id(None)}
    raise ValueError(f"Unknown audit case: {case}")


def run_cases(case_ids, expectations):
    results = {}
    for case in case_ids:
        reference = expectations[case]
        actual = observations(case)
        controls, target = reference["controls"], reference["target"]
        historical = reference["observed_v10_35_3"]
        if set(controls) & set(target) or set(historical) != set(target) or set(actual) != set(controls) | set(target):
            raise ValueError(f"Observation keys do not match the frozen case {case}")
        results[case] = {"surface": reference["surface"], "observed": actual,
                         "control_mismatches": [k for k, v in controls.items() if actual[k] != v],
                         "target_mismatches": [k for k, v in target.items() if actual[k] != v],
                         "differences_from_historic_observation": [k for k, v in historical.items() if actual[k] != v]}
    return results


def main():
    os.environ.setdefault("MPLBACKEND", "Agg")
    reference = yaml.safe_load((ROOT / "tests/fixtures/v11_business_baseline.yaml").read_bytes())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(reference["cases"]), action="append")
    parser.add_argument("--without-plot", action="store_true", help="Case 10 runs in the dedicated Figure job")
    parser.add_argument("--require-target", action="store_true")
    args = parser.parse_args()
    ids = list(dict.fromkeys(args.case or reference["cases"]))
    if args.without_plot and "10" in ids:
        if args.case:
            parser.error("--case 10 requires plotting dependencies")
        ids.remove("10")
    rows = run_cases(ids, reference["cases"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    print(json.dumps({"checkout": head, "working_tree_modified": dirty, "historical_baseline": reference["baseline_commit"],
                      "scope": "Synthetic maintenance interfaces only", "cases": rows}, ensure_ascii=True, indent=2))
    return int(any(row["control_mismatches"] or (args.require_target and row["target_mismatches"])
                   for row in rows.values()))


if __name__ == "__main__":
    raise SystemExit(main())
