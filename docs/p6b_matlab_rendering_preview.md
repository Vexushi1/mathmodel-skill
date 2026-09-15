# P6b 真实 MATLAB Rendering / Preview 证据

> 维护实施证据，不建立第二套 Figure Authority。Figure 决策继续由 `modules/04_figure_evidence.md` 唯一拥有；P6b 只把 P6a 的 publication profile/style implementation 放入真实 MATLAB 执行环境，产出可下载预览并做机器可判定的渲染边界检查。

## 修改简报

- **修改主题：** P6b，为 P6a 的 `hsk_publication_profile.m` 与 `hsk_apply_scientific_style.m` 建立真实 MATLAB rendering/preview CI。
- **当前版本：** Skill v9.1.0；P6a 已合并至 main `c8f2a42c6eb37ee7b469024f9ab73d5cb0ac37a3`。
- **目标版本：** 全面优化候选 minor release 能力；本 PR 不修改 release carriers，统一发布留给 P9。
- **变更等级：** minor-compatible / rendering assurance。
- **直接目标：** 在 GitHub-hosted 的真实 MATLAB 环境中生成代表性 publication previews；验证 profile/style API、文字与 legend、canvas、PNG/PDF 输出、monochrome print-safe 与输出目录边界；将真实预览作为 CI artifact 保存。
- **明确不做：** 不修改 Figure Authority；不把 preview fixture 当论文数值证据；不改变 qX/data_process 五文件接口、工作簿/Project State、Model Approval/SIB/stale、03A/03B、LaTeX 或 release carriers；不自动批准任何用户项目 Figure。
- **权威事实源：** `modules/04_figure_evidence.md`；P6a 实现为 `templates/matlab/hsk_publication_profile.m`、`templates/matlab/hsk_apply_scientific_style.m`；P6a/P6b 边界见 `docs/p6a_figure_reference_profile_split.md`。
- **预计修改文件：** 独立 MATLAB preview harness、P6b workflow、专项静态测试、本维护证据与优化实施记录；generated metadata 由既有流程管理。
- **禁止触碰：** 数值/工作簿/状态/审批/identity/stale 与正式论文内容语义。
- **兼容性要求：** 不改变 `hsk_apply_scientific_style(fig[, profile])` 或 profile registry API；preview harness 只消费现有 API；用户项目无迁移。
- **迁移要求：** 无。
- **验收测试：** P6b workflow 在真实 MATLAB runner 上成功；三个 profile 均生成非空 PNG/PDF；机器检查文字/legend/canvas/style/print-safe/output-boundary；完整 HSK Skill CI 与 Optimization baseline evidence 仍通过。
- **回滚方式：** 删除 P6b preview harness/workflow/tests/docs 即可；P6a profile/style implementation 与用户项目不受影响。

## 真实预览口径

代表性 preview 使用确定性合成数据，只验证 publication rendering implementation，不验证任何比赛结论。每个 preview 必须满足：

1. 在真实 MATLAB batch session 中创建不可见 figure；
2. 调用 `hsk_publication_profile` 与 `hsk_apply_scientific_style`，而不是复制 palette/profile 定义；
3. 至少包含坐标轴文字和 legend；正式图策略保持 in-figure title=`none`；
4. 固定 canvas，并检查 axes/legend/font/frame 与 profile spec 一致；
5. `monochrome_print` 必须证明其 series palette 为灰度等通道；
6. 同时导出 PNG 与 PDF，PNG 可由 `imread` 读取且不是空白画布；
7. 所有输出写入 CI 临时目录，不修改仓库源码或用户项目；
8. workflow 上传 preview artifact，供人工视觉复核；机器通过只代表 `preview_rendered + machine_checked`，不等同于用户项目 `approved_for_paper`。

## 环境边界

P6b 使用 MathWorks 官方 GitHub Actions 在 public GitHub-hosted runner 上设置 MATLAB 并执行 batch command。若真实 MATLAB action 无法获得许可、安装或运行，则 P6b 保持未验证，必须修复环境或明确阻塞；禁止用 Python/静态 lint/伪造图片替代真实 MATLAB preview。
