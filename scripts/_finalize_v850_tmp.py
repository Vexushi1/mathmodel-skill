#!/usr/bin/env python3
"""Temporary branch-only v8.5.0 release finalizer.

This script is intentionally deleted after the release-candidate metadata commit.
It updates version carriers, the v8.5 protocol header, release-regression constants,
and the v8.30 protected hashes for the four writing authorities intentionally
changed by this release.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "8.4.0"
NEW = "8.5.0"


def replace_marker(path: str, old: str, new: str, *, count: int = 1) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"expected marker missing in {path}: {old!r}")
    p.write_text(text.replace(old, new, count), encoding="utf-8")


for relative, old, new in (
    ("core/bootstrap.yaml", "skill_version: 8.4.0", "skill_version: 8.5.0"),
    ("core/workflow_router.yaml", "version: 8.4.0", "version: 8.5.0"),
    ("core/module_manifest.yaml", "version: 8.4.0", "version: 8.5.0"),
    ("core/output_contract.yaml", "version: 8.4.0", "version: 8.5.0"),
    ("core/writing_runtime_contract.yaml", "version: 8.4.0", "version: 8.5.0"),
    ("config/prose_audit_patterns.yaml", "version: 8.4.0", "version: 8.5.0"),
    ("core/hsk_core_policy.md", "# HSK Core Policy v8.4.0", "# HSK Core Policy v8.5.0"),
    ("modules/05_writing/paper_writing_protocol.md", "# Module 05A：Paper Writing Protocol（v8.4.0）", "# Module 05A：Paper Writing Protocol（v8.5.0）"),
):
    replace_marker(relative, old, new)

for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    p = ROOT / relative
    text = p.read_text(encoding="utf-8")
    text = text.replace("version: 8.4.0", "version: 8.5.0", 1)
    text = text.replace("# HSK 数学建模模块化工作流 v8.4.0", "# HSK 数学建模模块化工作流 v8.5.0", 1)
    p.write_text(text, encoding="utf-8")

plugin_path = ROOT / ".codex-plugin/plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
plugin["version"] = NEW
plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace("# mathmodel-skill v8.4.0", "# mathmodel-skill v8.5.0", 1)
marker = "## v8.4.0：建模求解叙事与作者表达强化"
if "## v8.5.0：Author Reasoning Voice 细化" not in readme:
    block = """## v8.5.0：Author Reasoning Voice 细化

本次升级把 v8.4 已允许的作者声音进一步细化为证据约束下的建模认知行为：Observation、Open Question、Inquiry、Judgment、Choice、Reduction、Introduction、Derivation、Interpretation、Validation 与 Qualification。重点不是增加“我们/本文”的出现次数，而是让关键观察、发问、选择、简化、解释和检验具有可恢复的数学去向。

新增 Question Closure、Claim Strength Alignment、Reasoning Necessity 与 Problem-Specificity；“我们”“本文”和数学对象主语按语义功能自然选择，不设置代词配额，不做作者身份或 AI 风格推断，不编造团队共识和试错经历。AI Cleanup 采用 Keep / Compress / Re-subject / Delete 的语义决策，并继续保护 Formula、Proof、Algorithm Trace、Citation、Numerical Evidence 与全局最优主张边界。简单解析或直接计算问题仍允许保持紧凑原文，不为展示探究感强行扩写。

"""
    if marker not in readme:
        raise RuntimeError("README v8.4 section marker missing")
    readme = readme.replace(marker, block + marker, 1)
readme_path.write_text(readme, encoding="utf-8")

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
current = "## Current release: 8.4.0"
if current in changelog:
    release = """## Current release: 8.5.0

- Deepened **Model/Solution Author Reasoning Voice** into 11 evidence-bound reasoning acts rather than a pronoun or style-frequency rule.
- Added Question Closure, Claim Strength Alignment, Reasoning Necessity and Problem-Specificity so natural questions, judgments, simplifications and interpretations must have real mathematical destinations and evidence boundaries.
- Clarified the semantic roles of “我们”, “本文” and mathematical/object subjects without quotas, bulk replacement, authorship inference or fabricated team history.
- Expanded the optional reasoning examples, AI Cleanup and final semantic review while keeping examples conditional and preserving the single Paper Writing Protocol authority.
- Added v8.5 fixed voice cases and regression coverage; existing Formula/Proof/Algorithm/Citation/Numerical/Global-Optimum gates remain authoritative, and simple direct problems retain an explicit no-bloat/no-change path.

## 8.4.0
"""
    changelog = changelog.replace(current + "\n", release, 1)
elif "## Current release: 8.5.0" not in changelog:
    raise RuntimeError("CHANGELOG current-release marker missing")
changelog_path.write_text(changelog, encoding="utf-8")

for relative in (
    "tests/test_current_skill_health.py",
    "tests/test_v802_entrypoint_surface_slimming.py",
    "tests/test_v830_editable_mechanism_diagram.py",
):
    p = ROOT / relative
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace(OLD, NEW), encoding="utf-8")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    blob = b"blob " + str(len(data)).encode() + b"\0" + data
    return hashlib.sha1(blob).hexdigest()

protected = {
    "core/writing_reasoning_contract.yaml": git_blob_sha(ROOT / "core/writing_reasoning_contract.yaml"),
    "modules/05_writing/paper_writing_protocol.md": git_blob_sha(ROOT / "modules/05_writing/paper_writing_protocol.md"),
    "modules/05_writing/ai_cleanup.md": git_blob_sha(ROOT / "modules/05_writing/ai_cleanup.md"),
    "modules/06_review_delivery.md": git_blob_sha(ROOT / "modules/06_review_delivery.md"),
}

test_path = ROOT / "tests/test_v830_editable_mechanism_diagram.py"
test_text = test_path.read_text(encoding="utf-8")
for relative, digest in protected.items():
    pattern = rf'("{re.escape(relative)}"\s*:\s*")[0-9a-f]{{40}}(")'
    test_text, n = re.subn(pattern, rf'\g<1>{digest}\2', test_text, count=1)
    if n != 1:
        raise RuntimeError(f"failed to update protected hash for {relative}")
test_path.write_text(test_text, encoding="utf-8")

print("v8.5.0 release carriers and intentional protected hashes finalized")
