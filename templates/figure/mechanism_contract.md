# HSK 机理/推导图 Figure Contract 模板

| 字段 | 内容 |
|---|---|
| 图编号 | 图 X |
| 对应问题 | 问题一 / 问题二 / ... |
| 图类型 | 题目对象关系图 / 机理推导图 / 几何截面图 / 临界状态图 / 模型选择说明图 / 结果验证图 |
| Figure role | mechanism / derivation / boundary / counterexample / validation / decision |
| Backend selection | MATLAB / TikZ / GeoGebra / PPT / draw.io / manual；为什么该后端比其他候选更适配 |
| Diagram type | object_relation / mechanism_relation / constraint_logic / critical_state / strategy_switch / comparison_boundary（draw.io 路径） |
| Core question | 该图回答的建模疑问，例如“为什么遮蔽不能只看目标中心线？” |
| Core conclusion | 该图支撑的一句话结论 |
| Model link | 对应变量、假设、目标函数、约束或判定条件 |
| Formula link | 对应公式编号，如式(3)--式(6) |
| Code link | 对应代码函数、判断条件或输出文件 |
| Semantic anchors | Framework 章节、公式、约束、假设、代码与已验收数值证据锚点 |
| Source | 手工草图 / PPT / TikZ / Python / MATLAB / draw.io / Visio |
| Spec（可选） | `figures/source/qX_<slug>.mechanism.yaml` |
| Editable source（可选） | `figures/source/qX_<slug>.drawio` |
| Rendered preview（可选） | `figures/preview/qX_<slug>.png`；未查看不得批准 |
| Formal exports（可选） | `figures/qX_<slug>.pdf|svg|png` |
| Provenance hashes（可选） | spec / drawio / preview SHA-256 |
| Structure validation | pending / passed / failed / review_required；只表示结构与几何检查 |
| Visual review | pending / preview_rendered / visual_reviewed / approved_for_paper / rejected |
| Change class | pure_visual / semantic；semantic 必须与 current Authority 比较 |
| Reviewer risk | 没有该图时评委可能质疑之处 |
| Caption duty | 图注必须解释的机制、边界、推导或临界状态 |
| Paper location | 正文章节位置 |

旧合同不强制补齐 draw.io 字段；只有新建或主动重绘的 draw.io 图使用这些可选项。Spec 与 `.drawio` 是渲染/编辑载体，不是模型或数值事实源。
