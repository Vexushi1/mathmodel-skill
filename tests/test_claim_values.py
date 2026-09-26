"""Bounded arithmetic tests; no workbook qualification is inferred here."""
from __future__ import annotations
import unittest
from decimal import Decimal
from pathlib import Path
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import claim_values as values

class ClaimValuesTests(unittest.TestCase):
    def setUp(self):
        self.contract=yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text())
    def value(self,x,unit='kg',scenario='baseline',origin=None,kind='scalar',**axes):
        return values.Value(kind,Decimal(str(x)) if kind=='scalar' else x,unit,
            {'metric':'cost','scenario':scenario,'sample':'S1',**axes},frozenset({origin or scenario}))
    def calc(self,op,base=100,candidate=80,unit='kg',**params):
        args={'baseline':self.value(base,unit),'candidate':self.value(candidate,unit,'candidate')}
        return values.derive({'id':'d','op':op,'inputs':{'baseline':'source:b','candidate':'source:c'},
                             'comparison_axis':'scenario',**params},args,self.contract)
    def test_improvement_has_explicit_direction(self):
        self.assertEqual(self.calc('improvement',direction='lower').value,Decimal('.2'))
        self.assertEqual(self.calc('improvement',direction='higher').value,Decimal('-.2'))
    def test_difference_sign(self): self.assertEqual(self.calc('difference').value,Decimal('-20'))
    def test_percent_and_points_are_distinct(self):
        self.assertEqual(self.calc('percentage_points',40,50,'%').value,Decimal('10'))
        self.assertEqual(self.calc('percentage_points',40,50,'%').unit,'百分点')
        self.assertEqual(self.calc('relative_change',40,50,'%').value,Decimal('.25'))
        with self.assertRaises(values.EvidenceError):self.calc('percentage_points',40,50,'kg')
    def test_zero_negative_base_not_called_improvement(self):
        for x in (0,-100):
            for op in ('relative_change','improvement'):
                with self.subTest(x=x,op=op),self.assertRaises(values.EvidenceError):
                    self.calc(op,x,direction='lower')
        with self.assertRaises(values.EvidenceError):self.calc('ratio',0)
    def test_finite_numbers_and_boolean_rejected(self):
        for x in (True,False,'NaN','Infinity','1e301','1e-301','1+2','1,000'):
            with self.subTest(x=x),self.assertRaises(values.EvidenceError):values.number(x,self.contract)
    def test_time_conversion(self):
        got=values.derive({'id':'d','op':'convert_unit','to_unit':'h'},
                         {'value':self.value(3600,'s')},self.contract)
        self.assertEqual(got.value,Decimal(1));self.assertEqual(got.unit,'h')
    def test_unsupported_unit_not_guessed(self):
        with self.assertRaises(values.NeedsReview):
            values.derive({'id':'d','op':'convert_unit','to_unit':'K'},
                          {'value':self.value(10,'degC')},self.contract)
    def test_mismatched_samples_rejected(self):
        with self.assertRaises(values.EvidenceError):
            values.derive({'id':'d','op':'difference','comparison_axis':'scenario'},
              {'baseline':self.value(1),'candidate':self.value(2,scenario='candidate',sample='S2')},self.contract)
    def test_duplicate_observation_not_aggregate_replication(self):
        with self.assertRaises(values.EvidenceError):
            values.derive({'id':'d','op':'aggregate','axis':'scenario','reducer':'mean'},
             {'items':[self.value(1,origin='cell1'),self.value(2,scenario='candidate',origin='cell1')]},self.contract)
    def test_aggregate_scope_and_precision(self):
        got=values.derive({'id':'d','op':'aggregate','axis':'scenario','reducer':'mean'},
           {'items':[self.value(1),self.value(2,scenario='candidate')]},self.contract)
        self.assertEqual(got.value,Decimal('1.5'))
    def test_identity_scale_preserves_long_source_decimal(self):
        original=self.value('1.'+'1234567890'*10,'kg')
        result=values.converted(original,'kg',self.contract)
        self.assertEqual(result.value,original.value)
    def test_percent_ratio_conversion_is_explicit(self):
        result=values.derive({'op':'percent_to_ratio'},{'value':self.value(40,'%')},self.contract)
        self.assertEqual(result.value,Decimal('.4'))
        result=values.derive({'op':'ratio_to_percent'},{'value':result},self.contract)
        self.assertEqual(result.value,Decimal('40'))
    def test_interval_identity_only(self):
        v=self.value((Decimal('1'),Decimal('2')),kind='interval')
        self.assertEqual(values.derive({'op':'identity'},{'value':v},self.contract),v)
        with self.assertRaises(values.NeedsReview):
            values.derive({'op':'convert_unit','to_unit':'g'},{'value':v},self.contract)
    def test_percent_to_points_conversion_not_silent(self):
        with self.assertRaises(values.EvidenceError):
            values.derive({'op':'convert_unit','to_unit':'pp'},{'value':self.value(50,'%')},self.contract)

    def test_inexact_cancellation_must_not_report_zero_as_exact(self):
        with self.assertRaises(values.NeedsReview):
            values.derive({'op':'aggregate','axis':'scenario','reducer':'sum'},
                {'items':[self.value('1e80',scenario='a'),self.value('1',scenario='b'),
                          self.value('-1e80',scenario='c')]},self.contract)
    def test_nonterminating_ratio_is_explicitly_unverified(self):
        with self.assertRaises(values.NeedsReview):
            self.calc('ratio',3,1)
    def test_inexact_unit_conversion_does_not_match_rounded_raw_value(self):
        with self.assertRaises(values.NeedsReview):
            values.converted(self.value(1,'s'),'h',self.contract)

if __name__=='__main__':unittest.main()
