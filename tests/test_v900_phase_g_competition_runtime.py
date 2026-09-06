from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_runtime():
    path = ROOT / "scripts/resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_phase_g", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load resolve_runtime.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["resolve_runtime_phase_g"] = module
    spec.loader.exec_module(module)
    return module


class PhaseGCompetitionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime()
        cls.profiles = yaml.safe_load(
            (ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8")
        )
        cls.golden = yaml.safe_load(
            (ROOT / "tests/fixtures/phase_g_cumcm_runtime_golden.yaml").read_text(encoding="utf-8")
        )

    def _projection(self, plan):
        return {
            "load_order": list(plan.get("load_order", [])),
            "contracts": list(plan.get("contracts", [])),
            "templates": list(plan.get("templates", [])),
            "writing_runtime": plan.get("writing_runtime"),
        }

    def test_cumcm_routes_match_pre_migration_golden(self):
        for intent, expected in self.golden["routes"].items():
            with self.subTest(intent=intent):
                kwargs = {"primary": "mechanism"} if intent == "full_workflow" else {}
                actual = self.runtime.resolve_runtime(intent, competition="CUMCM", **kwargs)
                self.assertEqual(self._projection(actual), expected)

    def test_cumcm_aliases_keep_canonical_runtime_output(self):
        expected = self.golden["routes"]["latex"]
        for token in ("CUMCM", "cumcm", "国赛"):
            with self.subTest(token=token):
                plan = self.runtime.resolve_runtime("latex", competition=token)
                self.assertEqual(self._projection(plan), expected)
                self.assertEqual(plan["writing_runtime"]["competition"], "CUMCM")

    def test_non_cumcm_profiles_keep_full_reasoning_fallback(self):
        for token in ("MCM", "ICM", "diangong", "电工杯", "certification cup"):
            with self.subTest(token=token):
                plan = self.runtime.resolve_runtime("latex", competition=token)
                self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
                self.assertNotIn("templates/latex/cumcm/hsk/template_manifest.yaml", plan["load_order"])
                self.assertNotEqual((plan.get("writing_runtime") or {}).get("mode"), "compact")

    def test_profiles_declare_runtime_modes(self):
        profiles = self.profiles["profiles"]
        self.assertEqual(profiles["cumcm"]["stable"]["writing_runtime"]["mode"], "template_first_progressive")
        for name in ("mcm_icm", "diangong", "certification_cup"):
            self.assertEqual(
                profiles[name]["stable"]["writing_runtime"]["mode"],
                "full_reasoning_fallback",
            )

    def test_missing_writing_runtime_profile_fails_closed(self):
        plan = {
            "intents": ["latex"],
            "competition": "Synthetic",
            "load_order": [
                "core/hsk_core_policy.md",
                "core/writing_reasoning_contract.yaml",
                "modules/05_writing/latex.md",
            ],
        }
        synthetic = {
            "profiles": {
                "synthetic": {"aliases": ["Synthetic"], "stable": {}}
            }
        }
        with self.assertRaisesRegex(ValueError, "lacks stable.writing_runtime"):
            self.runtime._apply_profile_writing_runtime(plan, profiles=synthetic)

    def test_resolver_has_no_cumcm_writing_constants(self):
        text = (ROOT / "scripts/resolve_runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("COMPACT_WRITING_COMPETITIONS", text)
        self.assertNotIn("CUMCM_WRITING_PACKAGE_INTENTS", text)
        self.assertIn("COMPETITION_PROFILES_PATH", text)

    def test_runtime_fingerprint_includes_competition_profiles(self):
        contract = yaml.safe_load(
            (ROOT / "core/runtime_assurance_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertIn(
            "config/competition_profiles.yaml",
            contract["authority_fingerprint"]["ordered_sources"],
        )


if __name__ == "__main__":
    unittest.main()
