from __future__ import annotations
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import claim_evidence as audit
from claim_sources import Sources
from claim_workbook import Workbook
import conformance_gate
from tests import conformance_a2_smoke as smoke
from tests.test_model_code_conformance import save,bytes_in
from tests.claim_fixture import install_record

class ClaimEvidenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.seed=Path(cls.tmp.name)/'seed';cls.seed.mkdir()
        state=smoke.prepare(cls.seed,'python',required=('primary','analysis'))
        state,_=smoke.run_stage(cls.seed,'python','primary',state)
        state,_=smoke.run_stage(cls.seed,'python','analysis',state)
        cls.state=state
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmp2=tempfile.TemporaryDirectory();self.root=Path(self.tmp2.name)/'project';shutil.copytree(self.seed,self.root)
        self.state=deepcopy(self.__class__.state);install_record(self.state);save(self.root,self.state)
    def tearDown(self):self.tmp2.cleanup()
    def test_actual_pipeline_source_qualified_and_readonly(self):
        before=bytes_in(self.root);report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'evidence_checked',report)
        self.assertFalse(report['execution_authorized']);self.assertEqual(report['semantic_support'],'not_established')
        self.assertEqual(bytes_in(self.root),before)
    def test_actual_analysis_uses_accepted_runtime_evidence(self):
        install_record(self.state,'analysis');save(self.root,self.state)
        before=bytes_in(self.root);report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'evidence_checked',report)
        self.assertEqual(report['sources'][0]['artifact'],'accepted_result_analysis_workbook')
        self.assertEqual(bytes_in(self.root),before)
        self.state['subproblems']['Q1']['result_analysis_status']='pending';save(self.root,self.state)
        self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')
    def test_cli_outputs_status_and_no_permission_grant(self):
        cmd=[sys.executable,'-B',str(ROOT/'scripts/claim_evidence.py'),str(self.root)]
        proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(json.loads(proc.stdout)['status'],'evidence_checked')
    def test_no_requested_arithmetic_is_reported_as_not_requested(self):
        record=self.state['paper_framework']['claim_evidence']
        record['claims'][0]['evidence']=[{'ref':'source:answer','relation':'supports'}]
        record['claims'][0].pop('assertion')
        save(self.root,self.state)
        report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'evidence_checked',report)
        self.assertEqual(report['source_qualification'],'verified')
        self.assertEqual(report['selection_status'],'selected')
        self.assertEqual(report['arithmetic_status'],'not_requested')
    def test_unquoted_decimal_assertion_does_not_match_after_yaml_float_rounding(self):
        self.state['paper_framework']['claim_evidence']['claims'][0]['assertion']['value']='4.0000000000000001'
        save(self.root,self.state)
        path=self.root/'state/project_state.yaml';original=path.read_text(encoding='utf-8')
        quoted="value: '4.0000000000000001'"
        self.assertIn(quoted,original)
        path.write_text(original.replace(quoted,'value: 4.0000000000000001',1),encoding='utf-8')
        report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked',report)
        self.assertTrue(any('record schema' in error for error in report['errors']),report)
    def test_missing_record_does_not_load_new_contract_or_workbook(self):
        self.state['paper_framework'].pop('claim_evidence');save(self.root,self.state)
        with patch.object(audit,'Sources',side_effect=AssertionError('must not load')):
            report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'not_assessed')
    def test_source_status_alone_cannot_qualify_changed_workbook(self):
        p=self.root/self.state['subproblems']['Q1']['solution_workbook'];p.write_bytes(p.read_bytes()+b'changed')
        before=bytes_in(self.root);report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked');self.assertEqual(bytes_in(self.root),before)
    def test_data_drift_and_source_drift_rejected(self):
        for relative in ('constraints.json',self.state['subproblems']['Q1']['code']):
            p=self.root/relative;original=p.read_bytes();p.write_bytes(original+b' ')
            self.assertEqual(audit.inspect_project(self.root)['status'],'blocked');p.write_bytes(original)
    def test_input_drift_during_selection_blocked(self):
        original=Workbook.select
        def drift(reader,*args):
            got=original(reader,*args);p=self.root/'constraints.json';p.write_bytes(p.read_bytes()+b' ');return got
        with patch.object(Workbook,'select',new=drift):report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked');self.assertTrue(any('read-set' in x for x in report['errors']))
    def test_state_and_workbook_drift_during_selection_blocked(self):
        original=Workbook.select
        for relative in ('state/project_state.yaml',self.state['subproblems']['Q1']['solution_workbook']):
            p=self.root/relative;old=p.read_bytes()
            def drift(reader,*args):
                got=original(reader,*args);p.write_bytes(old+b' ');return got
            with patch.object(Workbook,'select',new=drift):report=audit.inspect_project(self.root)
            self.assertEqual(report['status'],'blocked');p.write_bytes(old)
    def test_upstream_source_drift_during_analysis_selection_is_blocked(self):
        install_record(self.state,'analysis');save(self.root,self.state)
        original=Workbook.select
        def drift(reader,*args):
            selected=original(reader,*args)
            path=self.root/self.state['subproblems']['Q1']['code']
            path.write_bytes(path.read_bytes()+b'\n# changed\n')
            return selected
        with patch.object(Workbook,'select',new=drift):report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked')
        self.assertTrue(any('read-set' in x for x in report['errors']))
    def test_repeated_selectors_share_one_qualification_but_not_two_observations(self):
        item=self.state['paper_framework']['claim_evidence']
        second=deepcopy(item['sources'][0]);second['id']='same_answer';item['sources'].append(second)
        save(self.root,self.state)
        import claim_sources
        original=claim_sources.runtime.hydrate_project_context
        with patch.object(claim_sources.runtime,'hydrate_project_context',wraps=original) as call:
            report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'evidence_checked',report)
        self.assertEqual(call.call_count,1)
        self.assertEqual(report['sources'][0]['physical_sources'],report['sources'][1]['physical_sources'])
    def test_pending_transaction_not_recovered(self):
        from project_transaction import JOURNAL_RELATIVE_PATH
        p=self.root/JOURNAL_RELATIVE_PATH;p.write_text('pending')
        self.assertEqual(audit.inspect_project(self.root)['status'],'blocked');self.assertEqual(p.read_text(),'pending')
    def test_null_unknown_schema_or_role_rejected(self):
        for bad in (None,{'protocol_version':'99.0.0'}):
            self.state['paper_framework']['claim_evidence']=bad;save(self.root,self.state)
            self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')
        install_record(self.state);self.state['paper_framework']['claim_evidence']['sources'][0]['artifact_role']='attachments'
        save(self.root,self.state);self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')
    def test_source_path_escape_rejected(self):
        self.state['subproblems']['Q1']['solution_workbook']='../foreign.xlsx';save(self.root,self.state)
        self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')
    def test_alias_and_duplicate_yaml_key_blocked(self):
        p=self.root/'state/project_state.yaml';old=p.read_bytes()
        for extra in (b'\npaper_framework: {}\n',b'\nx: &x [1]\ny: *x\n'):
            p.write_bytes(old+extra);self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')
        p.write_bytes(old)
    def test_needs_review_formula_does_not_change_qualification(self):
        self.state['paper_framework']['numeric_profile'][0]['status']='stale';save(self.root,self.state)
        self.assertEqual(audit.inspect_project(self.root)['status'],'blocked')

class ClaimCrossVersionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'project';self.root.mkdir()
        self.root=self.root.resolve()
        fixtures=ROOT/'tests/fixtures/claim_evidence'
        meta=json.loads((fixtures/'a2_baseline_provenance.json').read_text(encoding='utf-8'))
        data=(fixtures/'a2_baseline_synthetic.zip').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),meta['capsule_sha256'])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(set(z.namelist()),set(meta['files']))
            for name in z.namelist():
                p=self.root/name;self.assertTrue(p.resolve().is_relative_to(self.root));p.parent.mkdir(parents=True,exist_ok=True)
                raw=z.read(name);self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['files'][name]);p.write_bytes(raw)
        self.state=yaml.safe_load((self.root/'state/project_state.yaml').read_text(encoding='utf-8'))
        install_record(self.state);save(self.root,self.state)
    def tearDown(self):self.tmp.cleanup()
    def cli(self,script,*args):
        proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/script),str(self.root),*args],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
    def test_real_old_authority_fails_then_explicit_revalidation_restores_same_workbook(self):
        before=bytes_in(self.root);entry=self.state['subproblems']['Q1'];approval={k:entry[k] for k in entry if 'approved' in k or 'approval' in k}
        report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked');self.assertEqual(bytes_in(self.root),before)
        self.assertTrue(report['revalidation_guidance'])
        first=report['revalidation_guidance'][0]
        self.assertNotEqual(first['old_authority_sha256'],first['current_authority_sha256'])
        workbooks={k:v for k,v in before.items() if k.endswith('.xlsx')}
        # Only original delivery and receipt coordinators run, never the numerical scripts.
        for stage,field,workbook in [('primary','code','solution_workbook'),('analysis','result_analysis_code','result_analysis_workbook')]:
            if stage=='analysis':
                current=yaml.safe_load((self.root/'state/project_state.yaml').read_text(encoding='utf-8'))
                self.assertFalse(current['subproblems']['Q1'].get('result_analysis_requirement_reason'))
                # Explicit synthetic author reassessment, not an automatic B1 state repair.
                current['subproblems']['Q1']['result_analysis_requirement_reason']='Reconfirmed synthetic coefficient stress test after primary revalidation'
                save(self.root,current)
                guide=Sources(self.root,(self.root/'state/project_state.yaml').read_bytes(),current,
                              yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text(encoding='utf-8')))
                self.assertTrue(guide.revalidation_guidance('Q1','analysis')[-1]['prerequisites_before_commands'])
            self.cli('validate_code_delivery.py','--script',entry[field],'--stage',stage,'--write','--strict')
            self.cli('validate_user_execution.py','--workbook',entry[workbook],'--write','--strict')
        after=yaml.safe_load((self.root/'state/project_state.yaml').read_text(encoding='utf-8'))
        self.assertEqual(approval,{k:after['subproblems']['Q1'][k] for k in approval})
        self.assertEqual(workbooks,{k:v for k,v in bytes_in(self.root).items() if k.endswith('.xlsx')})
        result=audit.inspect_project(self.root);self.assertEqual(result['status'],'evidence_checked',result)
        install_record(after,'analysis');save(self.root,after)
        result=audit.inspect_project(self.root);self.assertEqual(result['status'],'evidence_checked',result)
    def test_changed_input_cannot_be_repaired_by_revalidation_guidance(self):
        p=self.root/'constraints.json';p.write_text('{"right_hand_side_offset":99}')
        before=bytes_in(self.root);report=audit.inspect_project(self.root)
        self.assertEqual(report['status'],'blocked');self.assertEqual(bytes_in(self.root),before)
        entry=self.state['subproblems']['Q1']
        proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/validate_code_delivery.py'),str(self.root),
                            '--script',entry['code'],'--stage','primary','--write','--strict'],capture_output=True)
        self.assertNotEqual(proc.returncode,0);self.assertEqual(bytes_in(self.root),before)

class ClaimActivationCompatibilityTests(unittest.TestCase):
    def test_new_projects_without_a2_and_analysis_only_retain_original_policies(self):
        for policy in ('none','analysis_only'):
            with self.subTest(policy=policy),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'project';root.mkdir()
                state=smoke.prepare(root,'python',required=('analysis',))
                if policy=='none':state['subproblems']['Q1'].pop(conformance_gate.POLICY)
                save(root,state)
                state,_=smoke.run_stage(root,'python','primary',state)
                state,_=smoke.run_stage(root,'python','analysis',state)
                install_record(state,'analysis');save(root,state)
                before=bytes_in(root);report=audit.inspect_project(root)
                self.assertEqual(report['status'],'evidence_checked',report)
                self.assertEqual(before,bytes_in(root))
                primary=state['subproblems']['Q1']['solver_execution']['primary']
                self.assertNotIn(conformance_gate.DELIVERY,primary)
                self.assertNotIn(conformance_gate.ACCEPTANCE,primary)

if __name__=='__main__':unittest.main()
