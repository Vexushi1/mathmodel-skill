# HSK Python 用户执行管线（template lineage v7.0.0）

本目录保留 Python 数学模式与工作簿 IO；运行配置、实际回执和用户执行资格只服从 `core/user_execution_contract.yaml`。管线不再拥有项目状态或框架写入权，也不把本地质量检查通过说成正式验收。

本目录提供用户本地运行的数值底座：

- `run_primary_pipeline()`：包级导出的主求解数学骨架，保留数据审计、求解、质量检查与失败证据输出；仅写约定工作簿。
- `main_pipeline.run_result_analysis_pipeline()`：仅显式保留的历史内存适配器，不在包级导出；它不证明当前主工作簿 accepted，也不代替独立03B入口。当前分析入口仍须按执行 Authority 从已验收工作簿开始。
- `main_pipeline.run_pipeline()`：旧名称仅提供明确的迁入提示，调用即报错，不执行任何钩子或连跑。需要复现旧编排行为时保留原版本环境，不能将旧 runner 重新引入当前正式入口。

`framework_sync_hook` 参数及 `_write_state` / `_update_primary_state` / `_update_analysis_state` 路径已经退出。旧调用传入框架钩子会在计算前报错，不静默忽略；应移除回调，让既有交付、回执及同步控制面登记状态和框架。`ResultAnalysisResult` 中的回退阶段/失效建议只是兼容返回数据，不表示已经写入项目。任意题目自定义数学钩子仍需静态审查；本库不是限制任意 Python 写文件行为的沙箱。

题目专属的实际激活阶段脚本在各自交付前都必须通过 `scripts/validate_code_delivery.py`；工程质量细则只由 `core/code_quality_contract.yaml` 定义，本管线不复制阈值。用户执行、`full_fidelity`、禁止降级/静默 fallback 与版本化 RUN_RECEIPT 的全局政策只由 `core/user_execution_contract.yaml` 定义，`PipelineConfig` 不重复承载这些不可变政策字段。

## 推荐复制结构

优先使用自包含入口；确有复用需要时，可只复制工作簿 IO，而不是默认复制整套 legacy runner。精确产物与阶段入口名称由 `core/output_contract.yaml` 定义。以下只展示可选 IO helper 在入口目录内的布局，不代表每问必需新增这些文件：

```text
问题一求解/
├─ 问题一求解.py
└─ hsk_pipeline/
   ├─ __init__.py              # 仅包说明，不导入 main_pipeline
   ├─ result_io.py
   └─ workbook_validation.py
```

入口用正常静态导入 `from hsk_pipeline.result_io import write_workbook`。三个辅助源码的实际相对路径和 SHA-256 都要纳入 `code_dependencies`，包括包初始化文件；无需修改 `sys.path` 或依赖 Skill 安装位置。包内使用明确的同级静态导入，缺失内部依赖会原样失败，不转到全局同名模块掩盖错误。

若为兼容维护而复制本目录原始 `__init__.py`，它会导入 `main_pipeline.py`，因此后者也属于真实闭包，必须声明，不能只列两个 IO 文件。本目录 runner 不再写项目状态或框架，旧组合调用会明确失败；新题目入口只产出约定工作簿及回执，由仓库已有事务门登记状态。

历史平铺的 `result_io.py` / `workbook_validation.py` 仍可在同一脚本导入目录中正常运行；这不等于平铺形式通过现代源码闭包认证。当前保守相对导入检查要求正式 1.1 交付使用上述明确包上下文；不要通过动态单文件装载、捕获 ImportError 后换模块或豁免模板来规避。

新生成 03A/03B 脚本使用唯一顶层 `RUN_CONFIG` 声明 stage/problem/data/hash/solver/seed/tolerance/limit/workbook/protocol 等任务输入，写 `solver_backend="python"`、`run_receipt_protocol_version="1.1.0"`；以 `code_dependencies=[{"path": "项目内相对源码路径", "sha256": "文件摘要"}]` 声明实际源码闭包（不含入口自身），包括复制到项目中的实际 `hsk_pipeline` 依赖。不重复 owner/profile/六个 no-degradation 字段，不把 `solver_version` 当运行前必填参数，也不把最终 bundle 摘要写回入口。旧 1.0、P5a 与 `FULL_FIDELITY_CONFIG` / `FULL_RUN_CONFIG` 只按原历史分支兼容；项目级 Python 预处理仍使用 1.0。

用户运行后构造逻辑 `RUN_RECEIPT`，**仍序列化到既有工作簿 `运行配置(项目, 值)`**，不新增回执工作表或独立 YAML/JSON。新 03A/03B 写 `run_receipt_version="1.1.0"`、`solver_backend="python"`、`code_sha256` 和 `code_bundle_sha256`，记录 owner/profile、solver/version、实际停止原因、平台、fallback 和 no-degradation 标志，并回显配置任务字段。入口必须在执行前绑定源码和输入、写出前复核；完整身份序列化只服从执行 Authority。未知或不匹配版本 fail closed。

保留的 PipelineConfig 和题型 starter 是数学/IO骨架，不会自动升级为 1.1 交付入口；旧连跑 API 已停止执行。实例化时须补齐上述运行配置与真实回执，并把 `运行配置` 工作表交给共用 `result_io.write_workbook()`；writer 接受该表的新字段，但不替调用方生成后端/bundle 证明。用户运行代码只依赖交付到项目内的源码与声明环境，不依赖 Skill 安装路径。

新 1.1 的 `project_level` 路径显式使用 `data_identity_mode="preprocessing_workbook"`，`data_paths` 恰为已验收预处理 XLSX，`data_sha256` 为其普通文件 SHA。其他两种预处理决策默认 `combined`；完整数据身份规则只由 `core/user_execution_contract.yaml#code_delivery.data_identity_mode` 维护。

## 主求解阶段

```text
主代码工程质量门
→ config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 构造RUN_RECEIPT并写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ 问题一求解/问题一求解结果.xlsx
→ validate_user_execution.py
→ RUN_CONFIG↔RUN_RECEIPT握手 / 数值证据验收
→ accepted / solved
→ 冻结问题一求解.py
→ Analysis Necessity Gate
```

`run_receipt_protocol_version` 只标识运行事实协议，不替代主求解专用 `primary_quality_protocol_version`。新 primary RUN_CONFIG 同时携带两者；前者约束 RUN_RECEIPT，后者约束主数值证据复核。

## 条件式结果深化阶段

主工作簿 accepted 后先执行 Analysis Necessity Gate：

- `not_required`：必须记录非空 `result_analysis_requirement_reason`；不生成 `问题一结果深化分析.py` 或 `问题一结果深化分析.xlsx`，也不得把该状态表述为稳健性、稳定性或替代算法一致性已通过；
- `required` 且选定 Python：单独生成 `问题一求解/问题一结果深化分析.py`，读取已验收主工作簿和必要当前数据事实源，按实际风险完成分析；再次通过代码质量门后由用户运行并输出分析工作簿。analysis RUN_CONFIG 声明 `run_receipt_protocol_version="1.1.0"`、`solver_backend="python"`、自身 `code_dependencies` 和 `primary_workbook_sha256`；返回工作簿写 1.1 回执及本阶段入口/bundle/主工作簿摘要，不得覆盖更新主求解代码。若选择 MATLAB，则读取对应 MATLAB 阶段模板。

Figure 阶段的 `q1_plot.m` 始终与主工作簿同目录。主结果图只要求 accepted 主工作簿；只有目标 Figure 实际消费 03B evidence 时才要求条件存在的分析工作簿，缺失时必须 fail closed。求解入口不生成正式论文图；绘图入口不重新求解，默认不创建图表目录或自动导出文件。
