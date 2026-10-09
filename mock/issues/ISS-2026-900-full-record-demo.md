---
bug_id: ISS-2026-900
title: 【样板】演示记录——展示当前 issue 记录结构的全部字段与章节
status: verified
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
files:
  - skills/agentflow/references/contracts.md
  - demo-repo@abc1234:src/api/client.ts
affected_slices:
  - delegation-briefs
  - frontend-implementation
recorded_at: 2026-09-17T02:00:00Z
updated_at: 2026-09-17T03:00:00Z
source_revision: 779f9d4
agentflow_version: 0.4.2
reviewer: independent-reviewer-demo
review_decision: approved
regression_status: pass
closure_criteria: 演示用例断言该约束存在；`python3 tools/lab/validate.py all` 八项 PASS，删掉该断言时用例 FAIL
fix_revision: agentflows@779f9d4
---

## 现象

（演示）简报只声明了写入范围，未要求读取范围，实施者据此改动了一个被全局响应拦截器
覆盖的页面，导致该页面在合法未登录状态下被强制跳转到登录页。复现步骤：

1. 构造只含 `write_scope` 的简报并委派前端改动；
2. 改动落在「忘记密码」页（该页未登录是合法状态）；
3. 打开页面即被重定向——拦截器在 401 时跳登录页。

## 问题代码

```ts
// demo-repo@abc1234:src/api/client.ts
axios.interceptors.response.use(null, (error) => {
  if (error.response?.status === 401) router.push('/login')
  return Promise.reject(error)
})
```

简报规范缺少读取范围的原文（`demo-repo@abc1234:docs/brief-spec.md`）：

> 简报必须分别声明写入范围与读取范围；读取范围要覆盖改动经过的一切共享机制。只写写入
> 范围的简报按缺陷退回。

## 根因

简报纪律只约束了写入范围，没有要求追踪横切机制（拦截器/守卫/全局监听）到注册点，也
没有「表面 × 合法状态」矩阵——「忘记密码」页未登录是合法状态这一点在改动时没有任何
环节会被审到。归因 `workflow_policy`：缺的是流程约束，不是知识。

## 修复

`skills/agentflow/references/contracts.md` 增加隐式行为检查：写入/读取范围分离、
注册点搜索、表面 × 合法状态矩阵、空集显式声明。演示记录的修复已并入门禁校验。

## 回归检查

- pass：`python3 tools/lab/validate.py all` 八项 PASS；
- 反例验证：删去约束断言时对应用例 FAIL（演示值为示意）。

## 审查

- reviewer: independent-reviewer-demo
- decision: approved
- evidence: 演示证据引用——约束条款 `skills/agentflow/references/contracts.md` 隐式行为
  检查节；回归检查上述命令输出。

## 变更记录

- 2026-09-17 02:00 · 建档（open）· 演示记录创建，用于展示当前结构的全部字段与章节。
- 2026-09-17 03:00 · 转 verified · 补齐 reviewer / regression_status / closure_criteria，
  演示完整流转形态。
