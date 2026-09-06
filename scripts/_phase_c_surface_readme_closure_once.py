from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, *, expected: int = 1) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrences, found {count}: {old!r}")
    file.write_text(text.replace(old, new), encoding="utf-8")


replace(
    "README.md",
    "项目级预处理和主求解代码交付前必须验证 challenge/approval 与当前 revision/hash 完全一致。",
    "项目级预处理和主求解代码交付前必须验证 challenge/approval 与当前 `semantic_revision` / validated `semantic_identity_hash` 完全一致；legacy hash 只保留历史只读 provenance。",
)
replace(
    "README.md",
    "语义 revision/hash 变化会使旧 challenge、approval 与 locked model stale；纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。",
    "semantic revision 或 structured identity 变化会使旧 challenge、approval 与 locked model stale；纯排版、SIB 外纯措辞、caption、公式编号或不改变 structured identity 的 LaTeX 文件拆分只影响 text provenance，不触发重新审批。",
)

test_path = ROOT / "tests/test_v900_semantic_identity_surface_closure.py"
test = test_path.read_text(encoding="utf-8")
old_paths = '''            ".codex-plugin/plugin.json",\n        ]'''
new_paths = '''            ".codex-plugin/plugin.json",\n            "README.md",\n            "scripts/README.md",\n            "REPOSITORY_INDEX.md",\n        ]'''
if test.count(old_paths) != 1:
    raise SystemExit("surface test: critical paths anchor changed")
test = test.replace(old_paths, new_paths)
old_forbidden = '''            "Human Model Approval（绑定 current semantic revision/hash）",\n        ]'''
new_forbidden = '''            "Human Model Approval（绑定 current semantic revision/hash）",\n            "challenge/approval 与当前 revision/hash 完全一致",\n            "current semantic revision/hash",\n        ]'''
if test.count(old_forbidden) != 1:
    raise SystemExit("surface test: forbidden anchor changed")
test = test.replace(old_forbidden, new_forbidden)
test_path.write_text(test, encoding="utf-8")
