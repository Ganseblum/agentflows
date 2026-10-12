---
bug_id: ISS-2026-047
title: 瘦身批二期——归档桶裁撤、已完成批次删除与门豁免收敛（用户授权的门变更）
status: fixed-pending-review
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - tools/lab/validate.py
  - tests/test_lab_contracts.py
  - skills/agentflow/references/test-records.md
  - skills/agentflow/references/contracts.md
  - README.md
  - index.md
recorded_at: 2026-10-12T17:30:00+08:00
source_revision: agentflows@cc03012 + 本批工作树（2026-10-12）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-12）
regression_status: pass
---

## 现象

用户以「不用留归档的东西，直接开始全面升级改造，做项目级别的瘦身和专业能力提升，大刀阔斧的改 只要合理就行」驱动二期瘦身。排查证实四类负担为真：

1. `_archive/`（audit-2026-09 / handoff-2026-10 / records-2026-10，14 个跟踪文件）：三份冻结档全部可在 git 历史回溯，归档桶本身让门逻辑与文档面长期背着一套豁免（FROZEN_ARCHIVE_ROOT、handoff 指针豁免、live_doc_paths 排除、schema/断链扫描排除）。
2. `features/feature-2026-10-09-结构改造/` 与 `features/feature-2026-10-09-彻底清理与防漂移/`：两个已完成批次（13 个跟踪文件），执行叙事已由 CHANGELOG 与 episode 承载；`index.md`、`issues/README.md`、`releases/README.md` 仍链接其 migration-mapping。
3. `docs/self-improvement-design.md` 头部仍宣称「业务任务度量切片（`evals/business/`）仪器就绪」——该切片已在同日精简批（ISS-2026-046）裁撤，典型的「没更新的过时面」；`README.md` 目录表同样还列着已删的角色镜像与迭代日志。
4. `_archive/records-2026-10/tests/README.md` 是被 4 个活契约（SKILL、plan-architect、test-planner、test-executor）引用的测试记录形态说明——上一批误冻：它讲的是现行 `features/<批次>/testing/` 路径，且内含两处退役路径（`records/tests`、`records/bugs`）。

## 根因

归档桶是「以防万一」型预留面的最终形态：一旦存在，门要为它开豁免、文档要为它留入口、读者要为它付阅读税，而 git 本身就是不可变历史——归档桶没有提供 git 给不了的东西。测试记录 README 被误冻则是 2026-10 结构改造批次按目录整树迁移时未逐件核对「活契约 vs 历史」。

## 修复

用户显式授权门变更（「大刀阔斧的改 只要合理就行」），整批执行：

1. 删 `_archive/` 整目录、两个已完成 `features/` 批次目录与 `.zcode/` 会话残留；本仓不再保留归档桶。
2. `validate.py` 摘除 `FROZEN_ARCHIVE_ROOT`、`FROZEN_HANDOFF_PREFIX`、`live_doc_paths` 的 `_archive/` 排除与 `MIGRATION_RECORD_DIRS` 豁免；`HISTORICAL_DOC_CARRIERS` 收敛为 `CHANGELOG.md`；`RETIRED_PATH_TOKENS` 增补 `docs/iteration-log` 与 `docs/agent-roles`（防重建漂移）；token 扫描新增**仓限定地址剔除**——`<repo>@<revision>:<path>` 是记录契约认可的证据地址而非主张，历史记录引用含退役 token 的历史路径（如 `agentflows@0.8.2:docs/agent-roles.md`）不再误报。
3. 测试同步：豁免判别测试重写为「仅豁免 runtime 与 CHANGELOG」+ 新增「重建退役载体必触发 token 扫描」反向断言 + 仓限定地址钉子。
4. `test-records.md` 恢复至 `skills/agentflow/references/`（4 处引用改指），随恢复修正两处过时路径；`contracts.md` 三级冻结条款改写为两级（L3 = 删除 + git 回溯）。
5. 活面引用全量改指（README、index、project-structure、system-guide、spec-fact-check-design、self-improvement-design、issues/README、releases/README、plans×3、PENDING-DECISIONS、product/README、method-spec）；ISS-2026-005/006 的 `_archive` files 条目改仓限定引用并补 blockquote 片段；README 目录表同步摘除已删面的描述。

## 回归检查

- `python3 tools/lab/validate.py all` → 9×PASS（schemas/examples/evals/artifacts/protected/manifests/docs/tests/doc_chain），exit=0。
- `python3 -m unittest discover -s tests` → 139 全 OK。
- 全仓活面 grep（`_archive` / `seed_grader` / `evals/business`，剔除 CHANGELOG 历史与仓限定地址）→ 零命中。
- 被删内容可回溯性核对：`git ls-files` 确认 14 个 `_archive` 跟踪文件与 13 个 `features` 跟踪文件全部在 HEAD；唯一未跟踪件 `_archive/records-2026-10/PLAN-BUSINESS-EVAL-001.md` 的原身 `plans/PLAN-BUSINESS-EVAL-001.md` 在 HEAD。
- runtime 重建后 `validate.py installed` 待随本批提交复验。

## 变更记录

- 2026-10-12 · recorded + fixed · 瘦身批二期落地（fix_revision 随本批提交）
