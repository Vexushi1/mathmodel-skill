"""B2 Figure source observation must survive the full read-only audit path."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tests import test_b2b3b_figure_source as fixture
import claim_consumption
import claim_figure_source
from tests.test_model_code_conformance import save


class FigureSourceConsumptionIntegrationTests(unittest.TestCase):
    save_projection = fixture.FigureSourceTests.save_projection

    @classmethod
    def setUpClass(cls):
        fixture.FigureSourceTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.FigureSourceTests.tearDownClass.__func__(cls)

    def setUp(self):
        fixture.FigureSourceTests.setUp(self)

    def tearDown(self):
        fixture.FigureSourceTests.tearDown(self)

    def test_full_audit_reports_current_source_and_prior_approval_freshness(self):
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['b1_status'], 'evidence_checked', report)
        self.assertEqual(report['figure_source_checks'][0]['status'], 'current', report)
        identity = report['figure_identity_checks'][0]
        self.assertEqual(identity['identity_status'], 'matched', report)
        self.assertEqual(identity['source_qualification'], 'current', report)
        self.assertEqual(identity['approval_freshness'], 'current', report)
        self.assertEqual(identity['source_and_visual_semantics'], 'not_assessed', report)

    def test_changed_approved_bundle_is_visible_in_full_audit(self):
        (self.root / 'figures/q1_f01.png').write_bytes(b'replaced before audit')
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['figure_source_checks'][0]['status'], 'needs_review', report)
        self.assertEqual(report['figure_identity_checks'][0]['approval_freshness'], 'not_assessed', report)

    def test_artifacts_stale_cannot_report_original_approval_as_current(self):
        entry = self.state['subproblems']['Q1']
        entry['stale_layers'] = ['analysis_code']
        entry['artifacts_stale'] = True
        save(self.root, self.state)
        report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['figure_source_checks'][0]['approval_freshness'], 'not_assessed', report)

    def test_added_image_during_audit_blocks_return(self):
        original = claim_figure_source.recheck_source_discovery

        def add_image_then_recheck(root, state, checks):
            (self.root / '问题一求解/extra.png').write_bytes(b'new image')
            return original(root, state, checks)

        with patch.object(claim_figure_source, 'recheck_source_discovery',
                          side_effect=add_image_then_recheck):
            report = claim_consumption.inspect_project(self.root)
        self.assertEqual(report['status'], 'blocked', report)
        self.assertTrue(any('Figure source discovery changed' in item
                            for item in report['errors']), report)


if __name__ == '__main__':
    unittest.main()
