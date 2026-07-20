# HSK Stage 12：提交前检查清单

## 文件检查

- [ ] `paper/main.tex` 或最终主 tex 文件存在；
- [ ] 国赛模板类文件存在；
- [ ] 图片文件均存在且文件名英文；
- [ ] 代码附录或代码压缩包存在；
- [ ] 结果表格存在；
- [ ] 参考文献存在；
- [ ] 最终 PDF 已生成。

## 内容检查

- [ ] 摘要逐问给出方法和结论；
- [ ] 问题分析与模型选择一致；
- [ ] 每个核心问题至少有机理图、推导图、临界图或结构示意图；
- [ ] 机理/推导图能对应公式、约束、假设或代码判断；
- [ ] 变量表、假设、公式完整；
- [ ] 数据预处理说明充分；
- [ ] 每问有模型、求解、结果、分析；
- [ ] 有模型检验；
- [ ] 有敏感性或鲁棒性分析；
- [ ] 结论不空泛。

## 编译检查

- [ ] `latexmk -xelatex main.tex` 通过；
- [ ] 无 `??`；
- [ ] 无 missing file；
- [ ] 无 overfull hbox 大面积报警；
- [ ] 图表位置可接受。


## 交付闭环补充检查

提交前额外检查：

- 是否维护 `data_output/result_manifest.yaml`；
- 是否生成 `data_output/run_info.json`；
- 优化类问题是否输出 `问题X约束违反检查.csv`；
- 摘要是否通过 `templates/shared/hsk_abstract_result_checklist.md`；
- 核心公式是否通过 `templates/shared/hsk_formula_code_closure_table.md`；
- 核心机理/推导图是否通过 `templates/shared/hsk_mechanism_figure_qa_checklist.md`；
- 核心图表是否通过 `templates/shared/hsk_figure_paper_check_table.md`；
- 若使用高级模型，是否通过 `references/hsk_advanced_model_gatekeeping.md`。
