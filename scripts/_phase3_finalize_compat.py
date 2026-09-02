from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    anchor = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->\n\n"
    if text.count(anchor) != 1:
        raise RuntimeError(f"entry contract anchor drifted: {relative}")
    compat = '''<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->

## 默认执行

默认入口始终是 `scripts/resolve_runtime.py`；`scripts/resolve_workflow.py` 只作为 legacy / 无状态兼容 resolver，不参与默认 assured read path。

### 项目工作记忆

项目语义继续由 `模型论文框架.md`、`state/project_state.yaml` 与 accepted workbook 分层恢复；本节只保留稳定导航标题，不复制 Project Memory 合同字段。

## 主链

为兼容活动导航与健康检查，只列出主链语义节点，不在入口重新定义其业务规则：

`通用数据审计` → `两条模型路线与数据需求比较` → `preprocessing_decision` → `proposed_model_spec` → `Model Reviewer + Devil's Advocate` → `awaiting_model_approval` → explicit Human Model Approval → `locked_model_spec` → resolver-selected preprocessing / solve / analysis stages。

## 目录、正式交付

目录与 artifact 数量只服从 `core/output_contract.yaml`。LaTeX 公共审计入口是 `scripts/audit_latex_project.py`；提交包在 resolver 返回的全部 gate 完成后才可成为 `validated_submission_package`。

'''
    text = text.replace(anchor, compat, 1)
    path.write_text(text, encoding="utf-8", newline="\n")

project_path = ROOT / "PROJECT_INSTRUCTIONS.md"
project = project_path.read_text(encoding="utf-8")
old_model = "- Problem Contract、Model Challenge passed 或用户未反对都不能替代显式 Human Model Approval。正式项目级预处理或主求解代码前，current `semantic_revision/hash` 必须与 current `locked_model_spec` 的批准状态闭合，并执行 resolver 返回的语义/模型批准 gate。"
new_model = "- Problem Contract 冻结后形成 `proposed_model_spec`，依次经过独立 `Model Reviewer` 与 `Devil's Advocate`；challenge passed 后进入 `awaiting_model_approval`，只有用户显式批准 current `semantic_revision/hash` 才形成 current `locked_model_spec`。正式项目级预处理或主求解代码前仍必须执行 resolver 返回的语义/模型批准 gate。"
if project.count(old_model) != 1:
    raise RuntimeError("project model-approval anchor drifted")
project = project.replace(old_model, new_model, 1)

anchor_exec = "- 题目专属预处理、主求解和结果深化 Python 默认由用户本地 full-fidelity 执行。助手生成并静态检查代码、验收返回工作簿；不得为了省时静默改变采样、精度、时域、重复次数、容差或求解器。"
exec_add = anchor_exec + "\n- Artifact 名称只作导航：每问最终默认恰好包含五个文件；两段题目专属 Python 入口为 `问题X求解.py` 与 `问题X结果深化分析.py`。具体五文件字段、目录和交付规则只服从 `core/output_contract.yaml`。"
if project.count(anchor_exec) != 1:
    raise RuntimeError("project execution anchor drifted")
project = project.replace(anchor_exec, exec_add, 1)

anchor_write = "- LaTeX 为默认主链。CUMCM 先读 `templates/latex/cumcm/hsk/template_manifest.yaml` 确定固定骨架，再按 `core/writing_runtime_contract.yaml` 的 progressive authoring 顺序读取 `modules/05_writing/paper_writing_protocol.md`；复杂数学/证据语义由 `core/writing_reasoning_contract.yaml` 裁决，`modules/05_writing/latex.md` 只负责载体适配。"
write_add = anchor_write + " `既定论文大章节骨架保持不变`；公开 LaTeX 项目审计统一从 `scripts/audit_latex_project.py` 进入。"
if project.count(anchor_write) != 1:
    raise RuntimeError("project writing anchor drifted")
project = project.replace(anchor_write, write_add, 1)
project_path.write_text(project, encoding="utf-8", newline="\n")

test_path = ROOT / "tests/test_v802_entrypoint_surface_slimming.py"
test = test_path.read_text(encoding="utf-8")
test = test.replace(
    '        for duplicated in (\n            "问题X求解.py",\n            "问题X结果深化分析.py",\n            "required / inline / not_applicable",',
    '        for artifact in ("问题X求解.py", "问题X结果深化分析.py"):\n            self.assertIn(artifact, self.instructions)\n        for duplicated in (\n            "├─",\n            "required / inline / not_applicable",',
)
if 'for artifact in ("问题X求解.py", "问题X结果深化分析.py")' not in test:
    raise RuntimeError("surface test compatibility patch failed")
test_path.write_text(test, encoding="utf-8", newline="\n")

print("v8.0.2 compatibility navigation shell applied")
