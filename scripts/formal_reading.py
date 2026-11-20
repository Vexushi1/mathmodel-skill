"""Read and verify formal-start rule volumes at one immutable Git commit."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml

from rule_corpus import (DECLARATION, DIRECTORY, REGISTRY_PATH, VOLUME_BYTES,
                         part_header, registered_sources, source_ranges)


MANIFEST_PATH = f"{DIRECTORY}/manifest.json"


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"pinned Git source unavailable: {args[-1]}")
    return result.stdout


def _blob_id(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return sha1(header + raw).hexdigest()


class PinnedCorpus:
    """Load the expected digest from the fixed tree, independently of each response."""

    def __init__(self, root: Path, commit: str):
        self.root = root
        self.commit = commit
        raw = _git_bytes(root, "cat-file", "blob", f"{commit}:{MANIFEST_PATH}")
        content = json.loads(raw)
        if (not isinstance(content, dict) or type(content.get("schema_version")) is not int
                or content["schema_version"] != 1):
            raise ValueError("unsupported formal-reading manifest schema")
        self.manifest_sha256 = sha256(raw).hexdigest()
        self.git_blobs = {}
        self.git_sizes = {}
        tracked = set()
        tree = _git_bytes(root, "ls-tree", "-r", "-l", "-z", commit)
        for record in tree.split(b"\0"):
            if not record:
                continue
            header, name = record.split(b"\t", 1)
            path = name.decode("utf-8")
            tracked.add(path)
            mode, kind, object_id, size = header.split()
            if kind == b"blob" and mode in (b"100644", b"100755"):
                self.git_blobs[path] = object_id.decode("ascii")
                self.git_sizes[path] = int(size)
        self._source_cache = {}
        self._line_starts = {}
        self._last_volume = ""
        delegator = yaml.safe_load(self._source(DECLARATION))
        registry = self._source(REGISTRY_PATH)
        if (not isinstance(delegator, dict) or delegator.get("rule_corpus") != REGISTRY_PATH
                or content.get("registry") != {"path": REGISTRY_PATH, "git_blob_sha1": self.git_blobs[REGISTRY_PATH],
                                               "sha256": sha256(registry).hexdigest()}):
            raise ValueError("registry identity differs from the pinned declaration")
        try:
            members, aliases, excerpts = registered_sources(tracked, yaml.safe_load(registry))
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("malformed pinned rule corpus source registry") from error
        self.volumes = self._volumes(content.get("volumes"), tracked)
        self._parts = {path: [] for path in self.volumes}
        self.sources = {}
        sources = content.get("sources")
        if (not isinstance(sources, list) or not all(isinstance(row, dict) for row in sources)
                or [row.get("path") for row in sources] != list(members)):
            raise ValueError("source inventory differs from pinned registry")
        self.source_count = len(sources)
        for row in sources:
            path = row["path"]
            mirrors = sorted(name for name, canonical in aliases.items() if canonical == path)
            if row.get("role") != members[path] or row.get("aliases") != mirrors:
                raise ValueError(f"source role or aliases differ from pinned registry: {path}")
            for name in [path, *mirrors]:
                if (name not in self.git_blobs or self.git_blobs[name] != row.get("git_blob_sha1")
                        or type(row.get("bytes")) is not int or row["bytes"] != self.git_sizes[name]):
                    raise ValueError(f"source differs from pinned manifest: {name}")
                self.sources[name] = row
            if not self._digest(row.get("sha256")):
                raise ValueError(f"invalid source digest: {path}")
            ranges = (source_ranges(self._source(path), excerpts[path], path)
                      if path in excerpts else [(0, self.git_sizes[path])])
            self._register_parts(row, ranges)
        for path, parts in self._parts.items():
            if not parts or parts[-1][1]["volume_end"] != self.volumes[path]["bytes"]:
                raise ValueError(f"missing volume body in pinned manifest: {path}")

    @staticmethod
    def _digest(value) -> bool:
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None

    def _source(self, path: str) -> bytes:
        if path not in self._source_cache:
            self._source_cache[path] = _git_bytes(self.root, "cat-file", "blob", f"{self.commit}:{path}")
        return self._source_cache[path]

    def _volumes(self, rows, tracked):
        if not isinstance(rows, list) or not rows or len(rows) > 999:
            raise ValueError("empty or invalid formal-reading volume inventory")
        result = {}
        for number, row in enumerate(rows, 1):
            path = f"{DIRECTORY}/volumes/{number:03d}.md"
            if (not isinstance(row, dict) or row.get("path") != path or path not in self.git_blobs
                    or type(row.get("bytes")) is not int or not 1 <= row["bytes"] <= VOLUME_BYTES
                    or row["bytes"] != self.git_sizes[path] or not self._digest(row.get("sha256"))):
                raise ValueError(f"invalid or unavailable volume in pinned manifest: {path}")
            result[path] = row
        if {p for p in tracked if p.startswith(f"{DIRECTORY}/volumes/")} != set(result):
            raise ValueError("volume inventory differs from the pinned tree")
        return result

    def _register_parts(self, row, ranges):
        path = row["path"]
        parts = row.get("parts")
        if not isinstance(parts, list) or not parts:
            raise ValueError(f"source has no registered text: {path}")
        index = 0
        cursor = ranges[0][0]
        for part in parts:
            keys = ("start", "end", "volume_start", "volume_end", "line_start", "line_end")
            if not isinstance(part, dict) or any(type(part.get(k)) is not int for k in keys):
                raise ValueError(f"invalid source fragment in pinned manifest: {path}")
            volume = part.get("volume")
            start, end = part["start"], part["end"]
            if (not isinstance(volume, str) or volume not in self.volumes or volume < self._last_volume
                    or index >= len(ranges)
                    or start != cursor or not start < end <= ranges[index][1]
                    or not 1 <= part["line_start"] <= part["line_end"] or not self._digest(part.get("sha256"))):
                raise ValueError(f"fragment outside registered source ranges: {path}")
            self._last_volume = volume
            entries = self._parts[volume]
            previous = entries[-1][1]["volume_end"] if entries else 0
            header = part_header(path, row["role"], start, part["line_start"])
            if (part["volume_start"] != previous + len(header)
                    or part["volume_end"] - part["volume_start"] != end - start
                    or part["volume_end"] > self.volumes[volume]["bytes"]):
                raise ValueError(f"invalid source-to-volume offsets: {path} in {volume}")
            entries.append((path, part, header))
            cursor = end
            if cursor == ranges[index][1]:
                index += 1
                if index < len(ranges):
                    cursor = ranges[index][0]
        if index != len(ranges):
            raise ValueError(f"registered ranges are incomplete for {path}")

    def identity(self) -> dict[str, str]:
        return {"source_commit": self.commit, "manifest_path": MANIFEST_PATH,
                "manifest_sha256": self.manifest_sha256}

    def catalog(self, offset: int, limit: int, source: str | None = None) -> dict[str, Any]:
        if source is not None:
            if source not in self.sources:
                raise ValueError(f"unregistered formal-reading source: {source}")
            descriptor = self.sources[source]
            parts = descriptor["parts"]
            return {**self.identity(), "status": "catalog_only",
                    "source": {k: v for k, v in descriptor.items() if k != "parts"},
                    "part_count": len(parts), "offset": offset, "parts": parts[offset:offset + limit],
                    "next_offset": offset + limit if offset + limit < len(parts) else None}
        volumes = list(self.volumes.values())
        return {**self.identity(), "status": "catalog_only", "source_count": self.source_count,
                "volume_count": len(volumes), "offset": offset, "volumes": volumes[offset:offset + limit],
                "next_offset": offset + limit if offset + limit < len(volumes) else None}

    def valid_bytes(self, path: str, raw: bytes) -> bool:
        expected = self.volumes[path]
        if (len(raw) != expected["bytes"] or sha256(raw).hexdigest() != expected["sha256"]
                or _blob_id(raw) != self.git_blobs[path]):
            return False
        for source, part, header in self._parts[path]:
            body = self._source(source)
            if source not in self._line_starts:
                if sha256(body).hexdigest() != self.sources[source]["sha256"]:
                    return False
                self._line_starts[source] = [0, *(match.end() for match in re.finditer(b"\n", body))]
            lines = self._line_starts[source]
            start, end = part["volume_start"], part["volume_end"]
            selected = body[part["start"]:part["end"]]
            if (raw[start - len(header):start] != header or raw[start:end] != selected
                    or sha256(selected).hexdigest() != part["sha256"]
                    or bisect_right(lines, part["start"]) != part["line_start"]
                    or bisect_right(lines, part["end"] - 1) != part["line_end"]):
                return False
        return True

    def read(self, path: str) -> dict[str, Any]:
        if path not in self.volumes:
            raise ValueError(f"volume is not listed at the selected commit: {path}")
        raw = _git_bytes(self.root, "cat-file", "blob", f"{self.commit}:{path}")
        if not self.valid_bytes(path, raw):
            raise ValueError(f"committed volume differs from pinned manifest: {path}")
        return {**self.identity(), "volume": path, "text": raw.decode("utf-8"),
                "status": "source_text_returned", "gate_status": "not_executed_by_reader"}

    def verify(self, received: list[Path], offset: int, limit: int) -> dict[str, Any]:
        accepted = set()
        issues = []
        for file in received:
            try:
                response = json.loads(file.read_bytes())
                if not isinstance(response, dict):
                    raise ValueError("expected an actual read response")
                if any(response.get(k) != v for k, v in self.identity().items()):
                    raise ValueError("response commit or manifest identity differs")
                path = response.get("volume")
                if not isinstance(path, str) or path not in self.volumes:
                    raise ValueError("volume is not in this pinned manifest")
                body = response.get("text")
                if not isinstance(body, str) or not self.valid_bytes(path, body.encode("utf-8")):
                    raise ValueError(f"missing or altered volume text: {path}")
                accepted.add(path)
            except (ValueError, OSError) as error:
                issues.append({"file": str(file), "error": str(error)})
        missing = [path for path in self.volumes if path not in accepted]
        complete = not missing and not issues
        return {**self.identity(), "complete": complete,
                "status": "supplied_bytes_verified" if complete else "reading_incomplete",
                "volume_count": len(self.volumes), "verified_volume_count": len(accepted),
                "missing_count": len(missing), "missing_volumes": missing[offset:offset + limit],
                "issue_count": len(issues), "issues": issues[offset:offset + limit], "offset": offset,
                "next_offset": offset + limit if offset + limit < max(len(missing), len(issues)) else None,
                "context_retention": "not_observable", "gate_status": "not_executed_by_reader"}


def main(argv: list[str], default_root: Path, verify_checkout) -> int:
    parser = argparse.ArgumentParser(prog="read_stage.py formal", description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("manifest", "read", "verify"):
        command = commands.add_parser(action)
        command.add_argument("--root", type=Path, default=default_root)
        command.add_argument("--source-commit", required=True, help="full 40-character pinned Git commit")
        if action == "read":
            command.add_argument("--volume", required=True, help="repository-relative path from the manifest")
        else:
            command.add_argument("--offset", default=0, type=int)
            command.add_argument("--limit", default=24, type=int)
        if action == "manifest":
            command.add_argument("--source", help="look up the registered fragments of a source or physical alias")
        if action == "verify":
            command.add_argument("--received", type=Path, nargs="+", action="extend", default=[],
                                 help="saved UTF-8 JSON read response(s), including original text")
            command.add_argument("--received-dir", type=Path, help="directory of saved *.json read responses")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        commit = verify_checkout(root, args.source_commit)
        corpus = PinnedCorpus(root, commit)
        if args.action != "read" and (args.offset < 0 or not 1 <= args.limit <= 100):
            raise ValueError("use a nonnegative offset and a limit of 1 to 100")
        if args.action == "manifest":
            result = corpus.catalog(args.offset, args.limit, args.source)
        elif args.action == "read":
            result = corpus.read(args.volume)
        else:
            if args.received_dir is not None:
                if not args.received_dir.is_dir():
                    raise ValueError("received-dir is not a directory")
                args.received.extend(sorted(args.received_dir.glob("*.json")))
            result = corpus.verify(args.received, args.offset, args.limit)
    except (ValueError, OSError, yaml.YAMLError) as error:
        parser.exit(2, f"reading incomplete: {error}\n")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return int(args.action == "verify" and not result["complete"])
