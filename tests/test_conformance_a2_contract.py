"""A2 compatibility and authority boundaries, including exact non-waiver controls."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'scripts',ROOT/'tests'):
    if str(path) not in sys.path:sys.path.insert(0,str(path))
import reading_plan_evidence as evidence
import test_reading_plan_evidence as predecessor
from test_conformance_integration import previous_a1_schema
from test_conformance_execution import bound_fixture
import conformance_gate as gate

class A2AuthorityControls(unittest.TestCase):
    def test_precise_disabled_carriers_are_recorded_not_erased(self):
        old,new=predecessor.AuditClosureProjectionTests().pair()
        new['version']='10.3.0';new['assurance']['schema_version']='2.2.0'
        projected,changes=evidence.approved_a2_carrier_change('facts_current',old,new)
        self.assertEqual(projected,old);self.assertNotEqual(old,new)
        actual={row['path']:row['candidate'] for row in changes}
        self.assertEqual(actual['version'],'10.3.0');self.assertEqual(actual['assurance.schema_version'],'2.2.0')
        for key,value in (('execution_authorized',True),('conformance_integration',{'forced':True})):
            changed=deepcopy(new);changed[key]=value
            candidate,_=evidence.approved_a2_carrier_change('facts_current',old,changed)
            self.assertEqual(candidate[key],value);self.assertNotEqual(candidate,old)

    def test_unknown_carriers_and_cases_are_not_waived(self):
        old,new=predecessor.AuditClosureProjectionTests().pair()
        for version,case in (('10.4.0','facts_current'),('10.3.0','new_case')):
            newer=deepcopy(new);newer['version']=version
            self.assertEqual(evidence.approved_a2_carrier_change(case,old,newer),(newer,[]))
        new['version']='10.3.0';new['assurance']['schema_version']='2.3.0'
        projected,_=evidence.approved_a2_carrier_change('facts_current',old,new)
        self.assertEqual(projected['assurance']['schema_version'],'2.3.0')
        self.assertNotEqual(projected,old)

    def test_solver_or_gate_changes_cannot_hide_behind_new_version(self):
        old,new=predecessor.AuditClosureProjectionTests().pair()
        new['version']='10.3.0';new['assurance']['schema_version']='2.2.0'
        new['solver_backend']['environment_verified']=True
        new['pre_delivery_gates']=[]
        projected,_=evidence.approved_a2_carrier_change('facts_current',old,new)
        self.assertTrue(projected['solver_backend']['environment_verified'])
        self.assertIn('pre_delivery_gates',projected)

    def test_old_schema_projection_protects_all_original_constraints(self):
        schema=yaml.safe_load((ROOT/'core/project_state.schema.yaml').read_text(encoding='utf-8'))
        self.assertEqual(previous_a1_schema(schema)['version'],'8.1.0')
        # An unrelated constraint cannot disappear inside the projection.
        changed=deepcopy(schema);changed['additionalProperties']=True
        with self.assertRaises(AssertionError):previous_a1_schema(changed)
        changed=deepcopy(schema);changed['$defs']['solver_stage_execution']['allOf'].append({'required':['invented']})
        with self.assertRaises(AssertionError):previous_a1_schema(changed)

    def test_unknown_bindings_and_boolean_revisions_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=bound_fixture(Path(tmp));entry=state['subproblems']['Q1']
            for field,value in (('semantic_revision',True),('protocol_version','2.0.0'),('independent_review',True)):
                modified=deepcopy(entry);modified['solver_execution']['primary'][gate.DELIVERY][field]=value
                self.assertTrue(gate.stored_issues(modified,'Q1'))

    def test_corrupted_current_certificates_are_not_satisfied_by_hash_self_declarations(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=bound_fixture(Path(tmp));entry=state['subproblems']['Q1']
            entry['solver_execution']['primary'].pop(gate.ACCEPTANCE)
            self.assertTrue(gate.stored_issues(entry,'Q1'))
            entry['solver_execution']['primary'][gate.DELIVERY]['source_bundle_sha256']='a'*64
            self.assertTrue(gate.stored_issues(entry,'Q1'))

    def test_current_docs_do_not_mislabel_a2_as_unimplemented(self):
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertNotIn('A2另行实施',readme)
        authority=yaml.safe_load((ROOT/'core/model_code_conformance_contract.yaml').read_text(encoding='utf-8'))
        self.assertEqual(authority['activation']['integration']['required_structure_result'],'structure_verified')
        self.assertFalse(authority['activation']['automatic_existing_gate_insertion'])
        self.assertEqual(authority['result_semantics']['mathematical_equivalence'],'not_established')
        self.assertFalse(authority['result_semantics']['execution_authorized'])
        self.assertIn('schema',authority['authority']['record_shape'])

if __name__=='__main__':unittest.main()
