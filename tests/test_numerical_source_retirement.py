"""Explicit migration freshness events, not migration authorization or live file writes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
import state_transitions as ST

CONTRACT = yaml.safe_load((ROOT / 'core/state_transition_contract.yaml').read_text(encoding='utf-8'))
PRIMARY = 'primary_numerical_source_retired'
ANALYSIS = 'analysis_numerical_source_retired'


def record(dependencies=()):
    return {'depends_on': list(dependencies), 'model_challenge_status': 'passed',
            'human_model_approval_status': 'approved', 'semantic_identity_hash': 'a'*64,
            'primary_execution_status': 'accepted', 'analysis_execution_status': 'accepted',
            'result_quality_status': 'passed', 'result_analysis_status': 'passed',
            'validation_status': 'passed', 'result_summary_status': 'current',
            'artifacts_stale': False, 'stale_layers': [],
            'solver_execution': {'primary': {'bundle_sha256': 'b'*64, 'validated_bundle_sha256': 'b'*64},
                                 'analysis': {'bundle_sha256': 'c'*64, 'validated_bundle_sha256': 'c'*64}}}


def dependency(source, kind):
    return source if kind is None else {'question': source, 'kind': kind}


class NumericalSourceRetirementTests(unittest.TestCase):
    def transition(self, state, event, source='Q1'):
        return ST.apply_transition(state, event=event, source_question=source, contract=CONTRACT)

    def test_two_retirement_events_reuse_existing_profiles(self):
        self.assertEqual(CONTRACT['version'], '1.2.0')
        for event, profile in ((PRIMARY, 'primary_result'), (ANALYSIS, 'analysis_result')):
            with self.subTest(event=event):
                spec = CONTRACT['transition_events'][event]
                self.assertEqual(spec['own_profile'], profile)
                self.assertEqual(spec['caller_scope'], 'explicit_project_backend_migration_only')
                self.assertEqual(set(spec['emitted_impacts']), {'data', 'parameter', 'result'})

    def test_each_retirement_event_propagates_only_matching_typed_edges(self):
        for event in (PRIMARY, ANALYSIS):
            for kind in ('data', 'parameter', 'result', 'model'):
                with self.subTest(event=event, kind=kind):
                    state = {'subproblems': {'Q1': record(), 'Q2': record([dependency('Q1', kind)])}}
                    before_q2 = deepcopy(state['subproblems']['Q2'])
                    report = self.transition(state, event)
                    q2 = state['subproblems']['Q2']
                    self.assertEqual(q2['human_model_approval_status'], 'approved')
                    self.assertEqual(q2['semantic_identity_hash'], 'a'*64)
                    if kind == 'model':
                        self.assertEqual(report['affected_questions'], ['Q1'])
                        self.assertEqual(q2, before_q2)
                    else:
                        self.assertEqual(report['affected_questions'], ['Q1', 'Q2'])
                        self.assertIn('solution_workbook', q2['stale_layers'])
                        self.assertEqual(q2['primary_execution_status'], 'pending')
                        self.assertEqual(q2['result_quality_status'], 'pending')
                        self.assertEqual(report['transitions'][1]['dependency_kind'], kind)

    def test_analysis_only_retirement_does_not_revoke_unaffected_primary(self):
        state = {'subproblems': {'Q1': record()}}
        q1 = state['subproblems']['Q1']
        primary_binding = deepcopy(q1['solver_execution']['primary'])
        self.transition(state, ANALYSIS)
        self.assertEqual(q1['primary_execution_status'], 'accepted')
        self.assertEqual(q1['result_quality_status'], 'passed')
        self.assertEqual(q1['solver_execution']['primary'], primary_binding)
        self.assertNotIn('primary_code', q1['stale_layers'])
        self.assertNotIn('solution_workbook', q1['stale_layers'])
        self.assertIn('analysis_code', q1['stale_layers'])
        self.assertEqual(q1['analysis_execution_status'], 'pending')

    def test_primary_retirement_clears_analysis_disposition_reason(self):
        state = {'subproblems': {'Q1': record()}}
        state['subproblems']['Q1'].update(result_analysis_status='not_required',
                                         result_analysis_requirement_reason='old result was sufficient')
        self.transition(state, PRIMARY)
        q1 = state['subproblems']['Q1']
        self.assertNotIn('result_analysis_requirement_reason', q1)
        self.assertEqual(q1['result_analysis_status'], 'pending')
        self.assertIn('primary_code', q1['stale_layers'])
        self.assertEqual(q1['model_challenge_status'], 'passed')

    def test_both_stage_events_cover_analysis_code_even_after_disposition_reset(self):
        state = {'subproblems': {'Q1': record()}}
        # The coordinator must capture stages before applying any freshness profiles.
        affected_stages = ('primary', 'analysis')
        events = {'primary': PRIMARY, 'analysis': ANALYSIS}
        reports = [self.transition(state, events[stage]) for stage in affected_stages]
        q1 = state['subproblems']['Q1']
        self.assertTrue({'primary_code', 'analysis_code', 'solution_workbook',
                         'result_analysis_workbook', 'matlab_script', 'figure_bundle',
                         'framework'}.issubset(q1['stale_layers']))
        self.assertEqual(ST.merge_transition_reports(reports)['affected_questions'], ['Q1'])
        self.assertEqual(q1['human_model_approval_status'], 'approved')

    def test_ordinary_code_events_keep_their_original_narrow_impacts(self):
        for event, impacts in (('primary_code_changed', {'result'}), ('analysis_code_changed', set())):
            with self.subTest(event=event):
                state = {'subproblems': {'Q1': record(),
                         'Q2': record([dependency('Q1', 'data')]),
                         'Q3': record([dependency('Q1', 'parameter')])}}
                report = self.transition(state, event)
                self.assertEqual(set(report['transitions'][0]['emitted_impacts']), impacts)
                self.assertEqual(report['affected_questions'], ['Q1'])
                self.assertFalse(state['subproblems']['Q2']['artifacts_stale'])

    def test_legacy_and_unknown_dependencies_remain_conservative(self):
        for event in (PRIMARY, ANALYSIS):
            for kind in (None, 'unknown-kind'):
                with self.subTest(event=event, kind=kind):
                    state = {'subproblems': {'Q1': record(), 'Q2': record([dependency('Q1', kind)])}}
                    report = self.transition(state, event)
                    self.assertEqual(report['affected_questions'], ['Q1', 'Q2'])
                    self.assertEqual(state['subproblems']['Q2']['human_model_approval_status'], 'stale')
                    self.assertEqual(report['transitions'][1]['dependency_kind'], 'legacy_untyped')

    def test_typed_chains_and_diamond_keep_edge_provenance(self):
        state = {'subproblems': {
            'Q1': record(), 'Q2': record([dependency('Q1', 'data')]),
            'Q3': record([dependency('Q1', 'parameter')]),
            'Q4': record([dependency('Q2', 'result'), dependency('Q3', 'parameter')]),
            'Q5': record([dependency('Q4', 'result')]),
            'Q6': record([dependency('Q1', 'model')]),
        }}
        report = self.transition(state, PRIMARY)
        self.assertEqual(report['affected_questions'], ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        incoming_q4 = [row for row in report['transitions'] if row['question'] == 'Q4']
        self.assertEqual({row['source'] for row in incoming_q4}, {'Q2', 'Q3'})
        for q in state['subproblems'].values():
            self.assertEqual(q['human_model_approval_status'], 'approved')
        self.assertFalse(state['subproblems']['Q6']['artifacts_stale'])

    def test_cycles_report_and_terminate_without_repeated_edge_application(self):
        state = {'subproblems': {'Q1': record([dependency('Q2', 'parameter')]),
                                 'Q2': record([dependency('Q1', 'parameter')])}}
        report = self.transition(state, PRIMARY)
        self.assertEqual(report['dependency_cycles'], ['Q1 -> Q2 -> Q1'])
        self.assertEqual(report['affected_questions'], ['Q1', 'Q2'])
        self.assertEqual(len(report['transitions']), 3)

    def test_retirement_is_idempotent_and_order_deterministic(self):
        state = {'subproblems': {'Q3': record([dependency('Q1', 'result')]),
                                'Q1': record(), 'Q2': record([dependency('Q1', 'data')])}}
        reordered = {'subproblems': dict(reversed(list(deepcopy(state['subproblems']).items())))}
        for event in (PRIMARY, ANALYSIS):
            first = self.transition(state, event)
            second = self.transition(reordered, event)
            self.assertEqual(first, second)
            once = deepcopy(state)
            self.transition(state, event)
            self.assertEqual(state, once)

    def test_independent_affected_question_requires_its_own_explicit_event(self):
        state = {'subproblems': {'Q1': record(), 'Q2': record(), 'Q3': record()}}
        first = self.transition(state, PRIMARY, 'Q1')
        self.assertFalse(state['subproblems']['Q2']['artifacts_stale'])
        second = self.transition(state, PRIMARY, 'Q2')
        merged = ST.merge_transition_reports([first, second])
        self.assertEqual(merged['affected_questions'], ['Q1', 'Q2'])
        self.assertFalse(state['subproblems']['Q3']['artifacts_stale'])

    def test_freshness_events_do_not_select_policy_archive_or_rebind_evidence(self):
        state = {'execution': {'solver_backend': 'python', 'solver_backend_selection_reason': 'fixture'},
                 'subproblems': {'Q1': record()}}
        original_policy = deepcopy(state['execution'])
        original_binding = deepcopy(state['subproblems']['Q1']['solver_execution'])
        self.transition(state, PRIMARY); self.transition(state, ANALYSIS)
        self.assertEqual(state['execution'], original_policy)
        self.assertEqual(state['subproblems']['Q1']['solver_execution'], original_binding)
        self.assertNotIn('backend_history', state)
        self.assertNotIn('execution_authorized', state)

    def test_unknown_event_does_not_modify_the_state(self):
        state = {'subproblems': {'Q1': record()}}
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, 'unknown state transition event'):
            self.transition(state, 'backend_request_conflict')
        self.assertEqual(state, before)


if __name__ == '__main__':
    unittest.main()
