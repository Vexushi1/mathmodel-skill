# Mechanism draw.io 实现参考

本文件只提供 `templates/figure/mechanism_drawio_spec.yaml` 的实现模式。是否需要机理图、画什么以及图能否入文，由 `modules/04_figure_evidence.md` 决定；本文件不是第二套 Figure Authority。

## 1. 使用顺序

1. 从 current `模型论文框架.md` 和 Mechanism Contract 恢复对象、变量、公式、约束、判断条件与结论。
2. 通过 Module 04 的 Mechanism Diagram Backend Selection Gate。数据驱动图继续由 MATLAB 从已验收工作簿绘制。
3. 复制 Spec 模板到项目级 `figures/source/qX_<slug>.mechanism.yaml`，替换其中全部题目专属内容。
4. 运行生成器产生未压缩、可编辑 `.drawio`。
5. 运行静态校验器，只采信其结构、几何和安全检查。
6. 用 diagrams.net/draw.io 打开并渲染，查看最新预览；先做语义 QA，再做版式 QA。
7. 人工审查通过后导出 PDF/SVG/PNG，并更新 Mechanism Contract 和 Framework 图表登记。

生成与校验：

```bash
python scripts/generate_mechanism_drawio.py \
  --spec figures/source/q1_occlusion.mechanism.yaml \
  --output figures/source/q1_occlusion.drawio

python scripts/validate_drawio_figure.py \
  figures/source/q1_occlusion.drawio \
  --spec figures/source/q1_occlusion.mechanism.yaml
```

`--check` 只校验 Spec 并在内存中生成，不写文件。`validate_drawio_figure.py --strict` 会让尚待人工预览、视觉复核或普通 warning 以退出码 2 返回；blocking 使用退出码 1。

`spec_sha256` 只绑定会影响图内容与渲染的 Spec 部分，不包含生成后才更新的 artifact 路径、hash 和审查状态，避免形成自引用；`drawio_sha256` 与 `preview_sha256` 分别绑定当前可编辑源和渲染表面。

## 2. 后端选择

| 证据结构 | 首选后端 | 判断依据 |
|---|---|---|
| 对象关系、机制链、反馈、状态切换、约束来源 | draw.io | 关系离散且赛中需要快速编辑节点、箭头和文字 |
| 工作簿驱动的结果、敏感性、误差、空间场 | MATLAB | 坐标、数值、区间和统计量必须来自真实表格 |
| 精确二维几何、连续曲线、切线或坐标推导 | MATLAB / TikZ / GeoGebra | 需要比例、坐标或解析几何精度 |
| 简短公式依赖且需紧贴 LaTeX 字体 | TikZ | 与公式排版直接一致 |
| 临时讨论草图 | PPT / 手绘 | 只能作为草案，入文前转为正式后端 |

不要因为 draw.io 可编辑就把所有图改成盒箭图。一个直接二维图已经能准确证明结论时，应使用更直接的后端。

## 3. Spec 建模边界

- `semantic_anchors` 只引用现有 Authority，不在 Spec 重写模型定义。
- 每个非装饰节点都给出 `source_anchor`；边也必须能回到公式、约束、状态定义或题面关系。
- `symbol_refs` 与 `formula_refs` 使用 Framework 已登记标识，不重新定义变量含义和单位。
- 图中阈值或数字必须来自已验收事实源，并在 `semantic_anchors.result_evidence` 登记。
- `geometry`、颜色、圆角和路径是渲染信息；节点对象、边端点、方向、关系类型和条件是语义信息。
- 禁止把相关关系擅自改成因果关系，也禁止由生成器自动补节点、边或结论。

稳定枚举以生成器实现为准。常用选择：

- `diagram_type`：`object_relation`、`mechanism_relation`、`constraint_logic`、`critical_state`、`strategy_switch`、`comparison_boundary`；
- `layout_mode`：`explicit`、`layered_lr`、`layered_tb`；
- `semantic_role`：对象、状态、变量、条件、约束、边界、决策、结果或上下文；
- `relation_type`：因果、约束、变换、依赖、流向、切换、比较、反馈或明确标注的自定义关系。

## 4. 节点与分组

### 4.1 节点

- 核心对象使用 `emphasis: primary`，真正竞争注意力的主对象通常不超过 2--3 个。
- 风险、失效或临界判定可使用 `risk`；辅助背景使用 `context`。
- 同一语义角色在同一图中优先保持形状、轮廓和线型一致；颜色不是默认语义编码。
- label 只写对象、必要变量和短条件；完整公式推导留在正文。
- 单节点优先保持一至两行。必须缩小到不可读字号才能容纳时，应缩短文字或拆分结构。

### 4.2 分组

`groups` 用于表达真实对象域、阶段、主体或可行/失效区域，不用于装饰边框。group 必须有来源锚点和显式 geometry。节点通过 `group_id` 声明所属组；生成器用 `hskGroup` 保留关系，不改变节点端点。

容器与成员盒重叠是正常嵌套，静态校验器不会把容器当普通实体；两个普通节点的实质重叠仍为 blocking。

## 5. 连接器

- `source` 与 `target` 永远按 Spec 的语义端点填写；不要通过交换坐标伪造箭头方向。
- `forward`、`backward`、`bidirectional`、`none` 只控制箭头标记，不改变端点 ID。
- `feedback` 明确表示返回路径，优先用 waypoint 绕开主链；不要让反馈线穿过无关节点。
- 分支条件写在边 label 上，互斥条件应能从文字中识别。
- 汇流点只有具有真实合并语义时才添加，不能为了对齐制造无来源节点。
- `custom` 必须填写非空关系名称；能用稳定关系类型时不使用 custom。

## 6. 布局模式

### 6.1 explicit

用于几何边界、临界状态、带反馈的复杂结构或需要人工固定构图的正式图。每个节点填写 `x/y/width/height`，waypoint 也使用同一画布坐标。

建议先把画布分成 3--5 个语义区域，再放核心对象；族间留白大于族内留白。箭头从对象外缘进入，避免从文字中央穿过。

### 6.2 layered_lr / layered_tb

用于简单有向关系的第一版草图。生成器仅根据非反馈、正向边建立稳定层级，并按 ID 排列同层节点；它不会推断语义、合并节点或解决复杂循环。

自动布局生成后仍须打开预览。若出现交叉、过长回路或阅读顺序不自然，切换到 `explicit` 并显式修正坐标，不修改端点语义来迁就版式。

## 7. 视觉语法

正式 draw.io 机理图默认使用 **黑白线稿 + 灰度层级**，不再按 `primary / secondary / risk` 自动分配蓝、绿、红色。

- `primary`：白底、黑/深灰主轮廓，适度加粗；
- `secondary`：白底、中深灰轮廓，常规线宽；
- `risk`：浅灰或白底、深色加粗轮廓，必要时结合线型/边界符号，而不是红色填充；
- `context`：极浅灰底与浅灰轮廓，主动降权。

视觉区分优先级为 `shape / geometry → line style / line width → grayscale → optional accent color`。默认输出不得包含蓝/绿/红多色语义填充；若人工精修确需强调色，应先证明黑白编码不足，通常只允许 1 个强调色，极少数复杂图最多 2 个，并保证黑白打印仍可辨识。

节点优先使用与题意实体一致的规则几何图形。稳定图元包括矩形/圆角矩形、圆/椭圆、三角形、菱形、四边形、六边形、圆柱投影，以及用圆形/椭圆轮廓表达的球体。不要把所有对象退化成圆角矩形盒子。精确几何比例、切线、曲线和坐标边界仍应转 MATLAB / TikZ / GeoGebra。

禁止 rainbow/jet、渐变装饰、拟物阴影、大面积高饱和底色、外部图标和装饰性 3D。正式论文缩放后必须保持文字、箭头、变量、虚实线和边界可读。

## 8. 静态校验与人工 QA 边界

静态脚本可以检查：

- XML 是否为单个未压缩 `mxGraphModel`；
- ID、端点、Spec 图元和几何是否合法；
- 图元是否越界、普通实体是否实质重叠；
- 明确连线是否穿过无关实体；
- 文字是否确定性溢出；
- 是否嵌入位图、外部 URL、脚本或远程资源；
- 声明的 hash 和预览文件是否 current。

静态脚本不能判断：

- 箭头方向是否符合真实机制；
- 变量、公式、阈值或约束是否数学正确；
- 是否遗漏关键对象、不利状态或反例；
- 图是否美观、是否足以支撑正文 claim；
- 复杂连接交叉是否在语义上允许。

因此 `structure_checked` 绝不等于 `approved_for_paper`。必须查看最新渲染预览，并按 `templates/figure/mechanism_qa.md` 先检查语义真实性，再检查版式。

## 9. 预览与导出

若本机已安装 diagrams.net CLI，可使用其实际可执行文件名导出。例如：

```bash
drawio --export --format png --scale 2 \
  --output figures/preview/q1_occlusion.png \
  figures/source/q1_occlusion.drawio

drawio --export --format pdf --crop \
  --output figures/q1_occlusion.pdf \
  figures/source/q1_occlusion.drawio
```

CLI 不是硬依赖。无法渲染时可以交付 `.drawio` 草稿和结构检查结果，但必须明确等待用户打开或返回截图；不得登记为 `approved_figures`。

建议路径：

```text
figures/source/q1_<slug>.mechanism.yaml
figures/source/q1_<slug>.drawio
figures/preview/q1_<slug>.png
figures/q1_<slug>.pdf
figures/q1_<slug>.svg
```

`.drawio`、Spec 和 preview 属于内部编辑/复核材料，默认不进入只允许 PDF 的 official package。是否进入 reproducibility package 继续服从现有 submission Authority。

## 10. 修改分流

只移动节点、调整间距/颜色/字体/线宽/圆角、换行、改变不影响端点的连线路径或重新导出，不改变模型语义，也不触发重新 Model Approval 或 03A/03B 重算。

新增/删除对象，改变 source、target、direction、relation type、变量、公式、约束、阈值、反馈或可行侧时，先对照 current Framework 与模型 Authority：

- Framework 正确、只是图画错：修图并刷新 Figure Evidence；
- 图的问题暴露模型或 Framework 冲突：回退现有语义治理链；
- 不能确认是哪一种：停止批准图，要求人工判定。