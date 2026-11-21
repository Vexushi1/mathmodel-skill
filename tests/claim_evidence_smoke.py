"""Inspect existing isolated synthetic native-stage outputs without running a solver."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT))
from claim_evidence import inspect_project
from run_config_parser import DELIVERY_MESSAGES, parse_embedded_config
from stage_code import resolve_stage_code
from tests.claim_fixture import install_record


def files(root: Path) -> dict[str,str]:
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def analysis_selector(root: Path, state: dict) -> None:
    """Bind the scalar-solution observation, distinct from the change-from-baseline result."""
    entry = state["subproblems"]["Q1"]
    stage = resolve_stage_code(root, "Q1", "analysis", entry=entry,
                               project_backend=state["execution"]["solver_backend"])
    if stage is None:
        raise ValueError("Missing delivered synthetic analysis source")
    raw = stage.path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["analysis_code_sha256"]:
        raise ValueError("Synthetic analysis source differs from the delivered digest")
    _, config = parse_embedded_config(raw.decode("utf-8-sig"), backend=stage.backend, messages=DELIVERY_MESSAGES)
    # The auxiliary Python fixture and current MATLAB starter phrase this test differently.
    target = {"python": "解是否为正", "matlab": "系数扰动后解是否始终为正"}[stage.backend]
    matches = [row["id"] for row in config["ordinary_experiments"] if row["target"] == target
               and row["method"] in {"参数敏感性", "parameter_sensitivity"}]
    if len(matches) != 1:
        raise ValueError(f"Expected one declared scalar-solution experiment for {target}")
    selector = state["paper_framework"]["claim_evidence"]["sources"][0]["selector"]
    selector["row_key"]["检验ID"] = matches[0]


def run(root: Path) -> dict:
    root=root.resolve()
    if root.is_relative_to(ROOT):
        raise ValueError('The smoke fixture must be outside the repository checkout')
    text=(root/'模型论文框架.md').read_text(encoding='utf-8')
    if 'Synthetic scalar equation a*x=b+offset' not in text:
        raise ValueError('Only the existing explicitly synthetic A2 fixture is supported')
    state_path=root/'state/project_state.yaml';original=state_path.read_bytes()
    state=yaml.safe_load(original);outcomes=[];initial=files(root)
    try:
        for stage in ('primary','analysis'):
            install_record(state,stage)
            if stage == "analysis":
                analysis_selector(root, state)
            state_path.write_text(yaml.safe_dump(state,allow_unicode=True,sort_keys=False),encoding='utf-8')
            before=files(root);report=inspect_project(root)
            assert report['status']=='evidence_checked',report
            assert before==files(root),'B1 wrote into the synthetic project'
            assert report['semantic_support']=='not_established' and not report['execution_authorized']
            outcomes.append({'stage':stage,'status':report['status'],
                'source_qualification':report['source_qualification'],
                'value':report['sources'][0]['value'],'artifact':report['sources'][0]['artifact']})
    finally:
        state_path.write_bytes(original)
    assert files(root)==initial,'Fixture source/approval/workbook changed'
    result={'synthetic_only':True,'backend':state['execution']['solver_backend'],
            'stages':outcomes,'reads_existing_execution_receipts':True,
            'new_numerical_run':False,'semantic_support':'not_established','project_preserved':True}
    (root/'b1_smoke_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.project),ensure_ascii=False))
