---
bug_id: ISS-2026-048
title: 结构改造批三期——记录根迁入 docs/、逐版本发布记录与改进三件套停用（用户拍板）
status: fixed-pending-review
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - tools/lab/validate.py
  - tools/lab/record_store.py
  - docs/issues/README.md
  - docs/features/README.md
  - skills/improve/SKILL.md
  - AGENTS.md
  - index.md
recorded_at: 2026-10-12T17:58:00+08:00
source_revision: agentflows@cc03012 + 本批工作树（2026-10-12）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-12）
regression_status: pass
---

## 现象

用户三轮拍板驱动三期结构改造：「plan、issues 放到 docs 下，弄 docs/feature 参考 youc-workflow-ai」「releases 很多版本没记录，就先不这样记录了」「improvements 看不懂干啥的，没用的就删除」。排查证实三类负担为真：

1. 顶层记录目录与文档目录割裂：`issues/`、`plans/` 与 `docs/` 平级，读者要在两处找「说明与记录」；批次目录 `features/` 空置顶层。
2. `releases/` 只有 0.8.4–0.8.6 三份版本 JSON，0.9.x / 0.10.0 从未补录——版本记录方式实际已断档，维护它是纯负债。
3. `improvements/`（14 个 JSON，全是 0.8.x 时代的改进三件套）在「人工治理 + 方法级改动一律 `measurement: none`」的现状下无活跃产出，读者无法从目录名读懂用途。

## 根因

三者都是「结构惯性」型负债：记录目录在 2026-10 结构改造时按「与 docs 平级的活区」落位，未从读者路径（说明与记录同处查）复核；版本 JSON 是逐次发布的手工登记义务，一断档就成了「补不完的账」；改进三件套是方法早期为自动改进环预留的仪器落点，实际运行收敛为人工治理后既无产出也无退役机制——共同缺口是缺一次「这套面今天还值不值」的整批审视（与一期同根）。

## 修复

1. `issues/` → `docs/issues/`、`plans/` → `docs/plans/`（记录与台账完整搬迁）；`releases/todo.md`、`pending-test.md` → `docs/releases/`，三份版本 JSON 与 README 删除（版本史单轨 `CHANGELOG.md`）；新建 `docs/features/`（形态对齐 youc-workflow-ai：`feature-<YYYY-MM-DD>-<主题>/` 五段骨架，README 载约定）。
2. `improvements/` 整目录删除（用户拍板「整目录删除」）；`skills/improve/SKILL.md` 的改进环落点条款改为「Supervisor 指派落点」；四个工程师角色的记录根清单同步。
3. 门配套（用户拍板授权的收敛部分）：`LIVE_RECORD_ROOTS` 收敛为 `docs/issues / docs/plans / docs/releases / episodes / reviews` 五根；遍历分支以 kind + 相对深度重写；releases 布局检查改为「仅 todo/pending-test 允许」；改进环 release 交叉检查段随停用移除；`record_store.py` 默认根同步。**脚本侧其余收尾（release 残段清理与 3 个 fixture 测试）按用户停手令冻结，待发话。**
4. 活面引用全量改指：AGENTS.md、README、index、project-structure、system-guide、product 链两份、四个角色文件、记录正文三处（ISS-026/030/040、两本台账）；`docs/issues/README.md` 与 `docs/plans/README.md` 的 schema 链接随深度改 `../../schemas/`。

## 回归检查

- `validate.py all`：schemas / examples / evals / artifacts / protected / manifests / docs / doc_chain PASS；tests 挂 10 个失败（fixture 待脚本收尾，用户停手令范围）。
- 活面 improvements 旧路径 grep 零残留（episodes 历史证据与 CHANGELOG 豁免）。

## 变更记录

- 2026-10-12 · recorded + fixed · 结构改造批三期落地（fix_revision 随本批提交）
- 2026-10-12 · 补充 · 对齐 youc-workflow-ai 收尾：`docs/spec-fact-check-design.md`（306 行讨论稿，2026-09-14 起未实施）删除，proposal OQ-2 与 project-structure 目录树同步改写；该文件不在版本散文守卫清单，未触碰脚本。三份 VERSION_PROSE 设计文档（host-native-plugin-design / self-improvement-design / agent-product-boundary）被 `validate.py` 守卫钉住，合并须改守卫清单——按停手令保留待发话。
