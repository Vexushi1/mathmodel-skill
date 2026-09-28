"""Bounded DOCX carrier facts for later B2 cross-format consumption."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import claim_docx  # noqa: E402
from claim_docx import bind_bookmark_figure, locate_literal_anchor, scan_docx  # noqa: E402


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOC_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure.png"/>
</Relationships>"""
VALID_DRAWING = (
    '<w:drawing><wp:inline><wp:extent cx="1" cy="1"/>'
    '<wp:docPr id="1" name="Picture 1"/><a:graphic>'
    '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="figure.png"/>'
    '<pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
    '<a:blip r:embed="rImg1"/><a:stretch><a:fillRect/></a:stretch>'
    '</pic:blipFill><pic:spPr><a:xfrm/><a:prstGeom prst="rect">'
    '<a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
    '</a:graphicData></a:graphic></wp:inline></w:drawing>'
)
DOCUMENT = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
 <w:body>
  <w:p><w:r><w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t></w:r></w:p>
  <w:p><w:bookmarkStart w:id="7" w:name="fig_q1"/><w:r>{VALID_DRAWING}</w:r>
   <w:r><w:t>Figure 1. Accepted result 100.00.</w:t></w:r><w:bookmarkEnd w:id="7"/></w:p>
  <w:sectPr/>
 </w:body>
</w:document>"""


class DocxScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "paper.docx"
        self.image = b"\x89PNG\r\n\x1a\nsynthetic-image"

    def tearDown(self):
        self.tmp.cleanup()

    def write_docx(self, *, document: str | bytes = DOCUMENT, document_rels: str = DOC_RELS,
                   extras: list[tuple[str, bytes | str]] | None = None) -> None:
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", CONTENT_TYPES)
            archive.writestr("_rels/.rels", ROOT_RELS)
            archive.writestr("word/document.xml", document)
            archive.writestr("word/_rels/document.xml.rels", document_rels)
            archive.writestr("word/media/figure.png", self.image)
            for name, payload in extras or []:
                archive.writestr(name, payload)

    def test_split_runs_anchor_and_bookmarked_image_caption_are_bound(self):
        self.write_docx()
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "scanned", scan)
        self.assertEqual(scan["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(scan["paragraphs"][0]["text"], "Answer: 100.00")
        location = locate_literal_anchor(scan, "Answer: 100.00")
        self.assertEqual(location["status"], "located", location)
        self.assertEqual(location["paragraph"], 1)
        binding = bind_bookmark_figure(scan, "fig_q1", "Figure 1.")
        self.assertEqual(binding["status"], "matched", binding)
        self.assertEqual(binding["relationship_id"], "rImg1")
        self.assertEqual(binding["package_part"], "word/media/figure.png")
        self.assertEqual(binding["image_sha256"], hashlib.sha256(self.image).hexdigest())

    def test_absent_or_ambiguous_literal_anchor_is_not_assessed(self):
        document = DOCUMENT.replace("<w:sectPr/>", "<w:p><w:r><w:t>Answer: 100.00</w:t></w:r></w:p><w:sectPr/>")
        self.write_docx(document=document)
        scan = scan_docx(self.path)
        self.assertEqual(locate_literal_anchor(scan, "missing")["status"], "not_assessed")
        ambiguous = locate_literal_anchor(scan, "Answer: 100.00")
        self.assertEqual(ambiguous["status"], "not_assessed")
        self.assertEqual(ambiguous["match_count"], 2)

    def test_tracked_changes_fields_and_altchunk_are_not_assessed(self):
        variants = {
            "tracked": '<w:ins w:id="1"><w:r><w:t>changed</w:t></w:r></w:ins>',
            "run_property_revision": '<w:r><w:rPr><w:rPrChange w:id="2"/></w:rPr><w:t>changed</w:t></w:r>',
            "paragraph_property_revision": '<w:pPr><w:pPrChange w:id="3"/></w:pPr>',
            "numbering_revision": '<w:pPr><w:numPr><w:numberingChange w:id="4"/></w:numPr></w:pPr>',
            "custom_xml_revision_range": '<w:customXmlInsRangeStart w:id="5"/><w:customXmlInsRangeEnd w:id="5"/>',
            "field": '<w:r><w:fldChar w:fldCharType="begin"/><w:instrText> REF target </w:instrText></w:r>',
            "altchunk": '<w:altChunk r:id="rChunk1"/>',
            "text_box": '<w:txbxContent><w:p><w:r><w:t>hidden box</w:t></w:r></w:p></w:txbxContent>',
            "alternate_content": (
                '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
                '<mc:Choice Requires="future"><w:p><w:r><w:t>choice</w:t></w:r></w:p></mc:Choice>'
                '<mc:Fallback><w:p><w:r><w:t>fallback</w:t></w:r></w:p></mc:Fallback>'
                '</mc:AlternateContent>'
            ),
        }
        for name, payload in variants.items():
            with self.subTest(name=name):
                self.write_docx(document=DOCUMENT.replace("<w:sectPr/>", payload + "<w:sectPr/>"))
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "not_assessed", scan)
                self.assertEqual(locate_literal_anchor(scan, "Answer: 100.00")["status"], "not_assessed")

    def test_chart_and_automatic_numbering_are_not_assessed(self):
        chart = DOCUMENT.replace(
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">',
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
            'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">',
        ).replace(
            "<w:sectPr/>",
            '<w:p><w:r><w:drawing><a:graphic><a:graphicData '
            'uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
            '<c:chart r:id="rChart1"/></a:graphicData></a:graphic>'
            '</w:drawing></w:r></w:p><w:sectPr/>',
        )
        chart_rels = DOC_RELS.replace(
            "</Relationships>",
            '<Relationship Id="rChart1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" '
            'Target="charts/chart1.xml"/></Relationships>',
        )
        self.write_docx(
            document=chart, document_rels=chart_rels,
            extras=[("word/charts/chart1.xml", "<chart>Globally optimal 999.0</chart>")],
        )
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("non_image_drawing_unsupported",
                      {row["code"] for row in scan["issues"]})

        numbering = DOCUMENT.replace(
            "<w:sectPr/>",
            '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/>'
            '</w:numPr></w:pPr><w:r><w:t>Visible item</w:t></w:r></w:p>'
            '<w:sectPr/>',
        )
        self.write_docx(document=numbering)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("automatic_numbering_unsupported",
                      {row["code"] for row in scan["issues"]})

    def test_external_relationship_is_blocked(self):
        rels = DOC_RELS.replace(
            "</Relationships>",
            '<Relationship Id="rExt" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.invalid" TargetMode="External"/></Relationships>',
        )
        self.write_docx(document_rels=rels)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("external_relationship_unsupported", {row["code"] for row in scan["issues"]})

    def test_relationship_types_modes_and_image_content_types_are_exact(self):
        for invalid_id in ("bad id", "1bad", "a:b"):
            with self.subTest(invalid_id=invalid_id):
                rels = DOC_RELS.replace('Id="rImg1"', f'Id="{invalid_id}"')
                document = DOCUMENT.replace('r:embed="rImg1"',
                                            f'r:embed="{invalid_id}"')
                self.write_docx(document=document, document_rels=rels)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "blocked", scan)
                self.assertIn("invalid_relationship_id",
                              {row["code"] for row in scan["issues"]})

        for encoded_target in (
            "media/%66igure.png", "media/%2e%2e/figure.png", "media/foo%2fbar.png",
            "media/figure#frag.png", "media/figure?x=.png",
        ):
            with self.subTest(encoded_target=encoded_target):
                rels = DOC_RELS.replace("media/figure.png", encoded_target)
                self.write_docx(
                    document_rels=rels,
                    extras=[("word/" + encoded_target, self.image)],
                )
                self.assertEqual(scan_docx(self.path)["status"], "blocked")

        fake_image = DOC_RELS.replace(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            "https://invalid.example/image",
        )
        self.write_docx(document_rels=fake_image)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("drawing_relationship_is_not_internal_image",
                      {row["code"] for row in scan["issues"]})

        invalid_mode = DOC_RELS.replace('Target="media/figure.png"',
                                        'Target="media/figure.png" TargetMode="Maybe"')
        self.write_docx(document_rels=invalid_mode)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("invalid_relationship_target_mode", {row["code"] for row in scan["issues"]})

        unsupported_type = CONTENT_TYPES.replace('ContentType="image/png"',
                                                  'ContentType="application/octet-stream"')
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", unsupported_type)
            archive.writestr("_rels/.rels", ROOT_RELS)
            archive.writestr("word/document.xml", DOCUMENT)
            archive.writestr("word/_rels/document.xml.rels", DOC_RELS)
            archive.writestr("word/media/figure.png", self.image)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("image_content_type_unsupported", {row["code"] for row in scan["issues"]})

    def test_duplicate_and_traversal_zip_entries_are_blocked(self):
        self.write_docx()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.path, "a") as archive:
                archive.writestr("word/document.xml", DOCUMENT)
        self.assertEqual(scan_docx(self.path)["status"], "blocked")
        self.write_docx(extras=[("../escape.xml", "<x/>")])
        self.assertEqual(scan_docx(self.path)["status"], "blocked")
        for alias in ("word//shadow.xml", "word/./shadow.xml"):
            with self.subTest(alias=alias):
                self.write_docx(extras=[(alias, "<x/>")])
                self.assertEqual(scan_docx(self.path)["status"], "blocked")

    def test_package_budgets_fail_closed(self):
        self.write_docx()
        self.assertEqual(scan_docx(self.path, max_entries=2)["status"], "blocked")
        self.assertEqual(scan_docx(self.path, max_entry_bytes=8)["status"], "blocked")
        self.assertEqual(scan_docx(self.path, max_total_uncompressed_bytes=32)["status"], "blocked")
        self.assertEqual(scan_docx(self.path, max_compression_ratio=1)["status"], "blocked")
        with patch.object(Path, "open", side_effect=AssertionError("oversized package was opened")):
            self.assertEqual(scan_docx(self.path, max_package_bytes=1)["status"], "blocked")

    def test_package_read_set_drift_is_blocked(self):
        self.write_docx()
        with patch.object(claim_docx, "_sha256_bounded_file", return_value="0" * 64):
            scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertTrue(any("changed during scan" in row.get("detail", "")
                            for row in scan["issues"]), scan)

    def test_damaged_bookmarks_are_blocked(self):
        crossed = DOCUMENT.replace(
            '<w:bookmarkStart w:id="7" w:name="fig_q1"/>',
            '<w:bookmarkStart w:id="7" w:name="fig_q1"/>'
            '<w:bookmarkStart w:id="8" w:name="fig_nested"/>',
        ).replace(
            '<w:bookmarkEnd w:id="7"/>',
            '<w:bookmarkEnd w:id="7"/><w:bookmarkEnd w:id="8"/>',
        )
        variants = {
            "unclosed": DOCUMENT.replace('<w:bookmarkEnd w:id="7"/>', ""),
            "orphan_end": DOCUMENT.replace('<w:bookmarkStart w:id="7" w:name="fig_q1"/>', ""),
            "duplicate_name": DOCUMENT.replace(
                "<w:sectPr/>",
                '<w:p><w:bookmarkStart w:id="8" w:name="fig_q1"/><w:r><w:t>x</w:t></w:r><w:bookmarkEnd w:id="8"/></w:p><w:sectPr/>',
            ),
            "reused_id": DOCUMENT.replace(
                "<w:sectPr/>",
                '<w:p><w:bookmarkStart w:id="7" w:name="fig_other"/><w:r><w:t>x</w:t></w:r><w:bookmarkEnd w:id="7"/></w:p><w:sectPr/>',
            ),
            "invalid_decimal_id": DOCUMENT.replace('w:id="7"', 'w:id="abc"'),
            "normalized_reused_id": DOCUMENT.replace(
                "<w:sectPr/>",
                '<w:p><w:bookmarkStart w:id="07" w:name="fig_other"/><w:r><w:t>x</w:t></w:r><w:bookmarkEnd w:id="07"/></w:p><w:sectPr/>',
            ),
            "crossed_ranges": crossed,
        }
        for name, document in variants.items():
            with self.subTest(name=name):
                self.write_docx(document=document)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "blocked", scan)
                self.assertTrue(any("bookmark" in row["code"] for row in scan["issues"]), scan)

    def test_bookmark_binding_requires_unique_caption_and_image(self):
        self.write_docx(document=DOCUMENT.replace("Figure 1.", "Caption without identifier."))
        scan = scan_docx(self.path)
        binding = bind_bookmark_figure(scan, "fig_q1", "Figure 1.")
        self.assertEqual(binding["status"], "not_assessed", binding)
        self.write_docx(document=DOCUMENT.replace(
            '<w:r><w:t>Figure 1.', f'<w:r>{VALID_DRAWING}</w:r><w:r><w:t>Figure 1.'))
        scan = scan_docx(self.path)
        binding = bind_bookmark_figure(scan, "fig_q1", "Figure 1.")
        self.assertEqual(binding["status"], "not_assessed", binding)
        self.assertEqual(binding["image_count"], 2)

    def test_image_at_same_text_offset_but_outside_bookmark_is_not_bound(self):
        document = DOCUMENT.replace(
            f'<w:bookmarkStart w:id="7" w:name="fig_q1"/><w:r>{VALID_DRAWING}</w:r>',
            f'<w:r>{VALID_DRAWING}</w:r>'
            '<w:bookmarkStart w:id="7" w:name="fig_q1"/>',
        )
        self.write_docx(document=document)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "scanned", scan)
        binding = bind_bookmark_figure(scan, "fig_q1", "Figure 1.")
        self.assertEqual(binding["status"], "not_assessed", binding)
        self.assertEqual(binding["image_count"], 0)

    def test_naked_or_misnested_blip_is_not_an_embedded_figure(self):
        for name, replacement in (
            ("naked", '<a:blip r:embed="rImg1"/>'),
            ("misnested", '<w:drawing><a:blip r:embed="rImg1"/></w:drawing>'),
        ):
            with self.subTest(name=name):
                self.write_docx(document=DOCUMENT.replace(VALID_DRAWING, replacement))
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "not_assessed", scan)
                self.assertIn("misnested_image_blip_unsupported",
                              {row["code"] for row in scan["issues"]})
                self.assertEqual(
                    bind_bookmark_figure(scan, "fig_q1", "Figure 1.")["status"],
                    "not_assessed",
                )

    def test_picture_outside_a_direct_paragraph_run_is_not_assessed(self):
        variants = {
            "outside_paragraph": DOCUMENT.replace(
                "<w:sectPr/>", f"<w:r>{VALID_DRAWING}</w:r><w:sectPr/>"),
            "wrapped_run": DOCUMENT.replace(
                f"<w:r>{VALID_DRAWING}</w:r>",
                f"<w:unknown><w:r>{VALID_DRAWING}</w:r></w:unknown>",
            ),
            "wrapped_drawing": DOCUMENT.replace(
                VALID_DRAWING, f"<w:unknown>{VALID_DRAWING}</w:unknown>"),
        }
        for name, document in variants.items():
            with self.subTest(name=name):
                self.write_docx(document=document)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "not_assessed", scan)
                self.assertIn("misnested_drawing_unsupported",
                              {row["code"] for row in scan["issues"]})
                self.assertEqual(
                    bind_bookmark_figure(scan, "fig_q1", "Figure 1.")["status"],
                    "not_assessed",
                )

    def test_alternate_svg_representation_cannot_bypass_image_identity(self):
        alternate = VALID_DRAWING.replace(
            '<a:blip r:embed="rImg1"/>',
            '<a:blip r:embed="rImg1"><a:extLst><a:ext uri="svg">'
            '<asvg:svgBlip '
            'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
            'r:embed="rImg2"/></a:ext></a:extLst></a:blip>',
        )
        rels = DOC_RELS.replace(
            "</Relationships>",
            '<Relationship Id="rImg2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            'Target="media/alternate.svg"/></Relationships>',
        )
        self.write_docx(
            document=DOCUMENT.replace(VALID_DRAWING, alternate),
            document_rels=rels,
            extras=[("word/media/alternate.svg", "<svg>different visible bytes</svg>")],
        )
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("alternate_image_representation_unsupported",
                      {row["code"] for row in scan["issues"]})
        self.assertEqual(
            bind_bookmark_figure(scan, "fig_q1", "Figure 1.")["status"],
            "not_assessed",
        )

    def test_main_document_content_type_must_be_exact(self):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", CONTENT_TYPES.replace(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
                "application/xml",
            ))
            archive.writestr("_rels/.rels", ROOT_RELS)
            archive.writestr("word/document.xml", DOCUMENT)
            archive.writestr("word/_rels/document.xml.rels", DOC_RELS)
            archive.writestr("word/media/figure.png", self.image)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("content type", scan["issues"][0]["detail"])

    def test_missing_image_media_and_dtd_are_blocked(self):
        self.write_docx(document_rels=DOC_RELS.replace("media/figure.png", "media/missing.png"))
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("image_media_part_missing", {row["code"] for row in scan["issues"]})
        dtd = DOCUMENT.replace('<?xml version="1.0" encoding="UTF-8"?>',
                               '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "x">]>')
        self.write_docx(document=dtd)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("docx_scan_failed", {row["code"] for row in scan["issues"]})

        late_dtd = DOCUMENT.replace(
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml version="1.0"?>' + (" " * 5000)
            + '<!DOCTYPE w:document [<!ENTITY claim "Answer: 100.00">]>',
        ).replace("Answer: </w:t></w:r><w:r><w:t>100.00", "&claim;</w:t></w:r><w:r><w:t>")
        self.write_docx(document=late_dtd)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertIn("docx_scan_failed", {row["code"] for row in scan["issues"]})

        unused_dtd = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY claim "hidden">]><x/>'
        self.write_docx(extras=[("word/unused.xml", unused_dtd)])
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "blocked", scan)
        self.assertTrue(any("word/unused.xml" in row.get("detail", "")
                            for row in scan["issues"]), scan)

        for encoding in ("utf-16", "utf-32"):
            with self.subTest(encoding=encoding):
                encoded = DOCUMENT.replace(
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    f'<?xml version="1.0" encoding="{encoding.upper()}"?>'
                    '<!DOCTYPE w:document [<!ENTITY claim "100.00">]>',
                ).replace('>100.00</w:t>', '>&claim;</w:t>', 1).encode(encoding)
                self.write_docx(document=encoded)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "blocked", scan)
                self.assertIn("docx_scan_failed", {row["code"] for row in scan["issues"]})

    def test_style_inherited_automatic_numbering_is_not_assessed(self):
        document = DOCUMENT.replace(
            '<w:p><w:r><w:t>Answer: </w:t>',
            '<w:p><w:pPr><w:pStyle w:val="ClaimList"/></w:pPr>'
            '<w:r><w:t>Answer: </w:t>',
        )
        rels = DOC_RELS.replace(
            "</Relationships>",
            '<Relationship Id="rStyles" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            '<Relationship Id="rNumbering" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" '
            'Target="numbering.xml"/></Relationships>',
        )
        styles = (
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:style w:type="paragraph" w:styleId="ClaimList">'
            '<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/>'
            '</w:numPr></w:pPr></w:style></w:styles>'
        )
        numbering = (
            '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0">'
            '<w:lvlText w:val="Globally optimal %1"/>'
            '</w:lvl></w:abstractNum></w:numbering>'
        )
        self.write_docx(
            document=document, document_rels=rels,
            extras=[("word/styles.xml", styles), ("word/numbering.xml", numbering)],
        )
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("automatic_numbering_unsupported",
                      {row["code"] for row in scan["issues"]})

    def test_misnested_text_cannot_satisfy_claims(self):
        variants = {
            "direct_text": DOCUMENT.replace(
                '<w:r><w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t></w:r>',
                '<w:t>Answer: 100.00</w:t>',
            ),
            "unknown_wml_wrapper": DOCUMENT.replace(
                '<w:r><w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t></w:r>',
                '<w:smartTag><w:r><w:t>Answer: 100.00</w:t></w:r></w:smartTag>',
            ),
        }
        for name, document in variants.items():
            with self.subTest(name=name):
                self.write_docx(document=document)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "not_assessed", scan)
                self.assertIn("misnested_text_unsupported",
                              {row["code"] for row in scan["issues"]})
                self.assertNotIn("Answer: 100.00", scan["text"])

    def test_orphan_text_and_wrapped_paragraph_are_not_assessed(self):
        variants = {
            "orphan_text": (
                DOCUMENT.replace("<w:sectPr/>",
                                 "<w:t>unregistered 999.00</w:t><w:sectPr/>"),
                "orphan_text_unsupported",
            ),
            "wrapped_paragraph": (
                DOCUMENT.replace(
                    '<w:p><w:r><w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t></w:r></w:p>',
                    '<w:unknown><w:p><w:r><w:t>Answer: 100.00</w:t></w:r></w:p></w:unknown>',
                ),
                "misnested_paragraph_unsupported",
            ),
        }
        for name, (document, expected_code) in variants.items():
            with self.subTest(name=name):
                self.write_docx(document=document)
                scan = scan_docx(self.path)
                self.assertEqual(scan["status"], "not_assessed", scan)
                self.assertIn(expected_code, {row["code"] for row in scan["issues"]})

    def test_hidden_direct_or_style_text_is_not_assessed(self):
        hidden = DOCUMENT.replace(
            "<w:r><w:t>Answer: </w:t>",
            "<w:r><w:rPr><w:vanish/></w:rPr><w:t>Answer: </w:t>",
        )
        self.write_docx(document=hidden)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("hidden_text_unsupported", {row["code"] for row in scan["issues"]})

        style_rels = DOC_RELS.replace(
            "</Relationships>",
            '<Relationship Id="rStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        )
        styles = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:style w:type="character" w:styleId="Hidden"><w:rPr><w:vanish/></w:rPr></w:style>'
            '</w:styles>'
        )
        self.write_docx(document_rels=style_rels, extras=[("word/styles.xml", styles)])
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("hidden_style_text_unsupported", {row["code"] for row in scan["issues"]})

    def test_visible_nontext_cannot_be_dropped_to_join_a_literal_anchor(self):
        symbol = DOCUMENT.replace(
            "<w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t>",
            '<w:t>Answer: </w:t><w:sym w:font="Wingdings" w:char="F0FC"/>'
            "</w:r><w:r><w:t>100.00</w:t>",
        )
        self.write_docx(document=symbol)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertEqual(locate_literal_anchor(scan, "Answer: 100.00")["status"],
                         "not_assessed")

        inline_image = DOCUMENT.replace(
            "<w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t>",
            f'<w:t>Answer: </w:t>{VALID_DRAWING}'
            "</w:r><w:r><w:t>100.00</w:t>",
        )
        self.write_docx(document=inline_image)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("inline_drawing_splits_text_unsupported",
                      {row["code"] for row in scan["issues"]})

    def test_unknown_ignorable_extension_cannot_supply_claim_text(self):
        document = DOCUMENT.replace(
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">',
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
            'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
            'xmlns:x="urn:ignored" mc:Ignorable="x">',
        ).replace(
            '<w:p><w:r><w:t>Answer: </w:t></w:r><w:r><w:t>100.00</w:t></w:r></w:p>',
            '<x:phantom><w:p><w:r><w:t>Answer: </w:t></w:r>'
            '<w:r><w:t>100.00</w:t></w:r></w:p></x:phantom>',
        )
        self.write_docx(document=document)
        scan = scan_docx(self.path)
        self.assertEqual(scan["status"], "not_assessed", scan)
        self.assertIn("unknown_extension_text_unsupported",
                      {row["code"] for row in scan["issues"]})


if __name__ == "__main__":
    unittest.main()
