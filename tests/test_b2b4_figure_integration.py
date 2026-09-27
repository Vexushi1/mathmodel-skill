"""B2b4 Figure delivery binds the live image to audit, recorder and package proof."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import unittest
from unittest.mock import patch
import zipfile
import zlib

import yaml

from tests import test_b2b3c_figure_caption as fixture
import audit_latex_project as latex_audit
import claim_consumption as claims
import latex_delivery as delivery
import hsk_pack_submission as packager
import sync_project as synchronizer
import validate_submission_package as package_validator
from artifact_fingerprint import combined_hash
from submission_requirements import bound_compile_files, reproducibility_requirements


class FigureFormalChainIntegrationTests(unittest.TestCase):
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
        self.state['paper_framework']['claim_consumption_policy'].update(
            protocol_version='1.3.0', mode='enforce_latex_text_and_figure_chain',
            required_consumptions=[{
                'claim_id': 'answer_claim',
                'fragment_kinds': ['abstract_claim', 'question_result_text', 'figure_or_table_claim'],
            }],
        )
        self.fragments[:0] = [
            {'id': 'paper.abstract.q1', 'kind': 'abstract_claim', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Answer:',
             'source_file': 'final_latex/abstract.tex', 'status': 'current'},
            {'id': 'paper.result.q1', 'kind': 'question_result_text', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Result:',
             'source_file': 'final_latex/body.tex', 'status': 'current'},
        ]
        (self.latex / 'body.tex').write_text('Result: 100.00.\n', encoding='utf-8')
        main = self.latex / 'main.tex'
        main.write_text(main.read_text(encoding='utf-8').replace(
            '\\input{result}', '\\input{body}\n\\input{result}'), encoding='utf-8')
        self.save_projection()

    def tearDown(self):
        fixture.FigureCaptionNumericTests.tearDown(self)

    def _proof(self, *, include_image: bool = True):
        main = self.latex / 'main.tex'
        audit = latex_audit.write_audit_report(
            main_file=main, findings=[], framework_path=self.root / '模型论文框架.md')
        self.assertEqual(audit['status'], 'passed', audit)
        (self.latex / 'main.pdf').write_bytes(b'%PDF-synthetic-B2b4-proof-fixture')
        (self.latex / 'main.log').write_text('This is XeTeX\n', encoding='utf-8')
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'passed', gate)
        options = {'project_root': self.root, 'allowed_external_graphics': {
            row['image_token']: self.root / row['image_path']
            for row in gate['figure_graphic_bindings']}}
        inputs = delivery.source_bundle_files(main, **options)
        with (self.latex / 'main.fls').open('w', encoding='utf-8') as recorder:
            recorder.write(f'PWD {self.latex.resolve()}\n')
            for path in inputs:
                if not include_image and path == self.root / 'figures/q1_f01.png':
                    continue
                token = path.relative_to(self.latex).as_posix() if path.is_relative_to(self.latex) \
                    else '../' + path.relative_to(self.root).as_posix()
                recorder.write(f'INPUT {token}\n')
        profile = delivery.current_profile_config('cumcm')
        report = delivery.write_compile_report(
            project=self.latex, main=main, profile='cumcm', engine='xelatex',
            bibliography='biber', sequence=profile['sequence'], profile_config=profile)
        return audit, report

    def test_v5_audit_compile_and_submission_replay(self):
        gate = claims.formal_figure_gate(self.root)
        self.assertEqual(gate['status'], 'passed', gate)
        self.assertEqual(gate['human_semantic_coverage'], 'not_assessed')
        self.assertEqual(gate['figure_image_paths'], ['figures/q1_f01.png'])
        findings = latex_audit.audit_project(
            self.latex / 'main.tex', framework_path=self.root / '模型论文框架.md',
            require_framework=True)
        self.assertFalse(any(item.code == 'b2_claim_figure_gate_failed' for item in findings), findings)
        audit, report = self._proof()
        self.assertEqual(audit['audit_schema_version'], '2.0.0')
        self.assertEqual(report['report_schema_version'], '5.0.0')
        self.assertIn('figures/q1_f01.png', {row['path'] for row in audit['source_files']})
        self.assertIn('figures/q1_f01.png', {row['path'] for row in report['actual_input_files']})
        self.assertEqual(delivery.verify_audit_report(
            project=self.latex, main=self.latex / 'main.tex', report=audit), [])
        self.assertEqual(delivery.verify_compile_report(
            project=self.latex, main=self.latex / 'main.tex',
            pdf=self.latex / 'main.pdf', report=report), [])

        pdf = self.latex / 'main.pdf'
        package = self.root / 'submission.zip'
        manifest = {'package_schema_version': '1.0.0', 'kind': 'reproducibility',
                    'files': [{'path': 'final_latex/main.pdf',
                               'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}]}
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('submission_manifest.yaml', yaml.safe_dump(manifest))
            archive.write(pdf, 'final_latex/main.pdf')
        with patch.object(package_validator, 'reproducibility_requirements', return_value=(set(), [])):
            package_report = package_validator.validate_package(self.root, package)
        self.assertEqual(package_report['status'], 'passed', package_report)

    def test_recorder_must_contain_the_actual_figure_image(self):
        _, report = self._proof(include_image=False)
        self.assertEqual(report['status'], 'failed', report)
        self.assertTrue(report['dependency_issues'], report)

    def test_v5_reproducibility_package_requires_source_and_bound_auxiliaries(self):
        _, report = self._proof()
        self.assertEqual(report['status'], 'passed', report)
        state = yaml.safe_load((self.root / 'state/project_state.yaml').read_text(encoding='utf-8'))
        bound, bound_issues = bound_compile_files(self.root, state)
        self.assertEqual(bound_issues, [])
        self.assertEqual({path.relative_to(self.root).as_posix() for path in bound},
                         {'final_latex/main.fls', 'final_latex/main.log'})
        required, _ = reproducibility_requirements(self.root, state)
        self.assertTrue({
            'final_latex/abstract.tex', 'final_latex/body.tex', 'final_latex/result.tex',
            'figures/q1_f01.png', 'final_latex/main.fls', 'final_latex/main.log',
        }.issubset(required), required)
        packed = packager.reproducibility_files(self.root, self.root / 'submission.zip')
        self.assertTrue(bound.issubset(set(packed)))

        pdf = self.latex / 'main.pdf'
        package = self.root / 'submission.zip'
        manifest = {'package_schema_version': '1.0.0', 'kind': 'reproducibility',
                    'files': [{'path': 'final_latex/main.pdf',
                               'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}]}
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('submission_manifest.yaml', yaml.safe_dump(manifest))
            archive.write(pdf, 'final_latex/main.pdf')
        package_report = package_validator.validate_package(self.root, package)
        self.assertEqual(package_report['status'], 'failed', package_report)
        for relative in ('final_latex/body.tex', 'figures/q1_f01.png',
                         'final_latex/main.fls', 'final_latex/main.log'):
            self.assertIn(f'完整复现包缺少当前必需文件: {relative}', package_report['issues'])

    def test_image_change_invalidates_the_entire_formal_chain(self):
        audit, report = self._proof()
        (self.root / 'figures/q1_f01.png').write_bytes(b'replaced after proof')
        self.assertEqual(claims.formal_figure_gate(self.root)['status'], 'failed')
        self.assertTrue(delivery.verify_audit_report(
            project=self.latex, main=self.latex / 'main.tex', report=audit))
        self.assertTrue(delivery.verify_compile_report(
            project=self.latex, main=self.latex / 'main.tex',
            pdf=self.latex / 'main.pdf', report=report))

    def test_explicit_sync_uses_figure_gate(self):
        with patch.object(synchronizer, 'contract_preflight_issues', return_value=[]), \
                patch.object(synchronizer, '_scope_artifact_issues', return_value=[]):
            report = synchronizer.synchronize(self.root, write=False, delivery_scope='latex')
        self.assertEqual(report['claim_figure_gate']['status'], 'passed', report)
        self.assertNotIn('claim_text_gate', report)

    def test_formal_sync_preserves_current_v5_proof_sources(self):
        synchronizer.synchronize(self.root, write=True)
        self.state = yaml.safe_load((self.root / 'state/project_state.yaml').read_text(encoding='utf-8'))
        self.fragments = self.state['paper_framework']['paper_fragments']
        for row in self.fragments:
            row['status'] = 'current'
        for entry in self.state['subproblems'].values():
            entry['artifacts_stale'] = False
            entry['stale_layers'] = []
        self.save_projection()
        self.assertEqual(claims.formal_figure_gate(self.root)['status'], 'passed')
        audit, compile_report = self._proof()
        state_before = (self.root / 'state/project_state.yaml').read_bytes()
        framework_before = (self.root / '模型论文框架.md').read_bytes()
        with patch.object(synchronizer, '_apply_snapshot_to_state', return_value=(False, [])), \
                patch.object(synchronizer, 'contract_preflight_issues', return_value=[]), \
                patch.object(synchronizer, '_scope_artifact_issues', return_value=[]):
            report = synchronizer.synchronize(self.root, write=True, delivery_scope='latex')
        self.assertEqual(report['status'], 'passed', report['issues'])
        self.assertEqual(report['claim_figure_gate']['status'], 'passed', report)
        self.assertFalse(report['state_write_performed'], report)
        self.assertEqual((self.root / 'state/project_state.yaml').read_bytes(), state_before)
        self.assertEqual((self.root / '模型论文框架.md').read_bytes(), framework_before)
        self.assertEqual(delivery.verify_audit_report(
            project=self.latex, main=self.latex / 'main.tex', report=audit), [])
        self.assertEqual(delivery.verify_compile_report(
            project=self.latex, main=self.latex / 'main.tex',
            pdf=self.latex / 'main.pdf', report=compile_report), [])

    @unittest.skipUnless(shutil.which('xelatex'), 'XeLaTeX is not installed')
    def test_real_xelatex_figure_image_proof(self):
        def chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return len(data).to_bytes(4, 'big') + body + zlib.crc32(body).to_bytes(4, 'big')

        png = (b'\x89PNG\r\n\x1a\n'
               + chunk(b'IHDR', (1).to_bytes(4, 'big') * 2 + bytes([8, 2, 0, 0, 0]))
               + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00'))
               + chunk(b'IEND', b''))
        image = self.root / 'figures/q1_f01.png'
        image.write_bytes(png)
        entry = self.state['subproblems']['Q1']
        digest = combined_hash([image], self.root)
        entry['artifact_hashes']['figure_bundle'] = digest
        entry['validated_artifact_hashes']['figure_bundle'] = digest
        main = self.latex / 'main.tex'
        main.write_text(main.read_text(encoding='utf-8').replace(
            '\\documentclass{article}', '\\documentclass{article}\n\\usepackage{graphicx}'),
            encoding='utf-8')
        self.save_projection()
        self.assertEqual(claims.formal_figure_gate(self.root)['status'], 'passed')
        audit = latex_audit.write_audit_report(
            main_file=main, findings=[], framework_path=self.root / '模型论文框架.md')
        self.assertEqual(audit['status'], 'passed', audit)
        command = ['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                   '-file-line-error', '-recorder', 'main.tex']
        for _ in range(2):
            compiled = subprocess.run(command, cwd=self.latex, capture_output=True, text=True,
                                      encoding='utf-8', errors='replace', check=False)
            self.assertEqual(compiled.returncode, 0, compiled.stdout[-3000:] + compiled.stderr[-3000:])
        profile = delivery.current_profile_config('diangong')
        report = delivery.write_compile_report(
            project=self.latex, main=main, profile='diangong', engine='xelatex',
            bibliography='none', sequence=['xelatex', 'xelatex'], profile_config=profile)
        self.assertEqual(report['status'], 'passed', report)
        self.assertEqual(delivery.verify_compile_report(
            project=self.latex, main=main, pdf=self.latex / 'main.pdf', report=report), [])


if __name__ == '__main__':
    unittest.main()
