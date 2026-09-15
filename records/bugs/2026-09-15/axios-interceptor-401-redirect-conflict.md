---
bug_id: BUG-20260915-001
title: Shared axios 401 interceptor redirects on legitimately logged-out pages, breaking forgot/reset password
status: fixed-pending-review
severity: high
error_kind: missing-constraint
attribution: workflow_policy
project: paipai-new-fe
files:
  - skills/agentflow/references/contracts.md
  - agents/frontend-engineer.md
  - agents/reviewer.md
  - agents/bug-investigator.md
  - schemas/plan.schema.json
  - evals/public/AF-015.json
affected_slices:
  - delegation-briefs
  - frontend-implementation
  - independent-review
recorded_at: 2026-09-15T02:30:00Z
updated_at: 2026-09-15T02:30:00Z
source_revision: 33962ee
agentflow_version: 0.3.3
regression_status: pass
---

## Symptom

在全局 layout 的顶部导航加入自动登录：复用已有的 `login()` 方法，成功后同步状态栏，失败
本地 catch。该方法单独看是正确的——发请求、成功更新状态、失败捕获。

但项目的 HTTP 客户端是 axios 封装，封装内部注册了响应拦截器：响应体 `code === 401` 时
跳转登录页。忘记密码/重置密码页面渲染在同一个全局 layout 内、本来就处于未登录状态，
导航栏仍会在挂载时发出默认的自动登录请求 → 401 → 被拦截器强制跳转登录页，用户无法
正常使用忘记/重置密码流程。

补充同类的第二个风险面：当方法或参数从根层级经父节点传入时，传参链上的改写同样不在
局部 diff 内。

## Root cause

两个独立缺陷叠加，任何一个被注意到都能拦住它：

1. 追踪止步于被复用方法的自身逻辑（"失败已 catch，处理完了"），没有追进 axios 封装看
   到第二个错误处理者——横切机制在调用链的下一层就存在，但没人被要求去追。
2. 即使读到"401 → 跳登录页"，也需要结合"该页面合法地处于未登录态"才能看到冲突——
   表面 × 合法状态的交集检查缺失。

对 Agentflow 而言归因为 `workflow_policy`：委派简报只定义写入范围，未定义读取范围；
没有任何步骤要求枚举"不经调用栈直接触发却会运行的代码"。写入边界严格、读取边界空白。

## Fix

按两轮复核后收敛的设计落地（方案与理由见 `docs/spec-fact-check-design.md` 相关讨论及
本次会话记录）：

- `contracts.md`：简报拆分 `write_scope` / `read_scope`（读取范围必须严格大于写入范围）；
  新增隐式行为检查——共享机制按框架注册点搜索发现、结果显式声明（空集也要声明）、
  表面 × 合法状态矩阵逐格给出检查或显式"未测"、深度以注册点引用（`path:line`）为终止
  条件、残差声明（强制提问不证明正确）。
- `frontend-engineer.md`：调用复用方法或挂进共享 layout 前先追横切行为到注册点并引用；
  显式给出机制在合法异态下的行为假设。
- `reviewer.md`：改动触及共享机制时，要求机制触发条件合法成立的表面/状态上的行为级
  证据（"读过代码"不是证据）。
- `bug-investigator.md`：症状为意外全局行为时，先按注册点枚举隐式运行代码再归因调用链；
  机制与调用方冲突归因 `missing-constraint`。
- `schemas/plan.schema.json`：新增必填 `shared_mechanisms[]`（`registration_ref` 必填——
  每个声明机制必须引用其注册点；未涉及时显式空数组），正反例计划同步。
- `evals/public/AF-015.json`：本案例的回归用例。

## Regression check

- `python3 tools/lab/validate.py all` 全部 PASS（含新增 AF-015 与 plan schema 字段）。
- `python3 -m unittest discover -s tests` 6 个用例通过。
- AF-015 与 input 已入库，`validate.py evals` 通过。

## Notes

- `project: paipai-new-fe` 取自 `docs/spec-fact-check-design.md` §9.6 的目标仓库名，来自
  会话上下文推断，未对仓库本身核实；如实际项目名不同，按记录规则追加更正而非改写。
- 外部项目的修复不在本仓范围；本记录的 "fix" 指 Agentflow 侧的流程契约加固。
- 状态保持 `fixed-pending-review`：契约变更与用例由用户授权落地，尚无独立 Reviewer
  判定，按规则不得写 verified。
- 本记录连同 `evals/` 与 `plan.schema.json` 的改动属于门/契约面变更，依据用户 2026-09-15
  明确请求执行，需用户以人工审查者身份最终确认。
