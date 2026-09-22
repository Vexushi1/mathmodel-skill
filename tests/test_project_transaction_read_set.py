"""Byte-bound control-plane commits; all files are isolated maintenance fixtures."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
import project_transaction as TX


class ReadSetTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'state').mkdir()
        self.state = {'project': {'state_generation': 0, 'current_phase': 'model_design'},
                      'subproblems': {}}
        self.path = self.root / TX.STATE_RELATIVE_PATH
        self.path.write_text(yaml.safe_dump(self.state), encoding='utf-8')
        (self.root / '模型论文框架.md').write_text('old framework\n', encoding='utf-8')
        (self.root / 'input.bin').write_bytes(bytes(range(256)))

    def hashes(self, *paths):
        return {relative: TX.sha256_file(self.root / relative)
                if (self.root / relative).is_file() else None
                for relative in (TX.STATE_RELATIVE_PATH, *paths)}

    def commit(self, expected=None, **kwargs):
        return TX.commit_project_state(
            self.root, self.state, expected_generation=0,
            expected_file_hashes=self.hashes() if expected is None else expected, **kwargs)

    def assert_clean(self):
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())
        self.assertEqual(list(self.root.rglob('*.stage')), [])
        self.assertEqual(list(self.root.rglob('*.bak')), [])

    def test_matching_snapshot_and_unicode_companion_commit(self):
        original_input = (self.root / 'input.bin').read_bytes()
        expected = self.hashes('input.bin', '模型论文框架.md', 'report.yaml')
        result = self.commit(expected, writes_before_state=[('模型论文框架.md', 'new framework\n')],
                             writes_after_state=[('report.yaml', 'status: current\n')])
        self.assertEqual(result['target_generation'], 1)
        self.assertEqual(self.state['project']['state_generation'], 1)
        self.assertEqual((self.root / 'input.bin').read_bytes(), original_input)
        self.assertEqual((self.root / '模型论文框架.md').read_text(), 'new framework\n')
        self.assertEqual(TX.JOURNAL_VERSION, 1)
        self.assert_clean()

    def test_same_generation_change_before_call_rejects(self):
        expected = self.hashes()
        changed = self.path.read_bytes() + b'# same generation change\n'
        self.path.write_bytes(changed)
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected)
        self.assertEqual(self.path.read_bytes(), changed)
        self.assertEqual(self.state['project']['state_generation'], 0)
        self.assert_clean()

    def test_same_generation_changes_during_preparation_reject(self):
        original = self.path.read_bytes()
        for point in ('before_stage', 'after_stage', 'after_validation', 'after_generation_check'):
            with self.subTest(point=point):
                self.path.write_bytes(original)
                expected = self.hashes()
                changed = original + b'# concurrent same-generation edit\n'
                def edit(actual):
                    if actual == point:
                        self.path.write_bytes(changed)
                with self.assertRaises(TX.ReadSetConflictError):
                    self.commit(expected, failure_hook=edit)
                self.assertEqual(self.path.read_bytes(), changed)
                self.assert_clean()

    def test_binary_source_drift_does_not_write_state(self):
        expected = self.hashes('input.bin')
        original_state = self.path.read_bytes()
        def edit(point):
            if point == 'after_generation_check':
                (self.root / 'input.bin').write_bytes(b'changed\x00\xff')
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected, failure_hook=edit)
        self.assertEqual(self.path.read_bytes(), original_state)
        self.assertEqual((self.root / 'input.bin').read_bytes(), b'changed\x00\xff')
        self.assert_clean()

    def test_missing_source_and_new_unexpected_file_reject(self):
        expected = self.hashes('input.bin')
        (self.root / 'input.bin').unlink()
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected)
        expected = self.hashes('absent.bin')
        (self.root / 'absent.bin').write_bytes(b'unexpected')
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected)
        self.assert_clean()

    def test_absent_state_can_initialize_with_explicit_absence(self):
        self.path.unlink()
        result = self.commit({TX.STATE_RELATIVE_PATH: None})
        self.assertEqual(result['target_generation'], 1)
        self.assertEqual(yaml.safe_load(self.path.read_text())['project']['state_generation'], 1)
        self.assert_clean()

    def test_absent_source_can_remain_absent(self):
        self.commit(self.hashes('never-created.bin'))
        self.assertFalse((self.root / 'never-created.bin').exists())

    def test_uppercase_digests_match_raw_bytes(self):
        self.commit({key: digest.upper() for key, digest in self.hashes().items()})
        self.assertEqual(self.state['project']['state_generation'], 1)

    def test_invalid_read_sets_reject_before_staging(self):
        cases = [{}, [], {TX.STATE_RELATIVE_PATH: ''}, {TX.STATE_RELATIVE_PATH: 'z'*64},
                 {TX.STATE_RELATIVE_PATH: True}, {TX.STATE_RELATIVE_PATH: '0'*63},
                 {TX.STATE_RELATIVE_PATH: '0'*64+'\n'}]
        original = self.path.read_bytes()
        for expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(TX.ProjectTransactionError):
                    self.commit(expected)
                self.assertEqual(self.path.read_bytes(), original)
                self.assert_clean()

    def test_all_companion_targets_must_be_covered(self):
        with self.assertRaisesRegex(TX.ProjectTransactionError, 'every write target'):
            self.commit(writes_before_state=[('模型论文框架.md', 'new')])
        with self.assertRaisesRegex(TX.ProjectTransactionError, 'every write target'):
            self.commit(writes_after_state=[('report.yaml', 'new')])
        self.assert_clean()

    def test_invalid_or_reserved_paths_reject(self):
        bad = ('../outside', '/absolute', 'state/../x', 'state//x', './input.bin',
               'state\\x', 'C:relative', 'input.bin:stream', 'bad\0name', '', TX.JOURNAL_RELATIVE_PATH, TX.LOCK_RELATIVE_PATH)
        for relative in bad:
            with self.subTest(relative=relative):
                expected = self.hashes(); expected[relative] = None
                with self.assertRaises(TX.ProjectTransactionError):
                    self.commit(expected)
                self.assert_clean()

    def test_directory_does_not_satisfy_absence_or_file_hash(self):
        (self.root / 'directory').mkdir()
        for digest in (None, '0'*64):
            expected = self.hashes(); expected['directory'] = digest
            with self.subTest(digest=digest), self.assertRaises(TX.ReadSetConflictError):
                self.commit(expected)
        self.assert_clean()

    @unittest.skipIf(sys.platform == 'win32', 'symlink creation may require Windows privileges')
    def test_symlink_and_dangling_symlink_are_not_absence(self):
        for target in ('input.bin', 'missing.bin'):
            link = self.root / 'alias.bin'
            link.symlink_to(self.root / target)
            with self.subTest(target=target), self.assertRaises(TX.ProjectTransactionError):
                self.commit({**self.hashes(), 'alias.bin': None})
            link.unlink()
        self.assert_clean()

    def test_expected_generation_is_not_a_boolean_or_coercible_string(self):
        for generation in (True, -1, '0', 0.0):
            with self.subTest(generation=generation), self.assertRaises(TX.ProjectTransactionError):
                TX.commit_project_state(self.root, self.state, expected_generation=generation,
                                        expected_file_hashes=self.hashes())
        self.assert_clean()

    def test_stale_generation_still_rejects_with_matching_bytes(self):
        with self.assertRaises(TX.GenerationConflictError):
            TX.commit_project_state(self.root, self.state, expected_generation=1,
                                    expected_file_hashes=self.hashes())
        self.assert_clean()

    def test_caller_read_set_cannot_be_rewritten_by_validator(self):
        expected = self.hashes()
        changed = self.path.read_bytes() + b'# validator mutation\n'
        def validator(staged):
            self.path.write_bytes(changed)
            expected[TX.STATE_RELATIVE_PATH] = TX.sha256_file(self.path)
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected, validators=[validator])
        self.assertEqual(self.path.read_bytes(), changed)
        self.assert_clean()

    def test_validator_sees_candidate_generation_but_failure_keeps_live(self):
        original = self.path.read_bytes()
        self.state['project']['current_phase'] = 'candidate'
        def validator(staged):
            candidate = yaml.safe_load(staged[TX.STATE_RELATIVE_PATH].read_text())
            self.assertEqual(candidate['project']['state_generation'], 1)
            self.assertEqual(candidate['project']['current_phase'], 'candidate')
            self.assertEqual(self.path.read_bytes(), original)
            raise ValueError('reject candidate')
        with self.assertRaisesRegex(ValueError, 'reject candidate'):
            self.commit(validators=[validator])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.state['project']['state_generation'], 0)
        self.assert_clean()

    def test_staged_file_mutation_by_validator_is_not_committed(self):
        original = self.path.read_bytes()
        def validator(staged):
            with staged[TX.STATE_RELATIVE_PATH].open('a') as handle:
                handle.write('# edited staged bytes\n')
        with self.assertRaisesRegex(TX.ProjectTransactionError, 'staged content changed'):
            self.commit(validators=[validator])
        self.assertEqual(self.path.read_bytes(), original)
        self.assert_clean()

    def test_backup_corruption_is_rejected_before_prepare(self):
        original = self.path.read_bytes()
        def corrupt(point):
            if point == 'after_stage':
                for backup in self.root.rglob('*.bak'):
                    backup.write_bytes(b'corrupt')
        with self.assertRaisesRegex(TX.ProjectTransactionError, 'backup differs'):
            self.commit(failure_hook=corrupt)
        self.assertEqual(self.path.read_bytes(), original)
        self.assert_clean()

    def test_hash_io_failure_leaves_live_state_unchanged(self):
        expected = self.hashes('input.bin'); original = self.path.read_bytes()
        real_hash = TX.sha256_file
        def fail_input(path):
            if path.name == 'input.bin':
                raise OSError('read failed')
            return real_hash(path)
        with patch.object(TX, 'sha256_file', fail_input), self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected)
        self.assertEqual(self.path.read_bytes(), original)
        self.assert_clean()

    def test_guarded_commit_does_not_implicitly_recover_prepared_journal(self):
        expected = self.hashes()
        def crash(point):
            if point == 'after_journal_prepared':
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.commit(expected, failure_hook=crash)
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(TX.TransactionRecoveryError, 'explicit recovery'):
            self.commit(expected)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        recovered = TX.recover_project_transaction(self.root)
        self.assertEqual(recovered['status'], 'rolled_forward')
        self.assert_clean()

    def test_guarded_commit_does_not_silently_clean_other_journal_states(self):
        journal = self.root / TX.JOURNAL_RELATIVE_PATH
        for content in ('not: valid journal\n', 'status: committed\nversion: 1\nentries: []\n'):
            with self.subTest(content=content):
                journal.write_text(content)
                with self.assertRaises(TX.TransactionRecoveryError):
                    self.commit()
                self.assertEqual(journal.read_text(), content)
        journal.unlink()
        self.assert_clean()

    def test_guarded_interruption_recovers_forward_at_each_replace_boundary(self):
        boundaries = ('after_journal_prepared', 'after_replace:模型论文框架.md',
                      'after_replace:state/project_state.yaml', 'after_replace:report.yaml')
        original = self.path.read_bytes()
        for boundary in boundaries:
            with self.subTest(boundary=boundary):
                self.path.write_bytes(original)
                self.state['project']['state_generation'] = 0
                expected = self.hashes('模型论文框架.md', 'report.yaml')
                def crash(point):
                    if point == boundary:
                        raise RuntimeError(boundary)
                with self.assertRaises(RuntimeError):
                    self.commit(expected, failure_hook=crash,
                                writes_before_state=[('模型论文框架.md', 'new framework\n')],
                                writes_after_state=[('report.yaml', 'new report\n')])
                result = TX.recover_project_transaction(self.root)
                self.assertEqual(result['status'], 'rolled_forward')
                self.assertEqual(yaml.safe_load(self.path.read_text())['project']['state_generation'], 1)
                self.assertEqual((self.root / 'report.yaml').read_text(), 'new report\n')
                self.assert_clean()

    def test_third_party_write_after_prepare_is_not_overwritten(self):
        expected = self.hashes(); changed = self.path.read_bytes()+b'# third party\n'
        def edit(point):
            if point == 'before_replace:state/project_state.yaml':
                self.path.write_bytes(changed)
        with self.assertRaises(TX.ReadSetConflictError):
            self.commit(expected, failure_hook=edit)
        self.assertEqual(self.path.read_bytes(), changed)
        self.assertTrue((self.root / TX.JOURNAL_RELATIVE_PATH).is_file())
        with self.assertRaises(TX.TransactionRecoveryError):
            TX.recover_project_transaction(self.root)
        self.assertEqual(self.path.read_bytes(), changed)

    def test_prepared_staged_tamper_is_not_written(self):
        original = self.path.read_bytes()
        def tamper(point):
            if point == 'before_replace:state/project_state.yaml':
                for path in self.root.rglob('*.stage'):
                    path.write_bytes(b'tampered')
        with self.assertRaisesRegex(TX.ProjectTransactionError, 'prepared staged content changed'):
            self.commit(failure_hook=tamper)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(TX.TransactionRecoveryError):
            TX.recover_project_transaction(self.root)

    def test_two_guarded_writers_do_not_rebase_stale_snapshot(self):
        expected = self.hashes(); first = deepcopy(self.state); second = deepcopy(self.state)
        inside = threading.Event(); release = threading.Event(); outcomes = {}
        def pause(point):
            if point == 'after_generation_check':
                inside.set()
                if not release.wait(5):
                    raise RuntimeError('writer wait timeout')
        def run(name, candidate, hook=None):
            try:
                outcomes[name] = TX.commit_project_state(
                    self.root, candidate, expected_generation=0,
                    expected_file_hashes=expected, failure_hook=hook)
            except Exception as exc:
                outcomes[name] = exc
        one = threading.Thread(target=run, args=('first', first, pause), daemon=True)
        two = threading.Thread(target=run, args=('second', second), daemon=True)
        one.start()
        try:
            self.assertTrue(inside.wait(5))
            two.start()
        finally:
            release.set()
            one.join(5)
            if two.ident is not None:
                two.join(5)
        self.assertFalse(one.is_alive()); self.assertFalse(two.is_alive())
        self.assertIsInstance(outcomes.get('first'), dict)
        self.assertIsInstance(outcomes.get('second'), TX.ReadSetConflictError)
        self.assertEqual(yaml.safe_load(self.path.read_text())['project']['state_generation'], 1)
        self.assert_clean()

    def test_unguarded_legacy_call_retains_recovery_semantics(self):
        def crash(point):
            if point == 'after_journal_prepared':
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.commit(failure_hook=crash)
        # An old caller explicitly using the target generation still invokes legacy recovery.
        result = TX.commit_project_state(self.root, self.state, expected_generation=1)
        self.assertEqual(result['target_generation'], 2)
        self.assert_clean()


if __name__ == '__main__':
    unittest.main()
