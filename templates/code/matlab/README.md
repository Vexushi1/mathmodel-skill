# MATLAB 主求解与条件深化模板

本目录实现 `core/user_execution_contract.yaml`、`core/output_contract.yaml` 和 `core/workbook_schema.yaml`，不另定义批准、质量或状态规则。适用运行基线为 MATLAB R2024b，使用原生 Excel 写出和 JVM SHA-256；需要 MATLAB 许可证，不依赖额外工具箱，不支持 `-nojvm`。其他求解器的工具箱与许可证必须随具体实例另行声明和核验。

`q1_solver.m` 是可实例化的 `a*x=b` 微型例子，`q1_analysis.m` 是已接受主结果之后的系数敏感性例子；它们不是任意题目的默认模型。实例化时同时替换数学结构、变量、求解器、输入、PQS 和结果字段，并先完成现有模型批准。替换配置里的数据摘要；只有主工作簿已验收且 Analysis Necessity Gate 为 `required`，才实例化分析入口并绑定 `primary_workbook_sha256`。`not_required` 不生成分析文件。

两个入口均放在本问 `问题一求解/`，主函数名与文件名一致；其他问题相应改为 `q2_solver` 等，并更新 problem_name、输入与输出位置。代码通过自身位置找到项目根目录，不依赖启动 cwd。默认 local functions 使每份交付代码自包含，用户不需要把 Skill 仓库加入 MATLAB path。

主函数的首条语句是唯一 `RUN_CONFIG = jsondecode('...');`。配置使用可静态读取的 JSON 字面量；不要动态拼接、重赋值或改用外部配置。新主/分析使用回执 1.1，`solver_backend=matlab`。种子、容差、完整求解范围实际由配置驱动。例子的直接求解只支持 `iteration_or_time_limit=direct`；分析必须执行声明的全部场景。

原始入口 SHA 与包含入口及声明 helper 的 bundle SHA 各自保留。bundle 按项目相对 POSIX 路径的 UTF-8 次序，把路径 UTF-8、NUL 与原始文件 SHA 字节连接后计算 SHA-256。数据摘要沿既有数据身份算法。入口及输入在运行前、写出前再次核对；helper 的路径、摘要和 MATLAB 实际解析位置也必须一致。调用 helper 的实例须声明实际项目源码并确保它被合法解析；未知动态加载不得声称闭包已验证。

数据身份在实例化时明确：省略 `data_identity_mode` 或设为 `combined`，使用既有“路径、NUL、文件 SHA 字节”的组合摘要；`project_level` 必须声明 `preprocessing_workbook`，`data_paths` 只包含既有已验收预处理 XLSX，`data_sha256` 使用该工作簿原始文件 SHA，与项目状态保持一致。此模式不再读取被预处理覆盖的原始源。微型例子通过 `模型输入` 表精确读取 `coefficient`、`right_hand_side`、`sensitivity_coefficients`，最后一列是明确记录的 JSON 数组；实际题目须实例化为自身真实字段，不能机械套用该表。主、深化遵守同一数据身份；03B 另行绑定 accepted 主工作簿 SHA。

每次正式数值运行使用新的 MATLAB `-batch` 进程，代码修改后也重新启动。示例命令在已安装 MATLAB 的终端运行，路径替换为项目中已交付代码的实际位置：

```text
matlab -batch "cd('C:/项目/问题一求解'); q1_solver"
matlab -batch "cd('C:/项目/问题一求解'); q1_analysis"
```

第二条仅在主工作簿 accepted 且分析 required、分析代码已交付时执行。不要复用 GUI 长会话中的旧函数体；`mlock` 可使旧体在磁盘源码已变化后仍运行，`clear`/`rehash` 不能无条件保证重载。入口内部的起止 SHA 检查不替代新进程边界；新进程也使 `persistent` 状态从本次运行重新初始化。

原生 writer 保留中文工作表和表头，拒绝重复、非法名称和不支持的单元格类型，使用同目录临时 XLSX，成功后替换正式文件，避免旧 sheet/尾行残留；失败不更改有效旧文件。支持有限实数、logical 与明确文本；合同允许缺失的字段可显式写入空字符串，保留记录键和数据行，不能补零、删行或把 NaN/Inf 静默改为空白。记录键非空且唯一；含前导零或超出精确整数范围的标识符按文本输出。

运行事实写入原 `运行配置(项目, 值)` 工作表，不创建用户级回执 JSON/YAML，也不写项目状态。主质量未通过时保存实际失败表并报错；准备或求解时无法形成合法工作簿的错误直接抛出，运行日志保留真实诊断。工作簿存在和代码无异常不等于 accepted；维护侧 Python 的回执、Schema 与数值证据检查仍必须通过。

正式绘图继续使用 `templates/matlab/q1_plot.m`；求解入口不生成正式图，绘图入口不重算核心结果。静态检查、Code Analyzer、真实 MATLAB 运行与用户项目数值验收分别报告。

维护合成验证入口为 `tests/test_solver_backend_end_to_end.py` 与 `tests/matlab/run_solver_backend_smoke.m`。`tests/solver_backend_mixed_smoke.py` 与 `tests/matlab/run_solver_backend_mixed_smoke.m` 中双向跨问混合及同问 Python 主求解接 MATLAB 深化的场景仅用于 v9 历史兼容与 v10 当前路径拒绝回归，不授权新项目逐问或逐阶段混用数值后端。测试只运行独立临时目录中复制并实例化的微型数学例子，不运行用户赛题，也不把静态检查或 skipped 的 MATLAB job 当作运行通过。
