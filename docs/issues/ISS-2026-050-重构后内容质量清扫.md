---
bug_id: ISS-2026-050
title: 内容质量批——四批结构改造后的活面过时内容全量复核与修正
status: fixed-pending-review
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - docs/product/spec/method-spec.md
  - docs/product/spec/acceptance-matrix.md
  - docs/product/design/product-design.md
  - docs/product/proposal/proposal.md
  - docs/product/README.md
  - docs/design-decisions.md
  - docs/system-guide.md
  - docs/releases/pending-test.md
  - index.md
recorded_at: 2026-10-12T18:34:00+08:00
source_revision: agentflows@cc03012 + 本批工作树（2026-10-12）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-12）
regression_status: pass
---

## 现象

用户「整体的内容质量检查一下，我改的东西比较多，把无效或者需要更新的都处理了」。四批结构改造（ISS-2026-046～049）后，机器门只覆盖断链与退役路径 token——**语义层面**的过时内容全部漏网，排查确认五类：

1. 产品规格与现状脱节：`method-spec.md` 的 S6 仍写「九类记录」与旧落点、S7 改进环仍标「待验证（U-01）」、S8 仍列已删的 `mock` 检查、S9 仍写「六个记录根」、S10 业务仪器整节仍写「待验证」（`seed_grader.py` 早已删除）；状态表中的 S7/S10/S12 行同病。
2. 验收矩阵引用已删台账：`acceptance-matrix.md` 头部指向 `docs/iteration-log.md`（ISS-2026-046 删除），S9 行声称「0.8.1 快照已重装比对」、S10 行标尺指向已删脚本。
3. 产品边界文档的对外口径过时：`agent-product-boundary.md` 仍描述「新增业务任务度量切片（仪器就绪）……首轮 smoke 实跑挂三个未决项」。
4. 计划与产品 README 的路径残留：`docs/product/README.md` 阅读顺序写 `plans/`、Plan 节引用旧路径、更新时间停在 2026-09-20；两份 PLAN 内引用 `plans/PENDING-DECISIONS.md` 与 `improvements/` 落点。
5. 索引重复行：`index.md` 迁移记录中四期条目被脚本插入两次（重复段落）。

## 根因

机器门的设计边界是「结构可判定的错误」（断链、退役 token、schema）；「描述与事实不符」需要语义判断，无门覆盖。四批改造逐批做了**被改对象的引用改指**，但未做**以现状为准的全文复核**——改动者视角（只改自己碰过的）与读者视角（通读是否还成立）的经典缺口。

## 修复

以「读者通读是否成立」为准绳，对全部活文档做语义复核并修正：

1. `method-spec.md`：S6 记录体系落点重写（`docs/issues/`、批次 `plan/`、`docs/releases/`）；S7 状态改「已停用（2026-10-12）」并把闭环口径标为「留存备查」；S8 检查清单删 `mock`、记为 9 项；S9 排除清单改五根口径；S10 整节标「已裁撤」；S12 状态改「条款生效 / 尚无首份证书」；S13 与 C-2 的 `plans/` 改批次 `plan/`；状态表 S6/S7/S10/S12 行同步。
2. `acceptance-matrix.md`：头部台账引用改 `CHANGELOG.md`；S7/S9/S10 行状态与标尺更新（停用/裁撤加删除线留痕）；「待建标尺」表更新。
3. `agent-product-boundary.md`：对外口径重写为「受治理的人工闭环」现状（业务切片裁撤、`measurement: none`、仪器存量保留）。
4. `docs/product/README.md`（阅读顺序、Plan 节路径、更新时间）、`proposal.md`（出处引用）、两份 PLAN（`docs/PENDING-DECISIONS.md` 路径、`improvements/` 落点标注）、`system-guide.md`（计划落点、Bug 记录路径、案例路径）、`product-design.md`（D5/D6、mermaid 记录根）逐项改指；`pending-test.md` 的历史数字加注（139→现 124）。
5. `index.md` 重复段删除。

## 回归检查

- `python3 tools/lab/validate.py all` → 9×PASS；`unittest` → 124 OK。
- 活文档旧根裸提法 grep（`plans/`、`issues/`、`releases/`、`九类记录`、`六个记录根`）在 README/AGENTS/index/docs/skills/agents 面零残留（历史记录与事实台账的时点引用除外）。
- 保留原则：`host-platform-facts.md` 的观察行（2026-09 时点的宿主事实）、`CHANGELOG.md`、`episodes/`、`docs/issues/` 记录正文按「时点证据」保持原样，不回写。

## 变更记录

- 2026-10-12 · recorded + fixed · 质量批落地（fix_revision 随本批提交）
- 2026-10-12 · 补充 · 本记录修正过的三份设计文档（host-native-plugin-design / self-improvement-design /
  agent-product-boundary）在同一日内合并为 `docs/design-decisions.md`（ISS-2026-051），files 条目随之一并改指。
