# Agentflow 产品文档链总览

本目录是 Agentflow 产品自身的文档链唯一入口，按 `proposal -> spec -> design -> plan`
主链组织。方法与工具的"为什么做、做成什么、怎么实现、接下来做什么"分别收口在四层，
上层不重复下层内容，只引用。

> 与旧设计文档的关系：`docs/self-improvement-design.md`、`docs/host-native-plugin-design.md`、
> `docs/agent-product-boundary.md` 是本链建立之前的决策记录，**保留原位不迁移**（多处记录
> 引用其路径，移动即断链）。本链把它们降级为证据引用：结论收口进本链，原文作为决策出处。
> 两处内容冲突时，以本链为准并回到旧文档补翻案记录。

推荐阅读顺序：

`proposal -> spec -> design -> plans/`

## 元信息

- 产品名称：Agentflow（宿主原生多角色协作方法插件）
- 主实施仓：本仓库（方法、角色、仪器、记录契约同仓）
- 分发形态：ZCode / Claude Code / Codex 宿主插件，marketplace 源指向
  `packaging/build_runtime.py` 生成的瘦快照
- 最后更新时间：`2026-09-20`

## 推进进度

> 规则：完成即将行首 `☐` 改为 `☑`；不适用改为 `☑` 并写 `(N/A: 原因)`；勾选时在行尾附上
> 文档相对链接。评审类门禁只能由**独立评审**勾选（作者不自证，硬边界 1）——作者成稿后
> 门禁保持 `☐`，直到独立评审跑过并给出 `approved`。

### 1. Proposal

- ☑ `proposal/proposal.md` 主稿 [→](./proposal/proposal.md)（含背景/目标/范围/核心原则/待冻结台账）

### 2. Spec [含 Proposal 反审]

> Spec 成稿时对照 Proposal 逐条挑缺口，登记为 §0 反审 checklist。**阻塞项全部关闭后**
> 本小节方可勾选；不等于 Spec 阶段已完成。

- ☑ [方法] `spec/method-spec.md` 行为规格（含 Proposal 反审 checklist） [→](./spec/method-spec.md)
- ☑ [验收] `spec/acceptance-matrix.md` 规格条目 ↔ 机器标尺对照矩阵 [→](./spec/acceptance-matrix.md)

### 3. 需求评审 [门禁]

- ☐ 需求评审通过（独立评审，文档模式 review proposal/spec；阻塞项全关后勾选）

### 4. Design [技术方案]

- ☑ [总体] `design/product-design.md`（决策表 + 技术挑战 + 架构 + 负责不负责 + 影响面评估） [→](./design/product-design.md)
- ☐ 技术方案评审通过（独立评审，文档模式 review design；通过后 Design 阶段冻结）

### 5. Plan [执行契约]

- ☑ 方法改进线：`plans/PLAN-LOOP-SMOKE-001.md`（第一次 improve 闭环，live 对照阻塞于 U-01）
- ☑ 业务评测线：`plans/PLAN-BUSINESS-EVAL-001.md`（业务尺子，仪器就绪）
- ☑ 打包线：`plans/PLAN-PRODUCT-001.md`（产品线四步总账）
- ☑ 工具守卫线：`plans/PLAN-PY-GUARD-001.md`（解释器下限 fail-closed，已完成）

## 门禁语义

1. **Spec 反审门**：spec §0 checklist 里标「阻塞」的缺口未全部关闭前，不得进入 Design。
2. **需求评审门**：独立评审以文档模式 review proposal 与 spec，给出 `approved` /
   `changes_requested` / `blocked`；评审记录落 `reviews/`。
3. **技术方案评审门**：同上，对象为 design；通过后 Design 冻结，后续改动走设计变更记录
   （同 aiwork 决策表翻案格式：改结论须留推翻过程与理由）。
4. **Plan 前置门**：执行计划引用的设计结论以**冻结后的 design** 为准；冻结前的 plan 条目
   若引用了后续被推翻的决策，回写修正并在 plan 留痕。
