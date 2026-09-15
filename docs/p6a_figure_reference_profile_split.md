# P6a 论文图例索引与 MATLAB Profile 分离

> 维护实施证据，不建立第二套 Figure Authority。通用 Figure 决策继续由 `modules/04_figure_evidence.md` 唯一拥有；本阶段只收束视觉参考索引和 MATLAB 渲染配置实现。

## 修改简报

- **修改主题：** P6a，把现有论文视觉参考资产整理为可按证据结构检索的图例索引，并把 MATLAB publication profile 从“应用样式”函数中拆成独立、纯数据的 profile registry。
- **当前版本：** Skill v9.1.0。
- **目标版本：** 全面优化候选 minor release 能力；本 PR 不修改 release carriers，统一发布留给 P9。
- **变更等级：** minor-compatible / figure implementation refactor。
- **直接目标：** 让图型选择阶段能在不加载整套图片的前提下，通过 `assets/figure_assets.yaml` 按 Evidence Structure / publication pattern / layout need 找到少量视觉参考；让 `hsk_apply_scientific_style.m` 只负责把已选 profile 应用到 figure，而 `hsk_publication_profile.m` 只返回 palette / typography / frame 等确定性 profile 数据。
- **“论文图例索引”口径：** 本阶段的“图例”指论文 Figure visual examples / reference assets，不是把 legend 决策从 Module 04 抽成新 Authority。legend strategy 仍服从 Module 04 与既有 implementation patterns。
- **明确不做：** 不新增或复制外部论文图片；不把参考图作为数据/结论/配色真值；不改变 Scientific Figure Synthesis、Figure Layout、Legend Strategy、Data Honesty 或 Portfolio Gate；不改变 Python/MATLAB 分工、03A/03B、Workbook/Project State、Model Approval/SIB/stale、每问五文件接口；不在 P6a 宣称真实 MATLAB 渲染已经验证。
- **权威事实源：** `modules/04_figure_evidence.md`；实现索引为 `assets/figure_assets.yaml`，候选图型索引为 `templates/figure/chart_selection.md`，MATLAB implementation surface 为 `templates/matlab/`。
- **预计修改文件：** `assets/figure_assets.yaml`、`assets/nature_figure/README.md`、`templates/matlab/hsk_publication_profile.m`、`templates/matlab/hsk_apply_scientific_style.m`、`templates/matlab/README.md`、Figure/MATLAB 专项测试、`docs/skill_optimization_status.md`；generated index/MANIFEST 由既有 workflow 管理。
- **禁止触碰：** Figure Authority 的业务决策语义、求解/分析代码、工作簿 Schema、Project State、审批/identity/stale、正式 LaTeX、release carriers。
- **兼容性要求：** `hsk_apply_scientific_style(fig)` 和显式三种 profile 名称保持不变；返回 palette 的 semantic fields 与 release-era aliases 保持；`qX_plot.m` / `data_process.m` 的单文件 local fallback 保持，不要求用户项目增加第六个正式文件；`assets[].path(s)/use_for` 旧读取继续可用。
- **迁移要求：** 无用户项目迁移；新增索引字段为 additive；共享 MATLAB template bundle 增加一个实现 helper，但不进入项目五文件合同。
- **验收测试：** 旧 v9.1 rendering regression；新增 asset-index closure、profile registry API/legacy fields、style-kernel separation、standalone-entry compatibility；完整 lint/unittest/generated/LaTeX CI 与 Optimization baseline。
- **回滚方式：** 撤销 P6a 新 registry/索引字段并恢复 style kernel 内嵌 profile；用户项目与 accepted workbook 无需迁移。

## 设计边界

P6a 只解决两个已经存在但耦合过紧的问题。

### 1. 论文视觉参考从“资产清单”升级为“按问题检索的索引”

现有 `assets/figure_assets.yaml` 已经是可选视觉参考的机器入口，且 `chart_selection.md` 已明确：只有图型/布局需要外部对照时才按需加载。P6a 不建立第二个目录或第二个 YAML，而在同一入口上增加三个 additive lookup：

```text
Evidence Structure  -> asset keys
Publication pattern -> asset keys
Layout need         -> asset keys
```

索引只返回候选视觉参考 key。最终图型、布局、palette、legend 和 annotation 仍必须回到 Figure Contract + Module 04 决策；资产本身不进入数值证据链。

### 2. profile data 与 style application 分离

P6a 后共享实现关系为：

```text
hsk_publication_profile(profile)
    -> deterministic profile spec
       palette / typography / frame

hsk_apply_scientific_style(fig, profile)
    -> select runtime font
    -> apply profile spec to current figure
    -> return backward-compatible palette
```

这样 palette/profile 数据不再埋在会直接修改 figure 的函数内部，后续 P6b 可以对 profile spec 做独立静态/真实渲染验证，而不需要复制 profile 定义。

`hsk_publication_profile.m` 不读取 workbook、不创建 figure、不导出图片、不选择图型，也不判断 legend/layout；因此它是 implementation registry，不是 Figure Authority。

## 与 P6b 的边界

P6a 不把“代码看起来能画”称为真实预览。P6b 才负责真实 rendering/preview 证据：在可用 MATLAB/兼容执行环境中，对代表性 profile/pattern 产生真实预览并验证文字、legend、canvas、print-safe 与输出边界；若执行环境不可用，P6b 必须保留为未验证状态而不能用静态检查冒充。
