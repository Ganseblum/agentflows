---
bug_id: ISS-2026-049
title: 结构改造批四期——plan 归入 feature 批次、顶层 plans/ 撤销、改进环死代码清除（用户授权）
status: verified
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - tools/lab/validate.py
  - tools/lab/record_store.py
  - docs/features/README.md
  - docs/features/feature-2026-09-19-产品线完善/README.md
  - tests/test_lab_contracts.py
  - docs/PENDING-DECISIONS.md
  - AGENTS.md
recorded_at: 2026-10-12T18:28:00+08:00
source_revision: agentflows@cc03012 + 本批工作树（2026-10-12）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-12）
regression_status: pass
updated_at: 2026-10-19T21:45:00+08:00
reviewer: agentflow:reviewer（2026-10-19 独立批量复审）
review_decision: approved
closure_criteria: `docs/plans/` 不在盘 + 两份 PLAN 位于 feature 批次 plan/ 且过 artifacts 门 + validate.py 无 improvements 遍历分支与 validate_improvement_* 函数 + LIVE_RECORD_ROOTS 五根 + validate.py all PASS。
---

## 现象

用户对比 youc-workflow-ai 与 aiwork-workflow-ai 后指出：「正常是有 feature 需求在进行 plan 和 spec、design 之类的，包括 issue」，判定顶层 `docs/plans/` 与版本散文守卫下的散设计文档是结构不合理的根。排查证实三类负担为真：

1. 顶层 `docs/plans/` 单挂两份计划（PLAN-PRODUCT-001 / PLAN-LOOP-SMOKE-001）与 PENDING-DECISIONS——而两个参考仓里 **plan 是 feature 批次的组成部分**（`features/<批次>/plan/`），不存在顶层 plans 根。
2. 改进三件套停用（三期）后，`validate.py` 里的 `improvements` 遍历分支、`validate_improvement_document`、`validate_improvement_cross_references`、schema 常量块全部成为无调用路径的死代码；对应的 12 个 workspace 级测试同时失去宿主。
3. 三期遗留 10 个挂起测试（用户停手令冻结）——fixture 与已停用机制不再一致。

## 根因

顶层 plans/ 根是 2026-10 结构改造时的目录平移遗留：当时把「记录」按类型平铺，未按「工作进行中的容器」组织；参考仓的形态证明计划应随批次走。死代码则来自「机制停用只摘调用、不删实现」的半步处置——停用不留残留是同一个纪律的两面。

## 修复

1. 两份计划迁入 `docs/features/feature-2026-09-19-产品线完善/plan/`（批次 README 建立段落映射：proposal/spec/design 由 `docs/product/` 链承载，不重复造册）；`PENDING-DECISIONS.md` 提到 `docs/PENDING-DECISIONS.md`（跨批次拍板口，在任何记录根之外）；顶层 `docs/plans/` 撤销。
2. `validate.py`：`LIVE_RECORD_ROOTS` 收敛为 `docs/issues / docs/releases / docs/features / episodes / reviews`；新增 features 分支（只校验 `<批次>/plan/<plan_id>.md` 的计划契约，README/proposal/spec/design 归文档链 linter）；删除 improvements 分支、`validate_improvement_document`、`validate_improvement_cross_references` 与改进环 schema 常量块（死代码）；`record_store.py` 默认根同步。
3. 测试收尾：`ImprovementArtifactContractTests`（12 个失去宿主的断言）退役；roots 钉子收敛为五根；fixture 对齐新根布局（releases 只放声明工作文件、features 增 plan 契约正反例）；`docs/features/README.md` 增「升格与登记」条款。
4. 活面引用全量改指（AGENTS / README / index / project-structure / system-guide / releases 两份 / reviewer / plan-architect / tools/lab README / packaging README / issues README）；`plans/README.md` 的计划形态契约并入 `docs/features/README.md`。

## 回归检查

- `python3 tools/lab/validate.py all` → 9×PASS（schemas/examples/evals/artifacts/protected/manifests/docs/tests/doc_chain），exit=0。
- `python3 -m unittest discover -s tests` → 124 全 OK（139 → 124：改进环 12 个退役、新增 features 契约与 releases 边界用例后净减 15）。
- 活面 `docs/plans` / `plans/PENDING-DECISIONS` / `plans/README` grep 零残留；批次内两份 PLAN 的计划契约在 artifacts 门内实测通过（含任务依赖图）。
- `installed` 待 runtime 重建后复验（本批改动的 agents/reviewer.md、plan-architect.md 在安装面内）。

## 审查

2026-10-19 独立复审（agentflow:reviewer 子代理，只读）。修复声称核对成立：两份 PLAN 位于 docs/features/feature-2026-09-19-产品线完善/plan/；`docs/plans/` 不在盘；PENDING-DECISIONS.md 提至 docs/ 根；改进环死代码零残留（validate_improvement_* 函数无命中）。回归证据：validate all 9×PASS、unittest 96 OK。review_decision：approved。

## 变更记录

- 2026-10-12 · recorded + fixed · 四期落地（含用户停手令范围的脚本收尾一次性完成）；fix_revision 随本批提交
- 2026-10-19 21:45 · 独立复审通过 · agentflow:reviewer 批量复审（只读）核对修复声称与回归证据成立，转 verified。
