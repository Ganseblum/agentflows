# 提案：表达面与角色治理批

## 0. 文档信息

- 来源：2026-10-28 会话。2026-10-28 全面评测报告（`docs/evaluations/AGENTFLOW-EVAL-2026-10-28.md`）
  列出七条发现，其中 B4（表达面膨胀）与 B5（角色深度倒挂）经复核**仅部分修复或完全未修**，
  用户据此指示「可以，先成立独立批次吧」。
- 前序批次：`docs/features/feature-2026-10-28-评测整改批/`（0.20.0）修掉了 B4 的表层三项
  （`execution-coordinator` 重复声明两处合一、链契约加降档速查、FE/BE 补裁决规则），
  但未触及病因。本批处理病因。

## 1. 背景（实测现状，非印象）

### 1.1 B4 的实测数据

| 载体 | 行数 | 说明 |
| --- | --- | --- |
| `skills/agentflow/SKILL.md` | 135 | 入口；第 131 行含「集成/推送授权」完整条款 |
| `skills/agentflow/references/contracts.md` | 195 | 硬边界第 3 条含同一纪律的**更长**版本 |
| `skills/agentflow/templates/host/global-rules.md` | 91 | 托管块模板；第 2 条含同一纪律的**第三份** |
| `skills/agentflow/references/document-chain.md` | 494 | references 第二名为 382，其余多数 < 100 |
| `skills/improve/SKILL.md` | 72 | 「装置裁撤」在 6 处出现（:30、:35、:37、:38、:42、:60） |

「集成他人改动需要当次授权」这条纪律，当前有**三份实质副本**：

- `contracts.md:13`（299 字符，最完整，含「是用户的决定…不是完成一次被拒推送的步骤」）
- `SKILL.md:131`（235 字符，含「不得从先前的指令推断」）
- `global-rules.md`（144 字符，含「解冲突不等于授权合并；合并不等于授权推送」）

`SKILL.md:102` 结尾仍写着同步义务：「这组规则与 `templates/host/global-rules.md` 的宿主级副本
必须同步：**改一处就改另一处**」。

`document-chain.md` 从 481 行涨到 494 行（前批加速查表所致）——**诊断在增长，不是收敛**。

### 1.2 B5 的实测数据

角色文件行数（`wc -l agents/*.md`，本批立项时实测）：

```
evaluator 20    bug-investigator 22   technical-director 22   feedback-analyst 24
release-governor 24   bug-fixer 28    backend-engineer 32     bug-recorder 35
frontend-engineer 40  candidate-engineer 44   plan-architect 74
test-executor 84      test-planner 86        reviewer 175
```

倒挂事实：`reviewer`（评审者）175 行，而 `backend-engineer`（产出主体）32 行、
`technical-director`（高风险决策者）22 行。四个治理角色 20–24 行。

FE/BE 合并悬案：`roles.md:83` 已在前批补上裁决规则（不一致率 <10%、产物所有权分歧为 0、
合并后 ≤60 行），但**规则未被执行**——28 例边界测试语料在盘
（`docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/`，
含 `plan-2026-10-13-001.md` 与三份 `run-*.md`，`run-2026-10-19-004.md` 记录 v2 全量 28/28），
但从未有人拿它算过「FE/BE 同场景判定不一致率」。

## 1.2 目标

| 编号 | 目标 | 成功标志 |
| --- | --- | --- |
| G1 | 规则单一权威 | 每条跨载体规则有一个「权威载体 + 其余为指针」的归属表；权威载体之外不再有实质副本 |
| G2 | 同步义务退场 | `SKILL.md:102` 的「改一处就改另一处」删除或收窄到确实无法单源的最小集 |
| G3 | 大文档可导航 | `document-chain.md` 拆成「链契约（谁产出什么）」+「判据细则（改门者查阅）」两份，且 C 检查扫描范围同步 |
| G4 | FE/BE 悬案裁决 | 用 28 例语料实测不一致率，给出「合并」或「保持分立」的**结论**，悬案关闭 |
| G5 | 实现角色深度对齐 | `backend-engineer` / `frontend-engineer` / `technical-director` 的篇幅与其职责相称，或书面说明为何不 |

## 1.3 关键约束（决定了本批不能一刀切）

**`templates/host/global-rules.md` 必须自带全文，不能收成指针。** 它被写进宿主的
`~/.zcode/AGENTS.md` 托管块，在**任意目标仓**生效；目标仓里既没有插件仓、也没有
`skills/agentflow/references/`。若把它改成「详见 contracts.md」，写进全局文件后就是断链，
规则当场失效。这条约束由 `references/hosts.md:15` 的设计意图反向推出（「分支纪律与证据纪律
必须在**任何仓、任何会话**默认在场」），是本批最重要的设计边界。

同理，`SKILL.md` 面向「刚调用 skill、还没读 references」的读者，它必须能独立站住到
「知道去哪读」为止；`contracts.md` 才是硬边界权威。

因此本批的形态是：**给每条规则指定一个权威载体，其余载体保留「自足所需的最短表述 + 指针」**，
而不是删除重复。

## 1.4 范围与非目标

**做**：载体归属表（G1）、同步义务退场（G2）、`document-chain.md` 拆分（G3）、
FE/BE 实测裁决（G4）、实现角色深度对齐（G5）。

**不做**（显式声明，理由随行）：

| 不做的事 | 理由 |
| --- | --- |
| 删除 `global-rules.md` 的任何条款全文 | 它会被写入目标仓之外的宿主全局文件，删了就断链（见 §1.3） |
| 合并 `reviewer` 与其他只读角色 | `roles.md:79` 已声明「有意不收敛」，且四组独立性会因合并消失；属产品决策 |
| 扩大 `document-chain.md` 拆分到全部 references | 其余 references 均 < 100 行，无拆分必要 |
| 改 `contracts.md` 的硬边界**内容** | `contracts.md` 在 `protected-paths.txt` 内，属受保护面；本批只允许「删重复段」类改动，且需逐项授权 |
| 给治理角色加深度（G5 只覆盖实现角色） | 治理角色的薄与「从未运转」互为因果，加深度不会让它运转；那属于 `PENDING-DECISIONS` 第 10 条的存废拍板 |

## 2. 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 「收成指针」被误做成「删掉重复」 | 目标仓/宿主全局面断链，规则静默失效 | spec 的载体归属表逐条标注「必须自足」与「可指针」；G1-AC-02 用一条脚本断言每条规则的权威载体存在且指针可解析 |
| 拆分 `document-chain.md` 打断 C 检查 | `doc_chain.py` 与 `doc_chain_live` 的扫描面变化，可能假绿或误报 | G3-AC-02 要求 `--self-test` 仍全过且 `doc_chain_live` 无新增 finding |
| 动受保护面（`contracts.md`） | 属门变更 | 逐条列出拟删段落，实施前单独授权 |
| FE/BE 实测结论与预期相反 | 若一致率很高，理论该合并，但合并会动角色面 | 结论照实写；合并动作本身另立拍板（角色面属公开契约） |
