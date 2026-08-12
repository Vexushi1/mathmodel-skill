#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, got {text.count(old)}")
    write(path, text.replace(old, new, 1))


VERSION_FILES = [
    "SKILL.md",
    "skills/mathmodel-skill/SKILL.md",
    ".codex-plugin/plugin.json",
    "core/bootstrap.yaml",
    "legacy/README.md",
    "core/code_quality_contract.yaml",
    "core/project_state.schema.yaml",
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "scripts/README.md",
    "core/user_execution_contract.yaml",
    "core/global_preprocessing_contract.yaml",
    "README.md",
    "core/hsk_core_policy.md",
    "scripts/resolve_workflow.py",
    "tests/test_schemas.py",
    "tests/test_v701_stage_boundary_closure.py",
    "scripts/lint_skill.py",
]

for path in VERSION_FILES:
    text = read(path)
    if "7.2.3" not in text:
        raise RuntimeError(f"{path}: current release marker 7.2.3 not found")
    write(path, text.replace("7.2.3", "7.2.4"))

# 1. Contract: enumerate MATLAB calls that are incompatible with a plot-only data_process.m.
replace_once(
    "core/global_preprocessing_contract.yaml",
    "  role: 只读取数据预处理结果.xlsx中Python已持久化的处理前/后、诊断和验证数据，绘制预处理证据图；不得在MATLAB中重新清洗、插值、滤波、重采样或估计参数。\n  minimum_evidence:",
    "  role: 只读取数据预处理结果.xlsx中Python已持久化的处理前/后、诊断和验证数据，绘制预处理证据图；不得在MATLAB中重新清洗、插值、滤波、重采样或估计参数。\n  runtime_forbidden_matlab_functions: [interp1, interp2, interp3, interpn, griddedInterpolant, scatteredInterpolant, fillmissing, rmmissing, standardizeMissing, filloutliers, rmoutliers, isoutlier, smooth, smoothdata, movmean, movmedian, resample, interpft, decimate, downsample, upsample, retime, synchronize, detrend, normalize, rescale, zscore, filter, filtfilt, designfilt, lowpass, highpass, bandpass, bandstop, butter, cheby1, cheby2, ellip, fir1, fir2, fit, fitlm, fitrlinear, fitrgp, fitrensemble, fitrtree, predict, trainNetwork, trainnet]\n  runtime_gate_rule: figures及后续正式交付时，sync_project必须对data_process.m实际代码执行函数调用扫描；命中上述函数即拒绝交付。完整行注释不参与扫描，避免说明性注释造成误报。\n  minimum_evidence:",
)

# 2. Runtime: centralize and broaden forbidden calls, then enforce them with a regex.
replace_once(
    "scripts/sync_project.py",
    'VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}\n',
    'VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}\nMATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS = (\n'
    '    "interp1", "interp2", "interp3", "interpn", "griddedInterpolant", "scatteredInterpolant",\n'
    '    "fillmissing", "rmmissing", "standardizeMissing",\n'
    '    "filloutliers", "rmoutliers", "isoutlier",\n'
    '    "smooth", "smoothdata", "movmean", "movmedian",\n'
    '    "resample", "interpft", "decimate", "downsample", "upsample", "retime", "synchronize",\n'
    '    "detrend", "normalize", "rescale", "zscore",\n'
    '    "filter", "filtfilt", "designfilt", "lowpass", "highpass", "bandpass", "bandstop",\n'
    '    "butter", "cheby1", "cheby2", "ellip", "fir1", "fir2",\n'
    '    "fit", "fitlm", "fitrlinear", "fitrgp", "fitrensemble", "fitrtree",\n'
    '    "predict", "trainNetwork", "trainnet",\n'
    ')\n'
    'MATLAB_PREPROCESSING_FORBIDDEN_RE = re.compile(\n'
    '    r"(?<![\\w])("\n'
    '    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)\n'
    '    + r")\\s*\\(",\n'
    '    re.IGNORECASE,\n'
    ')\n',
)

replace_once(
    "scripts/sync_project.py",
    '            text = matlab.read_text(encoding="utf-8", errors="ignore")\n            forbidden_calls = ("interp1(", "fillmissing(", "smoothdata(", "resample(", "filtfilt(", "designfilt(")\n            if any(token in text for token in forbidden_calls):\n                issues.append("data_process.m不得重新执行插值、填补、平滑、重采样或滤波")\n',
    '            text = matlab.read_text(encoding="utf-8", errors="ignore")\n'
    '            code_text = "\\n".join(\n'
    '                line for line in text.splitlines() if not line.lstrip().startswith("%")\n'
    '            )\n'
    '            forbidden_matches = sorted({\n'
    '                match.group(1).lower()\n'
    '                for match in MATLAB_PREPROCESSING_FORBIDDEN_RE.finditer(code_text)\n'
    '            })\n'
    '            if forbidden_matches:\n'
    '                issues.append(\n'
    '                    "data_process.m不得重新执行预处理、拟合或预测；检测到MATLAB调用: "\n'
    '                    + ", ".join(forbidden_matches)\n'
    '                )\n',
)

# 3. Figure Evidence: align prose with the actual router (solve + analysis before figure_evidence).
old_order = '''## 正确顺序

1. 若 `preprocessing_decision=project_level`，先锁定已验收的 `数据预处理结果.xlsx`，生成并人工检查 `数据预处理/data_process.m` 的预处理证据图；
2. Python 完成完整主求解并通过主结果质量门；
3. Python 基于题目风险完成实际需要的结果深化分析；
4. 锁定 `问题X求解/` 中的两个标准工作簿；
5. 继承当前 `preprocessing_decision`，明确每张图读取原始数据、统一预处理工作簿或结果工作簿中的哪一种事实源；
6. 为每张图先写 Core conclusion，再按信息效率选择图型；
7. 生成 MATLAB 代码前实际读取工作簿，锁定工作簿名、工作表名、真实表头、单位和数据类型；
8. 设置简洁 `title` 或一个整体 `sgtitle`，拟定不逐字重复的论文图注；
9. 将各问 `q{x}_plot.m` 与两类 Python 脚本、两类结果工作簿放在同一 `问题X求解/`；项目级预处理图脚本固定为 `数据预处理/data_process.m`；
10. 检查核心结论是否有图或表证据，并同步 `模型论文框架.md`；
11. 默认只保留图窗供人工检查，不自动创建图表子目录或批量导出图片。
'''
new_order = '''## 正确顺序

1. 继承已经锁定的 `preprocessing_decision`；若为 `project_level`，确认 `数据预处理结果.xlsx` 已 accepted 且预处理质量门通过，但此时不要求先生成 `data_process.m`；
2. Python 完成完整主求解并通过主结果质量门；
3. Python 基于题目风险完成实际需要的结果深化分析，并验收 `问题X求解/` 中两个标准工作簿；
4. 只有上述数值阶段完成后才进入 Figure Evidence；先明确每张图读取原始数据、统一预处理工作簿或结果工作簿中的哪一种事实源；
5. 若为 `project_level`，此时生成并人工检查 `数据预处理/data_process.m`，只把已验收预处理工作簿中的底层证据转成图；
6. 为各问结果图先写 Core conclusion，再按信息效率选择图型；
7. 生成 MATLAB 代码前实际读取工作簿，锁定工作簿名、工作表名、真实表头、单位和数据类型；
8. 设置简洁 `title` 或一个整体 `sgtitle`，拟定不逐字重复的论文图注；
9. 将各问 `q{x}_plot.m` 与两类 Python 脚本、两类结果工作簿放在同一 `问题X求解/`；项目级预处理图脚本固定为 `数据预处理/data_process.m`；
10. 检查核心结论是否有图或表证据，并同步 `模型论文框架.md`；
11. 默认只保留图窗供人工检查，不自动创建图表子目录或批量导出图片。
'''
replace_once("modules/04_figure_evidence.md", old_order, new_order)

# 4. Regression coverage for runtime call scanning and stage ordering.
test_insert = '''
    def test_runtime_forbidden_matlab_calls_match_contract_and_block_reprocessing(self):
        declared = set(self.contract["preprocessing_figure_contract"]["runtime_forbidden_matlab_functions"])
        runtime = set(self.sync.MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)
        self.assertEqual(declared, runtime)
        for name in ("interp2", "normalize", "detrend", "filter", "movmean", "movmedian", "predict"):
            self.assertIn(name, runtime)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            process_dir = root / "数据预处理"
            process_dir.mkdir()
            script = process_dir / "data_process.m"
            script.write_text(
                'title("证据图");\\nbook = "数据预处理结果.xlsx";\\ny = normalize(x);\\n',
                encoding="utf-8",
            )
            issues = self.sync._preprocessing_artifact_issues(
                root,
                {"preprocessing_matlab_script"},
                {"preprocessing": {"decision": "project_level"}},
            )
            self.assertTrue(any("normalize" in item for item in issues))

            script.write_text(
                '% normalize(x) 仅为说明，不应触发\\ntitle("证据图");\\nbook = "数据预处理结果.xlsx";\\nplot(x, y);\\n',
                encoding="utf-8",
            )
            issues = self.sync._preprocessing_artifact_issues(
                root,
                {"preprocessing_matlab_script"},
                {"preprocessing": {"decision": "project_level"}},
            )
            self.assertFalse(any("不得重新执行预处理" in item for item in issues))

    def test_figure_evidence_order_matches_router_stage_boundary(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        primary = text.index("Python 完成完整主求解")
        analysis = text.index("Python 基于题目风险完成实际需要的结果深化分析")
        enter_figures = text.index("只有上述数值阶段完成后才进入 Figure Evidence")
        data_process = text.index("此时生成并人工检查 `数据预处理/data_process.m`")
        self.assertLess(primary, analysis)
        self.assertLess(analysis, enter_figures)
        self.assertLess(enter_figures, data_process)
'''
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '\n\nif __name__ == "__main__":\n    unittest.main()\n',
    test_insert + '\n\nif __name__ == "__main__":\n    unittest.main()\n',
)

# 5. Static lint must notice if the runtime gate loses the key families again.
replace_once(
    "scripts/lint_skill.py",
    '    if "exportgraphics(" in data_process:\n        errors.append("data_process MATLAB template must not auto-export")\n',
    '    if "exportgraphics(" in data_process:\n'
    '        errors.append("data_process MATLAB template must not auto-export")\n'
    '    sync_runtime = read_text(ROOT / "scripts/sync_project.py")\n'
    '    for token in (\n'
    '        "MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS", "interp2", "normalize", "detrend",\n'
    '        "filter", "movmean", "movmedian", "predict",\n'
    '    ):\n'
    '        if token not in sync_runtime:\n'
    '            errors.append(f"sync_project preprocessing MATLAB runtime gate lacks: {token}")\n',
)

# 6. Release notes: preserve the full v7.2.3 history under Previous release.
replace_once(
    "CHANGELOG.md",
    "# Changelog\n\n## Current release: 7.2.3\n",
    "# Changelog\n\n## Current release: 7.2.4\n\n"
    "- Hardened `data_process.m` delivery with a contract-backed runtime forbidden-call set covering interpolation, missing/outlier repair, smoothing, resampling/alignment, detrending/normalization, filtering/filter design, fitting and prediction calls.\n"
    "- `scripts/sync_project.py` now scans executable MATLAB lines at figures-and-later delivery scopes and reports the exact forbidden functions detected; full-line comments are ignored to avoid documentation false positives.\n"
    "- Aligned `modules/04_figure_evidence.md` with the authoritative router: project-level preprocessing workbook acceptance precedes solving, while `data_process.m` is created only after primary solving and result analysis when Figure Evidence begins.\n"
    "- Added regression/static-lint coverage that locks the contract/runtime forbidden-function set and the Figure Evidence stage order without changing the three-state preprocessing decision or per-question five-file interface.\n\n"
    "## Previous release: 7.2.3\n",
)

# Remove this one-shot maintenance machinery from the commit it produces.
(ROOT / "scripts/apply_v724_patch.py").unlink()
workflow = ROOT / ".github/workflows/v724-patch.yml"
if workflow.exists():
    workflow.unlink()

print("v7.2.4 patch applied")
