#!/usr/bin/env python3
"""Instantiate or expand 模型论文框架.md without creating a second framework authority.

Mode semantics come from core/output_contract.yaml. The repository template is treated as
one canonical superset source; this script projects that source to compact/full and can
losslessly expand an existing compact framework to full. It never writes project state,
approval, semantic identity, or numerical artifacts.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_CONTRACT = ROOT / "core" / "output_contract.yaml"
MODE_LINE_RE = re.compile(
    r"(?mi)^-\s*框架模式\s*[:：]\s*`?(compact|full)`?[ \t]*$"
)
TOP_LEVEL_RE = re.compile(r"^##(?!#)[ \t]+(.+?)[ \t]*$", re.UNICODE)
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
VALID_MODES = {"compact", "full"}


class FrameworkInstantiationError(ValueError):
    """Fail-closed error for unsafe framework projection or transition."""


@dataclass(frozen=True)
class FrameworkParts:
    header: str
    order: tuple[str, ...]
    sections: Mapping[str, str]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def framework_contract(path: Path = DEFAULT_OUTPUT_CONTRACT) -> dict[str, Any]:
    payload = load_yaml(path)
    framework = payload.get("model_paper_framework")
    if not isinstance(framework, dict):
        raise FrameworkInstantiationError("output contract has no model_paper_framework mapping")
    if framework.get("default_mode") not in VALID_MODES:
        raise FrameworkInstantiationError("output contract must declare compact/full default_mode")
    modes = framework.get("modes")
    if not isinstance(modes, dict) or not VALID_MODES.issubset(modes):
        raise FrameworkInstantiationError("output contract must define compact and full modes")
    return framework


def canonical_template_path(
    *, contract_path: Path = DEFAULT_OUTPUT_CONTRACT, root: Path = ROOT
) -> Path:
    framework = framework_contract(contract_path)
    relative = Path(str(framework.get("template") or ""))
    if relative.is_absolute():
        raise FrameworkInstantiationError("framework template path must be repository-relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise FrameworkInstantiationError("framework template path escapes repository root")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _heading_name(line: str) -> str | None:
    match = TOP_LEVEL_RE.match(line.rstrip("\r\n"))
    if not match:
        return None
    return re.sub(r"[ \t]+#+[ \t]*$", "", match.group(1)).strip()


def split_top_level(text: str) -> FrameworkParts:
    """Split Markdown at real level-2 headings while ignoring fenced examples."""
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    fence: str | None = None
    offset = 0
    for line in lines:
        marker = FENCE_RE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            offset += len(line)
            continue
        if fence is None:
            name = _heading_name(line)
            if name:
                starts.append((offset, name))
        offset += len(line)

    if not starts:
        raise FrameworkInstantiationError("framework has no top-level ## sections")
    names = [name for _, name in starts]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise FrameworkInstantiationError(f"duplicate top-level framework headings: {duplicates}")

    sections: dict[str, str] = {}
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        sections[name] = text[start:end]
    return FrameworkParts(text[: starts[0][0]], tuple(names), sections)


def infer_mode(text: str) -> str:
    matches = MODE_LINE_RE.findall(split_top_level(text).header)
    if len(matches) != 1:
        raise FrameworkInstantiationError(
            "framework header must contain exactly one resolved 框架模式: compact|full line"
        )
    return matches[0].lower()


def _set_mode(header: str, mode: str) -> str:
    if mode not in VALID_MODES:
        raise FrameworkInstantiationError(f"unsupported framework mode: {mode}")
    matches = list(MODE_LINE_RE.finditer(header))
    if len(matches) != 1:
        raise FrameworkInstantiationError(
            "canonical/live framework header must contain exactly one compact/full mode line"
        )
    return MODE_LINE_RE.sub(f"- 框架模式: {mode}", header, count=1)


def _canonical_parts(
    *, contract_path: Path = DEFAULT_OUTPUT_CONTRACT, root: Path = ROOT
) -> tuple[dict[str, Any], FrameworkParts]:
    contract = framework_contract(contract_path)
    path = canonical_template_path(contract_path=contract_path, root=root)
    parts = split_top_level(path.read_text(encoding="utf-8"))
    # The current repository template is a canonical full superset. It is source material,
    # not the default live mode; new live instances always go through this projector.
    if infer_mode(path.read_text(encoding="utf-8")) != "full":
        raise FrameworkInstantiationError("canonical framework template must remain a full superset")
    return contract, parts


def _compact_top_level_names(contract: Mapping[str, Any], canonical: FrameworkParts) -> tuple[str, ...]:
    requested = list(((contract.get("modes") or {}).get("compact") or {}).get("required_sections") or [])
    names = tuple(name for name in canonical.order if name in requested)
    missing = [name for name in requested if name not in canonical.sections]
    if missing:
        raise FrameworkInstantiationError(
            f"compact required sections are not top-level canonical sections: {missing}"
        )
    if not names:
        raise FrameworkInstantiationError("compact mode resolved to no canonical sections")
    return names


def _assemble(header: str, order: tuple[str, ...], sections: Mapping[str, str]) -> str:
    text = header + "".join(sections[name] for name in order)
    return text if text.endswith("\n") else text + "\n"


def validate_projection(text: str, mode: str) -> list[str]:
    """Reuse the existing deterministic framework validator; do not define parallel rules."""
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from validate_model_paper_framework import validate_framework_text

    return validate_framework_text(text, mode=mode, strict=False)


def instantiate(
    mode: str | None = None,
    *,
    contract_path: Path = DEFAULT_OUTPUT_CONTRACT,
    root: Path = ROOT,
) -> str:
    contract, canonical = _canonical_parts(contract_path=contract_path, root=root)
    resolved = mode or str(contract.get("default_mode"))
    if resolved not in VALID_MODES:
        raise FrameworkInstantiationError(f"unsupported framework mode: {resolved}")
    order = canonical.order if resolved == "full" else _compact_top_level_names(contract, canonical)
    text = _assemble(_set_mode(canonical.header, resolved), order, canonical.sections)
    issues = validate_projection(text, resolved)
    if issues:
        raise FrameworkInstantiationError("projected canonical framework is invalid: " + "; ".join(issues))
    return text


def expand_to_full(
    source_text: str,
    *,
    contract_path: Path = DEFAULT_OUTPUT_CONTRACT,
    root: Path = ROOT,
) -> str:
    """Losslessly add full-only top-level sections to a valid compact framework."""
    current_mode = infer_mode(source_text)
    if current_mode == "full":
        # Idempotent by definition: do not rewrite a current full framework from template.
        return source_text
    if current_mode != "compact":
        raise FrameworkInstantiationError(f"cannot expand mode {current_mode!r}")

    contract, canonical = _canonical_parts(contract_path=contract_path, root=root)
    source = split_top_level(source_text)
    compact_names = _compact_top_level_names(contract, canonical)
    canonical_set = set(canonical.order)
    unknown = sorted(set(source.order) - canonical_set)
    if unknown:
        raise FrameworkInstantiationError(f"compact framework has unknown top-level sections: {unknown}")
    missing = [name for name in compact_names if name not in source.sections]
    if missing:
        raise FrameworkInstantiationError(f"compact framework is missing required sections: {missing}")
    full_only_present = [name for name in source.order if name not in compact_names]
    if full_only_present:
        raise FrameworkInstantiationError(
            "compact framework already contains full-only top-level sections: "
            + ", ".join(full_only_present)
        )

    projected: dict[str, str] = {}
    for name in canonical.order:
        projected[name] = source.sections[name] if name in source.sections else canonical.sections[name]
    expanded = _assemble(_set_mode(source.header, "full"), canonical.order, projected)
    issues = validate_projection(expanded, "full")
    if issues:
        raise FrameworkInstantiationError("expanded framework is invalid: " + "; ".join(issues))
    return expanded


def transition(
    source_text: str,
    target_mode: str,
    *,
    contract_path: Path = DEFAULT_OUTPUT_CONTRACT,
    root: Path = ROOT,
) -> str:
    current = infer_mode(source_text)
    if target_mode not in VALID_MODES:
        raise FrameworkInstantiationError(f"unsupported target mode: {target_mode}")
    if current == target_mode:
        return source_text
    if current == "compact" and target_mode == "full":
        return expand_to_full(source_text, contract_path=contract_path, root=root)
    raise FrameworkInstantiationError(
        "automatic full->compact conversion is forbidden because it may discard project facts"
    )


def _write_or_print(text: str, output: Path | None) -> None:
    if output is None:
        print(text, end="")
        return
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_OUTPUT_CONTRACT)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("new", help="project the canonical superset to a new compact/full scaffold")
    create.add_argument("--mode", choices=sorted(VALID_MODES), default=None)
    create.add_argument("--output", type=Path)

    expand = sub.add_parser("expand", help="losslessly expand an existing compact framework to full")
    expand.add_argument("source", type=Path)
    expand.add_argument("--output", type=Path)

    check = sub.add_parser("check", help="report current mode and deterministic validation issues")
    check.add_argument("source", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "new":
            text = instantiate(args.mode, contract_path=args.contract)
            _write_or_print(text, args.output)
        elif args.command == "expand":
            source = args.source.read_text(encoding="utf-8")
            text = transition(source, "full", contract_path=args.contract)
            _write_or_print(text, args.output)
        else:
            source = args.source.read_text(encoding="utf-8")
            mode = infer_mode(source)
            issues = validate_projection(source, mode)
            print(yaml.safe_dump({"mode": mode, "issues": issues}, allow_unicode=True, sort_keys=False), end="")
            return 1 if issues else 0
    except (FrameworkInstantiationError, FileNotFoundError, OSError) as exc:
        print(f"framework instantiation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
