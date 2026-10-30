# Agentflow 总体技术设计（design）

> 适用阶段：`design/`。前置依赖：`proposal/proposal.md`、`spec/method-spec.md`（含反审
> checklist，阻塞项已全关）。实施仓：本仓库。
> 契约：`spec/method-spec.md` 是行为承诺的唯一依据；本文回答"技术上如何承接、怎么验证、
> 影响面多大"。文档状态：**待技术方案评审**。
> 图纪律：每张图只回答一个问题。

## 0. 关键决策速览

| # | 决策点 | 结论 | 一句话理由 | 详见 |
| --- | --- | --- | --- | --- |
| D1 | 做产品还是做运行时 | 只做方法，宿主是运行时 | LangGraph/CrewAI/Dify 管循环已被做好；本产品管协作纪律、证据编译、改自己时不能改评分规则 | PLAN-PRODUCT-001 架构结论 |
| D2 | 产品载体 | 宿主插件（Skill + 角色文件 + manifest），不绑死单一宿主 | 方法写一次；用户留在成熟宿主里 | `docs/design-decisions.md` §1–§2 |
| D3 | 自迭代形态 | 受治理的人工闭环，不是自动学习系统 | 执行者发现并生成候选，独立评测验证，人按预声明门槛发布 | `docs/design-decisions.md` §3 |
| D4 | 评判门归属 | 保护门清单单点声明（`protected-paths.txt`），候选不可触碰 | 工具改自己时不能改评分规则；门变更=人工评审 | spec S8 |
| D5 | 记录形态 | 各类记录各有 schema 与落点，落盘即过编译门 | 摘要不算验证；不可复现的检查视同没跑 | spec S6 |
| D6 | 计划形态 | Markdown 融合契约（信封 + 看板任务表 + 机器断言） | 人读性与机器校验合一；plan 是执行契约不是改码授权，且随批次走 | `docs/features/README.md` 计划形态节 |
| D7 | 失败语义 | crash/timeout/empty 三类成文，编排层不做保底 | 降级=结果降级+丢弃在途；产品级 fallback 归异常矩阵 | spec S5 |
| D8 | 打包 | 瘦快照：`build_runtime.py` 生成，marketplace 源指向生成树 | 用户装的不是整仓死重；运行时面与实验室控制面分开 | spec S9 |
| D9 | 版本事实源 | manifest + CHANGELOG 唯一；文档禁复述版本号 | 版本散文化曾三次漂移，守卫检查执行 | spec S9、`validate.py docs` |
| D10 | 评测仪器 | ~~公开套件 + 业务切片~~ **已整线裁撤**（2026-10-12）；设计知识与恢复清单留存 | 仪器化度量暂停，方法级改动 `measurement: none` | 原始决策见 PLAN-LOOP-SMOKE-001 |
| D11 | 度量效度 | **随装置裁撤（2026-10-12）**：原口径为「被测树含 seeds 即 fail-closed；authoritative 运行强制隔离参数」，现存 `artifact_digest.py` 与 `isolation.py check-diff` 仍在，仪器化对照面已不在盘 | 种子泄漏=考试漏题；不可信基线不如不测。恢复仪器化时按 `docs/design-decisions.md` §3 的重建清单执行，与 D10 同批处置 | spec S10 |
| D12 | 文档链吸收 | 方法增加 proposal→spec→design→plan 交付链（对外生成 + 对内自举），**推翻**早期"只吸收评审判据、不建模板体系"的取舍 | 只有评审判据没有生成契约时，文档质量靠当次会话自觉——与方法的其余部分治理哲学不一致；用户 2026-09-20 拍板补链 | spec S11/S13；本文件 §1.4 |
| D13 | 文档链门禁 | spec 反审 proposal（阻塞清单）、design 冻结前独立评审、plan 前置=design 冻结 | 链条带门才不是仪式；复用评审桥落证据 | `references/document-chain.md` |
| D14 | 诚实声明 | 角色分离≠环境隔离等边界如实入文；measurement: none 合法 | 强度声明与证据等级一致是审计前提 | spec S15 |

## 1. 设计方案

### 1.1 技术挑战

| 优先级 | 技术挑战 | 应对 |
| --- | --- | --- |
| P0 | 工具改自己时可能松掉评分规则（candidate 改 schema/评测/守卫） | 保护门 + `check-diff` 对冻结父 revision 比对 + `validate.py protected` 守清单覆盖（D4） |
| P0（仪器化暂停） | 当前无独立评测 runner，不能声称候选效果已测量 | 方法级改动标记 `measurement: none` 并经人工评审；恢复仪器化前，按 D10/D11 的重建清单重新设计隔离对照 |
| P0 | 方法声明与宿主实态漂移：源码编辑≠宿主行为 | 瘦快照 + `installed` 逐文件比对（D8）；宿主事实只入 `host-platform-facts.md` 且带复验方法 |
| P1 | 记录一旦分散即不可检索，证据随会话消失 | 记录体系（schema + 编译门）+ FTS5 读侧 + episode 会话内强制落盘（D5） |
| P1 | 文档链只有评审没有生成契约，质量靠自觉 | D12 补生成契约 + D13 门禁；内部链自举（本目录即样例） |
| P2 | 多宿主行为差异（浏览器主会话专属、工具白名单语义不同） | 宿主差异如实分宿主记录；证书不跨宿主外推（S12/S15） |

### 1.2 技术架构

方法层与仪器层分离：宿主只装载方法层的瘦快照；仪器层留在仓库里做确定性验证与自迭代。

**图 1：模块关系**

```mermaid
flowchart TB
    User(["用户"]) --> Host["编码宿主<br/>(ZCode / Claude Code / Codex)"]
    Host -->|"装载瘦快照"| Skill["agentflow Skill<br/>十步流程 + 触发面"]
    Skill --> Roles["10 角色文件<br/>按需路由"]
    Skill --> Sup["Supervisor = 主会话"]
    Sup -->|"委派 write/read_scope"| Roles
    Roles --> Out["工件 + worker 结果契约"]
    Sup --> Gate1["独立评审门<br/>(reviewer)"]
    Gate1 --> Decide["决定记录 + claims ledger"]
    Decide --> Ep["记录根: docs/issues/ · docs/features/ · docs/releases/ · episodes/ · reviews/"]
    Ep --> Inst["实验室工具层（不入快照）<br/>validate / doc_chain / isolation / record_store / artifact_digest"]
    Inst -->|"方法级证据：measurement: none"| Human["人工独立评审与晋级决定"]
    Inst -."已裁撤（2026-10-29）".-> Loop["改进环与仪器化评测"]
    Loop -->|"候选树 + check-diff"| Gate2["保护门 protected-paths"]
    Inst --> Docs["产品文档链 docs/product/<br/>proposal→spec→design→plan"]
```

| 组件 | 职责 | 不负责 |
| --- | --- | --- |
| Skill（SKILL.md） | 触发、十步骨架、门禁接线 | 具体角色指令（在角色文件） |
| 角色文件（agents/*.md） | 单角色能力、产物归属、工具白名单 | 跨角色编排（在 Skill/Supervisor） |
| Supervisor（主会话） | 收口、委派、集成、决定、失败分类 | 替评审者下结论；豁免自己参与的评审门 |
| `docs/issues/` 等记录根 | 证据落盘与检索 | 承载产品叙事（在 `docs/`） |
| 实验室（tools/lab/） | 编译门、隔离检查、检索与摘要；仪器化评测暂停 | 进入宿主瘦快照 |
| docs/product/ | 产品四层文档链 | 取代原记录树中的产品叙事（执行契约在各批次 `docs/features/<批次>/plan/`） |
| 保护门（protected-paths.txt） | 候选禁区单点声明 | 保护"怎么干活"的角色提示词（改进环已裁撤，角色提示词不在保护面） |

### 1.3 文档链与角色/记录的接线

**图：文档链门禁流（回答：一个阶段什么时候才算走完、谁开的门）**

```mermaid
flowchart LR
    P["proposal<br/>原文逐字保留+台账"] -->|"spec 反审<br/>阻塞checklist"| S["spec<br/>条目→验收口径→标尺"]
    S -->|"阻塞项=产品决策<br/>→ 向需求方提问确认"| RV1["需求评审门<br/>(独立评审)"]
    RV1 -->|"approved"| D["design<br/>决策表+契约+时序图"]
    D -->|"技术方案评审门<br/>(独立评审)"| RV2["冻结"]
    RV2 --> PL["plan<br/>执行契约(分支/落点/回滚)"]
    PL --> IMPL["开工"]
    P -.证据.-> REV["reviews/<br/>(跨仓走评审桥)"]
    S -.证据.-> REV
    D -.证据.-> REV
```

| 链层 | 谁产出 | 谁把关 | 证据落点 |
| --- | --- | --- | --- |
| proposal | Supervisor 与用户收口（原文逐字保留） | spec 反审（blocking checklist） | 目标链目录 |
| spec | Supervisor 或 plan-architect 起；承接口登记缺口 | 需求评审门（独立评审，文档模式） | `reviews/`（跨仓）或目标仓约定 |
| design | 相应角色（跨层时 technical-director 定边界） | 技术方案评审门（独立评审） | 同上 |
| plan | plan-architect（只写不改码） | plan 前置门=design 冻结 | 本仓批次 `docs/features/<批次>/plan/` 或目标仓计划契约 |

### 1.4 本批改动与影响面评估

| 改动 | 落点 | 影响面 | 回滚 |
| --- | --- | --- | --- |
| 产品文档链建立 | `docs/product/`（新增 5 文件） | 纯新增；旧设计文档不迁移不改写，引用不断 | 删目录即回滚，无外部引用 |
| 文档交付链契约 | `skills/agentflow/references/document-chain.md`（新增） | 新 reference；宿主装载面 +1 文件 | 删文件 + 还原 SKILL.md 接线 |
| SKILL 接线 | `skills/agentflow/SKILL.md`（+1 节，触发描述 +1 句） | 方法触发面变化：文档交付类任务开始走链 | 还原该节 |
| 重装 | `packaging/runtime` 重新生成 + marketplace 刷新 + 重装 | 宿主行为在重装后切换 | 不适用（幂等构建） |

**不改动**：`agents/*.md`（角色面零变化）、`schemas/` 与一切保护门路径、`tools/lab/`、
`docs/issues/` 等记录根（不新增计划记录——本批以本链代替，理由见 §1.3 门禁设计）。

### 2. 验证与灰度

1. 确定性面：`python3 tools/lab/validate.py all` 全套全绿（docs 检查覆盖新文件的 schema
   引用与角色引用）。
2. 安装面：`build_runtime.py` 重新生成 → marketplace 刷新 → 重装 → `validate.py installed`
   逐文件 PASS。
3. 自举验证：本链自身走一遍 S13 的验收口径（出处可溯、引用不断）。
4. 独立评审：需求评审门 + 技术方案评审门各一轮，文档模式，记录落 `reviews/`。
   **未过门前本链状态是"成稿待评审"，不得当作已冻结引用。**
5. 注入演练（S5 缺口）：crash/timeout 语义在 `/tmp` 一次性副本上做故障注入，证据落台账
   （不阻塞本设计评审，列为待建标尺）。

### 3. 失败模式与回滚

| 失败模式 | 检测 | 处置 |
| --- | --- | --- |
| 链条跳门（spec 未反审就出 design） | 评审门检查反审 checklist 存在性与关闭状态 | 退回补反审；记录跳门事实 |
| 链条与旧设计文档结论冲突 | 需求/技术评审对照旧文档 | 裁决后按 aiwork 翻案格式留推翻记录，旧文档补注记 |
| 文档链被误当冻结引用 | 门禁语义（README）+ 评审记录缺失 | 评审通过前一律"成稿待评审" |
| 瘦快照与源码漂移 | `validate.py installed` FAIL | 重跑构建 + 刷新 + 重装（幂等） |
