"""O-03: blank padding must not erase keyed missing records in structural I/O.

These synthetic records do not establish that every unkeyed, entirely blank row
is semantically disposable. No numerical model or missing-value imputation runs.
"""
import sys
from pathlib import Path
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from templates.code.hsk_pipeline import result_io as RESULT_IO



def records(order=("A", "B", "C")):
    values = {"A": 1.0, "B": float("nan"), "C": 3.0}
    return pd.DataFrame({"记录键": list(order), "数值": [values[key] for key in order]})


def padded_records(order=("A", "B", "C")):
    padding = pd.DataFrame({"记录键": [None], "数值": [float("nan")]})
    real = records(order)
    return pd.concat([padding, real.iloc[:1], padding, real.iloc[1:], padding], ignore_index=True)


def solution_tables(*, audit_note="B的数值缺失，保留记录键与NaN，不插补"):
    return {
        "运行配置": pd.DataFrame({"项目": ["stage"], "值": ["primary"]}),
        "核心指标": pd.DataFrame({"指标": ["fixture"], "数值": [1.0]}),
        "数据审计": pd.DataFrame({
            "等级": ["Info"], "检查项": ["输入说明"], "信息": [audit_note], "处理方式": ["保留原始记录"],
        }),
        "主结果质量门": pd.DataFrame({"检查项": ["结构fixture"], "是否通过": [True], "证据": ["仅I/O测试"]}),
        "明细结果": padded_records(),
    }


def write_raw_fixture(path, tables):
    """Keep padding or missing audit text on disk, bypassing the production writer."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, index=False)


class BlankRecordPreservationTests(unittest.TestCase):
    def test_dataframe_drops_only_all_blank_padding_and_preserves_input(self):
        for order in (("A", "B", "C"), ("C", "B", "A")):
            with self.subTest(order=order):
                raw = padded_records(order)
                before = raw.copy(deep=True)
                cleaned = RESULT_IO.WORKBOOK_VALIDATION._as_frame(raw)
                # Padding may infer object keys in pandas 3; cleaning preserves
                # input dtypes rather than re-inferring from a nonempty fixture.
                pd.testing.assert_frame_equal(cleaned, records(order).astype(raw.dtypes))
                pd.testing.assert_frame_equal(raw, before)
                self.assertEqual(len(raw) - len(cleaned), 3)
                self.assertTrue(pd.isna(cleaned.loc[cleaned["记录键"] == "B", "数值"].iloc[0]))

    def test_production_xlsx_roundtrip_preserves_keyed_missing_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "主结果fixture.xlsx"
            RESULT_IO.write_workbook(path, solution_tables(), workbook_kind="solution")
            loaded = RESULT_IO.read_workbook_tables(path)
            pd.testing.assert_frame_equal(loaded["明细结果"], records())
            validated = dict(RESULT_IO.validate_workbook_file(path, "solution"))
            pd.testing.assert_frame_equal(validated["明细结果"], records())

    def test_raw_xlsx_padding_is_removed_without_losing_record_order_or_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "带空行fixture.xlsx"
            tables = solution_tables()
            tables["明细结果"] = padded_records(("C", "B", "A"))
            write_raw_fixture(path, tables)
            loaded = RESULT_IO.read_workbook_tables(path)
            pd.testing.assert_frame_equal(loaded["明细结果"], records(("C", "B", "A")))
            validated = dict(RESULT_IO.validate_workbook_file(path, "solution"))
            pd.testing.assert_frame_equal(validated["明细结果"], records(("C", "B", "A")))

    def test_retained_nan_still_requires_existing_missing_value_audit(self):
        tables = solution_tables(audit_note="常规字段检查通过")
        with self.assertRaisesRegex(ValueError, "数据审计未说明缺失处理"):
            RESULT_IO.validate_workbook_tables(tables, "solution")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "缺审计说明fixture.xlsx"
            write_raw_fixture(path, tables)
            with self.assertRaisesRegex(ValueError, "数据审计未说明缺失处理"):
                RESULT_IO.validate_workbook_file(path, "solution")


if __name__ == "__main__":
    unittest.main()
