# 提案：评审欠账清偿批

## 0. 文档信息

- 来源：2026-10-28 会话。用户读完 2026-10-28 全面评测报告
  （`docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md`）后要求「看看怎么修复，单独立项看看」。
- **本批三个目标各有独立出处，不是同一份文档的三个分支**：
  - G1（两批 L0 欠账）出自评测报告 §二 B2（`docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md:98-104`，
    「改进环空转，且评审能力无分级」一节记录了本轮 5 次派发全部失败）。
  - G2（伪降级无校验）出自 `skills/agentflow/references/contracts.md:42-43` 的成文要求
    「`review_tier: L0` 而 `dispatch_errors` 为空，是伪降级，同样无效」——这是一条已立但无实现的判据，
    与评测报告 §二 B2 的「无分级」判断同源、不同层。
  - G3（五条待评审缺陷）**不出自评测报告**。报告全文检索 `fixed-pending-review` 为零命中。
    该目标出自 2026-10-28 实测：`docs/issues/` 66 条记录中 5 条停在 `fixed-pending-review`，
    其中 4 条缺 `fix_revision`。它是本批立项时新发现的事实，不是报告结论的延伸。
- 前序批次：`docs/features/feature-2026-10-28-评测整改批/`（0.20.0，已并入 `main` 的 `26988a4`）
  写入了 L0/L1/L2 分级与三条不变式；`docs/features/feature-2026-10-28-表达面与角色治理/`（范围冻结）
  与本批无重叠——它处理表达面与角色深度，不处理评审欠账。

## 1. 背景（实测现状，非印象）

### 1.1 欠账的三类来源，逐类带实测数字

**第一类：两个批次的 L0 自审未补。** 两批都在**散文**里声明了 L0 档并承诺补复核。按
`contracts.md:42-43` 的载体规则，`review_tier` 应当写进「决策记录或 episode」，两批**都没有**
这么写——它们写在批次 README 与计划正文里：

| 批次 | 声明位置 | 承诺表述 |
| --- | --- | --- |
| 评测整改批 | `docs/features/feature-2026-10-28-评测整改批/README.md:13-16` | 「显式登记 `review_tier: L0`，恢复委派能力后须补一次独立复核」 |
| 表达面与角色治理批 | `docs/features/feature-2026-10-28-表达面与角色治理/README.md:15-16` | 「记 **L0**（主审自审 + 全套确定性门）…能力恢复后须补独立复核」 |

补充说明两处容易搞错的事实（前一版本草案在这两处写错过，此处按实测更正）：

1. 字面 `review_tier: L0` 只出现在评测整改批 README；表达面批只写「记 L0」。两批均未把它写进
   决策记录或 episode。
2. **并非「没有任何文件记录这两笔欠账」**。`docs/releases/todo.md` 第 8 条已写「评审档位 L0，
   恢复委派能力后须补独立复核」，`plan/PLAN-EVAL-001.md` 与 `plan/PLAN-GOV-001.md` 也各有记录。
   真实缺陷是：这些记录**都是散文**，没有任何机器可读的欠账清单——要回答「还欠几次、欠哪个
   revision」只能人工通读。两批 `reviews/` 目录当前均为 0 个文件。

**第二类：分级协议本身零机器校验。** `contracts.md` 第 26–47 行定义了三档与三条不变式，其中
第 1 条明确伪降级的判定。实测：

```
$ grep -rn "review_tier" tools/ schemas/ tests/ skills/agentflow/scripts/
（零命中）
```

`review_tier` 只出现在散文（契约、SKILL 第 8 步）与批次文档里，没有任何 schema 字段或门判据。
这与本仓已两次记录的反模式同形——ISS-2026-061 的标题就是「新判据『契约里声明、实现里不校验』六处」。

**第三类：五条缺陷停在 `fixed-pending-review`，其中四条缺 `fix_revision`。**

```
$ ls docs/issues/ISS-*.md | wc -l                    → 66
$ grep -h "^status:" docs/issues/ISS-*.md | sort | uniq -c
     44 status: verified
     17 status: open
      5 status: fixed-pending-review
```

五条待评审记录为 ISS-2026-057 / 058 / 060 / 061 / 066。逐条查 `fix_revision`：只有 ISS-2026-066 有
（值为「0.20.0（分支 feature-2026-10-28-评测整改批，未发布）」——该分支已并入 `main`，这句已过期），
其余四条**完全没有该字段**。按 `skills/agentflow/templates/issue/issue-template.md:35`，
「修复已落地需 `fix_revision`」，四条记录处在「声称修好了、却指不出修在哪个版本」的状态。
而状态机规定 `verified` 需要 `reviewer` + `review_decision: approved`——这五条缺的正是**独立评审**
这一环，与本批前两类同源。

### 1.2 目标

| 编号 | 目标 | 成功标志 |
| --- | --- | --- |
| G1 | 两个批次的 L0 欠账被清偿 | 两批各有独立评审记录落在 `reviews/`，结论含 `review_tier: L1` 与被评审 revision；`changes_requested` 的 findings 全部转成 ISS 或已关闭 |
| G2 | 评审欠账可机器清点 | 「当前欠几次独立评审」由一条命令给出，不靠读散文；`review_tier: L0` 且 `dispatch_errors` 为空被判红（伪降级） |
| G3 | 五条待评审缺陷逐条清偿 | 五条各自要么转为 `verified`（带 `reviewer` 与 `review_decision`），要么退回 `open` 并写明缺什么；四条补上 `fix_revision` 或显式写 `N/A: 理由` |

### 1.3 关键约束（决定了本批不能一刀切）

**约束一：清偿欠账需要委派能力，这不是代码能替的。** 本批 G1 与 G3 的实质动作是「派独立评审」，
`reviewer` 角色不可用时本批无法完成。2026-10-28 实测派发已恢复（向 `reviewer` 派发一次探测任务
成功返回）；但**一次成功只证明「至少 1 个只读角色可用」，不足以判定 L1 还是 L2**——按
`contracts.md:34-38`，L2 要求「至少能派出 2 个只读角色」，L1 是「只能派出 1 个」。
因此档位必须由 T01 的两组探测决定（1 个成功 + 2 个中的第 2 个失败 ⇒ L1；2 个都成功 ⇒ L2），
不得按成本偏好选档。若实施时能力再次不可用，T02/T03/T05/T06/T07 必须置 `⚠ 阻塞` 并如实登记，
**不得用主审自审冒充清偿**——那正是本批要清掉的欠账形态。

**约束二：G2 的判据要覆盖真实载体，不只是根 `reviews/`。** 伪降级的观察对象有两处：
根 `reviews/` 下的评审记录（受 `schemas/review.schema.json` 校验），以及批次 README/计划的 L0 声明
（不受任何记录契约校验）。只做前者会出现「判据在 A、真身在 B」——与本批要清的 ISS-2026-061 同形。
因此 G2 的判据必须同时覆盖：评审记录的 `review_tier`/`dispatch_errors` 一致性，以及
「批次文档声明 L0 而 `reviews/` 无对应记录」这一欠账形态。后者由 M-A 的欠账清单承接。

**约束三：改 `schemas/` 必须同批重建生成树。** `packaging/runtime/schemas/` 是 `build_runtime.py`
的产物，`validate.py manifests` 的 `validate_runtime_freshness` 逐字节比对源与快照（2026-10-28 实测：
改动源 schema 而不重建，`manifests` 报 `packaging/runtime/schemas/review.schema.json: content differs
from source`）。所以 G2 的实现动作是「改源 schema + 改校验器 + 重建生成树」三件一体，不是两件。

**约束四：`agents/reviewer.md` 不在受保护面内。** `protected-paths.txt:42-43` 只列
`agents/evaluator.md` 与 `agents/release-governor.md`；清单第 15-16 行明写「Role prompts that only
describe how work is done are NOT protected」。本批不改 `reviewer.md` 的理由不是「它受保护」，
而是「本批只要求按现有方法被真正执行一次，评审方法的改进不在本批目标内」。

**约束五：`schemas/` 与 `tools/lab/` 在受保护面内。** `protected-paths.txt` 明确列出 `schemas/`、
`tools/lab/validate.py`、`tools/lab/gate/`，以及 `tests/` 下的逐个文件。G2 的实现必然触碰这些路径，
属**门变更**，需要逐项授权；本批的计划把该动作单列为一条任务并标「需授权」，不在本期自动开工。

### 1.4 范围与非目标

**做**：欠账清单的字段级口径（`spec/be/backend.md` §1）、清偿判据（§1.2 的 G1-AC-01/02 等）、
`review_tier` 伪降级的记录侧校验方案（design）、五条缺陷的逐条清偿路径（plan T05–T07）。

**不做**（显式声明，理由随行）：

| 不做的事 | 理由 |
| --- | --- |
| 改 `contracts.md` 的分级条款正文 | 条款本身经 0.20.0 刚立，问题在「没有校验」不在「条款写错」；改正文属受保护面且无收益 |
| 新增评审能力档位（如 L3） | 三档已覆盖「2 个角色 / 1 个角色 / 0 个角色」的全部情形，加档不增加区分度 |
| 追溯并补做 2026-10-28 之前所有 L0 批次 | 更早批次多数已随发布闭环；无差别回补会产出大量无 review 对象的空记录，且其中多个批次的被评审 revision 已不可达 |
| 把 17 条 `open` 缺陷一并清偿 | 其中 16 条 `project: infinite-canvas`、`provenance: external`、`disposition: deferred`，属外部计划缺陷，不在本仓清偿范围；唯一的本仓条目 ISS-2026-059 已登记 `deferred`，另需授权 |
| 改 `agents/reviewer.md` 的评审方法 | 本批只要求「按现有方法被真正执行一次」，评审方法改进不在本批目标内；该文件本身**不在** `protected-paths.txt` 内（清单只保护 `agents/evaluator.md` 与 `agents/release-governor.md`） |

## 2. 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 委派能力在实施时再次不可用 | G1/G3 无法清偿，本批卡在立项状态 | 计划把「探测委派能力」列为 T01 的完成判据；不可用即置 ⚠ 并如实登记，不降级冒充 |
| 独立评审推翻已并入 `main` 的 0.20.0 | 已发布内容需回退 | 按 `contracts.md` 不变式 3 处理：`changes_requested` 的改动回到待修状态，本批负责转成 ISS 而不是就地修改 |
| 触碰受保护面（`schemas/`、`tools/lab/`） | 属门变更，需逐项授权 | 计划把该动作单列为 T04 并标「需授权」；未获授权时 T04 置 ⚠，G2 结论降为 `partial` |
| 五条缺陷中部分「修复」经复核不成立 | 状态机需要回退 | 显式允许退回 `open` 并写明缺什么，不为了清账而把不合格的修复推成 `verified` |

## 3. 与既有拍板的关系

`docs/PENDING-DECISIONS.md` 第 10–16 条均为待用户拍板事项，本批**不处理**其中任何一条，也不以本批
结论替代拍板。特别地，第 12 条（凭据形状扫描）与第 13 条（C17 变异覆盖）虽然同属「判据在不在」
这一主题，但它们各自的选项已登记在册，需用户单独选定；本批不把它们并入 G2，避免把「等拍板」
混进「可执行」。

## 4. 待冻结问题台账

本批有两项需要用户授权的决定，已按 `AGENTS.md`「等用户拍板的事项统一登记到
`docs/PENDING-DECISIONS.md`」的规则登记为第 17、18 条（2026-10-28 登记）：

| 编号 | 问题 | 阻塞性 | 关闭条件 | 归属 |
| --- | --- | --- | --- | --- |
| Q-01 | 是否授权改 `schemas/review.schema.json` 与 `tools/lab/gate/`，为 `review_tier` 加记录侧校验 | 阻塞 T04（G2 的实现动作） | 用户在 A（授权）/ B（不授权，G2 只保留清单可清点）中选定并记日期 | `docs/PENDING-DECISIONS.md` 第 17 条 |
| Q-02 | 五条 ISS 中若有复核不成立者，是否允许退回 `open` | 非阻塞（已按 spec M-C-01 定为允许） | 已在 spec M-C-01 写定为「允许退回 open 并写复核结论」 | 本批次 spec，无需拍板 |

不再使用「实施前需用户确认」这第三处并行台账——它与唯二落点（本表 / `PENDING-DECISIONS.md`）
重复，且容易与 spec 已冻结的行为冲突。

## 5. 成功指标与可观测性

`N/A: 理由` —— 本批只改记录 frontmatter、评审记录与文档索引，不新增用户可见行为、不新增埋点事件，
也没有线上行为可观测。可判定的成果由 `spec/qa/acceptance.md` 的验收点承担（两批 `reviews/` 文件数、
`fixed-pending-review` 记录数、缺 `fix_revision` 记录数、`grep review_tier` 命中数四个可实测数字），
不需要额外指标口径。