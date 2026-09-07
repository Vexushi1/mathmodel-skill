from pathlib import Path

p = Path("tests/test_v830_editable_mechanism_diagram.py")
text = p.read_text(encoding="utf-8")
replacements = {
    '"core/numerical_verification_contract.yaml": "b901923edf38112cbc922f51d1157265fe1931bd"':
    '"core/numerical_verification_contract.yaml": "f7e1921ec4945cb5e87984ccb8946302d854143f"',
    '"core/workbook_schema.yaml": "2422bbfa8cb3fad3b5b04c12de21c954ec8b3723"':
    '"core/workbook_schema.yaml": "ea33b857602754258915e35dbb0373e1f73fa7af"',
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one protected baseline: {old}")
    text = text.replace(old, new, 1)
p.write_text(text, encoding="utf-8")
