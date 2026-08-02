#!/usr/bin/env python3
"""Repair indentation and route/module structure introduced by the one-time migration."""
from __future__ import annotations

import py_compile
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "refresh-generated.yml"
ORIGINAL_WORKFLOW = '''name: Refresh generated repository metadata

on:
  push:
    branches:
      - main
      - "codex/**"
      - "fix/**"
      - "refactor/**"
      - "upgrade/**"
    paths-ignore:
      - SKILL_FILE_INDEX.md
      - TEMPLATE_INDEX.md
      - HSK_SKILL_FILE_INDEX_V622.md
      - HSK_TEMPLATE_INDEX_V622.md
      - MANIFEST.sha256
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: refresh-generated-${{ github.ref }}
  cancel-in-progress: true

jobs:
  refresh:
    if: github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.ref_name }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Rebuild active indexes and manifest
        run: python scripts/generate_indexes.py
      - name: Commit generated metadata when changed
        run: |
          if git diff --quiet -- SKILL_FILE_INDEX.md TEMPLATE_INDEX.md HSK_SKILL_FILE_INDEX_V622.md HSK_TEMPLATE_INDEX_V622.md MANIFEST.sha256; then
            echo "Generated metadata is current."
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add SKILL_FILE_INDEX.md TEMPLATE_INDEX.md HSK_SKILL_FILE_INDEX_V622.md HSK_TEMPLATE_INDEX_V622.md MANIFEST.sha256
          git commit -m "chore: refresh generated repository metadata"
          git push
'''


def dedent(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(dedent(text), encoding="utf-8", newline="\n")


def fix_schema() -> None:
    path = ROOT / "core" / "project_state.schema.yaml"
    text = path.read_text(encoding="utf-8")
    bad = '''        artifacts_stale: {type: boolean, default: false}
code: {type: string}
result_analysis_code: {type: string}
primary_code_sha256: {type: string, pattern: '^[0-9a-fA-F]{64}$'}
analysis_code_sha256: {type: string, pattern: '^[0-9a-fA-F]{64}$'}
primary_execution_status:
  type: string
  enum: [pending, code_delivered, awaiting_user_execution, workbook_received, accepted, rejected]
analysis_execution_status:
  type: string
  enum: [pending, code_delivered, awaiting_user_execution, workbook_received, accepted, rejected, redo_required]
        solution_workbook: {type: string}
'''
    good = '''        artifacts_stale: {type: boolean, default: false}
        code: {type: string}
        result_analysis_code: {type: string}
        primary_code_sha256: {type: string, pattern: '^[0-9a-fA-F]{64}$'}
        analysis_code_sha256: {type: string, pattern: '^[0-9a-fA-F]{64}$'}
        primary_execution_status:
          type: string
          enum: [pending, code_delivered, awaiting_user_execution, workbook_received, accepted, rejected]
        analysis_execution_status:
          type: string
          enum: [pending, code_delivered, awaiting_user_execution, workbook_received, accepted, rejected, redo_required]
        solution_workbook: {type: string}
'''
    if bad not in text:
        raise RuntimeError("schema subproblem block anchor missing")
    text = text.replace(bad, good, 1)
    bad = '''    properties:
owner: {type: string, enum: [user, assistant, external]}
profile: {type: string, enum: [full_fidelity]}
assistant_task_execution_allowed: {type: boolean}
allow_reduced_data: {type: boolean}
allow_coarser_grid: {type: boolean}
allow_shorter_horizon: {type: boolean}
allow_fewer_repetitions: {type: boolean}
allow_relaxed_tolerance: {type: boolean}
allow_silent_solver_fallback: {type: boolean}
python_version: {type: string}
      matlab_version: {type: string}
'''
    good = '''    properties:
      owner: {type: string, enum: [user, assistant, external]}
      profile: {type: string, enum: [full_fidelity]}
      assistant_task_execution_allowed: {type: boolean}
      allow_reduced_data: {type: boolean}
      allow_coarser_grid: {type: boolean}
      allow_shorter_horizon: {type: boolean}
      allow_fewer_repetitions: {type: boolean}
      allow_relaxed_tolerance: {type: boolean}
      allow_silent_solver_fallback: {type: boolean}
      python_version: {type: string}
      matlab_version: {type: string}
'''
    if bad not in text:
        raise RuntimeError("schema execution block anchor missing")
    path.write_text(text.replace(bad, good, 1), encoding="utf-8", newline="\n")


def fix_pipeline() -> None:
    path = ROOT / "templates" / "code" / "hsk_pipeline" / "main_pipeline.py"
    text = path.read_text(encoding="utf-8")
    bad = '''    capabilities: Mapping[str, bool]
random_seed: int = 2026
execution_owner: Literal["user"] = "user"
execution_profile: Literal["full_fidelity"] = "full_fidelity"
allow_reduced_data: bool = False
allow_coarser_grid: bool = False
allow_shorter_horizon: bool = False
allow_fewer_repetitions: bool = False
allow_relaxed_tolerance: bool = False
allow_silent_solver_fallback: bool = False

    def validate(self) -> None:
'''
    good = '''    capabilities: Mapping[str, bool]
    random_seed: int = 2026
    execution_owner: Literal["user"] = "user"
    execution_profile: Literal["full_fidelity"] = "full_fidelity"
    allow_reduced_data: bool = False
    allow_coarser_grid: bool = False
    allow_shorter_horizon: bool = False
    allow_fewer_repetitions: bool = False
    allow_relaxed_tolerance: bool = False
    allow_silent_solver_fallback: bool = False

    def validate(self) -> None:
'''
    if bad not in text:
        raise RuntimeError("pipeline dataclass anchor missing")
    text = text.replace(bad, good, 1)
    bad = '''        if not all(isinstance(value, bool) for value in self.capabilities.values()):
            raise TypeError("capabilities 的所有值必须为 bool")
if self.execution_owner != "user" or self.execution_profile != "full_fidelity":
    raise ValueError("v6.5.0正式代码必须由用户以full_fidelity模式执行")
forbidden_flags = {
    "allow_reduced_data": self.allow_reduced_data,
    "allow_coarser_grid": self.allow_coarser_grid,
    "allow_shorter_horizon": self.allow_shorter_horizon,
    "allow_fewer_repetitions": self.allow_fewer_repetitions,
    "allow_relaxed_tolerance": self.allow_relaxed_tolerance,
    "allow_silent_solver_fallback": self.allow_silent_solver_fallback,
}
enabled = sorted(name for name, value in forbidden_flags.items() if value)
if enabled:
    raise ValueError(f"完整版运行禁止启用降级标志: {enabled}")
if not self.framework_path.is_file():
            raise FileNotFoundError(f"模型锁定后必须先创建项目根目录模型论文框架: {self.framework_path}")
'''
    good = '''        if not all(isinstance(value, bool) for value in self.capabilities.values()):
            raise TypeError("capabilities 的所有值必须为 bool")
        if self.execution_owner != "user" or self.execution_profile != "full_fidelity":
            raise ValueError("v6.5.0正式代码必须由用户以full_fidelity模式执行")
        forbidden_flags = {
            "allow_reduced_data": self.allow_reduced_data,
            "allow_coarser_grid": self.allow_coarser_grid,
            "allow_shorter_horizon": self.allow_shorter_horizon,
            "allow_fewer_repetitions": self.allow_fewer_repetitions,
            "allow_relaxed_tolerance": self.allow_relaxed_tolerance,
            "allow_silent_solver_fallback": self.allow_silent_solver_fallback,
        }
        enabled = sorted(name for name, value in forbidden_flags.items() if value)
        if enabled:
            raise ValueError(f"完整版运行禁止启用降级标志: {enabled}")
        if not self.framework_path.is_file():
            raise FileNotFoundError(f"模型锁定后必须先创建项目根目录模型论文框架: {self.framework_path}")
'''
    if bad not in text:
        raise RuntimeError("pipeline validation anchor missing")
    path.write_text(text.replace(bad, good, 1), encoding="utf-8", newline="\n")


def write_router() -> None:
    write("core/workflow_router.yaml", r'''
        version: 6.5.0
        bootstrap: core/bootstrap.yaml
        default_load:
        - core/hsk_core_policy.md
        - core/module_manifest.yaml
        - core/task_taxonomy.yaml
        - core/user_execution_contract.yaml
        classification_contract:
          axes: [objective, structures, capabilities]
          capability_source: subproblem.capabilities
          deprecated_capability_alias: classification.capabilities
          objective_required_for_modeling_routes: true
          structures_max_items: 3
          legacy_task_labels_supported: true
          task_pack_budget: 3
        execution_contract:
          workflow_order: [problem_audit, model_design, solve_validate, result_analysis, figure_evidence, writing_latex, ai_cleanup, latex_compile_quality, review_delivery, writing_docx]
          formal_delivery_gates: [project_sync]
          task_code_execution_allowed: false
          rules:
          - Stop after the last module required by the user deliverable.
          - Never manufacture downstream artifacts when gate inputs are missing.
          - Generate full-fidelity task code and stop at awaiting_user_execution; never execute task-specific solve or analysis code.
          - Primary user-produced workbook must be accepted before final result-analysis code is generated.
          - Accepted result-analysis workbooks precede figures and writing.
          - Result analysis may send the workflow back to model_design or solve_validate when the locked result is not stable enough.
          - Merge multiple intents in workflow order and remove duplicate modules, packs and outputs.
          - Reuse current project state, framework and artifacts before recomputing.
          - A gate output is available only after the gate executes successfully.
          - Compile only the LaTeX source produced after AI cleanup.
        routing:
          new_problem_design:
            triggers: [新赛题, 建模方案, 建模思路, 全流程思路]
            infer_keywords: [新赛题, 建模方案, 建模思路, 审题并建模]
            load: [modules/01_problem_audit.md, packs/task/classifier.md]
            then: [modules/02_model_design.md]
            load_classified_task_packs: true
            load_competition_pack: true
            terminal_outputs: [requirement_map, route_comparison, selected_models, locked_model_spec, formula_closure, validation_plan, model_paper_framework]
            formal_delivery: true
            delivery_scope: design
          framework_sync:
            triggers: [模型论文框架, 框架同步, 结果摘要, 模型变更同步, 参数变更同步, 约束变更同步]
            infer_keywords: [模型论文框架, 框架同步, 更新框架, 同步结果摘要]
            load: [modules/02_model_design.md, templates/model/model_paper_framework.md]
            terminal_outputs: [model_paper_framework]
            formal_delivery: true
            delivery_scope: design
          project_sync:
            triggers: [项目同步, 同步项目, stale, 哈希检查, 产物一致性]
            infer_keywords: [项目同步, 同步项目, stale, 哈希, 产物一致性]
            load: [scripts/sync_project.py]
            terminal_outputs: [sync_report, project_state]
            formal_delivery: false
          proposition_proof:
            triggers: [命题证明, 命题, 证明, 引理, 推论, 等价性证明, 可行性证明, 单调性证明, 误差界]
            infer_keywords: [命题证明, 等价性证明, 可行性证明, 单调性证明, 误差界, 引理, 推论]
            load: [modules/02_model_design.md, templates/model/model_paper_framework.md]
            load_proposition_pack: true
            terminal_outputs: [formula_closure, proposition_plan, model_paper_framework]
            formal_delivery: true
            delivery_scope: design
          full_solution:
            triggers: [完整求解, 全部计算, 求出各问, 完成求解]
            infer_keywords: [完整求解, 全部计算, 求出各问, 完成求解]
            load: [modules/01_problem_audit.md, packs/task/classifier.md]
            then: [modules/02_model_design.md, modules/03_solve_validate.md, packs/artifact/code.md]
            load_classified_task_packs: true
            load_competition_pack: true
            terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, proposition_plan, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            formal_delivery: false
            delivery_scope: code
            pause_for_user_execution: true
          full_workflow:
            triggers: [全流程, 完整论文, 全套成果, 完整交付]
            infer_keywords: [全流程, 完整论文, 全套成果, 完整交付]
            load: [modules/01_problem_audit.md, packs/task/classifier.md]
            then: [modules/02_model_design.md, modules/03_solve_validate.md, packs/artifact/code.md]
            load_classified_task_packs: true
            load_competition_pack: true
            terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            formal_delivery: false
            delivery_scope: code
            pause_for_user_execution: true
          problem_analysis:
            triggers: [审题, 问题理解, 题目拆解, 设问意图, 命题意图]
            infer_keywords: [审题, 问题理解, 题目拆解, 设问意图]
            load: [modules/01_problem_audit.md, packs/task/classifier.md]
            terminal_outputs: [requirement_map, subproblem_map, classification_by_subproblem, data_schema]
            formal_delivery: false
          model_selection:
            triggers: [模型比较, 建模路线, 变量, 假设, 公式, 目标函数, 约束]
            infer_keywords: [模型比较, 建模路线, 变量, 假设, 公式, 目标函数, 约束]
            load: [modules/02_model_design.md, packs/task/classifier.md]
            load_classified_task_packs: true
            terminal_outputs: [route_comparison, selected_models, locked_model_spec, formula_closure, proposition_plan, validation_plan, model_paper_framework]
            formal_delivery: true
            delivery_scope: design
          advanced_method:
            triggers: [高级模型, W-DRO, CVaR, MPEC, Stackelberg, ALNS, GNN, 空间杜宾, DML, 强化学习, 深度学习]
            infer_keywords: [W-DRO, CVaR, MPEC, Stackelberg, ALNS, GNN, 空间杜宾, DML, 强化学习, 深度学习]
            load: [modules/02_model_design.md, packs/task/advanced_method_gate.md, packs/task/classifier.md]
            load_classified_task_packs: true
            terminal_outputs: [route_comparison, selected_models, locked_model_spec, validation_plan, proposition_plan, model_paper_framework]
            formal_delivery: true
            delivery_scope: design
          code_and_solution:
            triggers: [代码, Python, 求解, 算法, 最优解]
            infer_keywords: [Python代码, 求解代码, 开始求解, 求解, 继续求解, 重新求解, 重算, 算法实现, 最优解]
            load: [modules/03_solve_validate.md, packs/artifact/code.md, packs/task/classifier.md]
            load_classified_task_packs: true
            terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            formal_delivery: false
            delivery_scope: code
            pause_for_user_execution: true
          result_analysis:
            triggers: [结果分析, 深化分析, 敏感性, 鲁棒性, 多算法, 稳健性, 阈值分析, 结构稳健性, 异质性]
            infer_keywords: [结果分析, 敏感性分析, 鲁棒性分析, 多算法验证, 稳健性分析, 阈值分析, 结构稳健性, 异质性分析]
            load: [modules/03_result_analysis.md, packs/artifact/code.md, packs/task/classifier.md]
            load_classified_task_packs: true
            terminal_outputs: [result_analysis_plan, result_analysis_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            formal_delivery: false
            delivery_scope: code
            pause_for_user_execution: true
          returned_workbook_validation:
            triggers: [返回工作簿, 验收工作簿, 校验求解结果, 校验结果深化分析, 本地运行完成]
            infer_keywords: [返回工作簿, 验收工作簿, 本地运行完成, 校验求解结果]
            load: [scripts/validate_user_execution.py]
            pre_delivery_gates: [user_execution_receipt]
            terminal_outputs: [user_execution_validation_report, project_state]
            formal_delivery: false
          validation:
            triggers: [检验, 多算法, 全局最优, 敏感性, 鲁棒性, 误差, 稳健性]
            infer_keywords: [多算法, 全局最优, 敏感性, 鲁棒性, 稳健性, 误差分析, 模型检验]
            load: [modules/03_result_analysis.md, packs/task/classifier.md]
            load_classified_task_packs: true
            terminal_outputs: [result_analysis_code, full_run_config, execution_instructions, awaiting_user_execution, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            formal_delivery: false
            delivery_scope: code
            pause_for_user_execution: true
          figures:
            triggers: [图表, 可视化, 机理图, 推导图, Nature, SCI, MATLAB图标题]
            infer_keywords: [MATLAB绘图, MATLAB, 结果图, 敏感性图, 鲁棒性图, 机理图, 推导图, 可视化, 图表]
            load: [modules/04_figure_evidence.md, packs/artifact/figure.md, templates/figure/chart_selection.md]
            terminal_outputs: [figure_contracts, approved_figures, model_paper_framework]
            formal_delivery: true
            delivery_scope: figures
          docx:
            triggers: [DOCX, Word, 草稿论文]
            infer_keywords: [DOCX, Word, 草稿论文, 论文草稿]
            load: [modules/05_writing/docx.md, packs/artifact/docx.md]
            terminal_outputs: [docx_draft, latex_migration_notes]
            formal_delivery: true
            delivery_scope: docx
          latex:
            triggers: [LaTeX, PDF终稿, cumcmthesis, 终稿论文]
            infer_keywords: [LaTeX, PDF终稿, cumcmthesis, 终稿论文, 编译论文]
            load: [modules/05_writing/latex.md, modules/05_writing/ai_cleanup.md, modules/05_latex_compile_quality.md, packs/artifact/latex.md]
            load_competition_pack: true
            terminal_outputs: [latex_source, compiled_pdf, compile_report]
            formal_delivery: true
            delivery_scope: latex
          full_submission:
            triggers: [复现包, 提交压缩包, 提交包]
            infer_keywords: [复现包, 提交压缩包, 提交包]
            load: [modules/06_review_delivery.md, packs/artifact/full_submission.md]
            load_competition_pack: true
            terminal_outputs: [validated_submission_package]
            formal_delivery: true
            delivery_scope: submission
          review:
            triggers: [评分, 审稿, 终审, 检查, 提交包检查]
            infer_keywords: [评分, 审稿, 终审, 提交包检查, 论文检查]
            load: [modules/06_review_delivery.md, packs/artifact/review.md]
            load_competition_pack: true
            terminal_outputs: [review_report]
            formal_delivery: true
            delivery_scope: submission
        multi_intent_policy:
        - Merge modules in workflow order and remove duplicates.
        - Merge terminal outputs without dropping model_paper_framework for formal deliveries.
        - Code delivery and returned-workbook validation use dedicated gates that never execute task code.
        - Primary code delivery pauses for user execution; accepted primary workbooks precede result-analysis code delivery.
        - Accepted result-analysis workbooks precede figures and writing.
        - Result-analysis failure may route back to model design or primary solving.
        - Figures precede final writing insertion; AI cleanup precedes LaTeX compilation.
        - Proposition details are loaded only for explicit proof requests or a nonzero proposition plan.
        - Project synchronization is a utility gate and does not promote quality or validation success.
    ''')


def write_manifest() -> None:
    write("core/module_manifest.yaml", r'''
        version: 6.5.0
        workflow_order: [problem_audit, model_design, solve_validate, result_analysis, figure_evidence, writing_latex, ai_cleanup, latex_compile_quality, review_delivery, writing_docx]
        contracts:
          bootstrap: core/bootstrap.yaml
          taxonomy: core/task_taxonomy.yaml
          output: core/output_contract.yaml
          workbook: core/workbook_schema.yaml
          project_state: core/project_state.schema.yaml
          user_execution: core/user_execution_contract.yaml
          framework_template: templates/model/model_paper_framework.md
          compile_profiles: core/compile_profiles.yaml
        external_artifacts:
        - problem_text
        - attachments
        - competition
        - requested_deliverable
        - data
        - bibliography
        - compile_profile
        - workbook_schema
        - output_contract
        - all_requested_artifacts
        - existing_project_state
        - existing_model_paper_framework
        - discovered_artifacts
        - accepted_solution_workbook
        - accepted_result_analysis_workbook
        artifact_catalog:
          requirement_map: 题目要求与交付映射
          subproblem_map: 小问依赖和边界
          classification_by_subproblem: 每问objective、structures、顶层capabilities与置信度
          problem_types_by_subproblem: 旧版题型标签兼容派生输出
          data_schema: 字段、单位、粒度、键和数据质量口径
          risks: 审题、数据、模型和交付风险
          route_comparison: 每问模型路线比较
          selected_models: 每问选定模型
          locked_model_spec: 已锁定变量、假设、公式、目标和约束
          formula_closure: 公式—代码—输出映射
          proposition_plan: 全文0--4个高价值命题规划
          model_paper_framework: 当前有效模型语义、论文组织、逐问结果摘要和图表映射
          mechanism_contracts: 机理图合同
          validation_plan: 建模阶段识别的风险与候选验证方向
          python_code: 用户本地执行的完整版Python主求解代码
          result_analysis_code: 用户本地执行的完整版结果深化分析代码
          full_run_config: 完整精度运行参数、代码与数据哈希和禁止降级标志
          execution_instructions: 用户本地运行与返回工作簿说明
          code_delivery_report: 不执行赛题代码的静态交付检查报告
          awaiting_user_execution: 等待用户本地运行并返回工作簿的暂停状态
          user_execution_validation_report: 用户返回工作簿的运行配置、哈希和质量门验收报告
          solution_workbook: 用户返回并验收的主求解结果工作簿
          result_quality_report: 主结果精度、收敛、可行性和基础正确性报告
          solved_results: 已通过主结果质量门的结果
          constraint_checks: 约束、残差、守恒、离散或收敛检查
          result_analysis_plan: 基于主结果风险选择的深化分析计划
          result_analysis_workbook: 用户返回并验收的结果深化分析工作簿
          result_analysis_report: 实际深化分析报告
          validated_results: 通过结果深化分析且可用于写作的结果
          evidence_map: 结论到公式、代码、表和图的证据映射
          matlab_scripts: MATLAB问题专属绘图脚本
          result_figures: 工作簿驱动且包含简洁标题的正式结果图
          refined_mechanism_figures: 精修后的S/A级机理图
          figure_contracts: 结果图和机理图合同
          approved_figures: 已确认可入文的图
          docx_draft: DOCX草稿
          latex_migration_notes: DOCX到LaTeX迁移说明
          latex_source_draft: 未清理LaTeX源码
          paper_text: 可执行文本审查的论文内容
          latex_source: 已清理待编译LaTeX源码
          cleaned_paper_text: 已清理论文正文
          unsupported_claims: 缺乏证据的结论清单
          compiled_pdf: 最终PDF
          compile_report: 编译引擎、日志和警告检查
          review_report: 终审问题与评分报告
          validated_submission_package: 通过交付检查的提交包
          project_state: 项目机器状态
          sync_report: 项目同步器生成的发现、Schema校验、分层哈希、stale和证据链报告
          figure_evidence: 工作簿、MATLAB脚本与逐图哈希证据
        workflow_profiles:
          design:
            modules: [problem_audit, model_design]
            module_terminal_outputs: [requirement_map, route_comparison, selected_models, locked_model_spec, formula_closure, validation_plan, model_paper_framework]
            pre_delivery_gates: [project_sync]
            terminal_outputs: [requirement_map, route_comparison, selected_models, locked_model_spec, formula_closure, validation_plan, model_paper_framework, project_state, sync_report]
          full_solution:
            modules: [problem_audit, model_design, solve_validate]
            module_terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, proposition_plan, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, proposition_plan, model_paper_framework, project_state]
          full_workflow:
            modules: [problem_audit, model_design, solve_validate]
            module_terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
            pre_delivery_gates: [code_delivery]
            terminal_outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework, project_state]
        modules:
          problem_audit:
            path: modules/01_problem_audit.md
            inputs: [problem_text, attachments, competition, requested_deliverable]
            outputs: [requirement_map, subproblem_map, classification_by_subproblem, problem_types_by_subproblem, data_schema, risks]
          model_design:
            path: modules/02_model_design.md
            inputs: [requirement_map, data_schema, classification_by_subproblem]
            outputs: [route_comparison, selected_models, locked_model_spec, formula_closure, proposition_plan, model_paper_framework, mechanism_contracts, validation_plan]
          solve_validate:
            path: modules/03_solve_validate.md
            inputs: [locked_model_spec, formula_closure, proposition_plan, model_paper_framework, data_schema, data, workbook_schema]
            outputs: [python_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
          result_analysis:
            path: modules/03_result_analysis.md
            inputs: [accepted_solution_workbook, result_quality_report, validation_plan, model_paper_framework, workbook_schema]
            outputs: [result_analysis_plan, result_analysis_code, full_run_config, execution_instructions, code_delivery_report, awaiting_user_execution, model_paper_framework]
          figure_evidence:
            path: modules/04_figure_evidence.md
            inputs: [solution_workbook, result_analysis_workbook, workbook_schema, model_paper_framework, mechanism_contracts, evidence_map]
            outputs: [matlab_scripts, result_figures, refined_mechanism_figures, figure_contracts, approved_figures, evidence_map, model_paper_framework]
          writing_docx:
            path: modules/05_writing/docx.md
            inputs: [model_paper_framework, proposition_plan, locked_model_spec, validated_results, figure_contracts]
            outputs: [docx_draft, latex_migration_notes]
          writing_latex:
            path: modules/05_writing/latex.md
            inputs: [model_paper_framework, proposition_plan, locked_model_spec, validated_results, approved_figures, bibliography]
            outputs: [latex_source_draft, paper_text]
          ai_cleanup:
            path: modules/05_writing/ai_cleanup.md
            inputs: [latex_source_draft, paper_text, evidence_map]
            outputs: [latex_source, cleaned_paper_text, unsupported_claims]
          latex_compile_quality:
            path: modules/05_latex_compile_quality.md
            inputs: [latex_source, compile_profile]
            outputs: [compiled_pdf, compile_report]
          review_delivery:
            path: modules/06_review_delivery.md
            inputs: [all_requested_artifacts, proposition_plan, model_paper_framework, output_contract, workbook_schema, compile_profile, compile_report]
            outputs: [review_report, validated_submission_package]
        utility_gates:
          code_delivery:
            path: scripts/validate_code_delivery.py
            command: python scripts/validate_code_delivery.py <project_root> --write --strict
            inputs: [existing_project_state, existing_model_paper_framework, python_code, full_run_config, execution_instructions]
            outputs: [code_delivery_report, project_state, awaiting_user_execution]
          user_execution_receipt:
            path: scripts/validate_user_execution.py
            command: python scripts/validate_user_execution.py <project_root> --write --strict
            inputs: [existing_project_state, discovered_artifacts]
            outputs: [user_execution_validation_report, project_state, solution_workbook, result_analysis_workbook]
          project_sync:
            path: scripts/sync_project.py
            command: python scripts/sync_project.py <project_root> --write --strict --delivery-scope <delivery_scope>
            inputs: [existing_project_state, existing_model_paper_framework, discovered_artifacts, workbook_schema, output_contract]
            outputs: [project_state, sync_report]
            delivery_scopes: [design, code, results, figures, docx, latex, submission]
            stage_requirements_source: core/output_contract.yaml#project_sync.stage_requirements
            rules:
            - Reads exact delivery requirements from core/output_contract.yaml before checking artifacts.
            - Validates project state and the current model-paper framework before artifact discovery.
            - Discovers artifacts, validates workbook contracts and hashes the evidence chain without inventing model semantics or validation success.
            - Propagates stale from data, model, workbooks, MATLAB scripts and figure bundles without clearing it.
            - Required before formal model, workbooks, figures, DOCX, LaTeX or submission delivery.
            - Code delivery uses the dedicated non-executing code_delivery gate.
    ''')


def validate() -> None:
    for relative in (
        "core/project_state.schema.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml",
        "core/output_contract.yaml", "core/user_execution_contract.yaml",
    ):
        yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    for relative in (
        "templates/code/hsk_pipeline/main_pipeline.py",
        "scripts/validate_code_delivery.py", "scripts/validate_user_execution.py",
        "scripts/resolve_workflow.py",
    ):
        py_compile.compile(str(ROOT / relative), doraise=True)


def main() -> int:
    fix_schema()
    fix_pipeline()
    write_router()
    write_manifest()
    validate()
    WORKFLOW.write_text(ORIGINAL_WORKFLOW, encoding="utf-8", newline="\n")
    Path(__file__).unlink()
    print("v6.5.0 structural repair complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
