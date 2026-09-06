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
import os
import threading
from pathlib import Path
import shutil
import tempfile
from typing import Any
import uuid

import yaml

STATE_RELATIVE_PATH = "state/project_state.yaml"
JOURNAL_RELATIVE_PATH = "state/.project_transaction.yaml"
LOCK_RELATIVE_PATH = "state/.project_transaction.lock"
JOURNAL_VERSION = 1


class ProjectTransactionError(RuntimeError):
    """Base error for project transaction failures."""


class GenerationConflictError(ProjectTransactionError):
    """Raised when another writer changed project.state_generation."""


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
    if journal.get("version") != JOURNAL_VERSION:
        raise TransactionRecoveryError("unsupported project transaction journal version")
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
    for index, (relative, content) in enumerate(writes):
        target = _resolve_inside(root, relative)
        canonical_relative = _relative(root, target)
        if canonical_relative in seen:
            raise ProjectTransactionError(f"duplicate transaction target: {canonical_relative}")
        seen.add(canonical_relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.parent / f".{target.name}.txn-{transaction_id}-{index}.stage"
        backup = target.parent / f".{target.name}.txn-{transaction_id}-{index}.bak"
        _write_bytes_fsync(staged, content.encode("utf-8"))
        existed = target.is_file()
        old_sha = sha256_file(target) if existed else None
        if existed:
            shutil.copyfile(target, backup)
            with backup.open("rb") as handle:
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
    return entries, staged_map


@_with_project_lock
def commit_project_state(
    project_root: Path,
    state: Mapping[str, Any],
    *,
    expected_generation: int,
    writes_before_state: Sequence[tuple[str, str]] = (),
    writes_after_state: Sequence[tuple[str, str]] = (),
    validators: Sequence[StagedValidator] = (),
    failure_hook: FailureHook | None = None,
) -> dict[str, Any]:
    """Commit project state and optional companion text files as one recoverable transaction.

    The state payload is serialized with generation ``expected_generation + 1`` before staging.
    Existing projects without a generation are treated as generation zero.
    """
    root = Path(project_root).resolve()
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

        journal = {
            "version": JOURNAL_VERSION,
            "status": "prepared",
            "transaction_id": transaction_id,
            "base_generation": expected_generation,
            "target_generation": target_generation,
            "entries": entries,
        }
        journal_path = _journal_path(root)
        atomic_write_text(journal_path, yaml.safe_dump(journal, allow_unicode=True, sort_keys=False))
        journal_written = True
        _invoke_failure(failure_hook, "after_journal_prepared")

        for entry in entries:
            relative = str(entry["path"])
            target = _resolve_inside(root, relative)
            staged = _resolve_inside(root, str(entry["staged"]))
            _invoke_failure(failure_hook, f"before_replace:{relative}")
            os.replace(staged, target)
            _fsync_directory(target.parent)
            _invoke_failure(failure_hook, f"after_replace:{relative}")

        for entry in entries:
            target = _resolve_inside(root, str(entry["path"]))
            if not target.is_file() or sha256_file(target) != entry["new_sha256"]:
                raise ProjectTransactionError(f"post-commit hash verification failed: {entry['path']}")
        if _live_generation(root) != target_generation:
            raise ProjectTransactionError("post-commit state generation verification failed")

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
