"""B1 opt-in boundaries, exact predecessor projection and field-level non-waivers."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from resolve_runtime import resolve_runtime
from tests.claim_schema_reference import previous_a2_schema, previous_b1_schema
from tests import reading_plan_evidence as evidence
from tests import test_reading_plan_evidence as controls
import claim_evidence
from tests.claim_fixture import record

class ClaimContractTests(unittest.TestCase):
    def test_declared_decimal_lexemes_require_unambiguous_shapes(self):
        schema=yaml.safe_load((ROOT/'core/project_state.schema.yaml').read_text(encoding='utf-8'))
        validator=Draft202012Validator({'$ref':'#/$defs/claim_evidence','$defs':schema['$defs']})
        declared=record()
        declared['sources'][0]['selector']['row_key']['value']={'decimal':'1.0000000000000001'}
        self.assertTrue(validator.is_valid(declared))
        for value in (1.5, {'decimal':1.5}, {'decimal':'1','extra':True}):
            with self.subTest(value=value):
                declared['sources'][0]['selector']['row_key']['value']=value
                self.assertFalse(validator.is_valid(declared))
        declared=record()
        declared['claims'][0]['assertion']['value']=1.5
        self.assertFalse(validator.is_valid(declared))
        declared['claims'][0]['assertion']['value']='1.5'
        self.assertTrue(validator.is_valid(declared))
    def test_explicit_route_has_no_writer_or_numerical_authority(self):
        plan=resolve_runtime('claim_evidence_audit')
        self.assertEqual(plan['modules'],[])
        self.assertEqual(plan['terminal_outputs'],['claim_evidence_report'])
        self.assertEqual([x['name'] for x in plan['pre_delivery_gates']],['claim_evidence'])
        self.assertNotIn('--write',plan['pre_delivery_gates'][0]['command'])
        self.assertFalse(plan['task_code_execution_allowed'])
    def test_old_routes_do_not_gain_claim_resources_or_gate(self):
        for intent in ('new_problem_design','code_and_solution','latex','figures','returned_workbook_validation','result_analysis','review'):
            with self.subTest(intent=intent):
                plan=resolve_runtime(intent,objective='optimization')
                self.assertNotIn('core/claim_evidence_contract.yaml',plan['load_order'])
                self.assertNotIn('claim_evidence',[x['name'] for x in plan['pre_delivery_gates']])
    def test_old_schema_all_constraints_exactly_preserved(self):
        schema=yaml.safe_load((ROOT/'core/project_state.schema.yaml').read_text(encoding='utf-8'))
        self.assertEqual(previous_b1_schema(schema)['version'],'8.3.0')
        self.assertEqual(previous_a2_schema(schema)['version'],'8.2.0')
        mutated=deepcopy(schema);mutated['additionalProperties']=True
        with self.assertRaises(AssertionError):previous_a2_schema(mutated)
        mutated=deepcopy(schema);mutated['$defs']['conformance_delivery']['properties']['protocol_version']={'type':'string'}
        with self.assertRaises(AssertionError):previous_a2_schema(mutated)
    def test_exact_carrier_projection_does_not_waive_qualifications(self):
        old,new=controls.AuditClosureProjectionTests().pair()
        new['version']='10.4.0';new['assurance']['schema_version']='2.2.0'
        projected,changes=evidence.approved_b1_carrier_change('facts_current',old,new)
        self.assertEqual(projected,old)
        self.assertIn('10.4.0',[x['candidate'] for x in changes])
        for name,value in [('execution_authorized',True),('claim_evidence',{'forced':True}),('pre_delivery_gates',[])]:
            bad=deepcopy(new);bad[name]=value
            projected,_=evidence.approved_b1_carrier_change('facts_current',old,bad)
            self.assertEqual(projected[name],value);self.assertNotEqual(projected,old)
        for version,case in [('10.5.0','facts_current'),('10.4.0','unlisted_case')]:
            bad=deepcopy(new);bad['version']=version
            self.assertEqual(evidence.approved_b1_carrier_change(case,old,bad),(bad,[]))
    def test_same_a2_contract_and_receipt_versions(self):
        a2=yaml.safe_load((ROOT/'core/model_code_conformance_contract.yaml').read_text(encoding='utf-8'))
        self.assertEqual(a2['version'],'1.1.0')
        self.assertEqual(a2['activation']['integration']['binding_protocol_version'],'1.0.0')
        self.assertEqual(a2['activation']['integration']['required_structure_result'],'structure_verified')
        self.assertFalse(a2['result_semantics']['execution_authorized'])
        ce=yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text(encoding='utf-8'))
        self.assertEqual(ce['compatibility']['a2_authority_algorithm'],'unchanged')
        self.assertEqual(ce['compatibility']['fingerprint_projection'],'forbidden_in_production')
        self.assertEqual(ce['result_semantics']['exit_codes'],claim_evidence.EXIT_CODES)
    def test_profile_protocol_and_no_b2_writer_claimed(self):
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertIn('B2正文消费',readme)
        contract=yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text(encoding='utf-8'))
        self.assertEqual(contract['activation']['project_writer'],'none')
        self.assertEqual(contract['result_semantics']['semantic_support'],'not_established')
        self.assertFalse(contract['activation']['automatic_existing_gate_insertion'])

if __name__=='__main__':unittest.main()
