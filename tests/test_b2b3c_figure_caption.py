"""Read-only numeric Figure caption observation with live B1 evidence."""
from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

from tests import test_b2b3b_consumption_integration as fixture
from tests.test_model_code_conformance import bytes_in, save
import claim_consumption


class FigureCaptionNumericTests(unittest.TestCase):
    """Reuse the accepted workbook, original bundle and active Figure fixture."""

    save_projection = fixture.FigureSourceConsumptionIntegrationTests.save_projection

    @classmethod
    def setUpClass(cls):
        fixture.FigureSourceConsumptionIntegrationTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.FigureSourceConsumptionIntegrationTests.tearDownClass.__func__(cls)

    def setUp(self):
        fixture.FigureSourceConsumptionIntegrationTests.setUp(self)
        self.state['paper_framework']['numeric_profile'][0]['figure_caption_decimals'] = 2
        self.set_caption('Result evidence 100.00 ratio.')

    def tearDown(self):
        fixture.FigureSourceConsumptionIntegrationTests.tearDown(self)

    def set_caption(self, caption: str, optional: str = '') -> None:
        path = self.latex / 'result.tex'
        text = path.read_text(encoding='utf-8')
        start = text.index('\\caption')
        end = text.index('\n', start)
        text = text[:start] + f'\\caption{optional}{{{caption}}}' + text[end:]
        path.write_text(text, encoding='utf-8')
        parts = self.registry_row.split('|')
        parts[2] = f' {caption} '
        self.registry_row = '|'.join(parts)
        self.save_projection()

    def test_current_literal_caption_matches_live_scalar_at_its_own_precision(self):
        before = bytes_in(self.root)
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['b1_status'], 'evidence_checked', report)
        self.assertEqual(report['figure_source_checks'][0]['status'], 'current', report)
        self.assertEqual(report['figure_identity_checks'][0]['identity_status'], 'matched', report)
        check = report['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'matched', report)
        self.assertEqual(check['observed_value'], '100.00')
        self.assertEqual(check['expected_value'], '100.00')
        self.assertEqual(check['display_places'], 2)
        self.assertEqual(check['unit'], 'ratio')
        self.assertEqual(check['visual_semantics'], 'not_assessed')
        self.assertEqual(check['caption_semantic_support'], 'not_established')
        self.assertEqual(bytes_in(self.root), before)

    def test_conflicting_caption_value_is_separate_from_unassessed_semantics(self):
        prior_status = claim_consumption.inspect_project(self.root)['status']
        self.set_caption('Result evidence 110.00 ratio.')
        report = claim_consumption.inspect_project(self.root)
        check = report['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'conflict', report)
        self.assertEqual(check['expected_value'], '100.00')
        self.assertEqual(report['status'], prior_status, report)
        self.assertEqual(check['caption_semantic_support'], 'not_established')

    def test_multiline_caption_reports_the_number_physical_line(self):
        path = self.latex / 'result.tex'
        text = path.read_text(encoding='utf-8').replace(
            'Result evidence 100.00 ratio.', 'Result evidence\n100.00 ratio.')
        path.write_text(text, encoding='utf-8')
        self.registry_row = self.registry_row.replace('final_latex/result.tex:7',
                                                      'final_latex/result.tex:8')
        self.save_projection()
        report = claim_consumption.inspect_project(self.root)
        check = report['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'matched', report)
        self.assertEqual(check['line'], 5)
        physical_text = path.read_bytes().decode('utf-8')
        self.assertEqual(check['number_offset'], physical_text.index('100.00 ratio.'))
        self.assertEqual(check['number_byte_offset'],
                         len(physical_text[:check['number_offset']].encode('utf-8')))

    def test_old_text_gate_ignores_new_caption_numeric_observation(self):
        policy = self.state['paper_framework']['claim_consumption_policy']
        self.assertEqual(claim_consumption.formal_text_gate(self.root)['status'], 'not_applicable')
        policy.update(protocol_version='1.2.0', mode='enforce_latex_text')
        self.save_projection()
        before = claim_consumption.formal_text_gate(self.root)
        self.set_caption('Result evidence 110.00 ratio.')
        after = claim_consumption.formal_text_gate(self.root)
        self.assertEqual(before['status'], after['status'])
        self.assertEqual(before['audit_status'], after['audit_status'])
        self.assertEqual(before['issues'], after['issues'])
        self.assertEqual(claim_consumption.inspect_project(self.root)[
            'figure_caption_numeric_checks'][0]['status'], 'conflict')

    def test_missing_or_mismatched_unit_needs_review(self):
        for caption in ('Result evidence 100.00.', 'Result evidence 100.00 kg.',
                        'Result evidence 100.00 ratio/kg.'):
            with self.subTest(caption=caption):
                self.set_caption(caption)
                check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
                self.assertEqual(check['status'], 'needs_review', check)
                self.assertIn('unit', check['reason'])

    def test_complete_custom_unit_does_not_conflict_with_known_prefix_unit(self):
        self.state['paper_framework']['numeric_profile'][0]['unit'] = 'm/s'
        claim = self.state['paper_framework']['claim_evidence']['claims'][0]
        claim['assertion']['unit'] = 'm/s'
        self.set_caption('Result evidence 100.00 m/s.')
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['b1_status'], 'evidence_checked', report)
        self.assertEqual(report['figure_caption_numeric_checks'][0]['status'], 'matched', report)
        for caption in ('Result evidence 100.00 m/s^x.',
                        'Result evidence 100.00 m/s².',
                        'Result evidence 100.00 m/s ^x.'):
            with self.subTest(caption=caption):
                self.set_caption(caption)
                check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
                self.assertEqual(check['status'], 'needs_review', check)

    def test_caption_precision_is_not_borrowed_from_abstract_or_body(self):
        del self.state['paper_framework']['numeric_profile'][0]['figure_caption_decimals']
        save(self.root, self.state)
        check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'not_assessed', check)
        self.assertIn('precision', check['reason'])
        self.state['paper_framework']['numeric_profile'][0]['figure_caption_decimals'] = 2
        self.set_caption('Result evidence 100.0 ratio.')
        check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'needs_review', check)
        self.assertIn('precision', check['reason'])

    def test_multiple_values_claims_and_short_caption_remain_unassessed(self):
        self.set_caption('Result evidence 100.00 ratio and 5.00 ratio.')
        check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'not_assessed', check)
        self.assertIn('exactly one literal', check['reason'])
        self.set_caption('Result evidence 100.00 ratio.')
        extra = deepcopy(self.state['paper_framework']['claim_evidence']['claims'][0])
        extra['id'] = 'second_claim'
        self.state['paper_framework']['claim_evidence']['claims'].append(extra)
        self.fragments[0]['depends_on'].append('claim:second_claim')
        self.save_projection()
        check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'not_assessed', check)
        self.assertIn('exactly one direct claim', check['reason'])
        self.state['paper_framework']['claim_evidence']['claims'].pop()
        self.fragments[0]['depends_on'].pop()
        self.set_caption('Result evidence 100.00 ratio.', optional='[Short]')
        check = claim_consumption.inspect_project(self.root)['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'not_assessed', check)
        self.assertIn('short optional', check['reason'])

    def test_caption_macro_does_not_gain_numeric_match(self):
        self.set_caption(r'Result evidence \textbf{100.00} ratio.')
        report = claim_consumption.inspect_project(self.root)
        self.assertNotEqual(report['figure_caption_numeric_checks'][0]['status'], 'matched', report)
        self.assertEqual(report['figure_identity_checks'][0]['identity_status'], 'needs_review')

    def test_stale_original_image_and_legacy_binding_do_not_qualify_caption(self):
        (self.root / 'figures/q1_f01.png').write_bytes(b'replaced image')
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['figure_caption_numeric_checks'][0]['status'], 'not_assessed', report)
        self.binding.pop('source_bindings')
        self.save_projection()
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['figure_caption_numeric_checks'][0]['status'], 'not_assessed', report)
        self.state['paper_framework']['claim_consumption_policy'].pop('figure_bindings')
        self.save_projection()
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['figure_caption_numeric_checks'], [], report)

    def test_caption_source_change_during_read_set_recheck_blocks_return(self):
        original = claim_consumption.bounded._recheck

        def change_caption_before_recheck(root, observed):
            if root == self.root and 'final_latex/result.tex' in observed:
                path = self.latex / 'result.tex'
                path.write_text(path.read_text(encoding='utf-8') + '% changed\n', encoding='utf-8')
            return original(root, observed)

        with patch.object(claim_consumption.bounded, '_recheck',
                          side_effect=change_caption_before_recheck):
            report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['status'], 'blocked', report)
        self.assertTrue(any('read-set conflict' in error for error in report['errors']), report)


class FigureCaptionLiveOriginalTests(unittest.TestCase):
    """A separate accepted A2 run proves the caption does not borrow assertion rounding."""

    seed_offset = 194.06
    save_projection = FigureCaptionNumericTests.save_projection
    set_caption = FigureCaptionNumericTests.set_caption

    @classmethod
    def setUpClass(cls):
        fixture.FigureSourceConsumptionIntegrationTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.FigureSourceConsumptionIntegrationTests.tearDownClass.__func__(cls)

    def setUp(self):
        fixture.FigureSourceConsumptionIntegrationTests.setUp(self)
        self.state['paper_framework']['numeric_profile'][0]['figure_caption_decimals'] = 2
        self.set_caption('Result evidence 100.03 ratio.')

    def tearDown(self):
        fixture.FigureSourceConsumptionIntegrationTests.tearDown(self)

    def test_current_accepted_original_is_used_instead_of_rounded_assertion(self):
        claim = self.state['paper_framework']['claim_evidence']['claims'][0]
        self.assertEqual(claim['assertion']['value'], '100.0')
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['b1_status'], 'evidence_checked', report)
        check = report['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'matched', report)
        self.assertEqual(check['expected_value'], '100.03')
        self.set_caption('Result evidence 100.00 ratio.')
        report = claim_consumption.inspect_project(self.root)
        check = report['figure_caption_numeric_checks'][0]
        self.assertEqual(check['status'], 'conflict', report)
        self.assertEqual(check['expected_value'], '100.03')


if __name__ == '__main__':
    unittest.main()
