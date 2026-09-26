"""B2b3a Figure identity audit against a synthetic accepted B1 project."""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import tests.test_b2b2_text_gate as b2_fixture

claims = b2_fixture.claims
save = b2_fixture.save
sha256_text = b2_fixture.sha256_text


class B2b3FigureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b2_fixture.B2b2TextGateTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        b2_fixture.B2b2TextGateTests.tearDownClass.__func__(cls)

    def save_projection(self):
        b2_fixture.B2b2TextGateTests.save_projection(self)
        path = self.root / '模型论文框架.md'
        text = path.read_text(encoding='utf-8')
        text += ('\n## 图表证据链\n\n'
                 '| 图号 | DOCX/LaTeX 图注 | 图型/作用 | 源工作簿 | 工作表/精确唯一表头 | 绘图程序 | 导出文件 | 正文支撑判断 | 正文引用位置 |\n'
                 '|---|---|---|---|---|---|---|---|---|\n')
        if getattr(self, 'registry_row', None):
            text += self.registry_row + '\n'
        path.write_text(text, encoding='utf-8')
        self.state['paper_framework']['sha256'] = sha256_text(text)
        save(self.root, self.state)

    def setUp(self):
        b2_fixture.B2b2TextGateTests.setUp(self)
        policy = self.state['paper_framework']['claim_consumption_policy']
        policy.update(protocol_version='1.0.0', mode='observe',
                      required_consumptions=[{'claim_id': 'answer_claim',
                                              'fragment_kinds': ['figure_or_table_claim']}],
                      figure_bindings=[{'figure_id': 'Q1_F01',
                                        'fragment_id': 'paper.figure.q1',
                                        'latex_label': 'fig:q1-f01',
                                        'image_path': 'figures/q1_f01.png'}])
        self.fragments[:] = [{'id': 'paper.figure.q1', 'kind': 'figure_or_table_claim',
                             'scope': 'Q1', 'depends_on': ['claim:answer_claim'],
                             'anchor': 'Result evidence', 'source_file': 'final_latex/result.tex',
                             'status': 'current'}]
        self.registry_row = ('| Q1_F01 | Result evidence 100. | result figure | '
                             '问题1求解/问题1求解结果.xlsx | 核心指标/数值 | '
                             '问题1求解/q1_plot.m | figures/q1_f01.png | '
                             'Q1 result | final_latex/result.tex:7 |')
        self.latex.joinpath('result.tex').write_text(
            '\\begin{figure}\n\\centering\n'
            '\\includegraphics{../figures/q1_f01.png}\n'
            '\\caption{Result evidence 100.}\n\\label{fig:q1-f01}\n'
            '\\end{figure}\nSee Figure~\\ref{fig:q1-f01}.\n', encoding='utf-8')
        image = self.root / 'figures/q1_f01.png'
        image.parent.mkdir(exist_ok=True)
        image.write_bytes(b'\x89PNG\r\n\x1a\nsynthetic identity fixture')
        artifacts = self.state.setdefault('artifacts', {})
        artifacts['figures'] = ['figures/q1_f01.png']
        artifacts['approved_figures'] = ['figures/q1_f01.png']
        self.save_projection()

    def tearDown(self):
        b2_fixture.B2b2TextGateTests.tearDown(self)

    def test_declared_result_figure_identity_is_located_but_not_semantically_approved(self):
        report = claims.inspect_project(self.root)
        self.assertEqual(report['b1_status'], 'evidence_checked', report)
        check = report['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'matched', check)
        self.assertEqual(check['approval_freshness'], 'not_assessed')
        self.assertEqual(check['source_and_visual_semantics'], 'not_assessed')
        self.assertEqual(report['observed_sources']['project']['figures/q1_f01.png'],
                         hashlib.sha256((self.root / 'figures/q1_f01.png').read_bytes()).hexdigest())
        self.assertNotEqual(report['status'], 'observed')  # Caption value remains unqualified.

    def test_unapproved_or_changed_image_cannot_reuse_identity_observation(self):
        self.state['artifacts']['approved_figures'] = []
        self.save_projection()
        report = claims.inspect_project(self.root)
        self.assertEqual(report['figure_identity_checks'][0]['identity_status'], 'needs_review')
        self.state['artifacts']['approved_figures'] = ['figures/q1_f01.png']
        self.save_projection()
        original = claims.bounded._recheck

        def mutate_before_recheck(root, observed):
            if root == self.root and 'figures/q1_f01.png' in observed:
                (self.root / 'figures/q1_f01.png').write_bytes(b'replaced after observation')
            return original(root, observed)

        with patch.object(claims.bounded, '_recheck', side_effect=mutate_before_recheck):
            report = claims.inspect_project(self.root)
        self.assertEqual(report['status'], 'blocked', report)
        self.assertTrue(any('read-set conflict' in item for item in report['errors']), report)

    def test_prior_image_replacement_does_not_claim_approval_freshness(self):
        (self.root / 'figures/q1_f01.png').write_bytes(b'replaced before this audit')
        check = claims.inspect_project(self.root)['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'matched', check)
        self.assertEqual(check['approval_freshness'], 'not_assessed')

    def test_caption_and_image_mismatch_are_reported_without_writing(self):
        before = (self.root / 'state/project_state.yaml').read_bytes()
        self.latex.joinpath('result.tex').write_text(
            '\\begin{figure}\n\\includegraphics{../figures/other.png}\n'
            '\\caption{Result evidence 110.}\n\\label{fig:q1-f01}\n'
            '\\end{figure}\nSee Figure~\\ref{fig:q1-f01}.\n', encoding='utf-8')
        check = claims.inspect_project(self.root)['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'needs_review', check)
        self.assertTrue(any('caption differs' in item for item in check['issues']), check)
        self.assertTrue(any('image does not resolve' in item for item in check['issues']), check)
        self.assertEqual((self.root / 'state/project_state.yaml').read_bytes(), before)

    def test_stale_framework_reference_location_is_not_a_matched_identity(self):
        self.registry_row = self.registry_row.replace('result.tex:7', 'result.tex:99')
        self.save_projection()
        check = claims.inspect_project(self.root)['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'needs_review', check)
        self.assertTrue(any('reference location differs' in item for item in check['issues']), check)

    def test_nested_include_uses_main_tex_graphics_directory(self):
        section = self.latex / 'sections'
        section.mkdir()
        self.latex.joinpath('main.tex').write_text(
            '\\documentclass{article}\n\\begin{document}\n'
            '\\input{abstract}\n\\input{sections/result}\n\\end{document}\n', encoding='utf-8')
        section.joinpath('result.tex').write_text(self.latex.joinpath('result.tex').read_text(encoding='utf-8'),
                                                   encoding='utf-8')
        self.fragments[0]['source_file'] = 'final_latex/sections/result.tex'
        self.registry_row = self.registry_row.replace('final_latex/result.tex:7',
                                                       'final_latex/sections/result.tex:7')
        self.save_projection()
        check = claims.inspect_project(self.root)['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'matched', check)
        section.joinpath('result.tex').write_text(
            section.joinpath('result.tex').read_text(encoding='utf-8').replace(
                '../figures/q1_f01.png', '../../figures/q1_f01.png'), encoding='utf-8')
        check = claims.inspect_project(self.root)['figure_identity_checks'][0]
        self.assertEqual(check['identity_status'], 'needs_review', check)
        self.assertTrue(any('image does not resolve' in item for item in check['issues']), check)

    def test_old_observe_without_bindings_does_not_scan_or_read_images(self):
        self.state['paper_framework']['claim_consumption_policy'].pop('figure_bindings')
        self.save_projection()
        report = claims.inspect_project(self.root)
        self.assertEqual(report['figure_identity_checks'], [])
        self.assertNotIn('figures/q1_f01.png', report['observed_sources']['project'])
        self.assertNotIn('scripts/claim_figure.py', report['observed_sources']['skill'])


if __name__ == '__main__':
    unittest.main()
