"""A2 behavioral controls; synthetic model/source correspondences are not proofs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / 'scripts'):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
import model_code_conformance as audit
import stage_code
import validate_code_delivery as delivery
import validate_user_execution as receipts
import runtime_assurance as runtime
import sync_project as sync
import project_transaction as tx
from tests.test_model_code_conformance import fixture, save, bytes_in
from tests.test_solver_backend_downstream_identity import project_fixture
from tests.test_v900_semantic_identity_binding import identity, framework, structured_question
from tests.test_solver_backend_end_to_end import reference_digest


def policy(entry, stages=('primary',)):
    entry['implementation_conformance_policy'] = {'protocol_version': '1.0.0', 'required_stages': list(stages)}


def declare(root, state, stage='primary'):
    inventory = audit.inspect_project(root, 'Q1', stage, inventory=True)
    if inventory['status'] != 'not_assessed':
        raise AssertionError(inventory)
    anchors = inventory['source_symbols']
    anchor = next((row for row in anchors if row['symbol'] == 'solve'), anchors[0])
    record = {'protocol_version': '1.0.0', 'question': 'Q1', 'stage': stage,
              **inventory['binding'], 'mappings': [], 'reverse_review': []}
    for number, selector in enumerate(inventory['model_selectors'], 1):
        record['mappings'].append({'id': f'MC{number}', 'model_ref': selector, 'relation': 'direct',
            'rationale': 'Synthetic structural mapping only; no mathematical proof claimed.',
            'anchors': [{key: anchor[key] for key in ('path', 'symbol', 'sha256')}]})
    for row in inventory['reverse_candidates']:
        record['reverse_review'].append({'operation_id': row['operation_id'],
            'model_ref': inventory['model_selectors'][0], 'rationale': 'Synthetic lexical acknowledgement only.'})
    state['subproblems']['Q1'].setdefault('implementation_conformance', {})[stage] = record
    save(root, state)
    return record


def source_fixture(root, backend='python', *, enable=True, mapping=True, helper=False):
    state, path, sib = fixture(root, backend, helper=helper)
    (root / 'input.json').write_text('{"value":3}', encoding='utf-8')
    _, config = stage_code.parse_stage_config(path)
    config.update(data_paths=['input.json'], data_sha256=reference_digest(root, ['input.json']),
                  solver='synthetic_direct', random_seed=0, tolerance=1e-8, iteration_or_time_limit=1,
                  expected_workbook='问题一求解/问题一求解结果.xlsx', primary_quality_protocol_version='1.0.0')
    text = path.read_text(encoding='utf-8')
    if backend == 'python':
        text = 'RUN_CONFIG = ' + repr(config) + '\n' + text.split('\n', 1)[1]
        text += '\nif __name__ == "__main__":\n    solve(3, 0, 1)\n'
    else:
        import re
        literal = json.dumps(config, ensure_ascii=False).replace("'", "''")
        text = re.sub(r"RUN_CONFIG = jsondecode\('[^\n]*'\);", lambda _: f"RUN_CONFIG = jsondecode('{literal}');", text)
    path.write_text(text, encoding='utf-8')
    entry = state['subproblems']['Q1']
    entry.update(code=path.relative_to(root).as_posix(), data_hash=config['data_sha256'])
    state['project']['current_phase'] = 'solve_validate'
    if enable:
        policy(entry)
    save(root, state)
    if mapping:
        declare(root, state)
    return state, path, config


def accepted_fixture(root, backend='python', *, analysis=False):
    state = project_fixture(root, (backend,), analysis=analysis)
    sib = identity()
    state['subproblems']['Q1'].update(structured_question(sib))
    (root / '模型论文框架.md').write_text(framework(sib), encoding='utf-8')
    policy(state['subproblems']['Q1'], ('primary','analysis') if analysis else ('primary',))
    save(root, state)
    declare(root, state)
    if analysis:
        declare(root, state, 'analysis')
    return state


class A2BaselineGaps(unittest.TestCase):
    def test_required_missing_mapping_does_not_pass_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state, code, _ = source_fixture(root, mapping=False)
            before = bytes_in(root)
            errors, _ = delivery.validate_script(root, code, 'primary')
            self.assertTrue(any('conformance' in e.lower() for e in errors), errors)
            self.assertEqual(bytes_in(root), before)

    def test_direct_writer_cannot_bypass_missing_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state, code, config = source_fixture(root, mapping=False)
            before = bytes_in(root)
            with self.assertRaises(ValueError):
                delivery.update_state(root, config, code)
            self.assertEqual(bytes_in(root), before)


    def test_direct_writer_configuration_cannot_differ_from_the_inspected_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root)
            altered=deepcopy(config);altered['random_seed']=123
            before=bytes_in(root)
            with self.assertRaisesRegex(ValueError,'caller configuration'):
                delivery.update_state(root,altered,code)
            self.assertEqual(before,bytes_in(root))
            # Only the genuine source-config pair can be delivered.
            delivery.update_state(root,config,code)

    def test_valid_delivery_binds_structure_without_a_workbook(self):
        for backend in ('python','matlab'):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); state,code,config=source_fixture(root,backend)
                errors, _ = delivery.validate_script(root,code,'primary')
                self.assertEqual(errors, [], errors)
                delivery.update_state(root,config,code)
                new=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
                binding=new['subproblems']['Q1']['solver_execution']['primary']
                self.assertIn('conformance_delivery',binding)
                self.assertNotIn('conformance_acceptance',binding)
                self.assertFalse(list(root.rglob('*.xlsx')))

    def test_required_but_unbound_accepted_result_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); accepted_fixture(root)
            before=bytes_in(root)
            hydrated=runtime.hydrate_project_context(root)
            self.assertNotIn('accepted_solution_workbook',hydrated['verified_artifacts'])
            self.assertIn('locked_model_spec',hydrated['verified_artifacts'])
            self.assertEqual(bytes_in(root),before)

    def test_null_policy_does_not_disappear(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); state,code,_=source_fixture(root)
            state['subproblems']['Q1']['implementation_conformance_policy']=None; save(root,state)
            errors,_=delivery.validate_script(root,code,'primary')
            self.assertTrue(any('conformance' in e.lower() for e in errors),errors)

    def test_unchanged_a1_only_still_uses_original_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); state,code,config=source_fixture(root,enable=False)
            errors,_=delivery.validate_script(root,code,'primary')
            self.assertEqual(errors,[],errors)
            delivery.update_state(root,config,code)
            new=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            self.assertNotIn('conformance_delivery',new['subproblems']['Q1']['solver_execution']['primary'])





import conformance_gate as gate
import state_transitions as transitions
from tests.conformance_a2_smoke import prepare as numeric_prepare, prepare_stage as numeric_stage, run_stage
from resolve_runtime import resolve_runtime


def bound_fixture(root, backend='python', analysis=False):
    """Synthetic prior certificates for invalidation tests, not execution evidence."""
    state=accepted_fixture(root,backend,analysis=analysis)
    entry=state['subproblems']['Q1']
    for stage in ('primary','analysis') if analysis else ('primary',):
        check=gate.inspect_gate(root,state,'Q1',stage)
        assert not check['issues'],check
        slot=entry['solver_execution'][stage]
        slot[gate.DELIVERY]=check['delivery_candidate']
        layer='solution_workbook' if stage=='primary' else 'result_analysis_workbook'
        slot[gate.ACCEPTANCE]=gate.acceptance_binding(slot[gate.DELIVERY],entry['validated_artifact_hashes'][layer])
    save(root,state)
    return state


class A2ProtocolTests(unittest.TestCase):
    def test_policy_shape_and_orphans_fail_closed(self):
        invalid=(None,True,{}, {'protocol_version':'2.0.0','required_stages':['primary']},
            {'protocol_version':'1.0.0','required_stages':[]},
            {'protocol_version':'1.0.0','required_stages':['primary','primary']},
            {'protocol_version':'1.0.0','required_stages':['preprocessing']},
            {'protocol_version':'1.0.0','required_stages':['primary'],'skip':True})
        for value in invalid:
            with self.subTest(value=value),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);state,code,config=source_fixture(root)
                state['subproblems']['Q1'][gate.POLICY]=value;save(root,state)
                before=bytes_in(root);result=gate.inspect_gate(root,state,'Q1','primary')
                self.assertTrue(result['issues'],result);self.assertEqual(before,bytes_in(root))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root)
            state['subproblems']['Q1'].pop(gate.POLICY);save(root,state)
            self.assertTrue(gate.inspect_gate(root,state,'Q1','primary')['issues'])

    def test_partial_or_false_certificate_never_qualifies(self):
        for field in ('protocol_version','stage','question','declaration_sha256','authority_sha256','applicability'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);state=bound_fixture(root)
                slot=state['subproblems']['Q1']['solver_execution']['primary']
                slot[gate.DELIVERY][field]={'stage':'analysis','question':'Q2','applicability':'stale'}.get(field,'bad')
                save(root,state)
                self.assertTrue(gate.inspect_gate(root,state,'Q1','primary',boundary='current')['issues'])

    def test_needs_review_is_not_promoted_and_does_not_revoke_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root)
            state['subproblems']['Q1']['implementation_conformance']['primary']['mappings'][0]['relation']='numerical_choice'
            save(root,state);before=bytes_in(root)
            errors,_=delivery.validate_script(root,code,'primary')
            self.assertTrue(any('needs_review' in issue for issue in errors),errors)
            with self.assertRaises(ValueError):delivery.update_state(root,config,code)
            self.assertEqual(before,bytes_in(root))
            self.assertEqual(state['subproblems']['Q1']['human_model_approval_status'],'approved')

    def test_receipt_bundle_and_validated_workbook_are_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root)
            self.assertFalse(gate.inspect_gate(root,state,'Q1','primary',boundary='current')['issues'])
            self.assertTrue(gate.inspect_gate(root,state,'Q1','primary',boundary='receipt',
                receipt={'code_bundle_sha256':'f'*64})['issues'])
            entry=state['subproblems']['Q1'];entry['solver_execution']['primary'][gate.ACCEPTANCE]['workbook_sha256']='f'*64
            save(root,state)
            self.assertTrue(gate.inspect_gate(root,state,'Q1','primary',boundary='current')['issues'])
            self.assertTrue(gate.stored_issues(entry,'Q1'))

    def test_mapping_edit_requires_redelivery_not_hash_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root)
            record=state['subproblems']['Q1']['implementation_conformance']['primary']
            record['mappings'][0]['rationale']='New explanation; not a new numeric execution.'
            save(root,state)
            self.assertFalse(gate.inspect_gate(root,state,'Q1','primary',boundary='delivery')['issues'])
            self.assertTrue(gate.inspect_gate(root,state,'Q1','primary',boundary='receipt')['issues'])
            self.assertNotIn('accepted_solution_workbook',runtime.hydrate_project_context(root)['verified_artifacts'])

    def test_raw_input_drift_and_helper_drift_are_not_laundered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root,helper=True)
            delivery.update_state(root,config,code)
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            for relative in ('input.json','问题一求解/helper.py'):
                path=root/relative;old=path.read_bytes();path.write_bytes(old+b' ')
                try:self.assertTrue(gate.inspect_gate(root,state,'Q1','primary',boundary='receipt')['issues'])
                finally:path.write_bytes(old)

    def test_primary_and_analysis_policies_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root,analysis=True)
            entry=state['subproblems']['Q1']
            entry['implementation_conformance']['analysis']['mappings'][0]['rationale']='analysis changed'
            save(root,state)
            self.assertFalse(gate.inspect_gate(root,state,'Q1','primary',boundary='current')['issues'])
            self.assertTrue(gate.inspect_gate(root,state,'Q1','analysis',boundary='current')['issues'])

    def test_legacy_off_does_not_call_a1_or_parse_user_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,_,_=source_fixture(root,enable=False)
            with patch.object(audit,'inspect_project',side_effect=AssertionError('A1 must be off')):
                self.assertEqual(gate.inspect_gate(root,state,'Q1','primary')['status'],'not_enabled')


class A2TransactionTests(unittest.TestCase):
    def test_delivery_commit_rejects_late_source_input_framework_and_state_edits(self):
        for relative in ('input.json','问题一求解/问题一求解.py','问题一求解/helper.py','模型论文框架.md','state/project_state.yaml'):
            with self.subTest(relative=relative),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);state,code,config=source_fixture(root,helper=True)
                original=tx.commit_project_state;before=(root/'state/project_state.yaml').read_bytes()
                def race(*args,**kwargs):
                    path=root/relative;path.write_bytes(path.read_bytes()+b'\n ')
                    return original(*args,**kwargs)
                with patch.object(delivery.PROJECT_TX,'commit_project_state',side_effect=race):
                    with self.assertRaises((ValueError,RuntimeError)):delivery.update_state(root,config,code)
                self.assertEqual((root/'state/project_state.yaml').read_bytes(),
                    before+b'\n ' if relative=='state/project_state.yaml' else before)
                self.assertFalse((root/tx.JOURNAL_RELATIVE_PATH).exists())

    def test_skill_edit_at_staged_validation_rejects_commit(self):
        with tempfile.TemporaryDirectory() as tmp,tempfile.TemporaryDirectory() as sk:
            root=Path(tmp);state,code,config=source_fixture(root)
            copied=Path(sk)
            for relative in (*audit.POLICY_SOURCES,*gate.EXTRA_SOURCES):
                path=copied/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/relative).read_bytes())
            original=tx.commit_project_state;before=(root/'state/project_state.yaml').read_bytes()
            def race(*args,**kwargs):
                path=copied/audit.CONTRACT;path.write_bytes(path.read_bytes()+b'\n# new contract\n')
                return original(*args,**kwargs)
            with patch.object(audit,'ROOT',copied),patch.object(gate,'ROOT',copied),patch.object(delivery.PROJECT_TX,'commit_project_state',side_effect=race):
                with self.assertRaises((ValueError,RuntimeError)):delivery.update_state(root,config,code)
            self.assertEqual((root/'state/project_state.yaml').read_bytes(),before)

    def test_pending_journal_is_not_automatically_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root)
            journal=root/tx.JOURNAL_RELATIVE_PATH;journal.parent.mkdir(parents=True,exist_ok=True);journal.write_text('{}',encoding='utf-8')
            before=bytes_in(root)
            with self.assertRaises((ValueError,RuntimeError)):delivery.update_state(root,config,code)
            self.assertEqual(before,bytes_in(root))

    def test_prepared_failure_uses_existing_explicit_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root)
            original=tx.commit_project_state
            def interrupted(*args,**kwargs):
                def fail(point):
                    if point=='after_journal_prepared':raise RuntimeError('synthetic interruption after prepare')
                return original(*args,**kwargs,failure_hook=fail)
            with patch.object(delivery.PROJECT_TX,'commit_project_state',side_effect=interrupted):
                with self.assertRaises(RuntimeError):delivery.update_state(root,config,code)
            self.assertTrue((root/tx.JOURNAL_RELATIVE_PATH).exists())
            # No recovery by checker. Use the existing explicit recovery API.
            self.assertTrue(gate.inspect_gate(root,state,'Q1','primary')['issues'])
            tx.recover_project_transaction(root)
            recovered=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            self.assertIn(gate.DELIVERY,recovered['subproblems']['Q1']['solver_execution']['primary'])


class A2StatePropagationTests(unittest.TestCase):
    def test_change_profiles_invalidate_only_applicable_bindings(self):
        contract=yaml.safe_load((ROOT/'core/state_transition_contract.yaml').read_text(encoding='utf-8'))
        for event,primary,analysis,approval in (
            ('primary_code_changed','stale','stale','approved'),
            ('analysis_code_changed','current','stale','approved'),
            ('data_changed','current','stale','approved'),
            ('paper_fragment_changed','current','current','approved'),
            ('figure_bundle_changed','current','current','approved'),
            ('semantic_identity_changed','stale','stale','stale')):
            with self.subTest(event=event),tempfile.TemporaryDirectory() as tmp:
                state=bound_fixture(Path(tmp),analysis=True)
                transitions.apply_transition(state,event=event,source_question='Q1',contract=contract)
                entry=state['subproblems']['Q1'];slots=entry['solver_execution']
                self.assertEqual(slots['primary'][gate.DELIVERY]['applicability'],primary)
                self.assertEqual(slots['analysis'][gate.DELIVERY]['applicability'],analysis)
                self.assertEqual(entry['human_model_approval_status'],approval)
                again=deepcopy(state)
                transitions.apply_transition(state,event=event,source_question='Q1',contract=contract)
                self.assertEqual(again,state)

    def test_sync_detects_changed_mapping_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root)
            entry=state['subproblems']['Q1'];entry['implementation_conformance']['primary']['mappings'][0]['rationale']='Changed mapping'
            save(root,state)
            sync.synchronize(root,write=True)
            first=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            slot=first['subproblems']['Q1']['solver_execution']['primary']
            self.assertEqual(slot[gate.DELIVERY]['applicability'],'stale')
            self.assertEqual(slot[gate.ACCEPTANCE]['applicability'],'stale')
            self.assertEqual(first['subproblems']['Q1']['human_model_approval_status'],'approved')
            sync.synchronize(root,write=True)
            second=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            self.assertEqual(first['subproblems'],second['subproblems'])

    def test_retirement_preserves_stale_provenance_without_active_bundle(self):
        from jsonschema import Draft202012Validator
        schema=yaml.safe_load((ROOT/'core/project_state.schema.yaml').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            state=bound_fixture(Path(tmp));entry=state['subproblems']['Q1']
            contract=yaml.safe_load((ROOT/'core/state_transition_contract.yaml').read_text(encoding='utf-8'))
            transitions.apply_transition(state,event='primary_numerical_source_retired',source_question='Q1',contract=contract)
            slot=entry['solver_execution']['primary'];slot.pop('bundle_sha256');slot.pop('validated_bundle_sha256')
            valid=Draft202012Validator({'$ref':'#/$defs/solver_stage_execution','$defs':schema['$defs']})
            self.assertFalse(list(valid.iter_errors(slot)))
            self.assertFalse(gate.stored_issues(entry,'Q1'))
            slot[gate.DELIVERY]['applicability']='current'
            self.assertTrue(list(valid.iter_errors(slot)))


class A2ActualExecutionTests(unittest.TestCase):
    def test_native_python_main_and_analysis_through_actual_receipt_cli(self):
        from tests.conformance_a2_smoke import run_smoke
        with tempfile.TemporaryDirectory() as tmp:
            report=run_smoke(Path(tmp),'python')
            self.assertTrue(report['drift_rejected'])
            self.assertEqual([row['receipt_cli_exit'] for row in report['stages']],[0,0])

    def test_analysis_only_does_not_force_primary_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,required=('analysis',))
            state,_=run_stage(root,'python','primary',state)
            self.assertNotIn(gate.DELIVERY,state['subproblems']['Q1']['solver_execution']['primary'])
            state,_=run_stage(root,'python','analysis',state)
            self.assertIn(gate.ACCEPTANCE,state['subproblems']['Q1']['solver_execution']['analysis'])
            self.assertIn('accepted_solution_workbook',runtime.hydrate_project_context(root)['verified_artifacts'])

    def test_pqs_failure_cannot_create_conformance_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,required=('primary',))
            code,config=numeric_stage(root,state,'python','primary');delivery.update_state(root,config,code)
            result=subprocess.run([sys.executable,'-B',str(code)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            with patch.object(receipts.NUMERICAL_VALIDATION,'validate_primary_numerical_evidence',return_value=(False,['synthetic PQS rejection'],{})):
                errors=receipts.validate_one(root,root/config['expected_workbook'],state,True)
            self.assertIn('synthetic PQS rejection',errors)
            self.assertNotIn(gate.ACCEPTANCE,state['subproblems']['Q1']['solver_execution']['primary'])
            self.assertEqual(state['subproblems']['Q1']['primary_execution_status'],'rejected')

    def test_receipt_read_set_rejects_change_between_validation_and_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,required=('primary',))
            code,config=numeric_stage(root,state,'python','primary');delivery.update_state(root,config,code)
            result=subprocess.run([sys.executable,'-B',str(code)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'));before=(root/'state/project_state.yaml').read_bytes()
            observed={'project':{},'skill':{}}
            self.assertFalse(receipts.validate_one(root,root/config['expected_workbook'],state,True,conformance_read_set=observed))
            for relative in ('constraints.json',config['expected_workbook']):
                path=root/relative;old=path.read_bytes();path.write_bytes(old+b' ')
                try:
                    with self.assertRaises((ValueError,RuntimeError)):
                        tx.commit_project_state(root,state,expected_generation=tx.state_generation(state),expected_file_hashes=observed['project'])
                    self.assertEqual(before,(root/'state/project_state.yaml').read_bytes())
                finally:path.write_bytes(old)




class A2RoutingAndReplayTests(unittest.TestCase):
    def test_conditional_route_loads_authority_but_does_not_add_parallel_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,_,_=source_fixture(root)
            enabled=resolve_runtime('code_and_solution',project_root=root,question='Q1',objective='optimization')
            self.assertIn(audit.CONTRACT,enabled['load_order'])
            self.assertIn(audit.CONTRACT,[row['path'] for row in enabled['reading_plan']['read_now']])
            self.assertFalse(enabled['conformance_integration']['execution_authorized'])
            self.assertNotIn('model_code_conformance',[row['name'] for row in enabled['pre_delivery_gates']])
            state['subproblems']['Q1'].pop(gate.POLICY);save(root,state)
            disabled=resolve_runtime('code_and_solution',project_root=root,question='Q1',objective='optimization')
            self.assertNotIn(audit.CONTRACT,disabled['load_order'])
            self.assertEqual(enabled['pre_delivery_gates'],disabled['pre_delivery_gates'])
            self.assertEqual(enabled['terminal_outputs'],disabled['terminal_outputs'])
            self.assertNotIn('conformance_integration',disabled)

    def test_redelivery_mapping_change_requires_reacceptance_and_preserves_model_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,required=('primary',))
            state,_=run_stage(root,'python','primary',state)
            entry=state['subproblems']['Q1'];workbook=root/entry['solution_workbook'];oldbytes=workbook.read_bytes()
            old_approval={key:entry[key] for key in ('semantic_revision','semantic_identity_hash','human_model_approval_status')}
            entry['implementation_conformance']['primary']['mappings'][0]['rationale']='Clarified synthetic mapping without another numeric run.'
            save(root,state)
            self.assertTrue(receipts.validate_one(root,workbook,deepcopy(state),False))
            source=root/entry['code'];_,config=stage_code.parse_stage_config(source)
            reports=delivery.update_state(root,config,source)
            self.assertTrue(any(row['event']=='primary_conformance_changed' for row in reports))
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'));entry=state['subproblems']['Q1']
            self.assertEqual(entry['solver_execution']['primary'][gate.ACCEPTANCE]['applicability'],'stale')
            self.assertEqual(entry['primary_execution_status'],'awaiting_user_execution')
            self.assertEqual(old_approval,{key:entry[key] for key in old_approval})
            self.assertFalse(receipts.validate_one(root,workbook,state,True))
            self.assertEqual(entry['solver_execution']['primary'][gate.ACCEPTANCE]['applicability'],'current')
            self.assertEqual(oldbytes,workbook.read_bytes())

    def test_receipt_validation_race_returns_issues_without_candidate_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,required=('primary',))
            code,config=numeric_stage(root,state,'python','primary');delivery.update_state(root,config,code)
            result=subprocess.run([sys.executable,'-B',str(code)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'));before=deepcopy(state)
            numeric=receipts.NUMERICAL_VALIDATION.validate_primary_numerical_evidence
            def race(*args,**kwargs):
                valid=numeric(*args,**kwargs)
                code.write_bytes(code.read_bytes()+b'\n# changed during numeric validation\n')
                return valid
            with patch.object(receipts.NUMERICAL_VALIDATION,'validate_primary_numerical_evidence',side_effect=race):
                errors=receipts.validate_one(root,root/config['expected_workbook'],state,True)
            self.assertTrue(any('conformance' in e for e in errors),errors)
            self.assertEqual(state,before)

    def test_sync_late_mapping_read_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=bound_fixture(root);before=(root/'state/project_state.yaml').read_bytes()
            real=sync.PROJECT_TX.commit_project_state
            def race(*args,**kwargs):
                source=root/state['subproblems']['Q1']['code'];source.write_bytes(source.read_bytes()+b'\n# late\n')
                return real(*args,**kwargs)
            with patch.object(sync.PROJECT_TX,'commit_project_state',side_effect=race):
                with self.assertRaises((ValueError,RuntimeError)):sync.synchronize(root,write=True)
            self.assertEqual(before,(root/'state/project_state.yaml').read_bytes())

    def test_missing_a2_binding_on_prior_delivery_is_not_treated_as_first_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state,code,config=source_fixture(root,enable=False)
            delivery.update_state(root,config,code)
            state=yaml.safe_load((root/'state/project_state.yaml').read_text(encoding='utf-8'))
            policy(state['subproblems']['Q1']);save(root,state)
            report=sync.synchronize(root,write=False)
            self.assertTrue(any('conformance' in issue for issue in report['issues']),report['issues'])

    def test_matlab_stage_mapping_is_statically_supported_without_claiming_native_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=numeric_prepare(root,'matlab',required=('primary',))
            source,config=numeric_stage(root,state,'matlab','primary')
            errors,_=delivery.validate_script(root,source,'primary',require_native=False)
            self.assertEqual(errors,[],errors)
            self.assertEqual(gate.inspect_gate(root,state,'Q1','primary')['status'],'satisfied')
            self.assertEqual(audit.inspect_project(root,'Q1','primary')['native_execution'],'not_run')

if __name__ == '__main__':
    unittest.main()
