"""B2b2 opt-in text gate against a synthetic live A2/B1 accepted chain."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_latex_project as latex_audit
import claim_consumption as claims
import latex_delivery as delivery
import project_transaction as transaction
import sync_project as synchronizer
import validate_submission_package as package_validator
from tests import conformance_a2_smoke as smoke
from tests.claim_fixture import install_record
from tests.test_model_code_conformance import bytes_in, save
from validate_model_paper_framework import sha256_text


class B2b2TextGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed_tmp = tempfile.TemporaryDirectory()
        cls.seed = Path(cls.seed_tmp.name) / 'seed'
        cls.seed.mkdir()
        state = smoke.prepare(cls.seed, 'python', required=('primary', 'analysis'))
        (cls.seed / 'constraints.json').write_text('{"right_hand_side_offset":194}', encoding='utf-8')
        state, _ = smoke.run_stage(cls.seed, 'python', 'primary', state)
        state, _ = smoke.run_stage(cls.seed, 'python', 'analysis', state)
        cls.base_state = state

    @classmethod
    def tearDownClass(cls):
        cls.seed_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'project'
        shutil.copytree(self.seed, self.root)
        self.state = deepcopy(self.base_state)
        install_record(self.state)
        framework = self.state['paper_framework']
        claim = framework['claim_evidence']['claims'][0]
        claim.update(text='Synthetic scalar equation result is 100.', numeric_profile_id='N99')
        claim['assertion'].update(value='100.0', display_location='abstract')
        framework['numeric_profile'][0].update(abstract_decimals=1, body_decimals=2)
        framework['claim_consumption_policy'] = {
            'protocol_version': '1.2.0', 'mode': 'enforce_latex_text',
            'required_consumptions': [{'claim_id': 'answer_claim',
                                       'fragment_kinds': ['abstract_claim', 'question_result_text']}],
        }
        self.fragments = [
            {'id': 'paper.abstract.q1', 'kind': 'abstract_claim', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Answer:',
             'source_file': 'final_latex/abstract.tex', 'status': 'current'},
            {'id': 'paper.result.q1', 'kind': 'question_result_text', 'scope': 'Q1',
             'depends_on': ['claim:answer_claim'], 'anchor': 'Result:',
             'source_file': 'final_latex/result.tex', 'status': 'current'},
        ]
        framework['paper_fragments'] = self.fragments
        self.latex = self.root / 'final_latex'
        self.latex.mkdir(exist_ok=True)
        (self.latex / 'main.tex').write_text(
            '\\documentclass{article}\n\\begin{document}\n'
            '\\input{abstract}\n\\input{result}\n\\end{document}\n', encoding='utf-8')
        (self.latex / 'abstract.tex').write_text('Answer: 100.0.\n', encoding='utf-8')
        (self.latex / 'result.tex').write_text('Result: 100.00.\n', encoding='utf-8')
        self.save_projection()

    def tearDown(self):
        self.tmp.cleanup()

    def save_projection(self):
        path = self.root / '模型论文框架.md'
        text = path.read_text(encoding='utf-8').split('### Paper Fragment Dependency Map', 1)[0]
        lines = ['### Paper Fragment Dependency Map', '',
                 '| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |',
                 '|---|---|---|---|---|---|---|']
        for row in self.fragments:
            values = [row[key] for key in ('id', 'kind', 'scope')]
            values += [', '.join(row['depends_on']), row['anchor'],
                       f"`{row['source_file']}`", row['status']]
            lines.append('| ' + ' | '.join(values) + ' |')
        text += '\n'.join(lines) + '\n'
        path.write_text(text, encoding='utf-8')
        self.state['paper_framework']['sha256'] = sha256_text(text)
        save(self.root, self.state)

    def synthetic_compile_proof(self):
        """Build a proof-chain fixture without claiming a real TeX compilation."""
        main = self.latex / 'main.tex'
        framework = self.root / '模型论文框架.md'
        audit = latex_audit.write_audit_report(main_file=main, findings=[], framework_path=framework)
        self.assertEqual(audit['status'], 'passed', audit)
        (self.latex / 'main.pdf').write_bytes(b'%PDF-synthetic-attestation-fixture')
        (self.latex / 'main.log').write_text('This is XeTeX\n', encoding='utf-8')
        inputs = delivery.source_bundle_files(main)
        (self.latex / 'main.fls').write_text(
            f'PWD {self.latex.resolve()}\n' + ''.join(
                f'INPUT {path.relative_to(self.latex).as_posix()}\n' for path in inputs),
            encoding='utf-8',
        )
        profile = delivery.current_profile_config('cumcm')
        compile_report = delivery.write_compile_report(
            project=self.latex, main=main, profile='cumcm', engine='xelatex',
            bibliography='biber', sequence=profile['sequence'], profile_config=profile,
        )
        self.assertEqual(compile_report['status'], 'passed', compile_report)
        return audit, compile_report

    def test_live_matched_text_passes_without_authorizing_semantics_or_writing(self):
        before = bytes_in(self.root)
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'passed', gate)
        self.assertEqual(gate['human_semantic_coverage'], 'not_assessed')
        self.assertIn('state/project_state.yaml', gate['observed_sources']['project'])
        self.assertIn('final_latex/result.tex', gate['observed_sources']['project'])
        self.assertEqual(bytes_in(self.root), before)

    def test_legacy_policies_keep_formal_gate_unselected_but_unknown_pair_fails(self):
        for pair in [('1.0.0', 'observe'), ('1.1.0', 'propagate')]:
            with self.subTest(pair=pair):
                self.state['paper_framework']['claim_consumption_policy'].update(
                    protocol_version=pair[0], mode=pair[1])
                save(self.root, self.state)
                self.assertEqual(claims.formal_text_gate(self.root)['status'], 'not_applicable')
        self.state['paper_framework']['claim_consumption_policy'].pop('required_consumptions')
        save(self.root, self.state)
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')
        self.state['paper_framework']['claim_consumption_policy'].update(
            protocol_version='1.9.0', mode='enforce_latex_text')
        save(self.root, self.state)
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')

    def test_missing_state_is_legacy_but_creation_during_gate_fails(self):
        (self.root / 'state/project_state.yaml').unlink()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'not_applicable', gate)
        self.assertIsNone(gate['observed_sources']['project']['state/project_state.yaml'])
        recheck = claims.bounded._recheck

        def inject_state(root, observed):
            if root == self.root and observed.get('state/project_state.yaml') is None:
                save(self.root, self.state)
            return recheck(root, observed)

        with patch.object(claims.bounded, '_recheck', side_effect=inject_state):
            gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('read-set conflict' in issue for issue in gate['issues']), gate)

    def test_real_numeric_conflict_wording_and_unregistered_candidate_fail(self):
        result = self.latex / 'result.tex'
        result.write_text('Result: 110.00.\n', encoding='utf-8')
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')
        self.state['subproblems']['Q1'].update(optimality_claim='heuristic',
                                                result_analysis_status='not_required')
        result.write_text('Result: 100.00; globally optimal and robust across all cases.\n', encoding='utf-8')
        save(self.root, self.state)
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')
        self.state['subproblems']['Q1'].pop('optimality_claim', None)
        self.state['subproblems']['Q1'].pop('result_analysis_status', None)
        result.write_text('Result: 100.00.\nOther unregistered value: 17.\n', encoding='utf-8')
        save(self.root, self.state)
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')

    def test_stale_active_fragment_and_missing_required_kind_fail(self):
        self.fragments[1]['status'] = 'stale'
        self.save_projection()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('not current' in item for item in gate['issues']), gate)
        self.fragments[1]['status'] = 'current'
        self.fragments.pop()
        self.save_projection()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('required text consumption' in item for item in gate['issues']), gate)

    def test_single_file_tex_is_outside_enforced_scope(self):
        (self.latex / 'main.tex').write_text(
            '\\documentclass{article}\\begin{document}Answer: 100.0.\\end{document}', encoding='utf-8')
        self.assertEqual(claims.formal_text_gate(self.root)['status'], 'failed')

    def test_non_text_claim_linked_kinds_fail_even_without_numeric_assertion(self):
        claim = self.state['paper_framework']['claim_evidence']['claims'][0]
        claim.pop('assertion', None)
        claim.pop('numeric_profile_id', None)
        self.state['paper_framework']['claim_consumption_policy']['required_consumptions'][0][
            'fragment_kinds'].append('figure_or_table_claim')
        self.fragments.append({
            'id': 'paper.caption.q1', 'kind': 'figure_or_table_claim', 'scope': 'Q1',
            'depends_on': ['claim:answer_claim'], 'anchor': 'Caption:',
            'source_file': 'final_latex/result.tex', 'status': 'current',
        })
        (self.latex / 'result.tex').write_text('Result: 100.00.\nCaption: diagram.\n', encoding='utf-8')
        self.save_projection()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('outside the formal text gate' in issue for issue in gate['issues']), gate)
        self.state['paper_framework']['claim_consumption_policy']['required_consumptions'][0][
            'fragment_kinds'][-1] = 'paper_section'
        self.fragments[-1]['kind'] = 'paper_section'
        self.save_projection()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'failed', gate)
        self.assertTrue(any('outside the formal text gate' in issue for issue in gate['issues']), gate)

    def test_formal_audit_binds_b2_read_set_and_rejects_changed_state(self):
        main = self.latex / 'main.tex'
        framework = self.root / '模型论文框架.md'
        report = latex_audit.write_audit_report(main_file=main, findings=[], framework_path=framework)
        self.assertEqual(report['claim_text_gate']['status'], 'passed', report)
        self.assertFalse(delivery.verify_audit_report(
            project=self.latex, main=main, report=report), report)
        self.state['project']['state_generation'] = self.state['project'].get('state_generation', 0) + 1
        save(self.root, self.state)
        issues = delivery.verify_audit_report(project=self.latex, main=main, report=report)
        self.assertTrue(any('stale' in issue or '未通过' in issue for issue in issues), issues)

    def test_formal_sync_preserves_audit_and_compile_proof_bytes(self):
        # First materialize the ordinary sync metadata; the formal no-op path
        # must then preserve the exact State/Framework proof inputs.
        synchronizer.synchronize(self.root, write=True)
        # The first sync sees the synthetic fixture's newly added paper files as
        # downstream changes. Re-establish the fixture's reviewed current rows.
        self.state = yaml.safe_load((self.root / 'state/project_state.yaml').read_text(encoding='utf-8'))
        self.fragments = self.state['paper_framework']['paper_fragments']
        for row in self.fragments:
            row['status'] = 'current'
        for entry in self.state['subproblems'].values():
            entry['artifacts_stale'] = False
        self.save_projection()
        gate = claims.formal_text_gate(self.root)
        self.assertEqual(gate['status'], 'passed', gate['issues'])
        framework = self.root / '模型论文框架.md'
        audit, compile_report = self.synthetic_compile_proof()
        main = self.latex / 'main.tex'
        state_before = (self.root / 'state/project_state.yaml').read_bytes()
        framework_before = framework.read_bytes()
        # The A2 smoke State is intentionally not a complete delivery project;
        # isolate its unrelated project-wide preflight and snapshot transition.
        with patch.object(synchronizer, '_apply_snapshot_to_state', return_value=(False, [])), \
                patch.object(synchronizer, 'contract_preflight_issues', return_value=[]), \
                patch.object(synchronizer, '_scope_artifact_issues', return_value=[]):
            report = synchronizer.synchronize(self.root, write=True, delivery_scope='latex')
        self.assertEqual(report['status'], 'passed', report['issues'])
        self.assertFalse(report['state_write_performed'], report)
        self.assertEqual((self.root / 'state/project_state.yaml').read_bytes(), state_before)
        self.assertEqual(framework.read_bytes(), framework_before)
        self.assertFalse(delivery.verify_audit_report(project=self.latex, main=main, report=audit))
        self.assertFalse(delivery.verify_compile_report(
            project=self.latex, main=main, pdf=self.latex / 'main.pdf', report=compile_report))

    def test_direct_submission_validation_rejects_missing_formal_compile_proof(self):
        pdf = self.latex / 'main.pdf'
        pdf.write_bytes(b'%PDF-synthetic-only')
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        manifest = {'package_schema_version': '1.0.0', 'kind': 'reproducibility',
                    'files': [{'path': 'final_latex/main.pdf', 'sha256': digest}]}
        package = self.root / 'submission.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('submission_manifest.yaml', yaml.safe_dump(manifest))
            archive.write(pdf, 'final_latex/main.pdf')
        with patch.object(package_validator, 'reproducibility_requirements', return_value=(set(), [])):
            report = package_validator.validate_package(self.root, package)
        self.assertEqual(report['status'], 'failed', report)
        self.assertTrue(any('compile_report.yaml' in issue for issue in report['issues']), report)

    def test_direct_package_detects_workbook_change_after_zip_checks(self):
        self.synthetic_compile_proof()
        pdf = self.latex / 'main.pdf'
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        manifest = {'package_schema_version': '1.0.0', 'kind': 'reproducibility',
                    'files': [{'path': 'final_latex/main.pdf', 'sha256': digest}]}
        package = self.root / 'submission.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('submission_manifest.yaml', yaml.safe_dump(manifest))
            archive.write(pdf, 'final_latex/main.pdf')
        with patch.object(package_validator, 'reproducibility_requirements', return_value=(set(), [])):
            baseline = package_validator.validate_package(self.root, package)
        self.assertEqual(baseline['status'], 'passed', baseline)
        workbook = self.root / self.state['subproblems']['Q1']['solution_workbook']
        original_hash = package_validator._sha256_stream
        visits = 0

        def drift_after_zip_checks(path):
            nonlocal visits
            if path == package:
                visits += 1
                if visits == 2:
                    workbook.write_bytes(workbook.read_bytes() + b'drift')
            return original_hash(path)

        with patch.object(package_validator, 'reproducibility_requirements', return_value=(set(), [])), \
                patch.object(package_validator, '_sha256_stream', side_effect=drift_after_zip_checks):
            report = package_validator.validate_package(self.root, package)
        self.assertEqual(report['status'], 'failed', report)
        self.assertTrue(any('读集冲突' in issue for issue in report['issues']), report)

    def test_direct_package_rejects_state_change_between_initial_read_and_gate(self):
        self.synthetic_compile_proof()
        pdf = self.latex / 'main.pdf'
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        package = self.root / 'submission.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('submission_manifest.yaml', yaml.safe_dump({
                'package_schema_version': '1.0.0', 'kind': 'reproducibility',
                'files': [{'path': 'final_latex/main.pdf', 'sha256': digest}],
            }))
            archive.write(pdf, 'final_latex/main.pdf')
        real_gate = claims.formal_text_gate

        def drift_state(root, **kwargs):
            self.state['project']['state_generation'] = self.state['project'].get('state_generation', 0) + 1
            save(self.root, self.state)
            return real_gate(root, **kwargs)

        with patch.object(package_validator, 'reproducibility_requirements', return_value=(set(), [])), \
                patch.object(claims, 'formal_text_gate', side_effect=drift_state):
            report = package_validator.validate_package(self.root, package)
        self.assertEqual(report['status'], 'failed', report)
        self.assertTrue(any('State首读与B2门读集不一致' in issue for issue in report['issues']), report)

    def test_formal_sync_cannot_accept_tex_change_after_compile_proof_check(self):
        self.synthetic_compile_proof()
        result_tex = self.latex / 'result.tex'
        real_gate = claims.formal_text_gate
        visits = 0

        def drift_before_gate(root, **kwargs):
            nonlocal visits
            visits += 1
            if visits == 2:
                result_tex.write_text('Result: 100.00. \n', encoding='utf-8')
            return real_gate(root, **kwargs)

        with patch.object(claims, 'formal_text_gate', side_effect=drift_before_gate):
            try:
                report = synchronizer.synchronize(self.root, write=True, delivery_scope='latex')
            except transaction.ReadSetConflictError:
                pass
            else:
                self.assertEqual(report['status'], 'failed', report['issues'])
        self.assertGreaterEqual(visits, 2)


if __name__ == '__main__':
    unittest.main()
