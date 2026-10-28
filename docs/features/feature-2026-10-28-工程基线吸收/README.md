# feature-2026-10-28-工程基线吸收 — 把目标仓的工程事实接进主流程

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

- 需求原文：2026-10-28 用户指示「看看 `/Users/lihanghang1/Desktop/WorkProject/ts/fe/total-security`
  里面那些 agents.md、rules，以及 claude、cursor 下的 skill 和各种 md、各种 spec，还有
  `/Users/lihanghang1/Desktop/TestProject/Youc/youc-workflow-ai/workflow`，看看沉淀吸收一下，
  增强一些 agent、或者 skill 等我的 agentflow 能力」。经一次问答拍定范围为 **P1 四项 + 完整文档链**；
  2026-10-28 用户指出第一轮只补后端与测试、FE 不对称，追加 **G5/M05（FE 实现纪律）**，要求「合适的都补充，全部仔细看一遍」。
- 主实施仓：本仓（agentflows）。相关系统：无。UI 轨：未启用。埋点：N/A。
- 状态：链已成文、原四项实施与独立评审通过；2026-10-28 追加 M05（FE）增量实施与评审中。唯一权威状态源是
  `plan/PLAN-BASE-001.md` 的任务看板；本 README 只作入口索引。
- 评审档位（如实）：本批立项时宿主子代理委派能力可用（2026-10-28 实测派发成功），两个入口门按
  L1 档由独立 `reviewer` 承担，经四轮收敛后 approved；记录 `reviews/review-2026-10-28-001.md`。
  FE 增量未做独立评审：用户 2026-10-28 明确拒绝派发子代理，T12 记 ⚠；不写成已批准。
- 并发环境（如实）：工作树为多会话共享。实施期间另一会话在做 ISS 记录改名与门工具修改，共享树曾出现
  中间状态为红；16:10 复跑共享树 `validate.py all` 为 11/11 PASS。本批另用干净副本（克隆当前提交 +
  只叠加本批 hunk）复跑同为 11/11 PASS。两份原始输出都在 `testing/agentflow-baseline/evidence/`。本批不修改、不提交另一会话的源文件。`packaging/runtime` 是全树生成物；本批的生成树文件只有：五份 manifest、`agents/backend-engineer.md`、`agents/test-planner.md`、`skills/agentflow/SKILL.md`、`skills/agentflow/references/document-chain.md`、`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/README.md`、`skills/agentflow/templates/engineering/`、`skills/agentflow/templates/feature/design/be/backend.md`、`skills/agentflow/templates/feature/prototype/README.md`、`skills/agentflow/templates/testing/plan.md`、`agents/frontend-engineer.md`、`skills/agentflow/templates/feature/design/fe/frontend.md`、`skills/agentflow/templates/feature/spec/fe/frontend.md`。其余生成树改动（含 `schemas/` 与 `tools/lab/docchain/`）属另一会话；**2026-10-28 晚该会话的改动已并入 `main`（`d5b52ce`），生成树已在那棵干净树上重建并与源面逐字节一致（`validate.py manifests` PASS）**，本段原有的「不得随本批提交 / 待其落定后再重建」约束随之失效。其中 `skills/agentflow/SKILL.md`、`skills/agentflow/templates/README.md`、`skills/agentflow/templates/testing/plan.md`、`agents/test-planner.md` 在工作树里还混有另一会话的 ID 格式改名（`REV/TP/ISS-<YYYY-MM-DD>`），`skills/agentflow/references/hosts.md` 还混有另一会话新增的 `templates/hub/repo-rules.md` 链接；干净副本复跑脚本按 hunk 只叠加本批改动，不含这些外部改动。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 两处语料的盘点、已覆盖项、四项缺口与不做事项 |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 模板必填字段口径、验收判据 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 落点决策、状态图/流程图/失败分支、字段级契约与验证矩阵 |
| plan | `plan/PLAN-BASE-001.md` | 执行计划（任务看板 + 状态与证据回写） |
| testing | `testing/agentflow-baseline/` | 门禁原始输出 |
| reviews | `reviews/` | 独立评审记录落点 |

## 推进进度

> 规则：完成即将行首 ☐ 改 ☑；不适用改 ☑ 并写 (N/A: 原因)；评审类门禁只能由独立评审勾选。

### 1. Proposal [PM]
☑ 主稿已成文（`proposal/proposal.md`），含两处语料盘点、已覆盖项与四项缺口

### 2. Spec [按角色]
☑ spec/be 已成文（`spec/be/backend.md`），含 Proposal 反审 checklist，阻塞项已关闭；2026-10-28 追加 M05（FE）
☑ spec/qa 已成文（`spec/qa/acceptance.md`），验收点与判据预先写定

### 3. 需求评审 [门禁]
☑ 独立评审通过（L1 档，四轮收敛；记录 `reviews/review-2026-10-28-001.md`）

### 4. Design [按角色]
☑ design/be 已成文（`design/be/backend.md`）
☑ design/qa 已成文（`design/qa/testing.md`）

### 5. 技术方案评审 [门禁]
☑ 独立评审通过（同一记录覆盖设计与实现；`reviews/review-2026-10-28-001.md`）

### 6. Plan [执行契约]
☑ 已成文（`plan/PLAN-BASE-001.md`）

### 7. 实施与验证
◐ 原四项 9/9 已完成并通过评审；FE 增量 T10/T11 完成、门禁全绿；T12 独立评审因用户拒绝派发子代理而 ⚠ 未运行（不写成已批准）

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 目标仓工程基线可落地 | `proposal/proposal.md` §1.2 | M01，G1-AC-01 至 G1-AC-03 | T01、T02、T06、T07、T08、T09 | ☑ 已完成 |
| G2 后端数据与配置设计可核对 | `proposal/proposal.md` §1.2 | M02，G2-AC-01、G2-AC-02 | T03、T07 | ☑ 已完成 |
| G3 原型可点性与 Mock 约定可判定 | `proposal/proposal.md` §1.2 | M03，G3-AC-01、G3-AC-02 | T04、T07 | ☑ 已完成 |
| G4 测试设计的三类易漏维度进入计划 | `proposal/proposal.md` §1.2 | M04，G4-AC-01、G4-AC-02 | T05、T07 | ☑ 已完成 |
| G5 前端实现纪律与设计核对可执行 | `proposal/proposal.md` §1.2 | M05，G5-AC-01 至 G5-AC-04 | T10、T11、T12 | ⚠ 阻塞（实现与门完成；独立评审 T12 未运行） |

> T09（独立评审）覆盖 G1–G4 四个目标；承接表只在 G1 行列出一次，避免重复。T12 覆盖 G5 的增量评审。
