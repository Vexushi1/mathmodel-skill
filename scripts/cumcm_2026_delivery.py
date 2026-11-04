#!/usr/bin/env python3
"""CUMCM 2026 external upload pair, separate from internal submission ZIPs.

Only two files may be uploaded: the standalone PDF and, when required, a
support ZIP containing actual active source/material files. This adapter reads
existing project State and formal LaTeX evidence; it creates no new project
state or substitute approval. Archive membership is checked against the
real appendix, not inferred from directory contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping

import yaml

from audit_latex_project import (
    audit_cumcm_2026_compliance, discover_tex_graph, flatten_tex,
)
from latex_delivery import verify_compile_report
from submission_requirements import latex_artifact_defaults, project_path
import plot_backend as PLOT_BACKEND
import stage_code as STAGE_CODE
import run_config_parser

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE = SKILL_ROOT / "config/competition_profiles.yaml"
PAPER_NAME = "cumcm2026_paper.pdf"
SUPPORT_NAME = "cumcm2026_support.zip"
FORBIDDEN_PARTS = {"state", "submission", ".git", "__pycache__", ".venv", "venv"}
SENSITIVE = (
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"(?:学号|队员姓名|参赛队编号)\s*[:：]?\s*[A-Za-z0-9-]{5,}"),
)
LISTING = re.compile(r"\\lstinputlisting(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
PARTIAL_LISTING = re.compile(r"\\lstinputlisting\s*\[[^\]]*(?:firstline|lastline)[^\]]*\]")


class DeliveryError(ValueError):
    """Official external delivery cannot be verified against current sources."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_yaml(path: Path) -> Mapping[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise DeliveryError(f"无法读取当前证据 {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise DeliveryError(f"文件内容必须为映射: {path}")
    return data


def _inside(root: Path, raw: str, *, support: bool = False) -> Path:
    if Path(raw).is_absolute() or ".." in Path(raw).parts:
        raise DeliveryError(f"禁止绝对或上级路径: {raw}")
    try:
        path = project_path(root, raw)
        rel = path.relative_to(root).parts
    except ValueError as exc:
        raise DeliveryError(str(exc)) from exc
    if support and (not rel or any(part in FORBIDDEN_PARTS for part in rel)):
        raise DeliveryError(f"官方支撑包不能包含内部状态、日志或存档: {raw}")
    if not path.is_file():
        raise DeliveryError(f"当前文件不存在: {raw}")
    return path


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _source_type(source: Mapping[str, Any]) -> str:
    raw = str(source.get("role", "")) + " " + str(source.get("name", ""))
    if "赛题" in raw or "竞赛提供" in raw or "组委会提供" in raw:
        return "problem_attachment"
    if any(token in raw for token in ("独立", "自行", "自采", "公开", "外部", "自主查阅")):
        return "independent"
    return "unclassified"


def _code_selection(root: Path, state: Mapping[str, Any]) -> set[str]:
    """Use the existing accepted solver / 03B / Figure identity only."""
    result: set[str] = set()
    questions = state.get("subproblems") or {}
    if not isinstance(questions, Mapping):
        raise DeliveryError("subproblems 必须为映射")
    plot = PLOT_BACKEND.inspect_plotting(state)
    if plot["issues"]:
        raise DeliveryError("绘图后端身份存在冲突: " + "; ".join(plot["issues"]))
    for key, row in sorted(questions.items()):
        if not isinstance(row, Mapping) or not re.fullmatch(r"Q[1-9]\d*", str(key)):
            raise DeliveryError(f"问题状态非法: {key}")
        n = int(str(key)[1:])
        cn = STAGE_CODE.question_name(str(key))
        for stage, field, status_field in (
            ("primary", "code", "primary_execution_status"),
            ("analysis", "result_analysis_code", "analysis_execution_status"),
        ):
            declared = row.get(field)
            if not declared:
                continue
            if stage == "analysis" and row.get("result_analysis_status") == "not_required":
                raise DeliveryError(f"{key}: 未启用 03B 却登记深化分析代码")
            if row.get(status_field) != "accepted":
                raise DeliveryError(f"{key}: {stage}代码尚未经人工执行验收")
            issues = STAGE_CODE.validate_stage_binding(
                root, row, stage, require_validated=True,
                project_backend=STAGE_CODE.current_project_backend(state, required=True),
            )
            if issues:
                raise DeliveryError(f"{key}: {stage}源码身份不合格: {'; '.join(issues)}")
            ref = _inside(root, str(declared), support=True)
            result.add(_relative(root, ref))
            raw = ref.read_text(encoding="utf-8-sig")
            _, config = run_config_parser.parse_embedded_config(
                raw, messages=run_config_parser.DELIVERY_MESSAGES,
                backend=STAGE_CODE.current_project_backend(state, required=True),
            )
            for record in config.get("code_dependencies", []):
                dep = _inside(root, str(record["path"]), support=True)
                result.add(_relative(root, dep))
        if (row.get("plot_script") or row.get("matlab_script")
                or plot["kind"] == "historical_matlab"):
            ref = PLOT_BACKEND.resolve_question_script(root, state, str(key), cn, n)
            if ref.path.is_file():
                fig = _inside(root, ref.relative, support=True)
                validated = (row.get("validated_artifact_hashes") or {}).get(ref.hash_field)
                if plot["backend"] == "python" and (
                    not isinstance(validated, str) or _sha(fig).lower() != validated.lower()
                ):
                    raise DeliveryError(f"{key}: Python绘图源码未与验收哈希绑定")
                if isinstance(validated, str) and _sha(fig).lower() != validated.lower():
                    raise DeliveryError(f"{key}: 绘图源码变更后尚未重新验收")
                result.add(_relative(root, fig))

    prep = state.get("preprocessing") or {}
    if isinstance(prep, Mapping) and prep.get("decision") == "project_level":
        for field in ("code",):
            if prep.get(field):
                path = _inside(root, str(prep[field]), support=True)
                if prep.get("code_sha256") != _sha(path):
                    raise DeliveryError("项目级数据预处理源码哈希与当前状态不一致")
                result.add(_relative(root, path))
        backend = plot.get("backend")
        if backend in {"python", "matlab"}:
            relative = ("数据预处理/data_process.py" if backend == "python"
                        else "数据预处理/data_process.m")
            path = _inside(root, relative, support=True)
            result.add(_relative(root, path))
    return result


def _profile(state: Mapping[str, Any]) -> Mapping[str, Any]:
    project = state.get("project") or {}
    if not isinstance(project, Mapping) or str(project.get("competition", "")).strip().lower() not in {
        "cumcm", "国赛", "全国大学生数学建模竞赛",
    }:
        raise DeliveryError("仅适用于 CUMCM 正式项目")
    if str(project.get("competition_edition") or "") != "2026":
        raise DeliveryError("必须显式确认项目参赛届次为 2026；不得替旧项目推断年份")
    rules = _read_yaml(PROFILE)["profiles"]["cumcm"]["edition_rules"]
    if (rules.get("edition") != "2026" or rules.get("verification_status") != "verified"
            or not rules.get("source") or not rules.get("ai_rule_source") or not rules.get("verified_at")):
        raise DeliveryError("2026 竞赛规则当前性未经核验")
    return rules


def _scan_personal_data(text: str, label: str) -> None:
    if any(pattern.search(text) for pattern in SENSITIVE):
        raise DeliveryError(f"{label} 包含疑似身份/联系方式，需人工删改后重新验收")


def _appendix_and_ai(main: Path, state: Mapping[str, Any]) -> tuple[str, bool]:
    files, findings = discover_tex_graph(main)
    if any(item.severity == "blocking" for item in findings):
        raise DeliveryError("无法解析当前 LaTeX 源文件: " + "; ".join(x.message for x in findings))
    flattened = flatten_tex(main, files)
    failures = audit_cumcm_2026_compliance(main, flattened)
    if failures:
        raise DeliveryError("2026 正式论文结构不合格: " + "; ".join(x.message for x in failures))
    appendix = flattened.split(r"\section*{附录}", 1)[1].split(r"\end{appendices}", 1)[0]
    declaration = flattened.split(r"\section*{AI工具使用声明}", 1)[1].split(r"\printbibliography", 1)[0]
    used = ("本参赛队在竞赛过程中使用了AI工具" in
            re.sub(r"\s+", "", declaration))
    _scan_personal_data(flattened, "论文 LaTeX")
    return appendix, used


def prepare(root: Path, *, extra_files: tuple[str, ...], anonymous_confirmed: bool,
            formal: bool = True) -> dict[str, Any]:
    """Derive exact external upload requirements; never scan all project files."""
    root = root.resolve()
    state = _read_yaml(root / "state/project_state.yaml")
    rules = _profile(state)
    if not anonymous_confirmed:
        raise DeliveryError("正式外部上传前必须由参赛队人工确认 PDF 和全部支撑文件匿名")
    source, pdf_name, report_name = latex_artifact_defaults(state)
    main = _inside(root, source)
    pdf = _inside(root, pdf_name)
    report_path = _inside(root, report_name)
    if main.suffix.lower() != ".tex" or pdf.suffix.lower() != ".pdf":
        raise DeliveryError("A2 目前使用现有 LaTeX/PDF 正式证据，不接受未经证明的 DOCX 转 PDF")
    if formal:
        issues = verify_compile_report(
            project=root, main=main, pdf=pdf, report=_read_yaml(report_path))
        if issues:
            raise DeliveryError("当前 PDF 编译证明失效: " + "; ".join(issues))
    if not pdf.read_bytes().startswith(b"%PDF-"):
        raise DeliveryError("正式论文不是有效 PDF 文件头")
    if pdf.stat().st_size > int(rules["paper"]["max_paper_mb"]) * 1024 * 1024:
        raise DeliveryError("论文 PDF 超过 20MB")
    active_main = "\n".join(
        line.split("%", 1)[0] for line in main.read_text(encoding="utf-8").splitlines()
    )
    if not re.search(r"\\documentclass\s*\[\s*withoutpreface\s*\]\s*\{cumcmthesis\}", active_main):
        raise DeliveryError("电子版必须实际启用摘要首页模式，不能包含承诺书与编号专用页")
    appendix, ai_used = _appendix_and_ai(main, state)
    program_names = _code_selection(root, state)
    support: set[str] = set(program_names)
    raw_problem = set()
    for row in (state.get("data") or {}).get("sources") or []:
        if not isinstance(row, Mapping):
            raise DeliveryError("data.sources 包含非法数据记录")
        kind = _source_type(row)
        if kind == "problem_attachment":
            raw_problem.add(str(row["path"]))
        elif kind == "independent":
            support.add(_relative(root, _inside(root, str(row["path"]), support=True)))
    for name in extra_files:
        support.add(_relative(root, _inside(root, name, support=True)))
    if support & raw_problem:
        raise DeliveryError("官方支撑包不得重新收录赛题提供的原始附件: " + str(sorted(support & raw_problem)))
    program_names.update(name for name in support if Path(name).suffix.lower()
                         in {".py", ".m", ".r", ".do", ".sps", ".jl", ".c", ".cpp", ".sh"})
    ai_name = str(rules["paper"]["ai_detail_file_when_used"])
    if ai_used:
        support.add(_relative(root, _inside(root, ai_name, support=True)))
        if not (root / ai_name).read_bytes().startswith(b"%PDF-"):
            raise DeliveryError("AI 使用详情文件不是有效 PDF")
    elif ai_name in support:
        raise DeliveryError("声明未使用 AI 时，不得输出 AI 使用详情")
    if support and "本论文没有支撑材料" in appendix:
        raise DeliveryError("附录声称没有支撑材料，但当前实际需要支撑 ZIP")
    if not support and "本论文没有支撑材料" not in appendix:
        raise DeliveryError("无支撑文件时须在附录中写明“本论文没有支撑材料”")
    if program_names and "本论文没有用到程序" in appendix:
        raise DeliveryError("已有实际源程序却在附录声称没有使用程序")
    if not program_names and "本论文没有用到程序" not in appendix:
        raise DeliveryError("未登记实际源程序时，附录须声明“本论文没有用到程序”")
    listed = sorted(support)
    for name in listed:
        if name not in appendix:
            raise DeliveryError(f"支撑材料未在正文附录列示精确路径: {name}")
    if PARTIAL_LISTING.search(appendix):
        raise DeliveryError("附录不得用 firstline/lastline 截取源程序后冒充完整代码")
    included = set()
    for name in LISTING.findall(appendix):
        path = (main.parent / name).resolve()
        if not path.is_relative_to(root):
            raise DeliveryError("附录源码引用越出项目根目录")
        included.add(_relative(root, path))
    for name in sorted(program_names):
        if name not in included:
            raise DeliveryError(f"附录必须使用完整可执行源程序引用（\\lstinputlisting）: {name}")
    for name in listed:
        path = _inside(root, name, support=True)
        if path.suffix.lower() in {".py", ".m", ".txt", ".r", ".csv", ".json", ".yaml"}:
            _scan_personal_data(path.read_text(encoding="utf-8-sig"), name)
    return {"root": root, "state": state, "rules": rules, "main": main, "pdf": pdf,
            "support": listed, "programs": sorted(program_names), "ai_used": ai_used,
            "pdf_sha256": _sha(pdf), "support_sha256": {p: _sha(_inside(root, p, support=True))
                                                    for p in listed}}


def verify(plan: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    """Verify actual external files against current project bytes and appendix."""
    root = plan["root"]
    paper = output_dir / PAPER_NAME
    support = output_dir / SUPPORT_NAME
    if _sha(plan["pdf"]) != plan["pdf_sha256"]:
        raise DeliveryError("当前正式 PDF 在交付准备之后发生变化，必须重新验收")
    for relative, expected_sha in plan["support_sha256"].items():
        if _sha(_inside(root, relative, support=True)) != expected_sha:
            raise DeliveryError(f"当前支撑文件内容已变化: {relative}")
    if not paper.is_file() or _sha(paper) != plan["pdf_sha256"]:
        raise DeliveryError("对外 PDF 缺失或已与当前已编译 PDF 不一致")
    max_paper = int(plan["rules"]["paper"]["max_paper_mb"]) * 1024 * 1024
    max_support = int(plan["rules"]["paper"]["max_support_mb"]) * 1024 * 1024
    if paper.stat().st_size > max_paper:
        raise DeliveryError("对外 PDF 超过当届大小上限")
    if plan["support"]:
        if not support.is_file() or support.stat().st_size > max_support:
            raise DeliveryError("必要支撑 ZIP 不存在或超过当届大小上限")
        try:
            with zipfile.ZipFile(support) as z:
                names = z.namelist()
                if (len(names) != len(set(names)) or set(names) != set(plan["support"])
                        or any(name.startswith("/") or ".." in Path(name).parts for name in names)):
                    raise DeliveryError("支撑 ZIP 包内清单不等于正文附录和现有活动材料清单")
                for name in names:
                    if hashlib.sha256(z.read(name)).hexdigest() != plan["support_sha256"][name]:
                        raise DeliveryError(f"支撑 ZIP 的文件内容已变化: {name}")
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            raise DeliveryError(f"无法读取支撑 ZIP: {exc}") from exc
    elif support.exists():
        raise DeliveryError("论文确无支撑材料，但提交目录仍遗留旧支撑 ZIP")
    return {"status": "passed", "edition": "2026", "paper": str(paper),
            "paper_sha256": _sha(paper),
            "support_zip": str(support) if plan["support"] else None,
            "support_files": plan["support"], "ai_used": plan["ai_used"],
            "anonymous_confirmation": "confirmed_by_contestant"}


def build(plan: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    root = plan["root"]
    if not output_dir.resolve().is_relative_to(root):
        raise DeliveryError("外部上传输出必须位于当前项目目录")
    output_dir.mkdir(parents=True, exist_ok=True)
    paper = output_dir / PAPER_NAME
    support = output_dir / SUPPORT_NAME
    if not plan["support"] and support.exists():
        raise DeliveryError("发现旧支撑 ZIP，必须先由参赛队核对后再选择无支撑材料交付")
    with tempfile.TemporaryDirectory(prefix="cumcm_a2_", dir=output_dir) as tempdir:
        temp = Path(tempdir)
        staged_pdf = temp / PAPER_NAME
        shutil.copyfile(plan["pdf"], staged_pdf)
        if plan["support"]:
            with zipfile.ZipFile(temp / SUPPORT_NAME, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for name in plan["support"]:
                    z.write(_inside(root, name, support=True), arcname=name)
        checked = verify(plan, temp)
        os.replace(staged_pdf, paper)
        if plan["support"]:
            os.replace(temp / SUPPORT_NAME, support)
        return verify(plan, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="CUMCM 2026 verified external delivery")
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--verify", action="store_true", help="Validate, do not generate")
    parser.add_argument("--extra-file", action="append", default=[],
                        help="A necessary independent dataset, command or support material")
    parser.add_argument("--anonymous-confirmed", action="store_true",
                        help="Contestants personally checked PDF and every support file")
    parser.add_argument("--output-dir", default="submission/cumcm2026_external")
    args = parser.parse_args()
    try:
        root = Path(args.project).resolve()
        plan = prepare(root, extra_files=tuple(args.extra_file),
                       anonymous_confirmed=args.anonymous_confirmed)
        directory = (root / args.output_dir).resolve()
        if not directory.is_relative_to(root):
            raise DeliveryError("output-dir 越出项目目录")
        result = verify(plan, directory) if args.verify else build(plan, directory)
    except (DeliveryError, OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(json.dumps({"status": "failed", "issue": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
