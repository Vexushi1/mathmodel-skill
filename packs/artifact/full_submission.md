# Artifact Pack：提交与完整复现

本 Pack 区分**竞赛官方提交包**与**完整复现包**。两者必须显式选择，不能把内部复现材料机械塞进官方提交物，也不能用只含官方文件的 ZIP 冒充完整复现包。

## 1. 竞赛官方提交包

官方提交内容只服从当届题面/官方通知、`config/competition_profiles.yaml` 中已核验的 `edition_rules` 和对应 competition Pack。若 `verification_status != verified`，或者缺少 `verified_at`、`source`、`submission_files`，Skill 必须拒绝自动生成 official package，而不是根据往届经验猜测。

当届规则核验后，`edition_rules.submission_files` 是机器可读 allowlist。例如赛事只要求最终 PDF 时，allowlist 只应解析到该 PDF；不得因为项目里存在 `模型论文框架.md`、state、Python、Excel、MATLAB、原始数据或内部检查材料而自动加入。

正式生成：

```bash
python scripts/hsk_pack_submission.py . \
  --mode official \
  --competition <profile-or-alias> \
  --output submission/submission.zip
```

ZIP 内自动写入 `submission_manifest.yaml`，记录 package kind、竞赛 profile、规则核验时间/来源、allowlist，以及每个实际文件的 SHA-256。

## 2. 完整复现包

仅当用户明确要求“完整复现包 / 全套成果 / 内部归档”时使用 reproducibility mode：

```bash
python scripts/hsk_pack_submission.py . \
  --mode reproducibility \
  --output submission/reproducibility.zip
```

完整复现包按项目实际状态包含当前有效的：

- `模型论文框架.md`；
- LaTeX 源码与最终 PDF；
- 允许归档的赛题、附件说明和实际输入数据；
- 若 `preprocessing_decision=project_level`：数据预处理三文件；
- 每问标准五文件目录；
- 正式图、可编辑机理图与必要复现说明。

其中每问标准目录仍为：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

主工作簿 accepted 后冻结主求解 Python；深化分析由独立 Python 完成。旧敏感性/鲁棒性工作簿、旧 `结果数据表/问题X/` 与 v6.6 单脚本四文件结构仅作历史只读兼容输入，不作为新复现包标准结构。

## 3. 包级 provenance gate

生成 ZIP 不等于通过交付。正式提交范围还必须运行：

```bash
python scripts/validate_submission_package.py . --strict
```

默认读取 `state/project_state.yaml -> artifacts.submission_package`；未声明时才回退 `submission/submission.zip`。验证器要求：

- ZIP 中恰好一个 `submission_manifest.yaml`；
- manifest 与 ZIP 文件集合完全一致，不允许未声明文件或重复路径；
- 每个归档文件 SHA-256 与 manifest 一致，并与当前项目同路径文件一致；
- 包内至少一个 PDF 的哈希必须等于当前 `compiled_pdf`；
- official package 必须重新读取**当前**已核验 `edition_rules`，并与 `submission_files` allowlist 精确一致；
- reproducibility package 至少包含当前 PDF、Python、结果工作簿和 MATLAB 脚本；
- 包内旧 PDF、旧代码或旧工作簿即使文件名正确，也不能通过当前性验证。

`validated_submission_package` 只有在该 gate 成功后才视为可正式交付；不能用“ZIP 存在”替代 provenance 验证。

## 4. 元数据边界

`run_info.json`、`result_manifest.yaml`、`matlab_figure_handoff.json` 不是每问默认产物。只有用户明确要求完整复现包且确有必要时才生成，并统一放在项目级内部元数据目录；不得破坏每问五文件合同或项目级预处理三文件合同。

`latex_audit_report.yaml`、`compile_report.yaml` 和 `submission_manifest.yaml` 属于正式交付证明链的机器元数据；它们用于审计和当前性验证，不机械写进论文正文，也不自动进入只允许 PDF 的官方提交包。

## 5. 提交前检查

1. 主结果与深化分析质量门已通过，无 unresolved `redo_required`；
2. 当前模型、工作簿、MATLAB 图、正文和 `模型论文框架.md` 一致且无 stale；
3. 正式 LaTeX 已形成 current `latex_audit_report.yaml + compile_report.yaml + compiled_pdf` 证明链；
4. `project_sync --delivery-scope submission` 通过；
5. 官方包按当前 verified rules 裁剪，复现包保持内部完整性；
6. `validate_submission_package.py --strict` 对实际准备交付的 ZIP 通过。

新项目不得创建 `结果数据表/`、`Python求解/`、`MATLAB绘图/` 等平行数值目录；每问只保留一个 `问题X求解/`。内部检查表和复现元数据不得机械进入论文正文。
