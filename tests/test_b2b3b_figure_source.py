"""B2b3b source-chain checks use synthetic accepted A2/B1 workbook bytes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import yaml

from tests import test_b2b3_figure_audit as figure_fixture
import claim_evidence
import claim_figure
import claim_figure_source as figure_source
from artifact_fingerprint import combined_hash
from tests.test_model_code_conformance import save


class FigureSourceTests(unittest.TestCase):
    save_projection = figure_fixture.B2b3FigureAuditTests.save_projection

    @classmethod
    def setUpClass(cls):
        figure_fixture.B2b3FigureAuditTests.setUpClass.__func__(cls)
        cls.claim_contract = yaml.safe_load(
            (Path(__file__).resolve().parents[1] / 'core/claim_evidence_contract.yaml').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        figure_fixture.B2b3FigureAuditTests.tearDownClass.__func__(cls)

    def setUp(self):
        figure_fixture.B2b3FigureAuditTests.setUp(self)
        entry = self.state['subproblems']['Q1']
        workbook = entry['solution_workbook']
        script_relative = '问题一求解/q1_plot.m'
        script = self.root / script_relative
        script.write_text("function q1_plot\nT = readtable('问题一求解结果.xlsx');\n"
                          "exportgraphics(gcf, '../figures/q1_f01.png');\nend\n", encoding='utf-8')
        entry['matlab_script'] = script_relative
        digest = hashlib.sha256(script.read_bytes()).hexdigest()
        entry.setdefault('artifact_hashes', {})['matlab_script'] = digest
        entry.setdefault('validated_artifact_hashes', {})['matlab_script'] = digest
        image = self.root / 'figures/q1_f01.png'
        bundle = combined_hash([image], self.root)
        entry['artifact_hashes']['figure_bundle'] = bundle
        entry['validated_artifact_hashes']['figure_bundle'] = bundle
        entry['artifacts_stale'] = False
        entry['stale_layers'] = []
        self.registry_row = self.registry_row.replace('问题1求解/问题1求解结果.xlsx', workbook)
        self.registry_row = self.registry_row.replace('问题1求解/q1_plot.m', script_relative)
        self.binding = self.state['paper_framework']['claim_consumption_policy']['figure_bindings'][0]
        self.binding['source_bindings'] = [
            {'source_id': 'answer', 'sheet': '核心指标', 'required_headers': ['数值']}]
        self.save_projection()

    def tearDown(self):
        figure_fixture.B2b3FigureAuditTests.tearDown(self)

    def inspect(self):
        b1 = claim_evidence.inspect_project(self.root)
        observed = b1['observed_sources']
        text = (self.root / '模型论文框架.md').read_text(encoding='utf-8')
        registry = claim_figure.parse_framework_figure_rows(text)['Q1_F01']
        check = figure_source.inspect_source_binding(
            self.root, self.state, self.binding, registry, b1, observed, self.claim_contract)
        return check, observed

    def test_current_accepted_workbook_script_and_original_figure_hashes(self):
        check, observed = self.inspect()
        self.assertEqual(check['status'], 'current', check)
        self.assertEqual(check['approval_freshness'], 'current', check)
        self.assertEqual(check['visual_and_caption_semantics'], 'not_assessed')
        self.assertIn('问题一求解/q1_plot.m', observed['project'])
        self.assertIn('figures/q1_f01.png', observed['project'])
        self.assertEqual(figure_source.recheck_source_discovery(self.root, self.state, [check]), [])

    def test_extra_framework_header_or_missing_actual_header_needs_review(self):
        self.registry_row = self.registry_row.replace('核心指标/数值', '核心指标/数值;核心指标/虚构列')
        self.save_projection()
        check, _ = self.inspect()
        self.assertEqual(check['status'], 'needs_review', check)
        self.assertTrue(any('sheet/header entries differ' in issue for issue in check['issues']), check)
        self.registry_row = self.registry_row.replace(';核心指标/虚构列', '')
        self.binding['source_bindings'][0]['required_headers'] = ['虚构列']
        self.save_projection()
        check, _ = self.inspect()
        self.assertEqual(check['status'], 'needs_review', check)
        self.assertTrue(any('header is absent' in issue for issue in check['issues']), check)

    def test_changed_script_or_image_cannot_reuse_original_approval(self):
        script = self.root / '问题一求解/q1_plot.m'
        script.write_text(script.read_text(encoding='utf-8') + '% changed\n', encoding='utf-8')
        check, _ = self.inspect()
        self.assertEqual(check['approval_freshness'], 'not_assessed', check)
        self.assertTrue(any('MATLAB script differs' in issue for issue in check['issues']), check)
        script.write_text(script.read_text(encoding='utf-8')[:-10], encoding='utf-8')
        (self.root / 'figures/q1_f01.png').write_bytes(b'replaced image')
        check, _ = self.inspect()
        self.assertEqual(check['approval_freshness'], 'not_assessed', check)
        self.assertTrue(any('Figure bundle differs' in issue for issue in check['issues']), check)

    def test_unapproved_or_stale_figure_and_discovery_race_needs_review(self):
        self.state['artifacts']['approved_figures'] = []
        save(self.root, self.state)
        check, _ = self.inspect()
        self.assertEqual(check['approval_freshness'], 'not_assessed', check)
        self.state['artifacts']['approved_figures'] = ['figures/q1_f01.png']
        self.state['subproblems']['Q1']['stale_layers'] = ['figure_bundle']
        save(self.root, self.state)
        check, _ = self.inspect()
        self.assertEqual(check['approval_freshness'], 'not_assessed', check)
        self.state['subproblems']['Q1']['stale_layers'] = []
        self.state['subproblems']['Q1']['artifacts_stale'] = False
        save(self.root, self.state)
        check, _ = self.inspect()
        self.assertEqual(check['status'], 'current', check)
        extra = self.root / '问题一求解/extra.png'
        extra.write_bytes(b'new discovered image')
        self.assertTrue(figure_source.recheck_source_discovery(self.root, self.state, [check]))

    def test_workbook_replaced_with_same_selected_value_is_not_accepted(self):
        workbook = self.root / self.state['subproblems']['Q1']['solution_workbook']
        workbook.write_bytes(workbook.read_bytes() + b'\n')
        check, _ = self.inspect()
        self.assertNotEqual(check['status'], 'current', check)
        self.assertTrue(any('Live B1' in issue or 'B1 source' in issue for issue in check['issues']), check)

    def test_contradicting_evidence_is_not_a_figure_support_source(self):
        claim = self.state['paper_framework']['claim_evidence']['claims'][0]
        claim['evidence'][0]['relation'] = 'contradicts'
        save(self.root, self.state)
        check, _ = self.inspect()
        self.assertEqual(check['status'], 'needs_review', check)
        self.assertTrue(any('not linked' in issue for issue in check['issues']), check)

    def test_two_figures_share_one_workbook_script_and_scoped_image_capture(self):
        second = self.root / '问题一求解/second.png'
        second.write_bytes(b'\x89PNG\r\n\x1a\nsecond synthetic image')
        first = self.root / 'figures/q1_f01.png'
        bundle = combined_hash([first, second], self.root)
        entry = self.state['subproblems']['Q1']
        entry['artifact_hashes']['figure_bundle'] = bundle
        entry['validated_artifact_hashes']['figure_bundle'] = bundle
        self.state['artifacts']['approved_figures'].append('问题一求解/second.png')
        save(self.root, self.state)
        b1 = claim_evidence.inspect_project(self.root)
        observed = b1['observed_sources']
        registry = claim_figure.parse_framework_figure_rows(
            (self.root / '模型论文框架.md').read_text(encoding='utf-8'))['Q1_F01']
        second_binding = {**self.binding, 'figure_id': 'Q1_F02',
                          'image_path': '问题一求解/second.png'}
        cache = {}
        original_read = figure_source.bounded._read
        original_discovery = figure_source.project_snapshot.scoped_figure_files
        with patch.object(figure_source.bounded, '_read', wraps=original_read) as read, \
             patch.object(figure_source.project_snapshot, 'scoped_figure_files',
                          wraps=original_discovery) as discover:
            checks = [figure_source.inspect_source_binding(
                self.root, self.state, binding, registry, b1, observed,
                self.claim_contract, cache=cache)
                for binding in (self.binding, second_binding)]
        self.assertEqual([check['status'] for check in checks], ['current', 'current'], checks)
        self.assertEqual(discover.call_count, 1)
        paths = [call.args[1] for call in read.call_args_list]
        for path in (entry['solution_workbook'], entry['matlab_script'],
                     'figures/q1_f01.png', '问题一求解/second.png'):
            self.assertEqual(paths.count(path), 1, paths)
        self.assertEqual(cache['image_bytes'], len(first.read_bytes()) + len(second.read_bytes()))
        with patch.object(figure_source.project_snapshot, 'scoped_figure_files',
                          wraps=original_discovery) as final_discovery:
            self.assertEqual(figure_source.recheck_source_discovery(self.root, self.state, checks), [])
        self.assertEqual(final_discovery.call_count, 1)


if __name__ == '__main__':
    unittest.main()
