# 案例记忆：按需检索与决策引用

在当前题意和结构特征已经明确、需要比较既有建模模式时，选择 `case_memory_retrieve`。规则来自 `core/case_memory_retrieval_contract.yaml`，卡片准入仍由 `knowledge/case_memory/schema.yaml` 管理；项目引用形状由 Project State Schema 管理。

## 查询与判断

1. 给出本题的 objective、structures、capabilities 和明确的数据制度、变量类型、信息边界及必要条件。缺少的信息填 `unknown`，不能凭题名或模型名称推断已经具备数据。
2. 实际调用 `scripts/case_memory_retrieve.py` 获取少量当前准入案例、匹配依据、差异、缺少条件和不可迁移项。工具导航或读取计划不证明检索已执行。
3. `conditional` 表示仍有条件待核对；`no_match` 是合法结果。关闭或索引不可用时保留原有建模工作流，不能编造历史经验。分数仅用于排序，不是模型适用概率。
4. 首批资料都是明确合成案例，其验证建议、参数和数字不能成为当前题结果或“原作者已经验证”的事实。

## 采用、拒绝与复核

adopt 至少声明一项采用内容和一项经当前位置/哈希核验的本题依据；reference/reject 可以明确没有这类依据。定位核验不证明条件语义，报告始终保留 `project_condition_semantics=not_assessed`。

使用 `scripts/case_references.py` 先 preview 当前已有 Qn 决策，记录具体采用/拒绝部分、理由和真实本题来源引用；明确 record 写入使用原有项目事务。预览和 inspect 默认只读。

引用表达作者决策声明。改变模型时仍需当前模型语义修订、Model Challenge 和 Human Model Approval；引用不能写入批准或 accepted 资格。只有原数值、回执和证据合同可证明相关事实。

后续 inspect 复核案例、来源、项目范围和固定规则的当前性。首版只持久保存 query hash，不保存原 query，因此明确报告 `ranking_not_recomputed`；不能宣称当前仍是推荐命中。案例撤回或相关来源变化列为 `needs_review`，由本题证据重新判断，不自动宣布旧数值错误。

## 使用与资源边界

普通任务不加载完整案例库。检索离线、有界、确定性；不运行卡片里的命令、不访问网络、不自动学习或发布用户资料。固定开发 query 集验证检索契约；同源污染被标记，开发集结果不证明独立留出或真实建模质量提升。
