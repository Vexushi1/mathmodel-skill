from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "RUNTIME_ROUTER.md"
text = path.read_text(encoding="utf-8")
old = "`model_approval` 在当前代码阶段被返回时验证 Challenge/Human Approval 与 current semantic revision/hash；"
new = "`model_approval` 在当前代码阶段被返回时验证 Challenge/Human Approval 与 current `semantic_revision` / validated `semantic_identity_hash`；legacy hash 仅保留只读 provenance；"
count = text.count(old)
if count != 1:
    raise SystemExit(f"RUNTIME_ROUTER.md: expected 1 remaining legacy approval phrase, found {count}")
path.write_text(text.replace(old, new), encoding="utf-8")
