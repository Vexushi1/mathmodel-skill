from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_yaml(relative: str):
    return yaml.safe_load(read(relative))


def active_sources(
    manifest: dict,
    *,
    data: bool,
    model_preparation: bool,
    ai_disclosure: bool,
    questions: int,
) -> list[str]:
    """Resolve final physical sources from the existing ordered_slots + activation facts."""
    examples = manifest["cumcm_question_section"]["maintained_examples"][:questions]
    result: list[str] = []
    for slot in manifest["paper_skeleton"]["ordered_slots"]:
        slot_id = slot["id"]
        if slot_id == "question_sections":
            result.extend(item["source"] for item in examples)
        elif slot_id == "data":
            if data:
                result.append(slot["source"])
        elif slot_id == "model_preparation":
            if model_preparation:
                result.append(slot["source"])
        elif slot_id == "ai_disclosure":
            if ai_disclosure:
                result.append(slot["source"])
        elif slot.get("required") or slot.get("default_active"):
            result.append(slot["source"])
    return result


class TestV810CrossFileChapterHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = read("modules/05_writing/paper_writing_protocol.md")
        cls.runtime = load_yaml("core/writing_runtime_contract.yaml")
        cls.framework = read("templates/model/model_paper_framework.md")
        cls.review = read("modules/06_review_delivery.md")
        cls.manifest = load_yaml("templates/latex/cumcm/hsk/template_manifest.yaml")
        cls.reasoning = load_yaml("core/writing_reasoning_contract.yaml")
        cls.project_state = read("core/project_state.schema.yaml")

    def test_protocol_is_the_only_cross_file_prose_authority(self):
        self.assertIn("Cross-File Chapter Handoff", self.protocol)
        for token in (
            "narrative",
            "registry_or_definition",
            "frontmatter_consistency",
            "structural_terminal",
            "cross_question_increment",
            "object_continuity",
            "symbol_term_continuity",
            "dependency_continuity",
            "claim_continuity",
            "duplication_control",
            "transition_necessity",
        ):
            self.assertIn(token, self.protocol)

        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        self.assertEqual(
            handoff["authority"],
            "modules/05_writing/paper_writing_protocol.md#5A-Cross-File-Chapter-Handoff",
        )
        self.assertIn("只消费", self.review)
        self.assertNotIn("cross_file_chapter_handoff", self.reasoning)
        self.assertNotIn("cross_file_handoff_contract", read("SKILL_FILE_INDEX.md"))

    def test_existing_manifest_recovers_minimal_final_order_without_new_schema(self):
        sources = active_sources(
            self.manifest,
            data=False,
            model_preparation=False,
            ai_disclosure=False,
            questions=1,
        )
        self.assertEqual(
            sources,
            [
                "frontmatter/abstract.tex",
                "sections/01_problem_statement.tex",
                "sections/02_problem_analysis.tex",
                "sections/03_assumptions.tex",
                "sections/04_symbols.tex",
                "sections/06_question1.tex",
                "sections/09_evaluation.tex",
                "references.bib",
                "appendices/appendices.tex",
            ],
        )

    def test_conditional_slots_change_actual_adjacency_only_when_active(self):
        no_optional = active_sources(
            self.manifest,
            data=False,
            model_preparation=False,
            ai_disclosure=False,
            questions=1,
        )
        data_only = active_sources(
            self.manifest,
            data=True,
            model_preparation=False,
            ai_disclosure=False,
            questions=1,
        )
        preparation_only = active_sources(
            self.manifest,
            data=False,
            model_preparation=True,
            ai_disclosure=False,
            questions=1,
        )
        both = active_sources(
            self.manifest,
            data=True,
            model_preparation=True,
            ai_disclosure=False,
            questions=1,
        )

        symbols = "sections/04_symbols.tex"
        q1 = "sections/06_question1.tex"
        self.assertEqual(no_optional[no_optional.index(symbols) + 1], q1)
        self.assertEqual(data_only[data_only.index(symbols) + 1], "sections/05_data.tex")
        self.assertEqual(
            preparation_only[preparation_only.index(symbols) + 1],
            "sections/05_model_preparation.tex",
        )
        self.assertEqual(
            both[both.index("sections/05_data.tex") + 1],
            "sections/05_model_preparation.tex",
        )
        self.assertEqual(
            both[both.index("sections/05_model_preparation.tex") + 1],
            q1,
        )

    def test_ai_disclosure_changes_terminal_adjacency_only_when_active(self):
        inactive = active_sources(
            self.manifest,
            data=False,
            model_preparation=False,
            ai_disclosure=False,
            questions=1,
        )
        active = active_sources(
            self.manifest,
            data=False,
            model_preparation=False,
            ai_disclosure=True,
            questions=1,
        )
        evaluation = "sections/09_evaluation.tex"
        disclosure = "sections/10_ai_tool_statement.tex"
        references = "references.bib"
        self.assertEqual(inactive[inactive.index(evaluation) + 1], references)
        self.assertEqual(active[active.index(evaluation) + 1], disclosure)
        self.assertEqual(active[active.index(disclosure) + 1], references)

    def test_q1_q2_q3_keep_final_adjacency_without_forced_dependency(self):
        sources = active_sources(
            self.manifest,
            data=False,
            model_preparation=False,
            ai_disclosure=False,
            questions=3,
        )
        question_sources = [source for source in sources if "_question" in source]
        self.assertEqual(
            question_sources,
            [
                "sections/06_question1.tex",
                "sections/07_question2.tex",
                "sections/08_question3.tex",
            ],
        )
        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        profile = handoff["profiles"]["cross_question_increment"]
        self.assertEqual(profile["activate_when"], "actual_dependency_exists")
        self.assertEqual(profile["delegates_to"], "cross_question_progression")

    def test_final_assembly_order_not_authoring_order_controls_seams(self):
        progressive = self.runtime["template_first_progressive_authoring"]
        handoff = progressive["cross_file_chapter_handoff"]
        self.assertEqual(
            handoff["order"]["assembled_order_source"],
            "templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton.ordered_slots+activation",
        )
        self.assertEqual(handoff["order"]["authoring_order_source"], "stages")
        self.assertEqual(
            handoff["order"]["seam_gate_uses"],
            ["assembled_predecessor", "assembled_successor"],
        )
        self.assertEqual(
            handoff["abstract_special_case"]["required_final_seam"],
            "frontmatter/abstract.tex -> sections/01_problem_statement.tex",
        )
        self.assertEqual(
            handoff["abstract_special_case"]["forbidden_authoring_seam"],
            "sections/09_evaluation.tex -> frontmatter/abstract.tex",
        )

    def test_runtime_declares_read_write_gate_and_assembled_sweep(self):
        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        self.assertIn("before_write", handoff["timing"])
        self.assertIn("after_write", handoff["timing"])
        self.assertIn("stage_gate", handoff["timing"])
        self.assertIn("draft_semantic_review", handoff["timing"])
        self.assertEqual(
            handoff["timing"]["draft_semantic_review"],
            "assembled_seam_sweep_in_final_active_order",
        )
        stages = {
            stage["id"]: stage
            for stage in self.runtime["template_first_progressive_authoring"]["stages"]
        }
        self.assertIn("resolve_active_final_assembly_and_actual_seams", stages["template_inspection"]["run_now"])
        self.assertIn("assembled_seam_sweep", stages["draft_semantic_review"]["run_now"])

    def test_framework_map_is_optional_writing_memory_outside_semantic_hash(self):
        self.assertIn("### Chapter Handoff Map", self.framework)
        self.assertIn("writing-only", self.framework)
        self.assertIn("不属于模型语义哈希区", self.framework)
        for field in (
            "Seam ID",
            "Profile",
            "Source File",
            "Target File",
            "Source Closure",
            "Carry Forward",
            "Open Gap / Entry Reason",
            "Consistency Anchors",
            "Bridge Need",
            "Status",
        ):
            self.assertIn(field, self.framework)

        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        boundary = handoff["semantic_boundary"]
        self.assertTrue(boundary["writing_only"])
        self.assertFalse(boundary["included_in_model_semantic_hash"])
        self.assertFalse(boundary["pure_handoff_semantic_revision_bump"])
        self.assertFalse(boundary["invalidates_locked_model_spec"])
        self.assertFalse(boundary["triggers_model_approval"])
        self.assertFalse(boundary["triggers_primary_solve"])
        self.assertNotIn("chapter_handoff", self.project_state)

    def test_old_framework_and_single_file_routes_remain_compatible(self):
        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        compatibility = handoff["compatibility"]
        self.assertEqual(
            compatibility["missing_map"],
            "initialize_incrementally_on_next_writing_route",
        )
        self.assertFalse(compatibility["rewrite_existing_body"])
        self.assertEqual(handoff["activation"]["single_file"], "not_applicable")
        self.assertEqual(
            handoff["activation"]["non_cumcm_or_missing_manifest"],
            "full_reasoning_fallback",
        )

    def test_no_forced_transition_or_connector_frequency_gate(self):
        handoff = self.runtime["template_first_progressive_authoring"]["cross_file_chapter_handoff"]
        self.assertEqual(
            handoff["record"]["bridge_need_values"],
            ["required", "optional", "not_needed"],
        )
        machine = self.runtime["machine_boundary"]
        self.assertNotIn("connector_frequency", machine["may_check"])
        self.assertIn("semantic_continuity_from_transition_words", machine["must_not_claim"])
        self.assertIn("不建立连接词词库", self.protocol)
        self.assertIn("不要求每个 physical-file seam 都出现正文过渡句", self.protocol)
        self.assertIn("assembled seam sweep", self.review)


if __name__ == "__main__":
    unittest.main()
