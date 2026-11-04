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

## 4. 让 browser 证据可重跑

`browser` 证据若只在会话里点一次，下一次改动就没人重跑，等于把「链路通没通」退回给记忆力。新项目在首次铺测试栈时把那次点击固化成脚本：[`templates/testing/playwright/`](../templates/testing/playwright/README.md) 给了 config 与含边界用例（连点 / 超时 / 过期 / 退出失败）的测试骨架，`npm run test:e2e` 的逐字输出就是 `run-*.md` 的证据列内容。**老项目不动**——硬塞第二套 runner 会制造两套并行 e2e 套件，那是 `execution.md` 明确反对的形态。脚本通过不替代 manual 目视验收，也不证明 api 契约。
