"""A2 external two-file CUMCM 2026 upload tests.

Tests operate on disposable project data; production CLI always checks the real
v4/v5 compile attestation rather than the synthetic PDF headers in these units.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cumcm_2026_delivery as DELIVERY  # noqa: E402


NO_USE = "本参赛队在竞赛过程中未使用任何AI工具。"
AI_USE = "本参赛队在竞赛过程中使用了AI工具，主要用于代码核验，详细使用情况见支撑材料。"
NONE = "本论文没有用到程序。\n本论文没有支撑材料。"


class Cumcm2026ExternalDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "final_latex").mkdir()
        self.output = self.root / "submission/cumcm2026_external"
        self.main = self.root / "final_latex/main.tex"
        (self.root / "final_latex/main.pdf").write_bytes(b"%PDF-1.5\nsynthetic-test-pdf\n")
        (self.root / "final_latex/compile_report.yaml").write_text("{}\n", encoding="utf-8")
        self.state = {
            "project": {"competition": "CUMCM", "competition_edition": "2026"},
            "artifacts": {
                "latex_source": "final_latex/main.tex",
                "compiled_pdf": "final_latex/main.pdf",
                "compile_report": "final_latex/compile_report.yaml",
            },
            "subproblems": {},
            "data": {"sources": []},
        }
        self._save_state()
        self._paper()

    def _save_state(self) -> None:
        (self.root / "state/project_state.yaml").write_text(
            yaml.safe_dump(self.state, allow_unicode=True, sort_keys=False),
            encoding="utf-8")

    def _paper(self, *, declaration: str = NO_USE, appendix: str = NONE,
               electronic: bool = True) -> None:
        cls = (r"\documentclass[withoutpreface]{cumcmthesis}" if electronic
               else r"\documentclass{cumcmthesis}")
        self.main.write_text(
            cls + "\n"
            + r"\begin{document}" + "\n"
            + r"\section*{AI工具使用声明}" + "\n" + declaration + "\n"
            + r"\printbibliography" + "\n"
            + r"\begin{appendices}" + "\n"
            + r"\section*{附录}" + "\n"
            + appendix + "\n"
            + r"\end{appendices}" + "\n"
            + r"\end{document}" + "\n", encoding="utf-8")

    def _prepare(self, *, files: tuple[str, ...] = (),
                 confirmed: bool = True, formal: bool = False):
        return DELIVERY.prepare(
            self.root, extra_files=files,
            anonymous_confirmed=confirmed, formal=formal,
        )

    def test_no_material_means_only_pdf_no_internal_zip(self) -> None:
        plan = self._prepare()
        self.assertEqual([], plan["support"])
        result = DELIVERY.build(plan, self.output)
        self.assertEqual("passed", result["status"])
        self.assertIsNone(result["support_zip"])
        self.assertTrue((self.output / DELIVERY.PAPER_NAME).is_file())
        self.assertFalse((self.output / DELIVERY.SUPPORT_NAME).exists())
        self.assertFalse((self.output / "submission.zip").exists())

    def test_independent_data_is_auto_selected_and_exactly_listed(self) -> None:
        source = self.root / "资料/独立数据.csv"
        source.parent.mkdir()
        source.write_text("x,y\n1,2\n", encoding="utf-8")
        self.state["data"]["sources"] = [
            {"name": "独立公开采集资料", "path": "资料/独立数据.csv", "role": "自主查阅"}
        ]
        self._save_state()
        self._paper(appendix="本论文没有用到程序。\n支撑材料文件：资料/独立数据.csv")
        plan = self._prepare()
        self.assertEqual(["资料/独立数据.csv"], plan["support"])
        result = DELIVERY.build(plan, self.output)
        with zipfile.ZipFile(self.output / DELIVERY.SUPPORT_NAME) as z:
            self.assertEqual(["资料/独立数据.csv"], z.namelist())
            self.assertNotIn("submission_manifest.yaml", z.namelist())
        self.assertEqual(["资料/独立数据.csv"], result["support_files"])

    def test_ai_use_requires_detail_pdf_and_appendix_listing(self) -> None:
        self._paper(declaration=AI_USE,
                    appendix="本论文没有用到程序。\nAI工具使用详情.pdf")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "不存在"):
            self._prepare()
        detail = self.root / "AI工具使用详情.pdf"
        detail.write_bytes(b"%PDF-1.5\nactual-detail-placeholder-for-unit-test\n")
        plan = self._prepare()
        self.assertTrue(plan["ai_used"])
        self.assertEqual(["AI工具使用详情.pdf"], plan["support"])
        self.assertEqual("passed", DELIVERY.build(plan, self.output)["status"])
        detail.write_bytes(b"%PDF-1.5\naltered\n")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "文件内容已变化"):
            DELIVERY.verify(plan, self.output)

    def test_excel_and_spss_commands_can_be_explicit_support(self) -> None:
        cmd = self.root / "命令/analysis.sps"
        cmd.parent.mkdir()
        cmd.write_text("FREQUENCIES VARIABLES=x.", encoding="utf-8")
        self._paper(appendix=(
            "支撑材料文件：命令/analysis.sps\n"
            r"\lstinputlisting{../命令/analysis.sps}"
        ))
        plan = self._prepare(files=("命令/analysis.sps",))
        self.assertIn("命令/analysis.sps", plan["programs"])
        self.assertEqual("passed", DELIVERY.build(plan, self.output)["status"])

    def test_incomplete_program_listing_and_false_no_program_are_blocked(self) -> None:
        code = self.root / "源码/q1.py"
        code.parent.mkdir()
        code.write_text("print(42)\n", encoding="utf-8")
        self._paper(appendix="本论文没有用到程序。\n源码/q1.py\n")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "已有实际源程序"):
            self._prepare(files=("源码/q1.py",))
        self._paper(appendix="源码/q1.py\n")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "lstinputlisting"):
            self._prepare(files=("源码/q1.py",))
        self._paper(appendix="源码/q1.py\n"
                    + r"\lstinputlisting[firstline=1,lastline=1]{../源码/q1.py}")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "firstline/lastline"):
            self._prepare(files=("源码/q1.py",))

    def test_missing_appendix_support_name_rejected(self) -> None:
        aux = self.root / "资料/extra.csv"
        aux.parent.mkdir()
        aux.write_text("one,two", encoding="utf-8")
        self._paper(appendix="本论文没有用到程序。")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "未在正文附录列示"):
            self._prepare(files=("资料/extra.csv",))

    def test_problem_attachment_never_auto_or_explicitly_exported(self) -> None:
        attachment = self.root / "附件一.xlsx"
        attachment.write_bytes(b"example")
        self.state["data"]["sources"] = [
            {"name": "赛题附件一", "path": "附件一.xlsx", "role": "赛题原始输入"}
        ]
        self._save_state()
        self.assertEqual([], self._prepare()["support"])
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "赛题提供"):
            self._prepare(files=("附件一.xlsx",))

    def test_path_traversal_and_internal_archives_are_blocked(self) -> None:
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "禁止绝对或上级路径"):
            self._prepare(files=("../unsafe.csv",))
        archive = self.root / "submission/submission.zip"
        archive.parent.mkdir(exist_ok=True)
        archive.write_bytes(b"internal")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "内部状态"):
            self._prepare(files=("submission/submission.zip",))

    def test_anonymity_needs_human_confirmation_and_personal_data_rejected(self) -> None:
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "人工确认"):
            self._prepare(confirmed=False)
        self._paper(appendix="本论文没有用到程序。\n本论文没有支撑材料。\n"
                    "联系邮箱 author@example.edu")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "身份"):
            self._prepare()

    def test_wrong_edition_or_paper_mode_or_placeholder_blocked(self) -> None:
        self.state["project"]["competition_edition"] = "2025"
        self._save_state()
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "届次"):
            self._prepare()
        self.state["project"]["competition_edition"] = "2026"
        self._save_state()
        self._paper(electronic=False)
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "摘要首页"):
            self._prepare()
        self._paper(declaration="【待填写】")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "正式论文结构不合格"):
            self._prepare()

    def test_pdf_staleness_size_limit_and_extra_zip_blocked(self) -> None:
        plan = self._prepare()
        DELIVERY.build(plan, self.output)
        (self.root / "final_latex/main.pdf").write_bytes(b"%PDF-1.5\nchanged\n")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "已与当前"):
            DELIVERY.verify(self._prepare(), self.output)
        (self.root / "final_latex/main.pdf").write_bytes(b"%PDF-1.5\nsynthetic-test-pdf\n")
        plan = self._prepare()
        plan["rules"] = dict(plan["rules"])
        plan["rules"]["paper"] = dict(plan["rules"]["paper"])
        plan["rules"]["paper"]["max_paper_mb"] = 0
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "超过"):
            DELIVERY.verify(plan, self.output)
        (self.output / DELIVERY.SUPPORT_NAME).write_bytes(b"stale")
        with self.assertRaisesRegex(DELIVERY.DeliveryError, "遗留旧支撑 ZIP"):
            DELIVERY.verify(self._prepare(), self.output)

    def test_formal_build_calls_live_compilation_attestation(self) -> None:
        with patch.object(DELIVERY, "verify_compile_report",
                          return_value=["编译证明过期"]) as verifier:
            with self.assertRaisesRegex(DELIVERY.DeliveryError, "编译证明过期"):
                self._prepare(formal=True)
            verifier.assert_called_once()


if __name__ == "__main__":
    unittest.main()
