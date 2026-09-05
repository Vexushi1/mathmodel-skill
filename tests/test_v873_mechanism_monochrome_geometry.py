from __future__ import annotations

import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "hsk_generate_mechanism_drawio_v873", ROOT / "scripts/generate_mechanism_drawio.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = load_generator()


def base_spec(shape: str = "rect") -> dict:
    return {
        "spec_version": "1.0.0",
        "figure_id": "MF-Q1-873",
        "question_id": "Q1",
        "diagram_type": "object_relation",
        "core_question": "规则几何对象如何构成约束关系？",
        "core_conclusion": "对象几何与约束方向可由黑白线稿直接表达。",
        "framework_anchor": "模型论文框架.md#Q1-机理图",
        "backend": "drawio",
        "layout_mode": "explicit",
        "semantic_anchors": {
            "model": ["模型论文框架.md#Q1-模型"],
            "formulas": [],
            "constraints": ["C1"],
            "assumptions": [],
            "code": [],
            "result_evidence": [],
        },
        "canvas": {
            "width": 800,
            "height": 500,
            "orientation": "landscape",
            "target_use": "paper",
            "target_width_mm": 150,
        },
        "groups": [],
        "nodes": [
            {
                "id": "n1",
                "label": "对象 A",
                "semantic_role": "object",
                "symbol_refs": ["A"],
                "source_anchor": "模型论文框架.md#Q1-A",
                "group_id": None,
                "shape": shape,
                "emphasis": "primary",
                "geometry": {"x": 80, "y": 120, "width": 160, "height": 100},
            },
            {
                "id": "n2",
                "label": "边界 B",
                "semantic_role": "boundary",
                "symbol_refs": ["B"],
                "source_anchor": "模型论文框架.md#Q1-B",
                "group_id": None,
                "shape": "circle",
                "emphasis": "risk",
                "geometry": {"x": 480, "y": 120, "width": 120, "height": 120},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "relation_type": "constrains",
                "direction": "forward",
                "label": "约束",
                "source_anchor": "模型论文框架.md#C1",
                "formula_refs": [],
                "waypoints": [],
            }
        ],
        "artifact": {
            "spec_source": "figures/source/q1_geometry.mechanism.yaml",
            "editable_source": "figures/source/q1_geometry.drawio",
            "preview": None,
            "final_exports": [],
            "spec_sha256": None,
            "drawio_sha256": None,
            "preview_sha256": None,
            "validation_status": "pending",
            "visual_review_status": "pending",
        },
    }


class MechanismMonochromeGeometryTests(unittest.TestCase):
    def test_new_regular_geometry_shapes_are_supported(self):
        required = {"circle", "sphere", "triangle", "quadrilateral", "cylinder"}
        self.assertTrue(required.issubset(GENERATOR.SHAPES))
        for shape in sorted(required):
            with self.subTest(shape=shape):
                root = ET.fromstring(GENERATOR.generate_drawio(base_spec(shape)))
                node = next(cell for cell in root.iter("mxCell") if cell.attrib.get("id") == "n1")
                self.assertIn("strokeColor=", node.attrib["style"])

    def test_default_generator_has_no_semantic_blue_green_red_palette(self):
        xml_text = GENERATOR.generate_drawio(base_spec()).decode("utf-8")
        for forbidden in ("#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):
            self.assertNotIn(forbidden, xml_text)
        self.assertIn("fillColor=#FFFFFF", xml_text)
        self.assertIn("strokeColor=#111827", xml_text)
        self.assertIn("strokeColor=#1F2937", xml_text)

    def test_rule_geometry_maps_to_simple_drawio_primitives(self):
        expected_tokens = {
            "circle": "ellipse;aspect=fixed;",
            "sphere": "ellipse;aspect=fixed;",
            "triangle": "triangle;direction=north;",
            "quadrilateral": "shape=parallelogram;",
            "cylinder": "shape=cylinder3;",
        }
        for shape, token in expected_tokens.items():
            with self.subTest(shape=shape):
                root = ET.fromstring(GENERATOR.generate_drawio(base_spec(shape)))
                node = next(cell for cell in root.iter("mxCell") if cell.attrib.get("id") == "n1")
                self.assertIn(token, node.attrib["style"])

    def test_authority_and_implementation_reference_monochrome_first(self):
        authority = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        patterns = (ROOT / "templates/figure/mechanism_drawio_patterns.md").read_text(encoding="utf-8")
        qa = (ROOT / "templates/figure/mechanism_qa.md").read_text(encoding="utf-8")
        self.assertIn("monochrome-first", authority)
        self.assertIn("黑白线稿", authority)
        self.assertIn("规则几何", patterns)
        self.assertIn("黑白打印", qa)


if __name__ == "__main__":
    unittest.main()
