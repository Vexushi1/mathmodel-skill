from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests/test_v830_editable_mechanism_diagram.py"

text = PATH.read_text(encoding="utf-8")

old_comment = '''    # v8.7.0 intentionally updates the four writing authorities below for per-question
    # capability preflight, Formula Roles and state-driven activation. Unrelated numerical,
    # model-approval, workbook, project-state, plotting and delivery snapshots remain pinned.
'''
new_comment = '''    # v8.7.0 intentionally updated the writing-authority baseline below for per-question
    # capability preflight. The v8.7.1 release sync changes only the Paper Writing Protocol
    # release-carrier header, so that single header is normalized before the v8.7.0 body snapshot check.
'''

old_test = '''    def test_protected_authorities_have_not_drifted(self):
        for relative, expected in self.PROTECTED.items():
            with self.subTest(relative=relative):
                self.assertEqual(git_blob_sha(ROOT / relative), expected)
'''
new_test = '''    def test_protected_authorities_have_not_drifted(self):
        protocol = "modules/05_writing/paper_writing_protocol.md"
        current_header = "# Module 05A：Paper Writing Protocol（v8.7.1）"
        baseline_header = "# Module 05A：Paper Writing Protocol（v8.7.0）"
        for relative, expected in self.PROTECTED.items():
            with self.subTest(relative=relative):
                path = ROOT / relative
                if relative == protocol:
                    text = path.read_text(encoding="utf-8")
                    self.assertEqual(text.count(current_header), 1)
                    data = text.replace(current_header, baseline_header, 1).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\\0" + data
                    ).hexdigest()
                else:
                    actual = git_blob_sha(path)
                self.assertEqual(actual, expected)
'''

for label, old, new in (
    ("comment", old_comment, new_comment),
    ("test body", old_test, new_test),
):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one {label} match, found {count}")
    text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8")
