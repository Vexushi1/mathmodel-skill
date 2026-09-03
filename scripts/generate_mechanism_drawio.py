#!/usr/bin/env python3
"""Generate deterministic, editable draw.io XML from an HSK mechanism spec."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import yaml


SPEC_VERSION = "1.0.0"
DIAGRAM_TYPES = {
    "object_relation",
    "mechanism_relation",
    "constraint_logic",
    "critical_state",
    "strategy_switch",
    "comparison_boundary",
}
LAYOUT_MODES = {"explicit", "layered_lr", "layered_tb"}
SEMANTIC_ROLES = {
    "object",
    "state",
    "variable",
    "condition",
    "constraint",
    "boundary",
    "decision",
    "outcome",
    "context",
}
RELATION_TYPES = {
    "causes",
    "constrains",
    "transforms",
    "depends_on",
    "flows_to",
    "switches_to",
    "compares_with",
    "feedback",
    "custom",
}
DIRECTIONS = {"forward", "backward", "bidirectional", "none"}
SHAPES = {"rounded_rect", "rect", "ellipse", "diamond", "hexagon"}
EMPHASIS_LEVELS = {"primary", "secondary", "context", "risk"}
VALIDATION_STATUSES = {"pending", "passed", "failed", "review_required"}
VISUAL_REVIEW_STATUSES = {
    "pending",
    "preview_rendered",
    "visual_reviewed",
    "approved_for_paper",
    "rejected",
}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDERS = {"节点1", "节点2", "输入", "模型", "输出", "input", "model", "output", "todo", "tbd"}
ANCHOR_KEYS = {"model", "formulas", "constraints", "assumptions", "code", "result_evidence"}


class SpecError(ValueError):
    """Raised when a mechanism spec violates the v1 contract."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SpecError(f"{field} must be a mapping")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SpecError(f"{field} must be a list")
    return value


def _text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise SpecError(f"{field} must be a string")
    result = value.strip()
    if not allow_empty and not result:
        raise SpecError(f"{field} must not be empty")
    return result


def _enum(value: Any, field: str, allowed: set[str]) -> str:
    result = _text(value, field)
    if result not in allowed:
        raise SpecError(f"{field} must be one of {sorted(allowed)}")
    return result


def _number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise SpecError(f"{field} must be a finite number")
    result = float(value)
    if positive and result <= 0:
        raise SpecError(f"{field} must be greater than zero")
    return result


def _only_keys(value: Mapping[str, Any], field: str, allowed: set[str], required: set[str]) -> None:
    missing = required - set(value)
    extra = set(value) - allowed
    if missing:
        raise SpecError(f"{field} missing keys: {sorted(missing)}")
    if extra:
        raise SpecError(f"{field} has unsupported keys: {sorted(extra)}")


def _string_list(value: Any, field: str) -> list[str]:
    items = _list(value, field)
    result = [_text(item, f"{field}[{index}]") for index, item in enumerate(items)]
    if len(result) != len(set(result)):
        raise SpecError(f"{field} contains duplicates")
    return result


def _id(value: Any, field: str) -> str:
    result = _text(value, field)
    if not ID_RE.fullmatch(result):
        raise SpecError(f"{field} must match {ID_RE.pattern}")
    return result


def _anchor(value: Any, field: str) -> str:
    result = _text(value, field)
    lowered = result.lower()
    if any(token in lowered for token in ("http://", "https://", "data:", "javascript:")):
        raise SpecError(f"{field} must reference a local semantic authority")
    return result


def _geometry(value: Any, field: str, *, require_position: bool) -> dict[str, float]:
    geometry = _mapping(value, field)
    allowed = {"x", "y", "width", "height"}
    required = allowed if require_position else {"width", "height"}
    _only_keys(geometry, field, allowed, required)
    width = _number(geometry["width"], f"{field}.width", positive=True)
    height = _number(geometry["height"], f"{field}.height", positive=True)
    result = {"width": width, "height": height}
    if "x" in geometry:
        result["x"] = _number(geometry["x"], f"{field}.x")
    if "y" in geometry:
        result["y"] = _number(geometry["y"], f"{field}.y")
    if require_position and (result["x"] < 0 or result["y"] < 0):
        raise SpecError(f"{field} position must be non-negative")
    return result


def _artifact_path(value: Any, field: str, *, prefix: str, suffixes: set[str]) -> str:
    result = _text(value, field)
    if "\\" in result:
        raise SpecError(f"{field} must use POSIX separators")
    path = PurePosixPath(result)
    if path.is_absolute() or ".." in path.parts or not result.startswith(prefix):
        raise SpecError(f"{field} must be a project-relative path under {prefix}")
    if path.suffix.lower() not in suffixes:
        raise SpecError(f"{field} must use one of {sorted(suffixes)}")
    return result


def _optional_sha(value: Any, field: str) -> str | None:
    if value is None:
        return None
    result = _text(value, field)
    if not SHA256_RE.fullmatch(result):
        raise SpecError(f"{field} must be a lowercase SHA-256 digest")
    return result


def canonical_spec_sha256(spec: Mapping[str, Any]) -> str:
    """Hash semantic/render input while excluding mutable artifact lifecycle state."""
    normalized = copy.deepcopy(dict(spec))
    normalized.pop("artifact", None)

    def canonicalize(value: Any, key: str | None = None) -> Any:
        if isinstance(value, Mapping):
            return {item_key: canonicalize(item_value, item_key) for item_key, item_value in sorted(value.items())}
        if isinstance(value, list):
            items = [canonicalize(item) for item in value]
            if key in {"groups", "nodes", "edges"} and all(isinstance(item, Mapping) and "id" in item for item in items):
                return sorted(items, key=lambda item: str(item["id"]))
            if key in ANCHOR_KEYS | {"symbol_refs", "formula_refs", "final_exports"} and all(isinstance(item, str) for item in items):
                return sorted(items)
            return items
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    payload = json.dumps(canonicalize(normalized), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reject_unresolved_placeholders(value: Any, field: str = "spec") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unresolved_placeholders(item, f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unresolved_placeholders(item, f"{field}[{index}]")
    elif isinstance(value, str) and "REPLACE_" in value.upper():
        raise SpecError(f"{field} contains an unresolved REPLACE_* placeholder")


def validate_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a normalized v1 mechanism diagram spec."""
    source = _mapping(spec, "spec")
    _reject_unresolved_placeholders(source)
    top_keys = {
        "spec_version", "figure_id", "question_id", "diagram_type", "core_question",
        "core_conclusion", "framework_anchor", "backend", "layout_mode",
        "semantic_anchors", "canvas", "groups", "nodes", "edges", "artifact",
    }
    _only_keys(source, "spec", top_keys, top_keys)
    if str(source["spec_version"]) != SPEC_VERSION:
        raise SpecError(f"spec_version must be {SPEC_VERSION}")

    normalized: dict[str, Any] = {
        "spec_version": SPEC_VERSION,
        "figure_id": _id(source["figure_id"], "figure_id"),
        "question_id": _id(source["question_id"], "question_id"),
        "diagram_type": _enum(source["diagram_type"], "diagram_type", DIAGRAM_TYPES),
        "core_question": _text(source["core_question"], "core_question"),
        "core_conclusion": _text(source["core_conclusion"], "core_conclusion"),
        "framework_anchor": _anchor(source["framework_anchor"], "framework_anchor"),
        "backend": _enum(source["backend"], "backend", {"drawio"}),
        "layout_mode": _enum(source["layout_mode"], "layout_mode", LAYOUT_MODES),
    }

    anchors = _mapping(source["semantic_anchors"], "semantic_anchors")
    _only_keys(anchors, "semantic_anchors", ANCHOR_KEYS, ANCHOR_KEYS)
    normalized["semantic_anchors"] = {
        key: _string_list(anchors[key], f"semantic_anchors.{key}") for key in sorted(ANCHOR_KEYS)
    }
    if not any(normalized["semantic_anchors"].values()):
        raise SpecError("semantic_anchors must contain at least one authority reference")

    canvas = _mapping(source["canvas"], "canvas")
    canvas_keys = {"width", "height", "orientation", "target_use", "target_width_mm"}
    _only_keys(canvas, "canvas", canvas_keys, canvas_keys)
    width = _number(canvas["width"], "canvas.width", positive=True)
    height = _number(canvas["height"], "canvas.height", positive=True)
    orientation = _enum(canvas["orientation"], "canvas.orientation", {"landscape", "portrait"})
    if orientation == "landscape" and width <= height:
        raise SpecError("landscape canvas must be wider than it is high")
    if orientation == "portrait" and height <= width:
        raise SpecError("portrait canvas must be higher than it is wide")
    normalized["canvas"] = {
        "width": width,
        "height": height,
        "orientation": orientation,
        "target_use": _enum(canvas["target_use"], "canvas.target_use", {"paper", "presentation"}),
        "target_width_mm": _number(canvas["target_width_mm"], "canvas.target_width_mm", positive=True),
    }

    groups: list[dict[str, Any]] = []
    seen_ids: set[str] = {"0", "1"}
    for index, raw in enumerate(_list(source["groups"], "groups")):
        item = _mapping(raw, f"groups[{index}]")
        keys = {"id", "label", "source_anchor", "geometry"}
        _only_keys(item, f"groups[{index}]", keys, keys)
        item_id = _id(item["id"], f"groups[{index}].id")
        if item_id in seen_ids:
            raise SpecError(f"duplicate cell id: {item_id}")
        seen_ids.add(item_id)
        groups.append({
            "id": item_id,
            "label": _text(item["label"], f"groups[{index}].label"),
            "source_anchor": _anchor(item["source_anchor"], f"groups[{index}].source_anchor"),
            "geometry": _geometry(item["geometry"], f"groups[{index}].geometry", require_position=True),
        })
    group_ids = {item["id"] for item in groups}

    nodes: list[dict[str, Any]] = []
    node_keys = {"id", "label", "semantic_role", "symbol_refs", "source_anchor", "group_id", "shape", "emphasis", "geometry"}
    node_required = node_keys - {"geometry"}
    for index, raw in enumerate(_list(source["nodes"], "nodes")):
        item = _mapping(raw, f"nodes[{index}]")
        _only_keys(item, f"nodes[{index}]", node_keys, node_required | ({"geometry"} if normalized["layout_mode"] == "explicit" else set()))
        item_id = _id(item["id"], f"nodes[{index}].id")
        if item_id in seen_ids:
            raise SpecError(f"duplicate cell id: {item_id}")
        seen_ids.add(item_id)
        label = _text(item["label"], f"nodes[{index}].label")
        if label.strip().lower() in {value.lower() for value in PLACEHOLDERS}:
            raise SpecError(f"nodes[{index}].label is an unresolved placeholder")
        group_id = item["group_id"]
        if group_id is not None:
            group_id = _id(group_id, f"nodes[{index}].group_id")
            if group_id not in group_ids:
                raise SpecError(f"nodes[{index}].group_id does not exist: {group_id}")
        geometry = None
        if "geometry" in item and item["geometry"] is not None:
            geometry = _geometry(
                item["geometry"],
                f"nodes[{index}].geometry",
                require_position=normalized["layout_mode"] == "explicit",
            )
        nodes.append({
            "id": item_id,
            "label": label,
            "semantic_role": _enum(item["semantic_role"], f"nodes[{index}].semantic_role", SEMANTIC_ROLES),
            "symbol_refs": _string_list(item["symbol_refs"], f"nodes[{index}].symbol_refs"),
            "source_anchor": _anchor(item["source_anchor"], f"nodes[{index}].source_anchor"),
            "group_id": group_id,
            "shape": _enum(item["shape"], f"nodes[{index}].shape", SHAPES),
            "emphasis": _enum(item["emphasis"], f"nodes[{index}].emphasis", EMPHASIS_LEVELS),
            "geometry": geometry,
        })
    if not nodes:
        raise SpecError("nodes must not be empty")
    node_ids = {item["id"] for item in nodes}

    edges: list[dict[str, Any]] = []
    edge_keys = {"id", "source", "target", "relation_type", "direction", "label", "source_anchor", "formula_refs", "waypoints"}
    for index, raw in enumerate(_list(source["edges"], "edges")):
        item = _mapping(raw, f"edges[{index}]")
        _only_keys(item, f"edges[{index}]", edge_keys, edge_keys)
        item_id = _id(item["id"], f"edges[{index}].id")
        if item_id in seen_ids:
            raise SpecError(f"duplicate cell id: {item_id}")
        seen_ids.add(item_id)
        source_id = _id(item["source"], f"edges[{index}].source")
        target_id = _id(item["target"], f"edges[{index}].target")
        if source_id not in node_ids or target_id not in node_ids:
            raise SpecError(f"edges[{index}] references an unknown node")
        if source_id == target_id:
            raise SpecError(f"edges[{index}] self-loops are not supported in v1")
        relation = _enum(item["relation_type"], f"edges[{index}].relation_type", RELATION_TYPES)
        direction = _enum(item["direction"], f"edges[{index}].direction", DIRECTIONS)
        if relation not in {"compares_with", "custom"} and direction == "none":
            raise SpecError(f"edges[{index}] uses a directed relation and cannot set direction=none")
        label = _text(item["label"], f"edges[{index}].label", allow_empty=True)
        if relation == "custom" and not label:
            raise SpecError(f"edges[{index}].label is required for custom relations")
        waypoints: list[dict[str, float]] = []
        for point_index, raw_point in enumerate(_list(item["waypoints"], f"edges[{index}].waypoints")):
            point = _mapping(raw_point, f"edges[{index}].waypoints[{point_index}]")
            _only_keys(point, f"edges[{index}].waypoints[{point_index}]", {"x", "y"}, {"x", "y"})
            waypoints.append({
                "x": _number(point["x"], f"edges[{index}].waypoints[{point_index}].x"),
                "y": _number(point["y"], f"edges[{index}].waypoints[{point_index}].y"),
            })
        edges.append({
            "id": item_id,
            "source": source_id,
            "target": target_id,
            "relation_type": relation,
            "direction": direction,
            "label": label,
            "source_anchor": _anchor(item["source_anchor"], f"edges[{index}].source_anchor"),
            "formula_refs": _string_list(item["formula_refs"], f"edges[{index}].formula_refs"),
            "waypoints": waypoints,
        })

    artifact = _mapping(source["artifact"], "artifact")
    artifact_keys = {
        "spec_source", "editable_source", "preview", "final_exports", "spec_sha256",
        "drawio_sha256", "preview_sha256", "validation_status", "visual_review_status",
    }
    _only_keys(artifact, "artifact", artifact_keys, artifact_keys)
    normalized_artifact = {
        "spec_source": _artifact_path(artifact["spec_source"], "artifact.spec_source", prefix="figures/source/", suffixes={".yaml", ".yml"}),
        "editable_source": _artifact_path(artifact["editable_source"], "artifact.editable_source", prefix="figures/source/", suffixes={".drawio"}),
        "preview": None,
        "final_exports": [],
        "spec_sha256": _optional_sha(artifact["spec_sha256"], "artifact.spec_sha256"),
        "drawio_sha256": _optional_sha(artifact["drawio_sha256"], "artifact.drawio_sha256"),
        "preview_sha256": _optional_sha(artifact["preview_sha256"], "artifact.preview_sha256"),
        "validation_status": _enum(artifact["validation_status"], "artifact.validation_status", VALIDATION_STATUSES),
        "visual_review_status": _enum(artifact["visual_review_status"], "artifact.visual_review_status", VISUAL_REVIEW_STATUSES),
    }
    if artifact["preview"] is not None:
        normalized_artifact["preview"] = _artifact_path(
            artifact["preview"], "artifact.preview", prefix="figures/preview/", suffixes={".png", ".svg", ".pdf"}
        )
    normalized_artifact["final_exports"] = [
        _artifact_path(item, f"artifact.final_exports[{index}]", prefix="figures/", suffixes={".pdf", ".svg", ".png"})
        for index, item in enumerate(_list(artifact["final_exports"], "artifact.final_exports"))
    ]
    if len(normalized_artifact["final_exports"]) != len(set(normalized_artifact["final_exports"])):
        raise SpecError("artifact.final_exports contains duplicates")
    path_fields = {
        "artifact.spec_source": normalized_artifact["spec_source"],
        "artifact.editable_source": normalized_artifact["editable_source"],
    }
    if normalized_artifact["preview"]:
        path_fields["artifact.preview"] = normalized_artifact["preview"]
    expected_parents = {
        "artifact.spec_source": PurePosixPath("figures/source"),
        "artifact.editable_source": PurePosixPath("figures/source"),
        "artifact.preview": PurePosixPath("figures/preview"),
    }
    for field, value in path_fields.items():
        if PurePosixPath(value).parent != expected_parents[field]:
            raise SpecError(f"{field} must be stored directly under {expected_parents[field]}")
    for index, value in enumerate(normalized_artifact["final_exports"]):
        if PurePosixPath(value).parent != PurePosixPath("figures"):
            raise SpecError(f"artifact.final_exports[{index}] must be stored directly under figures/")
    spec_stem = PurePosixPath(normalized_artifact["spec_source"]).stem
    if spec_stem.endswith(".mechanism"):
        spec_stem = spec_stem[: -len(".mechanism")]
    related_paths = [normalized_artifact["editable_source"], *normalized_artifact["final_exports"]]
    if normalized_artifact["preview"]:
        related_paths.append(normalized_artifact["preview"])
    if any(PurePosixPath(value).stem != spec_stem for value in related_paths):
        raise SpecError("artifact spec, draw.io, preview, and final exports must share one stem")
    if normalized_artifact["preview_sha256"] and not normalized_artifact["preview"]:
        raise SpecError("artifact.preview_sha256 requires artifact.preview")
    if normalized_artifact["validation_status"] == "passed" and not normalized_artifact["drawio_sha256"]:
        raise SpecError("validation_status=passed requires artifact.drawio_sha256")
    if normalized_artifact["visual_review_status"] in {"preview_rendered", "visual_reviewed", "approved_for_paper"}:
        if not normalized_artifact["preview"] or not normalized_artifact["preview_sha256"]:
            raise SpecError("rendered/reviewed states require a preview path and preview_sha256")
    if normalized_artifact["visual_review_status"] in {"visual_reviewed", "approved_for_paper"} and normalized_artifact["validation_status"] != "passed":
        raise SpecError("visual_reviewed/approved_for_paper requires validation_status=passed")
    if normalized_artifact["visual_review_status"] == "approved_for_paper":
        if not normalized_artifact["preview"] or not normalized_artifact["preview_sha256"]:
            raise SpecError("approved_for_paper requires a rendered preview and preview_sha256")
        if normalized_artifact["validation_status"] != "passed":
            raise SpecError("approved_for_paper requires validation_status=passed")
    normalized["groups"] = sorted(groups, key=lambda item: item["id"])
    normalized["nodes"] = sorted(nodes, key=lambda item: item["id"])
    normalized["edges"] = sorted(edges, key=lambda item: item["id"])
    normalized["artifact"] = normalized_artifact

    for group in normalized["groups"]:
        box = group["geometry"]
        if box["x"] + box["width"] > width or box["y"] + box["height"] > height:
            raise SpecError(f"group {group['id']} lies outside the canvas")
    if normalized["layout_mode"] == "explicit":
        for node in normalized["nodes"]:
            box = node["geometry"]
            assert box is not None
            if box["x"] + box["width"] > width or box["y"] + box["height"] > height:
                raise SpecError(f"node {node['id']} lies outside the canvas")
        for edge in normalized["edges"]:
            for point in edge["waypoints"]:
                if not (0 <= point["x"] <= width and 0 <= point["y"] <= height):
                    raise SpecError(f"edge {edge['id']} waypoint lies outside the canvas")

    declared_spec_hash = normalized_artifact["spec_sha256"]
    if declared_spec_hash and declared_spec_hash != canonical_spec_sha256(source):
        raise SpecError("artifact.spec_sha256 does not match the normalized spec")
    return normalized


def _node_ranks(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    ids = [str(item["id"]) for item in nodes]
    indegree = {item_id: 0 for item_id in ids}
    outgoing: dict[str, list[str]] = {item_id: [] for item_id in ids}
    for edge in edges:
        if edge["relation_type"] == "feedback" or edge["direction"] in {"backward", "bidirectional", "none"}:
            continue
        source, target = str(edge["source"]), str(edge["target"])
        outgoing[source].append(target)
        indegree[target] += 1
    ranks = {item_id: 0 for item_id in ids}
    queue = sorted(item_id for item_id, degree in indegree.items() if degree == 0)
    visited: set[str] = set()
    while queue:
        current = queue.pop(0)
        visited.add(current)
        for target in sorted(outgoing[current]):
            ranks[target] = max(ranks[target], ranks[current] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    # Cyclic components remain at rank zero; feedback cycles are intentionally not unfolded.
    return ranks


def _layout_nodes(spec: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    nodes = list(spec["nodes"])
    mode = str(spec["layout_mode"])
    if mode == "explicit":
        return {str(node["id"]): dict(node["geometry"]) for node in nodes}
    canvas = spec["canvas"]
    width, height = float(canvas["width"]), float(canvas["height"])
    margin = max(48.0, min(width, height) * 0.08)
    ranks = _node_ranks(nodes, spec["edges"])
    by_rank: dict[int, list[Mapping[str, Any]]] = {}
    for node in nodes:
        by_rank.setdefault(ranks[str(node["id"])], []).append(node)
    max_rank = max(by_rank, default=0)
    placed: dict[str, dict[str, float]] = {}
    for rank in sorted(by_rank):
        layer = sorted(by_rank[rank], key=lambda item: str(item["id"]))
        for position, node in enumerate(layer):
            geometry = node.get("geometry") or {}
            node_width = float(geometry.get("width", 180.0))
            node_height = float(geometry.get("height", 68.0))
            if mode == "layered_lr":
                usable_x = max(0.0, width - 2 * margin - node_width)
                x = margin + (usable_x * rank / max_rank if max_rank else usable_x / 2)
                slot = (height - 2 * margin) / max(1, len(layer))
                y = margin + slot * position + max(0.0, (slot - node_height) / 2)
            else:
                usable_y = max(0.0, height - 2 * margin - node_height)
                y = margin + (usable_y * rank / max_rank if max_rank else usable_y / 2)
                slot = (width - 2 * margin) / max(1, len(layer))
                x = margin + slot * position + max(0.0, (slot - node_width) / 2)
            placed[str(node["id"])] = {
                "x": round(x, 3),
                "y": round(y, 3),
                "width": node_width,
                "height": node_height,
            }
    return placed


def _format_number(value: float) -> str:
    rounded = round(float(value), 3)
    return str(int(rounded)) if rounded.is_integer() else f"{rounded:.3f}".rstrip("0").rstrip(".")


def _node_style(node: Mapping[str, Any]) -> str:
    palettes = {
        "primary": ("#E8F1FF", "#1478FF", "#0B3B75"),
        "secondary": ("#EAF8F1", "#16B364", "#065F46"),
        "context": ("#F4F5F7", "#98A2B3", "#344054"),
        "risk": ("#FFF1F0", "#F04444", "#912018"),
    }
    fill, stroke, font = palettes[str(node["emphasis"])]
    shape_style = {
        "rounded_rect": "rounded=1;arcSize=14;",
        "rect": "rounded=0;",
        "ellipse": "ellipse;",
        "diamond": "rhombus;",
        "hexagon": "shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;",
    }[str(node["shape"])]
    return (
        f"{shape_style}whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};"
        f"fontColor={font};fontFamily=Arial;fontSize=14;strokeWidth=1.6;align=center;verticalAlign=middle;"
    )


def _edge_style(edge: Mapping[str, Any]) -> str:
    direction = str(edge["direction"])
    arrows = {
        "forward": "startArrow=none;endArrow=block;endFill=1;",
        "backward": "startArrow=block;startFill=1;endArrow=none;",
        "bidirectional": "startArrow=block;startFill=1;endArrow=block;endFill=1;",
        "none": "startArrow=none;endArrow=none;",
    }[direction]
    color = "#F04444" if edge["relation_type"] in {"constrains", "switches_to"} else "#475467"
    dashed = "dashed=1;dashPattern=6 4;" if edge["relation_type"] in {"depends_on", "compares_with", "feedback"} else "dashed=0;"
    return (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=0;"
        f"{arrows}{dashed}strokeColor={color};fontColor=#344054;fontFamily=Arial;fontSize=12;strokeWidth=1.5;"
    )


def generate_drawio(spec: Mapping[str, Any]) -> bytes:
    """Return deterministic, uncompressed draw.io XML bytes."""
    normalized = validate_spec(spec)
    canvas = normalized["canvas"]
    positions = _layout_nodes(normalized)
    spec_hash = canonical_spec_sha256(normalized)

    mxfile = ET.Element("mxfile", {
        "host": "app.diagrams.net",
        "agent": "HSK mathmodel-skill",
        "version": "8.3.0",
        "compressed": "false",
    })
    diagram = ET.SubElement(mxfile, "diagram", {
        "id": normalized["figure_id"],
        "name": normalized["question_id"],
        "hskSpecVersion": SPEC_VERSION,
        "hskSpecSha256": spec_hash,
    })
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "0", "dy": "0", "grid": "1", "gridSize": "10", "guides": "1",
        "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1",
        "page": "1", "pageScale": "1",
        "pageWidth": _format_number(canvas["width"]),
        "pageHeight": _format_number(canvas["height"]),
        "math": "1", "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    for group in normalized["groups"]:
        cell = ET.SubElement(root, "mxCell", {
            "id": group["id"],
            "value": group["label"],
            "style": "swimlane;container=1;collapsible=0;rounded=1;html=0;fillColor=#F9FAFB;strokeColor=#D0D5DD;fontColor=#344054;fontFamily=Arial;fontSize=13;strokeWidth=1.2;",
            "vertex": "1",
            "parent": "1",
            "hskKind": "group",
            "hskSourceAnchor": group["source_anchor"],
        })
        geometry = group["geometry"]
        ET.SubElement(cell, "mxGeometry", {
            "x": _format_number(geometry["x"]),
            "y": _format_number(geometry["y"]),
            "width": _format_number(geometry["width"]),
            "height": _format_number(geometry["height"]),
            "as": "geometry",
        })

    for node in normalized["nodes"]:
        attributes = {
            "id": node["id"],
            "value": node["label"],
            "style": _node_style(node),
            "vertex": "1",
            "parent": "1",
            "hskKind": "node",
            "hskSemanticRole": node["semantic_role"],
            "hskSourceAnchor": node["source_anchor"],
            "hskSymbolRefs": ",".join(node["symbol_refs"]),
        }
        if node["group_id"]:
            attributes["hskGroup"] = node["group_id"]
        cell = ET.SubElement(root, "mxCell", attributes)
        geometry = positions[node["id"]]
        ET.SubElement(cell, "mxGeometry", {
            "x": _format_number(geometry["x"]),
            "y": _format_number(geometry["y"]),
            "width": _format_number(geometry["width"]),
            "height": _format_number(geometry["height"]),
            "as": "geometry",
        })

    for edge in normalized["edges"]:
        cell = ET.SubElement(root, "mxCell", {
            "id": edge["id"],
            "value": edge["label"],
            "style": _edge_style(edge),
            "edge": "1",
            "parent": "1",
            "source": edge["source"],
            "target": edge["target"],
            "hskKind": "edge",
            "hskRelationType": edge["relation_type"],
            "hskDirection": edge["direction"],
            "hskSourceAnchor": edge["source_anchor"],
            "hskFormulaRefs": ",".join(edge["formula_refs"]),
        })
        geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        if edge["waypoints"]:
            points = ET.SubElement(geometry, "Array", {"as": "points"})
            for point in edge["waypoints"]:
                ET.SubElement(points, "mxPoint", {
                    "x": _format_number(point["x"]),
                    "y": _format_number(point["y"]),
                })

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True, short_empty_elements=True) + b"\n"


def load_spec(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SpecError(f"cannot read spec {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise SpecError("spec root must be a mapping")
    return dict(payload)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic uncompressed draw.io XML from an HSK mechanism spec.")
    parser.add_argument("--spec", required=True, type=Path, help="Mechanism Diagram Spec YAML")
    parser.add_argument("--output", type=Path, help="Destination .drawio file; required unless --check is used")
    parser.add_argument("--check", action="store_true", help="Validate and render in memory without writing")
    args = parser.parse_args(argv)
    try:
        payload = load_spec(args.spec)
        xml_bytes = generate_drawio(payload)
        normalized = validate_spec(payload)
        if args.check:
            print(json.dumps({
                "status": "passed",
                "claim": "spec_and_generation_only",
                "spec_sha256": canonical_spec_sha256(normalized),
                "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
                "written": False,
            }, ensure_ascii=False, sort_keys=True))
            return 0
        if args.output is None:
            parser.error("--output is required unless --check is used")
        if args.output.suffix.lower() != ".drawio":
            raise SpecError("output must use the .drawio suffix")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(xml_bytes)
        print(json.dumps({
            "status": "generated",
            "claim": "editable_structure_only",
            "output": str(args.output),
            "spec_sha256": canonical_spec_sha256(normalized),
            "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except SpecError as exc:
        print(f"mechanism spec failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
