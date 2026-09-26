"""Numeric Profile shapes and display modes cannot silently weaken B1 checks."""
from decimal import Decimal
from pathlib import Path
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import claim_evidence as audit
from claim_values import Value, EvidenceError
from claim_workbook import Workbook
from tests.claim_fixture import source, workbook


class ClaimProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = yaml.safe_load((ROOT / 'core/claim_evidence_contract.yaml').read_text())

    def setUp(self):
        self.value = Value('scalar', Decimal('.2'), 'ratio', {'metric': 'cost'}, frozenset({'A'}))
        self.profile = {'id': 'N1', 'metric': 'cost', 'unit': 'ratio',
                        'display_form': 'decimal', 'status': 'current', 'body_decimals': 3}
        self.claim = {'numeric_profile_id': 'N1', 'assertion':
                      {'evidence_ref': 'source:x', 'value': '.2', 'unit': 'ratio', 'display_location': 'body'}}

    def check(self):
        return audit._assertion(self.claim, self.value, [self.profile], self.contract)

    def test_unknown_or_partial_profile_is_not_decimal_fallback(self):
        for mutation in ({'display_form': 'unknown'}, {'unexpected': True}):
            with self.subTest(mutation=mutation):
                self.profile.update(mutation)
                with self.assertRaises(EvidenceError): self.check()
                self.setUp()
        self.profile.pop('display_form')
        with self.assertRaises(EvidenceError): self.check()

    def test_percent_profile_requires_actual_percent_quantity(self):
        self.profile['display_form'] = 'percent'
        with self.assertRaises(EvidenceError): self.check()
        self.profile['unit'] = '%'
        self.claim['assertion'].update(value='20', unit='%')
        self.assertEqual(self.check()['status'], 'matched')

    def test_integer_profile_requires_zero_places(self):
        self.profile['display_form'] = 'integer'
        with self.assertRaises(EvidenceError): self.check()
        self.profile['body_decimals'] = 0
        self.claim['assertion']['value'] = '0'
        self.assertEqual(self.check()['status'], 'matched')

    def test_interval_and_category_forms_cannot_describe_scalar(self):
        for form in ('interval', 'categorical'):
            self.profile['display_form'] = form
            with self.subTest(form=form), self.assertRaises(EvidenceError): self.check()

    def test_profile_unit_source_also_uses_existing_schema(self):
        selector = source()['selector']
        selector['unit'] = {'kind': 'numeric_profile', 'profile_id': 'N1'}
        self.profile.update(unit='kg', display_form='unknown')
        with self.assertRaises(EvidenceError):
            Workbook(workbook(), self.contract).select(selector, [self.profile])
        self.profile['display_form'] = 'decimal'
        self.assertEqual(Workbook(workbook(), self.contract).select(selector, [self.profile])[0].unit, 'kg')

    def test_declared_scientific_precision_control(self):
        self.profile.update(display_form='scientific', body_decimals=1)
        self.assertEqual(self.check()['status'], 'matched')


if __name__ == '__main__': unittest.main()
