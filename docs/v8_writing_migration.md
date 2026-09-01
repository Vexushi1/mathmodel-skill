# v8.0.0 写作架构迁移说明

本说明只处理 v7 项目进入 v8 Template-First 写作架构时的文件与职责迁移。它不修改模型数学、参数、结果、工作簿、Python/MATLAB 代码、Model Approval 或数值验证状态。

## 1. 新项目

新 CUMCM 项目复制 `templates/latex/cumcm/hsk/` 到 `final_latex/`，将 `hsk_main.tex` 重命名为 `main.tex`，并按 `template_manifest.yaml` 启用真实需要的插槽。

- 数据章默认关闭；只有项目级共享数据方法需要时启用。
- 模型准备章默认关闭；只有两问及以上共享实质机理、几何、状态方程或公共判定式时启用。
- 问题章按实际小问数量复制，每问一级标题保持 `问题X模型建立及求解`。
- 已确定正文按 Paper Writing Protocol 写入槽位，LaTeX Adapter 只负责环境、引用和编译接口。

## 2. v7 项目只读兼容

v8.x 继续读取下列 v7 形式：

- 单文件 LaTeX 工程；
- 已填写的旧模块化子文件；
- `required / inline / not_applicable` 核心模型收束状态；
- v7 的问题章正文和历史二级标题。

兼容层至少保留到 v9.0.0 之前。v8 不自动重命名、拆分或移动已填写正文，不把旧项目的章节顺序事后宣称为 v8 Template Authority。

## 3. 职责映射

| v7 位置/概念 | v8 唯一归属 | 迁移动作 |
|---|---|---|
| `latex.md` 中的固定一级骨架 | `template_manifest.yaml` | 新项目按 manifest；旧项目保持原文件 |
| `latex.md` 中的普通正文写法 | `paper_writing_protocol.md` | 只在后续重写相关段落时采用 |
| 数学语义、证据和 claim 裁决 | `writing_reasoning_contract.yaml` | 保持现有事实，争议时加载完整 Authority |
| LaTeX 环境、路径、引用、编译 | `latex.md` Adapter | 可直接采用，不改变正文语义 |
| `required` | `displayed` | 仅状态解释映射，不自动增加标题 |
| `inline` | `inline` | 保持段内/邻近公式收束 |
| `not_applicable` | `omitted` | 不生成形式化汇总块 |
| 全文统一结果/验证章 | 各问题局部 RESULT / VALIDATE | 只在人工确认后迁移，禁止自动剪切正文 |

上述核心模型状态映射的机器权威仍为 `core/writing_reasoning_contract.yaml#v8_compatibility`；本表只是面向维护者的说明。

## 4. 人工迁移检查（默认 dry-run）

对已有项目先只生成检查结论，不写文件：

1. 识别当前 `main.tex` 的有效 include graph；
2. 列出已填写正文文件、一级标题和交叉引用；
3. 标出可映射到 v8 槽位的文件，不移动内容；
4. 检查目标路径是否已存在，任何冲突均停止；
5. 检查 `label`、`ref`、`cite`、图片和 BibTeX 依赖；
6. 由用户确认后，才逐章复制到新工程并重新审计、编译。

仓库不提供自动迁移脚本，因为仅凭文件名和标题无法安全判断题目专属正文边界。任何自动覆盖、自动拆段或自动删除旧正文都属于不支持行为。

## 5. 回滚

若 v8 工程迁移失败，保留原 v7 项目目录不变，删除或弃用单独创建的 v8 `final_latex/` 副本即可。Skill 仓库可回退到 v7.19.0；项目的模型、代码、工作簿和原论文正文不需要反向迁移。
