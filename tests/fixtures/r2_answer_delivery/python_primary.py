"""Two-station answer delivery fixture, copied outside the repository by CI."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

import openpyxl


def solve(payload, scenario):
    times = payload["times"]
    values = payload["cases"][scenario]
    peaks = []
    events = []
    for station, samples in zip(payload["stations"], values):
        peak = max(samples)
        for time, value in zip(times, samples):
            if value == peak:
                peaks.append([f"{scenario}-{station}-{time}", station, peak, time, "1", "s"])
        triggered = [time for time, value in zip(times, samples) if value >= payload["threshold"]]
        events.append([station, "已触发" if triggered else "未触发", triggered[0] if triggered else None,
                       "达到阈值" if triggered else "全部采样值低于阈值"])
    network_peak = max(sum(row[index] for row in values) for index in range(len(times)))
    return {
        "运行配置": [["项目", "值"], ["execution_owner", "user"],
                 ["execution_profile", "full_fidelity"], ["stage", "primary"]],
        "核心指标": [["指标", "数值"], ["全网峰值", network_peak]],
        "数据审计": [["等级", "检查项", "信息", "处理方式"],
                 ["Info", "事件时刻", "未触发事件的时刻缺失", "保留空值、状态与原因"]],
        "主结果质量门": [["检查项", "是否通过", "证据"],
                   ["逐站峰值", len({row[1] for row in peaks}) == len(payload["stations"]), "每站保留全部并列峰时"]],
        "站点峰值": [["记录键", "站点", "峰值", "时刻", "单位", "时间单位"], *peaks],
        "执行停止证据": [["迭代或样本数", "指标", "数值", "单位"],
                    [len(times), "末采样时刻", times[-1], "s"]],
        "事件状态": [["站点", "状态", "时刻", "原因"], *events],
    }


def apply_submission_formats(book):
    sheet = book["站点峰值"]
    for row in sheet.iter_rows(min_row=2):
        row[2].number_format = "0.00"
        row[3].number_format = "0.0"


def write_results(path, sheets):
    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, rows in sheets.items():
        sheet = book.create_sheet(name)
        for row in rows:
            sheet.append(row)
    apply_submission_formats(book)
    descriptor, temporary = tempfile.mkstemp(suffix=".xlsx", dir=path.parent)
    os.close(descriptor)
    try:
        book.save(temporary)
        book.close()
        os.replace(temporary, path)
    finally:
        book.close()
        Path(temporary).unlink(missing_ok=True)


def main():
    folder = Path(__file__).resolve().parent
    payload = json.loads((folder.parent / "input.json").read_text(encoding="utf-8"))
    sheets = solve(payload, sys.argv[1])
    write_results(folder / "问题一求解结果.xlsx", sheets)


if __name__ == "__main__":
    main()
