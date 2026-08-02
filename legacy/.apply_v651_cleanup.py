from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8", newline="\n")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    if old not in text:
        raise RuntimeError(f"missing replacement anchor in {relative}: {old[:80]!r}")
    write(relative, text.replace(old, new, 1))


def replace_all(relative: str, old: str, new: str) -> None:
    text = read(relative)
    if old not in text:
        raise RuntimeError(f"missing replacement token in {relative}: {old!r}")
    write(relative, text.replace(old, new))


def runtime_config_frame_source(indent: str = "") -> str:
    return (
        f'{indent}"运行配置": pd.DataFrame({{\n'
        f'{indent}    "项目": ["execution_owner", "execution_profile", "stage"],\n'
        f'{indent}    "值": ["user", "full_fidelity", "primary"],\n'
        f'{indent}}}),\n'
    )


def convert_starter(relative: str) -> None:
    text = read(relative)
    text = text.replace("    ResultAnalysisResult,\n", "")
    text = text.replace("    run_pipeline,\n", "    run_primary_pipeline,\n")
    text = re.sub(
        r"\n\ndef analyze_results\(.*?\n\ndef sync_primary_framework",
        "\n\ndef sync_primary_framework",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"\n\ndef sync_analysis_framework\(.*?\n\ndef main",
        "\n\ndef main",
        text,
        flags=re.S,
    )
    text = text.replace("    run_pipeline(\n", "    run_primary_pipeline(\n")
    text = text.replace(
        "        result_analysis_hook=analyze_results,\n"
        "        primary_framework_sync_hook=sync_primary_framework,\n"
        "        analysis_framework_sync_hook=sync_analysis_framework,\n",
        "        framework_sync_hook=sync_primary_framework,\n",
    )
    if "run_pipeline(" in text or "ResultAnalysisResult" in text or "analyze_results" in text:
        raise RuntimeError(f"starter still contains combined pipeline residue: {relative}")
    if "run_primary_pipeline(" not in text:
        raise RuntimeError(f"starter lacks primary runner: {relative}")
    write(relative, text)


for starter in (
    "templates/code/starter/classification.py",
    "templates/code/starter/evaluation.py",
    "templates/code/starter/prediction.py",
    "templates/code/starter/simulation.py",
):
    convert_starter(starter)

# The optimization starter was already converted in the first branch commit.
optimization = read("templates/code/starter/optimization.py")
if "run_primary_pipeline(" not in optimization or "run_pipeline(" in optimization:
    raise RuntimeError("optimization starter is not primary-only")

write(
    "templates/code/starter/README.md",
    """# 题型 Starter 使用说明 v6.5.1

本目录包含五个**主求解代码入口**：

- `classification.py`：分类、判别和监督学习；
- `evaluation.py`：综合评价、评分和排序；
- `optimization.py`：显式目标与约束优化；
- `prediction.py`：时间序列或滚动预测；
- `simulation.py`：随机、状态转移或离散事件仿真。

Starter 只调用 `run_primary_pipeline()`，不得在同一脚本中继续执行结果深化分析。公共写表、质量门和状态记录由 `hsk_pipeline` 提供；赛题代码由用户本地完整运行，助手不得执行。

## 使用步骤

1. 将整个 `templates/code/hsk_pipeline/` 复制为项目根目录下的 `hsk_pipeline/`；
2. 选择一个 starter，复制到项目根目录并改名为 `问题一求解.py` 等中文名；
3. 替换 `INPUT_FILE`、`FRAMEWORK_SECTION` 和 `PROBLEM_NAME`；
4. 根据当前 `模型论文框架.md` 修改 objective、structures 和 capabilities；
5. 实现数据处理、模型求解、主结果质量门、`运行配置` 工作表和主结果框架同步；
6. 生成 `问题X完整运行配置.yaml` 与 `问题X本地运行说明.md`，执行 `validate_code_delivery.py`；
7. 用户本地运行 `问题X求解.py`，返回 `问题X求解结果.xlsx`；
8. `validate_user_execution.py` 验收通过后，另行生成 `问题X结果深化分析.py`；
9. 用户运行深化脚本并返回深化工作簿；两类工作簿均 accepted 后才进入 results、MATLAB 和 LaTeX。

正式主代码交付使用 `--delivery-scope code`。禁止把多个 starter 拼接到同一脚本，也禁止在主求解 starter 中保留未使用的结果深化钩子。
""",
)

write(
    "templates/code/hsk_pipeline/README.md",
    """# HSK Python 用户执行管线 v6.5.1

本目录提供可由用户本地运行的完整数值底座：

- `run_primary_pipeline()`：数据审计、完整版主求解、主结果质量门和主工作簿；
- `run_result_analysis_pipeline()`：在主工作簿 accepted 后，执行题目专属结果深化并写入深化工作簿；
- `run_pipeline()`：仅保留为旧项目和用户本地显式编排的兼容 API，不是新项目默认入口。

新项目的题型 starter 只调用 `run_primary_pipeline()`。助手交付主代码、完整运行配置和说明后停在 `awaiting_user_execution`；用户运行产生工作簿后，状态只到 `workbook_received`，必须由 `validate_user_execution.py` 验收后才进入 `accepted/solved`。

## 推荐复制结构

```text
项目根目录/
├─ hsk_pipeline/
│  ├─ __init__.py
│  ├─ main_pipeline.py
│  ├─ result_io.py
│  └─ workbook_validation.py
├─ 问题一求解.py
├─ 问题一完整运行配置.yaml
├─ 问题一本地运行说明.md
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 主求解阶段

```text
config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ primary_execution_status = workbook_received
→ 用户返回工作簿
→ validate_user_execution.py
→ accepted / solved
```

主工作簿必须包含 `运行配置`，并记录代码/数据 SHA-256、求解器版本、容差、停止原因、随机种子、场景或重复次数、网格或时域、平台以及全部禁止降级标志。

## 结果深化阶段

主工作簿 accepted 后，依据真实主结果单独生成 `问题X结果深化分析.py`、深化完整运行配置和本地说明。用户本地运行后返回 `问题X结果深化分析.xlsx`；该工作簿同样必须包含 `运行配置`、`分析设计`、至少一个实质分析表和 `结论稳定性汇总`。验收通过后才进入 `analyzed`。

`run_pipeline()` 不得被助手调用，也不得作为新 starter 的默认入口。Python 不生成正式论文图；MATLAB 只读取两类 accepted 工作簿。

正式代码交付：

```bash
python scripts/sync_project.py <project_root> --write --strict --delivery-scope code
```

两类工作簿均验收后，正式结果交付才使用 `--delivery-scope results`。
""",
)

for obsolete in (
    ROOT / "templates/review/robustness_check.md",
    ROOT / "templates/code/hsk_pipeline/config.yaml",
):
    if not obsolete.is_file():
        raise RuntimeError(f"obsolete file already missing: {obsolete}")
    obsolete.unlink()

# Main pipeline: require run configuration, preserve split user-execution states.
pipeline_path = "templates/code/hsk_pipeline/main_pipeline.py"
pipeline = read(pipeline_path).replace("6.5.0", "6.5.1")
pipeline = pipeline.replace(
    '        required = {"分析设计", "结论稳定性汇总"}',
    '        required = {"运行配置", "分析设计", "结论稳定性汇总"}',
)
pipeline = pipeline.replace(
    '    if "核心指标" not in solution:\n'
    '        raise KeyError("solution 必须包含“核心指标”")\n'
    '    tables: dict[str, Any] = {\n'
    '        "核心指标": solution["核心指标"],',
    '    for required_sheet in ("运行配置", "核心指标"):\n'
    '        if required_sheet not in solution:\n'
    '            raise KeyError(f"solution 必须包含“{required_sheet}”")\n'
    '    tables: dict[str, Any] = {\n'
    '        "运行配置": solution["运行配置"],\n'
    '        "核心指标": solution["核心指标"],',
)
primary_state = '''def _update_primary_state(primary: PrimarySolveResult, passed: bool) -> None:
    loaded = _load_state(primary.context.config)
    if loaded is None:
        return
    path, state = loaded
    entry = state.setdefault("subproblems", {}).setdefault(
        _question_key(primary.context.config.problem_name), {}
    )
    relative = primary.solution_path.relative_to(primary.context.config.project_root).as_posix()
    entry["solution_workbook"] = relative
    entry["result_quality_report"] = f"{relative}#主结果质量门"
    entry["primary_execution_status"] = "workbook_received" if passed else "rejected"
    entry["result_quality_status"] = "pending" if passed else "failed"
    entry["result_analysis_status"] = "pending"
    entry["execution_note"] = (
        "主工作簿已由用户本地运行生成，等待validate_user_execution.py验收"
        if passed else "主结果质量门未通过，需修正后重跑"
    )
    hashes = entry.setdefault("artifact_hashes", {})
    hashes["solution_workbook"] = _file_hash(primary.solution_path)
    entry.setdefault("validated_artifact_hashes", {}).pop("solution_workbook", None)
    entry["status"] = "designed"
    entry["result_summary_status"] = "stale" if not passed else "pending"
    entry["validation_status"] = "pending"
    entry["artifacts_stale"] = True
    entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | {
        "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
    })
    entry["proposition_refs"] = []
    state.setdefault("paper_framework", {})["sync_status"] = "stale"
    state.setdefault("project", {})["current_phase"] = "solve_validate"
    _write_state(path, state)
'''
pipeline, count = re.subn(
    r"def _update_primary_state\(.*?\n\ndef _normalize_analysis_result",
    primary_state + "\n\ndef _normalize_analysis_result",
    pipeline,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("failed to replace _update_primary_state")
analysis_state = '''def _update_analysis_state(
    primary: PrimarySolveResult,
    analysis_path: Path,
    result: ResultAnalysisResult,
) -> None:
    config = primary.context.config
    loaded = _load_state(config)
    if loaded is None:
        return
    path, state = loaded
    entry = state.setdefault("subproblems", {}).setdefault(_question_key(config.problem_name), {})
    relative = analysis_path.relative_to(config.project_root).as_posix()
    entry["result_analysis_workbook"] = relative
    entry["result_analysis_report"] = f"{relative}#结论稳定性汇总"
    entry["analysis_methods"] = list(result.methods)
    hashes = entry.setdefault("artifact_hashes", {})
    hashes["result_analysis_workbook"] = _file_hash(analysis_path)
    entry.setdefault("validated_artifact_hashes", {}).pop("result_analysis_workbook", None)
    if result.status == "passed":
        entry["analysis_execution_status"] = "workbook_received"
        entry["result_analysis_status"] = "pending"
        entry["execution_note"] = "深化工作簿已由用户本地运行生成，等待validate_user_execution.py验收"
        entry["status"] = "solved"
        entry["artifacts_stale"] = True
        entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | {
            "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
        })
        state.setdefault("project", {})["current_phase"] = "result_analysis"
    elif result.status == "failed":
        entry["analysis_execution_status"] = "rejected"
        entry["result_analysis_status"] = "failed"
        entry["validation_status"] = "pending"
        state.setdefault("project", {})["current_phase"] = "result_analysis"
    else:
        entry["analysis_execution_status"] = "redo_required"
        entry["result_analysis_status"] = "redo_required"
        entry["status"] = "designed"
        entry["validation_status"] = "pending"
        entry["result_summary_status"] = "stale"
        entry["artifacts_stale"] = True
        entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | set(result.stale_layers))
        entry["proposition_refs"] = []
        state.setdefault("project", {})["current_phase"] = result.restart_phase
        state.setdefault("paper_framework", {})["sync_status"] = "stale"
    _write_state(path, state)
'''
pipeline, count = re.subn(
    r"def _update_analysis_state\(.*?\n\ndef project_sync_command",
    analysis_state + "\n\ndef project_sync_command",
    pipeline,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("failed to replace _update_analysis_state")
pipeline = re.sub(
    r"def main\(\) -> None:\n    config = build_config\(Path\(__file__\)\)\n    run_pipeline\(.*?\n\n\nif __name__ == \"__main__\":",
    '''def main() -> None:
    config = build_config(Path(__file__))
    run_primary_pipeline(
        config,
        load_data_hook=load_data,
        preprocess_hook=preprocess_data,
        build_features_hook=build_features,
        solve_hook=solve_model,
        constraint_hook=check_constraints,
        quality_hook=evaluate_primary_quality,
        framework_sync_hook=sync_primary_framework,
    )


if __name__ == "__main__":''',
    pipeline,
    flags=re.S,
)
write(pipeline_path, pipeline)

# Workbook schema: execution evidence is mandatory in both workbooks.
schema_path = "core/workbook_schema.yaml"
schema = read(schema_path)
schema = schema.replace("schema_version: 2.2.0", "schema_version: 2.2.1", 1)
schema = schema.replace(
    "  - MATLAB代码生成前必须读取实际工作簿并确认真实工作表与真实表头。",
    "  - MATLAB代码生成前必须读取实际工作簿并确认真实工作表与真实表头。\n"
    "  - 两类工作簿都必须包含运行配置工作表，作为用户完整版执行、代码/数据哈希和禁止降级标志的验收证据。",
    1,
)
schema = schema.replace(
    "  common_required_sheets:\n    核心指标:",
    "  common_required_sheets:\n    运行配置:\n      required_columns: [项目, 值]\n    核心指标:",
    1,
)
schema = schema.replace(
    "  common_required_sheets:\n    分析设计:",
    "  common_required_sheets:\n    运行配置:\n      required_columns: [项目, 值]\n    分析设计:",
    1,
)
schema = schema.replace(
    "  sheet_schemas:\n    分析设计:",
    "  sheet_schemas:\n    运行配置:\n      required_columns: [项目, 值]\n    分析设计:",
    1,
)
write(schema_path, schema)

# Starter contract tests.
write(
    "tests/test_starter_templates.py",
    '''import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "templates/code/starter"
PIPELINE_DIR = ROOT / "templates/code/hsk_pipeline"
STARTERS = {
    "classification.py": "inference",
    "evaluation.py": "evaluation",
    "optimization.py": "optimization",
    "prediction.py": "prediction",
    "simulation.py": "simulation",
}


class TestStarterTemplates(unittest.TestCase):
    def test_starters_are_primary_only_side_effect_free_entries(self):
        forbidden = (
            "np.random.seed", "PROJECT_ROOT =", "SOLUTION_BOOK", "ROBUSTNESS_BOOK",
            "workbook_paths(", "write_workbook(", "def validate_model(",
            "run_pipeline(", "ResultAnalysisResult", "analyze_results",
            "sync_analysis_framework", "result_analysis_hook=",
        )
        for filename, objective in STARTERS.items():
            path = STARTER_DIR / filename
            text = path.read_text(encoding="utf-8")
            ast.parse(text)
            self.assertIn(f'objective="{objective}"', text)
            self.assertIn("run_primary_pipeline(", text)
            self.assertIn("evaluate_primary_quality", text)
            self.assertIn("sync_primary_framework", text)
            self.assertIn("REQUIRED_CAPABILITIES", text)
            self.assertIn('if __name__ == "__main__":', text)
            for token in forbidden:
                self.assertNotIn(token, text, f"{filename}: {token}")

    def test_importing_starters_does_not_create_outputs(self):
        code_root = str(ROOT / "templates/code")
        added = code_root not in sys.path
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        if added:
            sys.path.insert(0, code_root)
        try:
            before = {path.name for path in STARTER_DIR.glob("*.py")}
            for filename in STARTERS:
                importlib.import_module(f"starter.{Path(filename).stem}")
            after = {path.name for path in STARTER_DIR.glob("*.py")}
            self.assertEqual(before, after)
            self.assertFalse((STARTER_DIR / "结果数据表").exists())
        finally:
            sys.dont_write_bytecode = previous
            if added:
                sys.path.remove(code_root)

    def test_pipeline_keeps_split_runners_and_compatibility_api(self):
        init_text = (PIPELINE_DIR / "__init__.py").read_text(encoding="utf-8")
        pipeline_text = (PIPELINE_DIR / "main_pipeline.py").read_text(encoding="utf-8")
        for token in ("run_primary_pipeline", "run_result_analysis_pipeline", "run_pipeline"):
            self.assertIn(token, init_text)
        self.assertIn("def run_primary_pipeline(", pipeline_text)
        self.assertIn("def run_result_analysis_pipeline(", pipeline_text)
        self.assertIn("def run_pipeline(", pipeline_text)
        self.assertIn('"运行配置": solution["运行配置"]', pipeline_text)
        self.assertIn('required = {"运行配置", "分析设计", "结论稳定性汇总"}', pipeline_text)

    def test_profiles_enable_required_primary_capabilities(self):
        optimization = (STARTER_DIR / "optimization.py").read_text(encoding="utf-8")
        prediction = (STARTER_DIR / "prediction.py").read_text(encoding="utf-8")
        classification = (STARTER_DIR / "classification.py").read_text(encoding="utf-8")
        simulation = (STARTER_DIR / "simulation.py").read_text(encoding="utf-8")
        for token in ("has_explicit_constraints=True", "requires_feasibility_check=True"):
            self.assertIn(token, optimization)
        for text in (prediction, classification):
            self.assertIn("requires_out_of_sample_validation=True", text)
            self.assertIn("requires_leakage_check=True", text)
        self.assertIn("requires_convergence_diagnostic=True", simulation)
        self.assertIn("requires_uncertainty_quantification=True", simulation)

    def test_cleanup_removes_obsolete_active_templates(self):
        self.assertFalse((PIPELINE_DIR / "config.yaml").exists())
        self.assertFalse((ROOT / "templates/review/robustness_check.md").exists())
        self.assertTrue((ROOT / "templates/code/full_fidelity_config.yaml").is_file())
        self.assertTrue((ROOT / "templates/review/result_analysis_check.md").is_file())

    def test_cleanup_has_no_recreatable_or_migrated_residual_files(self):
        self.assertFalse((ROOT / "state/.gitkeep").exists())
        self.assertTrue((ROOT / "state/project_state.example.yaml").is_file())
        self.assertFalse((ROOT / "templates/latex/cumcm/cumcmthesis/example.pdf").exists())
        self.assertTrue((ROOT / "templates/latex/cumcm/cumcmthesis/example.tex").is_file())
        for name in ("hsk_find_project_root.m", "hsk_export_figure.m"):
            self.assertFalse((ROOT / "templates/matlab" / name).exists())
            self.assertTrue((ROOT / "legacy/matlab_compat" / name).is_file())


if __name__ == "__main__":
    unittest.main()
''',
)

# Schema assertions.
test_schemas = read("tests/test_schemas.py")
test_schemas = test_schemas.replace('schema["version"], "6.5.0"', 'schema["version"], "6.5.1"')
test_schemas = test_schemas.replace('schema["schema_version"], "2.2.0"', 'schema["schema_version"], "2.2.1"')
test_schemas = test_schemas.replace(
    'self.assertIn("主结果质量门", schema["solution_workbook"]["common_required_sheets"])',
    'self.assertIn("主结果质量门", schema["solution_workbook"]["common_required_sheets"])\n'
    '        self.assertIn("运行配置", schema["solution_workbook"]["common_required_sheets"])',
)
test_schemas = test_schemas.replace(
    'self.assertEqual(set(analysis["common_required_sheets"]), {"分析设计", "结论稳定性汇总"})',
    'self.assertEqual(set(analysis["common_required_sheets"]), {"运行配置", "分析设计", "结论稳定性汇总"})',
)
test_schemas = test_schemas.replace('contract["version"], "6.5.0"', 'contract["version"], "6.5.1"')
write("tests/test_schemas.py", test_schemas)

# Result I/O test helpers carry the mandatory evidence sheet.
result_io_test = read("tests/test_result_io.py")
result_io_test = result_io_test.replace(
    "    def solution_tables(self):\n        return {\n",
    "    def run_config(self, stage=\"primary\"):\n"
    "        return pd.DataFrame({\"项目\": [\"execution_owner\", \"execution_profile\", \"stage\"], \"值\": [\"user\", \"full_fidelity\", stage]})\n\n"
    "    def solution_tables(self):\n        return {\n            \"运行配置\": self.run_config(\"primary\"),\n",
    1,
)
result_io_test = result_io_test.replace(
    "    def analysis_tables(self):\n        return {\n",
    "    def analysis_tables(self):\n        return {\n            \"运行配置\": self.run_config(\"analysis\"),\n",
    1,
)
result_io_test = result_io_test.replace(
    '{"核心指标", "数据审计", "主结果质量门"}',
    '{"运行配置", "核心指标", "数据审计", "主结果质量门"}',
)
result_io_test = result_io_test.replace(
    '        only_headers = {\n            "分析设计":',
    '        only_headers = {\n            "运行配置": self.analysis_tables()["运行配置"],\n            "分析设计":',
)
write("tests/test_result_io.py", result_io_test)

# Sync-project workbook builders.
sync_test = read("tests/test_sync_project.py")
sync_test = sync_test.replace(
    "def write_solution(path: Path, *, constraint=False, out_of_sample=False, objective=\"optimization\"):\n    book = Workbook()\n",
    "def write_solution(path: Path, *, constraint=False, out_of_sample=False, objective=\"optimization\"):\n"
    "    book = Workbook()\n"
    "    append_sheet(book, \"运行配置\", [\"项目\", \"值\"], [\"stage\", \"primary\"])\n",
    1,
)
sync_test = sync_test.replace(
    "def write_analysis(path: Path):\n    book = Workbook()\n",
    "def write_analysis(path: Path):\n"
    "    book = Workbook()\n"
    "    append_sheet(book, \"运行配置\", [\"项目\", \"值\"], [\"stage\", \"analysis\"])\n",
    1,
)
write("tests/test_sync_project.py", sync_test)

# Runtime tests carry evidence and assert workbook_received semantics.
runtime_test = read("tests/test_split_pipeline_runtime.py")
runtime_test = runtime_test.replace(
    "def solve(features, cfg):\n    return {\n",
    "def run_config(stage):\n"
    "    return pd.DataFrame({\"项目\": [\"execution_owner\", \"execution_profile\", \"stage\"], \"值\": [\"user\", \"full_fidelity\", stage]})\n\n\n"
    "def solve(features, cfg):\n    return {\n        \"运行配置\": run_config(\"primary\"),\n",
    1,
)
runtime_test = runtime_test.replace(
    '            tables = {\n                "分析设计":',
    '            tables = {\n                "运行配置": run_config("analysis"),\n                "分析设计":',
    1,
)
runtime_test = runtime_test.replace(
    '            self.assertEqual(entry["result_analysis_status"], "redo_required")',
    '            self.assertEqual(entry["analysis_execution_status"], "redo_required")\n'
    '            self.assertEqual(entry["result_analysis_status"], "redo_required")',
    1,
)
write("tests/test_split_pipeline_runtime.py", runtime_test)

# Active residue regression.
residue = read("tests/test_active_residue_cleanup.py")
anchor = "    def test_root_and_packaged_skill_versions_match(self) -> None:\n"
addition = '''    def test_v651_obsolete_templates_are_absent(self) -> None:
        self.assertFalse((ROOT / "templates/review/robustness_check.md").exists())
        self.assertFalse((ROOT / "templates/code/hsk_pipeline/config.yaml").exists())
        self.assertTrue((ROOT / "templates/review/result_analysis_check.md").is_file())
        self.assertTrue((ROOT / "templates/code/full_fidelity_config.yaml").is_file())

    def test_current_starters_stop_at_primary_user_execution_gate(self) -> None:
        for path in (ROOT / "templates/code/starter").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("run_primary_pipeline(", text, path.name)
            self.assertNotIn("run_pipeline(", text, path.name)
            self.assertNotIn("analyze_results", text, path.name)

'''
if anchor not in residue:
    raise RuntimeError("active residue test anchor missing")
residue = residue.replace(anchor, addition + anchor, 1)
write("tests/test_active_residue_cleanup.py", residue)

# Version coordination.
version_files = (
    ".codex-plugin/plugin.json", "SKILL.md", "skills/mathmodel-skill/SKILL.md", "README.md",
    "AGENTS.md", "PROJECT_INSTRUCTIONS.md", "RUNTIME_ROUTER.md", "scripts/README.md",
    "agents/openai.yaml", "core/bootstrap.yaml", "core/hsk_core_policy.md",
    "core/module_manifest.yaml", "core/output_contract.yaml", "core/project_state.schema.yaml",
    "core/user_execution_contract.yaml", "core/workflow_router.yaml", "scripts/generate_indexes.py",
    "scripts/lint_skill.py", "scripts/resolve_workflow.py", "templates/code/hsk_pipeline/matlab_handoff.py",
    "legacy/README.md",
)
for relative in version_files:
    text = read(relative)
    if "6.5.0" not in text:
        raise RuntimeError(f"version marker missing in {relative}")
    write(relative, text.replace("6.5.0", "6.5.1"))

# Lint expects the workbook schema patch version.
lint = read("scripts/lint_skill.py").replace(
    'workbook.get("schema_version") != "2.2.0"',
    'workbook.get("schema_version") != "2.2.1"',
).replace(
    'workbook schema version must be 2.2.0',
    'workbook schema version must be 2.2.1',
)
write("scripts/lint_skill.py", lint)

# Changelog keeps historical releases intact.
changelog = read("CHANGELOG.md")
old_heading = "## Current release: 6.5.0\n"
new_heading = """## Current release: 6.5.1

- Removed the obsolete fixed sensitivity/robustness checklist and the unreferenced pre-user-execution pipeline config.
- New-project starters now stop after `run_primary_pipeline()`; `run_pipeline()` remains only as a user-local compatibility API.
- Local workbook generation records `workbook_received` and can no longer promote a subproblem to `solved` or `analyzed` before returned-workbook validation.
- Both standard workbooks now require the `运行配置` evidence sheet; workbook schema version is 2.2.1.

## Previous release: 6.5.0
"""
if old_heading not in changelog:
    raise RuntimeError("changelog current-release anchor missing")
write("CHANGELOG.md", changelog.replace(old_heading, new_heading, 1))

# Final source-level assertions before CI.
for forbidden in (
    ROOT / "templates/review/robustness_check.md",
    ROOT / "templates/code/hsk_pipeline/config.yaml",
):
    if forbidden.exists():
        raise RuntimeError(f"obsolete file still exists: {forbidden}")
for starter in (ROOT / "templates/code/starter").glob("*.py"):
    text = starter.read_text(encoding="utf-8")
    if "run_primary_pipeline(" not in text or "run_pipeline(" in text:
        raise RuntimeError(f"invalid starter gate: {starter}")
