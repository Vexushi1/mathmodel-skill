from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one exact match, found {count}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def replace_all_version(path: str) -> None:
    text = read(path)
    if "7.2.4" not in text:
        raise RuntimeError(f"{path}: no 7.2.4 marker found")
    write(path, text.replace("7.2.4", "7.2.5"))


VERSION_FILES = [
    "SKILL.md",
    "skills/mathmodel-skill/SKILL.md",
    ".codex-plugin/plugin.json",
    "README.md",
    "legacy/README.md",
    "scripts/README.md",
    "core/bootstrap.yaml",
    "core/hsk_core_policy.md",
    "core/code_quality_contract.yaml",
    "core/project_state.schema.yaml",
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "core/user_execution_contract.yaml",
    "core/global_preprocessing_contract.yaml",
    "scripts/resolve_workflow.py",
    "scripts/lint_skill.py",
    "tests/test_schemas.py",
    "tests/test_v701_stage_boundary_closure.py",
]

for item in VERSION_FILES:
    replace_all_version(item)

# 1) Resolver: normalize accepted preprocessing artifact alias before all dependency checks.
replace_once(
    "scripts/resolve_workflow.py",
    '    available_set = set(available_artifacts or ())\n',
    '    available_set = set(available_artifacts or ())\n'
    '    if "accepted_preprocessing_workbook" in available_set:\n'
    '        available_set.add("preprocessing_workbook")\n',
)
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '        self.assertIn("python_code", plan["terminal_outputs"])\n\n    def test_state_schema_supports_conditional_preprocessing_phase(self):\n',
    '        self.assertIn("python_code", plan["terminal_outputs"])\n'
    '        self.assertNotIn("solve_validate:preprocessing_workbook", plan["missing_prerequisites"])\n\n'
    '    def test_state_schema_supports_conditional_preprocessing_phase(self):\n',
)

# 2) State contract: explicitly list only raw sources replaced by the unified workbook.
replace_once(
    "core/project_state.schema.yaml",
    '      operations:\n        type: array\n        uniqueItems: true\n        items: {type: string}\n      forbidden_operations:\n',
    '      operations:\n        type: array\n        uniqueItems: true\n        items: {type: string}\n'
    '      covered_raw_sources:\n'
    '        description: decision=project_level时被统一工作簿替代、下游不得再次直接读取的原始数据源路径；仅列实际覆盖源，未列出的独立辅助附件可继续按模型需要读取。\n'
    '        type: array\n'
    '        minItems: 1\n'
    '        uniqueItems: true\n'
    '        items: {type: string, minLength: 1}\n'
    '      forbidden_operations:\n',
)
replace_once(
    "core/global_preprocessing_contract.yaml",
    '      raw_readers_allowed:\n      - 数据预处理/数据预处理.py\n      downstream_raw_read_forbidden: true\n      rule: 统一工作簿通过质量门后，所有依赖该公共数据口径的主求解、深化分析和数据型MATLAB流程不得再次直接读取共享原始数据；如需改变公共口径必须回退本阶段并传播stale。\n',
    '      raw_readers_allowed:\n      - 数据预处理/数据预处理.py\n'
    '      covered_raw_sources_field: state.preprocessing.covered_raw_sources\n'
    '      covered_raw_sources_required: true\n'
    '      independent_raw_sources_allowed: true\n'
    '      downstream_raw_read_forbidden: true\n'
    '      rule: 统一工作簿通过质量门后，state.preprocessing.covered_raw_sources中列出的原始源由统一工作簿替代，依赖该公共口径的主求解、深化分析和数据型MATLAB流程不得再次直接读取这些源；未列入covered_raw_sources的独立辅助附件可按题意继续读取。如需改变覆盖范围或公共口径必须回退本阶段并传播stale。\n',
)
replace_once(
    "core/global_preprocessing_contract.yaml",
    '  - 读取需要统一处理的共享原始数据源\n',
    '  - 读取需要统一处理的共享原始数据源，并把实际被统一工作簿替代的路径冻结到state.preprocessing.covered_raw_sources\n',
)
replace_once(
    "core/user_execution_contract.yaml",
    '  task_prediction_is_not_preprocessing: true\n  substantive_preprocessing_requires_paper_evidence: true\n',
    '  task_prediction_is_not_preprocessing: true\n'
    '  project_level_covered_raw_sources_required: true\n'
    '  substantive_preprocessing_requires_paper_evidence: true\n',
)
replace_once(
    "core/user_execution_contract.yaml",
    '    role: 读取需要统一处理的共享原始数据，执行通用审计和已批准公共处理，输出数据预处理结果.xlsx；同时保存论文公式/方法证据、处理前后对比、验证和data_process绘图底层数据\n',
    '    role: 读取需要统一处理的共享原始数据，冻结covered_raw_sources，执行通用审计和已批准公共处理，输出数据预处理结果.xlsx；同时保存论文公式/方法证据、处理前后对比、验证和data_process绘图底层数据\n',
)
replace_once(
    "modules/03_data_preprocessing.md",
    '- 只执行 `preprocessing_decision.operations` 中已批准的公共处理；\n',
    '- 只执行 `preprocessing_decision.operations` 中已批准的公共处理，并将被统一工作簿替代的原始路径显式写入 `state.preprocessing.covered_raw_sources`；\n',
)

# 3) Code-delivery runtime gate: project-level downstream scripts must use the accepted data fact source.
replace_once(
    "scripts/validate_code_delivery.py",
    'VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}\n\n\ndef load_yaml',
    'VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}\n'
    'DATA_READER_NAMES = {\n'
    '    "open", "ExcelFile", "read_csv", "read_excel", "read_table", "read_fwf",\n'
    '    "read_json", "read_parquet", "read_feather", "read_pickle", "read_hdf",\n'
    '    "load", "loadtxt", "genfromtxt",\n'
    '}\n'
    'DATA_READER_PATH_KEYWORDS = {"path", "filepath", "filename", "fname", "io", "filepath_or_buffer"}\n\n\n'
    'def load_yaml',
)
replace_once(
    "scripts/validate_code_delivery.py",
    'def _decision_gate_issues(project_root: Path, stage: str, data_hash: str | None = None) -> list[str]:\n',
    '''def _normalize_path_token(value: Any) -> str:\n    text = str(value or "").strip().replace("\\\\", "/")\n    while text.startswith("./"):\n        text = text[2:]\n    return text.casefold()\n\n\ndef _path_matches(candidate: Any, target: Any) -> bool:\n    left = _normalize_path_token(candidate)\n    right = _normalize_path_token(target)\n    if not left or not right:\n        return False\n    return left == right or left.endswith("/" + right) or right.endswith("/" + left)\n\n\ndef _call_leaf_name(node: ast.AST) -> str:\n    if isinstance(node, ast.Name):\n        return node.id\n    if isinstance(node, ast.Attribute):\n        return node.attr\n    return ""\n\n\ndef _literal_path_argument(node: ast.AST) -> str | None:\n    if isinstance(node, ast.Constant) and isinstance(node.value, str):\n        return node.value\n    if isinstance(node, ast.Call) and _call_leaf_name(node.func) in {"Path", "str"} and node.args:\n        return _literal_path_argument(node.args[0])\n    return None\n\n\ndef literal_data_reader_paths(text: str) -> list[str]:\n    try:\n        tree = ast.parse(text)\n    except SyntaxError:\n        return []\n    found: list[str] = []\n    for node in ast.walk(tree):\n        if not isinstance(node, ast.Call) or _call_leaf_name(node.func) not in DATA_READER_NAMES:\n            continue\n        candidate: ast.AST | None = node.args[0] if node.args else None\n        if candidate is None:\n            candidate = next(\n                (item.value for item in node.keywords if item.arg in DATA_READER_PATH_KEYWORDS),\n                None,\n            )\n        if candidate is not None:\n            value = _literal_path_argument(candidate)\n            if value:\n                found.append(value)\n    return list(dict.fromkeys(found))\n\n\ndef _decision_gate_issues(\n    project_root: Path,\n    stage: str,\n    data_hash: str | None = None,\n    data_paths: Any = None,\n    code_text: str = "",\n) -> list[str]:\n''',
)
replace_once(
    "scripts/validate_code_delivery.py",
    '''    if stage == "primary" and decision == "project_level":\n        if preprocessing.get("status") != "accepted" or preprocessing.get("quality_status") != "passed":\n            issues.append("project_level项目必须先验收数据预处理结果.xlsx并通过预处理质量门")\n        expected = str(preprocessing.get("workbook_sha256", "")).lower()\n        if expected and data_hash and expected != str(data_hash).lower():\n            issues.append("主求解data_sha256必须等于已验收数据预处理结果.xlsx哈希")\n    return issues\n''',
    '''    if stage in {"primary", "analysis"} and decision == "project_level":\n        if preprocessing.get("status") != "accepted" or preprocessing.get("quality_status") != "passed":\n            issues.append("project_level项目必须先验收数据预处理结果.xlsx并通过预处理质量门")\n        expected = str(preprocessing.get("workbook_sha256", "")).lower()\n        if expected and data_hash and expected != str(data_hash).lower():\n            issues.append(f"{stage}阶段data_sha256必须等于已验收数据预处理结果.xlsx哈希")\n\n        covered = [str(item) for item in (preprocessing.get("covered_raw_sources") or []) if str(item).strip()]\n        if not covered:\n            issues.append("project_level必须在state.preprocessing.covered_raw_sources声明被统一工作簿替代的原始数据源")\n        configured_paths = [str(item) for item in (data_paths or [])] if isinstance(data_paths, (list, tuple)) else []\n        workbook = str(preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx")\n        if stage == "primary" and not any(_path_matches(item, workbook) for item in configured_paths):\n            issues.append("project_level主求解FULL_FIDELITY_CONFIG.data_paths必须包含已验收数据预处理结果.xlsx")\n        for item in configured_paths:\n            if any(_path_matches(item, source) for source in covered):\n                issues.append(f"project_level下游data_paths不得重新声明已覆盖共享原始数据源: {item}")\n        for item in literal_data_reader_paths(code_text):\n            if any(_path_matches(item, source) for source in covered):\n                issues.append(f"project_level下游代码不得重新读取已覆盖共享原始数据源: {item}")\n    return list(dict.fromkeys(issues))\n''',
)
replace_once(
    "scripts/validate_code_delivery.py",
    '    issues.extend(_decision_gate_issues(project_root, stage, str(config.get("data_sha256", ""))))\n',
    '    issues.extend(_decision_gate_issues(\n'
    '        project_root, stage, str(config.get("data_sha256", "")),\n'
    '        config.get("data_paths"), text,\n'
    '    ))\n',
)

# Regression coverage for source facts and independent auxiliary sources.
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '    def test_figure_evidence_order_matches_router_stage_boundary(self):\n',
    '''    def test_project_level_code_gate_blocks_covered_raw_source_but_allows_independent_auxiliary(self):\n        config = {\n            "execution_owner": "user", "execution_profile": "full_fidelity",\n            "stage": "primary", "problem_name": "问题一",\n            "data_paths": ["数据预处理/数据预处理结果.xlsx", "data/aux.csv"],\n            "data_sha256": "b" * 64, "solver": "test", "solver_version": "1",\n            "random_seed": 2026, "tolerance": 1e-8, "iteration_or_time_limit": "full",\n            "expected_workbook": "问题一求解结果.xlsx",\n            "allow_reduced_data": False, "allow_coarser_grid": False,\n            "allow_shorter_horizon": False, "allow_fewer_repetitions": False,\n            "allow_relaxed_tolerance": False, "allow_silent_solver_fallback": False,\n        }\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            (root / "state").mkdir()\n            (root / "state/project_state.yaml").write_text(\n                yaml.safe_dump({"preprocessing": {\n                    "decision": "project_level", "status": "accepted", "quality_status": "passed",\n                    "workbook": "数据预处理/数据预处理结果.xlsx", "workbook_sha256": "b" * 64,\n                    "covered_raw_sources": ["data/raw.csv"],\n                }}, allow_unicode=True),\n                encoding="utf-8",\n            )\n            folder = root / "问题一求解"\n            folder.mkdir()\n            script = folder / "问题一求解.py"\n            script.write_text(\n                "FULL_FIDELITY_CONFIG = " + repr(config)\n                + "\\nimport pandas as pd\\ndef main():\\n    pd.read_csv('data/raw.csv')\\n    return 0"\n                + "\\nif __name__ == '__main__':\\n    raise SystemExit(main())\\n",\n                encoding="utf-8",\n            )\n            issues, _ = self.code_gate.validate_script(root, script, "primary")\n            self.assertTrue(any("不得重新读取已覆盖共享原始数据源" in item for item in issues))\n\n            script.write_text(\n                "FULL_FIDELITY_CONFIG = " + repr(config)\n                + "\\nimport pandas as pd\\ndef main():\\n    pd.read_csv('data/aux.csv')\\n    return 0"\n                + "\\nif __name__ == '__main__':\\n    raise SystemExit(main())\\n",\n                encoding="utf-8",\n            )\n            issues, _ = self.code_gate.validate_script(root, script, "primary")\n            self.assertFalse(any("共享原始数据源" in item for item in issues))\n\n    def test_figure_evidence_order_matches_router_stage_boundary(self):\n''',
)

# 4) MATLAB gate: strip inline comments and block dynamic dispatch/forbidden function handles.
replace_once(
    "scripts/sync_project.py",
    '''MATLAB_PREPROCESSING_FORBIDDEN_RE = re.compile(\n    r"(?<![\\w])("\n    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)\n    + r")\\s*\\(",\n    re.IGNORECASE,\n)\n''',
    '''MATLAB_PREPROCESSING_FORBIDDEN_RE = re.compile(\n    r"(?<![\\w])("\n    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)\n    + r")\\s*\\(",\n    re.IGNORECASE,\n)\nMATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_FUNCTIONS = ("eval", "evalin", "feval", "str2func", "builtin")\nMATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_RE = re.compile(\n    r"(?<![\\w])("\n    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_FUNCTIONS)\n    + r")\\s*\\(",\n    re.IGNORECASE,\n)\nMATLAB_PREPROCESSING_FORBIDDEN_HANDLE_RE = re.compile(\n    r"@(" + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS) + r")\\b",\n    re.IGNORECASE,\n)\n''',
)
replace_once(
    "scripts/sync_project.py",
    'def _parse_matlab(script: Path) -> tuple[bool, list[str], list[str]]:\n',
    '''def _matlab_executable_text(text: str) -> str:\n    """Remove MATLAB comments while preserving percent signs inside quoted strings."""\n    cleaned: list[str] = []\n    for source in text.splitlines():\n        line = source\n        in_single = False\n        in_double = False\n        index = 0\n        while index < len(line):\n            char = line[index]\n            if char == '"' and not in_single:\n                if in_double and index + 1 < len(line) and line[index + 1] == '"':\n                    index += 2\n                    continue\n                in_double = not in_double\n            elif char == "'" and not in_double:\n                if in_single:\n                    if index + 1 < len(line) and line[index + 1] == "'":\n                        index += 2\n                        continue\n                    in_single = False\n                else:\n                    previous = line[index - 1] if index else ""\n                    if not previous or not (previous.isalnum() or previous in "_)]}."):\n                        in_single = True\n            elif char == "%" and not in_single and not in_double:\n                line = line[:index]\n                break\n            index += 1\n        cleaned.append(line)\n    return "\\n".join(cleaned)\n\n\ndef _parse_matlab(script: Path) -> tuple[bool, list[str], list[str]]:\n''',
)
replace_once(
    "scripts/sync_project.py",
    '''            text = matlab.read_text(encoding="utf-8", errors="ignore")\n            code_text = "\\n".join(\n                line for line in text.splitlines() if not line.lstrip().startswith("%")\n            )\n            forbidden_matches = sorted({\n                match.group(1).lower()\n                for match in MATLAB_PREPROCESSING_FORBIDDEN_RE.finditer(code_text)\n            })\n            if forbidden_matches:\n                issues.append(\n                    "data_process.m不得重新执行预处理、拟合或预测；检测到MATLAB调用: "\n                    + ", ".join(forbidden_matches)\n                )\n''',
    '''            text = matlab.read_text(encoding="utf-8", errors="ignore")\n            code_text = _matlab_executable_text(text)\n            forbidden_matches = sorted({\n                match.group(1).lower()\n                for match in MATLAB_PREPROCESSING_FORBIDDEN_RE.finditer(code_text)\n            })\n            dispatch_matches = sorted({\n                match.group(1).lower()\n                for match in MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_RE.finditer(code_text)\n            })\n            handle_matches = sorted({\n                match.group(1).lower()\n                for match in MATLAB_PREPROCESSING_FORBIDDEN_HANDLE_RE.finditer(code_text)\n            })\n            if forbidden_matches:\n                issues.append(\n                    "data_process.m不得重新执行预处理、拟合或预测；检测到MATLAB调用: "\n                    + ", ".join(forbidden_matches)\n                )\n            if dispatch_matches:\n                issues.append(\n                    "data_process.m不得使用可绕过绘图职责边界的动态调用: "\n                    + ", ".join(dispatch_matches)\n                )\n            if handle_matches:\n                issues.append(\n                    "data_process.m不得持有被禁止预处理函数句柄: "\n                    + ", ".join(handle_matches)\n                )\n''',
)
replace_once(
    "core/global_preprocessing_contract.yaml",
    '  runtime_forbidden_matlab_functions: [interp1, interp2, interp3, interpn, griddedInterpolant, scatteredInterpolant, fillmissing, rmmissing, standardizeMissing, filloutliers, rmoutliers, isoutlier, smooth, smoothdata, movmean, movmedian, resample, interpft, decimate, downsample, upsample, retime, synchronize, detrend, normalize, rescale, zscore, filter, filtfilt, designfilt, lowpass, highpass, bandpass, bandstop, butter, cheby1, cheby2, ellip, fir1, fir2, fit, fitlm, fitrlinear, fitrgp, fitrensemble, fitrtree, predict, trainNetwork, trainnet]\n  runtime_gate_rule: figures及后续正式交付时，sync_project必须对data_process.m实际代码执行函数调用扫描；命中上述函数即拒绝交付。完整行注释不参与扫描，避免说明性注释造成误报。\n',
    '  runtime_forbidden_matlab_functions: [interp1, interp2, interp3, interpn, griddedInterpolant, scatteredInterpolant, fillmissing, rmmissing, standardizeMissing, filloutliers, rmoutliers, isoutlier, smooth, smoothdata, movmean, movmedian, resample, interpft, decimate, downsample, upsample, retime, synchronize, detrend, normalize, rescale, zscore, filter, filtfilt, designfilt, lowpass, highpass, bandpass, bandstop, butter, cheby1, cheby2, ellip, fir1, fir2, fit, fitlm, fitrlinear, fitrgp, fitrensemble, fitrtree, predict, trainNetwork, trainnet]\n'
    '  runtime_forbidden_matlab_dispatch_functions: [eval, evalin, feval, str2func, builtin]\n'
    '  runtime_gate_rule: figures及后续正式交付时，sync_project必须对data_process.m剥离行尾/整行注释后的实际代码执行函数调用扫描；命中上述预处理函数、动态调度函数或被禁止函数句柄即拒绝交付，避免通过feval/str2func/@function等方式绕过绘图职责边界。\n',
)
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '        runtime = set(self.sync.MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)\n        self.assertEqual(declared, runtime)\n',
    '        runtime = set(self.sync.MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)\n'
    '        self.assertEqual(declared, runtime)\n'
    '        declared_dispatch = set(self.contract["preprocessing_figure_contract"]["runtime_forbidden_matlab_dispatch_functions"])\n'
    '        runtime_dispatch = set(self.sync.MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_FUNCTIONS)\n'
    '        self.assertEqual(declared_dispatch, runtime_dispatch)\n',
)
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '''            script.write_text(\n                '% normalize(x) 仅为说明，不应触发\\ntitle("证据图");\\nbook = "数据预处理结果.xlsx";\\nplot(x, y);\\n',\n                encoding="utf-8",\n            )\n            issues = self.sync._preprocessing_artifact_issues(\n                root,\n                {"preprocessing_matlab_script"},\n                {"preprocessing": {"decision": "project_level"}},\n            )\n            self.assertFalse(any("不得重新执行预处理" in item for item in issues))\n''',
    '''            script.write_text(\n                'title("证据图");\\nbook = "数据预处理结果.xlsx";\\nplot(x, y); % normalize(x) 仅为行尾说明\\n',\n                encoding="utf-8",\n            )\n            issues = self.sync._preprocessing_artifact_issues(\n                root,\n                {"preprocessing_matlab_script"},\n                {"preprocessing": {"decision": "project_level"}},\n            )\n            self.assertFalse(any("不得重新执行预处理" in item for item in issues))\n\n            script.write_text(\n                'title("证据图");\\nbook = "数据预处理结果.xlsx";\\ny = feval("normalize", x);\\n',\n                encoding="utf-8",\n            )\n            issues = self.sync._preprocessing_artifact_issues(\n                root,\n                {"preprocessing_matlab_script"},\n                {"preprocessing": {"decision": "project_level"}},\n            )\n            self.assertTrue(any("动态调用" in item and "feval" in item for item in issues))\n\n            script.write_text(\n                'title("证据图");\\nbook = "数据预处理结果.xlsx";\\nf = @normalize;\\ny = f(x);\\n',\n                encoding="utf-8",\n            )\n            issues = self.sync._preprocessing_artifact_issues(\n                root,\n                {"preprocessing_matlab_script"},\n                {"preprocessing": {"decision": "project_level"}},\n            )\n            self.assertTrue(any("函数句柄" in item and "normalize" in item for item in issues))\n''',
)

# 5) Clarify that data_process.m belongs to preprocessing evidence but is generated in Figure Evidence.
for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace_once(
        path,
        '`data_process.m` 是预处理阶段固定 MATLAB 绘图脚本名，只读取 `数据预处理结果.xlsx` 中 Python 已保存的处理前后、诊断和验证底层数据，',
        '`data_process.m` 是项目级预处理证据的固定 MATLAB 绘图脚本名；文件归属 `数据预处理/`，但仅在 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只读取 `数据预处理结果.xlsx` 中 Python 已保存的处理前后、诊断和验证底层数据，',
    )
replace_once(
    "modules/03_data_preprocessing.md",
    '这是**预处理阶段固定 MATLAB 绘图脚本名**。它只能读取 `数据预处理结果.xlsx` 中 Python 已持久化的数据，负责：',
    '这是**项目级预处理证据的固定 MATLAB 绘图脚本名**；文件归属 `数据预处理/`，但仅在后续 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只能读取 `数据预处理结果.xlsx` 中 Python 已持久化的数据，负责：',
)
replace_once(
    "core/user_execution_contract.yaml",
    '  - 在预处理工作簿accepted后生成data_process.m；该MATLAB脚本只读工作簿绘图，不执行数值预处理\n',
    '  - 在预处理工作簿accepted、主求解与结果深化分析完成后，于Figure Evidence阶段生成data_process.m；该MATLAB脚本只读工作簿绘图，不执行数值预处理\n',
)

# Changelog: keep v7.2.4 history and prepend v7.2.5.
replace_once(
    "CHANGELOG.md",
    '## Current release: 7.2.4\n\n',
    '''## Current release: 7.2.5\n\n- Normalized `accepted_preprocessing_workbook` to the canonical `preprocessing_workbook` artifact before resolver dependency reporting, eliminating false missing-prerequisite warnings after an accepted project-level preprocessing workbook.\n- Added `state.preprocessing.covered_raw_sources` so project-level preprocessing explicitly records only the raw sources replaced by the unified workbook; independent auxiliary attachments remain readable when they are not covered.\n- Hardened `validate_code_delivery.py` so project-level primary/analysis code must retain the accepted preprocessing data hash, primary code must declare the unified workbook in `data_paths`, and covered raw sources cannot be reintroduced through `data_paths` or literal data-reader calls.\n- Hardened `data_process.m` runtime checks by stripping inline MATLAB comments and blocking dynamic dispatch (`eval`, `evalin`, `feval`, `str2func`, `builtin`) plus forbidden preprocessing function handles.\n- Clarified across Skill/module contracts that `data_process.m` belongs to the project-level preprocessing evidence directory but is generated only in the later Figure Evidence stage after primary solve and result analysis.\n\n## Previous release: 7.2.4\n\n''',
)

# Remove this one-shot patcher from the final branch content. Workflow removes itself too.
(ROOT / "scripts/apply_v725_patch.py").unlink()
workflow = ROOT / ".github/workflows/apply-v725.yml"
if workflow.exists():
    workflow.unlink()

print("v7.2.5 protected patch applied")
