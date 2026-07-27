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

## 测试结果

- [ ] `python scripts/lint_skill.py`
- [ ] `python -m unittest discover -s tests`
- [ ] `python scripts/generate_indexes.py --check`
- [ ] 已完成受影响专项测试
- [ ] 已检查生成文件差异
- [ ] CI 已通过或已明确说明仍在运行

专项测试：

```text
填写实际命令与结果
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