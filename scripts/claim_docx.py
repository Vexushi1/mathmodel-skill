#!/usr/bin/env python3
"""Bounded, read-only inspection of ordinary DOCX OOXML documents.

The scanner exposes physical package facts for a later B2 carrier adapter.  It
does not decide whether prose or a Figure is semantically sufficient.  Unsafe
package structure is ``blocked``; Word constructs whose rendered text cannot be
recovered faithfully by this small parser are ``not_assessed``.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any, Mapping
import xml.etree.ElementTree as ET
from xml.parsers import expat
import zipfile


MAX_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 2048
MAX_ENTRY_BYTES = 16 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
MATH = "http://schemas.openxmlformats.org/officeDocument/2006/math"
OFFICE_DOCUMENT_REL = f"{R}/officeDocument"
IMAGE_REL = f"{R}/image"
STYLES_REL = f"{R}/styles"
SUPPORTED_IMAGE_CONTENT_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/bmp", "image/tiff",
    "image/svg+xml", "image/x-emf", "image/x-wmf", "image/emf", "image/wmf",
}

W_P = f"{{{W}}}p"
W_R = f"{{{W}}}r"
W_TBL = f"{{{W}}}tbl"
W_TR = f"{{{W}}}tr"
W_TC = f"{{{W}}}tc"
W_T = f"{{{W}}}t"
W_TAB = f"{{{W}}}tab"
W_BR = f"{{{W}}}br"
W_CR = f"{{{W}}}cr"
W_DRAWING = f"{{{W}}}drawing"
W_HYPERLINK = f"{{{W}}}hyperlink"
W_BOOKMARK_START = f"{{{W}}}bookmarkStart"
W_BOOKMARK_END = f"{{{W}}}bookmarkEnd"
A_BLIP = f"{{{A}}}blip"
A_GRAPHIC = f"{{{A}}}graphic"
A_GRAPHIC_DATA = f"{{{A}}}graphicData"
WP_INLINE = f"{{{WP}}}inline"
WP_ANCHOR = f"{{{WP}}}anchor"
WP_EXTENT = f"{{{WP}}}extent"
WP_DOC_PR = f"{{{WP}}}docPr"
PIC_PIC = f"{{{PIC}}}pic"
PIC_NV_PIC_PR = f"{{{PIC}}}nvPicPr"
PIC_BLIP_FILL = f"{{{PIC}}}blipFill"
PIC_SP_PR = f"{{{PIC}}}spPr"
PICTURE_GRAPHIC_URI = "http://schemas.openxmlformats.org/drawingml/2006/picture"

NOT_ASSESSED_TAGS = {
    f"{{{W}}}ins": "tracked_changes_unsupported",
    f"{{{W}}}del": "tracked_changes_unsupported",
    f"{{{W}}}moveFrom": "tracked_changes_unsupported",
    f"{{{W}}}moveTo": "tracked_changes_unsupported",
    f"{{{W}}}moveFromRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}moveFromRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}moveToRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}moveToRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}rPrChange": "tracked_changes_unsupported",
    f"{{{W}}}pPrChange": "tracked_changes_unsupported",
    f"{{{W}}}sectPrChange": "tracked_changes_unsupported",
    f"{{{W}}}tblPrChange": "tracked_changes_unsupported",
    f"{{{W}}}tblGridChange": "tracked_changes_unsupported",
    f"{{{W}}}trPrChange": "tracked_changes_unsupported",
    f"{{{W}}}tcPrChange": "tracked_changes_unsupported",
    f"{{{W}}}numberingChange": "tracked_changes_unsupported",
    f"{{{W}}}cellIns": "tracked_changes_unsupported",
    f"{{{W}}}cellDel": "tracked_changes_unsupported",
    f"{{{W}}}cellMerge": "tracked_changes_unsupported",
    f"{{{W}}}customXmlInsRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}customXmlInsRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}customXmlDelRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}customXmlDelRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}customXmlMoveFromRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}customXmlMoveFromRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}customXmlMoveToRangeStart": "tracked_changes_unsupported",
    f"{{{W}}}customXmlMoveToRangeEnd": "tracked_changes_unsupported",
    f"{{{W}}}fldSimple": "fields_unsupported",
    f"{{{W}}}instrText": "fields_unsupported",
    f"{{{W}}}fldChar": "fields_unsupported",
    f"{{{W}}}altChunk": "altchunk_unsupported",
    f"{{{W}}}txbxContent": "text_box_unsupported",
    f"{{{W}}}sdt": "content_control_unsupported",
    f"{{{W}}}customXml": "custom_xml_unsupported",
    f"{{{W}}}subDoc": "subdocument_unsupported",
    f"{{{W}}}sym": "visible_symbol_unsupported",
    f"{{{W}}}noBreakHyphen": "visible_special_character_unsupported",
    f"{{{W}}}softHyphen": "visible_special_character_unsupported",
    f"{{{W}}}footnoteReference": "note_reference_unsupported",
    f"{{{W}}}endnoteReference": "note_reference_unsupported",
    f"{{{W}}}commentReference": "comment_reference_unsupported",
    f"{{{W}}}ptab": "positional_tab_unsupported",
    f"{{{W}}}numPr": "automatic_numbering_unsupported",
    f"{{{W}}}contentPart": "content_part_unsupported",
    f"{{{W}}}pict": "legacy_drawing_unsupported",
    f"{{{W}}}object": "embedded_object_unsupported",
    f"{{{MATH}}}oMath": "office_math_unsupported",
    f"{{{MATH}}}oMathPara": "office_math_unsupported",
    f"{{{MC}}}AlternateContent": "alternate_content_unsupported",
}


def _issue(code: str, **details: Any) -> dict[str, Any]:
    return {"code": code, **{key: value for key, value in details.items() if value is not None}}


def _safe_member_name(name: str) -> bool:
    """Accept only normalized relative OPC part names."""
    if (not name or "\\" in name or any(char in name for char in "%#?")
            or any(char.isspace() or ord(char) < 0x20 or ord(char) == 0x7f for char in name)
            or name.startswith(("/", "//")) or ":" in name):
        return False
    directory = name.endswith("/")
    candidate = name[:-1] if directory else name
    if not candidate or candidate != PurePosixPath(candidate).as_posix():
        return False
    parts = PurePosixPath(candidate).parts
    return bool(parts) and all(part not in ("", ".", "..") for part in parts)


def _resolve_part(source_part: str | None, target: str) -> str | None:
    if (not target or "\\" in target or any(char in target for char in "%#?")
            or any(char.isspace() or ord(char) < 0x20 or ord(char) == 0x7f for char in target)
            or target.startswith(("/", "//")) or ":" in target):
        return None
    base = posixpath.dirname(source_part) if source_part else ""
    value = posixpath.normpath(posixpath.join(base, target))
    if value in ("", ".", "..") or value.startswith("../") or not _safe_member_name(value):
        return None
    return value


class _ForbiddenXmlDeclaration(Exception):
    """Internal sentinel used to abort Expat before entity expansion."""


def _validate_xml_syntax(payload: bytes, part: str) -> None:
    """Reject DTD/entity declarations in every XML encoding Expat accepts."""
    parser = expat.ParserCreate()

    def reject(*_args: Any) -> None:
        raise _ForbiddenXmlDeclaration

    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    try:
        parser.Parse(payload, True)
    except _ForbiddenXmlDeclaration as exc:
        raise ValueError(f"DTD/entity declarations are unsupported in {part}") from exc
    except expat.ExpatError as exc:
        raise ValueError(f"malformed XML in {part}: {exc}") from exc


def _parse_xml(payload: bytes, part: str) -> ET.Element:
    # Every XML part is bounded before this helper is called.  Expat performs
    # encoding-aware declaration rejection; the second parse builds the tree.
    _validate_xml_syntax(payload, part)
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError(f"malformed XML in {part}: {exc}") from exc


def _relationships(payload: bytes, *, source_part: str | None, part: str) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    root = _parse_xml(payload, part)
    relationships: dict[str, dict[str, str]] = {}
    issues: list[dict[str, Any]] = []
    expected = f"{{{PKG_REL}}}Relationships"
    if root.tag != expected:
        return {}, [_issue("malformed_relationships_root", part=part)]
    for node in root:
        if node.tag != f"{{{PKG_REL}}}Relationship":
            continue
        rel_id = node.attrib.get("Id", "")
        rel_type = node.attrib.get("Type", "")
        target = node.attrib.get("Target", "")
        mode = node.attrib.get("TargetMode", "Internal")
        if not rel_id or rel_id in relationships:
            issues.append(_issue("duplicate_or_missing_relationship_id", part=part, relationship_id=rel_id or None))
            continue
        if len(rel_id) > 256 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9._-]*", rel_id):
            issues.append(_issue("invalid_relationship_id", part=part,
                                 relationship_id=rel_id))
            continue
        if mode not in {"Internal", "External"}:
            issues.append(_issue("invalid_relationship_target_mode", part=part,
                                 relationship_id=rel_id, target_mode=mode))
            continue
        if mode == "External":
            issues.append(_issue("external_relationship_unsupported", part=part,
                                 relationship_id=rel_id, target=target))
            relationships[rel_id] = {"type": rel_type, "target": target, "mode": "External"}
            continue
        resolved = _resolve_part(source_part, target)
        if resolved is None:
            issues.append(_issue("relationship_target_outside_package", part=part,
                                 relationship_id=rel_id, target=target))
            continue
        relationships[rel_id] = {"type": rel_type, "target": resolved, "mode": "Internal"}
    return relationships, issues


def _rels_part_for(source_part: str) -> str:
    directory, name = posixpath.split(source_part)
    return posixpath.join(directory, "_rels", name + ".rels") if directory else f"_rels/{name}.rels"


def _read_bounded_file(path: Path, limit: int) -> bytes:
    """Read at most ``limit`` bytes and reject a changed/oversized source."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("DOCX path must be a regular non-symlink file")
    if path.stat().st_size > limit:
        raise ValueError("DOCX package byte budget exceeded")
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
        if len(payload) > limit or handle.read(1):
            raise ValueError("DOCX package byte budget exceeded")
    return payload


def _sha256_bounded_file(path: Path, limit: int) -> str:
    """Hash a current regular file without allocating beyond the byte budget."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("DOCX path must remain a regular non-symlink file")
    if path.stat().st_size > limit:
        raise ValueError("DOCX package byte budget exceeded during recheck")
    digest = hashlib.sha256()
    observed = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            observed += len(chunk)
            if observed > limit:
                raise ValueError("DOCX package byte budget exceeded during recheck")
            digest.update(chunk)
    return digest.hexdigest()


HIDDEN_TEXT_TAGS = {
    f"{{{W}}}vanish", f"{{{W}}}webHidden", f"{{{W}}}specVanish",
}


def _on_off_enabled(node: ET.Element) -> bool:
    value = node.attrib.get(f"{{{W}}}val")
    return value is None or value.strip().lower() not in {"0", "false", "off", "no"}


def _bookmark_id(value: str) -> str | None:
    """Return the canonical ST_DecimalNumber identity for a bounded lexical value."""
    if not value or len(value) > 64 or not re.fullmatch(r"[+-]?[0-9]+", value):
        return None
    return str(int(value, 10))


def _paragraph_for_offset(paragraphs: list[dict[str, Any]], offset: int, *, end: bool = False) -> dict[str, Any] | None:
    if not paragraphs:
        return None
    for paragraph in paragraphs:
        if paragraph["start"] <= offset < paragraph["end"]:
            return paragraph
        if not end and offset == paragraph["end"] and paragraph["start"] == paragraph["end"]:
            return paragraph
    if end and offset == paragraphs[-1]["end"]:
        return paragraphs[-1]
    return next((row for row in paragraphs if row["start"] > offset), paragraphs[-1])


def _drawing_structure_issues(body: ET.Element, part: str) -> list[dict[str, Any]]:
    """Admit only one explicit DrawingML picture source per w:drawing."""
    issues: list[dict[str, Any]] = []
    valid_blips: set[int] = set()
    for drawing in body.iter(W_DRAWING):
        alternate = False
        containers = [child for child in drawing if child.tag in {WP_INLINE, WP_ANCHOR}]
        valid = len(containers) == 1
        container = containers[0] if valid else None
        if container is not None:
            valid &= (container.find(WP_EXTENT) is not None
                      and container.find(WP_DOC_PR) is not None)
            graphics = [child for child in container if child.tag == A_GRAPHIC]
            valid &= len(graphics) == 1
        else:
            graphics = []
        if valid:
            graphic_data = [child for child in graphics[0] if child.tag == A_GRAPHIC_DATA]
            valid &= (len(graphic_data) == 1
                      and graphic_data[0].attrib.get("uri") == PICTURE_GRAPHIC_URI)
        else:
            graphic_data = []
        if valid:
            pictures = [child for child in graphic_data[0] if child.tag == PIC_PIC]
            valid &= len(pictures) == 1
        else:
            pictures = []
        if valid:
            picture = pictures[0]
            fills = [child for child in picture if child.tag == PIC_BLIP_FILL]
            valid &= (picture.find(PIC_NV_PIC_PR) is not None
                      and picture.find(PIC_SP_PR) is not None
                      and len(fills) == 1)
        else:
            fills = []
        if valid:
            blips = [child for child in fills[0] if child.tag == A_BLIP]
            valid &= (len(blips) == 1
                      and isinstance(blips[0].attrib.get(f"{{{R}}}embed"), str)
                      and not blips[0].attrib.get(f"{{{R}}}link"))
        else:
            blips = []
        if valid:
            blip = blips[0]
            valid &= list(drawing.iter(A_BLIP)) == [blip]
            alternate = any(
                node is not blip
                and any(key in node.attrib for key in (f"{{{R}}}embed", f"{{{R}}}link"))
                for node in drawing.iter()
            )
            if alternate:
                issues.append(_issue("alternate_image_representation_unsupported", part=part))
                valid = False
        if valid:
            valid_blips.add(id(blips[0]))
        elif not alternate:
            issues.append(_issue("non_image_drawing_unsupported", part=part))
    for blip in body.iter(A_BLIP):
        if id(blip) not in valid_blips:
            issues.append(_issue("misnested_image_blip_unsupported", part=part))
    return issues


def _flatten_document(root: ET.Element, relationships: Mapping[str, Mapping[str, str]]) -> tuple[
        str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
        list[dict[str, Any]], list[dict[str, Any]]]:
    if root.tag != f"{{{W}}}document":
        return "", [], [], [], [_issue("malformed_document_root", part="word/document.xml")]
    body = root.find(f"{{{W}}}body")
    if body is None:
        return "", [], [], [], [_issue("document_body_missing", part="word/document.xml")]

    issues: list[dict[str, Any]] = []
    unsupported_seen: set[tuple[str, int]] = set()
    parents = {child: parent for parent in body.iter() for child in parent}
    for node in body.iter():
        if node.tag == W_P:
            cursor = node
            path: list[str] = []
            while cursor is not body and cursor in parents:
                path.append(cursor.tag)
                cursor = parents[cursor]
            if cursor is not body:
                issues.append(_issue("misnested_paragraph_unsupported",
                                     part="word/document.xml"))
                continue
            path.reverse()
            previous = f"{{{W}}}body"
            transitions = {
                f"{{{W}}}body": {W_P, W_TBL},
                W_TBL: {W_TR},
                W_TR: {W_TC},
                W_TC: {W_P, W_TBL},
            }
            for tag in path:
                if tag not in transitions.get(previous, set()):
                    issues.append(_issue("misnested_paragraph_unsupported",
                                         part="word/document.xml"))
                    break
                previous = tag
        elif node.tag in {W_T, W_TAB, W_BR, W_CR}:
            cursor = parents.get(node)
            while cursor is not None and cursor is not body and cursor.tag != W_P:
                cursor = parents.get(cursor)
            if cursor is body or cursor is None:
                issues.append(_issue("orphan_text_unsupported",
                                     part="word/document.xml"))
    for node in body.iter():
        code = NOT_ASSESSED_TAGS.get(node.tag)
        if code and (code, id(node)) not in unsupported_seen:
            unsupported_seen.add((code, id(node)))
            issues.append(_issue(code, part="word/document.xml"))
        namespace = node.tag[1:].partition("}")[0] if node.tag.startswith("{") else ""
        if (namespace not in {W, A}
                and any(descendant.tag in {W_P, W_T} for descendant in node.iter()
                        if descendant is not node)
                and ("unknown_extension_text_unsupported", id(node)) not in unsupported_seen):
            unsupported_seen.add(("unknown_extension_text_unsupported", id(node)))
            issues.append(_issue("unknown_extension_text_unsupported",
                                 part="word/document.xml", namespace=namespace or None))

    paragraphs: list[dict[str, Any]] = []
    bookmark_starts: dict[str, dict[str, Any]] = {}
    bookmark_names: set[str] = set()
    bookmarks: list[dict[str, Any]] = []
    bookmark_ids_seen: set[str] = set()
    bookmark_stack: list[str] = []
    image_events: list[dict[str, Any]] = []
    hyperlinks: list[dict[str, Any]] = []
    chunks: list[str] = []
    global_offset = 0
    event_order = [0]

    def walk(node: ET.Element, local_chunks: list[str], local_length: list[int],
             paragraph_index: int, ancestors: tuple[str, ...] = ()) -> None:
        event_order[0] += 1
        node_order = event_order[0]
        local_offset = local_length[0]
        if node.tag == W_P and ancestors:
            issues.append(_issue("misnested_paragraph_unsupported",
                                 part="word/document.xml",
                                 paragraph=paragraph_index))
            return
        if node.tag == W_HYPERLINK:
            start = global_offset + local_offset
            for child in node:
                walk(child, local_chunks, local_length, paragraph_index,
                     ancestors + (node.tag,))
            end = global_offset + local_length[0]
            hyperlinks.append({
                "anchor": node.attrib.get(f"{{{W}}}anchor"),
                "relationship_id": node.attrib.get(f"{{{R}}}id"),
                "start": start, "end": end, "paragraph": paragraph_index,
            })
            return
        if node.tag == W_BOOKMARK_START:
            raw_bookmark_id = node.attrib.get(f"{{{W}}}id", "")
            bookmark_id = _bookmark_id(raw_bookmark_id)
            name = node.attrib.get(f"{{{W}}}name", "")
            if (bookmark_id is None or not name or bookmark_id in bookmark_ids_seen
                    or name in bookmark_names):
                issues.append(_issue("damaged_bookmark_start", part="word/document.xml",
                                     paragraph=paragraph_index,
                                     bookmark_id=raw_bookmark_id or None,
                                     bookmark=name or None))
            else:
                bookmark_starts[bookmark_id] = {
                    "name": name, "id": bookmark_id, "start": global_offset + local_offset,
                    "start_paragraph": paragraph_index, "start_order": node_order,
                }
                bookmark_ids_seen.add(bookmark_id)
                bookmark_names.add(name)
                bookmark_stack.append(bookmark_id)
        elif node.tag == W_BOOKMARK_END:
            raw_bookmark_id = node.attrib.get(f"{{{W}}}id", "")
            bookmark_id = _bookmark_id(raw_bookmark_id)
            start = bookmark_starts.pop(bookmark_id, None) if bookmark_id is not None else None
            if start is None:
                issues.append(_issue("damaged_bookmark_end", part="word/document.xml",
                                     paragraph=paragraph_index,
                                     bookmark_id=raw_bookmark_id or None))
            else:
                if not bookmark_stack or bookmark_stack[-1] != bookmark_id:
                    issues.append(_issue("crossed_bookmark_range", part="word/document.xml",
                                         paragraph=paragraph_index, bookmark_id=bookmark_id,
                                         bookmark=start["name"]))
                    if bookmark_id in bookmark_stack:
                        bookmark_stack.remove(bookmark_id)
                else:
                    bookmark_stack.pop()
                bookmarks.append({**start, "end": global_offset + local_offset,
                                  "end_paragraph": paragraph_index, "end_order": node_order})
        elif node.tag in {W_T, W_TAB, W_BR, W_CR} and not (
                ancestors and ancestors[-1] == W_R
                and (len(ancestors) >= 2 and ancestors[-2] == W_P
                     or len(ancestors) >= 3 and ancestors[-2] == W_HYPERLINK
                     and ancestors[-3] == W_P)):
            issues.append(_issue("misnested_text_unsupported",
                                 part="word/document.xml",
                                 paragraph=paragraph_index))
        elif node.tag == W_T:
            value = node.text or ""
            local_chunks.append(value)
            local_length[0] += len(value)
        elif node.tag == W_TAB:
            local_chunks.append("\t")
            local_length[0] += 1
        elif node.tag in {W_BR, W_CR}:
            local_chunks.append("\n")
            local_length[0] += 1
        elif node.tag == A_BLIP:
            embedded = node.attrib.get(f"{{{R}}}embed")
            linked = node.attrib.get(f"{{{R}}}link")
            if linked:
                issues.append(_issue("external_image_link_unsupported", part="word/document.xml",
                                     paragraph=paragraph_index, relationship_id=linked))
            if embedded:
                image_events.append({"relationship_id": embedded,
                                     "offset": global_offset + local_offset,
                                     "paragraph": paragraph_index, "order": node_order})
        elif node.tag in HIDDEN_TEXT_TAGS and _on_off_enabled(node):
            issues.append(_issue("hidden_text_unsupported", part="word/document.xml",
                                 paragraph=paragraph_index))
        for child in node:
            walk(child, local_chunks, local_length, paragraph_index,
                 ancestors + (node.tag,))

    # ElementTree preserves document order.  Body-level tables contribute their
    # cell paragraphs in the same order as Word's logical reading stream.
    for paragraph_node in body.iter(W_P):
        paragraph_index = len(paragraphs) + 1
        local_chunks: list[str] = []
        walk(paragraph_node, local_chunks, [0], paragraph_index)
        value = "".join(local_chunks)
        start = global_offset
        end = start + len(value)
        paragraph_images = [row["relationship_id"] for row in image_events
                            if row["paragraph"] == paragraph_index]
        if any(0 < row["offset"] - global_offset < len(value)
               for row in image_events if row["paragraph"] == paragraph_index):
            issues.append(_issue("inline_drawing_splits_text_unsupported",
                                 part="word/document.xml", paragraph=paragraph_index))
        paragraphs.append({"index": paragraph_index, "part": "word/document.xml",
                           "start": start, "end": end, "text": value,
                           "image_relationship_ids": paragraph_images})
        chunks.append(value)
        global_offset = end
        # A single LF is the normalized separator; it is not a raw OOXML byte offset.
        chunks.append("\n")
        global_offset += 1

    if chunks:
        chunks.pop()
        global_offset -= 1
    text = "".join(chunks)
    for bookmark_id, start in sorted(bookmark_starts.items()):
        issues.append(_issue("unclosed_bookmark", part="word/document.xml",
                             bookmark_id=bookmark_id, bookmark=start["name"]))
    for bookmark in bookmarks:
        bookmark["text"] = text[bookmark["start"]:bookmark["end"]]
        bookmark["image_relationship_ids"] = sorted([
            row["relationship_id"] for row in image_events
            if bookmark["start_order"] < row["order"] < bookmark["end_order"]
        ])
    known = set(relationships)
    for event in image_events:
        if event["relationship_id"] not in known:
            issues.append(_issue("image_relationship_missing", part="word/document.xml",
                                 paragraph=event["paragraph"],
                                 relationship_id=event["relationship_id"]))
    for hyperlink in hyperlinks:
        hyperlink["text"] = text[hyperlink["start"]:hyperlink["end"]]
    return (text, paragraphs,
            sorted(bookmarks, key=lambda row: (row["start"], row["name"])),
            image_events, hyperlinks, issues)


def scan_docx(
    path: str | Path,
    *,
    max_package_bytes: int = MAX_PACKAGE_BYTES,
    max_entries: int = MAX_ENTRIES,
    max_entry_bytes: int = MAX_ENTRY_BYTES,
    max_total_uncompressed_bytes: int = MAX_TOTAL_UNCOMPRESSED_BYTES,
    max_compression_ratio: int = MAX_COMPRESSION_RATIO,
) -> dict[str, Any]:
    """Inspect one DOCX package without extracting files or executing content."""
    source = Path(path).expanduser()
    report: dict[str, Any] = {
        "status": "blocked", "path": str(source), "sha256": None,
        "scope": "main_document_body_only_normalized_ooxml_text",
        "text": "", "paragraphs": [], "bookmarks": [], "hyperlinks": [],
        "images": [], "issues": [],
    }
    try:
        if source.suffix.lower() != ".docx":
            raise ValueError("DOCX scanner requires a .docx file")
        raw = _read_bounded_file(source, max_package_bytes)
        report["sha256"] = hashlib.sha256(raw).hexdigest()
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(infos) > max_entries:
                raise ValueError("DOCX ZIP entry budget exceeded")
            if len(names) != len(set(names)):
                raise ValueError("DOCX ZIP contains duplicate entry names")
            if any(not _safe_member_name(name) for name in names):
                raise ValueError("DOCX ZIP contains an unsafe or non-normalized entry path")
            total = 0
            for info in infos:
                if info.flag_bits & 0x1:
                    raise ValueError("encrypted DOCX ZIP entries are unsupported")
                if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ValueError("unsupported DOCX ZIP compression method")
                if info.file_size > max_entry_bytes:
                    raise ValueError("DOCX ZIP entry byte budget exceeded")
                total += info.file_size
                if total > max_total_uncompressed_bytes:
                    raise ValueError("DOCX total uncompressed byte budget exceeded")
                if info.file_size > 0 and info.compress_size == 0:
                    raise ValueError("invalid DOCX ZIP compression sizes")
                if info.compress_size and info.file_size > info.compress_size * max_compression_ratio:
                    raise ValueError("DOCX ZIP compression ratio budget exceeded")
            members = set(names)
            required = {"[Content_Types].xml", "_rels/.rels"}
            missing = sorted(required - members)
            if missing:
                raise ValueError("DOCX package is missing required OPC parts: " + ", ".join(missing))
            # Reject declarations across the complete bounded XML package, not
            # only parts consumed below.  This check is encoding aware, so a
            # UTF-16/UTF-32 declaration cannot evade an ASCII byte search.
            for name in sorted(names):
                if not (name.lower().endswith(".xml") or name.lower().endswith(".rels")):
                    continue
                _validate_xml_syntax(archive.read(name), name)
            content_types = _parse_xml(archive.read("[Content_Types].xml"),
                                       "[Content_Types].xml")
            if content_types.tag != f"{{{CONTENT_TYPES}}}Types":
                raise ValueError("DOCX package has a malformed content-types root")

            # Reject external relationships anywhere in the package, rather than
            # checking only hyperlinks reachable from the main document.
            parsed_rels: dict[str, dict[str, dict[str, str]]] = {}
            for rels_part in sorted(name for name in names if name.endswith(".rels")):
                if rels_part == "_rels/.rels":
                    source_part = None
                else:
                    directory, rel_name = posixpath.split(rels_part)
                    if not directory.endswith("/_rels") or not rel_name.endswith(".rels"):
                        raise ValueError(f"unsupported relationship part path: {rels_part}")
                    source_part = posixpath.join(directory[:-6], rel_name[:-5]).lstrip("/")
                rels, rel_issues = _relationships(archive.read(rels_part), source_part=source_part,
                                                  part=rels_part)
                if rel_issues:
                    report["issues"].extend(rel_issues)
                parsed_rels[rels_part] = rels

            root_rels = parsed_rels.get("_rels/.rels", {})
            office = [row for row in root_rels.values()
                      if row.get("type") == OFFICE_DOCUMENT_REL]
            if len(office) != 1 or office[0].get("mode") != "Internal":
                raise ValueError("DOCX package requires one internal officeDocument relationship")
            document_part = office[0]["target"]
            if document_part not in members:
                raise ValueError("DOCX officeDocument part is missing")
            document_types = [
                node.attrib.get("ContentType")
                for node in content_types
                if (node.tag == f"{{{CONTENT_TYPES}}}Override"
                    and node.attrib.get("PartName") == "/" + document_part)
            ]
            expected_document_type = (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document.main+xml"
            )
            if document_types != [expected_document_type]:
                raise ValueError("DOCX main document content type is absent, ambiguous or unsupported")
            document_rels_part = _rels_part_for(document_part)
            document_rels = parsed_rels.get(document_rels_part, {})
            style_relationships = [
                row for row in document_rels.values()
                if row.get("mode") == "Internal" and row.get("type") == STYLES_REL
            ]
            if len(style_relationships) > 1:
                report["issues"].append(_issue("ambiguous_styles_relationship",
                                                part=document_rels_part))
            for relationship in style_relationships:
                style_part = relationship["target"]
                if style_part not in members:
                    report["issues"].append(_issue("styles_part_missing", package_part=style_part))
                    continue
                styles = _parse_xml(archive.read(style_part), style_part)
                if styles.tag != f"{{{W}}}styles":
                    report["issues"].append(_issue("malformed_styles_root", part=style_part))
                    continue
                if any(node.tag in HIDDEN_TEXT_TAGS and _on_off_enabled(node)
                       for node in styles.iter()):
                    report["issues"].append(_issue("hidden_style_text_unsupported",
                                                    part=style_part))
                if any(node.tag == f"{{{W}}}numPr" for node in styles.iter()):
                    report["issues"].append(_issue("automatic_numbering_unsupported",
                                                    part=style_part))
            document = _parse_xml(archive.read(document_part), document_part)
            body = document.find(f"{{{W}}}body")
            if body is not None:
                report["issues"].extend(_drawing_structure_issues(body, document_part))
            (text, paragraphs, bookmarks, image_events, hyperlinks,
             doc_issues) = _flatten_document(document, document_rels)
            report.update(text=text, paragraphs=paragraphs, bookmarks=bookmarks,
                          hyperlinks=hyperlinks)
            report["issues"].extend(doc_issues)

            used_image_ids = sorted({row["relationship_id"] for row in image_events})
            images: list[dict[str, Any]] = []
            for rel_id in used_image_ids:
                relationship = document_rels.get(rel_id)
                if not relationship:
                    continue
                if relationship.get("mode") != "Internal" or relationship.get("type") != IMAGE_REL:
                    report["issues"].append(_issue("drawing_relationship_is_not_internal_image",
                                                    relationship_id=rel_id))
                    continue
                target = relationship["target"]
                if target not in members:
                    report["issues"].append(_issue("image_media_part_missing",
                                                    relationship_id=rel_id, package_part=target))
                    continue
                overrides = [
                    node.attrib.get("ContentType") for node in content_types
                    if (node.tag == f"{{{CONTENT_TYPES}}}Override"
                        and node.attrib.get("PartName") == "/" + target)
                ]
                extension = PurePosixPath(target).suffix.lstrip(".").lower()
                defaults = [
                    node.attrib.get("ContentType") for node in content_types
                    if (node.tag == f"{{{CONTENT_TYPES}}}Default"
                        and str(node.attrib.get("Extension", "")).lower() == extension)
                ]
                image_types = overrides if overrides else defaults
                if len(image_types) != 1 or image_types[0] not in SUPPORTED_IMAGE_CONTENT_TYPES:
                    report["issues"].append(_issue(
                        "image_content_type_unsupported", relationship_id=rel_id,
                        package_part=target, content_types=image_types,
                    ))
                    continue
                payload = archive.read(target)
                images.append({"relationship_id": rel_id, "package_part": target,
                               "sha256": hashlib.sha256(payload).hexdigest(),
                               "size": len(payload)})
            report["images"] = images

        if _sha256_bounded_file(source, max_package_bytes) != report["sha256"]:
            raise ValueError("DOCX bytes changed during scan")
        blocked_codes = {
            "malformed_relationships_root", "duplicate_or_missing_relationship_id",
            "invalid_relationship_id",
            "invalid_relationship_target_mode",
            "external_relationship_unsupported", "relationship_target_outside_package",
            "malformed_document_root", "document_body_missing",
            "damaged_bookmark_start", "damaged_bookmark_end",
            "unclosed_bookmark", "crossed_bookmark_range",
            "external_image_link_unsupported",
            "image_relationship_missing", "drawing_relationship_is_not_internal_image",
            "image_media_part_missing", "image_content_type_unsupported",
            "ambiguous_styles_relationship",
            "styles_part_missing", "malformed_styles_root",
        }
        not_assessed_codes = set(NOT_ASSESSED_TAGS.values()) | {
            "hidden_text_unsupported", "hidden_style_text_unsupported",
            "inline_drawing_splits_text_unsupported", "unknown_extension_text_unsupported",
            "misnested_paragraph_unsupported", "misnested_text_unsupported",
            "orphan_text_unsupported",
            "non_image_drawing_unsupported", "misnested_image_blip_unsupported",
            "alternate_image_representation_unsupported",
        }
        codes = {row["code"] for row in report["issues"]}
        report["status"] = (
            "blocked" if codes & blocked_codes else
            "not_assessed" if codes & not_assessed_codes else
            "scanned"
        )
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, OverflowError) as exc:
        report["status"] = "blocked"
        report["issues"].append(_issue("docx_scan_failed", detail=str(exc)[:4096]))
    return report


def locate_literal_anchor(scan: Mapping[str, Any], anchor: str) -> dict[str, Any]:
    """Locate one literal anchor in normalized main-document text."""
    result: dict[str, Any] = {"status": "not_assessed", "anchor": anchor}
    if scan.get("status") != "scanned":
        result["reason"] = "DOCX scan is not fully assessed"
        return result
    if not isinstance(anchor, str) or not anchor:
        result["reason"] = "anchor must be a nonempty literal string"
        return result
    text = scan.get("text")
    paragraphs = scan.get("paragraphs")
    if not isinstance(text, str) or not isinstance(paragraphs, list):
        result["reason"] = "DOCX scan result is malformed"
        return result
    hits: list[int] = []
    cursor = 0
    while True:
        found = text.find(anchor, cursor)
        if found < 0:
            break
        hits.append(found)
        cursor = found + max(1, len(anchor))
        if len(hits) > 1:
            break
    if len(hits) != 1:
        result["reason"] = "anchor is absent or ambiguous in normalized DOCX body text"
        result["match_count"] = len(hits)
        return result
    start = hits[0]
    finish = start + len(anchor)
    first = _paragraph_for_offset(paragraphs, start)
    last = _paragraph_for_offset(paragraphs, finish, end=True)
    if first is None or last is None:
        result["reason"] = "anchor location is outside normalized DOCX paragraphs"
        return result
    result.update(status="located", part=first["part"], offset=start,
                  end_offset=finish, paragraph=first["index"],
                  paragraph_end=last["index"], char_offset=start - first["start"])
    return result


def bind_bookmark_figure(scan: Mapping[str, Any], bookmark: str, caption_anchor: str) -> dict[str, Any]:
    """Bind one named bookmark to one embedded image and one literal caption."""
    result: dict[str, Any] = {"status": "not_assessed", "bookmark": bookmark,
                              "caption_anchor": caption_anchor}
    if scan.get("status") != "scanned":
        result["reason"] = "DOCX scan is not fully assessed"
        return result
    if not bookmark or not caption_anchor:
        result["reason"] = "bookmark and caption_anchor must be nonempty literals"
        return result
    rows = [row for row in scan.get("bookmarks", []) if row.get("name") == bookmark]
    if len(rows) != 1:
        result["reason"] = "bookmark is absent or ambiguous"
        result["match_count"] = len(rows)
        return result
    row = rows[0]
    caption_hits = row.get("text", "").count(caption_anchor)
    if caption_hits != 1:
        result["reason"] = "caption anchor is absent or ambiguous inside the bookmark"
        result["caption_match_count"] = caption_hits
        return result
    relationship_ids = row.get("image_relationship_ids", [])
    if len(relationship_ids) != 1:
        result["reason"] = "bookmark must contain exactly one embedded image"
        result["image_count"] = len(relationship_ids)
        return result
    rel_id = relationship_ids[0]
    images = [image for image in scan.get("images", []) if image.get("relationship_id") == rel_id]
    if len(images) != 1:
        result["reason"] = "bookmark image relationship has no unique current media part"
        return result
    image = images[0]
    result.update(status="matched", part="word/document.xml", start=row["start"],
                  end=row["end"], start_paragraph=row["start_paragraph"],
                  end_paragraph=row["end_paragraph"], relationship_id=rel_id,
                  package_part=image["package_part"], image_sha256=image["sha256"],
                  image_size=image["size"])
    return result
