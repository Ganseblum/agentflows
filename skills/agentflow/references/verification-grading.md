# 验证分级：smoke / integration / e2e

> **加载者**：`skills/agentflow/SKILL.md` 工程内容标准节与分档纪律；`execution.md` 的实现自检节；`templates/host/maker.md` 的验收条款。判断「链路通没通」之前读——curl 只算 smoke。

> **解决什么**：痛点 5c——「接口通 ≠ 链路通」。会话里出现把 `curl` 四步（login→me→logout→me）当「会话闭环」「登录成功」验证，结果页面一测全是 bug。SKILL.md §运行工作流 第 8 步已写「`curl`/API 200 只能证明协议链，不能关闭用户可见路径」，本册把它**强制化并落到 plan/design/qa 模板**，消除模板级自相矛盾。

## 0. 三级定义

| 级别 | 手段 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| **smoke** | `curl` / `healthz` / 端口监听 | 服务起了、接口契约存在、路由可达 | 任何用户可见行为正确 |
| **integration** | API 契约测试（`npm test` 后端）、单接口断言 | 单个接口的输入输出符合契约 | 多步骤用户旅程、前端状态、跨页面 |
| **e2e** | 浏览器 / 手动走查 + **原始证据**（截图 / DOM / 网络） | 用户真实入口到终态的链路正确 | — |

## 1. 强制规则

1. **`curl` 只能用于 smoke**：证明「服务起没起 / 接口契约存在 / 路由可达」。
2. **`curl` / API 200 不得作为「登录成功」「会话闭环」「功能可用」的通过证据**——这是反模式，发现即 `changes_requested`。
3. **端到端验收（AC 表的 M 系列用户可见路径）必须用 `browser` 或 `manual` 证据关闭**，证据落 `testing/<项目>-<功能>/run-*.md` + `evidence/`（沿用 test-login 已建范式）。
4. plan 的「验证命令」节中，凡标「用户可见路径」的命令，依据只能是 `人工确认：<理由>` 指向 browser/manual 证据，**不得写 `curl ... && echo ok` 充当通过**。

## 2. 入口矩阵（来自 SKILL.md §8）

每个用户可见入口（按钮、弹窗含 iframe、整页跳转、深链、回调页、脚本）都要有执行记录；e2e 通过证据必须是 `browser` 或 `manual`。`curl`/API 200 只证明协议链。

## 3. Reviewer 检查点

- [ ] 是否有把 `curl` 当 e2e / 会话闭环通过证据的地方 → 有即 `changes_requested`
- [ ] 每个 M 系列 AC 是否有 browser/manual 原始证据
- [ ] 证据是否落 `run-*.md` + `evidence/`，而非只在会话里说「测过了」

## 4. browser 证据的形态：Ego Light 操作序列

本工作流的用户可见路径证据走 **Ego Light**（`ego-browser`）——不为它另起一套 Playwright / Cypress runner。可复跑性靠**用例形态**保证，不靠新 runner：[`templates/testing/testcases.yaml.example`](../templates/testing/testcases.yaml.example) 每条 `type: browser` 用例都带 `steps`（可直接照做的操作序列）与 `expect`（预期结果），执行时把逐字输出、截图、DOM、网络证据贴进 `run-*.md` 的证据列。改一行代码要重跑哪些用例，就是查 `testcases.yaml` 的 `source` / `ac` 一次查询，而不是回忆上次点过哪里。

四类边界（连点 / 超时 / 过期 / 退出失败）已在该样例里逐条写成 Ego Light 序列；边界清单在测试计划中必选，不适用也要逐项写理由（见 [`execution.md`](execution.md)）。需要重复执行的序列从一次性草稿提升为 `testing/<项目>-<功能>/scripts/` 下的进仓脚本——仍是同一套 Ego Light 路线。

脚本通过不替代 `manual` 目视验收（视觉与文案判不了），也不证明 api 契约；反过来 `api` 通过只许表述为「api 层通过」。目标仓**本来就有** Playwright / Cypress 时按 [`execution.md`](execution.md) 的 D1 口径用既有 runner，不新起平行套件；为一个纯 Ego Light 项目新增 runner 才是被禁的形态。
