"""Build bounded UTF-8 reading volumes from the reviewed source roles in the module manifest."""
from __future__ import annotations

import bisect
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

import yaml

DECLARATION = "core/module_manifest.yaml"
REGISTRY_PATH = "core/rule_corpus_sources.yaml"
DIRECTORY = "core/full_reading"
VOLUME_BYTES = 12 * 1024
GENERATED = re.compile(r"core/full_reading/(?:manifest\.json|volumes/[0-9]{3}\.md)\Z")


def _inventory(root: Path) -> set[str]:
    """Check a Git working tree, including new source files, or an unpacked resource root."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True, stdout=subprocess.PIPE,
        )
        return {name.decode("utf-8") for name in result.stdout.split(b"\0") if name}
    files = set()
    for base, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}]
        for name in names:
            files.add((Path(base) / name).relative_to(root).as_posix())
    return files


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _body(root: Path, name: str) -> bytes:
    path = root / name
    if not path.is_relative_to(root) or path.resolve() != path or not path.is_file():
        raise ValueError(f"expected a regular source file at {name}")
    data = path.read_bytes()
    if not data or b"\x00" in data:
        raise ValueError(f"empty or binary normative source: {name}")
    data.decode("utf-8")
    return data


def registered_sources(available: set[str], declaration: dict):
    """Classify an independently enumerated tree and return its canonical members."""
    if not isinstance(declaration, dict) or type(declaration.get("schema_version")) is not int or declaration["schema_version"] != 1:
        raise ValueError("unsupported rule corpus source registry")
    roles = {}
    aliases = declaration["aliases"]
    excerpts = declaration["excerpts"]
    trees = declaration["excluded_trees"]
    members = {}

    def register(name, role):
        if name not in available or name in roles or GENERATED.fullmatch(name):
            raise ValueError(f"missing, duplicate or generated source registration: {name}")
        roles[name] = role

    for role, names in declaration["members"].items():
        for name in names:
            register(name, role)
            members[name] = role
    for name, spec in excerpts.items():
        register(name, spec["role"])
        members[name] = spec["role"]
    for alias, original in aliases.items():
        register(alias, "alias")
        if original not in members or alias == original:
            raise ValueError(f"alias {alias} must name a canonical source")
    for role, names in declaration["excluded"].items():
        for name in names:
            register(name, role)
    # These namespaces have an unconditional lifecycle role (e.g. tests and archives).
    # Mixed-use directories, including docs/, scripts/ and templates/, have no fallback.
    for name in available:
        if GENERATED.fullmatch(name):
            continue
        if name.split("/", 1)[0] in trees:
            if name in roles:
                raise ValueError(f"ambiguous namespace and source registration: {name}")
        elif name not in roles:
            raise ValueError(f"unclassified repository path: {name}")
    if not members:
        raise ValueError("rule corpus has no normative members")
    return members, aliases, excerpts


def source_ranges(data: bytes, spec: dict | None, name: str):
    """Resolve exact whole-line anchors, retaining each original byte and line ending."""
    if spec is None:
        return [(0, len(data))]
    offsets = {}
    pos = 0
    for line in data.splitlines(keepends=True):
        offsets.setdefault(line.rstrip(b"\r\n").decode("utf-8"), []).append(pos)
        pos += len(line)

    def locate(label, default):
        if label is None:
            return default
        matches = offsets.get(label, ())
        if len(matches) != 1:
            raise ValueError(f"missing or ambiguous corpus anchor in {name}: {label}")
        return matches[0]

    ranges = []
    for first, following in spec["ranges"]:
        start, end = locate(first, 0), locate(following, len(data))
        if start >= end or (ranges and start < ranges[-1][1]):
            raise ValueError(f"empty, overlapping or unordered corpus range in {name}")
        ranges.append((start, end))
    if not ranges:
        raise ValueError(f"no selected text in {name}")
    return ranges


def part_header(name: str, role: str, start: int, line_start: int) -> bytes:
    target = f"../../../{quote(name)}#L{line_start}"
    return f"\n\n## [{name}]({target}) · {role} · byte {start}\n\n".encode()


def _blob_id(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


class _Volumes:
    def __init__(self):
        self.files = {}
        self.current = bytearray()

    def _path(self):
        number = len(self.files) + 1
        if number > 999:
            raise ValueError("volume count exceeds the three-digit filename format")
        return f"{DIRECTORY}/volumes/{number:03d}.md"

    def finish(self):
        if self.current:
            self.files[self._path()] = bytes(self.current)
            self.current.clear()

    def add(self, name, role, data, lines, start, end):
        while start < end:
            line_start = bisect.bisect_right(lines, start)
            header = part_header(name, role, start, line_start)
            space = VOLUME_BYTES - len(self.current) - len(header)
            # Prefer keeping a small source in one volume over splitting its last few lines.
            if self.current and (space < 256 or space < end - start <= VOLUME_BYTES - len(header)):
                self.finish()
                continue
            if space < 4:
                raise ValueError(f"source header exceeds reading volume capacity: {name}")
            stop = min(end, start + space)
            if stop < end:
                newline = data.rfind(b"\n", start, stop)
                if newline >= start:
                    stop = newline + 1
                else:
                    while data[stop] & 0xC0 == 0x80:
                        stop -= 1
            self.current.extend(header)
            volume_start = len(self.current)
            body = data[start:stop]
            self.current.extend(body)
            yield {
                "volume": self._path(), "start": start, "end": stop,
                "line_start": line_start,
                "line_end": bisect.bisect_right(lines, stop - 1),
                "volume_start": volume_start, "volume_end": len(self.current), "sha256": _sha(body),
            }
            start = stop
            if start < end:
                self.finish()


def _build(root: Path, registry_path: str):
    if registry_path != REGISTRY_PATH:
        raise ValueError(f"rule_corpus must point to {REGISTRY_PATH}")
    raw_registry = _body(root, REGISTRY_PATH)
    members, aliases, excerpts = registered_sources(_inventory(root), yaml.safe_load(raw_registry))
    if REGISTRY_PATH in members or REGISTRY_PATH in aliases:
        raise ValueError("the source registry itself is selection metadata")
    sources = []
    volumes = _Volumes()
    for name, role in members.items():
        data = _body(root, name)
        mirrors = sorted(alias for alias, original in aliases.items() if original == name)
        for alias in mirrors:
            if _body(root, alias) != data:
                raise ValueError(f"physical alias {alias} differs from {name}")
        lines = [0, *(match.end() for match in re.finditer(b"\n", data))]
        parts = []
        for start, end in source_ranges(data, excerpts.get(name), name):
            parts.extend(volumes.add(name, role, data, lines, start, end))
        sources.append({
            "path": name, "role": role, "aliases": mirrors, "bytes": len(data),
            "sha256": _sha(data),
            "git_blob_sha1": _blob_id(data),
            "parts": parts,
        })
    volumes.finish()
    index = {
        "schema_version": 1,
        "registry": {"path": REGISTRY_PATH, "git_blob_sha1": _blob_id(raw_registry), "sha256": _sha(raw_registry)},
        "offsets": "zero-based half-open raw UTF-8 bytes; original file line numbers are one-based",
        "volumes": [{"path": path, "bytes": len(data), "sha256": _sha(data)}
                    for path, data in volumes.files.items()],
        "sources": sources,
    }
    return index, volumes.files


def _manifest(root):
    document = yaml.safe_load((root / DECLARATION).read_bytes())
    if not isinstance(document, dict):
        raise ValueError(f"expected mapping in {DECLARATION}")
    return document


def build_corpus(root: Path) -> tuple[dict, dict[str, bytes]]:
    """Construct the registered corpus from a single root, without writing files."""
    root = Path(root).resolve()
    declaration = _manifest(root).get("rule_corpus")
    if declaration is None:
        raise ValueError("fixed source does not declare a rule corpus")
    return _build(root, declaration)


def generated_payloads(root: Path) -> dict[Path, str]:
    """UTF-8 payloads for the existing generator. Older unregistered resources produce none."""
    root = Path(root).resolve()
    manifest = _manifest(root) if (root / DECLARATION).exists() else {}
    if "rule_corpus" not in manifest:
        assurance_path = root / "core/runtime_assurance_contract.yaml"
        if assurance_path.is_file():
            assurance = yaml.safe_load(assurance_path.read_bytes())
            if not isinstance(assurance, dict) or not isinstance(assurance.get("reading_plan", {}), dict):
                raise ValueError("invalid runtime assurance registration")
            if "formal_rule_delivery" in assurance.get("reading_plan", {}):
                raise ValueError("formal_rule_delivery requires core/module_manifest.yaml#rule_corpus")
        return {}
    index, volumes = _build(root, manifest["rule_corpus"])
    payloads = {root / path: data.decode("utf-8") for path, data in volumes.items()}
    payloads[root / DIRECTORY / "manifest.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    return payloads
