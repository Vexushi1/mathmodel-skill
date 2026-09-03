#!/usr/bin/env python3
"""Validate draw.io structure, geometry, safety, and review readiness only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_mechanism_drawio import SpecError, canonical_spec_sha256, validate_spec  # noqa: E402


SEVERITIES = ("blocking", "review_required", "warning")
EXTERNAL_MARKERS = ("http://", "https://", "data:image", "javascript:", "vbscript:", "file://")
PLACEHOLDER_RE = re.compile(r"^(?:节点\s*\d+|input|model|output|todo|tbd|输入|模型|输出)$", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    element_id: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"invalid finding severity: {self.severity}")


@dataclass(frozen=True)
class Box:
    element_id: str
    x: float
    y: float
    width: float
    height: float
    is_group: bool
    label: str
    style: str

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in style.split(";"):
        if "=" in token:
            key, value = token.split("=", 1)
            result[key] = value
    return result


def _graph_models(root: ET.Element) -> list[ET.Element]:
    if root.tag == "mxGraphModel":
        return [root]
    return list(root.findall("./diagram/mxGraphModel"))


def _cell_boxes(cells: Iterable[ET.Element]) -> list[Box]:
    boxes: list[Box] = []
    for cell in cells:
        if cell.attrib.get("vertex") != "1":
            continue
        geometry = cell.find("mxGeometry")
        if geometry is None:
            continue
        style = cell.attrib.get("style", "")
        style_data = _style_map(style)
        boxes.append(Box(
            element_id=cell.attrib.get("id", ""),
            x=_float(geometry.attrib.get("x")),
            y=_float(geometry.attrib.get("y")),
            width=_float(geometry.attrib.get("width")),
            height=_float(geometry.attrib.get("height")),
            is_group=cell.attrib.get("hskKind") == "group" or style_data.get("container") == "1" or style.startswith("swimlane"),
            label=cell.attrib.get("value", ""),
            style=style,
        ))
    return boxes


def _overlap_area(first: Box, second: Box) -> float:
    width = max(0.0, min(first.right, second.right) - max(first.x, second.x))
    height = max(0.0, min(first.bottom, second.bottom) - max(first.y, second.y))
    return width * height


def _point_inside(box: Box, point: tuple[float, float], *, margin: float = 3.0) -> bool:
    x, y = point
    return box.x + margin < x < box.right - margin and box.y + margin < y < box.bottom - margin


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    first = _orientation(a, b, c)
    second = _orientation(a, b, d)
    third = _orientation(c, d, a)
    fourth = _orientation(c, d, b)
    return (first > 0 > second or second > 0 > first) and (third > 0 > fourth or fourth > 0 > third)


def _segment_crosses_box(start: tuple[float, float], end: tuple[float, float], box: Box) -> bool:
    if _point_inside(box, start) or _point_inside(box, end):
        return True
    corners = (
        (box.x + 3, box.y + 3),
        (box.right - 3, box.y + 3),
        (box.right - 3, box.bottom - 3),
        (box.x + 3, box.bottom - 3),
    )
    return any(
        _segments_intersect(start, end, corners[index], corners[(index + 1) % 4])
        for index in range(4)
    )


def _edge_points(cell: ET.Element, boxes: Mapping[str, Box]) -> list[tuple[float, float]]:
    source = boxes.get(cell.attrib.get("source", ""))
    target = boxes.get(cell.attrib.get("target", ""))
    if source is None or target is None:
        return []
    points: list[tuple[float, float]] = [source.center]
    geometry = cell.find("mxGeometry")
    if geometry is not None:
        array = geometry.find("Array[@as='points']")
        if array is not None:
            for point in array.findall("mxPoint"):
                points.append((_float(point.attrib.get("x")), _float(point.attrib.get("y"))))
    points.append(target.center)
    return points


def _label_extent(label: str, font_size: float) -> tuple[float, float]:
    lines = label.replace("<br>", "\n").replace("<br/>", "\n").splitlines() or [""]
    widths = []
    for line in lines:
        units = sum(1.0 if ord(char) > 127 else 0.56 for char in line)
        widths.append(units * font_size)
    return max(widths, default=0.0), len(lines) * font_size * 1.35


def _project_root_from_spec(spec_path: Path) -> Path | None:
    resolved = spec_path.resolve()
    parts = resolved.parts
    try:
        index = parts.index("figures")
    except ValueError:
        return None
    return Path(*parts[:index])


def _preview_format_is_valid(path: Path, data: bytes) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix == ".pdf":
        return data.startswith(b"%PDF-")
    if suffix == ".svg":
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return False
        return root.tag.rsplit("}", 1)[-1].lower() == "svg"
    return False


def validate_drawio_bytes(
    xml_bytes: bytes,
    *,
    spec: Mapping[str, Any] | None = None,
    spec_path: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        return [Finding("blocking", "xml_parse_error", f"draw.io XML cannot be parsed: {exc}")]

    models = _graph_models(root)
    if len(models) != 1:
        diagrams = root.findall("./diagram") if root.tag == "mxfile" else []
        code = "compressed_payload" if diagrams and not models else "graph_model_count"
        return [Finding("blocking", code, "v1 requires exactly one uncompressed mxGraphModel")]
    model = models[0]
    cells = list(model.iter("mxCell"))
    ids = [cell.attrib.get("id", "") for cell in cells]
    empty_ids = [item for item in ids if not item]
    if empty_ids:
        findings.append(Finding("blocking", "empty_cell_id", "every mxCell must have a non-empty id"))
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            findings.append(Finding("blocking", "duplicate_cell_id", f"duplicate mxCell id: {item_id}", item_id or None))
        seen.add(item_id)

    serialized = xml_bytes.decode("utf-8", errors="replace").lower()
    if any(marker in serialized for marker in EXTERNAL_MARKERS) or re.search(r"(?:^|;)image=", serialized):
        findings.append(Finding("blocking", "external_resource", "embedded images, URLs, scripts, and external resources are forbidden"))

    cell_map = {cell.attrib.get("id", ""): cell for cell in cells if cell.attrib.get("id")}
    for cell in cells:
        if cell.attrib.get("edge") != "1":
            continue
        edge_id = cell.attrib.get("id")
        for endpoint in ("source", "target"):
            endpoint_id = cell.attrib.get(endpoint, "")
            if not endpoint_id or endpoint_id not in cell_map:
                findings.append(Finding("blocking", "missing_edge_endpoint", f"edge {edge_id} has unknown {endpoint}: {endpoint_id}", edge_id))

    page_width = _float(model.attrib.get("pageWidth"))
    page_height = _float(model.attrib.get("pageHeight"))
    if page_width <= 0 or page_height <= 0:
        findings.append(Finding("blocking", "invalid_canvas", "mxGraphModel requires positive pageWidth and pageHeight"))
    boxes = _cell_boxes(cells)
    box_map = {box.element_id: box for box in boxes}
    entities = [box for box in boxes if not box.is_group]
    for box in boxes:
        if box.width <= 0 or box.height <= 0:
            findings.append(Finding("blocking", "invalid_geometry", "vertex width and height must be positive", box.element_id))
        if box.x < 0 or box.y < 0 or box.right > page_width or box.bottom > page_height:
            findings.append(Finding("blocking", "out_of_canvas", "vertex lies outside the declared canvas", box.element_id))
        if not box.label.strip():
            findings.append(Finding("warning", "empty_label", "vertex label is empty", box.element_id))
        if PLACEHOLDER_RE.fullmatch(box.label.strip()):
            findings.append(Finding("review_required", "placeholder_label", "vertex contains an unresolved generic placeholder", box.element_id))
        font_size = _float(_style_map(box.style).get("fontSize"), 14.0)
        label_width, label_height = _label_extent(box.label, font_size)
        if label_width > max(0.0, box.width - 16) or label_height > max(0.0, box.height - 10):
            findings.append(Finding("blocking", "text_overflow", "label deterministically exceeds the vertex text area", box.element_id))
        elif font_size < 10:
            findings.append(Finding("review_required", "font_too_small", "font may be unreadable at paper scale", box.element_id))

    for index, first in enumerate(entities):
        for second in entities[index + 1:]:
            area = _overlap_area(first, second)
            threshold = max(9.0, 0.03 * min(first.width * first.height, second.width * second.height))
            if area > threshold:
                findings.append(Finding("blocking", "entity_overlap", f"entities overlap materially: {first.element_id}, {second.element_id}"))

    for cell in cells:
        if cell.attrib.get("edge") != "1":
            continue
        edge_id = cell.attrib.get("id", "")
        points = _edge_points(cell, box_map)
        if len(points) < 2:
            continue
        geometry = cell.find("mxGeometry")
        explicit_points = geometry.find("Array[@as='points']") if geometry is not None else None
        style = _style_map(cell.attrib.get("style", ""))
        if explicit_points is None and style.get("edgeStyle") == "orthogonalEdgeStyle":
            continue
        endpoints = {cell.attrib.get("source"), cell.attrib.get("target")}
        for box in entities:
            if box.element_id in endpoints:
                continue
            if any(_segment_crosses_box(points[index], points[index + 1], box) for index in range(len(points) - 1)):
                findings.append(Finding("blocking", "connector_crosses_entity", f"edge crosses unrelated entity {box.element_id}", edge_id))

    font_sizes = {
        _style_map(box.style).get("fontSize", "") for box in boxes if _style_map(box.style).get("fontSize")
    }
    fill_colors = {
        _style_map(box.style).get("fillColor", "") for box in boxes if _style_map(box.style).get("fillColor")
    }
    if len(font_sizes) > 3:
        findings.append(Finding("warning", "font_variety", "more than three font sizes increase visual inconsistency"))
    if len(fill_colors) > 6:
        findings.append(Finding("warning", "color_variety", "more than six fill colors increase visual competition"))
    if page_width and page_height:
        ratio = max(page_width / page_height, page_height / page_width)
        if ratio > 3.2:
            findings.append(Finding("review_required", "extreme_aspect_ratio", "canvas aspect ratio requires rendered review"))

    normalized_spec: dict[str, Any] | None = None
    if spec is not None:
        try:
            normalized_spec = validate_spec(spec)
        except SpecError as exc:
            findings.append(Finding("blocking", "invalid_spec", str(exc)))
        if normalized_spec is not None:
            expected_ids = {item["id"] for key in ("groups", "nodes", "edges") for item in normalized_spec[key]}
            for item_id in sorted(expected_ids - set(cell_map)):
                findings.append(Finding("blocking", "spec_cell_missing", "cell declared by the spec is absent from draw.io", item_id))
            for edge in normalized_spec["edges"]:
                cell = cell_map.get(edge["id"])
                if cell is None:
                    continue
                for key, attribute in (("source", "source"), ("target", "target"), ("direction", "hskDirection"), ("relation_type", "hskRelationType")):
                    if cell.attrib.get(attribute) != edge[key]:
                        findings.append(Finding("blocking", "spec_structure_mismatch", f"draw.io {attribute} differs from the spec", edge["id"]))
            artifact = normalized_spec["artifact"]
            declared_drawio = artifact.get("drawio_sha256")
            actual_drawio = hashlib.sha256(xml_bytes).hexdigest()
            if declared_drawio and declared_drawio != actual_drawio:
                findings.append(Finding("blocking", "drawio_hash_mismatch", "artifact.drawio_sha256 does not match the current draw.io file"))
            if artifact.get("spec_sha256") and artifact["spec_sha256"] != canonical_spec_sha256(spec):
                findings.append(Finding("blocking", "spec_hash_mismatch", "artifact.spec_sha256 does not match the current spec"))
            if artifact.get("visual_review_status") != "approved_for_paper":
                findings.append(Finding("review_required", "preview_not_reviewed", "structure_checked is not approved_for_paper; inspect a current rendered preview"))
            project_root = _project_root_from_spec(spec_path) if spec_path is not None else None
            preview = artifact.get("preview")
            preview_sha = artifact.get("preview_sha256")
            if project_root is not None and preview:
                preview_path = project_root / preview
                if not preview_path.is_file():
                    findings.append(Finding("review_required", "preview_missing", "declared rendered preview does not exist"))
                else:
                    preview_bytes = preview_path.read_bytes()
                    if not _preview_format_is_valid(preview_path, preview_bytes):
                        findings.append(Finding("blocking", "preview_format_invalid", "declared preview is not a valid PNG, PDF, or SVG surface"))
                    if preview_sha and hashlib.sha256(preview_bytes).hexdigest() != preview_sha:
                        findings.append(Finding("blocking", "preview_hash_mismatch", "declared preview hash is stale"))

    return findings


def _load_spec(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SpecError(f"cannot read spec {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise SpecError("spec root must be a mapping")
    return dict(payload)


def _report(findings: Sequence[Finding], drawio: Path) -> dict[str, Any]:
    counts = {severity: sum(item.severity == severity for item in findings) for severity in SEVERITIES}
    return {
        "status": "failed" if counts["blocking"] else ("review_required" if counts["review_required"] else "passed"),
        "claim": "structure_and_geometry_only",
        "drawio": str(drawio),
        "counts": counts,
        "findings": [asdict(item) for item in findings],
        "semantic_validation": "not_performed",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate draw.io structure/geometry; never claim mathematical or semantic correctness.")
    parser.add_argument("drawio", type=Path)
    parser.add_argument("--spec", type=Path, help="Optional Mechanism Diagram Spec YAML")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--strict", action="store_true", help="Return 2 when review-required or warning findings remain")
    args = parser.parse_args(argv)
    try:
        xml_bytes = args.drawio.read_bytes()
        payload = _load_spec(args.spec) if args.spec else None
    except (OSError, SpecError) as exc:
        print(f"draw.io validation failed: {exc}", file=sys.stderr)
        return 1
    findings = validate_drawio_bytes(xml_bytes, spec=payload, spec_path=args.spec)
    report = _report(findings, args.drawio)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"draw.io structure/geometry status: {report['status']}")
        print("semantic validation: not performed")
        for severity in SEVERITIES:
            print(f"{severity}: {report['counts'][severity]}")
        for item in findings:
            suffix = f" [{item.element_id}]" if item.element_id else ""
            print(f"- {item.severity}/{item.code}{suffix}: {item.message}")
    if report["counts"]["blocking"]:
        return 1
    if args.strict and findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
