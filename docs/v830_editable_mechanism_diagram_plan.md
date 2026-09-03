# v8.3.0 Editable Mechanism Diagram Production & Visual QA 修改计划

> 状态：**APPROVED / PLAN MERGED**
> 当前 Skill：`8.2.0`  
> 计划目标版本：`8.3.0`（候选，新增向后兼容的机理图生产与校验能力）  
> 计划基线：`main@aa7347116a970675b6c8a416898559cef8dbf7aa`  
> 计划分支：`docs/v830-editable-mechanism-diagram-plan`  
> 计划 PR：`#106`，已合并为 `6420817474d830d530833d2e56e97a419c83923e`
> 实施分支：`upgrade/v8.3.0-editable-mechanism-diagrams`，从上述干净 `main` 建立。
> 本计划 PR 只保存实施上下文；正式能力只有在独立功能 PR 完成全量验证并合并后才进入运行链。

---

## 目录

1. 背景与输入证据
2. 当前能力与真实缺口
3. 修改简报
4. Authority 与职责边界
5. 目标使用场景与明确排除项
6. 目标运行链
7. 绘图后端选择门
8. Mechanism Diagram Spec 设计
9. 可编辑 draw.io 生成器设计
10. 静态校验器设计
11. 渲染预览与人工语义 QA
12. 数据、模型与语义变更边界
13. 目录、产物与交付边界
14. 逐文件实施方案
15. 版本、兼容与迁移
16. 受保护语义冻结
17. 实施顺序
18. 测试矩阵
19. 验收标准
20. 风险与抑制措施
21. 回滚与后续扩展

---

## 1. 背景与输入证据

当前数学建模 Skill 已经具备较完整的 Figure Evidence 治理：图必须绑定核心结论、Evidence level、Primary question、模型/公式/约束、真实数据事实源、正文位置和 caption；结果图还必须经过 Scientific Figure Synthesis、Basic-form Challenge、Scientific Rendering Profile、Figure Layout Gate、Enhancement Gate 与 Portfolio Gate。

但机理图目前主要停留在“应该画什么、为什么画、必须绑定什么”的语义层。现有 `templates/matlab/draw_mechanism_structure.m` 只是节点—边骨架，没有形成稳定的可编辑图源、版式预检、渲染预览和返修闭环。实际使用时，Agent 即使知道某张机理图必须支撑公式或约束，也仍可能不知道如何把对象、状态、变量、边界和箭头关系落成可提交的图。

本计划参考了公开仓库 `jihe520/sci-box` 在 `main@9687d2a52037e92bf68a781b9b1e061ca03c8125` 的两类能力：

- `scibox-figure`：11 套 Python/Matplotlib 科研图型模板；
- `scibox-diagram`：可编辑 `.drawio` 生成、静态布局检查、预览、导出和人工复核流程。

只读审计和代表性运行确认：

1. `scibox-figure` 能输出 PNG/PDF/SVG，但模板主要使用确定性模拟数据和硬编码标签/指标；仓库中未发现 `read_excel` / `read_csv` 数据入口，也未发现该绘图 Skill 的自动化测试；
2. 代表性预测模板中，图内硬编码的 $R^2$/RMSE 与脚本生成点重新计算得到的值不一致；ROC 模板还包含未由统计检验产生的 `p<0.01` 文案；
3. `scibox-figure` 的自动导出、关闭图窗、固定面板标题、英文标签和跨面板颜色语义与当前 HSK Figure Authority 存在冲突；
4. `scibox-diagram` 的代表性示例可以生成 103 个图元的 `.drawio`，其静态检查返回 `FAIL 0 / WARN 0`；
5. `scibox-diagram` 中“可编辑源 + 机器可算几何检查 + 渲染后人工复核”的分层思想，对当前机理图实现层有直接参考价值；
6. 外部仓库未发现覆盖其自有脚本的顶层许可证，且代码包含 Claude 专属路径/工具字段，因此本计划不复制、移植、vendor 或运行时依赖其代码、模板、图标和资产。

结论：**吸收生产闭环，不吸收模拟数据；吸收可编辑与校验思想，不复制外部实现；保留现有 Figure Authority，不建立第二套机理图审美规则。**

---

## 2. 当前能力与真实缺口

### 2.1 当前已经具备

`modules/04_figure_evidence.md` 已经定义：

- 机理图优先表达公式来源、约束来源、临界状态和策略机制；
- 图中只保留对象、变量、方向、边界、距离、角度、流向和临界状态；
- 禁止用通用“输入—模型—输出”流程图替代题目专属机理图；
- 机理图必须绑定 Core question、Core conclusion、Model link、Formula link、Code link、Reviewer risk、Caption duty 和 Paper location；
- Figure Enhancement、颜色、视觉注意力和正式 caption 的通用规则；
- 正文引用、图注、框架登记和论文证据闭环。

现有 `templates/figure/mechanism_contract.md`、`mechanism_practical_check.md` 与 `mechanism_qa.md` 已覆盖：

- 题目对象、图型、核心问题和核心结论；
- 变量/假设/目标函数/约束/公式/代码链接；
- 图前六问、S/A/B 级判定和通用流程图负面清单；
- 公式、约束、临界状态、几何方向和正文引用检查。

`core/output_contract.yaml` 已经允许 `draw.io`、SVG、TikZ、PPT、GeoGebra 用于非数据驱动机理图。因此本计划不是引入一个此前被禁止的工具，而是补齐已有可选后端的生产和校验协议。

### 2.2 已确认的真实缺口

1. **Backend Selection Gap**  
   当前允许多种机理图工具，但没有说明何时选 draw.io、TikZ、MATLAB 或其他后端。Agent 容易把概念关系图、精确几何图和数据结果图混在一起。

2. **Editable Source Gap**  
   机理图合同允许填写 `Source=draw.io`，但没有规定可编辑源、正式导出、预览和内容规格之间的关系。

3. **Structured Authoring Gap**  
   当前只有自然语言合同，没有可供生成器读取的节点、边、分组、公式锚点、语义角色和画布布局规格。

4. **Deterministic Production Gap**  
   缺少从稳定规格生成未压缩 `.drawio` XML 的确定性入口。同一内容在不同对话中可能产生完全不同的坐标、颜色和连接方式。

5. **Machine-checkable Geometry Gap**  
   当前 QA 可以要求“无重叠、无溢出、箭头正确”，但没有低依赖脚本检查重复 ID、非法端点、越界、文字溢出风险、非预期重叠、连线穿越对象、内嵌位图和外部资源。

6. **Rendered Evidence Gap**  
   XML 合法不等于图可读。当前没有规定必须查看最新渲染预览后才能将机理图登记为 `approved_figures`。

7. **Semantic/Visual Boundary Gap**  
   当前 Model Approval 已排除 caption/formatting 变化，但机理图的“移动盒子”和“改变箭头方向”必须有明确不同的治理路径。

8. **Delivery Provenance Gap**  
   缺少可编辑源、预览、正式导出与所依据 Mechanism Contract/Spec 的最小 hash 绑定方式，同时又不能为此扩张 Project State 或建立平行 figure evidence 数据库。

---

## 3. 修改简报

```text
修改主题：Editable Mechanism Diagram Production & Visual QA
当前版本：8.2.0
目标版本：8.3.0
变更等级：minor
直接目标：为题目专属非数据驱动机理图增加可编辑 draw.io 规格、确定性生成、静态几何检查、渲染预览和人工语义复核闭环
明确不做：不复制 sci-box；不引入其模板/图标/代码；不替换 MATLAB 数据结果图；不改变模型/数值/工作簿 Authority；不新增 Project State 字段；不强制安装 draw.io CLI；不新增浏览器自动化；不把通用研究框架图当核心机理图
权威事实源：modules/04_figure_evidence.md；core/output_contract.yaml；core/model_approval_contract.yaml；当前 模型论文框架.md 与 Mechanism Contract
预计修改文件：Figure Authority、Figure Pack、现有机理图合同/QA、一个可选 Spec 模板、一个实现参考、生成器、校验器、最小路由/产物指针、测试、lint、版本载体、生成索引
禁止触碰文件：模型审批语义、数值验证、工作簿 Schema、Project State Schema、03A、03B、Writing Authority、Review Authority、LaTeX audit/compile、submission package allowlist、MATLAB 数据图所有权
兼容性要求：旧项目、旧 Mechanism Contract、qX_plot.m、data_process.m 和无 draw.io 环境继续可用；新字段可选；结果图路径不变
迁移要求：无强制迁移；只有新建或主动重绘的非数据驱动机理图使用 v1 Spec
验收测试：后端选择、Spec 结构、确定性 XML、几何负例、语义边界、无外部依赖、旧图兼容、路由最小加载、版本同步、生成文件、全量 CI
回滚方式：整体回滚单一 v8.3.0 功能 PR；既有模型、代码、工作簿、MATLAB 图和论文源无需迁移
```

---

## 4. Authority 与职责边界

本修改不得创建新的 Figure 语义 Authority。

| 职责 | Authority / Consumer | v8.3.0 边界 |
|---|---|---|
| 为什么画、画什么、证据层级、视觉与正文闭环 | `modules/04_figure_evidence.md` | 继续作为唯一 Figure Authority；新增机理图生产链与机器/人工边界 |
| 图表阶段适配 | `packs/artifact/figure.md` | 给出进入 draw.io 路径的摘要，不复制完整规则 |
| 模型、变量、假设、目标、约束与公式含义 | 当前 `模型论文框架.md` + 模型 Authority | draw.io Spec 只引用，不重新定义 |
| 机理图语义登记 | `templates/figure/mechanism_contract.md` | 保留现有合同并增加可编辑源/后端/证据字段；不另建平行合同 |
| 可生成的图元与关系规格 | 新增 `templates/figure/mechanism_drawio_spec.yaml` | 只是渲染输入，不是模型事实源 |
| draw.io 实现模式 | 新增 `templates/figure/mechanism_drawio_patterns.md` | 只提供图元、布局与导出参考，不拥有审美决策权 |
| `.drawio` 生成 | 新增 `scripts/generate_mechanism_drawio.py` | 只把已确认 Spec 变成可编辑 XML，不发明对象、变量、边或结论 |
| 结构/几何校验 | 新增 `scripts/validate_drawio_figure.py` | 只校验确定性结构与几何风险，不判定模型、箭头语义或审美正确性 |
| 语义变更与 Model Approval | `core/model_approval_contract.yaml` | 继续决定何时 stale；Figure 工具不得自行扩大语义类别 |
| 数据结果图 | `modules/04_figure_evidence.md` + MATLAB 合同 | 继续由 `qX_plot.m` / `data_process.m` 绘制；draw.io 不读取结果工作簿替代数据图 |
| 正式 LaTeX/交付 | 现有 LaTeX 与 submission Authority | 不改变包规则；`.drawio` 默认不是官方提交文件 |

目标关系：

```text
当前模型论文框架 + Mechanism Contract
                 ↓
Mechanism Diagram Backend Selection
                 ↓
draw.io Spec（渲染载体，不是语义事实源）
                 ↓
确定性 .drawio 生成
                 ↓
结构/几何静态校验
                 ↓
渲染预览 + 人工语义/视觉 QA
                 ↓
正式 PDF/SVG/PNG + Framework 图表登记
```

---

## 5. 目标使用场景与明确排除项

### 5.1 适用场景

draw.io 路径只面向非数据驱动、需要可编辑对象关系的题目专属图：

- 题目对象关系图；
- 机制作用链与状态转移图；
- 约束来源与可行/失效逻辑图；
- 临界状态、策略切换和决策分支图；
- 多对象交互、流向、反馈与信息传递图；
- 简化前后或假设边界对照图；
- 需要赛中快速修改文本、箭头和结构的矢量机理图。

### 5.2 不适用场景

- 数据驱动的折线、散点、分布、回归、敏感性、Pareto、空间场和网络权重图；
- 必须精确按数据坐标、误差、置信区间或数值网格绘制的图；
- 需要严格几何比例、坐标变换、切线或连续函数曲线的推导图；
- 正文算法伪代码与普通程序流程；它们继续服从 Algorithm Trace / algorithm-flow Pack；
- 只有“输入—处理—输出”且不能绑定本题对象、公式、约束或判定条件的通用流程图；
- 纯装饰研究框架、软件架构或答辩封面图。

### 5.3 核心准入条件

进入 draw.io 路径前至少满足：

1. Mechanism Contract 已回答图前六问；
2. 至少绑定一个模型变量/公式/约束/判定条件，或明确属于 A 级解释图；
3. 能列出题目专属对象与有方向含义的关系；
4. 不需要把真实数据序列伪装成示意图；
5. 可说明为什么 draw.io 比 MATLAB/TikZ/正文文字更合适。

---

## 6. 目标运行链

### 6.1 恢复当前语义

读取：

- 当前 `模型论文框架.md`；
- 对应小问 Problem Contract、selected/locked model、变量、假设、目标、约束和公式锚点；
- 当前 Mechanism Contract；
- 若图涉及已计算临界值，只读取 accepted 工作簿或框架中已绑定的当前结果，不自行计算新结果。

### 6.2 先完成图前设计

确定：

- Core question；
- Core conclusion；
- Diagram type；
- 必须出现与禁止出现的对象；
- 节点语义角色；
- 每条箭头的来源、去向、方向和关系含义；
- 公式/约束/代码锚点；
- 正文位置与 Caption duty；
- 选用 draw.io 的理由。

### 6.3 形成 Spec

把已确认内容写成最小机器可读 Spec。Spec 不能从外部模板填充虚构变量，也不能成为对模型事实的第二次人工转录源；所有语义字段必须可追溯到 Framework/Contract 锚点。

### 6.4 生成与静态检查

生成器输出未压缩 `.drawio`。随后校验器执行结构与几何检查。存在 blocking 结构错误时不得进入渲染审批。

### 6.5 渲染分流

- draw.io CLI 可用：导出 1:1 PNG 预览和 PDF/SVG 候选正式图；
- draw.io CLI 不可用：交付可编辑 `.drawio`，由用户在 draw.io/diagrams.net 打开并导出；在收到或查看渲染预览前，不得标记为 `approved_figures`。

### 6.6 人工复核

人工先审语义，再审版式：对象是否遗漏、箭头方向是否正确、变量是否与正文一致、临界状态是否准确，然后检查文字、重叠、穿线、字号、颜色、留白和 A4 缩放可读性。

### 6.7 入文闭环

正式导出通过后更新 Framework 图表登记、Caption、正文引用和 Figure Contract；只有已确认的正式 PDF/SVG/PNG 进入论文源，`.drawio`/Spec/预览属于内部编辑或复现材料。

---

## 7. 绘图后端选择门

| 图的真实任务 | 首选后端 | 选择依据 |
|---|---|---|
| 数据序列、误差、区间、分布、敏感性、Pareto、空间场 | MATLAB | 保持现有工作簿驱动和数据图所有权 |
| 精确坐标、解析几何、函数曲线、切线/角度/比例 | TikZ / MATLAB / GeoGebra | 需要数学坐标或几何精度，不能靠拖拽近似 |
| 题目对象、状态、反馈、约束来源、策略切换 | draw.io | 需要可编辑对象和关系，坐标主要服务结构表达 |
| 简单公式依赖链且需与 LaTeX 字体统一 | TikZ | 直接与论文公式环境一致 |
| 临时讨论草图 | PPT/手绘 | 只作草案，入文前转成正式后端 |

选择 draw.io 不能只因为“看起来高级”。如果一个简单、精确的二维几何图或 MATLAB 图更能证明结论，应否决 draw.io。

---

## 8. Mechanism Diagram Spec 设计

新增 `templates/figure/mechanism_drawio_spec.yaml`，作为可选渲染规格模板。建议结构：

```yaml
spec_version: 1.0.0
figure_id: MF-Q1-01
question_id: Q1
diagram_type: mechanism_relation
core_question: null
core_conclusion: null
framework_anchor: null
backend: drawio
layout_mode: explicit

semantic_anchors:
  model: []
  formulas: []
  constraints: []
  assumptions: []
  code: []
  result_evidence: []

canvas:
  width: 1000
  height: 700
  orientation: landscape
  target_use: paper
  target_width_mm: 150

groups: []
nodes: []
edges: []

artifact:
  editable_source: null
  preview: null
  final_exports: []
  spec_sha256: null
  drawio_sha256: null
  preview_sha256: null
  validation_status: pending
  visual_review_status: pending
```

### 8.1 稳定枚举

`diagram_type`：

- `object_relation`
- `mechanism_relation`
- `constraint_logic`
- `critical_state`
- `strategy_switch`
- `comparison_boundary`

`layout_mode`：

- `explicit`
- `layered_lr`
- `layered_tb`

`node.semantic_role`：

- `object`
- `state`
- `variable`
- `condition`
- `constraint`
- `boundary`
- `decision`
- `outcome`
- `context`

`edge.relation_type`：

- `causes`
- `constrains`
- `transforms`
- `depends_on`
- `flows_to`
- `switches_to`
- `compares_with`
- `feedback`
- `custom`

这些枚举只描述图元语义角色，不新增模型分类。

### 8.2 Node 最小字段

```yaml
- id: n_target
  label: 目标对象
  semantic_role: object
  symbol_refs: [T]
  source_anchor: 模型论文框架.md#Q1-变量
  group_id: null
  shape: rounded_rect
  emphasis: primary
  geometry: {x: 80, y: 120, width: 180, height: 70}
```

要求：

- ID 唯一且稳定；
- label 使用题目/模型当前术语；
- 变量只引用当前符号，不在 Spec 中重新定义含义和单位；
- 非装饰节点必须有 `source_anchor`；
- `context` 节点不得抢占核心视觉层级；
- 不允许保留 `节点1`、`输入`、`模型`、`输出` 等未具体化占位内容进入正式图。

### 8.3 Edge 最小字段

```yaml
- id: e_occlusion
  source: n_occluder
  target: n_target
  relation_type: constrains
  direction: forward
  label: 遮蔽约束
  source_anchor: 模型论文框架.md#式-6
  formula_refs: [F6]
  waypoints: []
```

要求：

- source/target 必须指向已存在节点；
- 有向关系必须声明方向；
- `custom` 必须提供非空 label；
- 与公式/约束有关的边必须给出锚点；
- 反馈必须明确是双向、闭环还是返回某状态；
- 机器只能检查字段闭合，不能证明箭头含义正确。

### 8.4 布局字段边界

- `explicit` 用于几何、边界、临界状态和复杂题目专属关系；
- `layered_lr/tb` 只用于简单抽象关系初稿，生成后仍须人工调整；
- 自动布局不允许改变边方向、合并节点或省略对象；
- 位置、颜色、圆角和线宽属于渲染信息，不进入模型语义；
- 节点/边的对象、方向、条件、符号和锚点属于语义信息。

---

## 9. 可编辑 draw.io 生成器设计

新增 `scripts/generate_mechanism_drawio.py`：

```bash
python scripts/generate_mechanism_drawio.py \
  --spec figures/source/q1_occlusion.mechanism.yaml \
  --output figures/source/q1_occlusion.drawio

python scripts/generate_mechanism_drawio.py --spec ... --check
```

### 9.1 必须行为

- 使用仓库已有 Python 依赖，不新增 draw.io Python SDK；
- 读取 v1 Spec 并执行严格字段/枚举/ID/端点/几何校验；
- 生成未压缩、可读、稳定排序的 `mxGraphModel` XML；
- 同一 Spec 在同一版本中产生完全相同的 `.drawio` 字节；
- 使用基础矢量图元，不嵌入位图、远程图标、外链脚本或数据 URI；
- XML 中保留稳定节点/边 ID，方便后续定点修改；
- `--check` 只验证，不写文件；
- 默认不自动导出或关闭外部应用；
- 不读取工作簿、不计算模型、不生成数字、不修改 Framework/Project State。

### 9.2 视觉实现边界

- 只内置一套克制的论文级基础视觉语法，而不是四套固定研究框架模板；
- 颜色语义服从 Module 04：核心对象高对比、辅助对象降权、风险/可行方向保持一致；
- 不允许任意彩虹、拟物阴影、渐变装饰或大面积无语义色块；
- 默认字体、字号和线宽根据 `target_use` 与 `target_width_mm` 计算，不直接复制外部仓库像素常量；
- 不预置任何赛题对象、变量、方法名称、模型名称或通用输入—输出节点。

### 9.3 非目标

- 第一版不实现任意图自动美化；
- 不实现复杂图标库；
- 不实现 OCR、参考图复刻或像素级差分；
- 不实现网络自动布局库或 Graphviz 依赖；
- 不承诺所有 draw.io 文件都能由生成器无损反向还原为 Spec。

---

## 10. 静态校验器设计

新增 `scripts/validate_drawio_figure.py`：

```bash
python scripts/validate_drawio_figure.py figure.drawio
python scripts/validate_drawio_figure.py figure.drawio --spec figure.mechanism.yaml
python scripts/validate_drawio_figure.py figure.drawio --spec ... --strict
```

### 10.1 Blocking 检查

- XML 无法解析或不含唯一 `mxGraphModel`；
- v1 不支持的压缩 payload；
- 重复/空 ID；
- Spec 节点/边在 `.drawio` 中缺失；
- edge source/target 不存在；
- 图元越出画布或被裁切；
- 文字按保守宽度模型确定性溢出；
- 非容器实体发生实质矩形重叠；
- 明确线段穿过无关实体盒；
- 内嵌位图、远程图片、外部 URL、脚本或 `data:image`；
- 声明的正式导出/预览路径不符合项目相对路径规则；
- Spec/drawio hash 声明与当前文件不一致。

### 10.2 Review-required / Warning 检查

- 字号在目标论文宽度下可能过小；
- 字号、线宽、形状或填充色种类过多；
- 连接器端点压边；
- 疑似空盒或遗留占位词；
- 主要对象过多、画布长宽比极端或留白比例异常；
- 节点有 symbol/formula 但图中未出现可恢复标识；
- 声明预览但预览 hash 未更新；
- 只有 `.drawio` 而没有经过渲染视觉复核。

### 10.3 刻意不自动判断

- 箭头方向是否符合真实机制；
- 变量、公式、约束是否数学正确；
- 是否遗漏关键对象或不利状态；
- 布局是否美观、视觉重心是否合理；
- 颜色是否符合特定赛题语义；
- 临界状态是否画在真实位置；
- 图是否足以支撑正文 claim；
- 两条线在复杂 draw.io 路由中是否视觉相交但语义允许。

这些内容必须由人工语义 QA 完成。静态脚本不得输出“数学正确”或“机理已验证”。

### 10.4 输出

默认输出终端摘要和退出码；可选 `--json` 输出结构化结果到 stdout。第一版不默认创建独立 audit 文件，避免违反当前“默认不生成独立 figure_evidence 文件”的项目原则。需要持久记录时，把状态、hash 和主要 finding 写入现有 Mechanism Contract/Framework 图表登记。

---

## 11. 渲染预览与人工语义 QA

### 11.1 渲染状态

机理图状态至少区分：

```text
spec_draft
→ drawio_generated
→ structure_checked
→ preview_rendered
→ visual_reviewed
→ approved_for_paper
```

不得把 `structure_checked` 等同于 `approved_for_paper`。

### 11.2 人工复核顺序

#### 第一层：语义真实性

1. 每个对象是否来自当前题目/模型；
2. 箭头方向是否与因果、约束、流向或状态切换一致；
3. 符号、上下标、单位和正文是否一致；
4. 临界、可行/不可行、风险/安全侧是否画反；
5. 是否遗漏反例、边界或关键反馈；
6. 图中数值是否来自已验收事实源；
7. 是否确实能绑定声明的公式、约束或判断函数。

#### 第二层：可读性与版式

1. 文字是否溢出、过小、被线穿过；
2. 同族图元是否对齐、同宽、间距一致；
3. 族间留白是否大于族内留白；
4. 核心对象是否比辅助对象更显著；
5. 颜色是否稳定且不靠红绿单独表达；
6. 箭头是否有明确端点、方向和分支/汇流结构；
7. A4/双栏缩放后是否仍可读；
8. 是否存在装饰节点、重复文字和通用流程口号；
9. 最新修改是否引入新的重叠、错向或遗漏。

### 11.3 预览不可用时

如果无法获得任何渲染预览：

- 可以交付 `.drawio` 草稿供用户打开；
- 可以报告结构检查结果；
- 不得报告“机理图已完成”或加入 `approved_figures`；
- 必须明确等待用户渲染/截图后继续 QA。

---

## 12. 数据、模型与语义变更边界

### 12.1 不改变模型语义的修改

- 移动节点但关系不变；
- 调整画布、间距、字体、颜色、线宽、圆角；
- 文字换行但术语和含义不变；
- 更换箭头路径但 source/target/direction 不变；
- PDF/SVG/PNG 导出设置；
- caption-only、编号或文件名调整。

这些变化不递增模型 `semantic_revision`，不使 `locked_model_spec` stale，不触发重新 Model Approval、03A 或 03B 重算；但正式图和论文引用仍需刷新并保持 hash/mtime current。

### 12.2 必须进入语义审查的修改

- 新增、删除或替换模型对象/状态/变量；
- 改变边的 source、target、direction 或关系类型；
- 改变公式、约束、假设、阈值或判定条件的含义；
- 把相关关系改写成因果关系；
- 改变反馈、先后、包含、约束或可行侧；
- 添加没有来源的新数值、新机制或新结论。

处理规则：

- 若图原先画错而模型/Framework 已正确：修图并刷新 Figure Evidence，不修改模型语义；
- 若修图暴露 Framework 与模型本身有冲突：按现有 semantic change category 回退模型设计/求解；
- draw.io 工具不得自行决定哪一种情况成立，必须比较当前 Authority 和证据。

### 12.3 数值边界

- draw.io 只允许展示已确认数值、阈值和单位；
- 不从论文摘要或图片反推数据；
- 不在生成器中求解、插值、平滑、回归或重算；
- 数据驱动图继续由 MATLAB 从标准工作簿生成。

---

## 13. 目录、产物与交付边界

### 13.1 建议项目路径

第一版使用项目级 `figures/`，不改变每问五文件结构：

```text
figures/
├── source/
│   ├── q1_<slug>.mechanism.yaml
│   └── q1_<slug>.drawio
├── preview/
│   └── q1_<slug>.png
├── q1_<slug>.pdf
└── q1_<slug>.svg
```

- `source/` 和 `preview/` 是内部编辑/复核材料；
- 根级正式 PDF/SVG/PNG 供 LaTeX/DOCX 使用；
- 不把这些文件塞进 `问题X求解/`，避免破坏固定五文件交接；
- 不因启用 draw.io 要求所有项目创建这些目录；
- 没有机理图或不使用 draw.io 时目录完全不出现。

### 13.2 文件命名

- 使用 ASCII 小写 slug；
- 题号前缀稳定，如 `q1_occlusion_boundary`；
- 中文正式图名只进入 caption/Framework；
- 同一 Figure 的 Spec、drawio、preview 和正式导出共享 stem。

### 13.3 正式提交包

- `.drawio`、Spec 和 preview 默认不加入只允许 PDF 的 official package；
- reproducibility package 是否包含可编辑源，继续服从现有 submission Authority 和用户明确要求；
- 本次不修改 official package allowlist；
- 不新增 submission manifest 字段。

---

## 14. 逐文件实施方案

### 14.1 `modules/04_figure_evidence.md`

作为唯一 Authority，新增：

- Mechanism Diagram Backend Selection Gate；
- draw.io 的适用/不适用范围；
- Spec → generate → validate → preview → semantic QA → export 链；
- 机器几何检查与人工语义审查边界；
- 可编辑源、预览、正式导出和 Framework 登记关系；
- 纯视觉修改与语义修改分流；
- 无预览不得标记 approved。

不得复制具体 XML 实现、像素常量和检查器算法。

### 14.2 `packs/artifact/figure.md`

- 增加机理图进入 draw.io 路径的短摘要；
- 引用 Module 04、现有 Mechanism Contract 和新 Spec/Patterns；
- 保持 MATLAB 数据图段落不变；
- 不在 Pack 重复后端选择和 QA 全规则。

### 14.3 现有 Mechanism Contract 与 QA

`templates/figure/mechanism_contract.md` 增加：

- Backend selection 与理由；
- Diagram type；
- Semantic anchors；
- Editable source / Spec / Preview / Formal exports；
- Spec/drawio/preview hash；
- Structure validation status；
- Visual review status；
- 是否属于纯视觉修改或语义修改。

`mechanism_qa.md` 与 `mechanism_practical_check.md` 只补 draw.io 必需的机器/人工检查，不另建第四份完整 QA。

### 14.4 新 Spec 与实现参考

- `templates/figure/mechanism_drawio_spec.yaml`：最小机器可读渲染规格；
- `templates/figure/mechanism_drawio_patterns.md`：图元、连接器、分支/汇流、边界、状态切换、字体缩放和 CLI/人工导出参考。

Patterns 只说明实现方式，不定义哪些图应该画。

### 14.5 新脚本

`scripts/generate_mechanism_drawio.py`：

- 严格读取 Spec；
- 生成确定性未压缩 XML；
- 支持 `--check`；
- 不生成语义、不读取数据、不依赖网络。

`scripts/validate_drawio_figure.py`：

- 解析 Spec/XML；
- 执行确定性结构/几何/安全检查；
- 支持 human-readable 与 JSON stdout；
- 严格区分 blocking/review_required/warning；
- 不宣称语义或数学正确。

第一版不新增单独 render wrapper；文档给出 draw.io CLI 可用时的标准导出命令，CLI 不可用时走用户预览分支。

### 14.6 路由与产物指针

`core/workflow_router.yaml`：

- 为 `draw.io / drawio / 可编辑机理图 / 约束关系图 / 临界状态图` 补充精确触发；
- figure route 只增最小按需加载指针；
- 不让普通结果图无条件加载 draw.io patterns。

`core/module_manifest.yaml`：

- 将 Mechanism Spec、editable source、preview/exports 作为可选 Figure outputs；
- 不增加新 workflow stage。

`core/output_contract.yaml`：

- 在现有 `other_figure_tools` 基础上补 draw.io 项目路径与交付边界；
- 保持每问五文件、MATLAB figure contract 和官方包不变。

### 14.7 Lint 与测试

`scripts/lint_skill_checks.py` 只增加稳定合同检查：

- Module 04 保持单一 Authority；
- 新脚本、Spec、Patterns 和路由指针存在；
- MATLAB 数据图所有权未变化；
- 外部 `sci-box` 路径、代码、模板和图标未进入仓库；
- Project State、Model Approval、submission allowlist 未被扩大；
- 生成器模板不含“输入/模型/输出”等默认占位节点。

新增 `tests/test_v830_editable_mechanism_diagram.py`，并只在现有 ownership/tooling/current-health 测试中补必要集成断言。

### 14.8 版本载体

专项测试通过后按现有 release 规则同步 `8.3.0`：

- `.codex-plugin/plugin.json`；
- `SKILL.md`；
- `skills/mathmodel-skill/SKILL.md`；
- `core/bootstrap.yaml`；
- `core/hsk_core_policy.md`；
- `core/workflow_router.yaml`；
- `core/module_manifest.yaml`；
- `core/output_contract.yaml`；
- 其他由 current-health 测试明确要求的当前 release carriers；
- `README.md`；
- `CHANGELOG.md`。

禁止全仓库盲目替换历史版本文本。

### 14.9 生成文件

只通过 `scripts/generate_indexes.py` 刷新：

- `SKILL_FILE_INDEX.md`；
- `TEMPLATE_INDEX.md`；
- `MANIFEST.sha256`；
- 其他生成器确实产生变化的 compatibility index。

禁止手工修改 hash。

---

## 15. 版本、兼容与迁移

### 15.1 版本判断

该修改新增：

- 可选 Mechanism Diagram Spec；
- 可编辑 draw.io 生成能力；
- 结构/几何校验 CLI；
- 新的机理图生产与 QA 路由。

现有接口仍可用，因此候选版本为：

```text
8.2.0 → 8.3.0
```

### 15.2 旧项目

- 旧 Mechanism Contract 继续可读；
- 不要求补 Spec、drawio 或 hash；
- 原 MATLAB 结果图、预处理图和机理图骨架继续可用；
- 不新增 Project State 必填字段；
- 不改变 Framework schema/version；
- 不改变每问五文件；
- 不改变 LaTeX、compile report、submission manifest 或 package validator。

### 15.3 新项目

只有选择 draw.io 的机理图才使用 v1 Spec。选择 TikZ/MATLAB/GeoGebra/PPT 的图继续使用现有 Mechanism Contract 和 QA，不被强制迁移到 draw.io。

### 15.4 未来兼容

v1 只承诺生成器输出的未压缩 `.drawio`。用户手工保存为压缩格式时，校验器应明确报告“不支持的格式”，而不是误判图损坏。是否支持压缩 payload 留待后续独立评估。

---

## 16. 受保护语义冻结

以下 blob SHA 来自 `main@aa7347116a970675b6c8a416898559cef8dbf7aa`。计划合并后，实施前必须从最新 `main` 重新冻结。

### 16.1 必须逐字节保持的模型、数值、写作和交付 Authority

| 受保护文件 | 基线 blob SHA |
|---|---|
| `core/model_approval_contract.yaml` | `7d97255dde9cf780755bab896964e905066bf4b8` |
| `core/numerical_verification_contract.yaml` | `b901923edf38112cbc922f51d1157265fe1931bd` |
| `core/workbook_schema.yaml` | `2422bbfa8cb3fad3b5b04c12de21c954ec8b3723` |
| `core/project_state.schema.yaml` | `fa12de39d7bbdc2e014b2912a186834b941b28d4` |
| `core/writing_reasoning_contract.yaml` | `adb962b3b764c08f78fdb002b97401adde693856` |
| `modules/03_solve_validate.md` | `f49480d96e6a491255010868e409b2d64d620f5e` |
| `modules/03_result_analysis.md` | `f43d21dc99d71e6b19baeec7af66cbf334da13a7` |
| `modules/05_writing/paper_writing_protocol.md` | `5404b1dc891227249644b040c40482bd6065b81a` |
| `modules/05_writing/ai_cleanup.md` | `c5200f4f1513c6770952284ac2d49e3db7bef273` |
| `modules/06_review_delivery.md` | `845350d958628e69d8d779f7d92542756a6da8e6` |
| `config/competition_profiles.yaml` | `fcddec42a30ad4d4bc760dc8322cc13a998a6ebd` |
| `scripts/validate_semantic_governance.py` | `481199d1d0b541eacd0ddd3b3794c301aac6e690` |
| `scripts/validate_submission_package.py` | `47bd01db5f45dd8c902418be62f494419a03c676` |

### 16.2 第一版必须保持的现有绘图实现与选择规则

| 受保护文件 | 基线 blob SHA |
|---|---|
| `templates/matlab/q1_plot.m` | `b9e67798051b1a130d2df11bca20e3976de0a6c2` |
| `templates/matlab/draw_mechanism_structure.m` | `65ba4a3b3462a565f86880c49af0959edd21f9a4` |
| `templates/figure/chart_selection.md` | `ba293a44f3ce4e0162c22e224ba33fd0ec94c048` |
| `templates/figure/figure_enhancement_patterns.md` | `d2fb8bc7b1d61556b9453682c4102b0e08ea246a` |
| `scripts/validate_code_delivery.py` | `d7b2593a72d6ab4f9a297e46f77f1922c405c128` |

第一版不把 draw.io 扩张为数据图后端，不重写已有 MATLAB 模板。

### 16.3 允许按计划修改的核心基线

| 目标文件 | 基线 blob SHA | 允许变化 |
|---|---|---|
| `modules/04_figure_evidence.md` | `3a34af07c7c8f58769e28dc22ab3b712481107f7` | 后端选择、draw.io 生产链、机器/人工边界、视觉/语义分流 |
| `packs/artifact/figure.md` | `c51781612cdcdda2067658ab94a61ed3818f7b79` | 最小适配与指针 |
| `templates/figure/mechanism_contract.md` | `2e021d9f868ee2aabdc9944564697e0d2df1f032` | 后端、源/预览/导出/hash/状态字段 |
| `templates/figure/mechanism_qa.md` | `810a5d7330f4178b456d7076b553eee22c0e1d54` | 渲染后语义与版式 QA |
| `templates/figure/mechanism_practical_check.md` | `f9969564606816f7bceb144805c4ad7e5d7b07aa` | draw.io 准入和负面检查 |
| `core/workflow_router.yaml` | `85c23bd5f50b560b3734b203deff6784c1fb0c92` | 精确触发与按需指针 |
| `core/module_manifest.yaml` | `1bf8023038628646c0347ad2fd6b18b8d08ba99b` | 可选产物与合同指针 |
| `core/output_contract.yaml` | `5485f54024c712fe229601fa173a4264fb120619` | draw.io 路径/交付边界；MATLAB 规则不变 |
| `scripts/lint_skill_checks.py` | `8671820981237b38c904b048cd2b413f90bbed66` | 最小静态合同检查 |

Release carriers 只允许版本、能力摘要和必要指针变化。

---

## 17. 实施顺序

### 阶段 A：计划批准与干净基线

1. 本计划 PR 不写功能；
2. 用户审阅并明确批准；
3. 计划进入 `main`；
4. 从最新 `main` 重查版本、提交、开放 PR 与 Authority；
5. 重新冻结受保护 SHA；
6. 创建独立 `upgrade/v8.3.0-editable-mechanism-diagram`。

### 阶段 B：先写失败测试

1. Spec 正向/反向结构测试；
2. 生成器确定性与 `--check` 测试；
3. draw.io XML 可解析与 ID/端点测试；
4. 越界、溢出、重叠、穿盒、位图/URL 测试；
5. CLI 无预览分支测试；
6. 纯视觉/语义修改边界文本合同测试；
7. MATLAB ownership、Project State 和 package allowlist 防漂移测试。

### 阶段 C：最小实现

1. 新增 Spec 模板；
2. 实现 Spec 校验与确定性 XML 生成；
3. 实现独立静态 validator；
4. 使用 3--4 个题目专属测试夹具验证不同拓扑；
5. 更新 Mechanism Contract/QA；
6. 更新 Module 04 与 Figure Pack；
7. 最小接入 router/manifest/output contract。

### 阶段 D：真实闭环演练

至少构造：

- 对象—约束关系图；
- 临界状态对照图；
- 带反馈的机制图；
- 一个故意错向、溢出或穿盒的负例。

对正例执行 Spec → drawio → validator → preview → manual QA。测试内容必须题目专属，不能使用通用“输入—模型—输出”作为成功样例。

### 阶段 E：版本与生成文件

1. 确认功能边界未扩大；
2. 同步 release carriers 到 `8.3.0`；
3. 更新 README/CHANGELOG；
4. 运行生成器；
5. 检查生成差异只包含预期索引/hash。

### 阶段 F：全量验收

1. 基础 lint、完整单元测试、生成文件检查；
2. draw.io 专项测试和代表性 CLI 演练；
3. 三套 LaTeX 与 Production attestation；
4. 受保护 SHA 比较；
5. root/package Skill byte parity；
6. 版本载体同步；
7. 检查无外部代码、资产、临时图片和无关格式化；
8. 全部 CI 通过后才合并；
9. 合并后执行 current-main 健康审计。

---

## 18. 测试矩阵

### 18.1 Spec 正向测试

- 六种 diagram type 均可表达；
- explicit/layered_lr/layered_tb 均产生合法 XML；
- 节点/边顺序变化经过规范化后输出稳定；
- 中文、变量下标、单位和换行正确转义；
- group/container 不被误判为实体重叠；
- source anchors、formula refs 和 artifact 字段完整保留。

### 18.2 Spec 反向测试

- 重复 node/edge ID 失败；
- 未知枚举失败；
- edge 指向不存在节点失败；
- 非装饰节点缺 source anchor 失败；
- custom relation 缺 label 失败；
- explicit geometry 缺坐标/尺寸失败；
- 负宽高、非法画布、越界失败；
- 正式状态仍含占位符失败；
- hash 声明不匹配失败。

### 18.3 生成器测试

- 同一 Spec 两次输出 SHA-256 完全一致；
- `--check` 不写文件；
- 输出为未压缩 XML；
- 不含位图、URL、脚本、外部字体或远程资产；
- 只使用标准基础图元；
- 不读取 Excel/CSV，不调用求解器；
- 不修改输入 Spec、Framework 或 Project State。

### 18.4 静态几何测试

- 文字宽/高确定性溢出；
- 图元越界；
- 非容器盒重叠；
- 明确折线穿盒；
- 端点压边 warning；
- 多字号/多颜色 warning；
- 空盒/占位内容 warning；
- 缺预览状态不能进入 approved；
- `--strict` 把 review-required/warning 转为非零退出按合同执行。

### 18.5 语义边界测试

- Module 04 明确机器不判箭头语义/数学正确；
- 纯布局变化不触发 Model Approval；
- 节点/箭头/公式/约束含义变化必须比较当前语义 Authority；
- draw.io 不能成为模型/数值事实源；
- 无 accepted 数值来源时不得在图中生成阈值；
- 通用研究框架不得成为核心机理图成功夹具。

### 18.6 兼容与防漂移

- 旧 Mechanism Contract 仍可使用；
- 无 draw.io 环境的 figure route 仍可完成 MATLAB/TikZ 路径；
- `qX_plot.m`、`data_process.m` 和每问五文件不变；
- Project State schema 不变；
- Model Approval 与 semantic categories 不变；
- Writing/Review/LaTeX/submission Authority 不变；
- official package allowlist 不变；
- root/package Skill byte parity；
- release carriers 均为 8.3.0；
- 生成索引与 Manifest current。

### 18.7 必跑命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python -m unittest tests.test_python_matlab_ownership
python -m unittest tests.test_v830_editable_mechanism_diagram
python scripts/generate_mechanism_drawio.py --spec <fixture> --check
python scripts/validate_drawio_figure.py <fixture.drawio> --spec <fixture> --strict
```

### 18.8 必须通过的 CI

- Static contract lint
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- Generated file contract
- LaTeX CUMCM
- LaTeX MCM-ICM
- LaTeX Diangong
- Production LaTeX attestation

---

## 19. 验收标准

v8.3.0 只有同时满足以下条件才算完成：

1. Agent 能基于当前模型/公式/约束选择正确绘图后端；
2. draw.io 只用于适配的非数据驱动机理图；
3. Spec 中每个核心节点/边都能追溯到当前 Framework/Contract；
4. 同一 Spec 产生完全一致的 `.drawio`；
5. `.drawio` 保持可编辑且不嵌入外部/位图资产；
6. 静态 validator 能捕获结构和几何负例；
7. validator 不越权判断数学、因果、箭头语义或审美；
8. 未查看渲染预览的图不能进入 `approved_figures`；
9. 人工 QA 明确先检查语义，再检查版式；
10. 图中数值只能来自已验收事实源；
11. 不复制或依赖 `sci-box` 的代码、模板、图标和路径；
12. MATLAB 数据结果图和每问五文件保持不变；
13. Project State、Model Approval、Workbook、03A、03B、Writing、Review、LaTeX 与 submission Authority 无漂移；
14. 旧项目无强制迁移；
15. release carriers 全部同步到 8.3.0；
16. 生成文件由生成器产生且 current；
17. 全量测试和 CI 通过；
18. PR 不混入 Python 数据绘图模板、参考图复刻、图标库或无关重构。

---

## 20. 风险与抑制措施

| 风险 | 抑制措施 |
|---|---|
| 把通用流程图包装成核心机理图 | 保留图前六问、题目专属对象和公式/约束锚点 Hard 准入 |
| draw.io 与 MATLAB 数据图争夺职责 | Backend Selection Gate + ownership 测试锁死 |
| Spec 成为第二套模型事实源 | 所有语义字段只引用 Framework/Contract；冲突时 Authority 优先 |
| 自动布局改变语义 | 生成器不得改变节点、端点、方向、关系类型；自动布局仅排坐标 |
| 几何检查被误报为语义正确 | 输出用词限定为结构/几何检查；人工 QA 必须独立通过 |
| 文字宽度启发式误报 | blocking 只用于确定性溢出；边界情形降为 review_required |
| draw.io CLI 不可用阻断 Skill | CLI 可选；无 CLI 时交付 editable source 并等待用户预览 |
| 外部代码许可证不清 | clean-room 原创实现，不复制代码/资产/常量/模板 |
| 生成文件污染项目目录 | 只有选择 draw.io 时创建 `figures/source`/`preview`；不改每问目录 |
| 可编辑源进入 official package | 明确内部/复现属性，official allowlist 保持不变 |
| 图中出现未验证数值 | Spec 要求 result evidence anchor；生成器不计算数值 |
| 视觉调整错误触发模型重算 | 明确 pure visual 与 semantic edit 分流 |
| 语义箭头改错却被当成布局修改 | 比较 source/target/direction/relation_type；人工语义 QA |
| 模板数量膨胀 | 第一版只提供一套基础视觉语法和三种布局模式，不建大图型库 |
| Skill 上下文继续膨胀 | Module 只保留决策规则，Patterns/Spec/脚本按需加载 |

---

## 21. 回滚与后续扩展

### 21.1 回滚

若生成器、校验器或 draw.io 路由造成误判或兼容问题：

1. 整体回滚单一 v8.3.0 功能 PR；
2. 删除新 Spec/Patterns/脚本与路由指针；
3. 旧项目继续使用现有 Mechanism Contract 与 MATLAB/TikZ/PPT/draw.io 手工路径；
4. 不回滚模型、代码、工作簿、结果图、论文源和 Project State；
5. 重新生成索引/Manifest并运行全量测试。

### 21.2 后续独立评估

以下能力不属于第一版：

- 支持 draw.io 压缩 payload；
- 自动调用 diagrams.net 在线服务；
- 浏览器自动化预览；
- OCR/参考图高保真复刻；
- 图标库、外部 SVG 资产和第三方模板；
- Graphviz/ELK 等复杂自动布局依赖；
- 像素级或结构级参考图差分；
- 从论文文本自动推断节点与因果边；
- Python/Matplotlib 正式数据图后端；
- 把 draw.io audit 写入 Project State 或正式 attestation hash 链；
- 更改 official/reproducibility package 规则。

这些能力只有在真实使用证明必要、许可证清晰、误报可控且不破坏 Authority 时，才能另写计划。

---

## 计划批准后的准确状态语义

本计划进入 `main` 只表示实施范围获得仓库级上下文，不表示 v8.3.0 已实施：

```text
详细计划      ✅ 已写入 / 待批准或已批准
计划入 main   ⏳ 取决于计划 PR 状态
实施前冻结    ⏳ 计划合并后从最新 main 重做
v8.3.0实施    ⏳ 尚未写入
v8.3.0 PR     ⏳ 尚未建立
完整 CI       ⏳ 尚未执行
最终健康审计  ⏳ 尚未执行
正式 Skill    8.2.0（直到功能 PR 合并并验证）
```

不得把“已有 draw.io 计划”“计划已批准”或“计划已合并”表述为可编辑机理图能力已经进入正式运行链。
