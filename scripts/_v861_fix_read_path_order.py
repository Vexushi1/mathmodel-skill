from pathlib import Path

path = Path(__file__).resolve().parents[1] / "RUNTIME_ROUTER.md"
text = path.read_text(encoding="utf-8")
old = "raw manifest 中即使列有 `locked_model_spec` 也不构成 current locked artifact 或执行授权。"
new = "raw manifest 中即使列有可锁定模型候选产物，也不构成 current locked artifact 或执行授权。"
if text.count(old) != 1:
    raise RuntimeError(f"expected one read-path phrase, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("v8.6.1 read-path ordering wording fixed")
