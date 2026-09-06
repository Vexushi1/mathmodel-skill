#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one match, got {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(path: Path, marker: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one marker, got {count}: {marker[:80]!r}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


def patch_transaction() -> None:
    path = ROOT / "scripts/project_transaction.py"
    replace_once(
        path,
        "from collections.abc import Callable, Mapping, Sequence\nfrom copy import deepcopy\nimport hashlib\nimport os\n",
        "from collections.abc import Callable, Mapping, Sequence\nfrom contextlib import contextmanager\nfrom copy import deepcopy\nfrom functools import wraps\nimport hashlib\nimport os\nimport threading\n",
    )
    replace_once(
        path,
        'JOURNAL_RELATIVE_PATH = "state/.project_transaction.yaml"\nJOURNAL_VERSION = 1\n',
        'JOURNAL_RELATIVE_PATH = "state/.project_transaction.yaml"\nLOCK_RELATIVE_PATH = "state/.project_transaction.lock"\nJOURNAL_VERSION = 1\n',
    )
    marker = "\n\ndef sha256_file(path: Path) -> str:\n"
    addition = r'''

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
'''
    insert_before(path, marker, addition)
    replace_once(
        path,
        "def recover_project_transaction(project_root: Path) -> dict[str, Any]:\n",
        "def _recover_project_transaction_locked(project_root: Path) -> dict[str, Any]:\n",
    )
    marker = "\n\ndef load_state_for_update(\n"
    addition = '''\n\n@_with_project_lock\ndef recover_project_transaction(project_root: Path) -> dict[str, Any]:\n    \"\"\"Recover one prepared journal while holding the project-local writer lock.\"\"\"\n    return _recover_project_transaction_locked(Path(project_root).resolve())\n'''
    insert_before(path, marker, addition)
    replace_once(
        path,
        "def commit_project_state(\n",
        "@_with_project_lock\ndef commit_project_state(\n",
    )
    replace_once(
        path,
        "    root = Path(project_root).resolve()\n    recover_project_transaction(root)\n    live_generation = _live_generation(root)\n",
        "    root = Path(project_root).resolve()\n    _recover_project_transaction_locked(root)\n    live_generation = _live_generation(root)\n",
    )


def patch_tests() -> None:
    path = ROOT / "tests/test_v900_project_transaction.py"
    replace_once(
        path,
        "import tempfile\nimport unittest\n",
        "import tempfile\nimport threading\nimport time\nimport unittest\n",
    )
    marker = "\n    def test_validation_failure_leaves_all_live_files_untouched(self):\n"
    addition = r'''

    def test_concurrent_same_generation_writer_is_rejected_after_lock_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, generation=0)
            _, first, first_generation = TX.load_state_for_update(root)
            _, second, second_generation = TX.load_state_for_update(root)
            first["project"]["current_phase"] = "solve_validate"
            second["project"]["current_phase"] = "result_analysis"

            first_inside_commit = threading.Event()
            release_first = threading.Event()
            outcomes: dict[str, object] = {}

            def pause_first(point: str) -> None:
                if point == "after_generation_check":
                    first_inside_commit.set()
                    if not release_first.wait(timeout=5):
                        raise RuntimeError("timed out waiting to release first writer")

            def run_first() -> None:
                try:
                    outcomes["first"] = TX.commit_project_state(
                        root,
                        first,
                        expected_generation=first_generation,
                        failure_hook=pause_first,
                    )
                except Exception as exc:  # noqa: BLE001
                    outcomes["first"] = exc

            def run_second() -> None:
                try:
                    outcomes["second"] = TX.commit_project_state(
                        root,
                        second,
                        expected_generation=second_generation,
                    )
                except Exception as exc:  # noqa: BLE001
                    outcomes["second"] = exc

            thread_one = threading.Thread(target=run_first, daemon=True)
            thread_two = threading.Thread(target=run_second, daemon=True)
            thread_one.start()
            self.assertTrue(first_inside_commit.wait(timeout=5))
            thread_two.start()
            time.sleep(0.1)
            self.assertTrue(thread_two.is_alive(), "second writer should wait for the project lock")
            release_first.set()
            thread_one.join(timeout=5)
            thread_two.join(timeout=5)
            self.assertFalse(thread_one.is_alive())
            self.assertFalse(thread_two.is_alive())
            self.assertIsInstance(outcomes.get("first"), dict)
            self.assertIsInstance(outcomes.get("second"), TX.GenerationConflictError)
            live = self.read_state(root)
            self.assertEqual(live["project"]["state_generation"], 1)
            self.assertEqual(live["project"]["current_phase"], "solve_validate")
'''
    insert_before(path, marker, addition)


def patch_inventory() -> None:
    path = ROOT / "docs/phase_f_transaction_writer_inventory.md"
    marker = "\n## Journal and recovery direction\n"
    addition = '''\n## Writer serialization and stale rejection\n\nControl-plane commits also take a project-local advisory lock at `state/.project_transaction.lock`. The lock only serializes the short recover/check/journal/replace critical section; it does not replace optimistic generation control and is not an external lock service. A writer keeps the generation captured when it loaded state. If another writer commits while it waits for the lock, the waiting writer sees the advanced live generation after lock handoff and fails with `GenerationConflictError` instead of overwriting current state. The lock file may remain as an empty hidden coordination file; journal/stage/backup files are still cleaned after a successful commit.\n'''
    insert_before(path, marker, addition)


if __name__ == "__main__":
    patch_transaction()
    patch_tests()
    patch_inventory()
