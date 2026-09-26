"""Read-set adapter to the existing runtime/receipt authorities; no second acceptance rule."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any, Mapping
import model_code_conformance as bounded
import conformance_gate as conformance
import runtime_assurance as runtime
import stage_code
import run_config_parser
from artifact_fingerprint import sha256_file
from execution_protocol import declared_input_paths
from stage_inputs import input_files
from project_transaction import JOURNAL_RELATIVE_PATH
from claim_values import EvidenceError

ROOT=Path(__file__).resolve().parents[1]
CONTRACT='core/claim_evidence_contract.yaml'
AUTHORITY_SOURCES=tuple(dict.fromkeys((*bounded.POLICY_SOURCES,*conformance.EXTRA_SOURCES,
    CONTRACT,'core/workbook_schema.yaml','core/writing_reasoning_contract.yaml',
    'scripts/claim_sources.py','scripts/claim_evidence.py','scripts/claim_values.py','scripts/claim_workbook.py',
    'scripts/analysis_prerequisites.py','scripts/artifact_identity.py')))

class QualificationError(EvidenceError):
    """Original artifact qualification failed; explicit A2 guidance may apply."""

class Sources:
    def __init__(self,root: Path,raw: bytes,state: dict,contract: dict):
        self.root=Path(root).resolve();self.state=state;self.contract=contract
        self.snapshot=runtime.ProjectStateSnapshot(self.root,raw)
        self.read_set={'project':{'state/project_state.yaml':hashlib.sha256(raw).hexdigest()},'skill':{}}
        self.workbooks: dict[str,bytes]={};self.contexts={};self.seen_stages=set()
        self.source_sizes={};self.input_sizes={};self.qualifications={}
        self.snapshot.assert_current()
        for path in AUTHORITY_SOURCES:
            bounded._read(ROOT,path,8*1024*1024,self.read_set['skill'])
        bounded._read(self.root,'模型论文框架.md',contract['limits']['framework_bytes'],self.read_set['project'])

    def assert_current(self):
        if (self.root/JOURNAL_RELATIVE_PATH).exists() or (self.root/JOURNAL_RELATIVE_PATH).is_symlink():
            raise EvidenceError('pending transaction requires explicit recovery')
        conformance.assert_observed(self.root,self.read_set)
        self.snapshot.assert_current()

    def _stage(self,question: str,stage: str):
        if (question,stage) in self.seen_stages:return
        entry=self.state.get('subproblems',{}).get(question)
        if not isinstance(entry,dict):raise EvidenceError('unknown question scope')
        backend=stage_code.current_project_backend(self.state,required=True)
        code=stage_code.resolve_stage_code(self.root,question,stage,entry=entry,project_backend=backend)
        if code is None:raise EvidenceError('missing registered stage source')
        limits=self.contract['limits'];relative=code.path.relative_to(self.root).as_posix()
        raw=bounded._read(self.root,relative,limits['source_file_bytes'],self.read_set['project'])
        _,config=run_config_parser.parse_embedded_config(raw.decode('utf-8-sig'),messages=run_config_parser.DELIVERY_MESSAGES,backend=backend)
        if config.get('stage')!=stage or config.get('solver_backend')!=backend or config.get('problem_name')!=code.problem_name:
            raise EvidenceError('source configuration differs from question/stage/backend')
        deps=config.get('code_dependencies',[])
        if not isinstance(deps,list) or len(deps)+1>limits['source_files']:
            raise EvidenceError('declared source count exceeds budget')
        self.source_sizes[relative]=len(raw)
        for row in deps:
            if not isinstance(row,dict) or set(row)!= {'path','sha256'}:raise EvidenceError('malformed source dependency')
            self.source_sizes[row['path']]=len(bounded._read(self.root,row['path'],limits['source_file_bytes'],self.read_set['project']))
        if len(self.source_sizes)>limits['source_files'] or sum(self.source_sizes.values())>limits['total_source_bytes']:
            raise EvidenceError('total source observation budget exceeded')
        actual=stage_code.stage_code_fingerprint(self.root,code.path,deps)
        if any(self.read_set['project'][row['path']]!=row['sha256'] for row in actual['files']):
            raise EvidenceError('source changed during capture')
        inputs=input_files(self.root,declared_input_paths(config))
        for p in inputs:self.input_sizes[p.relative_to(self.root).as_posix()]=p.stat().st_size
        if len(self.input_sizes)>limits['input_files'] or sum(self.input_sizes.values())>limits['input_bytes']:
            raise EvidenceError('execution input observation budget exceeded')
        for p in inputs:
            name=p.relative_to(self.root).as_posix()
            conformance.merge_read_sets(self.read_set,{'project':{name:sha256_file(p)}})
        # This function also checks original input identity, not just the recorded hash.
        conformance.observe_execution_sources(self.root,self.state,question,
            {'entrypoint':relative,'solver_backend':backend},self.read_set)
        self.seen_stages.add((question,stage))

    def qualify(self,source: Mapping[str,Any]) -> tuple[bytes,dict]:
        question,stage,role=source['question'],source['stage'],source['artifact_role']
        expected_role='solution_workbook' if stage=='primary' else 'result_analysis_workbook'
        if role!=expected_role:raise EvidenceError('artifact role differs from source stage')
        cache_key=(question,stage,role)
        if cache_key in self.qualifications:
            self.assert_current()
            qualified=self.qualifications[cache_key]
            return self.workbooks[qualified['path']],dict(qualified)
        entry=self.state.get('subproblems',{}).get(question,{})
        relative=entry.get(role)
        if not isinstance(relative,str) or not relative:raise EvidenceError('registered artifact path is missing')
        if stage=='analysis':self._stage(question,'primary')
        self._stage(question,stage)
        paths=[relative]
        if stage=='analysis':paths.append(entry['solution_workbook'])
        for path in paths:
            if path not in self.workbooks:
                raw=bounded._read(self.root,path,self.contract['limits']['workbook_bytes'],self.read_set['project'])
                if sum(map(len,self.workbooks.values()))+len(raw)>self.contract['limits']['total_workbook_bytes']:
                    raise EvidenceError('total workbook byte budget exceeded')
                self.workbooks[path]=raw
        # The runtime is the single owner of accepted-primary/analysis qualification.
        context=runtime.hydrate_project_context(self.root,question,state_snapshot=self.snapshot)
        self.contexts[question]=context
        if context['conflicts']:raise QualificationError('; '.join(context['conflicts']))
        rows=context['artifact_evidence'];artifact='accepted_'+role
        selected=[x for x in rows if x.get('scope')==question and x.get('artifact')==artifact]
        locks=[x for x in rows if x.get('scope')==question and x.get('artifact')=='locked_model_spec']
        if len(locks)!=1 or locks[0].get('status')!='verified':
            raise QualificationError('current approved model identity has not been established')
        if len(selected)!=1 or selected[0].get('status')!='verified':
            reason=selected[0].get('reason','') if selected else 'missing runtime evidence'
            raise QualificationError('original artifact qualification failed: '+reason)
        row=selected[0];raw=self.workbooks[relative]
        if row.get('path')!=relative or row.get('actual_sha256')!=hashlib.sha256(raw).hexdigest():
            raise EvidenceError('qualified workbook and captured bytes differ')
        self.assert_current()
        qualified={'source_qualification':'verified','artifact':artifact,'question':question,'stage':stage,
                    'path':relative,'sha256':hashlib.sha256(raw).hexdigest(),'model_identity':locks[0].get('actual_sha256')}
        self.qualifications[cache_key]=qualified
        return raw,dict(qualified)

    def revalidation_guidance(self,question: str,stage: str) -> list[dict]:
        """Never execute these commands or manufacture new current bindings."""
        entry=self.state.get('subproblems',{}).get(question,{})
        required=conformance.required_stages(entry)
        steps=[]
        for current in (('primary','analysis') if stage=='analysis' else ('primary',)):
            if current not in required:continue
            report=conformance.inspect_gate(self.root,self.state,question,current,boundary='delivery')
            conformance.merge_read_sets(self.read_set,report['observed_sources'])
            old=entry.get('solver_execution',{}).get(current,{}).get('conformance_delivery',{})
            candidate=report.get('delivery_candidate',{})
            field='code' if current=='primary' else 'result_analysis_code'
            workbook='solution_workbook' if current=='primary' else 'result_analysis_workbook'
            commands=[]
            if isinstance(entry.get(field),str):
                commands.append(['python','scripts/validate_code_delivery.py',str(self.root),'--script',entry[field],
                                 '--stage',current,'--write','--strict'])
            if isinstance(entry.get(workbook),str):
                commands.append(['python','scripts/validate_user_execution.py',str(self.root),'--workbook',entry[workbook],
                                 '--write','--strict'])
            steps.append({'question':question,'stage':current,'old_authority_sha256':old.get('authority_sha256'),
                'current_authority_sha256':candidate.get('authority_sha256'),
                'current_structure_status':report.get('structure_status','not_assessed'),
                'observation_issues':report['issues'],'commands':commands,'commands_executed':False,
                'prerequisites_before_commands': ([
                    'After primary revalidation, explicitly reassess and record the Analysis Necessity Gate '
                    'under the existing workflow before analysis delivery. Do not automatically restore its old reason.'
                ] if current=='analysis' else []),
                'native_matlab_command_may_be_required':self.state.get('execution',{}).get('solver_backend')=='matlab',
                'guidance':'Explicitly redeliver and revalidate using the original coordinators in dependency order. '
                           'Unchanged source/input/workbook may reuse the same original receipt; only those gates decide. '
                           'Changed execution evidence may require a real rerun. Do not delete policies or refresh old hashes.'})
        return steps
