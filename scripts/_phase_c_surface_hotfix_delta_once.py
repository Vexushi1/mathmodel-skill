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


for skill in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace(
        skill,
        "正式项目级预处理或主求解代码只有在用户明确批准 current `semantic_revision/hash`、形成 current `locked_model_spec` 后才允许进入对应 gate。",
        "正式项目级预处理或主求解代码只有在用户明确批准 current `semantic_revision` 与 validated `semantic_identity_hash`、并由 Model Approval gate 确认 current = validated = approved identity 后才允许进入对应 gate；legacy hash 只读兼容不能授权新代码。",
    )
    replace(
        skill,
        "`state/project_state.yaml` 管 revision/hash/stale；accepted workbook 是具体数值事实源。",
        "`state/project_state.yaml` 管 revision/structured identity/text provenance/stale；accepted workbook 是具体数值事实源。",
    )

# The manifest uses an initial capital in the prose; the assertion is semantic,
# not a casing convention.
test = ROOT / "tests/test_v900_semantic_identity_surface_closure.py"
text = test.read_text(encoding="utf-8")
old = '        self.assertIn("legacy semantic_hash", manifest)'
new = '        self.assertIn("legacy semantic_hash", manifest.lower())'
if text.count(old) != 1:
    raise SystemExit("surface closure test: expected one case-sensitive legacy assertion")
test.write_text(text.replace(old, new), encoding="utf-8")
