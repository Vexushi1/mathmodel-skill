# Artifact Pack：提交与完整复现

本 Pack 区分**竞赛官方提交包**与**完整复现包**。两者必须显式选择，不能把内部复现材料机械塞进官方提交物，也不能用只含官方文件的 ZIP 冒充完整复现包。

## 1. 竞赛官方提交包

官方提交内容只服从当届题面/官方通知、`config/competition_profiles.yaml` 中已核验的 `edition_rules` 和对应 competition Pack。若 `verification_status != verified`，或者缺少 `verified_at`、`source`、`submission_files`，Skill 必须拒绝自动生成 official package，而不是根据往届经验猜测。

当届规则核验后，`edition_rules.submission_files` 是机器可读 allowlist。例如赛事只要求最终 PDF 时，allowlist 只应解析到该 PDF；不得因为项目里存在 `模型论文框架.md`、state、Python、Excel、MATLAB、原始数据或内部检查材料而自动加入。

助手核对规则后内部生成：

```bash
python scripts/hsk_pack_submission.py . \
  --mode official \
  --competition <profile-or-alias> \
  --output submission/submission.zip
```

ZIP 内自动写入 `submission_manifest.yaml`，记录 package kind、竞赛 profile、规则核验时间/来源、allowlist，以及每个实际文件的 SHA-256。这是**内部证据包**，不能作为 CUMCM 2026 对外上传文件。

### 2026 CUMCM 的独立对外上传（A2）

使用 `config/competition_profiles.yaml#profiles.cumcm.edition_rules` 和 `core/output_contract.yaml#delivery_attestation.cumcm_2026_external_upload`；实际工具为 `scripts/cumcm_2026_delivery.py`。**不改变旧内部包命令**。完成当前项目正式 LaTeX 编译及 03A/03B 验收后，人工确认 PDF 与全部支撑材料匿名，并执行：

```bash
python scripts/cumcm_2026_delivery.py <项目目录> --anonymous-confirmed \
  --extra-file "资料/自主查阅数据.csv" \
  --program-file "命令/Excel交互命令.txt"
python scripts/cumcm_2026_delivery.py <项目目录> --anonymous-confirmed \
  --extra-file "资料/自主查阅数据.csv" \
  --program-file "命令/Excel交互命令.txt" --verify
```

参数按实际需要使用；没有独立数据和交互命令时不添加对应参数。程序入口从已验收 State、活动求解/03B 阶段、项目选定 Python/MATLAB 绘图脚本及真实源码依赖获取，数据来源从已登记的独立/公开来源或明确的 `--extra-file` 获取；其他文字命令等可通过 `--program-file` 由参赛队显式指定。程序必须在论文附录以完整 `\\lstinputlisting{...}` 引用，并精确列示 ZIP 中每个文件的相对路径；不能用摘录或固定 A/B 占位代替。

输出目录只包含可对外提交的 `cumcm2026_paper.pdf` 及**当确有程序、独立数据、AI 使用详情或其他支撑材料时**才存在的 `cumcm2026_support.zip`。支撑 ZIP 内使用项目相对路径、不附带内部 manifest、`state/`、内部 ZIP、过期文件或赛题原始附件；两件分别不得超过 20MB。使用过 AI 时必需包含准确文件名 `AI工具使用详情.pdf` 且被附录列示；未使用 AI、确无程序或支撑材料时按官方要求保留相应声明，不伪造 ZIP。最终 `--verify` 再比对真实 ZIP 内各项 SHA-256、PDF 正式编译身份、活动源程序及当前附录清单，另需参赛队人工核实匿名与内容真实性。

这条外部文件校验是原有 `edition_compliance`、`anonymity_and_metadata`、`ai_disclosure`、`reproducibility_and_package` 检查族的 CUMCM 2026 消费接口，不创建第二套项目状态，也不将工具输出解释成数学正确性证明。

## 2. 完整复现包

仅当用户明确要求“完整复现包 / 全套成果 / 内部归档”时，由助手使用 reproducibility mode：

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
- 每问由 `core/output_contract.yaml` 定义的 current conditional layout：基础三文件始终收集，Gate=`required` 时再收集实际存在且 current 的 03B 两文件；
- 正式图、可编辑机理图与必要复现说明。

每问目录按 current 状态解释为：

```text
问题X求解/
├─ <项目后端对应主入口：问题X求解.py 或 qX_solver.m>
├─ 问题X求解结果.xlsx
├─ qX_plot.m
├─ [同一项目后端对应深化入口：问题X结果深化分析.py 或 qX_analysis.m]    # only Gate=required
└─ [问题X结果深化分析.xlsx]  # only Gate=required and analysis executed
```

Gate=`not_required` 且理由非空时，复现包不得为了凑固定结构伪造、补空或复制 03B 文件；这也不表示稳健性、稳定性或替代算法一致性已经验证。Gate=`required` 时，当前 03B 代码/工作簿属于复现材料并必须保持 provenance/currentness，已声明的源码 helper 也必须在当前包中与 bundle 一致。主工作簿 accepted 后冻结主求解代码；已激活的深化分析由同一项目后端对应的独立入口完成。旧敏感性/鲁棒性工作簿、旧 `结果数据表/问题X/` 与 v6.6 单脚本四文件结构仅作历史只读兼容输入，不作为新复现包标准结构。

## 3. 包级 provenance gate

packer 只生成 ZIP 和 manifest，不自动完成包验收。助手继续按 resolver 返回的顺序执行 `submission_package_validation`，接口见 `scripts/README.md`；用户获取完成验收的文件后按赛事渠道提交。

验证器按 `core/output_contract.yaml` 与现有包级 gate 核对实际 ZIP、manifest、当前项目来源及 compiled PDF，并按 package mode 检查已核验官方 allowlist 或完整复现材料。优先读取 `artifacts.submission_package`；未声明时，仅在 `submission/` 恰好存在一个 ZIP 时选择该候选，存在多个 ZIP 则要求显式声明，没有候选时才检查默认 `submission/submission.zip`。

`validated_submission_package` 只有在该 gate 成功后才视为可正式交付；不能用“ZIP 存在”替代 provenance 验证。

## 4. 元数据边界

`run_info.json`、`result_manifest.yaml`、`matlab_figure_handoff.json` 不是每问默认产物。只有用户明确要求完整复现包且确有必要时才生成，并统一放在项目级内部元数据目录：

```text
internal_metadata/
```

不得把这些文件塞入 `问题X求解/` 或 `数据预处理/`，也不得破坏每问 conditional layout contract 或项目级预处理三文件合同。旧称“每问五文件合同”只对应 Gate=`required` 的 total=5 情形，不能作为 `not_required` 项目的缺件判据。

`latex_audit_report.yaml`、`compile_report.yaml` 和 `submission_manifest.yaml` 属于正式交付证明链的机器元数据；它们用于审计和当前性验证，不机械写进论文正文，也不自动进入只允许 PDF 的官方提交包。

## 5. 助手提交前检查

1. 主结果质量门已通过；Analysis Necessity Gate 已有 current disposition：`required` 时 03B 质量/验收链通过且无 unresolved `redo_required`，`not_required` 时理由非空；
2. 当前模型、工作簿、MATLAB 图、正文和 `模型论文框架.md` 一致且无 stale；
3. 正式 LaTeX 已形成 current `latex_audit_report.yaml + compile_report.yaml + compiled_pdf` 证明链；
4. resolver 返回的同步与包级 gate 按顺序通过；
5. 官方包按当前 verified rules 裁剪，复现包保持内部完整性并只收集 current 状态实际要求的 03B 产物；
6. `Algorithm Trace` 与论文算法呈现闭合：`stepwise/pseudocode` 可追溯到当前模型/公式/命题/约束、真实代码实现和工作簿结果或验证证据；`not_needed` 不保留装饰性算法框；
7. 命题 0--4 仅是默认正文阅读预算；P5+ 若保留，已完成必要性审查并记录 justification，不把默认预算恢复成 Hard 上限。

新项目不得创建 `结果数据表/`、`Python求解/`、`MATLAB绘图/` 等平行数值目录；每问只保留一个 `问题X求解/`。内部检查表和复现元数据不得机械进入论文正文。
