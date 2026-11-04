# 测试用例结构化：testcases.yaml

> **加载者**：`skills/agentflow/SKILL.md` 工程内容标准节；`agents/test-planner.md` 与 `templates/feature/plan/execution.md` 写用例时读。AC 权威口径（plan 注册表「来源」列）在这里。

> **解决什么**：痛点 12——验收标准（AC 表 M01-AC-*）是 markdown 散文，改动用例时无法机械校验「是否破坏了某条 AC 的覆盖」。引入以 AC 为键的结构化用例文件，让 design 必须表述操作过程 + 预期结果，并可用 `scripts/check-testcases.py` 机械校验覆盖。**口径如实**：该校验是目标仓侧的按需独立脚本（门外工具），本插件未把它接入 `validate.py` 或 CI——是否接入由各仓自己的门配置决定，不得宣称已默认门校验。

## 0. 文件位置与形态

- 落点：`<feature>/testing/<项目>-<功能>/testcases.yaml`（与 `run-*.md` 同目录）。
- 形态：YAML 列表，每条用例以 `ac` 为键指向 `spec/qa/acceptance.md` 的 AC 编号。

## 1. 字段 schema

```yaml
- ac: M01-AC-01            # 必填，指向 spec/qa 的 AC 编号
  title: 正确凭据登录成功
  priority: P0             # P0/P1/P2
  source: proposal §1.2 G1 # 来源可追溯
  type: browser            # browser | api | unit
  steps:                   # design 必须表述操作过程
    - 打开登录页
    - 输入 demo@example.com / Demo@12345
    - 点击登录
  expect: 进入 upload 视图且导航显示邮箱   # 预期结果必须明确可判定
  automated: server/*.test.mjs + browser    # 承载自动化用例的路径；api/unit 填对应测试文件
  evidence: run-2026-11-02-001.md#TR-03     # 最近一次执行的证据锚点
```

## 2. 强制规则

1. **design 必须表述操作过程 + 预期结果**才能写进 yaml——空 `steps` / 空 `expect` 不允许。
2. **每条 AC 至少 1 条用例**：`check-testcases.py` 校验「AC × 用例映射无空白」（沿用 `document-chain` 的映射检查精神；按需运行，未默认接入门——见开头口径）。
3. **改动用例不影响其他 AC 覆盖**：结构化后可做 diff / 影响面分析——删除 / 改名某用例时，校验器报「X 条 AC 失去覆盖」而非静默。
4. `source` 必须可追溯到 `proposal` / `spec` 的具体节，杜绝「自造验收点」。

## 3. 与既有体系衔接

- `spec/qa/acceptance.md` 的「AC × 用例覆盖映射」改为**指向本 yaml**（不再手工维护 markdown 映射表）。
- `plan/execution.md` 的验证命令引用本 yaml 的 `automated` 字段所指测试。
- `test-records.md` 的 bug 状态联动不变（bug 仍用 `ISS-*`）。

## 4. 校验（新增，非门禁脚本内改）

`scripts/check-testcases.py <feature-dir>`：
- 解析 `spec/qa/acceptance.md` 的全部 `M##-AC-##`；
- 解析 `testcases.yaml` 的 `ac` 键；
- 报告：未覆盖 AC、孤儿用例（ac 不在 AC 表）、缺 `steps`/`expect` 的用例。
- 该脚本为**新增独立脚本**，不改 `tools/lab/validate.py` 既有权限边界。
