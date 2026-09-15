# Nature figure reference assets

本目录仅保存按需论文 Figure 视觉参考。机器入口为 `assets/figure_assets.yaml`。

这些图片用于对照图型、留白、面板层级、信息密度和复杂图例/布局处理，不是数据源、结果证据、固定配色模板或可直接复制的论文图。正式图仍必须满足：

```text
Python结果 → 标准工作簿 → Figure Contract → q{x}_plot.m → 论文图 → 正文结论
```

`assets/figure_assets.yaml#reference_index` 只把当前 Evidence Structure、publication pattern 或 layout need 映射到少量已有 asset key；最终是否采用某种视觉结构仍由 `modules/04_figure_evidence.md` 与 Figure Contract 决定。只有 `templates/figure/chart_selection.md` 判定视觉参考确有帮助时才做 lookup，并只加载命中的 `path/paths`，默认运行不读取全部图片。

P6a 不新增或复制外部论文图。现有 atlas/gallery 只作为受控 visual-example surface；不得从参考图反推数据、结论、legend 语义、颜色或面板数量。
