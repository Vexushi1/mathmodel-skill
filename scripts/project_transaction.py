#!/usr/bin/env python3
"""Recoverable file transactions for project-state writers.

This module owns file-safety mechanics only. It intentionally does not own semantic,
stale, workbook, competition, or resolver policy.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
import hashlib
import json
import os
import stat
import threading
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import tempfile
from typing import Any
import uuid

import yaml

STATE_RELATIVE_PATH = "state/project_state.yaml"
JOURNAL_RELATIVE_PATH = "state/.project_transaction.yaml"
LOCK_RELATIVE_PATH = "state/.project_transaction.lock"
JOURNAL_VERSION = 1
ARCHIVE_JOURNAL_VERSION = 2
HISTORY_ARCHIVE_VERSION = 1
MAX_ARCHIVE_MANIFEST_BYTES = 8 * 1024 * 1024


class ProjectTransactionError(RuntimeError):
    """Base error for project transaction failures."""


class GenerationConflictError(ProjectTransactionError):
    """Raised when another writer changed project.state_generation."""


class ReadSetConflictError(ProjectTransactionError):
    """Raised when raw files no longer match the caller's captured read set."""


class TransactionRecoveryError(ProjectTransactionError):
    """Raised when a prepared transaction cannot be recovered safely."""


FailureHook = Callable[[str], None]
StagedValidator = Callable[[Mapping[str, Path]], None]


_THREAD_LOCKS_GUARD = threading.Lock()
_THREAD_LOCKS: dict[str, threading.Lock] = {}


def _thread_lock_for(root: Path) -> threading.Lock:
    key = str(root.resolve())
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.Lock())


@contextmanager
def _project_lock(project_root: Path):
    """Serialize control-plane writers locally while generation still detects stale callers.

    The lock is project-local and advisory; it is not an external lock service. A
    process waiting for the lock keeps its originally-read expected generation, so
    once the preceding writer commits it is rejected by the generation check rather
    than silently rebasing its stale in-memory state.
    """
    root = Path(project_root).resolve()
    lock_path = _resolve_inside(root, LOCK_RELATIVE_PATH)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    local_lock = _thread_lock_for(root)
    with local_lock:
        with lock_path.open("a+b") as handle:
            if os.name == "nt":
                import msvcrt

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _with_project_lock(function):
    @wraps(function)
    def wrapped(project_root: Path, *args, **kwargs):
        root = Path(project_root).resolve()
        with _project_lock(root):
            return function(root, *args, **kwargs)

    return wrapped


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def state_generation(state: Mapping[str, Any] | None) -> int:
    """Read generation with v8 compatibility: missing means generation zero."""
    project = (state or {}).get("project") or {}
    value = project.get("state_generation", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProjectTransactionError("project.state_generation must be a non-negative integer")
    return value


def _resolve_inside(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    candidate = Path(relative)
    path = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not path.is_relative_to(root):
        raise ProjectTransactionError(f"transaction target escapes project root: {relative}")
    return path


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _write_bytes_fsync(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace one text file using a same-directory staged file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            staged = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
        staged = None
        _fsync_directory(path.parent)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ProjectTransactionError(f"expected YAML mapping: {path}")
    return value


def _live_generation(root: Path, state_relative: str = STATE_RELATIVE_PATH) -> int:
    state_path = _resolve_inside(root, state_relative)
    return state_generation(_load_yaml_mapping(state_path)) if state_path.is_file() else 0


def _journal_path(root: Path) -> Path:
    return _resolve_inside(root, JOURNAL_RELATIVE_PATH)


def _invoke_failure(hook: FailureHook | None, point: str) -> None:
    if hook is not None:
        hook(point)


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _cleanup_entry_files(root: Path, entries: Sequence[Mapping[str, Any]]) -> None:
    for entry in entries:
        for field in ("staged", "backup"):
            value = str(entry.get(field, "")).strip()
            if value:
                _safe_unlink(_resolve_inside(root, value))


def _remove_journal(root: Path) -> None:
    journal = _journal_path(root)
    if journal.exists():
        journal.unlink()
        _fsync_directory(journal.parent)


def _recover_project_transaction_locked(project_root: Path) -> dict[str, Any]:
    """Roll a prepared transaction forward to its declared new hashes.

    Recovery never guesses. Every target must still match either the journal's old hash
    or its new hash, and the live generation must be either the base or target generation.
    """
    root = Path(project_root).resolve()
    journal_path = _journal_path(root)
    if not journal_path.is_file():
        return {"recovered": False, "status": "clean"}

    journal = _load_yaml_mapping(journal_path)
    _verify_journal_archives(root, journal)
    status = str(journal.get("status", ""))
    entries = journal.get("entries") or []
    if not isinstance(entries, list):
        raise TransactionRecoveryError("transaction journal entries must be a list")
    if status == "committed":
        _cleanup_entry_files(root, entries)
        _remove_journal(root)
        return {"recovered": True, "status": "committed_cleanup"}
    if status != "prepared":
        raise TransactionRecoveryError(f"unknown transaction journal status: {status or '<missing>'}")

    base_generation = journal.get("base_generation")
    target_generation = journal.get("target_generation")
    if not isinstance(base_generation, int) or not isinstance(target_generation, int):
        raise TransactionRecoveryError("transaction journal generation metadata is invalid")
    live_generation = _live_generation(root)
    if live_generation not in {base_generation, target_generation}:
        raise GenerationConflictError(
            f"cannot recover transaction: live generation {live_generation} is neither "
            f"base {base_generation} nor target {target_generation}"
        )

    for raw in entries:
        if not isinstance(raw, Mapping):
            raise TransactionRecoveryError("transaction journal entry must be a mapping")
        relative = str(raw.get("path", ""))
        target = _resolve_inside(root, relative)
        staged = _resolve_inside(root, str(raw.get("staged", "")))
        old_sha = raw.get("old_sha256")
        new_sha = str(raw.get("new_sha256", ""))
        existed = raw.get("existed") is True
        if len(new_sha) != 64:
            raise TransactionRecoveryError(f"invalid new hash in transaction journal: {relative}")

        if target.is_file() and sha256_file(target) == new_sha:
            continue

        if existed:
            if not target.is_file() or not old_sha or sha256_file(target) != old_sha:
                raise TransactionRecoveryError(
                    f"cannot recover {relative}: target matches neither recorded old nor new hash"
                )
        elif target.exists():
            raise TransactionRecoveryError(
                f"cannot recover {relative}: target unexpectedly exists with unknown content"
            )

        if not staged.is_file() or sha256_file(staged) != new_sha:
            raise TransactionRecoveryError(
                f"cannot recover {relative}: remaining staged file is missing or corrupt"
            )
        os.replace(staged, target)
        _fsync_directory(target.parent)

    for raw in entries:
        target = _resolve_inside(root, str(raw.get("path", "")))
        new_sha = str(raw.get("new_sha256", ""))
        if not target.is_file() or sha256_file(target) != new_sha:
            raise TransactionRecoveryError(f"transaction recovery verification failed: {target}")

    _verify_journal_archives(root, journal)
    committed = dict(journal)
    committed["status"] = "committed"
    atomic_write_text(journal_path, yaml.safe_dump(committed, allow_unicode=True, sort_keys=False))
    _cleanup_entry_files(root, entries)
    _remove_journal(root)
    return {
        "recovered": True,
        "status": "rolled_forward",
        "base_generation": base_generation,
        "target_generation": target_generation,
    }


@_with_project_lock
def recover_project_transaction(project_root: Path) -> dict[str, Any]:
    """Recover one prepared journal while holding the project-local writer lock."""
    return _recover_project_transaction_locked(Path(project_root).resolve())


def load_state_for_update(
    project_root: Path,
    *,
    state_relative: str = STATE_RELATIVE_PATH,
) -> tuple[Path, dict[str, Any], int]:
    """Recover any interrupted transaction, then load state with its generation."""
    root = Path(project_root).resolve()
    recover_project_transaction(root)
    state_path = _resolve_inside(root, state_relative)
    state = _load_yaml_mapping(state_path)
    return state_path, state, state_generation(state)


def _stage_transaction_files(
    root: Path,
    transaction_id: str,
    writes: Sequence[tuple[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    entries: list[dict[str, Any]] = []
    staged_map: dict[str, Path] = {}
    seen: set[str] = set()
    prepared_paths: list[Path] = []
    try:
        for index, (relative, content) in enumerate(writes):
            target = _resolve_inside(root, relative)
            canonical_relative = _relative(root, target)
            if canonical_relative in seen:
                raise ProjectTransactionError(f"duplicate transaction target: {canonical_relative}")
            seen.add(canonical_relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            staged = target.parent / f".{target.name}.txn-{transaction_id}-{index}.stage"
            backup = target.parent / f".{target.name}.txn-{transaction_id}-{index}.bak"
            # Track before I/O: a failed write/copy may already have created a file,
            # but the caller receives entries only after this function returns.
            prepared_paths.extend((staged, backup))
            _write_bytes_fsync(staged, content.encode("utf-8"))
            existed = target.is_file()
            old_sha = sha256_file(target) if existed else None
            if existed:
                shutil.copyfile(target, backup)
                # Windows CRT requires a writable descriptor for fsync.
                with backup.open("r+b") as handle:
                    os.fsync(handle.fileno())
                _fsync_directory(backup.parent)
            new_sha = sha256_file(staged)
            entry = {
                "path": canonical_relative,
                "staged": _relative(root, staged),
                "backup": _relative(root, backup) if existed else "",
                "existed": existed,
                "old_sha256": old_sha,
                "new_sha256": new_sha,
            }
            entries.append(entry)
            staged_map[canonical_relative] = staged
    except Exception:
        for path in prepared_paths:
            _safe_unlink(path)
        raise
    return entries, staged_map


def _canonical_relative_name(relative: str) -> None:
    """Validate lexical names without depending on current filesystem contents."""
    if (not isinstance(relative, str) or not relative or "\\" in relative
            or ":" in relative or "\0" in relative
            or PureWindowsPath(relative).drive or PurePosixPath(relative).is_absolute()
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ProjectTransactionError(f"read-set path must be canonical and project-relative: {relative!r}")
    if relative in {JOURNAL_RELATIVE_PATH, LOCK_RELATIVE_PATH}:
        raise ProjectTransactionError(f"read set cannot include transaction internals: {relative}")


def _guarded_path(root: Path, relative: str) -> Path:
    """Resolve an unambiguous project-relative POSIX path for a byte-bound write."""
    _canonical_relative_name(relative)
    path = _resolve_inside(root, relative)
    if _relative(root, path) != relative or (root / relative).is_symlink():
        raise ProjectTransactionError(f"read-set path resolves through an alias: {relative}")
    return path


def _prepare_read_set(
    root: Path,
    expected: Mapping[str, str | None],
    writes: Sequence[tuple[str, str]],
) -> dict[str, str | None]:
    """Copy the caller's snapshot, requiring state and every companion write target."""
    if not isinstance(expected, Mapping):
        raise ProjectTransactionError("expected_file_hashes must be a mapping")
    normalized: dict[str, str | None] = {}
    identities: set[str] = set()
    for relative, digest in expected.items():
        path = _guarded_path(root, relative)
        identity = os.path.normcase(str(path))
        if identity in identities:
            raise ProjectTransactionError(f"duplicate read-set target: {relative}")
        identities.add(identity)
        if digest is not None and (
            not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in digest)
        ):
            raise ProjectTransactionError(f"read-set hash must be SHA-256 or None: {relative}")
        normalized[relative] = digest.lower() if digest is not None else None
    for relative, _ in writes:
        _guarded_path(root, relative)
        if relative not in normalized:
            raise ProjectTransactionError(f"read set must include every write target: {relative}")
    return normalized


def _check_read_set(root: Path, expected: Mapping[str, str | None]) -> None:
    for relative, digest in expected.items():
        try:
            path = _guarded_path(root, relative)
            matches = (not os.path.lexists(path)) if digest is None else (
                path.is_file() and sha256_file(path) == digest
            )
        except (OSError, ProjectTransactionError) as exc:
            raise ReadSetConflictError(f"read-set path is no longer readable: {relative}") from exc
        if not matches:
            raise ReadSetConflictError(f"read-set content changed: {relative}")


def _check_staged_read_set(
    root: Path, entries: Sequence[Mapping[str, Any]], expected: Mapping[str, str | None],
) -> None:
    """Do not prepare a journal with inconsistent staged data or old-file evidence."""
    for entry in entries:
        relative = str(entry["path"])
        old_digest = expected[relative]
        if entry["old_sha256"] != old_digest or entry["existed"] != (old_digest is not None):
            raise ReadSetConflictError(f"staged old identity differs from read set: {relative}")
        staged = _resolve_inside(root, str(entry["staged"]))
        if not staged.is_file() or sha256_file(staged) != entry["new_sha256"]:
            raise ProjectTransactionError(f"staged content changed after construction: {relative}")
        if old_digest is not None:
            backup = _resolve_inside(root, str(entry["backup"]))
            if not backup.is_file() or sha256_file(backup) != old_digest:
                raise ProjectTransactionError(f"staged backup differs from read set: {relative}")


class HistoryArchiveError(ProjectTransactionError):
    """Archive preparation failed; any created directory is retained, never purged."""

    def __init__(self, message: str, *, archive_relative: str | None = None):
        super().__init__(message)
        self.archive_relative = archive_relative
        self.cleanup_status = "retained" if archive_relative is not None else "not_created"
        self.state_commit_performed = False


def _archive_reference(reference: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(reference, Mapping) or set(reference) != {"manifest", "sha256"}:
        raise ProjectTransactionError("archive reference must contain only manifest and sha256")
    path, digest = reference["manifest"], reference["sha256"]
    if not isinstance(path, str) or PurePosixPath(path).name != "manifest.json":
        raise ProjectTransactionError("archive reference must identify manifest.json")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in digest)):
        raise ProjectTransactionError("archive reference digest must be SHA-256")
    return {"manifest": path, "sha256": digest.lower()}


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate archive manifest key: {key}")
        result[key] = value
    return result


def _archive_regular_file(root: Path, relative: str) -> Path:
    path = _guarded_path(root, relative)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ProjectTransactionError(f"archive member must be an independent regular file: {relative}")
    return path


def verify_history_archive(project_root: Path, reference: Mapping[str, str]) -> dict[str, Any]:
    """Read/verify archived bytes against an external manifest digest, not live sources.

    This is not Schema, numerical or approval validation. No locks/files are created
    and no transaction is recovered. Immutability is a protocol invariant, not an
    OS-level protection from subsequent external changes.
    """
    root = Path(project_root).resolve()
    ref = _archive_reference(reference)
    manifest_path = _archive_regular_file(root, ref["manifest"])
    archive = manifest_path.parent
    if archive == root:
        raise ProjectTransactionError("archive must have its own project-relative directory")
    with manifest_path.open("rb") as handle:
        raw = handle.read(MAX_ARCHIVE_MANIFEST_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_MANIFEST_BYTES or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ProjectTransactionError("archive manifest digest or size is invalid")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (ValueError, UnicodeError) as exc:
        raise ProjectTransactionError("archive manifest is not unambiguous UTF-8 JSON") from exc
    if (not isinstance(manifest, dict) or set(manifest) != {"version", "base_generation", "files"}
            or type(manifest["version"]) is not int or manifest["version"] != HISTORY_ARCHIVE_VERSION
            or type(manifest["base_generation"]) is not int or manifest["base_generation"] < 0
            or not isinstance(manifest["files"], dict)):
        raise ProjectTransactionError("archive manifest structure/version is invalid")
    records = manifest["files"]
    source_hashes: dict[str, str | None] = {}
    archive_hashes = {ref["manifest"]: ref["sha256"]}
    expected_members = {"manifest.json", "files"}
    total_bytes = 0
    source_identities = set()
    for relative, record in records.items():
        _canonical_relative_name(relative)
        source = root / relative
        identity = os.path.normcase(str(source))
        if identity in source_identities:
            raise ProjectTransactionError("duplicate archived source path")
        source_identities.add(identity)
        if source == archive or source.is_relative_to(archive) or archive.is_relative_to(source):
            raise ProjectTransactionError("archive overlaps its original source paths")
        if not isinstance(record, dict) or set(record) != {"sha256", "size_bytes"}:
            raise ProjectTransactionError(f"invalid archive file record: {relative}")
        digest, size = record["sha256"], record["size_bytes"]
        if type(size) is not int or size < 0:
            raise ProjectTransactionError(f"invalid archived size: {relative}")
        if digest is not None and (not isinstance(digest, str) or len(digest) != 64
                                  or any(c not in "0123456789abcdef" for c in digest)):
            raise ProjectTransactionError(f"invalid archived digest: {relative}")
        stored = f"{archive.relative_to(root).as_posix()}/files/{relative}"
        stored_path = _guarded_path(root, stored)
        source_hashes[relative] = digest
        if digest is None:
            if size != 0 or os.path.lexists(stored_path):
                raise ProjectTransactionError(f"absent source has unexpected archived bytes: {relative}")
            continue
        stored_path = _archive_regular_file(root, stored)
        if stored_path.stat().st_size != size or sha256_file(stored_path) != digest:
            raise ProjectTransactionError(f"archived content changed: {relative}")
        archive_hashes[stored] = digest
        total_bytes += size
        member = PurePosixPath("files") / relative
        expected_members.add(member.as_posix())
        expected_members.update(parent.as_posix() for parent in member.parents if parent != PurePosixPath("."))
    if not source_hashes.get(STATE_RELATIVE_PATH):
        raise ProjectTransactionError("archive must preserve the original project state bytes")
    actual_members = set()
    for directory, names, filenames in os.walk(archive, followlinks=False):
        for name in names + filenames:
            path = Path(directory) / name
            if path.is_symlink():
                raise ProjectTransactionError("archive contains a symbolic link")
            actual_members.add(path.relative_to(archive).as_posix())
    if actual_members != expected_members:
        raise ProjectTransactionError("archive contains missing or unlisted members")
    try:
        saved_state = _load_yaml_mapping(archive / "files" / STATE_RELATIVE_PATH)
        generation = state_generation(saved_state)
    except (yaml.YAMLError, UnicodeError, AttributeError) as exc:
        raise ProjectTransactionError("archived state is not a valid generation-bearing mapping") from exc
    if generation != manifest["base_generation"]:
        raise ProjectTransactionError("archived state generation differs from manifest")
    if sha256_file(manifest_path) != ref["sha256"]:
        raise ProjectTransactionError("archive manifest changed during verification")
    return {"base_generation": manifest["base_generation"], "source_hashes": source_hashes,
            "archive_hashes": archive_hashes, "file_count": len(archive_hashes) - 1,
            "total_bytes": total_bytes}


@_with_project_lock
def prepare_history_archive(
    project_root: Path, archive_relative: str, *, expected_generation: int,
    expected_file_hashes: Mapping[str, str | None], reserve_bytes: int = 1024 * 1024,
    failure_hook: FailureHook | None = None,
) -> dict[str, str]:
    """Create one new byte-preserving archive of the explicitly confirmed read set.

    The caller owns evidence selection and archive layout. This function chooses no
    backend, changes no source, and writes no project-state reference. On failure an
    already-created directory is retained and reported in HistoryArchiveError; there
    is no recursive cleanup that could remove another process's historical evidence.
    A process crash can likewise leave an incomplete directory; never reuse it.
    """
    root = Path(project_root).resolve()
    if type(expected_generation) is not int or expected_generation < 0:
        raise ProjectTransactionError("expected_generation must be a non-negative integer")
    if type(reserve_bytes) is not int or reserve_bytes < 0:
        raise ProjectTransactionError("reserve_bytes must be a non-negative integer")
    expected = _prepare_read_set(root, expected_file_hashes, [(STATE_RELATIVE_PATH, "")])
    if expected[STATE_RELATIVE_PATH] is None:
        raise ProjectTransactionError("archive requires existing project state bytes")
    if os.path.lexists(_journal_path(root)):
        raise TransactionRecoveryError("explicit recovery and a fresh snapshot are required before archiving")
    archive = _guarded_path(root, archive_relative)
    if os.path.lexists(archive):
        raise HistoryArchiveError("archive destination already exists; never overwrite or reuse it")
    for relative in expected:
        source = _guarded_path(root, relative)
        if source == archive or source.is_relative_to(archive) or archive.is_relative_to(source):
            raise ProjectTransactionError("archive destination overlaps a declared source")
    _check_read_set(root, expected)
    if _live_generation(root) != expected_generation:
        raise GenerationConflictError("archive confirmation has a stale state generation")
    records = {
        relative: {"sha256": digest, "size_bytes": (root / relative).stat().st_size if digest else 0}
        for relative, digest in sorted(expected.items())
    }
    manifest = {"version": HISTORY_ARCHIVE_VERSION, "base_generation": expected_generation, "files": records}
    raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if len(raw) > MAX_ARCHIVE_MANIFEST_BYTES:
        raise HistoryArchiveError("archive manifest exceeds supported size")
    ancestor = archive.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    required_bytes = sum(record["size_bytes"] for record in records.values()) + len(raw) + reserve_bytes
    if shutil.disk_usage(ancestor).free < required_bytes:
        raise HistoryArchiveError("insufficient free space for verified archive and reserve")
    created = False
    try:
        _invoke_failure(failure_hook, "before_archive_create")
        _guarded_path(root, archive_relative)
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.mkdir(exist_ok=False)
        created = True
        _fsync_directory(archive.parent)
        for relative, record in records.items():
            if record["sha256"] is None:
                continue
            _invoke_failure(failure_hook, f"before_archive_copy:{relative}")
            source = _guarded_path(root, relative)
            if not source.is_file():
                raise ReadSetConflictError(f"archive source is no longer a regular file: {relative}")
            stored = _guarded_path(root, f"{archive_relative}/files/{relative}")
            stored.parent.mkdir(parents=True, exist_ok=True)
            digest, size = hashlib.sha256(), 0
            with source.open("rb") as src, stored.open("xb") as dst:
                if not stat.S_ISREG(os.fstat(src.fileno()).st_mode):
                    raise ProjectTransactionError("archive source is not a regular file")
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                dst.flush()
                os.fsync(dst.fileno())
            _fsync_directory(stored.parent)
            if digest.hexdigest() != record["sha256"] or size != record["size_bytes"]:
                raise ReadSetConflictError(f"source changed while archiving: {relative}")
            _invoke_failure(failure_hook, f"after_archive_copy:{relative}")
        _check_read_set(root, expected)
        if _live_generation(root) != expected_generation:
            raise GenerationConflictError("state changed during archive preparation")
        _invoke_failure(failure_hook, "before_archive_manifest")
        manifest_path = _guarded_path(root, f"{archive_relative}/manifest.json")
        with manifest_path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(archive)
        reference = {"manifest": f"{archive_relative}/manifest.json", "sha256": hashlib.sha256(raw).hexdigest()}
        _invoke_failure(failure_hook, "after_archive_manifest")
        verify_history_archive(root, reference)
        _check_read_set(root, expected)
        return reference
    except Exception as exc:
        raise HistoryArchiveError(
            f"archive preparation failed: {exc}", archive_relative=archive_relative if created else None,
        ) from exc


def _preserved_archive_reports(
    root: Path, references: Sequence[Mapping[str, str]], base_generation: int,
    write_paths: Sequence[str],
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    if not isinstance(references, (list, tuple)):
        raise ProjectTransactionError("preserved_archives must be a list or tuple of references")
    refs, reports, seen = [], [], set()
    for reference in references:
        ref = _archive_reference(reference)
        directory = _guarded_path(root, ref["manifest"]).parent
        identity = os.path.normcase(str(directory))
        if identity in seen:
            raise ProjectTransactionError("duplicate preserved archive reference")
        seen.add(identity)
        for relative in write_paths:
            target = _guarded_path(root, relative)
            if target == directory or target.is_relative_to(directory) or directory.is_relative_to(target):
                raise ProjectTransactionError("transaction cannot write into a preserved archive")
        report = verify_history_archive(root, ref)
        if report["base_generation"] != base_generation:
            raise GenerationConflictError("preserved archive does not bind this transaction's base generation")
        refs.append(ref)
        reports.append(report)
    return refs, reports


def _verify_journal_archives(root: Path, journal: Mapping[str, Any]) -> None:
    version = journal.get("version")
    if type(version) is not int or version not in {JOURNAL_VERSION, ARCHIVE_JOURNAL_VERSION}:
        raise TransactionRecoveryError("unsupported project transaction journal version")
    if version == JOURNAL_VERSION:
        if "preserved_archives" in journal:
            raise TransactionRecoveryError("archive dependencies require journal version 2")
        return
    if (type(journal.get("base_generation")) is not int or journal["base_generation"] < 0
            or type(journal.get("target_generation")) is not int
            or journal["target_generation"] != journal["base_generation"] + 1):
        raise TransactionRecoveryError("archive-bound journal generations are invalid")
    references, entries = journal.get("preserved_archives"), journal.get("entries")
    if not isinstance(references, list) or not references or not isinstance(entries, list):
        raise TransactionRecoveryError("journal version 2 requires preserved archives and entries")
    try:
        touched_paths = []
        for entry in entries:
            touched_paths.append(entry["path"])
            # Cleanup also mutates the filesystem; a journal must never redirect
            # its temporary/backup paths into the evidence it promises to preserve.
            touched_paths.extend(entry[field] for field in ("staged", "backup") if entry.get(field))
        _, reports = _preserved_archive_reports(
            root, references, journal["base_generation"], touched_paths,
        )
        state_entries = [entry for entry in entries if entry["path"] == STATE_RELATIVE_PATH]
        if len(state_entries) != 1:
            raise ProjectTransactionError("archive-bound journal requires one state entry")
        state_entry = state_entries[0]
        for report in reports:
            if state_entry.get("old_sha256") != report["source_hashes"][STATE_RELATIVE_PATH]:
                raise ProjectTransactionError("journal old state differs from archived state")
    except (OSError, ValueError, TypeError, KeyError, ProjectTransactionError) as exc:
        raise TransactionRecoveryError(f"preserved archive verification failed: {exc}") from exc


@_with_project_lock
def commit_project_state(
    project_root: Path,
    state: Mapping[str, Any],
    *,
    expected_generation: int,
    expected_file_hashes: Mapping[str, str | None] | None = None,
    preserved_archives: Sequence[Mapping[str, str]] = (),
    writes_before_state: Sequence[tuple[str, str]] = (),
    writes_after_state: Sequence[tuple[str, str]] = (),
    validators: Sequence[StagedValidator] = (),
    failure_hook: FailureHook | None = None,
) -> dict[str, Any]:
    """Commit project state and optional companion text files as one recoverable transaction.

    The state payload is serialized with generation ``expected_generation + 1`` before staging.
    Existing projects without a generation are treated as generation zero.

    Optional ``expected_file_hashes`` binds raw state, all companion write targets,
    and any additional read-only sources to a caller-captured snapshot. None as a
    mapping value means the path must not exist. Checks hold the advisory writer
    lock but do not promise atomicity against arbitrary non-cooperating processes.
    A guarded caller must explicitly recover an existing journal and take a fresh
    snapshot; unguarded legacy callers retain automatic recovery. After preparation,
    recovery still rolls forward using the existing journal, not the old read set.
    Nonempty preserved_archives additionally require byte protection and persist
    externally bound archive references in journal v2 for recovery verification.
    Transactions without archives continue using v1. The caller still owns the
    durable project-level history reference and migration/approval semantics.
    """
    root = Path(project_root).resolve()
    read_set: dict[str, str | None] | None = None
    if not isinstance(preserved_archives, (list, tuple)):
        raise ProjectTransactionError("preserved_archives must be a list or tuple")
    if preserved_archives and expected_file_hashes is None:
        raise ProjectTransactionError("preserved archives require expected_file_hashes")
    archive_refs, archive_reports = _preserved_archive_reports(
        root, preserved_archives, expected_generation,
        [relative for relative, _ in [*writes_before_state, (STATE_RELATIVE_PATH, ""), *writes_after_state]],
    )
    if expected_file_hashes is not None:
        if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
            raise ProjectTransactionError("expected_generation must be a non-negative integer")
        read_set = _prepare_read_set(
            root, expected_file_hashes,
            [*writes_before_state, (STATE_RELATIVE_PATH, ""), *writes_after_state],
        )
        if os.path.lexists(_journal_path(root)):
            raise TransactionRecoveryError("explicit recovery and a fresh read set are required before a guarded commit")
        for report in archive_reports:
            for relative, digest in report["source_hashes"].items():
                if relative not in read_set or read_set[relative] != digest:
                    raise ReadSetConflictError(f"archive source differs from confirmed read set: {relative}")
            for relative, digest in report["archive_hashes"].items():
                if relative in read_set and read_set[relative] != digest:
                    raise ReadSetConflictError(f"archive differs from confirmed read set: {relative}")
                read_set[relative] = digest
        _check_read_set(root, read_set)
    else:
        _recover_project_transaction_locked(root)
    live_generation = _live_generation(root)
    if live_generation != expected_generation:
        raise GenerationConflictError(
            f"stale project writer: expected generation {expected_generation}, live generation {live_generation}"
        )

    target_generation = expected_generation + 1
    next_state = deepcopy(dict(state))
    project = next_state.setdefault("project", {})
    if not isinstance(project, dict):
        raise ProjectTransactionError("project state field 'project' must be a mapping")
    project["state_generation"] = target_generation
    state_text = yaml.safe_dump(next_state, allow_unicode=True, sort_keys=False)
    writes = [*writes_before_state, (STATE_RELATIVE_PATH, state_text), *writes_after_state]

    transaction_id = uuid.uuid4().hex
    entries: list[dict[str, Any]] = []
    staged_map: dict[str, Path] = {}
    journal_written = False
    try:
        _invoke_failure(failure_hook, "before_stage")
        entries, staged_map = _stage_transaction_files(root, transaction_id, writes)
        _invoke_failure(failure_hook, "after_stage")

        staged_state = staged_map[STATE_RELATIVE_PATH]
        parsed_state = _load_yaml_mapping(staged_state)
        if state_generation(parsed_state) != target_generation:
            raise ProjectTransactionError("staged state generation self-check failed")
        for validator in validators:
            validator(staged_map)
        _invoke_failure(failure_hook, "after_validation")

        live_generation = _live_generation(root)
        if live_generation != expected_generation:
            raise GenerationConflictError(
                f"stale project writer before commit: expected generation {expected_generation}, "
                f"live generation {live_generation}"
            )
        _invoke_failure(failure_hook, "after_generation_check")
        if read_set is not None:
            _check_read_set(root, read_set)
            _check_staged_read_set(root, entries, read_set)

        journal = {
            "version": ARCHIVE_JOURNAL_VERSION if archive_refs else JOURNAL_VERSION,
            "status": "prepared",
            "transaction_id": transaction_id,
            "base_generation": expected_generation,
            "target_generation": target_generation,
            "entries": entries,
        }
        if archive_refs:
            journal["preserved_archives"] = archive_refs
            _verify_journal_archives(root, journal)
        journal_path = _journal_path(root)
        atomic_write_text(journal_path, yaml.safe_dump(journal, allow_unicode=True, sort_keys=False))
        journal_written = True
        _invoke_failure(failure_hook, "after_journal_prepared")
        if archive_refs:
            _verify_journal_archives(root, journal)

        for entry in entries:
            relative = str(entry["path"])
            target = _resolve_inside(root, relative)
            staged = _resolve_inside(root, str(entry["staged"]))
            _invoke_failure(failure_hook, f"before_replace:{relative}")
            if read_set is not None:
                _check_read_set(root, {relative: read_set[relative]})
                if not staged.is_file() or sha256_file(staged) != entry["new_sha256"]:
                    raise ProjectTransactionError(f"prepared staged content changed: {relative}")
            os.replace(staged, target)
            _fsync_directory(target.parent)
            _invoke_failure(failure_hook, f"after_replace:{relative}")

        for entry in entries:
            target = _resolve_inside(root, str(entry["path"]))
            if not target.is_file() or sha256_file(target) != entry["new_sha256"]:
                raise ProjectTransactionError(f"post-commit hash verification failed: {entry['path']}")
        if _live_generation(root) != target_generation:
            raise ProjectTransactionError("post-commit state generation verification failed")

        _verify_journal_archives(root, journal)
        committed = dict(journal)
        committed["status"] = "committed"
        atomic_write_text(journal_path, yaml.safe_dump(committed, allow_unicode=True, sort_keys=False))
        _invoke_failure(failure_hook, "after_journal_committed")
        _cleanup_entry_files(root, entries)
        _remove_journal(root)
        if isinstance(state, dict):
            state.setdefault("project", {})["state_generation"] = target_generation
        return {
            "status": "committed",
            "transaction_id": transaction_id,
            "base_generation": expected_generation,
            "target_generation": target_generation,
            "paths": [str(entry["path"]) for entry in entries],
        }
    except Exception:
        if not journal_written:
            _cleanup_entry_files(root, entries)
        raise
