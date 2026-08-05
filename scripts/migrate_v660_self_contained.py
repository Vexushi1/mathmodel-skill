from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.6.0"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace(path: str, old: str, new: str, *, required: bool = True) -> None:
    text = read(path)
    if required and old not in text:
        raise RuntimeError(f"{path}: missing replacement token: {old!r}")
    write(path, text.replace(old, new))


def dump_yaml(path: str, payload: dict) -> None:
    write(path, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120))


def bump_versions() -> None:
    replacements = {
        "core/bootstrap.yaml": [("skill_version: 6.5.1", f"skill_version: {VERSION}")],
        "core/workflow_router.yaml": [("version: 6.5.1", f"version: {VERSION}")],
        "core/module_manifest.yaml": [("version: 6.5.1", f"version: {VERSION}")],
        "core/output_contract.yaml": [("version: 6.5.1", f"version: {VERSION}")],
        "core/project_state.schema.yaml": [("skill_version: 6.5.1", f"skill_version: {VERSION}")],
        "core/user_execution_contract.yaml": [("skill_version: 6.5.1", f"skill_version: {VERSION}")],
        "scripts/lint_skill.py": [("PACKAGE_VERSION = \"6.5.1\"", f"PACKAGE_VERSION = \"{VERSION}\"")],
        "scripts/resolve_workflow.py": [("HSK v6.5.1", f"HSK v{VERSION}")],
        "scripts/generate_indexes.py": [("6.5.1", VERSION)],
        "templates/code/hsk_pipeline/main_pipeline.py": [("v6.5.1", f"v{VERSION}")],
        "templates/code/hsk_pipeline/matlab_handoff.py": [("6.5.1", VERSION)],
        "AGENTS.md": [("v6.5.1", f"v{VERSION}")],
        "README.md": [("6.5.1", VERSION)],
        "SKILL.md": [("6.5.1", VERSION)],
        "PROJECT_INSTRUCTIONS.md": [("v6.5.1", f"v{VERSION}")],
        "RUNTIME_ROUTER.md": [("v6.5.1", f"v{VERSION}")],
        "scripts/README.md": [("v6.5.1", f"v{VERSION}")],
        "templates/code/hsk_pipeline/README.md": [("v6.5.1", f"v{VERSION}")],
        "templates/code/starter/README.md": [("v6.5.1", f"v{VERSION}")],
        "skills/mathmodel-skill/SKILL.md": [("6.5.1", VERSION)],
        ".codex-plugin/plugin.json": [("\"version\": \"6.5.1\"", f"\"version\": \"{VERSION}\"")],
    }
    for path, pairs in replacements.items():
        for old, new in pairs:
            replace(path, old, new, required=False)

    changelog = read("CHANGELOG.md")
    marker = "# Changelog\n\n"
    entry = (
        f"## Current release: {VERSION}\n\n"
        "- Restored one self-contained `问题X求解/` directory per subproblem.\n"
        "- New projects keep exactly one evolving Python script, two standard workbooks and one `qX_plot.m` in that directory.\n"
        "- Removed standalone run-config, execution-instruction and validation-report files from the default user-visible output.\n"
        "- Fixed cross-question Python hash contamination in project synchronization.\n"
        "- Kept legacy `结果数据表/问题X/` and separate analysis-code layouts as read-only compatibility inputs.\n"
        "- Corrected the nested plugin entry path and removed the stale LaTeX module version title.\n\n"
        "## Previous release: 6.5.1\n"
    )
    if f"## Current release: {VERSION}" not in changelog:
        changelog = changelog.replace(marker + "## Current release: 6.5.1\n", marker + entry, 1)
        write("CHANGELOG.md", changelog)


def update_output_contract() -> None:
    path = "core/output_contract.yaml"
    data = yaml.safe_load(read(path))
    data["version"] = VERSION
    project = data["project_root"]
    project.pop("python_scripts", None)
    project.pop("result_tables", None)
    project["per_question_outputs"] = "问题{中文序号}求解/"

    sync = data["project_sync"]
    sync["stage_requirements"]["code"] = ["project_state", "model_paper_framework", "python_code"]
    sync["stage_requirements"]["results"] = [
        "project_state", "model_paper_framework", "python_code", "solution_workbook",
        "result_quality_report", "result_analysis_workbook", "result_analysis_report",
    ]
    sync["stage_requirements"]["figures"] = [
        "project_state", "model_paper_framework", "solution_workbook", "result_quality_report",
        "result_analysis_workbook", "result_analysis_report", "matlab_scripts",
    ]
    sync["responsibilities"] = [
        "进入产物同步前强制执行项目状态Schema/语义校验与模型论文框架校验",
        "发现每问问题X求解目录中的唯一Python脚本、两类工作簿和qX_plot.m",
        "复用工作簿Schema检查工作表、字段、capability条件、主键、非有限数值和约束判定",
        "普通阶段同步按小问status检查最低产物；只有显式delivery scope执行正式交付全量门槛",
        "正式交付同时核对工作簿存在、质量与分析状态为passed以及下游产物非stale",
        "核对MATLAB对同目录两个标准工作簿的真实引用，不要求脚本自动导出图片",
        "按小问独立计算输入、唯一Python脚本、两类工作簿、MATLAB脚本和框架哈希",
        "当已验证哈希变化时按证据链传播stale",
        "只允许设置或保持stale；清除stale必须由质量门或结果分析流程显式完成",
        "对DOCX、LaTeX与提交scope检查真实文件、编译报告、图片引用和提交ZIP内容",
    ]
    sync["figure_provenance"] = {
        "default": "不生成独立figure_evidence文件",
        "legacy_read_compatibility": "结果数据表/问题X/figure_evidence.yaml",
        "mtime_role": "仅作辅助警告，不作为主要判定",
    }

    data["per_question"] = {
        "question_directory": "问题{中文序号}求解/",
        "python_script": "问题{中文序号}求解.py",
        "mandatory_workbooks": {
            "solution": "问题{中文序号}求解结果.xlsx",
            "result_analysis": "问题{中文序号}结果深化分析.xlsx",
        },
        "matlab_script": "q{阿拉伯序号}_plot.m",
        "exact_default_files": [
            "问题{中文序号}求解.py",
            "问题{中文序号}求解结果.xlsx",
            "问题{中文序号}结果深化分析.xlsx",
            "q{阿拉伯序号}_plot.m",
        ],
        "single_python_update_policy": "主求解阶段先交付同一脚本；主工作簿验收后在原文件中加入结果深化分析并覆盖更新，不另建分析脚本",
        "no_auxiliary_files_by_default": True,
        "legacy_compatibility": {
            "result_directory": "结果数据表/问题{中文序号}/",
            "separate_analysis_code": "问题{中文序号}结果深化分析.py",
            "sensitivity_robustness_filename": "问题{中文序号}敏感性与鲁棒性结果.xlsx",
            "mode": "read_only",
        },
    }

    matlab = data["matlab_figure_contract"]
    matlab["declared_export_must_exist"] = False
    matlab["formal_figure_must_not_predate_sources"] = False
    matlab["provenance_record"] = None
    matlab["default_output"] = "仅交付同目录qX_plot.m；图窗由用户人工检查和按需导出"

    data["ownership"]["Python"] = "每问仅维护同目录一个问题X求解.py；先输出主工作簿，验收后原位加入结果深化分析并输出第二工作簿"
    data["ownership"]["MATLAB"] = "同目录qX_plot.m精确读取两个标准工作簿，不重新计算核心结果，默认不自动导出图片"
    data["filenames"]["python_scripts"] = "问题X求解/问题X求解.py"
    data["filenames"]["matlab_scripts"] = "问题X求解/q1_plot.m、q2_plot.m等ASCII固定名称"
    data["optional_metadata"] = {
        "default_generation": "forbidden",
        "explicit_request_only": ["run_info.json", "result_manifest.yaml", "matlab_figure_handoff.json"],
        "rule": "不得放入问题X求解目录；仅在用户明确要求完整复现包时放入项目内部元数据目录",
    }
    data["rules"] = [
        "新项目每问只创建一个问题X求解目录，默认恰好包含一个Python脚本、两个Excel工作簿和一个qX_plot.m。",
        "主工作簿验收后在同一个问题X求解.py中加入结果深化分析阶段，不生成问题X结果深化分析.py。",
        "默认不生成独立完整运行配置、运行说明、code_delivery_report、user_execution_validation_report、figure_evidence或图表子目录。",
        "正式代码交付必须通过validate_code_delivery且不得执行赛题代码；校验结果在聊天或标准输出中返回，不额外落盘。",
        "用户返回工作簿必须先通过validate_user_execution；代码交付本身不得把状态提升为solved或analyzed。",
        "同步器只做发现、校验、哈希和stale传播，不替代主求解质量门与结果深化分析。",
        "旧结果数据表/问题X/与独立结果深化分析脚本仅作只读兼容，新项目不得继续生成。",
        "Excel工作簿是默认结果交换格式；CSV仅用于明确兼容需求。",
        "所有工作表必须非空；不生成不适用分析的占位工作表。",
    ]
    dump_yaml(path, data)


def update_user_execution_contract() -> None:
    data = {
        "version": "1.1.0",
        "skill_version": VERSION,
        "purpose": "定义用户本地完整版数值执行链，同时保持每问一个自包含目录和一个持续更新的Python脚本。",
        "default_mode": {
            "execution_owner": "user",
            "execution_profile": "full_fidelity",
            "assistant_runs_task_specific_code": False,
            "local_pipeline_remains_runnable_by_user": True,
        },
        "assistant_policy": {
            "prohibited": [
                "运行、导入或通过subprocess/runpy/notebook执行问题X求解/问题X求解.py",
                "为节省时间自动缩减数据、网格、时域、场景、重复次数、随机种子、迭代次数或容差",
                "在完整版失败后静默切换轻量模型、替代求解器、粗粒度近似或演示结果",
                "用户未返回工作簿前声称已求解、已分析或已得到正式数值",
            ],
            "allowed": [
                "审题、模型设计、公式闭环和完整版代码生成",
                "不导入求解脚本的静态代码、依赖和语法检查",
                "读取用户返回的工作簿并执行Schema、哈希、质量门和证据一致性校验",
                "运行本Skill仓库自身的lint、单元测试、索引生成和LaTeX模板CI",
            ],
        },
        "full_fidelity_flags": {
            "execution_profile": "full_fidelity",
            "allow_reduced_data": False,
            "allow_coarser_grid": False,
            "allow_shorter_horizon": False,
            "allow_fewer_repetitions": False,
            "allow_relaxed_tolerance": False,
            "allow_silent_solver_fallback": False,
        },
        "code_delivery": {
            "required_artifacts": ["task_specific_python_code"],
            "single_script": "问题X求解/问题X求解.py",
            "runtime_metadata": "嵌入Python中的FULL_FIDELITY_CONFIG，并写入两个工作簿的运行配置工作表",
            "standalone_files_forbidden_by_default": [
                "问题X完整运行配置.yaml", "问题X本地运行说明.md", "code_delivery_report.yaml",
                "问题X结果深化分析.py", "问题X结果深化完整运行配置.yaml", "问题X结果深化本地运行说明.md",
            ],
            "required_config_fields": [
                "execution_owner", "execution_profile", "stage", "problem_name", "data_paths", "data_sha256",
                "solver", "solver_version", "random_seed", "tolerance", "iteration_or_time_limit",
                "expected_workbook", "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
                "allow_fewer_repetitions", "allow_relaxed_tolerance", "allow_silent_solver_fallback",
            ],
            "no_placeholder_markers": ["TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError"],
        },
        "single_script_update_policy": {
            "primary": "首次交付问题X求解.py，仅运行主求解并输出问题X求解结果.xlsx",
            "analysis": "主工作簿验收后覆盖更新同一个问题X求解.py，加入结果深化分析入口并输出第二工作簿",
            "forbidden": "不得另建问题X结果深化分析.py",
        },
        "execution_states": {
            "primary": ["pending", "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected"],
            "analysis": ["pending", "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected", "redo_required"],
            "rules": [
                "代码交付不得把小问status提升为solved或analyzed。",
                "primary_execution_status=accepted且主结果质量门通过后，status才可进入solved。",
                "analysis_execution_status=accepted且结论稳定性校验通过后，status才可进入analyzed。",
                "主工作簿未验收前不得写入最终结果深化分析实现；只能形成候选分析方向。",
            ],
        },
        "returned_workbook": {
            "required_sheet": "运行配置",
            "required_columns": ["项目", "值"],
            "required_items": [
                "execution_owner", "execution_profile", "stage", "problem_name", "code_sha256", "data_sha256",
                "solver", "solver_version", "tolerance", "iteration_or_time_limit", "actual_stop_reason",
                "random_seed", "repetitions_or_scenarios", "grid_or_time_range", "fallback_used", "platform",
                "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon", "allow_fewer_repetitions",
                "allow_relaxed_tolerance", "allow_silent_solver_fallback",
            ],
            "acceptance_rules": [
                "execution_owner必须为user。", "execution_profile必须为full_fidelity。",
                "所有缩减、放宽和静默回退标志必须为false。", "fallback_used必须为false。",
                "code_sha256必须与对应阶段已交付的同一Python脚本版本完全一致。",
                "data_sha256必须与代码交付时锁定的数据哈希完全一致。",
                "主结果工作簿必须通过主结果质量门，结果深化分析工作簿必须包含分析设计和结论稳定性汇总。",
            ],
        },
        "filenames": {
            "question_directory": "问题X求解/",
            "python_code": "问题X求解/问题X求解.py",
            "primary_workbook": "问题X求解/问题X求解结果.xlsx",
            "analysis_workbook": "问题X求解/问题X结果深化分析.xlsx",
            "matlab_script": "问题X求解/qX_plot.m",
            "legacy_result_directory": "结果数据表/问题X/",
            "legacy_analysis_code": "问题X结果深化分析.py",
            "validation_reports": "仅在聊天或标准输出返回，不写入用户项目",
        },
    }
    dump_yaml("core/user_execution_contract.yaml", data)


def update_manifest() -> None:
    path = "core/module_manifest.yaml"
    data = yaml.safe_load(read(path))
    data["version"] = VERSION
    catalog = data["artifact_catalog"]
    catalog["python_code"] = "问题X求解目录中的唯一Python脚本；先交付主求解版本，验收后原位更新结果深化分析阶段"
    catalog["result_analysis_code"] = "对同一个问题X求解.py的结果深化分析更新，不生成第二个Python文件"
    catalog["full_run_config"] = "嵌入Python和工作簸运行配置表的完整精度参数，不单独落盘"
    catalog["execution_instructions"] = "聊天内给出的本地运行步骤，不单独落盘"
    catalog["code_delivery_report"] = "聊天或标准输出中的静态交付检查结果，不单独落盘"
    catalog["figure_evidence"] = "由同目录两个工作簿与qX_plot.m形成的逻辑证据，不默认生成独立文件"
    data["utility_gates"]["code_delivery"]["inputs"] = ["existing_project_state", "existing_model_paper_framework", "python_code"]
    dump_yaml(path, data)


def update_result_io() -> None:
    path = "templates/code/hsk_pipeline/result_io.py"
    text = read(path)
    text = text.replace(
        'PROBLEM_PATTERN = re.compile(r"问题[一二三四五六七八九十百]+")',
        'PROBLEM_PATTERN = re.compile(r"问题[一二三四五六七八九十百]+")\nQUESTION_DIR_PATTERN = re.compile(r"问题[一二三四五六七八九十百]+求解")',
    )
    text = re.sub(
        r"def find_project_root\(start: Path\) -> Path:\n.*?\n\ndef result_data_dir",
        '''def find_project_root(start: Path) -> Path:\n    start = Path(start).resolve()\n    current = start.parent if start.is_file() else start\n    if QUESTION_DIR_PATTERN.fullmatch(current.name):\n        return current.parent\n    for candidate in (current, *current.parents):\n        if (candidate / \"模型论文框架.md\").is_file() or (candidate / \"state\" / \"project_state.yaml\").is_file():\n            return candidate\n        if candidate.name == \"结果数据表\":\n            return candidate.parent\n        if candidate.parent.name == \"结果数据表\" and PROBLEM_PATTERN.fullmatch(candidate.name):\n            return candidate.parent.parent\n    return start.parent if start.is_file() else current\n\n\ndef result_data_dir''',
        text,
        flags=re.S,
    )
    text = re.sub(
        r"def result_data_dir\(project_root: Path, problem_name: str\) -> Path:\n.*?\n\ndef figure_dir",
        '''def result_data_dir(project_root: Path, problem_name: str) -> Path:\n    if not PROBLEM_PATTERN.fullmatch(problem_name):\n        raise ValueError(\"problem_name 应为问题一、问题二等中文名称\")\n    path = Path(project_root) / f\"{problem_name}求解\"\n    path.mkdir(parents=True, exist_ok=True)\n    return path\n\n\ndef legacy_result_data_dir(project_root: Path, problem_name: str) -> Path:\n    return Path(project_root) / \"结果数据表\" / problem_name\n\n\ndef figure_dir''',
        text,
        flags=re.S,
    )
    text = re.sub(
        r"def figure_dir\(project_root: Path, problem_name: str\) -> Path:\n.*?\n\ndef workbook_paths",
        '''def figure_dir(project_root: Path, problem_name: str) -> Path:\n    # v6.6.0默认不创建图表子目录；MATLAB脚本只打开图窗，用户按需导出。\n    return result_data_dir(project_root, problem_name)\n\n\ndef workbook_paths''',
        text,
        flags=re.S,
    )
    write(path, text)


def update_validate_code_delivery() -> None:
    content = '''#!/usr/bin/env python3\n"""静态校验每问唯一Python脚本，不运行赛题代码，也不生成额外报告文件。"""\nfrom __future__ import annotations\n\nimport argparse\nimport ast\nimport hashlib\nfrom pathlib import Path\nfrom typing import Any\n\nimport yaml\n\nFALSE_FLAGS = (\n    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",\n    "allow_fewer_repetitions", "allow_relaxed_tolerance",\n    "allow_silent_solver_fallback",\n)\nPLACEHOLDERS = ("TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError")\nCONFIG_NAMES = {"FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG", "RUN_CONFIG"}\nREQUIRED_FIELDS = {\n    "execution_owner", "execution_profile", "stage", "problem_name", "data_paths",\n    "data_sha256", "solver", "solver_version", "random_seed", "tolerance",\n    "iteration_or_time_limit", "expected_workbook", *FALSE_FLAGS,\n}\n\n\ndef load_yaml(path: Path) -> dict[str, Any]:\n    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}\n\n\ndef sha256(path: Path) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef is_sha256(value: Any) -> bool:\n    text = str(value).strip().lower()\n    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)\n\n\ndef embedded_config(text: str) -> dict[str, Any]:\n    tree = ast.parse(text)\n    for node in tree.body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            targets = node.targets if isinstance(node, ast.Assign) else [node.target]\n            if any(isinstance(target, ast.Name) and target.id in CONFIG_NAMES for target in targets):\n                value = ast.literal_eval(node.value)\n                if not isinstance(value, dict):\n                    raise ValueError("FULL_FIDELITY_CONFIG必须为字典常量")\n                return value\n    raise ValueError("缺少FULL_FIDELITY_CONFIG字典常量")\n\n\ndef problem_from_path(script: Path) -> str:\n    folder = script.parent.name\n    if not folder.endswith("求解"):\n        raise ValueError("Python脚本必须位于问题X求解目录")\n    problem = folder.removesuffix("求解")\n    if script.name != f"{problem}求解.py":\n        raise ValueError(f"脚本名必须为{problem}求解.py")\n    return problem\n\n\ndef validate_script(project_root: Path, script: Path, expected_stage: str | None = None) -> tuple[list[str], dict[str, Any]]:\n    issues: list[str] = []\n    try:\n        problem = problem_from_path(script)\n    except ValueError as exc:\n        return [str(exc)], {}\n    text = script.read_text(encoding="utf-8", errors="strict")\n    for marker in PLACEHOLDERS:\n        if marker in text:\n            issues.append(f"正式代码仍含占位标记: {marker}")\n    if "if __name__ == \"__main__\":" not in text and "if __name__ == '__main__':" not in text:\n        issues.append("正式代码缺少main入口")\n    try:\n        config = embedded_config(text)\n    except (SyntaxError, ValueError) as exc:\n        issues.append(str(exc))\n        config = {}\n    for field in sorted(REQUIRED_FIELDS):\n        if field not in config or config[field] in (None, "", []):\n            issues.append(f"嵌入运行配置缺少字段: {field}")\n    stage = str(config.get("stage", ""))\n    if stage not in {"primary", "analysis"}:\n        issues.append("stage必须为primary或analysis")\n    if expected_stage and stage != expected_stage:\n        issues.append(f"stage应为{expected_stage}")\n    if config.get("problem_name") != problem:\n        issues.append("problem_name与目录名不一致")\n    if config.get("execution_owner") != "user":\n        issues.append("execution_owner必须为user")\n    if config.get("execution_profile") != "full_fidelity":\n        issues.append("execution_profile必须为full_fidelity")\n    for flag in FALSE_FLAGS:\n        if config.get(flag) is not False:\n            issues.append(f"{flag}必须显式为false")\n    if not is_sha256(config.get("data_sha256")):\n        issues.append("data_sha256必须是64位十六进制SHA-256")\n    expected = f"{problem}求解结果.xlsx" if stage == "primary" else f"{problem}结果深化分析.xlsx"\n    if Path(str(config.get("expected_workbook", ""))).name != expected:\n        issues.append(f"expected_workbook必须指向同目录{expected}")\n    return issues, config\n\n\ndef update_state(project_root: Path, config: dict[str, Any], script: Path) -> None:\n    state_path = project_root / "state" / "project_state.yaml"\n    if not state_path.is_file():\n        return\n    state = load_yaml(state_path)\n    problem = str(config["problem_name"])\n    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]\n    suffix = problem.removeprefix("问题")\n    key = f"Q{order.index(suffix) + 1}" if suffix in order else problem\n    entry = state.setdefault("subproblems", {}).setdefault(key, {})\n    relative = script.relative_to(project_root).as_posix()\n    stage = str(config["stage"])\n    entry["data_hash"] = str(config["data_sha256"]).lower()\n    entry["code"] = relative\n    if stage == "primary":\n        entry["primary_code_sha256"] = sha256(script)\n        entry["primary_execution_status"] = "awaiting_user_execution"\n        entry.setdefault("analysis_execution_status", "pending")\n    else:\n        if entry.get("primary_execution_status") != "accepted":\n            raise ValueError("主工作簿未accepted，禁止写入最终结果深化分析实现")\n        entry["analysis_code_sha256"] = sha256(script)\n        entry["analysis_execution_status"] = "awaiting_user_execution"\n    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")\n\n\ndef discover_scripts(root: Path) -> list[Path]:\n    return sorted(root.glob("问题*求解/问题*求解.py"))\n\n\ndef main() -> int:\n    parser = argparse.ArgumentParser()\n    parser.add_argument("project_root", type=Path)\n    parser.add_argument("--script", type=Path)\n    parser.add_argument("--stage", choices=("primary", "analysis"))\n    parser.add_argument("--write", action="store_true")\n    parser.add_argument("--strict", action="store_true")\n    args = parser.parse_args()\n    root = args.project_root.resolve()\n    scripts = [args.script if args.script and args.script.is_absolute() else root / args.script] if args.script else discover_scripts(root)\n    issues: list[str] = []\n    checked: list[str] = []\n    for script in scripts:\n        item_issues, config = validate_script(root, script, args.stage)\n        issues.extend(f"{script.name}: {item}" for item in item_issues)\n        checked.append(script.relative_to(root).as_posix())\n        if args.write and not item_issues:\n            try:\n                update_state(root, config, script)\n            except ValueError as exc:\n                issues.append(f"{script.name}: {exc}")\n    report = {\n        "status": "passed" if not issues else "failed",\n        "checked_scripts": checked,\n        "issues": issues,\n        "task_code_executed": False,\n        "report_persisted": False,\n    }\n    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())\n    return 1 if issues and args.strict else 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'''
    write("scripts/validate_code_delivery.py", content)


def update_validate_user_execution() -> None:
    path = "scripts/validate_user_execution.py"
    text = read(path)
    text = re.sub(
        r"def discover\(root: Path\) -> list\[Path\]:\n.*?\n\ndef main",
        '''def discover(root: Path) -> list[Path]:\n    current_patterns = (\n        "问题*求解/问题*求解结果.xlsx",\n        "问题*求解/问题*结果深化分析.xlsx",\n    )\n    legacy_patterns = (\n        "结果数据表/问题*/问题*求解结果.xlsx",\n        "结果数据表/问题*/问题*结果深化分析.xlsx",\n    )\n    return sorted({\n        path.resolve()\n        for pattern in (*current_patterns, *legacy_patterns)\n        for path in root.glob(pattern)\n    })\n\n\ndef main''',
        text,
        flags=re.S,
    )
    text = text.replace(
        '    (root / "user_execution_validation_report.yaml").write_text(\n        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"\n    )\n',
        '    report["report_persisted"] = False\n    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())\n',
    )
    text = text.replace('    print("user-produced workbooks accepted without executing task code")\n', '')
    write(path, text)


def update_sync_project() -> None:
    path = "scripts/sync_project.py"
    text = read(path)
    helper = '''\n\ndef _question_dir(root: Path, chinese_name: str) -> Path:\n    current = root / f"{chinese_name}求解"\n    if current.is_dir():\n        return current\n    return root / "结果数据表" / chinese_name\n'''
    text = text.replace('\ndef _question_names(root: Path, state: Mapping[str, Any]) -> list[str]:', helper + '\n\ndef _question_names(root: Path, state: Mapping[str, Any]) -> list[str]:', 1)
    text = re.sub(
        r"def _question_names\(root: Path, state: Mapping\[str, Any\]\) -> list\[str\]:\n.*?\n\ndef _python_files",
        '''def _question_names(root: Path, state: Mapping[str, Any]) -> list[str]:\n    names = {chinese_question_name(str(key)) for key in (state.get("subproblems") or {})}\n    names.update(\n        path.name.removesuffix("求解")\n        for path in root.glob("问题*求解")\n        if path.is_dir() and QUESTION_RE.fullmatch(path.name.removesuffix("求解"))\n    )\n    result_root = root / "结果数据表"\n    if result_root.is_dir():\n        names.update(\n            path.name for path in result_root.iterdir()\n            if path.is_dir() and QUESTION_RE.fullmatch(path.name)\n        )\n    return sorted(names, key=lambda value: question_number(value) or 999)\n\n\ndef _python_files''',
        text,
        flags=re.S,
    )
    text = re.sub(
        r"def _python_files\(root: Path, chinese_name: str\) -> list\[Path\]:\n.*?\n\ndef _analysis_path",
        '''def _python_files(root: Path, chinese_name: str) -> list[Path]:\n    current = root / f"{chinese_name}求解" / f"{chinese_name}求解.py"\n    if current.is_file():\n        return [current]\n    legacy = [\n        root / f"{chinese_name}求解.py",\n        root / f"{chinese_name}结果深化分析.py",\n    ]\n    return [path for path in legacy if path.is_file()]\n\n\ndef _analysis_path''',
        text,
        flags=re.S,
    )
    text = re.sub(
        r"def _figure_files\(result_dir: Path\) -> list\[Path\]:\n.*?\n\ndef _validate_workbook",
        '''def _figure_files(result_dir: Path) -> list[Path]:\n    directories = [result_dir, result_dir / "图表"]\n    return sorted(\n        {path for directory in directories if directory.is_dir() for path in directory.iterdir()\n         if path.is_file() and path.suffix.lower() in FIGURE_SUFFIXES},\n        key=lambda item: item.as_posix(),\n    )\n\n\ndef _validate_workbook''',
        text,
        flags=re.S,
    )
    text = text.replace('    result_dir = root / "结果数据表" / chinese_name\n', '    result_dir = _question_dir(root, chinese_name)\n', 1)
    text = text.replace('        if not figures:\n            issues.append("图表交付缺少正式结果图")\n', '')
    text = text.replace('    evidence = root / "结果数据表" / str(snapshot["chinese_name"]) / "figure_evidence.yaml"\n', '    evidence = _question_dir(root, str(snapshot["chinese_name"])) / "figure_evidence.yaml"\n')
    text = re.sub(
        r"def _write_figure_evidence\(root: Path, snapshot: Mapping\[str, Any\]\) -> str \| None:\n.*?\n\ndef _replace_or_prepend",
        '''def _write_figure_evidence(root: Path, snapshot: Mapping[str, Any]) -> str | None:\n    # v6.6.0默认不生成额外figure_evidence文件。\n    return None\n\n\ndef _replace_or_prepend''',
        text,
        flags=re.S,
    )
    write(path, text)


def update_matlab_template() -> None:
    path = "templates/matlab/q1_plot.m"
    text = read(path)
    text = text.replace('% 放在“结果数据表/问题一/”，生成正式脚本前必须读取实际工作簿并替换全部占位符。', '% 放在“问题一求解/”，与唯一Python脚本和两个标准工作簿同目录。')
    text = text.replace('figureDir = fullfile(resultDir, "图表");\nEXPORT_FIGURES = false;\n', '')
    text = re.sub(
        r"\n%% 4\. 人工调整后按需导出\nif EXPORT_FIGURES\n.*?\nend\n\nfunction column",
        '\n%% 4. 图窗保留供人工检查；本脚本默认不自动导出文件\n\nfunction column',
        text,
        flags=re.S,
    )
    write(path, text)


def update_docs() -> None:
    solve_module = '''# Module 03A：每问唯一Python脚本的主求解交付\n\n本模块在 `问题X求解/` 中生成唯一的 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。\n\n## 主链\n\n```text\n锁定模型\n→ 创建问题X求解/问题X求解.py\n→ 用户本地完整运行\n→ 同目录问题X求解结果.xlsx\n→ 验收运行配置与主结果质量门\n```\n\n脚本必须包含数据检查、模型、求解器状态、容差、停止条件、约束/残差、收敛或外样本检查、随机种子和中文工作簿输出。完整运行配置嵌入 `FULL_FIDELITY_CONFIG`，并写入工作簿的 `运行配置` 表；不生成独立 YAML、运行说明或报告文件。\n\n主工作簿通过 `validate_user_execution.py` 验收后，才允许在原 `问题X求解.py` 中加入结果深化分析阶段。\n'''
    analysis_module = '''# Module 03B：在同一Python脚本中加入结果深化分析\n\n本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。\n\n## 更新规则\n\n```text\n主工作簿accepted\n→ 建立result_analysis_plan\n→ 覆盖更新问题X求解/问题X求解.py\n→ 用户本地运行analysis阶段\n→ 同目录问题X结果深化分析.xlsx\n→ 验收后进入analyzed或redo_required\n```\n\n不得另建 `问题X结果深化分析.py`，不得生成独立运行配置、运行说明或校验报告。若核心结论未保持，必须回退模型设计或主求解并标记下游 stale。\n'''
    write("modules/03_solve_validate.md", solve_module)
    write("modules/03_result_analysis.md", analysis_module)

    figure = read("modules/04_figure_evidence.md")
    figure = figure.replace('锁定 `问题X求解结果.xlsx` 与 `问题X结果深化分析.xlsx`；', '锁定 `问题X求解/` 中的两个标准工作簿；')
    figure = figure.replace('将 `q{x}_plot.m` 与两类工作簿放在同一问题目录；', '将 `q{x}_plot.m` 与唯一Python脚本、两类工作簿放在同一 `问题X求解/` 目录；')
    figure = figure.replace('正式交付前运行项目同步器。', '默认只交付 `q{x}_plot.m`，保留图窗供人工检查，不自动创建图表子目录或导出图片。')
    figure = figure.replace('图后另起正文段解释趋势、关键数值、机制、稳定范围或失效边界。无法绑定小问、公式、工作簿、工作表、真实表头、MATLAB 脚本、`模型论文框架.md` 映射或正文结论的图删除。', '图后另起正文段解释趋势、关键数值、机制、稳定范围或失效边界。正式图片在进入LaTeX时按需人工导出；求解阶段不额外生成图片文件。')
    write("modules/04_figure_evidence.md", figure)

    code_pack = '''# Artifact Pack：每问自包含求解目录\n\n每问的新项目默认只建立：\n\n```text\n问题X求解/\n├─ 问题X求解.py\n├─ 问题X求解结果.xlsx\n├─ 问题X结果深化分析.xlsx\n└─ qX_plot.m\n```\n\n`问题X求解.py` 是唯一Python文件：首次版本完成主求解；主工作簿验收后覆盖更新同一文件，加入结果深化分析阶段。完整运行配置嵌入代码并写入工作簿，不生成独立 YAML、MD 或校验报告。\n\nMATLAB 只读取同目录两个真实工作簿，精确匹配表头，不重新计算核心结果，默认只保留图窗和 `qX_plot.m`。旧 `结果数据表/问题X/` 与独立分析脚本仅作只读兼容。\n'''
    write("packs/artifact/code.md", code_pack)

    submission = read("packs/artifact/full_submission.md")
    submission = submission.replace('赛题、附件说明和各问 Python 脚本；', '赛题、附件说明和每问 `问题X求解/问题X求解.py`；')
    submission = submission.replace('每问 `问题X求解结果.xlsx`；\n- 每问 `问题X结果深化分析.xlsx`；\n- 同目录 `q{x}_plot.m`；\n- `图表/` 中的正式结果图；', '每问 `问题X求解/` 中的两个标准工作簿；\n- 同目录 `q{x}_plot.m`；\n- LaTeX阶段按需人工导出的正式结果图；')
    submission = submission.replace('不得为提交包额外复制出 `Python求解/`、`MATLAB绘图/` 或 `问题X结果数据/` 重复目录。', '不得创建 `结果数据表/`、`Python求解/`、`MATLAB绘图/` 或独立结果深化脚本；每问仅保留一个 `问题X求解/` 目录。')
    write("packs/artifact/full_submission.md", submission)

    for path in ("SKILL.md", "README.md", "PROJECT_INSTRUCTIONS.md", "RUNTIME_ROUTER.md", "AGENTS.md"):
        text = read(path)
        text = text.replace('结果数据表/问题一/', '问题一求解/')
        text = text.replace('结果数据表/问题X/', '问题X求解/')
        text = text.replace('问题X结果深化分析.py', '原位更新问题X求解.py')
        text = text.replace('完整运行配置和本地说明', '嵌入式完整运行配置和聊天内运行说明')
        write(path, text)

    nested = read("skills/mathmodel-skill/SKILL.md")
    nested = nested.replace('读取 `core/bootstrap.yaml`', '先定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`')
    nested = nested.replace('使用 `scripts/resolve_workflow.py`', '使用 `../../scripts/resolve_workflow.py`')
    write("skills/mathmodel-skill/SKILL.md", nested)

    replace("modules/05_latex_compile_quality.md", "# LaTeX 编译质量规范 v6.2.3", "# Module 05D：LaTeX 编译质量检查")


def update_tests() -> None:
    path = "tests/test_result_io.py"
    text = read(path)
    text = text.replace('"结果数据表/问题一/问题一求解结果.xlsx"', '"问题一求解/问题一求解结果.xlsx"')
    text = text.replace('"结果数据表/问题一/问题一结果深化分析.xlsx"', '"问题一求解/问题一结果深化分析.xlsx"')
    text = text.replace('script = Path(directory) / "问题一求解.py"\n            script.write_text("", encoding="utf-8")\n            self.assertEqual(MOD.find_project_root(script), Path(directory))', 'folder = Path(directory) / "问题一求解"\n            folder.mkdir()\n            script = folder / "问题一求解.py"\n            script.write_text("", encoding="utf-8")\n            self.assertEqual(MOD.find_project_root(script), Path(directory))')
    write(path, text)

    user_test = '''from __future__ import annotations\n\nimport hashlib\nimport importlib.util\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nimport openpyxl\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\nFALSE_FLAGS = (\n    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",\n    "allow_fewer_repetitions", "allow_relaxed_tolerance",\n    "allow_silent_solver_fallback",\n)\n\n\ndef load_module(name: str, path: Path):\n    spec = importlib.util.spec_from_file_location(name, path)\n    module = importlib.util.module_from_spec(spec)\n    assert spec.loader is not None\n    spec.loader.exec_module(module)\n    return module\n\n\nCODE = load_module("validate_code_delivery", ROOT / "scripts" / "validate_code_delivery.py")\nRECEIPT = load_module("validate_user_execution", ROOT / "scripts" / "validate_user_execution.py")\n\n\nclass UserExecutionContractTests(unittest.TestCase):\n    def make_project(self, root: Path) -> Path:\n        (root / "state").mkdir()\n        folder = root / "问题一求解"\n        folder.mkdir()\n        code = folder / "问题一求解.py"\n        config = {\n            "execution_owner": "user", "execution_profile": "full_fidelity", "stage": "primary",\n            "problem_name": "问题一", "data_paths": ["data.csv"], "data_sha256": "a" * 64,\n            "solver": "test", "solver_version": "1", "random_seed": 2026, "tolerance": 1e-8,\n            "iteration_or_time_limit": "full", "expected_workbook": "问题一求解结果.xlsx",\n            **{flag: False for flag in FALSE_FLAGS},\n        }\n        code.write_text(\n            "FULL_FIDELITY_CONFIG = " + repr(config) + "\\n\\ndef main():\\n    return 0\\n\\nif __name__ == \\\"__main__\\\":\\n    raise SystemExit(main())\\n",\n            encoding="utf-8",\n        )\n        state = {\n            "project": {"competition": "test", "problem": "A", "current_phase": "solve_validate"},\n            "requirements": {"total": 0, "completed": [], "pending": []}, "decisions": {},\n            "subproblems": {"Q1": {"status": "designed", "selected_model": "m", "capabilities": {},\n                "result_quality_status": "pending", "result_analysis_status": "pending",\n                "framework_section": "Q1", "result_summary_status": "pending"}},\n            "variables": {"locked": [], "source": {}},\n            "paper_framework": {"path": "模型论文框架.md", "version": "1", "sync_status": "stale",\n                "last_sync_scope": "design", "proposition_limit": 4, "proposition_count": 0,\n                "proposition_status": "not_assessed", "propositions": []},\n            "artifacts": {"code": [], "results": [], "figures": [], "papers": []},\n            "risks": [], "next_gate": {"module": "solve_validate", "condition": "code"},\n        }\n        (root / "state" / "project_state.yaml").write_text(\n            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"\n        )\n        return code\n\n    def make_primary_workbook(self, root: Path, code: Path, data_hash: str = "a" * 64) -> Path:\n        workbook = root / "问题一求解" / "问题一求解结果.xlsx"\n        book = openpyxl.Workbook()\n        sheet = book.active\n        sheet.title = "运行配置"\n        sheet.append(["项目", "值"])\n        items = {\n            "execution_owner": "user", "execution_profile": "full_fidelity", "stage": "primary",\n            "problem_name": "问题一", "code_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),\n            "data_sha256": data_hash, "solver": "test", "solver_version": "1", "tolerance": 1e-8,\n            "iteration_or_time_limit": "full", "actual_stop_reason": "optimal", "random_seed": 2026,\n            "repetitions_or_scenarios": 100, "grid_or_time_range": "full", "fallback_used": False,\n            "platform": "test", **{flag: False for flag in FALSE_FLAGS},\n        }\n        for key, value in items.items():\n            sheet.append([key, value])\n        quality = book.create_sheet("主结果质量门")\n        quality.append(["检查项", "是否通过", "证据"])\n        quality.append(["完整运行", True, "ok"])\n        book.save(workbook)\n        return workbook\n\n    def test_code_delivery_does_not_mark_solved(self):\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            code = self.make_project(root)\n            issues, config = CODE.validate_script(root, code, "primary")\n            self.assertEqual(issues, [])\n            CODE.update_state(root, config, code)\n            state = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))\n            self.assertEqual(state["subproblems"]["Q1"]["status"], "designed")\n            self.assertEqual(state["subproblems"]["Q1"]["primary_execution_status"], "awaiting_user_execution")\n            self.assertEqual(state["subproblems"]["Q1"]["data_hash"], "a" * 64)\n\n    def test_reduced_flag_is_rejected(self):\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            code = self.make_project(root)\n            text = code.read_text(encoding="utf-8").replace("'allow_reduced_data': False", "'allow_reduced_data': True")\n            code.write_text(text, encoding="utf-8")\n            issues, _ = CODE.validate_script(root, code, "primary")\n            self.assertTrue(any("allow_reduced_data" in item for item in issues))\n\n    def test_primary_workbook_acceptance_marks_solved(self):\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            code = self.make_project(root)\n            issues, config = CODE.validate_script(root, code, "primary")\n            self.assertEqual(issues, [])\n            CODE.update_state(root, config, code)\n            workbook = self.make_primary_workbook(root, code)\n            state = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))\n            issues = RECEIPT.validate_one(root, workbook, state, True)\n            self.assertEqual(issues, [])\n            self.assertEqual(state["subproblems"]["Q1"]["status"], "solved")\n\n    def test_data_hash_mismatch_is_rejected(self):\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            code = self.make_project(root)\n            _, config = CODE.validate_script(root, code, "primary")\n            CODE.update_state(root, config, code)\n            workbook = self.make_primary_workbook(root, code, data_hash="b" * 64)\n            state = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))\n            issues = RECEIPT.validate_one(root, workbook, state, True)\n            self.assertTrue(any("data_sha256" in item for item in issues))\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
    write("tests/test_user_execution_contract.py", user_test)

    for path in ("tests/test_sync_project.py", "tests/test_split_pipeline_runtime.py", "tests/test_v633_gate_hardening.py"):
        text = read(path)
        text = text.replace('root / "结果数据表" / "问题一"', 'root / "问题一求解"')
        text = text.replace('project / "结果数据表" / "问题一"', 'project / "问题一求解"')
        text = text.replace('"结果数据表/问题一/', '"问题一求解/')
        text = text.replace('结果数据表/问题一/', '问题一求解/')
        write(path, text)

    new_test = '''import importlib.util\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef load_sync():\n    spec = importlib.util.spec_from_file_location("sync_project_v660", ROOT / "scripts/sync_project.py")\n    module = importlib.util.module_from_spec(spec)\n    assert spec.loader is not None\n    spec.loader.exec_module(module)\n    return module\n\n\nclass TestV660SelfContainedQuestionFolder(unittest.TestCase):\n    def test_output_contract_has_exact_four_default_files(self):\n        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))\n        per_question = data["per_question"]\n        self.assertEqual(per_question["question_directory"], "问题{中文序号}求解/")\n        self.assertEqual(len(per_question["exact_default_files"]), 4)\n        self.assertTrue(per_question["no_auxiliary_files_by_default"])\n\n    def test_user_contract_forbids_standalone_auxiliary_files(self):\n        data = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))\n        forbidden = set(data["code_delivery"]["standalone_files_forbidden_by_default"])\n        self.assertIn("问题X结果深化分析.py", forbidden)\n        self.assertEqual(data["filenames"]["python_code"], "问题X求解/问题X求解.py")\n\n    def test_sync_python_discovery_is_question_specific(self):\n        sync = load_sync()\n        import tempfile\n        with tempfile.TemporaryDirectory() as temp:\n            root = Path(temp)\n            for problem in ("问题一", "问题二"):\n                folder = root / f"{problem}求解"\n                folder.mkdir()\n                (folder / f"{problem}求解.py").write_text("", encoding="utf-8")\n            files = sync._python_files(root, "问题一")\n            self.assertEqual([path.name for path in files], ["问题一求解.py"])\n\n    def test_nested_plugin_paths_resolve(self):\n        skill_dir = ROOT / "skills/mathmodel-skill"\n        self.assertTrue((skill_dir / "../../core/bootstrap.yaml").resolve().is_file())\n        self.assertTrue((skill_dir / "../../scripts/resolve_workflow.py").resolve().is_file())\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
    write("tests/test_v660_self_contained_question_folder.py", new_test)


def main() -> None:
    bump_versions()
    update_output_contract()
    update_user_execution_contract()
    update_manifest()
    update_result_io()
    update_validate_code_delivery()
    update_validate_user_execution()
    update_sync_project()
    update_matlab_template()
    update_docs()
    update_tests()


if __name__ == "__main__":
    main()
