# feature-2026-10-28-评测整改批 — 让整改可追踪、让评审能力可分级

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户对全面评测报告的回应「可以，全部处理吧」；评测结论见
  `docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md`（本批 proposal 逐字保留其五批方案）。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 状态：链已成文并执行。唯一权威状态源是 `plan/PLAN-EVAL-001.md` 的任务看板；本 README 只作入口索引。
- 独立评审边界（如实）：本批实施期间宿主子代理并发额度不可用（连续 5 次派发返回
  `model concurrency limit exceeded`），**需求评审门与技术方案评审门均按 L0 档执行**——由
  主审自审并显式登记 `review_tier: L0`，恢复委派能力后须补一次独立复核。分级协议本身
  就是本批 G2 要写入 `contracts.md` 的产物，见 `design/be/backend.md` §3。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 五批整改范围与不做事项（含评测报告原文定位） |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 门与契约字段口径、验收判据 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 评审分级状态机、异常矩阵、回滚点 |
| plan | `plan/PLAN-EVAL-001.md` | 执行计划（任务看板 + 状态与证据回写） |
| testing | `testing/` | 门基线与变异复跑输出 |
| reviews | `reviews/` | `review-2026-10-28-001.md`（L2 / approved / source_revision 26988a4） |

## 推进进度

> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），目标 G1–G5 与不做事项齐备

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist，阻塞项已关闭
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☑ 独立 L2 复核 `approved`（`reviews/review-2026-10-28-001.md`；原 L0 欠账已由 DEBT T02 清偿）

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☑ 独立 L2 复核 `approved`（`reviews/review-2026-10-28-001.md`）

### 6. Plan [执行契约]
☑ 已成文并执行（`plan/PLAN-EVAL-001.md`）

### 7. 实施与验证
◐ 实施中；权威进度以计划看板为准

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 整改可追踪 | `proposal/proposal.md` §1.2 | M01，G1-AC-01、G1-AC-02 | T01、T02、T12 | ☑ 已完成 |
| G2 评审能力可分级 | `proposal/proposal.md` §1.2 | M02，G2-AC-01 至 G2-AC-03 | T03、T04 | ☑ 已完成 |
| G3 表达面收敛 | `proposal/proposal.md` §1.2 | M03，G3-AC-01、G3-AC-02 | T05、T06 | ☑ 已完成 |
| G4 本地门基线可达 | `proposal/proposal.md` §1.2 | M04，G4-AC-01、G4-AC-02 | T07、T08、T11、T12 | ☑ 已完成 |
| G5 改进环首次真实闭环 | `proposal/proposal.md` §1.2 | M05，G5-AC-01、G5-AC-02 | T09、T10 | ☑ 已完成 |

## 当前步骤

按 `plan/PLAN-EVAL-001.md` 的 T01–T10 顺序执行；每完成一项在同一变更里回写看板的
「状态」与「证据」两列。验证命令见计划末节。
