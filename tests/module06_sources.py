"""Test-only consumers of the split review sources and the pre-split baseline.

The historical reconstruction reads every business section from its current
canonical source. The frozen fixture is comparison evidence only, never a source
of replacement text for a missing or changed live section.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = "modules/06_review_delivery.md"
CONTENT = "modules/06_review/content_review.md"
FINAL = "modules/06_review/final_delivery.md"
CANONICAL_PATHS = (ENTRY, CONTENT, FINAL)
BASELINE_PATH = "tests/fixtures/module06_v10210_source.md"
BASELINE_COMMIT = "a944de224ac967b7d4b76f8ce411eaef9a71e7b2"
BASELINE_SHA256 = "e78903a21d92bf040bbf13e71a031b0629d86e675b891995f6d99b3dc75a95fe"

# Independent migration expectations: each old top-level business section has
# exactly one current owner. This is a test baseline, not a runtime dispatch map.
SECTION_SOURCES = (
    ("## 一、评审分级", ENTRY),
    ("## 二、题意、框架与局部 stale 审查", CONTENT),
    ("## 三、公式、模型角色、算法、命题与数值证据审查", CONTENT),
    ("## 四、Terminology、Numeric Style 与 Claim Strength 审查", CONTENT),
    ("## 五、Title Claim、正文结构与 Paragraph Necessity", CONTENT),
    ("## 六、深化分析、图表与结果证据审查", CONTENT),
    ("## 七、Citation Evidence 与参考文献审查", CONTENT),
    ("## 八、编译、复现与提交包", FINAL),
    ("## 九、Final Submission Compliance & Evidence Sweep", FINAL),
    ("## 十、返修优先级", ENTRY),
    ("## 十一、Blocking 条件", ENTRY),
)


def split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Split real H2 sections without treating fenced examples as headings."""
    lines = text.splitlines(keepends=True)
    boundaries = []
    fence = None
    for number, line in enumerate(lines):
        stripped = line.strip()
        mark = re.match(r"^(`{3,}|~{3,})", stripped)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not stripped[len(token):].strip():
                fence = None
            continue
        if fence is None and re.match(r"^##\s+", line):
            boundaries.append((number, line.rstrip("\r\n")))
    if not boundaries:
        raise ValueError("review source has no top-level business sections")
    sections = []
    for index, (start, heading) in enumerate(boundaries):
        stop = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(lines)
        sections.append((heading, "".join(lines[start:stop])))
    return "".join(lines[:boundaries[0][0]]), sections


def review_text(root: Path = ROOT) -> str:
    """Read the entire current entry plus both leaves, including navigation."""
    return "\n".join((root / path).read_text(encoding="utf-8") for path in CANONICAL_PATHS) + "\n"


def historical_review_text(root: Path = ROOT) -> str:
    """Reconstruct the old business document from the current canonical owners."""
    documents = {path: split_sections((root / path).read_text(encoding="utf-8"))
                 for path in CANONICAL_PATHS}
    parts = [documents[ENTRY][0]]
    for heading, path in SECTION_SOURCES:
        matches = [body for key, body in documents[path][1] if key == heading]
        if len(matches) != 1:
            raise ValueError(f"review section must have one canonical owner: {path}#{heading}")
        body = matches[0]
        # These two sections moved from an internal boundary to a file end.
        # The files keep one final newline; restore only the old section
        # separator, never words or rules from the historical fixture.
        if (heading, path) in (
            ("## 七、Citation Evidence 与参考文献审查", CONTENT),
            ("## 九、Final Submission Compliance & Evidence Sweep", FINAL),
        ):
            body += "\n"
        parts.append(body)
    return "".join(parts)


def baseline_text(root: Path = ROOT) -> str:
    # Universal-newline reading matches the historical text/hash tests on both
    # Windows and Linux. The pinned value describes the committed LF fixture.
    text = (root / BASELINE_PATH).read_text(encoding="utf-8")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != BASELINE_SHA256:
        raise ValueError("pre-split review baseline changed")
    return text


def assert_preserved_review(root: Path = ROOT) -> str:
    current = historical_review_text(root)
    if current != baseline_text(root):
        raise ValueError("canonical review business text differs from the pre-split baseline")
    return current
