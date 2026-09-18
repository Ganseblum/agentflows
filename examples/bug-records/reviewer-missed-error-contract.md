---
bug_id: BUG-API-001
title: Reviewer 接受错误响应结构变更但未核对客户端契约
status: verified
severity: P2
error_kind: ai-ignored-doc
attribution: role_prompt
provenance: agentflow
project: example-project
files:
  - example-project@r1:services/api/orders.go
  - example-project@r1:clients/web/src/api/orders.ts
affected_slices:
  - review
  - cross-layer
  - api-contract
recorded_at: 2026-09-13T23:40:00Z
updated_at: 2026-09-14T10:00:00Z
agentflow_version: 0.2.0
reviewer: independent-review-example
review_decision: approved
regression_status: pass
closure_criteria: AF-003 用例断言错误结构检查存在；`python3 tools/lab/validate.py evals` PASS，删掉该断言则用例 FAIL
fix_revision: mock-commit-abc123 (example)
---

## 现象

Reviewer 批准了一个后端改动：orders API 的错误响应结构被改变，而前端客户端仍在按旧结构
解析。计划中明确要求错误结构保持兼容，reviewer 只报告了成功响应路径。

## 问题代码

```go
// example-project@r1:services/api/orders.go — 错误信封从 {"error": "..."} 变为 {"code": ..., "message": ...}
func writeError(w http.ResponseWriter, err error) {
    json.NewEncoder(w).Encode(map[string]any{"code": "ORD-ERR", "message": err.Error()})
}
```

前端客户端仍按旧结构解析（`example-project@r1:clients/web/src/api/orders.ts`）：

> 客户端从 `resp.data.error` 读取错误文案；信封改为 `{code, message}` 后该字段为
> `undefined`，错误提示静默丢失。

## 根因

reviewer 角色提示词只写了"检查实现"，没有明确要求把声明的错误契约与消费方对照核查，
于是 reviewer 只验证了成功路径。归因 `ai-ignored-doc`：既有文档化契约没有被角色执行。

## 修复

reviewer 契约与公开评测用例现在显式要求错误结构与兼容性检查（见
`skills/agentflow/references/contracts.md` 与 `evals/public/AF-003.json`）。

## 回归检查

- pass：`python3 tools/lab/validate.py evals` —— API 契约审查用例强制检查错误结构。

## 审查

- reviewer: independent-review-example
- decision: approved
- evidence: review record E-API-REVIEW；修复后上述回归检查通过。

> [!WARNING]
> 残余风险：同类 `resp.data.error` 读取只核对了 orders 客户端，未做全仓扫描——其他服务端
> 点可能存在同形信封变更未被覆盖（演示 `records/README.md` 视觉标注约定）。

## 备注

脱敏示例记录。
