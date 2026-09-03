from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = load_script("hsk_generate_mechanism_drawio", "scripts/generate_mechanism_drawio.py")
VALIDATOR = load_script("hsk_validate_drawio_figure", "scripts/validate_drawio_figure.py")


def base_spec(*, layout_mode: str = "explicit") -> dict:
    nodes = [
        {
            "id": "n_target",
            "label": "观测目标 T",
            "semantic_role": "object",
            "symbol_refs": ["T"],
            "source_anchor": "模型论文框架.md#Q1-对象",
            "group_id": None,
            "shape": "rounded_rect",
            "emphasis": "primary",
            "geometry": {"x": 80, "y": 120, "width": 180, "height": 70},
        },
        {
            "id": "n_boundary",
            "label": "可见边界 g(T)=0",
            "semantic_role": "boundary",
            "symbol_refs": ["g(T)"],
            "source_anchor": "模型论文框架.md#式-6",
            "group_id": None,
            "shape": "diamond",
            "emphasis": "risk",
            "geometry": {"x": 420, "y": 120, "width": 190, "height": 90},
        },
        {
            "id": "n_state",
            "label": "临界可见状态",
            "semantic_role": "state",
            "symbol_refs": ["z=1"],
            "source_anchor": "模型论文框架.md#Q1-状态",
            "group_id": None,
            "shape": "rounded_rect",
            "emphasis": "secondary",
            "geometry": {"x": 750, "y": 120, "width": 170, "height": 70},
        },
    ]
    edges = [
        {
            "id": "e_constraint",
            "source": "n_target",
            "target": "n_boundary",
            "relation_type": "constrains",
            "direction": "forward",
            "label": "遮蔽约束",
            "source_anchor": "模型论文框架.md#式-6",
            "formula_refs": ["F6"],
            "waypoints": [],
        },
        {
            "id": "e_switch",
            "source": "n_boundary",
            "target": "n_state",
            "relation_type": "switches_to",
            "direction": "forward",
            "label": "越过临界值",
            "source_anchor": "模型论文框架.md#Q1-判定条件",
            "formula_refs": ["F7"],
            "waypoints": [],
        },
    ]
    if layout_mode != "explicit":
        for node in nodes:
            node.pop("geometry")
    return {
        "spec_version": "1.0.0",
        "figure_id": "MF-Q1-01",
        "question_id": "Q1",
        "diagram_type": "critical_state",
        "core_question": "遮蔽约束如何决定目标的临界可见状态？",
        "core_conclusion": "边界函数变号触发可见状态切换。",
        "framework_anchor": "模型论文框架.md#Q1-机理图",
        "backend": "drawio",
        "layout_mode": layout_mode,
        "semantic_anchors": {
            "model": ["模型论文框架.md#Q1-模型"],
            "formulas": ["F6", "F7"],
            "constraints": ["C1"],
            "assumptions": ["A2"],
            "code": ["问题一求解.py:is_visible"],
            "result_evidence": [],
        },
        "canvas": {
            "width": 1000,
            "height": 700,
            "orientation": "landscape",
            "target_use": "paper",
            "target_width_mm": 150,
        },
        "groups": [],
        "nodes": nodes,
        "edges": edges,
        "artifact": {
            "spec_source": "figures/source/q1_occlusion.mechanism.yaml",
            "editable_source": "figures/source/q1_occlusion.drawio",
            "preview": None,
            "final_exports": ["figures/q1_occlusion.pdf", "figures/q1_occlusion.svg"],
            "spec_sha256": None,
            "drawio_sha256": None,
            "preview_sha256": None,
            "validation_status": "pending",
            "visual_review_status": "pending",
        },
    }


def write_spec(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


class MechanismSpecTests(unittest.TestCase):
    def test_template_is_problem_specific_and_machine_readable(self):
        path = ROOT / "templates/figure/mechanism_drawio_spec.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["spec_version"], "1.0.0")
        self.assertEqual(payload["backend"], "drawio")
        self.assertEqual(payload["nodes"], [])
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)
        self.assertNotIn("输入", path.read_text(encoding="utf-8"))
        self.assertNotIn("输出", path.read_text(encoding="utf-8"))
        self.assertNotIn("遮蔽", path.read_text(encoding="utf-8"))

    def test_all_supported_layout_modes_generate_valid_xml(self):
        for layout_mode in ("explicit", "layered_lr", "layered_tb"):
            with self.subTest(layout_mode=layout_mode):
                xml_bytes = GENERATOR.generate_drawio(base_spec(layout_mode=layout_mode))
                root = ET.fromstring(xml_bytes)
                self.assertEqual(root.tag, "mxfile")
                self.assertEqual(len(root.findall("diagram/mxGraphModel")), 1)

    def test_all_supported_diagram_types_are_expressible(self):
        for diagram_type in sorted(GENERATOR.DIAGRAM_TYPES):
            with self.subTest(diagram_type=diagram_type):
                payload = base_spec()
                payload["diagram_type"] = diagram_type
                self.assertTrue(GENERATOR.generate_drawio(payload).startswith(b"<?xml"))

    def test_node_order_does_not_change_output(self):
        first = base_spec()
        second = copy.deepcopy(first)
        second["nodes"].reverse()
        second["edges"].reverse()
        self.assertEqual(GENERATOR.generate_drawio(first), GENERATOR.generate_drawio(second))

    def test_chinese_and_formula_labels_round_trip(self):
        xml_bytes = GENERATOR.generate_drawio(base_spec())
        root = ET.fromstring(xml_bytes)
        cells = {cell.attrib["id"]: cell for cell in root.iter("mxCell")}
        self.assertEqual(cells["n_boundary"].attrib["value"], "可见边界 g(T)=0")
        self.assertEqual(cells["e_constraint"].attrib["hskFormulaRefs"], "F6")

    def test_invalid_spec_cases_fail_closed(self):
        cases = []
        duplicate = base_spec()
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        cases.append(duplicate)
        bad_enum = base_spec()
        bad_enum["diagram_type"] = "generic_pipeline"
        cases.append(bad_enum)
        missing_anchor = base_spec()
        missing_anchor["nodes"][0]["source_anchor"] = ""
        cases.append(missing_anchor)
        bad_endpoint = base_spec()
        bad_endpoint["edges"][0]["target"] = "missing"
        cases.append(bad_endpoint)
        custom_without_label = base_spec()
        custom_without_label["edges"][0]["relation_type"] = "custom"
        custom_without_label["edges"][0]["label"] = ""
        cases.append(custom_without_label)
        negative_size = base_spec()
        negative_size["nodes"][0]["geometry"]["width"] = -1
        cases.append(negative_size)
        for payload in cases:
            with self.subTest(case=len(cases)):
                with self.assertRaises(GENERATOR.SpecError):
                    GENERATOR.validate_spec(payload)

    def test_declared_spec_hash_uses_non_circular_normalization(self):
        payload = base_spec()
        expected = GENERATOR.canonical_spec_sha256(payload)
        payload["artifact"]["spec_sha256"] = expected
        GENERATOR.validate_spec(payload)
        payload["core_conclusion"] = "被篡改的结论"
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)


class GeneratorCliTests(unittest.TestCase):
    def test_check_mode_validates_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            output = root / "figure.drawio"
            write_spec(spec_path, base_spec())
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/generate_mechanism_drawio.py"), "--spec", str(spec_path), "--output", str(output), "--check"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(output.exists())

    def test_generate_cli_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            first = root / "first.drawio"
            second = root / "second.drawio"
            write_spec(spec_path, base_spec())
            for output in (first, second):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/generate_mechanism_drawio.py"), "--spec", str(spec_path), "--output", str(output)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            text = first.read_text(encoding="utf-8")
            for forbidden in ("http://", "https://", "data:image", "javascript:"):
                self.assertNotIn(forbidden, text.lower())


class DrawioValidatorTests(unittest.TestCase):
    def validate(self, payload: dict) -> list:
        xml_bytes = GENERATOR.generate_drawio(payload)
        return VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload)

    def test_clean_generated_diagram_has_no_blocking_findings(self):
        findings = self.validate(base_spec())
        self.assertFalse([item for item in findings if item.severity == "blocking"])
        self.assertTrue(any(item.code == "preview_not_reviewed" for item in findings))

    def test_group_container_is_not_misclassified_as_entity_overlap(self):
        payload = base_spec()
        payload["groups"] = [{
            "id": "g_observation",
            "label": "观测域",
            "source_anchor": "模型论文框架.md#Q1-对象域",
            "geometry": {"x": 50, "y": 75, "width": 590, "height": 180},
        }]
        payload["nodes"][0]["group_id"] = "g_observation"
        payload["nodes"][1]["group_id"] = "g_observation"
        findings = self.validate(payload)
        self.assertFalse(any(item.code == "entity_overlap" for item in findings))

    def test_overlap_is_blocking(self):
        payload = base_spec()
        payload["nodes"][1]["geometry"] = copy.deepcopy(payload["nodes"][0]["geometry"])
        findings = self.validate(payload)
        self.assertTrue(any(item.code == "entity_overlap" and item.severity == "blocking" for item in findings))

    def test_out_of_bounds_is_rejected_by_spec_validation(self):
        payload = base_spec()
        payload["nodes"][2]["geometry"]["x"] = 950
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)

    def test_external_resource_is_blocking(self):
        xml_bytes = GENERATOR.generate_drawio(base_spec()).replace(
            b"rounded=1;",
            b"rounded=1;image=https://example.invalid/a.svg;",
            1,
        )
        findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=base_spec())
        self.assertTrue(any(item.code == "external_resource" for item in findings))

    def test_missing_spec_cell_is_blocking(self):
        root = ET.fromstring(GENERATOR.generate_drawio(base_spec()))
        target = next(cell for cell in root.iter("mxCell") if cell.attrib.get("id") == "n_state")
        parent = next(parent for parent in root.iter() if target in list(parent))
        parent.remove(target)
        findings = VALIDATOR.validate_drawio_bytes(ET.tostring(root, encoding="utf-8"), spec=base_spec())
        self.assertTrue(any(item.code == "spec_cell_missing" for item in findings))

    def test_explicit_connector_through_unrelated_entity_is_blocking(self):
        payload = base_spec()
        payload["edges"].append({
            "id": "e_direct",
            "source": "n_target",
            "target": "n_state",
            "relation_type": "feedback",
            "direction": "forward",
            "label": "状态反馈",
            "source_anchor": "模型论文框架.md#Q1-反馈",
            "formula_refs": [],
            "waypoints": [{"x": 500, "y": 155}],
        })
        findings = self.validate(payload)
        self.assertTrue(any(item.code == "connector_crosses_entity" for item in findings))

    def test_approved_status_requires_preview_and_hash(self):
        payload = base_spec()
        payload["artifact"]["validation_status"] = "passed"
        payload["artifact"]["visual_review_status"] = "approved_for_paper"
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)

    def test_json_cli_and_strict_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            drawio_path = root / "figure.drawio"
            payload = base_spec()
            write_spec(spec_path, payload)
            drawio_path.write_bytes(GENERATOR.generate_drawio(payload))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_drawio_figure.py"), str(drawio_path), "--spec", str(spec_path), "--json", "--strict"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["claim"], "structure_and_geometry_only")
            self.assertGreaterEqual(report["counts"]["review_required"], 1)

    def test_current_preview_and_manual_approval_can_close_the_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source_dir = project / "figures/source"
            preview_dir = project / "figures/preview"
            source_dir.mkdir(parents=True)
            preview_dir.mkdir(parents=True)
            payload = base_spec()
            xml_bytes = GENERATOR.generate_drawio(payload)
            preview_bytes = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
            (preview_dir / "q1_occlusion.svg").write_bytes(preview_bytes)
            payload["artifact"].update({
                "preview": "figures/preview/q1_occlusion.svg",
                "spec_sha256": GENERATOR.canonical_spec_sha256(payload),
                "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
                "preview_sha256": hashlib.sha256(preview_bytes).hexdigest(),
                "validation_status": "passed",
                "visual_review_status": "approved_for_paper",
            })
            spec_path = source_dir / "q1_occlusion.mechanism.yaml"
            write_spec(spec_path, payload)
            self.assertEqual(GENERATOR.generate_drawio(payload), xml_bytes)
            findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload, spec_path=spec_path)
            self.assertEqual(findings, [])

    def test_fake_preview_surface_cannot_close_the_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source_dir = project / "figures/source"
            preview_dir = project / "figures/preview"
            source_dir.mkdir(parents=True)
            preview_dir.mkdir(parents=True)
            payload = base_spec()
            xml_bytes = GENERATOR.generate_drawio(payload)
            preview_bytes = b"not-a-png"
            (preview_dir / "q1_occlusion.png").write_bytes(preview_bytes)
            payload["artifact"].update({
                "preview": "figures/preview/q1_occlusion.png",
                "spec_sha256": GENERATOR.canonical_spec_sha256(payload),
                "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
                "preview_sha256": hashlib.sha256(preview_bytes).hexdigest(),
                "validation_status": "passed",
                "visual_review_status": "approved_for_paper",
            })
            spec_path = source_dir / "q1_occlusion.mechanism.yaml"
            write_spec(spec_path, payload)
            findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload, spec_path=spec_path)
            self.assertTrue(any(item.code == "preview_format_invalid" for item in findings))


class ContractAndDriftTests(unittest.TestCase):
    PROTECTED = {
        "core/model_approval_contract.yaml": "7d97255dde9cf780755bab896964e905066bf4b8",
        "core/numerical_verification_contract.yaml": "b901923edf38112cbc922f51d1157265fe1931bd",
        "core/workbook_schema.yaml": "2422bbfa8cb3fad3b5b04c12de21c954ec8b3723",
        "core/project_state.schema.yaml": "fa12de39d7bbdc2e014b2912a186834b941b28d4",
        "core/writing_reasoning_contract.yaml": "adb962b3b764c08f78fdb002b97401adde693856",
        "modules/03_solve_validate.md": "f49480d96e6a491255010868e409b2d64d620f5e",
        "modules/03_result_analysis.md": "f43d21dc99d71e6b19baeec7af66cbf334da13a7",
        "modules/05_writing/paper_writing_protocol.md": "5404b1dc891227249644b040c40482bd6065b81a",
        "modules/05_writing/ai_cleanup.md": "c5200f4f1513c6770952284ac2d49e3db7bef273",
        "modules/06_review_delivery.md": "845350d958628e69d8d779f7d92542756a6da8e6",
        "config/competition_profiles.yaml": "fcddec42a30ad4d4bc760dc8322cc13a998a6ebd",
        "scripts/validate_semantic_governance.py": "481199d1d0b541eacd0ddd3b3794c301aac6e690",
        "scripts/validate_submission_package.py": "47bd01db5f45dd8c902418be62f494419a03c676",
        "templates/matlab/q1_plot.m": "b9e67798051b1a130d2df11bca20e3976de0a6c2",
        "templates/matlab/draw_mechanism_structure.m": "65ba4a3b3462a565f86880c49af0959edd21f9a4",
        "templates/figure/chart_selection.md": "ba293a44f3ce4e0162c22e224ba33fd0ec94c048",
        "templates/figure/figure_enhancement_patterns.md": "d2fb8bc7b1d61556b9453682c4102b0e08ea246a",
        "scripts/validate_code_delivery.py": "d7b2593a72d6ab4f9a297e46f77f1922c405c128",
    }

    def test_protected_authorities_have_not_drifted(self):
        for relative, expected in self.PROTECTED.items():
            with self.subTest(relative=relative):
                self.assertEqual(git_blob_sha(ROOT / relative), expected)

    def test_matlab_ownership_and_per_question_layout_remain_unchanged(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertIn("draw.io", output["ownership"]["other_figure_tools"])
        self.assertEqual(len(output["per_question"]["exact_default_files"]), 5)
        self.assertIn("q{阿拉伯序号}_plot.m", output["per_question"]["exact_default_files"])
        self.assertNotIn("matplotlib", (ROOT / "templates/code").read_text(encoding="utf-8") if (ROOT / "templates/code").is_file() else "")

    def test_figure_authority_and_adapter_boundaries_are_explicit(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        pack = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        for token in ("Mechanism Diagram Backend Selection Gate", "structure_checked", "approved_for_paper", "不判断箭头方向是否符合真实机制"):
            self.assertIn(token, module)
        self.assertIn("templates/figure/mechanism_drawio_spec.yaml", pack)
        self.assertIn("modules/04_figure_evidence.md", pack)

    def test_route_loads_drawio_resources_only_for_precise_trigger(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        general = router["routing"]["figures"]
        precise = router["routing"]["editable_mechanism_diagram"]
        self.assertNotIn("templates/figure/mechanism_drawio_patterns.md", general["load"])
        self.assertIn("可编辑机理图", precise["triggers"])
        self.assertIn("templates/figure/mechanism_drawio_patterns.md", precise["load"])

    def test_natural_language_routing_keeps_drawio_resources_conditional(self):
        def resolve(request: str) -> dict:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/resolve_workflow.py"), "--request", request],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return yaml.safe_load(result.stdout)

        editable = resolve("请用 draw.io 生成一张可编辑机理图")
        ordinary = resolve("请根据结果工作簿生成结果图")
        resource = "templates/figure/mechanism_drawio_patterns.md"
        self.assertIn(resource, editable["load_order"])
        self.assertNotIn(resource, ordinary["load_order"])

    def test_release_carriers_are_830_and_skill_entrypoints_match(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(bootstrap["skill_version"], "8.3.0")
        self.assertEqual(plugin["version"], "8.3.0")
        self.assertEqual(root_skill, packaged)
        self.assertIn("Editable Mechanism Diagram", root_skill)


if __name__ == "__main__":
    unittest.main()
