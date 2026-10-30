# FE / BE 合并裁决复跑（2026-10-29）

> 来源：`docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` T16（承接 2026-10-28
> 治理批 T05/T06，拍板口第 22 条已由用户选定 C「分立并补实现深度」）。
> 本文件只记录复跑的数字与结论；语料与原始用例仍在同目录的 `plan-2026-10-13-001.md`。

## 1. 方法与限制

- 两个独立只读会话分别按 `agents/frontend-engineer.md` 与 `agents/backend-engineer.md` 行事，收到
  同一组用例输入，各自给出「结论 / 会改的路径 / 交回事项 / 理由」。
- 从 28 例中选可比子集 6 例：`TC-BACKEND-ENGINEER-01/02`、`TC-FRONTEND-ENGINEER-01/02`、
  `TC-TECHNICAL-DIRECTOR-01`、`TC-REVIEWER-01`。选择标准是「同一输入对两个实现角色都成立」；
  其余 22 例中 8 例属于 2026-10-29 已裁撤的改进环角色，14 例是角色专属输入，不构成同题对照。
- 这是**保守口径**：没有做 28 例全量双答（8 例的对象已不存在，全量不可能复现）。裁决按
  「任一条件不满足即保持分立」执行；重审触发条件见 §4。
- 模型标签：宿主未提供可靠标签，记 `unknown`；运行日期 2026-10-29。

## 2. 逐例结果

| 用例 | frontend-engineer | backend-engineer | 是否不一致 |
| --- | --- | --- | --- |
| TC-BACKEND-ENGINEER-01 | 不属于本角色，requires backend；不改文件 | 在 `src/api/orders/**` 内执行；越界部分 requires frontend | 是 |
| TC-BACKEND-ENGINEER-02 | 不属于本角色，requires backend；不改文件 | 在 `src/api/payments/**` 内执行；拒绝转述他人摘要 | 是 |
| TC-FRONTEND-ENGINEER-01 | 拒绝并上报：契约未确认前不改；共享组件需 Supervisor 授权 | 不属于本角色，requires frontend；不改文件 | 是 |
| TC-FRONTEND-ENGINEER-02 | 在 `src/web/orders/` 内执行；不拆薄封装 | 不属于本角色，requires frontend；不改文件 | 是 |
| TC-TECHNICAL-DIRECTOR-01 | 不属于本角色，requires technical-director | 不属于本角色，需 TD 决策 | 否 |
| TC-REVIEWER-01 | 不属于本角色，requires reviewer | 不属于本角色，requires reviewer | 否 |

## 3. 三条件数字

| 条件 | 判据 | 实测 | 结论 |
| --- | --- | --- | --- |
| ① 同场景判定不一致率 | 28 例中 ≤2 例不同结论（<10%） | 可比 6 例中 4 例不同（4/6）；28 例全量不可复现（8 例角色已裁撤、14 例角色专属） | 不满足，且样本不足以证明满足 |
| ② 产物所有权分歧项数 | 必须为 0，否则一票否决 | 2 项：前端独占 `src/web/**`、后端独占 `src/api/**`；共享组件另需 Supervisor 授权 | 不满足（一票否决） |
| ③ 合并稿行数 | ≤60 行 | frontend 44 行 + backend 35 行 = 79 行（未计合并后的公共头） | 不满足 |

## 4. 裁决与重审触发条件

**已裁决：保持分立。** 条件 ② 已经是一票否决——两个角色对「写哪些路径」的所有权不相交，
合并会让一个角色同时持有前端与后端两套写权限，属硬边界退让；条件 ③ 也独立失败。

重审触发条件（任一成立才重新开案）：

1. 角色面改版把 10 个角色的产物所有权矩阵统一成一张表，且前端/后端两列的写路径不再互斥；
2. 形成 ≥10 例「同一输入对两个角色都成立」的共享语料，且不一致率实测 <10%；
3. 宿主提供角色级环境隔离，使一个角色无法写入另一层的路径（届时「合并」不再是权限扩张）。

在此之前，本悬案关闭，不再以「待议」挂在 `roles.md` 里。
