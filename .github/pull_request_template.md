## 修改简报

- 修改主题：
- 当前版本：
- 目标版本：
- 变更等级：`docs / patch / minor / major`
- 直接目标：
- 明确不做：
- 权威事实源：
- 预计影响范围：
- 兼容性要求：
- 迁移要求：
- 回滚方式：

## 关键改动

-

## 关联检查

说明本次检查了哪些关联文件，以及哪些无需修改及原因。

-

## GitHub Actions 验收

- [ ] 源文件已推送，远端 `refresh-generated` 已生成并提交受管文件；已检查生成差异
- [ ] 最终 PR head 已由 GitHub Actions 验证
- [ ] Windows Python 3.10 full regression 成功
- [ ] Windows Python 3.14 full regression 成功
- [ ] Static contract lint 成功
- [ ] Generated file contract 成功
- [ ] 受影响原生/载体 job 成功
- [ ] Optimization baseline（若适用）成功
- [ ] 已记录最终 head SHA 与 workflow run
- [ ] 若删改 CI job / check 名称，已核对 `main` 的 required checks 并处理失效依赖
- [ ] 未以本地测试结果替代远端验收

最终 head SHA、workflow run 与受影响专项检查：

```text
填写 GitHub Actions 的实际运行链接或 ID、结果；未完成时如实注明。
```

合并后 `main` SHA 与 GitHub Actions 状态（未合并时注明待复核）：

```text
填写实际 SHA、运行链接或 ID、结果。
```

## 兼容与迁移

- 旧项目是否可继续运行：
- 兼容层及退出条件：
- 迁移步骤：

## 风险

-

## 治理确认

- [ ] 已从 `main` 读取 `core/bootstrap.yaml`
- [ ] 已从 `main` 读取 `SKILL_CHANGE_GOVERNANCE.md`
- [ ] 已确认当前版本、最新 `main` 提交和重叠 PR
- [ ] 本 PR 只有一个核心主题
- [ ] 未直接修改 `main`
- [ ] 未依据旧聊天记忆代替仓库事实
- [ ] 未重复定义已有权威规则
- [ ] 未手工伪造索引、MANIFEST 或测试结果
- [ ] 若修改超过 20 个活动文件，已解释无法拆分的原因
