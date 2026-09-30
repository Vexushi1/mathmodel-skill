"""Safe YAML parsing with bounded, process-local reuse of unchanged content.

Only parsed values are cached. Callers still own file reads, byte budgets, source
observations and currentness checks. Each result is an independent object graph.
Strict/custom loader protocols must continue using their own parser.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import os
from threading import RLock
from typing import Any

import yaml

MAX_CACHE_ENTRIES = 64
MAX_CACHE_BYTES = 4 * 1024 * 1024
MAX_ENTRY_BYTES = 256 * 1024
SOURCE_RELATIVE_PATH = "scripts/safe_yaml.py"
_CACHE: OrderedDict[tuple[type, str], tuple[bytes, Any]] = OrderedDict()
_LOCK = RLock()
_CACHE_BYTES = 0


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def loader_name(*, use_c: bool | None = None) -> str:
    """Report the loader selected now, including the explicit diagnostic override."""
    allow_c = not _enabled("HSK_YAML_PURE_PYTHON") if use_c is None else use_c
    return "CSafeLoader" if allow_c and hasattr(yaml, "CSafeLoader") else "SafeLoader"


def clear_cache() -> None:
    """Clear process-local reuse for diagnostics; this does not change file state."""
    global _CACHE_BYTES
    with _LOCK:
        _CACHE.clear()
        _CACHE_BYTES = 0


def cache_info() -> dict[str, int]:
    with _LOCK:
        return {"entries": len(_CACHE), "source_bytes": _CACHE_BYTES,
                "max_entries": MAX_CACHE_ENTRIES, "max_source_bytes": MAX_CACHE_BYTES}


def safe_load(text: str | bytes, *, use_c: bool | None = None,
              cache: bool | None = None) -> Any:
    """Parse ordinary UTF-8 YAML safely and return a fresh value.

    HSK_YAML_PURE_PYTHON=1 selects SafeLoader; HSK_YAML_DISABLE_CACHE=1 disables
    reuse. Content and loader semantics identify cache entries, and actual bytes
    must match even if their hashes collide. No paths or validation verdicts are
    stored. Byte inputs intentionally require UTF-8, as repository readers do.
    """
    global _CACHE_BYTES
    if isinstance(text, bytes):
        raw = text
        document = raw.decode("utf-8")
    elif isinstance(text, str):
        document = text
        raw = document.encode("utf-8")
    else:
        raise TypeError("safe YAML input must be UTF-8 bytes or text")
    name = loader_name(use_c=use_c)
    loader = getattr(yaml, name)
    allow_cache = not _enabled("HSK_YAML_DISABLE_CACHE") if cache is None else cache
    if not allow_cache or len(raw) > MAX_ENTRY_BYTES:
        return yaml.load(document, Loader=loader)
    key = (loader, hashlib.sha256(raw).hexdigest())
    with _LOCK:
        cached = _CACHE.get(key)
        if cached is not None and cached[0] == raw:
            _CACHE.move_to_end(key)
            value = cached[1]
        else:
            # Loading failures never enter the cache. Keep the cached graph private.
            value = yaml.load(document, Loader=loader)
            old = _CACHE.pop(key, None)
            if old is not None:
                _CACHE_BYTES -= len(old[0])
            _CACHE[key] = (raw, value)
            _CACHE_BYTES += len(raw)
            while len(_CACHE) > MAX_CACHE_ENTRIES or _CACHE_BYTES > MAX_CACHE_BYTES:
                _, evicted = _CACHE.popitem(last=False)
                _CACHE_BYTES -= len(evicted[0])
    return deepcopy(value)
