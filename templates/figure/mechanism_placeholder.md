# HSK 机理图占位兼容指针

> 状态：deprecated compatibility pointer。该路径仅用于旧项目、旧人工链接和历史维护脚本的路径兼容，不属于当前 Figure Authority，也不应进入默认运行链。

当前流程不再维护独立的“机理图合同 + DOCX/LaTeX 占位模板”规则。新项目或重新进入当前流程的旧项目应按以下职责读取：

- 是否需要机理图、图应回答什么问题、选择何种后端：`modules/04_figure_evidence.md`；
- 单张机理/推导图的当前合同：`templates/figure/mechanism_contract.md`；
- 每问图证据与论文位置规划：登记在项目根目录 `模型论文框架.md`，不再维护第二份独立规划表；
- 仅当 Backend Selection Gate 选择 draw.io 时，使用 `templates/figure/mechanism_drawio_spec.yaml`，实际生成或返修时再读取 `templates/figure/mechanism_drawio_patterns.md`；
- DOCX / LaTeX 的最终载体与题注、编号、排版分别服从当前对应 Artifact Pack / Adapter，不由本文件定义。

旧图位占位格式和早期后端列表已经保存在 `legacy/v616_sources/HSK_COMMON_TEMPLATES_V616.md` 与 `legacy/stage_v616/` 中，仅供历史追溯；当前运行不得从 legacy 恢复旧规则覆盖现行 Authority。
