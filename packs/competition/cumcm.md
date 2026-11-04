# CUMCM 国赛适配器

- 最终中文论文默认使用 `templates/latex/cumcm/hsk/` 模块化工程；`templates/latex/cumcm/cumcmthesis/` 仅作为上游 class/基础模板资源；
- 摘要覆盖所有小问，写方法、关键数值和结论，关键词 3--6 个；
- 重视题意覆盖、机制解释、模型合理性、结果可信、创新适度和附件复现；
- 2026 CUMCM 正文不堆代码，但**论文附录须含全部完整、可运行源程序代码**及实际支撑材料清单；同一批必要源码和自主查阅材料还须进入独立支撑 ZIP。确无程序或材料时使用官方两句分别对应的说明，不能将“附件 ZIP”代替论文内代码；
- 图表、表格、公式和参考文献按国赛模板统一；
- 不调用 `legacy/writing_phrase_corpus/` 套句，写作以本题证据为核心。

- CUMCM 2026 正式交付使用 `scripts/cumcm_2026_delivery.py`，只导出独立 PDF + 条件性支撑 ZIP。编译证明、来源身份、文件名单、大小和匿名核对细则见 `core/output_contract.yaml#delivery_attestation.cumcm_2026_external_upload` 与 `packs/artifact/full_submission.md`；原内部 `hsk_pack_submission.py` 保持独立。
