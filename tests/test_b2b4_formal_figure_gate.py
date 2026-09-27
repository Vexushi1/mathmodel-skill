"""Explicit 1.3.0 Figure-chain gate over live B1 and static modular LaTeX."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import claim_consumption as claims
from tests import test_b2b3c_figure_caption as fixture
from tests.test_model_code_conformance import bytes_in


class B2b4FormalFigureGateTests(unittest.TestCase):
    save_projection = fixture.FigureCaptionNumericTests.save_projection
    set_caption = fixture.FigureCaptionNumericTests.set_caption

    @classmethod
    def setUpClass(cls):
        fixture.FigureCaptionNumericTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.FigureCaptionNumericTests.tearDownClass.__func__(cls)

    def setUp(self):
        fixture.FigureCaptionNumericTests.setUp(self)
        policy = self.state['paper_framework']['claim_consumption_policy']
        policy.update(
            protocol_version='1.3.0', mode='enforce_latex_text_and_figure_chain',
            required_consumptions=[{
                'claim_id': 'answer_claim',
                'fragment_kinds': ['abstract_claim', 'question_result_text', 'figure_or_table_claim'],
            }],
        )
        self.fragments.extend([
            {'id': 'paper.abstract.q1', 'kind': 'abstract_claim', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Answer:',
             'source_file': 'final_latex/abstract.tex', 'status': 'current'},
            {'id': 'paper.body.q1', 'kind': 'question_result_text', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Result:',
             'source_file': 'final_latex/body.tex', 'status': 'current'},
        ])
        (self.latex / 'body.tex').write_text('Result: 100.00.\n', encoding='utf-8')
        main = self.latex / 'main.tex'
        main.write_text(main.read_text(encoding='utf-8').replace(
            '\\input{result}', '\\input{body}\n\\input{result}'), encoding='utf-8')
        self.save_projection()

    def tearDown(self):
        fixture.FigureCaptionNumericTests.tearDown(self)

    def test_schema_requires_nonempty_bindings_and_each_source_binding(self):
        schema = yaml.safe_load((Path(__file__).resolve().parents[1] /
                                 'core/project_state.schema.yaml').read_text(encoding='utf-8'))
        self.assertEqual(schema['version'], '8.10.0')
        validator = Draft202012Validator({
            '$ref': '#/$defs/claim_consumption_policy', '$defs': schema['$defs']})
        policy = self.state['paper_framework']['claim_consumption_policy']
        self.assertTrue(validator.is_valid(policy))
        self.assertFalse(validator.is_valid({k: v for k, v in policy.items()
                                             if k != 'figure_bindings'}))
        self.assertFalse(validator.is_valid({**policy, 'figure_bindings': []}))
        row = dict(policy['figure_bindings'][0])
        row.pop('source_bindings')
        self.assertFalse(validator.is_valid({**policy, 'figure_bindings': [row]}))
        self.assertFalse(validator.is_valid({**policy, 'mode': 'enforce_latex_text'}))

    def test_live_chain_passes_and_exposes_only_approved_graphic_paths(self):
        before = bytes_in(self.root)
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'passed', gate)
        self.assertEqual(gate['policy_protocol_version'], '1.3.0')
        self.assertEqual(gate['mode'], 'enforce_latex_text_and_figure_chain')
        self.assertEqual(gate['b1_status'], 'evidence_checked')
        self.assertEqual(gate['figure_image_paths'], ['figures/q1_f01.png'])
        self.assertEqual(gate['figure_graphic_bindings'], [{
            'figure_id': 'Q1_F01', 'image_token': '../figures/q1_f01.png',
            'image_path': 'figures/q1_f01.png'}])
        self.assertEqual(gate['human_semantic_coverage'], 'not_assessed')
        self.assertIn('figures/q1_f01.png', gate['observed_sources']['project'])
        self.assertIn('final_latex/body.tex', gate['observed_sources']['project'])
        self.assertIn('scripts/claim_figure_source.py', gate['observed_sources']['skill'])
        self.assertEqual(bytes_in(self.root), before)
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')

    def test_old_pairs_are_not_applicable_to_new_gate(self):
        policy = self.state['paper_framework']['claim_consumption_policy']
        for version, mode in (('1.0.0', 'observe'), ('1.1.0', 'propagate'),
                              ('1.2.0', 'enforce_latex_text')):
            with self.subTest(version=version):
                policy.update(protocol_version=version, mode=mode)
                self.save_projection()
                gate = claims.formal_figure_gate(self.root)
                self.assertEqual(gate['status'], 'not_applicable', gate)
                self.assertEqual(gate['figure_image_paths'], [])
                self.assertEqual(gate['figure_graphic_bindings'], [])

    def test_missing_binding_or_missing_text_obligation_fails_closed(self):
        policy = self.state['paper_framework']['claim_consumption_policy']
        for mutate in (
            lambda: policy.pop('figure_bindings'),
            lambda: policy['figure_bindings'][0].pop('source_bindings'),
            lambda: policy['required_consumptions'][0].update(
                fragment_kinds=['figure_or_table_claim']),
        ):
            with self.subTest(mutate=mutate):
                original = deepcopy(policy)
                mutate()
                self.save_projection()
                gate = claims.formal_figure_gate(self.root)
                self.assertEqual(gate['status'], 'failed', gate)
                self.assertEqual(gate['figure_image_paths'], [])
                self.assertEqual(gate['figure_graphic_bindings'], [])
                policy.clear()
                policy.update(original)

    def test_changed_image_caption_and_text_candidates_each_fail_closed(self):
        original_image = (self.root / 'figures/q1_f01.png').read_bytes()
        (self.root / 'figures/q1_f01.png').write_bytes(b'changed after approval')
        self.assertEqual(claims.formal_figure_gate(self.root)['status'], 'failed')
        (self.root / 'figures/q1_f01.png').write_bytes(original_image)
        self.set_caption('Result evidence 110.00 ratio.')
        self.assertEqual(claims.formal_figure_gate(self.root)['status'], 'failed')
        self.set_caption('Result evidence 100.00 ratio.')
        body = self.latex / 'body.tex'
        body.write_text(body.read_text(encoding='utf-8') +
                        'Globally optimal at 77.\n', encoding='utf-8')
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertEqual(gate['figure_image_paths'], [])
        self.assertTrue(any('unregistered' in issue for issue in gate['issues']), gate)

    def test_bound_figure_fragment_must_stay_current_and_located(self):
        self.fragments[0]['status'] = 'stale'
        self.save_projection()
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertEqual(gate['figure_graphic_bindings'], [])

    def test_located_nonclaim_stale_fragment_preserves_text_gate_condition(self):
        self.fragments.append({
            'id': 'paper.context.q1', 'kind': 'paper_section', 'scope': 'Q1',
            'depends_on': [], 'anchor': 'Context:',
            'source_file': 'final_latex/body.tex', 'status': 'stale',
        })
        body = self.latex / 'body.tex'
        body.write_text('Context: method.\n' + body.read_text(encoding='utf-8'),
                        encoding='utf-8')
        self.save_projection()
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertIn('active fragment is not current: paper.context.q1', gate['issues'])
        self.assertEqual(gate['figure_graphic_bindings'], [])

    def test_extra_number_inside_bound_figure_remains_unregistered(self):
        path = self.latex / 'result.tex'
        path.write_text(path.read_text(encoding='utf-8').replace(
            '\\end{figure}', 'Extra 77.\n\\end{figure}'), encoding='utf-8')
        self.registry_row = self.registry_row.replace('final_latex/result.tex:7',
                                                      'final_latex/result.tex:8')
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertEqual(audit['figure_caption_numeric_checks'][0]['status'], 'matched', audit)
        self.assertTrue(any(row['literal'] == '77' for row in audit['unregistered_candidates']), audit)
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('unregistered numeric' in issue for issue in gate['issues']), gate)

    def test_numeric_candidate_cap_cannot_hide_later_body_number(self):
        real_inspect = claims.inspect_project

        def capped_audit(*args, **kwargs):
            audit = real_inspect(*args, **kwargs)
            # The current report caps at 100. At the cap, further active text
            # candidates may have been truncated after matched Figure values.
            caption = audit['figure_caption_numeric_checks'][0]
            audit['unregistered_candidates'] = [{
                'source_file': caption['source_file'],
                'byte_offset': caption['number_byte_offset'],
                'literal': caption['literal'],
            }] * 100
            return audit

        with patch.object(claims, 'inspect_project', side_effect=capped_audit):
            gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('report reached its limit' in issue for issue in gate['issues']), gate)
        self.assertEqual(gate['figure_image_paths'], [])

    def test_second_read_set_recheck_catches_drift(self):
        original = claims.bounded._recheck
        calls = 0

        def drift_at_gate_recheck(root, observed):
            nonlocal calls
            if root == self.root and 'final_latex/body.tex' in observed:
                calls += 1
                if calls == 2:
                    path = self.latex / 'body.tex'
                    path.write_text(path.read_text(encoding='utf-8') + '% changed\n',
                                    encoding='utf-8')
            return original(root, observed)

        with patch.object(claims.bounded, '_recheck', side_effect=drift_at_gate_recheck):
            gate = claims.formal_figure_gate(self.root)
        self.assertGreaterEqual(calls, 2)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertEqual(gate['figure_image_paths'], [])
        self.assertTrue(any('read-set conflict' in issue for issue in gate['issues']), gate)


if __name__ == '__main__':
    unittest.main()
