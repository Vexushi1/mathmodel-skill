from __future__ import annotations

import importlib.util
import itertools
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_resolver():
    spec = importlib.util.spec_from_file_location(
        "resolve_workflow_v931_budget", SCRIPTS / "resolve_workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TaskPackBudgetClosureV931Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = load_resolver()
        cls.router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        cls.taxonomy = yaml.safe_load(
            (ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8")
        )

    def test_router_budget_covers_every_taxonomy_valid_unique_pack_combination(self):
        max_structures = int(
            self.taxonomy["classification_contract"]["structures_max_items"]
        )
        structure_names = list(self.taxonomy["structures"])
        maximum = 0
        witness = None

        for objective, objective_spec in self.taxonomy["objectives"].items():
            for size in range(max_structures + 1):
                for structures in itertools.combinations(structure_names, size):
                    packs = {
                        objective_spec["legacy_pack"],
                        *(
                            self.taxonomy["structures"][name]["supplemental_pack"]
                            for name in structures
                        ),
                    }
                    if len(packs) > maximum:
                        maximum = len(packs)
                        witness = (objective, structures, sorted(packs))

        budget = int(self.router["classification_contract"]["task_pack_budget"])
        self.assertGreaterEqual(
            budget,
            maximum,
            f"Router task_pack_budget={budget} cannot represent legal classification {witness}",
        )
        self.assertEqual(maximum, 4)

    def test_valid_objective_plus_three_structures_resolves_all_four_unique_packs(self):
        plan = self.resolver.resolve_workflow(
            "model_selection",
            objective="optimization",
            structures=["spatial", "network", "stochastic"],
        )

        expected = [
            "packs/task/optimization.md",
            "packs/task/spatial.md",
            "packs/task/graph_network.md",
            "packs/task/simulation.md",
        ]
        for path in expected:
            self.assertIn(path, plan["packs"])
        positions = [plan["packs"].index(path) for path in expected]
        self.assertEqual(positions, sorted(positions))

        self.assertIn("modules/02_model_design.md", plan["modules"])
        self.assertTrue(plan["pause_for_model_approval"])
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance"],
        )

    def test_full_runtime_builds_reading_plan_for_four_pack_classification(self):
        from resolve_runtime import resolve_runtime

        plan = resolve_runtime(
            "model_selection",
            objective="optimization",
            structures=["spatial", "network", "stochastic"],
        )
        paths = {row["path"] for row in plan["reading_plan"]["read_now"]}
        for path in (
            "packs/task/optimization.md",
            "packs/task/spatial.md",
            "packs/task/graph_network.md",
            "packs/task/simulation.md",
        ):
            self.assertIn(path, paths)
        self.assertIn("modules/02_model_design.md", paths)
        self.assertEqual(plan["reading_plan"]["profile"], "full")
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")

    def test_duplicate_pack_mappings_are_deduplicated_before_budget_check(self):
        plan = self.resolver.resolve_workflow(
            "model_selection",
            objective="simulation",
            structures=["stochastic", "spatial", "network"],
        )
        self.assertEqual(plan["packs"].count("packs/task/simulation.md"), 1)
        self.assertIn("packs/task/spatial.md", plan["packs"])
        self.assertIn("packs/task/graph_network.md", plan["packs"])
        self.assertLessEqual(
            len([path for path in plan["packs"] if path.startswith("packs/task/")]),
            self.router["classification_contract"]["task_pack_budget"],
        )

    def test_structure_count_above_taxonomy_limit_still_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "at most 3 structures are allowed"):
            self.resolver.resolve_workflow(
                "model_selection",
                objective="optimization",
                structures=["spatial", "network", "stochastic", "scheduling"],
            )

    def test_resolver_budget_is_router_authoritative_and_required(self):
        self.assertEqual(self.resolver.classification_task_pack_budget(self.router), 4)
        with self.assertRaisesRegex(ValueError, "task_pack_budget"):
            self.resolver.classification_task_pack_budget({})
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.resolver.classification_task_pack_budget(
                {"classification_contract": {"task_pack_budget": True}}
            )


if __name__ == "__main__":
    unittest.main()
