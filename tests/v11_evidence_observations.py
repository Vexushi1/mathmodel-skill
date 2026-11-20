"""Synthetic evidence, plotting and paper observations. No contest project or network access."""

import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

import openpyxl
import yaml

from v11_plot_observations import template
from audit_latex_project import audit_cumcm_2026_compliance
from audit_paper_prose import audit_bibliography, _audit_cross_references
from claim_evidence import evaluate, validate_record
from claim_workbook import Workbook
from literature_evidence import validate_report
from score_submission import score_submission
from tests import claim_fixture, test_literature_evidence, test_literature_snapshot, test_v820_final_review_compliance

ROOT = Path(__file__).resolve().parents[1]


def holdout_predictions(reordered):
    folder = ROOT / "templates/code/starter"
    with patch.dict(sys.modules, {"comparison_numerics": template(folder / "comparison_numerics.py")}):
        example = template(folder / "analysis_comparison.py")
    times = [4, 0, 1, 2, 3] if reordered else [0, 1, 2, 3, 4]
    inputs = {"train_t": [0, 1, 2, 3], "train_y": [0, 1, 4, 9], "evaluation_t": times,
              "scenarios": ["holdout" if t == 4 else f"train-{t}" for t in times], "model_difference_threshold": 1}
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = {"tolerance": 1e-10, "primary_workbook": "q.xlsx"}
        tables = example.primary_tables(config, inputs)
        example.write_workbook(root / "q.xlsx", tables)
        comparison = example.analysis_tables(root, config, inputs)
        book = openpyxl.load_workbook(root / "q.xlsx", read_only=True, data_only=True)
        try:
            details = next(row[2] for row in book["状态明细"].values if row[4] == "holdout")
            core_prediction = next(row[1] for row in book["核心指标"].values if row[0] == "留出预测")
        finally:
            book.close()
        if not math.isclose(details, 16) or not math.isclose(comparison["多模型检验"][1][8], 16):
            raise ValueError("Expected the holdout observation in the detail table and comparison baseline")
        return round(core_prediction, 8)


def checked_claim(candidate_reducer, *, reverse=False):
    contract = yaml.safe_load((ROOT / "core/claim_evidence_contract.yaml").read_bytes())
    schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_bytes())
    data = [["cost", scenario, key, 10, "kg"] for scenario in ("base", "new") for key in ("s1", "s2")]
    workbook = Workbook(claim_fixture.workbook(data), contract)
    sources, nodes, observations = [], [], {}
    for scenario in ("base", "new"):
        members = []
        for key in ("s1", "s2"):
            source = claim_fixture.source(scenario + key, scenario)
            source["selector"]["row_key"]["sample"] = key
            sources.append(source)
            ref = "source:" + source["id"]
            members.append(ref)
            observations[ref] = workbook.select(source["selector"], [])[0]
        if scenario == "new" and reverse:
            members.reverse()
        nodes.append({"id": scenario, "op": "aggregate", "axis": "sample",
                      "reducer": candidate_reducer if scenario == "new" else "mean", "inputs": {"items": members}})
    nodes.append({"id": "delta", "op": "difference", "comparison_axis": "scenario",
                  "inputs": {"baseline": "derivation:base", "candidate": "derivation:new"}})
    claim = {"id": "delta_claim", "scope": "Q1", "kind": "comparative", "text": "Synthetic cost difference.",
             "evidence": [{"ref": "derivation:delta", "relation": "supports"}],
             "assertion": {"evidence_ref": "derivation:delta", "value": 10 if candidate_reducer == "sum" else 0,
                           "unit": "kg"}}
    record = {"protocol_version": "1.0.0", "sources": sources, "derivations": nodes, "claims": [claim]}
    ordering = validate_record(record, schema, contract)
    _, claims = evaluate(record, ordering, observations, [], [], contract, {ref: {"Q1"} for ref in observations})
    return claims[0]["arithmetic_status"] == "checked"


def citation_result(retracted, disposition):
    report = test_literature_evidence.LiteratureEvidenceContractTests().report()
    report["scope"]["problem_contract_anchor"] = "Q1.md#Q1"
    report["sources"][0]["is_retracted"] = retracted
    report["methods"][0]["disposition"] = disposition
    if validate_report(report)["status"] != "passed":
        return "invalid"
    snapshot = test_literature_snapshot.SNAP
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "Q1.md").write_text("Q1 synthetic frozen conditions.", encoding="utf-8")
        (root / "research.json").write_text(json.dumps(report), encoding="utf-8")
        preview = snapshot.preview(root, "Q1", "Q1.md", "research.json")
        snapshot.record(root, "Q1", "Q1.md", "research.json", write=True,
                        expected_contract_sha256=preview["contract"]["sha256"],
                        expected_report_sha256=preview["report_source"]["sha256"])
        inspection = snapshot.inspect(root, "Q1")
        if inspection["status"] != "current":
            return "stale"
        return "candidate" if inspection["citation_candidates"] else "recorded_only"


def tex_observations():
    bib = "@article{present,\n title={x}\n}\n"
    def citation_codes(tex):
        return {issue.code for issue in audit_bibliography(tex, bib)}

    def unused_labels(tex):
        return sorted(issue.evidence for issue in _audit_cross_references(
            tex + r"\label{fig:a}\label{fig:b}") if issue.code == "unreferenced_label")

    return {
        "simple_missing_detected": "missing_bib_key" in citation_codes(r"\parencite{missing}"),
        "annotated_missing_detected": "missing_bib_key" in citation_codes(r"\parencite[see][p.~17]{missing}"),
        "annotated_present_reported_unused": "unused_bib_entries" in citation_codes(r"\parencite[see][p.~17]{present}"),
        "single_unused": unused_labels(r"\cref{fig:a}\cref{fig:b}"),
        "multi_unused": unused_labels(r"\cref{fig:a,fig:b}"),
    }


def appendix_observations():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "state").mkdir()
        (root / "final_latex").mkdir()
        (root / "state/project_state.yaml").write_text('project: {competition: CUMCM, competition_edition: "2026"}',
                                                        encoding="utf-8")
        prefix = r"\begin{document}\section*{AI工具使用声明}本参赛队在竞赛过程中未使用任何AI工具。\printbibliography"
        begin, end = r"\begin{appendices}", r"\end{appendices}\end{document}"
        heading, text = r"\section*{附录}", "本论文没有用到程序。本论文没有支撑材料。"
        fragments = {"correct": begin + heading + text, "empty": begin + heading, "outside": heading + text + begin}
        return {name: not bool(audit_cumcm_2026_compliance(root / "final_latex/main.tex", prefix + fragment + end))
                for name, fragment in fragments.items()}


def page_coverage(mode, status, evidence):
    fixture = test_v820_final_review_compliance.TestV820FinalReviewCompliance()
    fixture.config = json.loads((ROOT / "config/review_weights.json").read_bytes())
    report = fixture.valid_report()
    row = next(entry for entry in report["coverage"] if entry["check_family"] == "rendered_page_surface")
    row.update(verification_mode=mode, status=status, evidence=evidence)
    try:
        verdict = score_submission(fixture.config, report)
    except ValueError:
        return False
    return verdict["review_status"] == "passed"
