---
class_id: merge-integration-quality-gate
title: 分支合并/集成产物缺质量门——清冲突标记冒充验收
status: consolidated
consolidated_in: 0.8.2
first_record: BUG-20260920-01
occurrences:
  - BUG-20260920-01
recorded_at: 2026-09-20T00:00:00Z
updated_at: 2026-09-20T06:00:00Z
---

## 类模式

多分支合并/解冲突类任务的产物缺少质量门：合并/集成形态不在 agentflow 的触发判据（skill
description 枚举、用户级清单）、路由表与质量条款（硬边界 3 无质量句）的枚举里，评审门纪律
全部位于 skill workflow 内、skill 未加载时结构上不可能生效；执行者以「清冲突标记」级别的
自检冒充验收，解冲突引入的相邻行重复等缺陷直达用户。首现：supervisor 亲解冲突，Edit 边界
误判使 `func (c *Config) validate() error {` 声明行相邻重复进入交付，交付前自检仅 grep
冲突标记，用户验收执行 `go build` 才抓出（详见首现记录）。

## 归纳内容（已吸收进 Agentflow 的哪一层）

已归纳于 Agentflow 0.8.2（`status: consolidated`，`consolidated_in: 0.8.2`；用户已批准晋升，
版本已 bump、packaging/runtime 已重建、门检全绿）。四文件条款已发布落地（原候选计划改完成
时态）：`skills/agentflow/SKILL.md` description 枚举已补 branch integration and conflict
resolution；第 6 步 Integrate 已扩写合并质量门（触发条件/确定性检查原始输出/「清冲突标记
不是检查」反模式/宿主规则不构成豁免的裁决句）；`skills/agentflow/references/roles.md`
路由表已补一行（中文镜像 `docs/agent-roles.md` 已同步）；`skills/agentflow/references/contracts.md`
硬边界 3 末尾已接质量句（授权≠验证，清标记不是检查）。预防效果待对照验证（无 instrumented
merge/integration 用例，measurement: none），不写「已防住」。

## 再犯历史

| 次序 | 记录 | 发现版本 | 归纳后？ | 处置 |
| --- | --- | --- | --- | --- |
| 1 | [BUG-20260920-01](../2026-09-20/merge-conflict-resolution-quality-gate-gap.md) | 0.8.1 | 否（归纳前） | 0.8.2 已归纳落地；预防效果待对照验证（无 instrumented 用例，measurement: none） |

注：本类与 BUG-20260917-01（git 集成的授权侧缺口，0.4.2 修复）同属「分支集成」任务族，但
缺口面不同——那是授权（集成要不要问），这是质量（产物如何验收）；本次事件中 0.4.2 授权
约束按预期生效（合并本身是用户要求的，无越权）。两类记录不得聚类混并。

## 升级条件（再犯时怎么加重）

同一类缺陷在归纳版本之后的 Agentflow 版本再次出现时（新记录带
`class_id: merge-integration-quality-gate` 且 `agentflow_version` 高于 `consolidated_in`），
`python3 tools/lab/validate.py recurrence` 会把该类标为 `escalated`，并按首现记录写明的
触发条件升级为评测用例；归纳状态回到 `unconsolidated`，直到新版本重新归纳。当前为单次
出现；tier 由 `validate.py recurrence` 推导，不手写。
