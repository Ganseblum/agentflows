---
bug_id: BUG-20260915-001
title: 共享 axios 401 拦截器在合法未登录页面触发跳转，破坏忘记/重置密码流程
status: verified
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: paipai-new-fe
files:
  - skills/agentflow/references/contracts.md
  - agents/frontend-engineer.md
  - agents/reviewer.md
  - agents/bug-investigator.md
  - schemas/plan.schema.json
  - evals/public/AF-015.json
  - agents/backend-engineer.md
affected_slices:
  - delegation-briefs
  - frontend-implementation
  - independent-review
recorded_at: 2026-09-15T02:30:00Z
updated_at: 2026-09-17T16:00:00Z
source_revision: 33962ee
agentflow_version: 0.3.3
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 前置更正（修复段更正小节，2026-09-17 追加）落地后生效：契约幸存载体为 `skills/agentflow/references/contracts.md:28-52`（简报拆分 write_scope/read_scope 与隐式行为检查）、`agents/frontend-engineer.md:22`、`agents/backend-engineer.md:22`、`agents/reviewer.md:30`、`agents/bug-investigator.md:20-24`、`agents/plan-architect.md:42`（可选「接口与共享机制」节加提示词纪律——每个机制引用注册点、空集显式声明）；机器面移除实证为 `grep -c shared_mechanisms schemas/plan.schema.json` 输出 0，且 `validate.py` 的 PLAN_REQUIRED_HEADINGS（`tools/lab/validate.py:496-500`）不含该节；`python3 tools/lab/validate.py all` 退出码 0；再犯检测器为 recurrence 环（同类再犯自动翻 escalated 持续报警）。
fix_revision: agentflow 0.3.4
---

## 现象

在全局 layout 的顶部导航加入自动登录：复用已有的 `login()` 方法，成功后同步状态栏，失败
本地 catch。该方法单独看是正确的——发请求、成功更新状态、失败捕获。

但项目的 HTTP 客户端是 axios 封装，封装内部注册了响应拦截器：响应体 `code === 401` 时
跳转登录页。忘记密码/重置密码页面渲染在同一个全局 layout 内、本来就处于未登录状态，
导航栏仍会在挂载时发出默认的自动登录请求 → 401 → 被拦截器强制跳转登录页，用户无法
正常使用忘记/重置密码流程。

补充同类的第二个风险面：当方法或参数从根层级经父节点传入时，传参链上的改写同样不在
局部 diff 内。

## 根因

两个独立缺陷叠加，任何一个被注意到都能拦住它：

1. 追踪止步于被复用方法的自身逻辑（"失败已 catch，处理完了"），没有追进 axios 封装看
   到第二个错误处理者——横切机制在调用链的下一层就存在，但没人被要求去追。
2. 即使读到"401 → 跳登录页"，也需要结合"该页面合法地处于未登录态"才能看到冲突——
   表面 × 合法状态的交集检查缺失。

对 Agentflow 而言归因为 `workflow_policy`：委派简报只定义写入范围，未定义读取范围；
没有任何步骤要求枚举"不经调用栈直接触发却会运行的代码"。写入边界严格、读取边界空白。

## 修复

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

### 更正（2026-09-17 · 独立评审）：`shared_mechanisms[]` 机器强制面已随 0.5.0 移除

本小节为评审要求的更正，追加于原文之后，上文不改写。上列修复中
`schemas/plan.schema.json` 的必填 `shared_mechanisms[]` 是当时的机器强制面；该机器面已于
agentflow 0.5.0 随计划契约改为 Markdown 混合体被整体移除（CHANGELOG 0.5.0 节自述
"plan schema rewritten, plan validation rewritten"），现行替代为可选「## 接口与共享机制」
正文节加 plan-architect 提示词纪律。CHANGELOG 0.5.0 节（`CHANGELOG.md`，:124-125）自述
替代形态：

> optional `## 接口与共享机制` (contracts + exception matrix + release order × rollback
> points), `## 验证命令`.

机器面现状（C8 实证）：`validate.py` 的 `PLAN_REQUIRED_HEADINGS`（现
`tools/lab/validate.py:496-500`）恰含「进展概览 / 任务清单 / 验证命令」三节，不含
「接口与共享机制」；`grep -c shared_mechanisms schemas/plan.schema.json` 输出 0（grep
退出码 1）。契约纪律的幸存载体清单见 `closure_criteria` 与 `## 审查`。

## 回归检查

- `python3 tools/lab/validate.py all` 全部 PASS（含新增 AF-015 与 plan schema 字段）。
- `python3 -m unittest discover -s tests` 6 个用例通过。
- AF-015 与 input 已入库，`validate.py evals` 通过。

## 备注

- `project: paipai-new-fe` 取自 `docs/spec-fact-check-design.md` §9.6 的目标仓库名，来自
  会话上下文推断，未对仓库本身核实；如实际项目名不同，按记录规则追加更正而非改写。
- 外部项目的修复不在本仓范围；本记录的 "fix" 指 Agentflow 侧的流程契约加固。
- 状态保持 `fixed-pending-review`：契约变更与用例由用户授权落地，尚无独立 Reviewer
  判定，按规则不得写 verified。
- 本记录连同 `evals/` 与 `plan.schema.json` 的改动属于门/契约面变更，依据用户 2026-09-15
  明确请求执行，需用户以人工审查者身份最终确认。

## 审查

评审人 `agentflow:reviewer` 于 2026-09-17 批量评审本批 8 条 `fixed-pending-review` 记录。
本条先执行评审指定的更正（「## 修复」段末追加的机器面移除更正小节），随后按更正后的
事实翻转：指定检查 C0（全量确定性检查）、C7（幸存载体原文命中）与 C8（机器面移除实证）
由 supervisor 执行并回传原始输出；结论 `approved`，本记录转 `verified`，`fix_revision`
据实回填为 agentflow 0.3.4。

决定性证据（supervisor 回传，逐字输出）：

C0 —— `python3 tools/lab/validate.py all`：

```
8/8 PASS, exit 0
```

C7 —— 幸存载体原文命中（`skills/agentflow/references/contracts.md:28-52`，简报拆分与
隐式行为检查）：

```
write_scope: files the worker may edit
read_scope: files, call paths, and shared mechanisms the worker must read first
```

```
**Implicit-behavior check.** Before implementing against any reused method, shared component, or shared layout, the brief must be answerable for three bounded dimensions:
```

C8 —— 机器面移除实证（`grep -c shared_mechanisms schemas/plan.schema.json`，grep 退出码 1）：

```
0
```

`tools/lab/validate.py:496-500` 的 `PLAN_REQUIRED_HEADINGS`：

```python
PLAN_REQUIRED_HEADINGS = (
    "## 进展概览",
    "## 任务清单",
    "## 验证命令",
)
```

恰三节，不含「接口与共享机制」。

## 变更记录

- 2026-09-17 · 独立评审通过 · agentflow:reviewer 批量评审指定检查（C0–C8），supervisor 执行并回传原始输出，转 verified。
