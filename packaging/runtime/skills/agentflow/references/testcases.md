# 测试用例：Markdown 权威与可选执行映射

> **加载者**：`skills/agentflow/SKILL.md`、测试角色与计划模板。用例语义只有一个来源；记录形态与状态联动见[测试记录](test-records.md)。

## 1. 唯一语义来源

full 的用例权威是 `testing/<项目>-<功能>/plan-*.md` 的注册表与同名详情：注册表给出唯一 `case_id`（`TC-*`）、级别、优先级、入口和验收来源（AC/ISS）；详情给出前置、步骤、输入与预期可观察结果。AC 定义仍在已确认规格中；**AC↔用例映射只在注册表「来源」列维护**，不在 spec、design、frontmatter 或 YAML 再抄一份。

light 在唯一 README 的「最小用例」节承载同义注册表与详情、`test_plan_id` / `test_version` 和运行结果；无需额外 plan 文件。可以内嵌本轮 run，也可引用已有执行报告；不得为满足测试记录形态强制另建文档链。

用例 ID 在本计划内唯一，注册表与详情一一对应；来源必须指向已确认的 AC、需求条款或 ISS，确无编号时写「无 — 理由与已确认出处」，不留空。修改步骤、预期或覆盖关系时递增 `test_version`。期望来自契约或用户确认，不能由当前响应、实现常量或被测算法反推。

## 2. YAML 只作可选执行映射

目标 runner 需要时可用 `testcases.yaml`，它不是第二份用例库。每项只引用 Markdown 中的 TC ID，并给出 `automated` 执行路径与运行参数；不复制 `steps`、`expect`、`ac`、来源或验收正文。

```yaml
- case_id: TC-LOGIN-001
  automated: tests/login.spec.ts
  args: ["--grep", "TC-LOGIN-001"]
```

`automated` 是当前字段名；所有当前消费者保持同名。旧历史格式不批量回改。测试路径与参数必须在目标仓实际存在或明确标待实现，不宣称本插件提供并不存在的用例校验脚本。

## 3. 执行与核对

run 用 `test_plan_id` 绑定计划、用 `test_plan_version` 绑定该计划的 `test_version`（light 时定位 README 的最小用例节），逐 TC 记本轮状态、实际证据层级、实际结果与原始输出。YAML 不写最近结果，计划不写本轮结果。

接受前由主审与独审核对：注册表/详情 ID 唯一且闭合；全部必需 AC 有来源映射；执行映射无孤儿 ID；执行路径与具名用例真实可运行；结果属于被绑定的版本。目标仓已有实际检查命令时运行并留原始输出；无工具则如实记人工核对，不能写成自动门通过。e2e 的 pass 只接受 browser/manual，API 200 不能关闭用户可见路径。
