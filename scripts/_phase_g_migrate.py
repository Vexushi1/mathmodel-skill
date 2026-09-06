#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def load_runtime_module(name: str):
    path = SCRIPTS / "resolve_runtime.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load resolve_runtime.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def capture_cumcm_golden() -> dict[str, Any]:
    runtime = load_runtime_module("phase_g_runtime_before")
    payload: dict[str, Any] = {"schema_version": "1.0.0", "competition": "CUMCM", "routes": {}}
    for intent in ("latex", "review", "full_submission", "full_workflow"):
        plan = runtime.resolve_runtime(intent, competition="CUMCM")
        payload["routes"][intent] = {
            "load_order": list(plan.get("load_order", [])),
            "contracts": list(plan.get("contracts", [])),
            "templates": list(plan.get("templates", [])),
            "writing_runtime": plan.get("writing_runtime"),
        }
    return payload


def patch_profiles() -> None:
    path = ROOT / "config" / "competition_profiles.yaml"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "      language: zh-CN\n    edition_rules:\n",
        "      language: zh-CN\n"
        "      writing_runtime:\n"
        "        mode: template_first_progressive\n"
        "        competition_label: CUMCM\n"
        "        template_manifest: templates/latex/cumcm/hsk/template_manifest.yaml\n"
        "        supported_intents: [latex, review, full_submission, full_workflow]\n"
        "        compact_intents: [latex]\n"
        "    edition_rules:\n",
        "cumcm writing_runtime",
    )
    text = replace_once(
        text,
        "      language: en\n    edition_rules:\n",
        "      language: en\n"
        "      writing_runtime:\n"
        "        mode: full_reasoning_fallback\n"
        "    edition_rules:\n",
        "mcm writing_runtime",
    )
    # Two remaining zh-CN profiles are both explicit full-reasoning fallbacks.
    marker = "      language: zh-CN\n    edition_rules:\n"
    if text.count(marker) != 2:
        raise RuntimeError(f"fallback profiles: expected two remaining zh-CN markers, found {text.count(marker)}")
    text = text.replace(
        marker,
        "      language: zh-CN\n"
        "      writing_runtime:\n"
        "        mode: full_reasoning_fallback\n"
        "    edition_rules:\n",
    )
    write(path, text)


def patch_resolver() -> None:
    path = SCRIPTS / "resolve_runtime.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'WRITING_RUNTIME_PATH = ROOT / "core" / "writing_runtime_contract.yaml"\n\n# v8 keeps the full reasoning authority available, but ordinary CUMCM LaTeX writing\n# uses the compact Template-First package. Other competitions remain on the full\n# semantic fallback until they own a competition-specific Template Manifest.\nCOMPACT_WRITING_INTENTS = {"latex"}\nCOMPACT_WRITING_COMPETITIONS = {"cumcm"}\nCUMCM_WRITING_PACKAGE_INTENTS = {"latex", "review", "full_submission", "full_workflow"}\n',
        'WRITING_RUNTIME_PATH = ROOT / "core" / "writing_runtime_contract.yaml"\nCOMPETITION_PROFILES_PATH = ROOT / "config" / "competition_profiles.yaml"\n',
        "resolver constants",
    )
    start = text.index("def _apply_v8_writing_runtime(")
    end = text.index("\ndef resolve_runtime(", start)
    replacement = '''def _resolve_competition_profile(\n    token: str, profiles: dict[str, Any]\n) -> tuple[str, dict[str, Any], dict[str, Any]]:\n    normalized = token.strip().lower()\n    for name, config in (profiles.get("profiles", {}) or {}).items():\n        aliases = [name, *(config.get("aliases", []) or [])]\n        if normalized not in {str(item).strip().lower() for item in aliases}:\n            continue\n        stable = config.get("stable", {}) or {}\n        runtime_profile = stable.get("writing_runtime")\n        if not isinstance(runtime_profile, dict):\n            raise ValueError(\n                f"competition profile {name} lacks stable.writing_runtime; "\n                "declare template_first_progressive or full_reasoning_fallback"\n            )\n        return str(name), config, runtime_profile\n    raise ValueError(f"unknown competition profile for writing runtime: {token}")\n\n\ndef _apply_profile_writing_runtime(\n    plan: dict[str, Any], *, profiles: dict[str, Any] | None = None\n) -> dict[str, Any]:\n    """Apply competition writing-runtime policy without competition-specific Python branches.\n\n    Competition profiles select whether a route uses Template-First progressive writing or\n    retains the full reasoning authority. The writing runtime contract still owns the common\n    writing capabilities and fallback semantics; this function only assembles the resources\n    declared by the active competition profile.\n    """\n    intents = set(str(item) for item in plan.get("intents", []))\n    competition = str(plan.get("competition") or "").strip()\n    if not intents or not competition:\n        return plan\n\n    profile_payload = profiles if profiles is not None else load_yaml(COMPETITION_PROFILES_PATH)\n    profile_name, _profile, runtime_profile = _resolve_competition_profile(\n        competition, profile_payload\n    )\n    mode = str(runtime_profile.get("mode") or "").strip()\n    if mode == "full_reasoning_fallback":\n        return plan\n    if mode != "template_first_progressive":\n        raise ValueError(\n            f"competition profile {profile_name} has unsupported writing_runtime.mode: {mode!r}"\n        )\n\n    supported = {str(item) for item in runtime_profile.get("supported_intents", [])}\n    compact_intents = {str(item) for item in runtime_profile.get("compact_intents", [])}\n    if not supported:\n        raise ValueError(f"competition profile {profile_name} has no supported writing intents")\n    if not compact_intents.issubset(supported):\n        raise ValueError(\n            f"competition profile {profile_name} compact_intents must be a subset of supported_intents"\n        )\n    if not intents.intersection(supported):\n        return plan\n\n    runtime = load_yaml(WRITING_RUNTIME_PATH)\n    writing_module = runtime.get("writing_module", {}) or {}\n    adapter = str(writing_module.get("latex_adapter") or "")\n    load_order = list(plan.get("load_order", []))\n    if not adapter or adapter not in load_order:\n        return plan\n\n    template_manifest = str(runtime_profile.get("template_manifest") or "").strip()\n    if not template_manifest:\n        raise ValueError(\n            f"competition profile {profile_name} template_first_progressive mode requires template_manifest"\n        )\n    if not (ROOT / template_manifest).is_file():\n        raise ValueError(\n            f"competition profile {profile_name} template manifest does not exist: {template_manifest}"\n        )\n\n    old_authority = str(\n        (runtime.get("full_authority_fallback", {}) or {}).get(\n            "authority", "core/writing_reasoning_contract.yaml"\n        )\n    )\n    runtime_order = _unique(runtime.get("ordinary_writing_resource_order", []))\n    default_policy = "core/hsk_core_policy.md"\n    if default_policy in runtime_order:\n        runtime_order.remove(default_policy)\n\n    canonical_manifest = str(\n        (runtime.get("canonical_template", {}) or {}).get("manifest") or ""\n    )\n    if canonical_manifest and canonical_manifest in runtime_order:\n        runtime_order = [\n            template_manifest if item == canonical_manifest else item for item in runtime_order\n        ]\n    elif template_manifest not in runtime_order:\n        runtime_order.append(template_manifest)\n    runtime_order = _unique(runtime_order)\n\n    compact = intents.issubset(compact_intents)\n    managed = set(runtime_order)\n    if compact:\n        managed.add(old_authority)\n    load_order = [item for item in load_order if item not in managed]\n    insertion_point = load_order.index(default_policy) + 1 if default_policy in load_order else 0\n    load_order[insertion_point:insertion_point] = runtime_order\n    load_order = _unique(load_order)\n\n    plan["load_order"] = load_order\n    plan["contracts"] = [item for item in load_order if item.startswith("core/")]\n    plan["templates"] = [item for item in load_order if item.startswith("templates/")]\n    plan["writing_runtime"] = {\n        "mode": "compact" if compact else "full_authority",\n        "execution_mode": "template_first_progressive_authoring",\n        "competition": str(runtime_profile.get("competition_label") or profile_name),\n        "contract": "core/writing_runtime_contract.yaml",\n        "protocol": str(writing_module.get("protocol") or "modules/05_writing/paper_writing_protocol.md"),\n        "template_manifest": template_manifest,\n        "resource_order_semantics": runtime.get("template_first_progressive_authoring", {}).get(\n            "resource_order_semantics"\n        ),\n        "initial_read_order": list(\n            runtime.get("template_first_progressive_authoring", {}).get("initial_read_order", [])\n        ),\n        "authoring_sequence": list(\n            runtime.get("template_first_progressive_authoring", {}).get("stages", [])\n        ),\n        "full_reasoning_authority_preloaded": old_authority in load_order,\n        "full_reasoning_authority_fallback": old_authority,\n        "fallback_triggers": list(\n            runtime.get("semantic_capabilities", {}).get(\n                "load_full_reasoning_authority_when_any", []\n            )\n        ),\n    }\n    return plan\n\n'''
    text = text[:start] + replacement + text[end + 1 :]
    text = replace_once(
        text,
        "    plan = _apply_v8_writing_runtime(plan)\n",
        "    plan = _apply_profile_writing_runtime(plan)\n",
        "resolver apply call",
    )
    write(path, text)


def patch_runtime_assurance_contract() -> None:
    path = ROOT / "core/runtime_assurance_contract.yaml"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  - core/module_manifest.yaml\n  - core/runtime_assurance_contract.yaml\n",
        "  - core/module_manifest.yaml\n  - config/competition_profiles.yaml\n  - core/runtime_assurance_contract.yaml\n",
        "runtime fingerprint competition profile",
    )
    write(path, text)


def patch_lint() -> None:
    path = SCRIPTS / "lint_skill_checks.py"
    text = path.read_text(encoding="utf-8")
    anchor = "def check_templates(errors: list[str]) -> None:\n"
    addition = '''def check_competition_writing_runtime(errors: list[str]) -> None:\n    payload = load_structured(ROOT / "config/competition_profiles.yaml") or {}\n    allowed_modes = {"template_first_progressive", "full_reasoning_fallback"}\n    for name, profile in (payload.get("profiles", {}) or {}).items():\n        stable = (profile or {}).get("stable", {}) or {}\n        runtime = stable.get("writing_runtime")\n        if not isinstance(runtime, dict):\n            errors.append(f"competition profile {name} must declare stable.writing_runtime")\n            continue\n        mode = runtime.get("mode")\n        if mode not in allowed_modes:\n            errors.append(f"competition profile {name} has unsupported writing_runtime mode: {mode!r}")\n            continue\n        if mode == "template_first_progressive":\n            manifest = str(runtime.get("template_manifest") or "")\n            supported = [str(item) for item in runtime.get("supported_intents", [])]\n            compact = [str(item) for item in runtime.get("compact_intents", [])]\n            if not manifest:\n                errors.append(f"competition profile {name} Template-First runtime lacks template_manifest")\n            elif not (ROOT / manifest).is_file():\n                errors.append(f"competition profile {name} Template-First manifest is missing: {manifest}")\n            if not supported:\n                errors.append(f"competition profile {name} Template-First runtime lacks supported_intents")\n            if not set(compact).issubset(set(supported)):\n                errors.append(f"competition profile {name} compact_intents must be a subset of supported_intents")\n\n    resolver = read_text(ROOT / "scripts/resolve_runtime.py")\n    for forbidden in ("COMPACT_WRITING_COMPETITIONS", "CUMCM_WRITING_PACKAGE_INTENTS"):\n        if forbidden in resolver:\n            errors.append(f"runtime resolver must not retain competition-specific writing constant: {forbidden}")\n    for required in ("COMPETITION_PROFILES_PATH", "_apply_profile_writing_runtime", "full_reasoning_fallback"):\n        if required not in resolver:\n            errors.append(f"runtime resolver lacks profile-driven writing-runtime token: {required}")\n\n\n'''
    text = replace_once(text, anchor, addition + anchor, "lint competition runtime insertion")
    # Ensure the new check is invoked from the main lint sequence.
    call_anchor = "    check_templates(errors)\n"
    text = replace_once(
        text,
        call_anchor,
        "    check_competition_writing_runtime(errors)\n" + call_anchor,
        "lint competition runtime call",
    )
    write(path, text)


def write_golden_and_tests(golden: dict[str, Any]) -> None:
    fixture = ROOT / "tests/fixtures/phase_g_cumcm_runtime_golden.yaml"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(yaml.safe_dump(golden, allow_unicode=True, sort_keys=False), encoding="utf-8")

    test_path = ROOT / "tests/test_v900_phase_g_competition_runtime.py"
    test_path.write_text('''from __future__ import annotations\n\nimport importlib.util\nimport sys\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\nSCRIPTS = str(ROOT / "scripts")\nif SCRIPTS not in sys.path:\n    sys.path.insert(0, SCRIPTS)\n\n\ndef load_runtime():\n    path = ROOT / "scripts/resolve_runtime.py"\n    spec = importlib.util.spec_from_file_location("resolve_runtime_phase_g", path)\n    if spec is None or spec.loader is None:\n        raise RuntimeError("cannot load resolve_runtime.py")\n    module = importlib.util.module_from_spec(spec)\n    sys.modules["resolve_runtime_phase_g"] = module\n    spec.loader.exec_module(module)\n    return module\n\n\nclass PhaseGCompetitionRuntimeTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.runtime = load_runtime()\n        cls.profiles = yaml.safe_load(\n            (ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8")\n        )\n        cls.golden = yaml.safe_load(\n            (ROOT / "tests/fixtures/phase_g_cumcm_runtime_golden.yaml").read_text(encoding="utf-8")\n        )\n\n    def _projection(self, plan):\n        return {\n            "load_order": list(plan.get("load_order", [])),\n            "contracts": list(plan.get("contracts", [])),\n            "templates": list(plan.get("templates", [])),\n            "writing_runtime": plan.get("writing_runtime"),\n        }\n\n    def test_cumcm_routes_match_pre_migration_golden(self):\n        for intent, expected in self.golden["routes"].items():\n            with self.subTest(intent=intent):\n                actual = self.runtime.resolve_runtime(intent, competition="CUMCM")\n                self.assertEqual(self._projection(actual), expected)\n\n    def test_cumcm_aliases_keep_canonical_runtime_output(self):\n        expected = self.golden["routes"]["latex"]\n        for token in ("CUMCM", "cumcm", "国赛"):\n            with self.subTest(token=token):\n                plan = self.runtime.resolve_runtime("latex", competition=token)\n                self.assertEqual(self._projection(plan), expected)\n                self.assertEqual(plan["writing_runtime"]["competition"], "CUMCM")\n\n    def test_non_cumcm_profiles_keep_full_reasoning_fallback(self):\n        for token in ("MCM", "ICM", "diangong", "电工杯", "certification cup"):\n            with self.subTest(token=token):\n                plan = self.runtime.resolve_runtime("latex", competition=token)\n                self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])\n                self.assertNotIn("templates/latex/cumcm/hsk/template_manifest.yaml", plan["load_order"])\n                self.assertNotEqual((plan.get("writing_runtime") or {}).get("mode"), "compact")\n\n    def test_profiles_declare_runtime_modes(self):\n        profiles = self.profiles["profiles"]\n        self.assertEqual(profiles["cumcm"]["stable"]["writing_runtime"]["mode"], "template_first_progressive")\n        for name in ("mcm_icm", "diangong", "certification_cup"):\n            self.assertEqual(\n                profiles[name]["stable"]["writing_runtime"]["mode"],\n                "full_reasoning_fallback",\n            )\n\n    def test_missing_writing_runtime_profile_fails_closed(self):\n        plan = {\n            "intents": ["latex"],\n            "competition": "Synthetic",\n            "load_order": [\n                "core/hsk_core_policy.md",\n                "core/writing_reasoning_contract.yaml",\n                "modules/05_writing/latex.md",\n            ],\n        }\n        synthetic = {\n            "profiles": {\n                "synthetic": {"aliases": ["Synthetic"], "stable": {}}\n            }\n        }\n        with self.assertRaisesRegex(ValueError, "lacks stable.writing_runtime"):\n            self.runtime._apply_profile_writing_runtime(plan, profiles=synthetic)\n\n    def test_resolver_has_no_cumcm_writing_constants(self):\n        text = (ROOT / "scripts/resolve_runtime.py").read_text(encoding="utf-8")\n        self.assertNotIn("COMPACT_WRITING_COMPETITIONS", text)\n        self.assertNotIn("CUMCM_WRITING_PACKAGE_INTENTS", text)\n        self.assertIn("COMPETITION_PROFILES_PATH", text)\n\n    def test_runtime_fingerprint_includes_competition_profiles(self):\n        contract = yaml.safe_load(\n            (ROOT / "core/runtime_assurance_contract.yaml").read_text(encoding="utf-8")\n        )\n        self.assertIn(\n            "config/competition_profiles.yaml",\n            contract["authority_fingerprint"]["ordered_sources"],\n        )\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")


def main() -> int:
    golden = capture_cumcm_golden()
    patch_profiles()
    patch_resolver()
    patch_runtime_assurance_contract()
    patch_lint()
    write_golden_and_tests(golden)
    print("Phase G deterministic migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
