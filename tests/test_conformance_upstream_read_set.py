"""A2 T15/T17/T28 regressions: upstream reads and alias-free synthetic declarations."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
for location in (ROOT, ROOT / 'scripts'):
    if str(location) not in sys.path:
        sys.path.insert(0, str(location))
import conformance_gate as gate
import model_code_conformance as audit
import project_transaction as tx
import stage_code
import validate_code_delivery as delivery
import validate_user_execution as receipts
from tests import conformance_a2_smoke as smoke
from tests.test_model_code_conformance import fixture, save, bytes_in
from tests.test_solver_backend_end_to_end import reference_digest


def accepted_primary(root, required=('primary', 'analysis')):
    """Actually run/accept the synthetic primary, with primary-only helper/input."""
    state = smoke.prepare(root, required=required)
    code, config = smoke.prepare_stage(root, state, 'python', 'primary')
    previous = deepcopy(config)
    helper = code.parent / 'primary_only_helper.py'
    helper.write_text('def identity(value):\n    return value\n', encoding='utf-8')
    auxiliary = root / 'primary_only.json'
    auxiliary.write_bytes((root / 'constraints.json').read_bytes())
    config['code_dependencies'] = [{'path': helper.relative_to(root).as_posix(),
                                     'sha256': hashlib.sha256(helper.read_bytes()).hexdigest()}]
    config['auxiliary_data_paths'] = ['primary_only.json']
    config['auxiliary_data_sha256'] = reference_digest(root, ['primary_only.json'])
    text = code.read_text(encoding='utf-8')
    marker = f'RUN_CONFIG = {previous!r}'
    assert text.count(marker) == 1
    text = text.replace(marker, f'RUN_CONFIG = {config!r}')
    # This generated synthetic helper fixture must emit the real full source bundle.
    original_digest = 'code_bundle_sha256=digest(root, [code.relative_to(root).as_posix()])'
    assert text.count(original_digest) == 1
    text = text.replace(original_digest,
        "code_bundle_sha256=digest(root, [code.relative_to(root).as_posix(), *[item['path'] for item in config['code_dependencies']]])")
    code.write_text(text, encoding='utf-8')
    if 'primary' in required:
        smoke.declare(root, state, 'primary')
    delivery.update_state(root, config, code)
    ran = subprocess.run([sys.executable, '-B', str(code)], capture_output=True, text=True)
    assert ran.returncode == 0, ran.stdout + ran.stderr
    output = io.StringIO()
    with patch.object(sys, 'argv', ['validate_user_execution.py', str(root), '--workbook',
                                   config['expected_workbook'], '--write', '--strict']), redirect_stdout(output):
        assert receipts.main() == 0, output.getvalue()
    state = yaml.safe_load((root / tx.STATE_RELATIVE_PATH).read_text(encoding='utf-8'))
    return state, {'entry': code, 'helper': helper, 'auxiliary': auxiliary}


class UpstreamReadSetTests(unittest.TestCase):
    def test_analysis_inventory_captures_upstream_without_forcing_primary_policy(self):
        for required in (('analysis',), ('primary', 'analysis')):
            with self.subTest(required=required), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state, sources = accepted_primary(root, required)
                smoke.prepare_stage(root, state, 'python', 'analysis')
                before = bytes_in(root)
                report = gate.inspect_gate(root, state, 'Q1', 'analysis')
                self.assertFalse(report['issues'], report)
                self.assertEqual(before, bytes_in(root))
                for path in sources.values():
                    relative = path.relative_to(root).as_posix()
                    self.assertEqual(report['observed_sources']['project'].get(relative),
                                     hashlib.sha256(path.read_bytes()).hexdigest(), relative)
                self.assertFalse(report['execution_authorized'])
                if required == ('analysis',):
                    self.assertNotIn('primary', state['subproblems']['Q1'].get('implementation_conformance', {}))
                    self.assertNotIn(gate.DELIVERY, state['subproblems']['Q1']['solver_execution']['primary'])

    def test_analysis_delivery_rejects_late_upstream_entry_helper_or_auxiliary(self):
        for kind in ('entry', 'helper', 'auxiliary'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state, sources = accepted_primary(root, ('analysis',))
                code, config = smoke.prepare_stage(root, state, 'python', 'analysis')
                before = (root / tx.STATE_RELATIVE_PATH).read_bytes()
                original = tx.commit_project_state
                def late_change(*args, **kwargs):
                    path = sources[kind]
                    path.write_bytes(path.read_bytes() + b'\n ')
                    return original(*args, **kwargs)
                with patch.object(delivery.PROJECT_TX, 'commit_project_state', side_effect=late_change):
                    with self.assertRaises(tx.ReadSetConflictError):
                        delivery.update_state(root, config, code)
                self.assertEqual(before, (root / tx.STATE_RELATIVE_PATH).read_bytes())
                self.assertFalse((root / tx.JOURNAL_RELATIVE_PATH).exists())

    def test_real_analysis_receipt_rejects_late_upstream_sources_before_commit(self):
        for required in (('analysis',), ('primary', 'analysis')):
            with self.subTest(required=required), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state, sources = accepted_primary(root, required)
                code, config = smoke.prepare_stage(root, state, 'python', 'analysis')
                delivery.update_state(root, config, code)
                ran = subprocess.run([sys.executable, '-B', str(code)], capture_output=True, text=True)
                self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
                before = (root / tx.STATE_RELATIVE_PATH).read_bytes()
                original = tx.commit_project_state
                for kind, path in sources.items():
                    with self.subTest(kind=kind):
                        old = path.read_bytes()
                        def late_change(*args, **kwargs):
                            path.write_bytes(old + b'\n ')
                            return original(*args, **kwargs)
                        try:
                            with patch.object(receipts.PROJECT_TX, 'commit_project_state', side_effect=late_change), \
                                    patch.object(sys, 'argv', ['validate_user_execution.py', str(root), '--workbook',
                                                              config['expected_workbook'], '--write', '--strict']), \
                                    redirect_stdout(io.StringIO()):
                                with self.assertRaises(tx.ReadSetConflictError):
                                    receipts.main()
                            self.assertEqual(before, (root / tx.STATE_RELATIVE_PATH).read_bytes())
                            self.assertFalse((root / tx.JOURNAL_RELATIVE_PATH).exists())
                        finally:
                            path.write_bytes(old)
                            # Restore the synthetic pre-test snapshot if testing the unfixed baseline.
                            (root / tx.STATE_RELATIVE_PATH).write_bytes(before)

    def test_upstream_source_changed_before_inspection_is_not_freshly_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state, sources = accepted_primary(root, ('analysis',))
            smoke.prepare_stage(root, state, 'python', 'analysis')
            path = sources['helper']
            path.write_bytes(path.read_bytes() + b'\n# changed\n')
            before = bytes_in(root)
            report = gate.inspect_gate(root, state, 'Q1', 'analysis')
            self.assertTrue(report['issues'], report)
            self.assertEqual(report['status'], 'blocked')
            self.assertEqual(before, bytes_in(root))


class SyntheticMappingSerializationTests(unittest.TestCase):
    def test_matlab_reverse_candidates_do_not_generate_yaml_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state, _, _ = fixture(root, 'matlab', expression='max(h * (u - ambient), 0)')
            smoke.declare(root, state, 'primary')
            self.assertTrue(state['subproblems']['Q1']['implementation_conformance']['primary']['reverse_review'])
            text = (root / tx.STATE_RELATIVE_PATH).read_text(encoding='utf-8')
            self.assertFalse(any(isinstance(event, yaml.events.AliasEvent) for event in yaml.parse(text)))
            report = audit.inspect_project(root, 'Q1', 'primary')
            self.assertEqual(report['status'], 'structure_verified', report)
            self.assertEqual(report['native_execution'], 'not_run')


if __name__ == '__main__':
    unittest.main()
