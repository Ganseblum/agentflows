# Agentflow 审计整改台账（2026-09-18）

依据：2026-09-18 全库只读审计（四路并行子代理审计 + 人工实测复核）。逐字对话记录见仓库根
[`对话记录-2026-09-18-agentflow整体审计.md`](../对话记录-2026-09-18-agentflow整体审计.md)，
其中四项硬缺陷均为实测复现（非推断）。本台账回答三个问题：做了哪些、还剩哪些没做、从哪开始做以及为什么。

审计之后，仓库已落盘一轮 **0.7.5「Audit-driven hardening」**（未提交工作树，本台账创建时与 0.7.2~0.7.4
批一并提交）。0.7.5 的每项声明都经过本会话逐条代码核实（非仅采信 CHANGELOG 摘要），
`validate.py all` 8×PASS、124 个单测全绿（含新增 6 个 record_store 测试）。

---

## 一、已完成（含核实证据）

### 1. 审计与记录（本会话产出）
- 全库四路审计：角色系统与编排契约、测量/以模治模工具、记录/检索/记忆层、文档一致性与仓库卫生。
- 四项硬缺陷实测复现：全量 `@unittest.skip` 通过测试门；非 ASCII 文件名绕过 protected-paths 门；
  `policy.py` 在 `reject` 时退出 0；`records/` 缺失/掏空时 `artifacts` 仍 PASS。
- 审计全程逐字归档为对话记录文件。

### 2. 0.7.5 整改批（逐条核实 ✅ = 本会话在代码中确认）

| 审计项 | 状态 | 核实证据 |
| --- | --- | --- |
| A1 门进 CI + 保护 `.github/` | ✅ | `.github/workflows/validate.yml` 第一步从默认分支克隆可信副本跑 `isolation.py check-diff`；`protected-paths.txt:42` 已含 `.github/` |
| A2 非 ASCII/引号路径绕过 | ✅ | `tools/lab/isolation.py:132-134` 三处 git 调用均改 `-z` NUL 分隔 |
| A3 候选自带检查器/清单 | ✅ | `isolation.py:150`：checker_root 等于或嵌套于 candidate 时拒绝执行 |
| A4 测试门 skip/伪造计数 | ✅ | `validate.py:2515-2517`：解析 `skipped=N` 且 `>0` 即拒绝 |
| A5 空 records/ 报 PASS | ✅ | `validate.py:1944`：records 目录为空/缺失即报错 |
| A6 `policy.py` reject 退出 0 | ✅ | `policy.py:271`：reject 返回 1 |
| A7 REQUIRED_PROTECTED_PATHS 扩面 | ✅ | `tests/test_record_store.py` 已入保护清单（`protected-paths.txt:50`） |
| B2 评分可刷分 | ✅ | `seed_grader.py`：路径穿越拒绝、off_target 不计召回、finding 总量与单字段长度上限、去重、每文档 unmatched 上限 |
| B4 release 契约与 `measurement: none` 矛盾 | ✅ | `release-record.schema.json` 新增结构化 `measurement`；`promote` 要求 `evaluation_result: better` + 审批（allOf 约束已核实） |
| C1~C5 编排契约缺口 | ✅ | `contracts.md` brief/result 增加 `task_id`/`baseline_revision` 与 `status: partial`；路由表不再豁免 Supervisor 自己改动的评审门；improve 角色绑定补齐；plan 状态列执行期唯一写者为 Supervisor |
| E7 AF-009 死契约 | ✅ | `evals/public/inputs/AF-009.md` 已改为 `records/bugs/2026-09-14/parser-bug.md` |
| E9 文档内部矛盾（路由/属主） | ✅ | `roles.md:12/19` 已改为「Supervisor alone 但评审门不可豁免」 |
| F1/F2/F4（部分）检索读侧 | ✅（首版） | 新增 `tools/lab/record_store.py`（SQLite FTS5，一次性可重建）；SKILL Intake 已写明 briefing 前先检索 |
| 0.7.2~0.7.4 批 | ✅ | episode `review_roundtrips`、视觉标注约定、用词纪律扩展、文档同步——本批一并提交 |
| 版本对齐（本会话补） | ✅ | CHANGELOG 已有 0.7.5 而五份 manifest 停在 0.7.4——已全部 bump 至 0.7.5，README 两处与两份文档横幅同步 |
| 零星修正（本会话补） | ✅ | `SKILL.md:99` 断链 `../../../` → `../../`（源码树实测可解析）；`.gitignore` 补 `record_store` 默认库 `.agentflow-records.sqlite3` |

核实基线：`python3 tools/lab/validate.py all` → 8×PASS；`python3 -m unittest discover -s tests` → `Ran 124 tests ... OK`。

---

## 二、未完成清单（按优先级域分组）

标注 🔒 的项触及 protected-paths 所列路径，属 gate change，需显式人工评审后动手。

### B 域：度量效度（以模治模结论可信度的最后两个 S0 缺口）
1. **B1 🔒 答案仍在被测者工作目录。** `evals/business/seeds/*.seeds.json` 仍被 git 跟踪（已复核），
   候选 worktree checkout 整树后 seeds 就在候选 cwd 内；`protected-paths.txt` 防改不防读。
   修法：评测时由 runner 侧注入 seeds（或把 worktree 的 `--plugin-dir`/`cwd` 分离）。
2. **B3 🔒 决策指标仍全部自报。** `permission_violations` 仍是问违规者本人；
   `host_adapter.py:575` 注释自认观测到 `permission_denials` 但未读取。修法：从宿主 denial 输出解析，
   至少让一个 guardrail 变成观测值。
3. **B5 rollback 路径缺失。** `policy.py` 只会返回 promote/revise/reject；`rollback_target`
   （`policy.py:233`）仅回显 `parent_version`，未验证可安装。
4. **B8 🔒 低危 bug 残余。** 0.7.5 已修 adapter/eval_runner 一批；`validate.py` 的
   `load_bug_markdown` 只捕 OSError（非 UTF-8 记录裸 traceback）、`BODY_PATH_PATTERN` 无
   containment 等仍开放（清单见审计报告②§6 / 对话记录第 4 节）。

### C/D 域：编排与角色（结构缺口，需设计决策）
5. **D1 🔒（原则）角色收敛未动。** `bug-investigator`/`feedback-analyst`/`technical-director`
   仍是 reviewer 的 brief 变体；`roles.md:53` 的收敛原则未应用到自身。收敛会改 `agents/*.md`
   的公开角色面，属产品决策。
6. **D2 evaluator/release-governor 隔离仍是 prompt 级。** 与 hard boundary 7「不得仅凭 prompt
   文本宣称隔离」的张力未消：要么真实化（不同模型/上下文/工作区），要么文档如实声明。
7. **C 域残余：** 失败语义（crash/timeout/空返回）仍未成文；plan 看板回写有了唯一责任方，
   但回写时机仍未进入 SKILL 步骤清单。

### E 域：文档与打包失真
8. **E5 打包 allowlist 有口号无机制。** `docs/next-session-handoff.md:5` 新横幅声称根目录
   会话 HTML/历史报告「按 allowlist 打包时排除」，但全仓库不存在任何打包 allowlist 实现
   （grep 仅有散文提及）；本地目录型 marketplace 仍整目录快照，1.6MB HTML 仍会进安装快照。
   这条是 0.7.5 引入的**新失真**：横幅描述了一个不存在的机制。
9. **E3 handoff/iteration-log 残留失真。** handoff 加了免责横幅但 `:9`、`:485` 的错误机器
   路径与错误 remote 字符串原样保留；`iteration-log.md` 仍有 12 处「当前源码」标记（全假）。
10. **E2 版本号仍在散文里。** README/横幅本轮又手工同步了一遍（0.6.0→0.7.4→0.7.5），
    去散文化（版本只引用 manifest）未做；下一次 bump 还会再犯。
11. **E8 mock/ 零校验。** `grep -c mock tools/lab/validate.py` = 0；`mock/README.md` 声明
    与 git 状态的矛盾仍在。

### F/G 域：记忆层与流程闭环
12. **F3 class_id 归类与回写仍全手工。** 无自动发现；`consolidated_in` 无回写责任方；
    `escalated` 警报在人工标类前不可能触发。
13. **G2 🔒 `review_roundtrips` 仍未 required。** episode schema 已加 `revision/run/claims/evidence`
    （已核实），但 required 列表仍无 `review_roundtrips`——SKILL 声明的强制与 schema 不对齐。
14. **G3 生存者偏差未纠正。** 9/9 episode `outcome: accepted`；负向 episode 仍零收录。
15. **G4 首次真实业务评测未跑。** `records/improvement/` 仍只有 README；instrument-ready
    但从未运行，`measurement: none` 因此恒成立；first release record 仍不存在。

---

## 三、从哪开始做、为什么

**第一批：B1 + B3（度量效度收尾，均 🔒，一个 gate 评审批）。**

为什么从这里开始，而不是继续修文档或跑评测：

1. **0.7.5 修完之后，门已不是最薄弱环节**——CI 门、fail-closed、防绕过都已核实落地。
   此时整条「以模治模」证据链上仅剩的两个 S0 级问题恰好就是 B1 和 B3：前者让被测者能读到
   答案，后者让 guardrail 由被测者自报。不先关掉这两个，后续任何评测数据、任何 promote
   结论都建立在可疑证据上。
2. **它们是 G4 的前置。** 台账第二、三、四批里最诱人的下一步是「跑第一次真实业务评测」，
   但在 B1/B3 关闭前跑，产出的基线数据会被这两个缺陷永久污染（评测 once，数据就是起点）。
   先修度量，再跑评测，顺序不可反。
3. **改动小而确定。** B1 是评测编排改动：seeds 移到 runner 侧（`--business-root`/holdout
   隔离位已有现成机制可复用）；B3 是解析宿主 denial 输出（观测点在 `host_adapter.py:575`
   已被注释定位）。两者都能在 `tests/test_lab_contracts.py` 加「修复前红、修复后绿」的回归用例。

**后续批次（建议顺序）：**

- 第二批：E5 + E3 + E10 + E11（普通改动，无需 gate 评审）——把「打包 allowlist」做成机制
  或删掉横幅里的虚假声明；清掉 handoff 错误字符串与 iteration-log 假标记；版本去散文化。
  理由：全是低成本、立刻止住「活跃误导」的改动，且不依赖任何设计决策。
- 第三批：G4 第一次真实业务评测（产出第一份 release 记录，实测检验 B4 修好的 measurement
  契约与 record_store 读侧）。理由：0.7.5 + 第一批完成后，这是闭环里第一个「新信息」来源。
- 第四批：F3 + G2 + G3（记忆层自动归类、roundtrips required 化、负向 episode 开始收录）。
  理由：评测跑起来、episode 开始稳定产出之后，归类与负样本才有数据可处理。
- 第五批：D1 + D2 + B5 + B8（需要产品/架构决策的长线项）。

**每批完成判据：** 对应发现先在 `tests/` 中加出「修复前红、修复后绿」的回归用例（若可机器化）；
`python3 tools/lab/validate.py all` 全绿；gate 批次另需 `validate.py protected` 覆盖新清单，
并在 CHANGELOG 记一条带 `measurement:` 状态的条目。完成一项就把该项从「未完成」移入
「已完成」并注明日期与证据（提交号或测试名），保持追加式历史，不原地打勾。

---

*创建：2026-09-18，依据当日审计与 0.7.5 整改批核实结果。维护规则：追加式，不打勾。*
