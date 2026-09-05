# Module 05B：LaTeX Adapter

本模块只负责把已经确定的论文内容放入当前 LaTeX 载体。**Template-First adapter architecture introduced in v8.0.1**；当前 Skill release 版本只由活动 release carriers（如 `core/bootstrap.yaml`）声明，本标题不再携带历史 release 号。本文件不拥有正文结构或表达规则。

Template-First 不等于一开始就读取本 Adapter 并生成全文。普通 CUMCM 新论文先按 `core/writing_runtime_contract.yaml#template_first_progressive_authoring` 检查 manifest/main，再逐章读取 Writing Protocol 并完成内容；本 Adapter 到命题/伪代码的载体需要或 `latex_assembly_audit_and_compile` 阶段才读取。AI Cleanup 和编译规则也不得提前支配问题重述、问题分析或模型建立及求解的内容取舍。

权威边界：

- `templates/latex/cumcm/hsk/template_manifest.yaml`：CUMCM 固定骨架、一级顺序、问题一级标题和模板文件组合；
- `modules/05_writing/paper_writing_protocol.md`：普通正文的数学叙事、段落承接、solver 说明、结果解释和验证组织；
- `core/writing_reasoning_contract.yaml`：跨题型复杂语义、Model / Solver / Validator、命题、Algorithm Trace、Claim Strength 等完整 Authority；
- `core/writing_runtime_contract.yaml`：普通 CUMCM LaTeX 写作的最小加载和完整 Authority 回退条件；
- 当前 `模型论文框架.md`、已验收工作簿和图表映射：项目事实与证据。

若上述来源冲突，先修复上游事实或 Authority；Adapter 不通过调整排版掩盖数学、结果或证据冲突。

## 1. Adapter 拥有与不拥有的内容

本模块拥有：

- 模板复制与 `main.tex` / 子文件装配；
- 公式、图、表、命题、算法、引用和附录的 LaTeX 环境；
- `label` / `ref` / `eqref` / `cite` 与工程路径；
- 载体级 objective / constraints 确定性渲染；
- 项目审计、编译和交付接口。

本模块不拥有：

- 一级章节及其顺序；
- 当前模型、solver、validator、参数、结果或验证方法；
- 问题章节内部的数学叙事规则；
- 二级/三级标题是否需要及其命名；
- 页数目标、命题预算、主张强度和风格判断。

## 2. 模板实例化

中文国赛正式项目复制完整目录：

```text
templates/latex/cumcm/hsk/
```

到项目的：

```text
final_latex/
```

随后把 `hsk_main.tex` 重命名为 `main.tex`。不要只复制单一主文件；固定结构由 `template_manifest.yaml` 管理，正文子文件按 `main.tex` 工程根目录解析。

数据章和模型准备章均为条件插槽。是否启用只取决于当前项目事实和 manifest 的 activation 条件，不因示例文件存在而自动启用。

用户明确要求偏离模板时，先在 `模型论文框架.md#当前写作选择` 记录 `template_id / instruction_source / override_scope / affected_files / reason / official_compliance_impact / status`。改变一级结构或官方格式的 proposed override 必须经用户确认；与当届官方格式冲突且当前交付仍受该格式约束时拒绝应用。

## 3. 槽位填充接口

Adapter 接收 Writing Protocol 已组织好的内容，并放入 manifest 指定槽位。复杂问题可使用 `MODEL → SOLVE → RESULT → VALIDATE` 四个功能槽，但它们不是强制逐字标题；简单题允许合并不必要的槽位。

公式语义服从 `Source → Derivation → Destination`，Adapter 只提供环境和引用：

```latex
\begin{equation}
    F(x,\theta)=0,
    \label{eq:q1-core}
\end{equation}
```

正文使用 `式~\eqref{eq:q1-core}`。不得在子文件中重复声明文档类、全局宏包或 `document` 环境。

## 4. 优化模型的确定性渲染

复杂优化模型需要展示核心模型时，目标函数与约束分开渲染：

```latex
\begin{equation}
    \min_{\mathbf{x}} f(\mathbf{x}).
\end{equation}

\begin{equation}
\text{s.t.}\quad
\left\{
\begin{aligned}
    g_i(\mathbf{x}) &\le 0,\\
    h_j(\mathbf{x}) &= 0,\\
    \mathbf{x} &\in \Omega.
\end{aligned}
\right.
\end{equation}
```

目标函数不得为了大括号整齐而塞进约束系统。`displayed / inline / omitted` 的选用由 Template Manifest 与 Writing Protocol 决定；Adapter 不强制独立“核心模型汇总”标题。

## 5. 图、表、命题和算法环境

- 图使用 `figure`，先 `\includegraphics`，后 `\caption` 与唯一 `\label{fig:...}`；
- 表使用 `table`，先 `\caption`，再以 `booktabs` 三线表承载内容；
- 正文核心图表必须以 `图~\ref{...}` / `表~\ref{...}` 显式引用；
- 命题只在上游已批准其数学作用时使用 `hskproposition` / `hskproof`；
- `not_needed / stepwise / pseudocode` 的选择与算法语义服从 `packs/artifact/algorithm_flow.md`；
- 伪代码环境只呈现数学对象和控制逻辑，不复制 Python 工程细节；
- 参考文献使用模板既有的 biblatex/Biber 接口，`\cite{}` key 必须存在于 `references.bib`。

具体图表解释、算法说明、命题治理与结果—验证承接不在本文件重复，分别回到 Writing Protocol 和完整 reasoning Authority。

## 6. 工程规则

- `main.tex` 只编排，正文按一级章或完整小问拆分；
- `\input` / `\include` 路径相对工程根目录；
- 主文件、子文件、图片与导出资源使用稳定 ASCII 文件名；
- label 在整个工程唯一；
- 子文件不得包含 `\documentclass`、`\begin{document}`、`\end{document}` 或全局 `\usepackage`；
- 图题在图下、表题在表上；正式图的整体标题由 LaTeX caption 承担；
- 参考文献位于问题章节和模型评价之后、附录之前；
- 旧的单文件 LaTeX 项目保持只读兼容，新项目默认使用模块化结构。

## 7. 审计与编译

正式交付统一执行：

```bash
python scripts/validate_template_manifest.py templates/latex/cumcm/hsk/template_manifest.yaml
python scripts/audit_latex_project.py final_latex/main.tex \
  --bib final_latex/references.bib \
  --framework 模型论文框架.md \
  --strict
python scripts/render_paper.py final_latex --profile cumcm --clean
```

`audit_latex_project.py` 会递归展开当前 include graph，并消费 prose audit 与 v8 surface audit；编译顺序和正式 attestation 继续由 `core/compile_profiles.yaml`、`modules/05_latex_compile_quality.md` 和 `scripts/render_paper.py` 管理。

## 8. v7 兼容索引（非 Authority）

- v7 核心模型收束模式的可读映射由 `core/writing_reasoning_contract.yaml#v8_compatibility` 唯一定义；
- v7 已填写的单文件或旧子文件布局不自动重排、不自动重命名，也不覆盖正文；
- v7 将本文件称为“正文结构与表达权威”的说法已废弃，替代项分别是 Template Manifest、Paper Writing Protocol 与本 Adapter；
- 完整迁移边界见 `docs/v8_writing_migration.md`。
