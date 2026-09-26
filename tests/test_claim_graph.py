from __future__ import annotations
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import sys
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import claim_evidence as audit
from claim_values import Value,EvidenceError
from tests.claim_fixture import record

class ClaimGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=yaml.safe_load((ROOT/'core/project_state.schema.yaml').read_text())
        cls.contract=yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text())
    def setUp(self):self.record=record()
    def validate(self):return audit.validate_record(self.record,self.schema,self.contract)
    def evaluate(self,profiles=None,titles=None):
        vals={f'source:{name}':Value('scalar',Decimal(value),'kg',{'metric':'cost','scenario':name,'sample':'S1'},frozenset({name}))
               for name,value in [('baseline','100'),('candidate','80')]}
        return audit.evaluate(self.record,self.validate(),vals,profiles or [],titles or [],self.contract,{k:{'Q1'} for k in vals})
    def test_good_graph_and_assertion(self):
        d,c=self.evaluate();self.assertEqual(d[0]['value'],'0.2');self.assertEqual(c[0]['arithmetic_status'],'checked')
        self.assertEqual(c[0]['semantic_support'],'not_established')
    def test_mismatched_assertion_is_not_verified(self):
        self.record['claims'][0]['assertion']['value']='.25'
        self.assertEqual(self.evaluate()[1][0]['arithmetic_status'],'blocked')
    def test_null_partial_unknown_version_and_fields_rejected(self):
        cases=[None,{}, {'protocol_version':'2.0.0',**{k:v for k,v in self.record.items() if k!='protocol_version'}},
               {**self.record,'unexpected':'x'}]
        for item in cases:
            with self.subTest(item=str(item)[:40]),self.assertRaises(EvidenceError):audit.validate_record(item,self.schema,self.contract)
    def test_duplicate_id_and_unknown_reference(self):
        self.record['sources'].append(deepcopy(self.record['sources'][0]))
        with self.assertRaises(EvidenceError):self.validate()
        self.record=record();self.record['derivations'][0]['inputs']['baseline']='source:missing'
        with self.assertRaises(EvidenceError):self.validate()
    def test_duplicate_edges_and_wrong_op_parameters(self):
        self.record['derivations'][0]['inputs']['candidate']='source:baseline'
        with self.assertRaises(EvidenceError):self.validate()
        self.record=record();self.record['derivations'][0]['expression']='__import__("os")'
        with self.assertRaises(EvidenceError):self.validate()
    def test_direct_and_indirect_cycles(self):
        self.record['derivations'][0]['inputs']['baseline']='derivation:gain'
        with self.assertRaises(EvidenceError):self.validate()
        self.record=record();self.record['derivations'][0]['inputs']['baseline']='derivation:second'
        self.record['derivations'].append({'id':'second','op':'identity','inputs':{'value':'derivation:gain'}})
        with self.assertRaises(EvidenceError):self.validate()
    def test_node_budget(self):
        limited=deepcopy(self.contract);limited['limits']['graph_nodes']=3
        with self.assertRaises(EvidenceError):audit.validate_record(self.record,self.schema,limited)
    def test_depth_budget(self):
        self.record['derivations']=[{'id':'gain','op':'identity','inputs':{'value':'source:baseline'}}]
        for i in range(65):
            self.record['derivations'].append({'id':f'd{i}','op':'identity',
               'inputs':{'value':'derivation:gain' if i==0 else f'derivation:d{i-1}'}})
        with self.assertRaises(EvidenceError):self.validate()
    def test_bool_and_float_indexes_not_accepted(self):
        for value in (True,1.0):
            self.record['sources'][0]['selector']['header_row']=value
            with self.subTest(value=value),self.assertRaises(EvidenceError):self.validate()
    def test_dangerous_assertion_is_not_evaluated(self):
        self.record['claims'][0]['assertion']['value']='__import__("os").system("echo bad")'
        self.assertEqual(self.evaluate()[1][0]['arithmetic_status'],'blocked')
    def test_wrong_claim_scope(self):
        self.record['claims'][0]['scope']='Q2'
        self.assertEqual(self.evaluate()[1][0]['arithmetic_status'],'blocked')
    def test_profile_display_precision(self):
        claim=self.record['claims'][0];claim['numeric_profile_id']='N1';claim['assertion']['display_location']='body'
        profile={'id':'N1','metric':'cost','unit':'ratio','display_form':'decimal','status':'current','body_decimals':3}
        self.assertEqual(self.evaluate([profile])[1][0]['arithmetic_status'],'checked')
        profile['body_decimals']=True
        self.assertEqual(self.evaluate([profile])[1][0]['arithmetic_status'],'blocked')
    def test_stale_or_wrong_metric_profile(self):
        self.record['claims'][0]['numeric_profile_id']='N1'
        for status,metric in [('stale','cost'),('current','time')]:
            self.assertEqual(self.evaluate([{'id':'N1','metric':metric,'status':status}])[1][0]['arithmetic_status'],'blocked')
    def test_strong_claim_not_proved_by_correct_arithmetic(self):
        for kind in ('optimality','robustness','mechanism'):
            self.record['claims'][0]['kind']=kind
            result=self.evaluate()[1][0]
            self.assertEqual(result['semantic_support'],'not_established')
    def test_assertion_ref_must_belong_to_claim(self):
        self.record['claims'][0]['assertion']['evidence_ref']='source:baseline'
        with self.assertRaises(EvidenceError):self.validate()
    def test_undeclared_or_stale_title_claim(self):
        self.record['claims'][0]['title_claim_id']='TC1'
        self.assertEqual(self.evaluate()[1][0]['arithmetic_status'],'blocked')
        self.assertEqual(self.evaluate(titles=[{'id':'TC1','status':'stale'}])[1][0]['arithmetic_status'],'blocked')

if __name__=='__main__':unittest.main()
