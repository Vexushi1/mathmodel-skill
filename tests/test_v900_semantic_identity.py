from __future__ import annotations

import importlib.util
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

SPEC = importlib.util.spec_from_file_location(
    "semantic_identity", ROOT / "scripts/semantic_identity.py"
)
SEMANTIC_IDENTITY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = SEMANTIC_IDENTITY
SPEC.loader.exec_module(SEMANTIC_IDENTITY)


def identity() -> dict:
    return {
        "schema_version": "1.0.0",
        "question": "Q1",
        "research_object": "城市配送车辆调度",
        "data_scope": [
            {"id": "D2", "source": "附件2", "role": "验证"},
            {"id": "D1", "source": "附件1", "role": "输入"},
        ],
        "variables": [
            {"id": "V2", "symbol": "y_j", "role": "state", "domain": "real"},
            {"id": "V1", "symbol": "x_i", "role": "decision", "domain": "binary"},
        ],
        "parameters": [
            {"id": "P1", "symbol": "c_i", "unit": "CNY"},
        ],
        "assumptions": [
            {"id": "A1", "statement": "需求在单个决策周期内保持给定"},
        ],
        "objective": {
            "sense": "minimize",
            "expression": "C(x)",
        },
        "constraints": [
            {"id": "C2", "expression": "sum_i x_i <= K", "role": "capacity"},
            {"id": "C1", "expression": "x_i in {0,1}", "role": "domain"},
        ],
        "preprocessing_decision": "question_local",
        "algorithm_semantics": {
            "model_family": "MILP",
            "solver_role": "exact_or_gap_bounded",
        },
        "dependencies": [],
        "extensions": {
            "stages": ["estimate", "optimize", "validate"],
        },
    }


def framework(identity_yaml: str, *, extra_prose: str = "模型说明A。") -> str:
    return f"""### Q1：第一问
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
{identity_yaml}```
<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->

{extra_prose}
#### 结果摘要
待求解。
"""


class TestV900SemanticIdentity(unittest.TestCase):
    def test_mapping_and_declared_set_order_do_not_change_identity_hash(self):
        left = identity()
        right = {
            key: deepcopy(left[key])
            for key in reversed(list(left.keys()))
        }
        right["variables"] = list(reversed(right["variables"]))
        right["constraints"] = list(reversed(right["constraints"]))
        right["data_scope"] = list(reversed(right["data_scope"]))

        self.assertEqual(
            SEMANTIC_IDENTITY.semantic_identity_hash(left),
            SEMANTIC_IDENTITY.semantic_identity_hash(right),
        )

    def test_order_sensitive_extension_list_changes_identity_hash(self):
        left = identity()
        right = deepcopy(left)
        right["extensions"]["stages"] = list(reversed(right["extensions"]["stages"]))
        self.assertNotEqual(
            SEMANTIC_IDENTITY.semantic_identity_hash(left),
            SEMANTIC_IDENTITY.semantic_identity_hash(right),
        )

    def test_objective_change_changes_identity_hash(self):
        left = identity()
        right = deepcopy(left)
        right["objective"]["sense"] = "maximize"
        self.assertNotEqual(
            SEMANTIC_IDENTITY.semantic_identity_hash(left),
            SEMANTIC_IDENTITY.semantic_identity_hash(right),
        )

    def test_prose_outside_identity_changes_text_hash_not_identity_hash(self):
        payload = identity()
        yaml_text = __import__("yaml").safe_dump(payload, allow_unicode=True, sort_keys=False)
        first = SEMANTIC_IDENTITY.inspect_question_semantics(
            framework(yaml_text, extra_prose="模型说明A。"), "Q1"
        )
        second = SEMANTIC_IDENTITY.inspect_question_semantics(
            framework(yaml_text, extra_prose="这里换一种措辞，但结构化模型语义没有变化。"), "Q1"
        )
        self.assertEqual(first["mode"], "semantic_identity_v1")
        self.assertEqual(first["semantic_identity_hash"], second["semantic_identity_hash"])
        self.assertNotEqual(first["semantic_text_hash"], second["semantic_text_hash"])

    def test_legacy_section_without_markers_remains_explicit_legacy_mode(self):
        section = """### Q1：第一问
#### 当前模型口径
- 目标：min f(x)
#### 结果摘要
待求解。
"""
        inspected = SEMANTIC_IDENTITY.inspect_question_semantics(section, "Q1")
        self.assertEqual(inspected["mode"], "legacy_text_hash")
        self.assertIsNone(inspected["semantic_identity_hash"])
        self.assertEqual(len(inspected["semantic_text_hash"]), 64)

    def test_partial_or_mismatched_markers_never_fall_back_to_legacy(self):
        section = """### Q1：第一问
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
question: Q1
```
#### 结果摘要
"""
        with self.assertRaises(SEMANTIC_IDENTITY.SemanticIdentityError):
            SEMANTIC_IDENTITY.inspect_question_semantics(section, "Q1")

    def test_placeholder_and_unknown_root_field_are_rejected(self):
        placeholder = identity()
        placeholder["research_object"] = "__FILL__"
        with self.assertRaises(SEMANTIC_IDENTITY.SemanticIdentityError):
            SEMANTIC_IDENTITY.semantic_identity_hash(placeholder)

        unknown = identity()
        unknown["typo_constraints"] = []
        with self.assertRaises(SEMANTIC_IDENTITY.SemanticIdentityError):
            SEMANTIC_IDENTITY.semantic_identity_hash(unknown)

    def test_duplicate_ids_and_question_mismatch_are_rejected(self):
        duplicate = identity()
        duplicate["variables"].append({"id": "V1", "symbol": "z"})
        with self.assertRaises(SEMANTIC_IDENTITY.SemanticIdentityError):
            SEMANTIC_IDENTITY.semantic_identity_hash(duplicate)

        payload = identity()
        yaml_text = __import__("yaml").safe_dump(payload, allow_unicode=True, sort_keys=False)
        q2_section = framework(yaml_text).replace("### Q1：", "### Q2：")
        with self.assertRaises(SEMANTIC_IDENTITY.SemanticIdentityError):
            SEMANTIC_IDENTITY.inspect_question_semantics(q2_section, "Q2")

    def test_dependency_order_is_set_like_but_dependency_content_is_semantic(self):
        left = identity()
        left["question"] = "Q3"
        left["dependencies"] = [
            {"question": "Q1", "kind": "data"},
            {"question": "Q2", "kind": "result", "selector": "recommended.alpha"},
        ]
        right = deepcopy(left)
        right["dependencies"] = list(reversed(right["dependencies"]))
        self.assertEqual(
            SEMANTIC_IDENTITY.semantic_identity_hash(left),
            SEMANTIC_IDENTITY.semantic_identity_hash(right),
        )
        right["dependencies"][0]["kind"] = "model"
        self.assertNotEqual(
            SEMANTIC_IDENTITY.semantic_identity_hash(left),
            SEMANTIC_IDENTITY.semantic_identity_hash(right),
        )


if __name__ == "__main__":
    unittest.main()
