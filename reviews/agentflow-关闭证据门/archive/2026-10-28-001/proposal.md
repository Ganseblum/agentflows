# 关闭证据门 — 需求提案

## 文档信息

- 批次：`feature-2026-10-28-关闭证据门`
- 来源：2026-10-28 用户指令（把 Youc 暴露的「修完不归档 / 关单无证据」问题回灌到 agentflow）。
- 主实施仓：本仓（agentflows）。

## 一、背景与目标

### 1.1 背景

下游项目 Youc 在 2026-10-28 暴露了一类可复发的形态：三条 Issue 的代码修复早已并入 `main`，看板也写着「已修复」，但各自声明的关闭条件（sim 浏览器走查、两账号同日签到）从未取过运行证据；同屏还有孤儿 Issue 与重复登记长期存在。回灌到本仓后逐层核对，得到三个**与第一直觉不同**的事实：

1. **schema 早已强制**：`schemas/bug-record.schema.json` 自 0.13.0（提交 `861b6ef`）起就有 `allOf` 条件——verified 必须齐备 `reviewer`、`review_decision=approved`、`regression_status=pass`、`closure_criteria`；rejected 必须带 `rejection_reason`。用 `SchemaValidator` 直接探测可复现四种负例。
2. **文档与门相反**：`docs/issues/README.md` 至今写着「当前 schema 尚不按状态强制该字段」。读者（包括本次实施的第一次判断）会据此以为门不存在，从而跳过字段或依赖人工核对。这是**文档滞后于门**，不是门缺失。
3. **真正的门缺口是流转记录**：`docs/issues/README.md` 要求每次状态流转追加 `## 变更记录`，`tools/lab/gate/records.py` 却只检查 `## 修复`（非 open）与 `## 审查`（verified）。49 条非 open 记录实测 100% 已有该节，机器却从不检查它。
4. **回归覆盖不全**：`tests/test_gate_schema.py` 只钉了「verified 缺 `closure_criteria`」一个负例；`reviewer`、`review_decision`、`regression_status` 的缺失与取值矛盾、rejected 缺理由都没有回归。门随时可能被改松而无人发现。

结论：缺的不是新规则，而是**三处载体没有对齐**——README 散文、记录门、回归测试。本批把三者收口到同一份契约。

### 1.2 目标

- **G1**：契约文档与门一致——`docs/issues/README.md` 与 issue 模板不再声称「schema 不强制」，并写出状态条件矩阵（verified 四项 + approved/pass、rejected 拒绝原因、非 open 变更记录）。
- **G2**：离开 `open` 的记录必须留下状态流转记录——正文必须包含 `## 变更记录`，否则 FAIL。
- **G3**：现有 schema 条件与新增标题检查都有负例钉住——verified 四项缺失、取值矛盾、rejected 缺理由、临时记录的 `## 变更记录` 缺失分别报错；正例保持 PASS；三道门（`doc_chain.py`、`unittest`、`validate.py all`）全绿。

### 1.3 本期范围

- 包含：
  - `tools/lab/gate/records.py`：非 open 记录要求 `## 变更记录`。
  - `tests/test_gate_schema.py`：schema 条件的四组负例与一组正例；记录门的 `## 变更记录` 负例。
  - `docs/issues/README.md`、`skills/agentflow/templates/issue/issue-template.md`：删除「schema 不强制」旧表述，补状态条件矩阵与流转记录要求。
  - 本 feature 的完整文档链与门禁原始输出。
- **不包含**：
  - **不改 `schemas/bug-record.schema.json`**：核实后确认条件已在，重复实现只会制造第二份真源。
  - 不强制 `fix_revision`：存量 44 条 `verified` 中 10 条没有该字段（多为 2026-09-20/21 的文档与流程修正，无单一提交号），强制会让合法历史记录变红。见 §五 Q-01。
  - 不把 `verified` 记录移入归档：本仓归档语义只覆盖 `rejected`（`docs/issues/README.md` 的归档规则），已由 `validate_bug_layout` 强制。
  - 不改写任何历史记录；不提交、不推送、不重装宿主。

## 二、产品定位与核心原则

- **定位**：把「关闭」从自报状态变成一类必须携带证据的可编译产物，与文档链的 C23（证据在场）同构；同时把「文档说没有门」当作与门缺失同级的缺陷处理。
- 原则：
  1. 先核实再落笔：文档、门、测试三面逐一对照，确认是缺规则还是缺载体。
  2. 只在状态跃迁的边界加约束，不重写记录正文结构。
  3. 存量不回改：先扫描数据证明新条件不会误伤历史记录。
  4. 门要有负例：没有反例的门视为未接。

## 三、用户与场景

| 用户 | 场景 | 承诺 |
| --- | --- | --- |
| bug-recorder / reviewer | 把记录从 `fixed-pending-review` 推到 `verified` | 缺审查结论、回归结论或关闭条件时，`validate.py artifacts` 直接点名字段 |
| 集成会话 / 记录审阅者 | 审阅一批记录是否真的关闭 | 不再需要逐条读正文猜证据；流转记录缺失会被门点名 |
| 后续候选 | 改记录状态或改门 | 改松 schema 条件会让负例立刻变红；文档不再误导「门不存在」 |

界面与视觉范围：`N/A: 纯记录契约与门工具，无用户界面`。

## 四、范围决策表

| 决策 | 做/不做 | 出处 |
| --- | --- | --- |
| 补 `## 变更记录` 机器检查 | 做 | 49 条非 open 记录实测 100% 已有该节，零迁移 |
| 补齐 schema 条件的负例回归 | 做 | 现有测试只覆盖 closure_criteria 一个字段 |
| 修 README 的「schema 不强制」旧表述 | 做 | 与 0.13.0 起的实际行为相反 |
| 重复实现 schema 条件 | 不做 | 条件已在；重复实现会制造第二份真源 |
| 强制 `fix_revision` | 不做 | 10 条 verified 记录为文档/流程修正，无单一提交号；见 Q-01 |
| verified 移入归档 | 不做 | 本仓归档只覆盖 rejected；见 `docs/issues/README.md` 归档规则 |
| 同步 Youc 的自有看板门 | 不做 | Youc 已用 `check-issue-docs.mjs` 落地自己的版本语义 |

## 五、待冻结问题台账

| # | 问题 | 阻塞性 | 关闭条件 | owner |
| --- | --- | --- | --- | --- |
| Q-01 | `fix_revision` 是否也应强制 | 非阻塞 | 若未来要求，先为 10 条存量 verified 补齐可复核载体，再改 schema | 后续批次 |
| Q-02 | 是否需要自动校验「文档表述与门一致」 | 非阻塞 | 先观察本批修正后是否再漂移；重复出现时再设计检查 | 后续批次 |

## 六、成功指标与可观测性

### 6.1 指标与口径

| 指标 | 口径 | 判据 |
| --- | --- | --- |
| 负例必红 | schema 四项缺失/取值矛盾/rejected 缺理由/非 open 缺流转记录分别触发对应错误 | `python3 -m unittest tests.test_gate_schema` 全绿 |
| 存量零误伤 | `validate.py artifacts` 对现有 66 条记录 PASS | 原始输出入 `testing/agentflow-关闭证据门/evidence/run-2026-10-28-001.md` |
| 文档不再误导 | 旧表述「schema 尚不按状态强制」零命中 | `grep` 结果入同上文件 |
| 文档链自洽 | 本批次 `doc_chain.py` 全绿 | 同上 |

本批为门工具与文档变更，`measurement: none`（不涉及用户可见行为，不声称疗效）。

### 6.2 埋点决策

`N/A: 纯记录契约与门工具，无客户端埋点`。
