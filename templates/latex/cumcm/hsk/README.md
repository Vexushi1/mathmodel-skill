# HSK CUMCM LaTeX Template Authority

本目录从 v8.0.0 起承担 **CUMCM HSK 论文结构与 LaTeX 渲染的 Template Authority**。模板决定论文固定骨架、一级章节顺序、问题章节一级标题、LaTeX 工程组织和确定性渲染方式；Writing Skill 只负责数学叙事、公式承接、求解说明、结果解释和验证表达，不再重复维护模板已经能够确定的结构。

当前 canonical template 已完成两类参考吸收：

- `reference/example_mm_r1.tex`：用户提供的 LaTeX 版式参考，主要吸收页面、标题层级、摘要、三线表、代码和附录组织；
- `reference/a196_framework_notes.md`：用户提供优秀论文 A196 的章节框架提炼，主要吸收“问题重述 → 问题分析 → 模型假设 → 符号说明 → 模型准备 → 各问题独立建立与求解 → 模型评价 → 参考文献 → 附录”的论文组织。

只吸收结构和表达组织，不复制参考论文的正文、公式、图表、算法、参数或结果。

- Template Manifest：`template_manifest.yaml`
- HSK 主入口：`hsk_main.tex`
- 原 `cumcmthesis` 资源：`../cumcmthesis/`
- 全局配置：`config/`
- 摘要：`frontmatter/abstract.tex`
- 正文章节：`sections/`
- 附录：`appendices/`
- 参考文献库：`references.bib`

## 1. v8.0.0 推荐章节框架

新模板参考优秀论文 A196 的整体组织，但保持 HSK 的自适应规则：

```text
摘要 / 关键词
一、问题重述
   1.1 问题背景
   1.2 问题提出
二、问题分析
   2.1 问题一的分析
   2.2 问题二的分析
   ...
三、模型假设
四、符号说明
五、模型准备                      [按需]
六、问题一模型建立及求解
七、问题二模型建立及求解
八、问题三模型建立及求解
...                               [按实际小问数量]
模型的评价与改进
参考文献
附录
```

若确有项目级共享数据处理，可在“符号说明”之后、“模型准备”之前插入 `05_data.tex`。它是条件章节，默认 `hsk_main.tex` 不启用。

### 模型准备的职责

`模型准备` 只在两问及以上共享实质结构时保留，用于统一定义：

- 共享运动/状态方程；
- 公共坐标系和几何关系；
- 公共事件判定式；
- 共用变量、边界、阈值或评价指标；
- 后续各问都要调用的基础机理。

如果只有一个问题使用某关系，应把它写回对应问题章节；如果没有共享结构，应删除 `模型准备`，不能为了编号完整保留空章。

## 2. 每个问题的局部框架

一级标题固定为：

```text
问题X模型建立及求解
```

复杂问题默认形成：

```text
模型建立
→ 模型求解
→ 求解结果
→ 结果的分析与验证
```

这四个名称是 canonical example，不是 Hard 的逐字标题。若题目对象更适合专业标题，例如“遮蔽几何关系建立”“多目标优化求解”“轨迹参数与有效时长结果”“离散精度与参数扰动检验”，可直接替换二级标题。

简单解析题、直接计算题可以合并或删除不必要的小节，不为模板对称强行保留四段。

优化类问题在“模型建立”内部常见的三级逻辑为：

```text
决策变量
→ 目标函数
→ 约束条件
→ 模型收束
```

但只有当前题目确实需要时才使用。

## 3. Template 与 Writing Skill 的边界

Template Authority 可以规定：

- `documentclass`、全局宏包与 LaTeX 环境；
- 一级论文骨架和一级章节顺序；
- CUMCM 问题章节一级标题 `问题X模型建立及求解`；
- `main.tex` 的编排与正文子文件位置；
- 图、表、公式、命题、算法、参考文献和附录的渲染接口；
- 复杂优化模型中 objective 与 constraints 的确定性展示示例。

Template Authority **不可以**规定：

- 当前题目采用什么模型、solver 或 validator；
- 当前公式、参数、结果和验证证据；
- 每个问题必须使用哪些固定二级标题；
- 简单问题必须设置算法、核心模型汇总或验证小节；
- 为达到目标页数而增加无技术作用的正文。

Writing Skill 负责数学论证和段落组织，项目事实继续由当前 `模型论文框架.md`、真实工作簿和图表证据提供。

## 4. 模块化源码约定

`hsk_main.tex` 只承担编排，不保存大段正文。正式项目中推荐复制整个 `hsk/` 模板内容到 `final_latex/`，再将 `hsk_main.tex` 重命名为 `main.tex`。不要只复制单个主文件，否则 `\input{...}` 引用的模块会缺失。

默认工程结构：

```text
final_latex/
├─ main.tex
├─ config/
│  ├─ preamble.tex
│  ├─ commands.tex
│  └─ metadata.tex
├─ frontmatter/
│  └─ abstract.tex
├─ sections/
│  ├─ 01_problem_statement.tex
│  ├─ 02_problem_analysis.tex
│  ├─ 03_assumptions.tex
│  ├─ 04_symbols.tex
│  ├─ 05_data.tex                    # 条件章节
│  ├─ 05_model_preparation.tex       # 共享基础模型，按需
│  ├─ 06_question1.tex
│  ├─ 07_question2.tex               # 优化类问题示例，可复制
│  └─ ...
├─ appendices/
│  └─ appendices.tex
└─ references.bib
```

每个一级章节或完整小问默认对应一个 `.tex` 文件；只有单问确实很长时再二级拆分，避免碎片化。

## 5. 核心模型收束的模板语义

“核心模型汇总”从 v8.0.0 起是 rendering mode，不是默认独立二级标题。

复杂优化模型在模型建立末尾通常先单独展示目标函数：

```latex
\begin{equation}
    \min_{\mathbf{x}} f(\mathbf{x})
\end{equation}
```

再单独展示约束：

```latex
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

目标函数不得放入约束大括号。非优化、多方程、状态空间或简单解析问题必须按真实数学结构改写，不能为了保留示例而伪造 objective / constraints。

## 6. 结果与验证的局部闭环

参考优秀论文的组织方式，主结果和验证默认留在对应问题内部：

```text
本问模型
→ 本问求解
→ 本问结果
→ 本问验证
→ 直接回答本问
```

不再默认设置一个全文统一的“结果分析与验证”一级章，把各问证据拖到文末集中解释。

只有跨问题共用的综合验证确有独立价值时，才新增跨问章节。

## 7. LaTeX 工程规则

正文子文件不得声明 `\documentclass`、`\begin{document}` 或 `\end{document}`，也不得重复加载全局宏包。公式、图、表、命题的 label 在整个工程内必须唯一，跨文件 `\ref` / `\eqref` / `\cite` 按同一文档处理。

所有 `\input` / `\include` 路径统一相对于 `main.tex` 所在工程根目录书写。项目路径、主文件名和图片名使用 ASCII，并确保 `cumcmthesis.cls` 位于可搜索路径。

## 8. 审计与编译

推荐从仓库根目录执行：

```bash
python scripts/validate_template_manifest.py templates/latex/cumcm/hsk/template_manifest.yaml
python scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict
python scripts/render_paper.py final_latex --profile cumcm --clean
```

实际编译顺序由 `core/compile_profiles.yaml` 控制：

```text
XeLaTeX → Biber → XeLaTeX → XeLaTeX
```

模板中的题号、队伍编号、年份和具体小问数量必须按当届题面修改；内部覆盖表、项目状态术语和 QA 检查不得进入终稿。
