#!/usr/bin/env python3
"""Apply two deterministic post-migration fixes, then remove this helper."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

state_path = ROOT / "scripts" / "validate_project_state.py"
state_text = state_path.read_text(encoding="utf-8")
start = state_text.index("def _framework_section_hash")
end = state_text.index("\ndef _validate_hashes", start)
replacement = '''def _framework_section_hash(path: Path, anchor: str) -> str | None:
    if not path.is_file() or not anchor.strip():
        return None
    lines = path.read_text(encoding="utf-8").replace("\\r\\n", "\\n").replace("\\r", "\\n").splitlines()
    target = anchor.strip()
    start = next((index for index, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        start = next(
            (
                index
                for index, line in enumerate(lines)
                if line.lstrip().startswith("#") and target in line.strip()
            ),
            None,
        )
    if start is None:
        return None
    heading = lines[start].lstrip()
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            next_level = len(stripped) - len(stripped.lstrip("#"))
            if next_level <= level:
                end = index
                break
    text = "\\n".join(lines[start:end]).strip() + "\\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

'''
state_path.write_text(state_text[:start] + replacement + state_text[end + 1 :], encoding="utf-8")

result_path = ROOT / "templates" / "code" / "hsk_pipeline" / "result_io.py"
result_text = result_path.read_text(encoding="utf-8")
old = '''    if kind is None:
        prepared = [(_sheet_name(name), _to_frame(value)) for name, value in tables.items()]
        for name, frame in prepared:
            _check_record_keys(name, frame)
            _check_finite_numbers(name, frame)
    else:
'''
new = '''    if kind is None:
        prepared = WORKBOOK_VALIDATION.prepare_tables(tables, name_normalizer=_sheet_name)
    else:
'''
if old not in result_text:
    raise RuntimeError("result_io generic workbook block not found")
result_path.write_text(result_text.replace(old, new, 1), encoding="utf-8")
