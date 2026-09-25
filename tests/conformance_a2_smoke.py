"""A2 opt-in integration on an explicitly synthetic scalar equation fixture.

Never runs a user task. Existing original quality/receipt checks remain active.
The SIB fixture's approval is setup data, not a real human-review assertion.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / 'scripts'):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
import conformance_gate as gate
import model_code_conformance as audit
import runtime_assurance as runtime
import validate_code_delivery as delivery
from tests.audit_auxiliary_smoke import prepare_project, instantiate_stage
from tests.test_v900_semantic_identity_binding import identity, framework, structured_question
from tests.test_model_code_conformance import save


def prepare(root: Path, backend: str = 'python', required=('primary','analysis')) -> dict:
    state = prepare_project(root, backend)
    sib = identity()
    sib.update(research_object='Synthetic scalar equation a*x=b+offset',
               data_scope=[{'id':'D1','source':'accepted preprocessing workbook and constraints.json','role':'input'}],
               variables=[{'id':'V1','symbol':'x','role':'state','domain':'real'}],
               parameters=[{'id':'P1','symbol':'a,b,offset','unit':'dimensionless'}],
               assumptions=[{'id':'A1','statement':'finite scalar inputs, nonzero coefficient'}],
               objective={'sense':'solve','expression':'a*x=b+offset'},
               constraints=[{'id':'C1','expression':'a is finite and nonzero'}],
               preprocessing_decision='project_level',
               algorithm_semantics={'model_family':'scalar_linear_equation','solver_role':'direct_division'})
    state['subproblems']['Q1'].update(structured_question(sib))
    state['subproblems']['Q1'][gate.POLICY]={'protocol_version':'1.0.0','required_stages':list(required)}
    (root/'模型论文框架.md').write_text(framework(sib),encoding='utf-8')
    save(root,state)
    return state


def declare(root: Path, state: dict, stage: str) -> None:
    observed = audit.inspect_project(root,'Q1',stage,inventory=True)
    assert observed['status']=='not_assessed', observed
    # Source mapping is a structural test declaration; not a proof of activation.
    target = 'result_sheets' if observed['binding']['solver_backend']=='python' else '<module>'
    anchor = next(row for row in observed['source_symbols'] if row['symbol']==target)
    record={'protocol_version':'1.0.0','question':'Q1','stage':stage,**observed['binding'],
            'mappings':[],'reverse_review':[]}
    for i,ref in enumerate(observed['model_selectors'],1):
        record['mappings'].append({'id':f'MC{i}','model_ref':deepcopy(ref),'relation':'direct',
            'rationale':'Synthetic structural association only; numerical correctness is checked separately.',
            'anchors':[{key:anchor[key] for key in ('path','symbol','sha256')}]})
    for candidate in observed['reverse_candidates']:
        record['reverse_review'].append({'operation_id':candidate['operation_id'],
            'model_ref':deepcopy(observed['model_selectors'][0]),
            'rationale':'Synthetic lexical acknowledgement, not independent review.'})
    state['subproblems']['Q1'].setdefault('implementation_conformance',{})[stage]=record
    save(root,state)


def prepare_stage(root: Path, state: dict, backend: str, stage: str):
    code, config = instantiate_stage(root,backend,stage,state)
    state['subproblems']['Q1']['code' if stage=='primary' else 'result_analysis_code']=code.relative_to(root).as_posix()
    save(root,state)
    if stage in gate.required_stages(state['subproblems']['Q1']):
        declare(root,state,stage)
    return code,config


def run_stage(root: Path, backend: str, stage: str, state: dict, matlab_command=None):
    code,config=prepare_stage(root,state,backend,stage)
    native={}
    issues,parsed=delivery.validate_script(root,code,stage,matlab_command=matlab_command,
        require_native=backend=='matlab' and bool(matlab_command), native_report=native)
    assert not issues, issues
    delivery.update_state(root,parsed,code)
    command=[sys.executable,'-B',str(code)]
    if backend=='matlab':
        assert matlab_command, 'MATLAB native command required'
        directory=str(code.parent).replace("'","''")
        command=[matlab_command,'-batch',f"cd('{directory}'); {code.stem}();"]
    executed=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'PYTHONUTF8':'1'})
    (root/f'a2_{stage}_native.log').write_text(executed.stdout+executed.stderr,encoding='utf-8')
    assert executed.returncode==0, executed.stdout+executed.stderr
    # Exercise the real coordinator, including transaction read-set and staged validation.
    checked=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/validate_user_execution.py'),str(root),
        '--workbook',config['expected_workbook'],'--write','--strict'],capture_output=True,text=True,
        env={**os.environ,'PYTHONUTF8':'1'})
    (root/f'a2_{stage}_receipt.log').write_text(checked.stdout+checked.stderr,encoding='utf-8')
    assert checked.returncode==0, checked.stdout+checked.stderr
    new=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
    report=gate.inspect_gate(root,new,'Q1',stage,boundary='current')
    assert not report['issues'],report
    assert not report['execution_authorized']
    return new, {'stage':stage,'native_exit':executed.returncode,'receipt_cli_exit':checked.returncode,
        'a2_status':report['status'],'structure_is_not_math_proof':True,
        'analyzer':{key:value for key,value in native.items() if key!='conformance'}}


def run_smoke(root: Path, backend: str, matlab_command=None):
    root.mkdir(parents=True,exist_ok=True)
    state=prepare(root,backend)
    pre=(root/state['preprocessing']['workbook']).read_bytes()
    outcomes=[];primary=None
    for stage in ('primary','analysis'):
        state,row=run_stage(root,backend,stage,state,matlab_command)
        outcomes.append(row)
        if stage=='primary':
            primary=(root/state['subproblems']['Q1']['solution_workbook']).read_bytes()
    assert (root/state['preprocessing']['workbook']).read_bytes()==pre
    assert (root/state['subproblems']['Q1']['solution_workbook']).read_bytes()==primary
    assert 'accepted_solution_workbook' in runtime.hydrate_project_context(root)['verified_artifacts']
    code=root/state['subproblems']['Q1']['code'];old=code.read_bytes()
    code.write_bytes(old+(b'\n# changed\n' if backend=='python' else b'\n% changed\n'))
    try:
        assert gate.inspect_gate(root,state,'Q1','primary',boundary='current')['issues']
        assert 'accepted_solution_workbook' not in runtime.hydrate_project_context(root)['verified_artifacts']
    finally:
        code.write_bytes(old)
    result={'synthetic_only':True,'backend':backend,'stages':outcomes,'drift_rejected':True,
            'preprocessing_preserved':True,'primary_preserved':True,'new_receipt_protocol':False}
    (root/'a2_smoke_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--backend',choices=('python','matlab'),required=True)
    parser.add_argument('--matlab-command')
    args=parser.parse_args()
    print(json.dumps(run_smoke(args.project.resolve(),args.backend,args.matlab_command),ensure_ascii=False))
