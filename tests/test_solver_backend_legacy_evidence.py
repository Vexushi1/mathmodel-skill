"""Keep approved baseline exceptions narrower than arbitrary routing changes."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reading_plan_evidence import approved_solver_changes


class SolverBaselineExceptionTests(unittest.TestCase):
    def test_only_one_execution_authority_insertion_is_approved(self):
        old = {"load_order": ["first", "last"]}
        new = {"load_order": ["first", "core/user_execution_contract.yaml", "last"]}
        projected, changes = approved_solver_changes(old, new)
        self.assertEqual(projected, old)
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(new["load_order"]), 3)
        for values in (["last", "core/user_execution_contract.yaml", "first"],
                       ["first", "core/user_execution_contract.yaml", "extra", "last"],
                       ["first", "core/user_execution_contract.yaml", "core/user_execution_contract.yaml", "last"]):
            with self.subTest(values=values):
                projected, changes = approved_solver_changes(old, {"load_order": values})
                self.assertEqual(changes, [])
                self.assertNotEqual(projected, old)

    def test_fingerprint_exception_preserves_all_old_hashes_and_sources(self):
        old = {"assurance": {"authority_fingerprint": {"sources": [{"path": "original", "sha256": "old"}]}}}
        new = deepcopy(old)
        rows = new["assurance"]["authority_fingerprint"]["sources"]
        rows.extend({"path": path, "sha256": "current"} for path in (
            "core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/output_contract.yaml"))
        self.assertEqual(approved_solver_changes(old, new)[0], old)
        rows[0]["sha256"] = "unapproved drift"
        self.assertEqual(approved_solver_changes(old, new)[1], [])


if __name__ == "__main__":
    unittest.main()
