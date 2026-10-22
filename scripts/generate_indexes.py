#!/usr/bin/env python3
"""Generate active-package indexes and a cross-platform MANIFEST.sha256."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"
SKILL_INDEX = ROOT / "SKILL_FILE_INDEX.md"
TEMPLATE_INDEX = ROOT / "TEMPLATE_INDEX.md"
LEGACY_SKILL_INDEX = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"
LEGACY_TEMPLATE_INDEX = ROOT / "HSK_TEMPLATE_INDEX_V622.md"
MANIFEST = ROOT / "MANIFEST.sha256"
STAGE_GUIDE_RELATIVE = Path("core") / "stage_reading_guide.md"
STAGE_GUIDE = ROOT / STAGE_GUIDE_RELATIVE
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
EXCLUDED_FILE_SUFFIXES = {".log"}
ACTIVE_ARCHIVE_POINTERS = {Path("legacy/README.md")}
BINARY_SUFFIXES = {
    ".7z", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".mat", ".npy",
    ".npz", ".otf", ".pdf", ".pickle", ".pkl", ".png", ".rar", ".tif", ".tiff",
    ".ttf", ".woff", ".woff2", ".xls", ".xlsx", ".zip",
}
COMPATIBILITY_POINTERS = {
    Path("PROJECT_INSTRUCTIONS_HSK_V622.md"),
    Path("HSK_RUNTIME_ROUTER_V622.md"),
    Path("HSK_SKILL_FILE_INDEX_V622.md"),
    Path("HSK_TEMPLATE_INDEX_V622.md"),
}
# This fragment is part of the active CUMCM assembly and remains in the Active
# Skill Index / MANIFEST. It is intentionally omitted only from the template
# discovery index so it is not advertised as a standalone reusable template.
TEMPLATE_INDEX_EXCLUDED_PATHS = {
    Path("templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex"),
}
GENERATED_RELATIVE = {
    SKILL_INDEX.relative_to(ROOT),
    TEMPLATE_INDEX.relative_to(ROOT),
    MANIFEST.relative_to(ROOT),
    STAGE_GUIDE_RELATIVE,
}

CURRENT_REFERENCE_DOCS = {
    Path("docs/v871_writing_reasoning_schema_version_policy.md"),
    Path("docs/v900_migration_contract.md"),
}
CURRENT_MAINTENANCE_DOCS = {
    Path("docs/skill_optimization_status.md"),
    Path("docs/v931_branch_cleanup_manifest.md"),
    Path("docs/v931_postrelease_health_remediation_plan.md"),
    Path("docs/v931_repository_hygiene_inventory.md"),
}
SKILL_INDEX_SECTION_ORDER = (
    ("active_runtime_reference", "Active Runtime & Reference"),
    ("current_maintenance", "Current Maintenance Records"),
    ("migration_compatibility", "Migration / Compatibility Records"),
    ("historical_provenance", "Historical Maintenance Provenance"),
    ("legacy_navigation", "Legacy Navigation"),
)


def current_skill_version() -> str:
    """Read the active Skill version from the bootstrap single source of truth."""
    if not BOOTSTRAP.is_file():
        raise FileNotFoundError(f"bootstrap missing: {BOOTSTRAP}")
    for raw_line in BOOTSTRAP.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line.startswith("skill_version:"):
            continue
        value = line.split(":", 1)[1].strip().strip('"\'')
        if value:
            return value
    raise ValueError("core/bootstrap.yaml must declare a non-empty skill_version")


def is_active_path(relative: Path) -> bool:
    # Runtime/test logs are ignored delivery artifacts and must not make an
    # index depend on a maintainer's local execution history.
    if relative.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return False
    if relative in COMPATIBILITY_POINTERS:
        return False
    if relative.parts and relative.parts[0] == "legacy":
        return relative in ACTIVE_ARCHIVE_POINTERS
    return True


def iter_files() -> list[Path]:
    files: set[Path] = set(GENERATED_RELATIVE)
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if not is_active_path(relative):
            continue
        files.add(relative)
    return sorted(files, key=lambda item: item.as_posix())


def template_index_files(files: list[Path]) -> list[Path]:
    """Return active template-discovery entries, excluding internal fragments."""
    return [
        path
        for path in files
        if path.parts
        and path.parts[0] == "templates"
        and path not in TEMPLATE_INDEX_EXCLUDED_PATHS
    ]


def index_text(title: str, files: list[Path], version: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"当前 Skill 版本：{version}",
        "",
        "本索引仅覆盖活动 Skill；历史文件通过 `legacy/README.md` 追溯。",
        "",
    ]
    lines.extend(f"- `{path.as_posix()}`" for path in files)
    return "\n".join(lines) + "\n"


def skill_index_section(relative: Path) -> str:
    """Classify active-package files for navigation without changing manifest coverage."""
    if relative == Path("legacy/README.md"):
        return "legacy_navigation"
    if not relative.parts or relative.parts[0] != "docs":
        return "active_runtime_reference"
    if relative in CURRENT_REFERENCE_DOCS:
        return "active_runtime_reference"
    if relative in CURRENT_MAINTENANCE_DOCS:
        return "current_maintenance"
    name = relative.name.lower()
    if (
        name.startswith("phase_")
        or "migration" in name
        or name == "semantic_state_runtime_refactor_plan.md"
    ):
        return "migration_compatibility"
    return "historical_provenance"


def skill_index_text(files: list[Path], version: str) -> str:
    """Render the Skill index as semantic navigation sections.

    Classification changes only index presentation. iter_files()/MANIFEST continue
    to retain every active-package file, including maintenance and historical
    provenance kept outside legacy/.
    """
    grouped = {key: [] for key, _ in SKILL_INDEX_SECTION_ORDER}
    for relative in files:
        grouped[skill_index_section(relative)].append(relative)

    lines = [
        "# HSK Active Skill File Index",
        "",
        f"当前 Skill 版本：{version}",
        "",
        "本索引按使用语义分区。只有 **Active Runtime & Reference** 表示默认活动导航；",
        "Maintenance / Migration / Historical 分区仅保留维护、兼容与 provenance，不因此成为 Runtime Authority。",
        "历史归档正文仍通过 `legacy/README.md` 追溯；所有本索引文件是否进入 MANIFEST 仍由 `iter_files()` 独立决定。",
        "",
    ]
    for key, title in SKILL_INDEX_SECTION_ORDER:
        members = grouped[key]
        if not members:
            continue
        lines.extend([f"## {title}", ""])
        lines.extend(f"- `{path.as_posix()}`" for path in members)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def compatibility_pointer(target: str) -> str:
    return (
        "# Compatibility Pointer\n\n"
        "该文件名仅为旧链接保留，不再承载活动索引。\n\n"
        f"请使用 [`{target}`]({target})。\n"
    )


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_manifest_bytes(path: Path, data: bytes) -> bytes:
    """Normalize line endings for UTF-8 text while preserving binary bytes exactly."""
    if path.suffix.lower() in BINARY_SUFFIXES:
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest_file(path: Path) -> str:
    return digest_bytes(normalized_manifest_bytes(path, path.read_bytes()))


def manifest_text(files: list[Path], overrides: dict[Path, str]) -> str:
    lines: list[str] = []
    for relative in files:
        if relative == MANIFEST.relative_to(ROOT):
            continue
        if relative in overrides:
            digest = digest_bytes(overrides[relative].encode("utf-8"))
        else:
            absolute = ROOT / relative
            if not absolute.is_file():
                raise FileNotFoundError(f"manifest source missing: {relative.as_posix()}")
            digest = digest_file(absolute)
        lines.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"




def _navigation_registrations() -> tuple[bool, bool]:
    """Read existing bootstrap pointers, without a new feature or version marker."""
    bootstrap = ROOT / "core/bootstrap.yaml"
    if not bootstrap.exists():
        return False, False  # Standalone old/fake roots need not have bootstrap.
    if not bootstrap.is_file():
        raise ValueError("navigation bootstrap must be a file")
    declaration = yaml.safe_load(bootstrap.read_text(encoding="utf-8-sig"))
    if not isinstance(declaration, dict):
        raise ValueError("navigation bootstrap must be a mapping")
    registrations = []
    for section, key in (("authoritative_sources", "routing"), ("entrypoints", "read_stage")):
        owner = declaration.get(section, {})
        if not isinstance(owner, dict):
            raise ValueError(f"navigation bootstrap {section} must be a mapping")
        if key in owner:
            pointer = owner[key]
            if not isinstance(pointer, str) or not pointer.strip():
                raise ValueError(f"navigation bootstrap {section}.{key} must be non-empty")
        registrations.append(key in owner)
    return registrations[0], registrations[1]


def lifecycle_navigation(router: dict, *, registered: bool = False) -> list[str]:
    """Project existing lifecycle pointers without selecting a route or a phase."""
    def mapping(owner: dict, key: str) -> dict | None:
        if key not in owner:
            return None  # Isolated roots may predate the lifecycle authorities.
        value = owner[key]
        if not isinstance(value, dict):
            raise ValueError(f"navigation source {key} must be a mapping")
        return value

    def text(value: object, source: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"navigation source {source} must be a non-empty string")
        return value.replace("`", "&#96;").replace("|", "\\|").replace("\n", " ")

    def string_list(owner: dict, key: str, source: str) -> list[str]:
        value = owner.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"navigation source {source}.{key} must be a list")
        return [text(item, f"{source}.{key}") for item in value]

    def scalar_parts(owner: dict, keys: tuple[str, ...], source: str) -> list[str]:
        return [f"{key}=`{text(owner[key], f'{source}.{key}')}`" for key in keys if key in owner]

    def boolean_part(owner: dict, key: str, source: str) -> list[str]:
        if key not in owner:
            return []
        if not isinstance(owner[key], bool):
            raise ValueError(f"navigation source {source}.{key} must be boolean")
        return [f"{key}=`{str(owner[key]).lower()}`"]

    routes = mapping(router, "routing")
    segments = mapping(router, "runtime_segments")
    memory = mapping(router, "project_memory_contract")
    if registered:
        for name, section in (("routing", routes), ("runtime_segments", segments),
                              ("project_memory_contract", memory)):
            if not section:
                raise ValueError(f"registered routing requires non-empty {name}")
    if routes is None and segments is None and memory is None:
        return []
    lines = [
        "## Whole-workflow navigation (original router owns selection and boundaries)",
        "",
        "Derived from the original `core/workflow_router.yaml` sections below.",
        "Route `load` / `then` and segment resource lists are raw availability inventories,",
        "not the effective `read_now`. Current evidence, boundary truncation, conditional packs,",
        "backend/template adaptation and dependency closure still belong to the existing resolver.",
        "Use its current `reading_plan.read_now`, `conditional`, `reasons`, `pause_state` and",
        "ordered `pre_delivery_gates`; this table does not compute a profile or a gate list.",
        "With GitHub-only access, read the original route, applicable boundaries and project facts;",
        "do not invent resolver output, accepted evidence or a completed gate.",
        "Default inventory and loading boundaries: `core/workflow_router.yaml#default_load` and",
        "`core/workflow_router.yaml#load_policy`. Full-fallback reasons come from the actual",
        "`reading_plan.reasons`; an unlisted or unresolved narrow scope remains conservative.",
        "",
    ]
    if routes is not None:
        lines += [
            "### Route authority pointers", "",
            "Read each route's original `load` / `then`; conditional flags below point back to",
            "that route and do not preload their resources or establish qualification.", "",
            "| Route | Original source | Declared roles / conditions / delegation |",
            "|---|---|---|",
        ]
        for name, route in routes.items():
            name = text(name, "routing key")
            if not isinstance(route, dict):
                raise ValueError(f"navigation source routing.{name} must be a mapping")
            source = f"routing.{name}"
            for key in ("load", "then"):
                string_list(route, key, source)
            roles = string_list(route, "boundary_roles", source)
            details = [f"roles=`{', '.join(roles)}`"] if roles else []
            conditional = mapping(route, "conditional_stage")
            if conditional is not None:
                if not all(key in conditional for key in ("when", "module", "insert_before")):
                    raise ValueError(f"navigation source {source}.conditional_stage is incomplete")
                details.extend(scalar_parts(conditional, ("when", "module", "insert_before", "pause_state"),
                                            f"{source}.conditional_stage"))
            for key in ("pause_for_user_execution", "load_classified_task_packs",
                        "load_competition_pack", "load_proposition_pack"):
                details.extend(boolean_part(route, key, source))
            details.extend(scalar_parts(route, ("execution_sequence", "writing_execution_sequence"), source))
            lines.append(f"| `{name}` | `core/workflow_router.yaml#{source}` | {'; '.join(details) or '—'} |")
        lines.append("")
    if segments is not None:
        lines += [
            "### Runtime-boundary authority pointers", "",
            "These are declarations, not the current phase. Read each original `satisfied_when`,",
            "`required_load` / `final_load` and canonical route against current verified evidence.",
            "A declared condition or pause does not prove it was satisfied or that approval occurred.", "",
            "| Segment | Original source | Declared stage / stop / pause |",
            "|---|---|---|",
        ]
        for name, segment in segments.items():
            name = text(name, "runtime_segments key")
            if not isinstance(segment, dict):
                raise ValueError(f"navigation source runtime_segments.{name} must be a mapping")
            source = f"runtime_segments.{name}"
            for key in ("required_load", "final_load"):
                string_list(segment, key, source)
            condition = mapping(segment, "satisfied_when")
            if condition is not None:
                string_list(condition, "any", f"{source}.satisfied_when")
                groups = condition.get("all_groups", [])
                if not isinstance(groups, list):
                    raise ValueError(f"navigation source {source}.satisfied_when.all_groups must be a list")
                for group in groups:
                    string_list({"group": group}, "group", f"{source}.satisfied_when.all_groups")
            details = scalar_parts(segment, ("role", "canonical_route", "stage_module", "stop_before_module",
                                             "reset_from_module", "pause_state"), source)
            details.extend(boolean_part(segment, "pause_for_user_execution", source))
            lines.append(f"| `{name}` | `core/workflow_router.yaml#{source}` | {'; '.join(details) or '—'} |")
        lines.append("")
    if memory is not None:
        source = "project_memory_contract"
        lines += ["### Project-memory and recovery authority pointers", "",
                  "Source: `core/workflow_router.yaml#project_memory_contract`; its rules own recovery.", ""]
        for key in ("project_file", "numeric_fact_source", "machine_state_source"):
            lines.append(f"- {key}: `{text(memory.get(key), f'{source}.{key}')}`")
        for key in ("read_before_modules", "targeted_read_sections", "full_read_when"):
            if key == "full_read_when" and key not in memory:
                raise ValueError("navigation source project_memory_contract.full_read_when is missing")
            values = string_list(memory, key, source)
            lines.append(f"- {key}: {', '.join(f'`{value}`' for value in values) or '—'}")
        lines += [
            "", "Apply the original full-read events to the current complete framework; ordinary",
            "targeted reads retain their original scope. Recovering source text does not recover",
            "approval, numeric acceptance or gate PASS from a chat summary. This navigation does",
            "not detect context compression or substitute for checking current project evidence.", "",
        ]
    return lines


def stage_reading_guide_text() -> str:
    """Generate navigation from existing routing/writing authorities, never copied rules."""
    router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
    writing = yaml.safe_load((ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8"))
    if not isinstance(router, dict) or not isinstance(writing, dict):
        raise ValueError("stage navigation authorities must be mappings")
    reading = router["reading_policy"]
    stages = writing["template_first_progressive_authoring"]["stages"]
    # A registered lifecycle cannot silently downgrade to a pre-lifecycle root.
    registered, _ = _navigation_registrations()
    lifecycle = lifecycle_navigation(router, registered=registered)
    router_source = "core/workflow_router.yaml" if lifecycle else "core/workflow_router.yaml#reading_policy"
    lines = [
        "# Stage Reading Guide (generated navigation)",
        "",
        f"Generated from `{router_source}` and",
        "`core/writing_runtime_contract.yaml#template_first_progressive_authoring.stages`.",
        "This is a source and conditional pointer inventory, not source text,",
        "a duplicate phase registry, proof of reading, an approval, or a gate result.",
        "Resolve current project facts and use the selected commit of the original Authority.",
        "",
        "## Common source selectors",
        "",
    ]

    def render(entry: str | dict, kind: str) -> str:
        if isinstance(entry, str):
            return f"- {kind}: `{entry}`"
        if not isinstance(entry, dict) or "path" not in entry:
            raise ValueError("reading source entry has no path")
        selector = entry.get("headings") or entry.get("yaml_paths") or []
        suffix = f"; selector={selector!r}" if selector else ""
        condition = f"; when={entry['when']}" if entry.get("when") else ""
        return f"- {kind}: `{entry['path']}`{suffix}{condition}"

    for entry in reading.get("common_reads", []):
        lines.append(render(entry, "read_now"))
    if lifecycle:
        lines += [""] + lifecycle
    lines += ["", "## Routing profiles (selection belongs to the resolver)", ""]
    for name, profile in reading.get("profiles", {}).items():
        lines += [f"### {name}", ""]
        for entry in profile.get("read_now", []):
            lines.append(render(entry, "read_now"))
        for entry in profile.get("conditional", []):
            lines.append(render(entry, "conditional"))
        lines.append("")
    lines += ["## CUMCM writing stages (order belongs to writing runtime)", ""]
    for stage in stages:
        lines += [f"### {stage['id']}", ""]
        preflight = stage.get("before_write_preflight") or {}
        for entry in preflight.get("read_now", []):
            lines.append(render(entry, "preflight"))
        for entry in stage.get("read_now", []):
            lines.append(render(entry, "read_now"))
        for name, branch in (stage.get("conditional_reads_before_relevant_passage") or {}).items():
            lines.append(f"- conditional branch: `{name}`; when={branch.get('when', 'unresolved')}")
            for entry in branch.get("read", []):
                lines.append(render(entry, "conditional source"))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def generated_payloads() -> dict[Path, str]:
    version = current_skill_version()
    guide_sources = (
        ROOT / "core" / "workflow_router.yaml",
        ROOT / "core" / "writing_runtime_contract.yaml",
    )
    _, body_interface_registered = _navigation_registrations()
    sources_present = all(path.is_file() for path in guide_sources)
    if body_interface_registered and not sources_present:
        missing = ", ".join(path.relative_to(ROOT).as_posix()
                            for path in guide_sources if not path.is_file())
        raise FileNotFoundError(f"registered read_stage interface requires guide source: {missing}")
    # Archived and isolated roots may predate this guide's two canonical sources.
    # A historical routing pointer alone does not register the later body reader.
    # Preserve their legacy output; registered missing sources fail above and
    # malformed available authorities fail inside stage_reading_guide_text().
    guide_payload = (
        stage_reading_guide_text()
        if sources_present
        else None
    )
    files = iter_files()
    if guide_payload is None:
        files = [path for path in files if path != STAGE_GUIDE_RELATIVE]
    corpus_root = ROOT / "knowledge" / "case_memory"
    case_relative = Path("knowledge/case_memory/index.json")
    case_payloads = {}
    # Old archived/fake repositories without this optional Authority keep their
    # original generator. A registered but missing corpus must fail closed.
    registered = "knowledge/case_memory/schema.yaml" in BOOTSTRAP.read_text(encoding="utf-8-sig")
    if corpus_root.exists() or registered:
        # Also work when this module is loaded by path, outside a script CLI.
        script_dir = str(Path(__file__).resolve().parent)
        sys.path.insert(0, script_dir)
        try:
            from case_memory import build_index
        finally:
            sys.path.pop(0)

        case_payloads[case_relative] = json.dumps(
            build_index(corpus_root), ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        files = sorted(set(files) | {case_relative}, key=lambda item: item.as_posix())
    template_files = template_index_files(files)
    skill_payload = skill_index_text(files, version)
    template_payload = index_text("HSK Active Template Index", template_files, version)
    legacy_skill_payload = compatibility_pointer(SKILL_INDEX.name)
    legacy_template_payload = compatibility_pointer(TEMPLATE_INDEX.name)
    overrides = {
        SKILL_INDEX.relative_to(ROOT): skill_payload,
        TEMPLATE_INDEX.relative_to(ROOT): template_payload,
        LEGACY_SKILL_INDEX.relative_to(ROOT): legacy_skill_payload,
        LEGACY_TEMPLATE_INDEX.relative_to(ROOT): legacy_template_payload,
        **case_payloads,
    }
    if guide_payload is not None:
        overrides[STAGE_GUIDE_RELATIVE] = guide_payload
    payloads = {
        SKILL_INDEX: skill_payload,
        TEMPLATE_INDEX: template_payload,
        LEGACY_SKILL_INDEX: legacy_skill_payload,
        LEGACY_TEMPLATE_INDEX: legacy_template_payload,
        **{ROOT / path: payload for path, payload in case_payloads.items()},
    }
    if guide_payload is not None:
        payloads[ROOT / STAGE_GUIDE_RELATIVE] = guide_payload
    payloads[MANIFEST] = manifest_text(files, overrides)
    return payloads


def write_lf_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files differ from repository state")
    args = parser.parse_args()
    payloads = generated_payloads()
    if args.check:
        differences = []
        for path, expected in payloads.items():
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != expected:
                differences.append(path.relative_to(ROOT).as_posix())
        if differences:
            print("generated indexes are stale:")
            for item in differences:
                print("-", item)
            return 1
        print("generated indexes are current")
        return 0
    for path, text in payloads.items():
        write_lf_text(path, text)
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
