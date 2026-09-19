# Agentflow 0.6.0 综合评审报告（多来源交叉验证版）

> **[2026-09-17 处置进展]** P0 六项已全部落地并通过独立评审两轮（episode EP-20260917-002）。P1 四项已落地：静默漏报族四项 + 测试 64→108、policy/check_diff/门完整性负向测试、四交接物落盘契约（records/improvement/ + comparison schema + 跨文档校验）、8 条记录经批量独立评审全部转 verified（含 BUG-20260915-001 的 0.5.0 退化更正留痕，episode EP-20260917-003）。P2：gitignore/报告横幅已处理，mock/ 入库与提交待用户；拆分 validate.py 与指标 $ref 需独立人工评审的门批；真实 improve 循环与业务 smoke 被 U-01/02/03 阻塞。全部改动未提交，版本仍为 0.6.0。

> 评审对象：agentflows @ main / 3862083（v0.6.0）
> 评审日期：2026-09-17
> 校验基线：`python3 tools/lab/validate.py all` 8/8 PASS；`python3 -m unittest discover -s tests` 58 项全过（本会话实跑）
> 来源：五路独立评审的合并——① 本会话四路并行深查（工具链 / 角色与 skill / 记录与评测 / 文档与测试）；② 三个外部会话导出（xiaomi/mimo-v2.5-pro ×2：`6c34dd64`、`a7e23bf3`；gpt-5.6-luna ×1：`22eff650`）；③ 库内 [ANALYSIS-REPORT.md](ANALYSIS-REPORT.md) 与 [REVIEW-REPORT.md](REVIEW-REPORT.md)（外部会话的落盘产物）。
> 收录标准：所有被采纳的发现均按本仓库硬边界 12 的要求在当前工作树上逐条复核或最小复现；无法复核的注明来源；已失效的旧论断集中列入附录 A，不混入正文。

---

## 一、总体判断

五路评审在事实层面高度一致，在结论语气上分三档：

| 来源 | 一句话结论 |
| --- | --- |
| mimo 会话一（6c34dd64） | "有法院、有警察、有宪法，只是还没完成第一次真实审判"——整体合理，剩余 gap 是外部依赖 |
| mimo 会话二（a7e23bf3，即 REVIEW-REPORT.md） | "写得很好的宪法，但没有法院和警察"——治理是声明式的，不是强制性的 |
| gpt-5.6-luna（22eff650） | 设计合理性 8/10，运行可信度 5/10——契约闭环已成形，真实运行闭环未验证 |
| 本会话（合并裁定） | 宪法、法院、警察都已存在且互相咬合；真正的缺口是：**警察有静默漏报，法院还没开过庭，宪法有三个条款仍印着旧版** |

两点重要的正面证据（本会话核实补充）：

1. **"外部评审 → 修复"的环真实运转过一次。** 0.6.0 CHANGELOG 的 "Post-review follow-ups" 吸收了外部会话的四项发现（argparse 重复 choices、episode schema 的 provenance 约束、GitHub Actions CI、三个判断词的定义）。这套体系被设计出来要做的"多路证据 → 修复 → 落版"循环，在仓库自身身上已经发生过。
2. **教训吸收链经逐条核实全部落地。** 9 条真实 bug 记录声称的规则修复，对照当前源码全部存在：contracts.md 硬边界 3/12/13/14、SKILL.md 的委派与 intake 步骤、AGENTS.md 实验纪律、host_adapter 的 argv 回归测试，均可查。方法的主要敌人被证实是"规则面滞后于情境"（9 条记录中 7 条 error_kind 为 missing-constraint），而不是模型能力。

---

## 二、交叉验证对照表（本报告最有价值的部分）

五路产出有互相矛盾之处，以下以**当前工作树**为准逐条裁定。

### 2.1 已失效——0.6.0 已修复，旧报告与旧会话不再适用

| # | 论断 | 来源 | 当前状态 | 复核证据 |
| --- | --- | --- | --- | --- |
| 1 | `validate.py` argparse choices 中 `"docs"` 重复 | REVIEW-REPORT.md / a7e23bf3 | **已修** | `validate.py:1899` choices 列表中 `docs` 仅出现一次 |
| 2 | `episode.schema.json` 的 `provenance` 是无类型 object，无约束 | 两份报告 / 6c34dd64 | **已修** | 现有 `additionalProperties: false`，required `carrier`/`sanitized`（本会话实读 schema） |
| 3 | 无 GitHub Actions CI，合入门控为零 | ANALYSIS-REPORT.md | **已建** | `.github/workflows/validate.yml` 在 push 与 PR 上跑 `validate.py all`（内含 tests；末尾再单跑一次 unittest 属冗余但无害） |
| 4 | "小改动 / risky work / 相同原因"无判定标准 | 两份报告 | **已定义（prompt 级）** | SKILL.md "Judgement calls made checkable" 一节（:112 起给出 same cause 的可操作定义）。注意：定义存在但仍是 prompt 级、机器不可判定——"无标准"不成立，"标准无机器执法"仍成立 |
| 5 | "repair once" 一轮还是无限次 reopen 有歧义 | REVIEW-REPORT.md | **措辞已被替代** | SKILL.md:88 现为 "a re-review may be scoped to the delta since the last reviewed revision"，歧义源已不存在 |

> 提示：外部会话导出于 0.6.0 定稿之前，其部分发现被 0.6.0 吸收。**继续把 ANALYSIS-REPORT.md / REVIEW-REPORT.md 当现行事实引用会误导后续工作**，见附录 A。

### 2.2 被驳回——经复核不成立

| # | 论断 | 来源 | 裁定 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | `mock/README.md` 引用不存在的文件 | 本会话深查代理之一 | **不成立** | `fixed-pending-review-demo.md` 与 `rejected-bug-demo.md` 均在盘上（代理只 ls 到 archive 截断处） |
| 2 | `marketplace.json` 顶层 `version: 1` 与 semver 不一致是缺陷 | 两份报告 | **非缺陷** | 该字段是 marketplace 清单格式版本，非插件版本；校验器经 `plugins[0]` 取值是正确行为（mimo 会话一的澄清，采纳） |

### 2.3 仍然成立——外部会话原创发现，本会话复核或复现确认

| # | 论断 | 来源 | 严重度 | 本会话复核证据 |
| --- | --- | --- | --- | --- |
| 1 | **业务评测 `target_docs` 无路径包含性校验** | gpt-5.6-luna | P1 | **已复现**：`host_adapter.validate_business_request`（`host_adapter.py:294`）对 `target_docs` 只查"非空字符串数组"（:330-335）；传入 `["/etc/passwd", "../../outside.md"]` 畅通通过，未抛错。提示词是唯一防线 |
| 2 | **`repeat_count` 被 CLI 覆盖，破坏 baseline/candidate 可比性** | gpt-5.6-luna | P1 | **已复现**：`eval_runner.build_request`（`eval_runner.py:191`）将 `args.repeat_count` 直接写入每个用例，用例自身的冻结值（eval-case schema 必填字段）从未被读取或比对；`--repeat-count` 是必填 CLI 参数（:455），调用者可造出与冻结用例不可比的运行 |
| 3 | manifest `description` 三种文案、`license` 仅 ZCode 声明 | 两份报告 | P3 | 实测四个 manifest：三种描述、仅 `.zcode-plugin` 有 `license: MIT`；name/version 有 `validate manifests` 守，description/license 无守 |
| 4 | evaluator / feedback-analyst 角色是骨架 | 两份报告 | P2 | `wc -l`：18 / 18 / 16 行（evaluator / feedback-analyst / release-governor），信息密度尚可但操作化细节确实薄 |
| 5 | 指标在多处重复定义 | mimo 会话一 | P2 | `evaluation-result.schema.json`、`release-record.schema.json`、`policy.py`、`eval_runner.py` 四处；**但 ContractPinTests 钉死了它们不漂移**——是"改一处要同步四处"的维护成本问题，不是漂移问题（采纳 mimo 会话一的这个 nuance） |
| 6 | `validate.py` God Object | 四路一致 | P2 | 1972 行单文件身兼 schema 验证器、六类文档校验、两个报表、安装比对、CLI 分发 |
| 7 | 纯 prompt 治理 / `maxTurns` 不验证 / ZCode 无 host adapter / improve 循环从未跑完 / 归纳台账仅 1 类 | 四路一致 | 见各节 | README 与 AGENTS.md 自己声明，属诚实披露而非隐瞒 |

---

## 三、确认问题清单（按当前树）

### 3.1 P0：一致性矛盾——正在误导读者，全部是文字级修复

1. **三条 0917 记录的正文与 frontmatter 自相矛盾。** frontmatter 已是 `status: fixed-pending-review` + `fix_revision: agentflow 0.4.2`，但「## 修复」段仍写"规则改动**尚未实施**，本记录保持 `open`，不写 `fix_revision`"。亲证 `records/bugs/2026-09-17/concurrent-writers-same-branch.md:57`，同批 BUG-…-01/03 同模式。「## 变更记录」记了流转，唯独正文旧文本没改——任何读到「## 修复」段的人会得出与 frontmatter 相反的结论。这违反了记录体系自己的规矩（corrections update the record）。
2. **AGENTS.md 停在 0.5.0 之前。** `AGENTS.md:61-63` 仍写 "plans are JSON. A plan file is named exactly `<plan_id>.json`"，而 0.5.0 起计划已是 Markdown 融合形态（schema、records/plans/README、实际文件全为 `.md`）。更结构性的问题：专门为抓这类漂移建的 `validate docs` 门，扫描面**不含 AGENTS.md**——这处漂移是结构性抓不到的。
3. **records/README.md 的 reviews 索引行是旧布局。** 索引表写 `reviews/YYYY-MM-DD/<project>-<slug>/`（日期锚定），同文件约定段、reviews/README、review schema、校验器全是 0.4.0 之后的 feature 锚定布局（无日期层）。同页两套约定并存。
4. **improve SKILL 第 9 步的校验承诺与实现不符。** SKILL 称 candidate 记录、评测结果、comparison、release record 都 "validated against its schema"；实际 `release-record.schema.json` 全仓无任何实例校验器，comparison 工件连 schema 文件都没有，candidate 记录的实例校验只在 `policy.py` 里以副作用形式存在。
5. **宿主绑定与指令矛盾。** agentflow SKILL 的 "Bind to the host" 对 Claude Code 只列 4 个角色，但全文对所有宿主强制"material bug 走 investigator → fixer → reviewer → recorder 全序列"、"planning 发给 plan-architect"——在 Claude Code 上会出现"指令要求启用一个未声明的角色"。
6. **角色正文宣称自己做不到的事。** `plan-architect` 与 `bug-recorder` 正文说计划/记录要 "written and validated"，但两者 `disallowedTools: Bash`，跑不了校验器；校验责任实际在 supervisor，措辞会误导角色自己去跑命令。

### 3.2 P1：工具链静默漏报族——"数据不正时检查无声"

这一族缺陷的共同形态与本项目最反对的事（"A check you cannot reproduce counts as not run"）同构，故整体定为 P1：

| # | 缺陷 | 位置 | 形态 |
| --- | --- | --- | --- |
| 1 | `records/` 顶层与未知子目录下的文件被静默跳过，不校验也不报错 | `validate.py:1280` 起的分发逻辑 | 实证：`records/.DS_Store` 在盘，`validate.py artifacts` 照样 PASS |
| 2 | 测试目录清空后 `validate tests` 仍 PASS（只看 unittest 退出码，0 个测试 = exit 0） | `validate.py:1652-1661` | 无法区分"回归通过"与"没有回归可跑" |
| 3 | `load_json` 不捕 `UnicodeDecodeError`，坏编码文件令整个 validate 裸 traceback | `validate.py:120-124` | 违背自身"每条失败都应是 ValidationError"的输出契约 |
| 4 | `examples/invalid` 负例按文件名前缀匹配，拼错名的负例被静默忽略；且负例只覆盖 bug/plan 两类 | `validate.py:1038-1043` | "examples 检查拒绝逻辑"的宣称覆盖面远小于实际 |
| 5 | `isolation.py` 对非 ASCII 路径拿到 git 八进制转义伪路径，不去引号不反转义 | `isolation.py:131-141` | 当前保护路径全 ASCII，是**潜在** fail-open 而非现实绕过 |
| 6 | `validate.py` 与 `isolation.py` 对 protected-paths.txt 行的归一化规则不一致 | 两文件 | 一个 fail-open 一个 fail-closed，同一清单被两个守门人按不同规则解释 |
| 7 | **`target_docs` 无路径包含性校验（本会话复现，见 2.3#1）** | `host_adapter.py:294` | "只读目标快照"边界的防御纵深缺失。缓解因素：`evals/` 在保护门内、用例经人工评审，利用它需要一次 gate change；但 adapter 层加包含性检查只要几行，且不需要把企业路径拖进公共校验面 |
| 8 | **`repeat_count` 被 CLI 覆盖（本会话复现，见 2.3#2）** | `eval_runner.py:191` | 与 #7 同属"评测机械面的边界靠约定不靠检查" |

### 3.3 P1：闭环断点——improve 循环的证据层

- **四个中枢交接物没有落盘位置与生产者。** candidate record、evaluation result、comparison、release record 无路径约定：candidate-engineer 被禁写 `records/`，evaluator 只读且无 Bash，release record 无人被指派。`records/README.md` 自己承认 "when the improvement control plane lands"——未落地。会话一旦中断，除 episode 外的循环证据全部丢失，这正是 episode README 警告过的失败模式，被复制到了循环其余环节。
- **verified 终态从未达成。** 9 条真实 bug 记录 0 条走完独立评审闭环，`records/reviews/` 只有一个 README、零真实使用。"作者不得自证"这条硬边界，在仓库自己的记录上处处悬置——每条都停在"修复者自证 + 等一个没有被指名的评审人"。
- **0.6.0 的三条 P1 修复零回归面。** 记录诚实标注"无自动化检测面可跑"，保护依赖"再犯才升级"的 recurrence 机制——等于用下一次失败来验证上一次的教训。
- **promote 之后的监控-回滚段无承载者。** SKILL 第 13 步写成可执行条目，但无角色、无工具、无记录类型；escalated 的 re-consolidate 要动 protected 文件，实际只能人工 gate change，指令读起来却像循环内动作。
- **feedback-analyst 的产出不可持久。** 输出仅作为消息返回，无 schema、无落盘要求；而 candidate.schema 的 `evidence_ids` 要求引用稳定证据 id——两者之间缺一环。

### 3.4 P2：测试盲区与维护性

- **`policy.py` 零测试**——274 行的确定性发布裁决逻辑（promote/revise/reject），protected，却在整个测试面之外。
- **`isolation.check_diff` 的阻断末端未测**——只测了 `changed_paths`，protected 前缀匹配的最后一跳没有覆盖。
- **三个门完整性检查自身零回归**——`validate_manifests` / `validate_protected_paths` / `validate_unit_tests` 的负向路径（版本分歧、清单缩水、tests 目录被塞东西）没有任何测试。"tests pin the gate tools" 的宣称只对了一半。
- **执法面会静默退化，且台账没抓到。** 实证：BUG-20260915-001 修复中唯一被机器强制的 `shared_mechanisms[].registration_ref` 必填，在 0.5.0 plan 重设计中被整体移除，替代的「## 接口与共享机制」是 optional 且不在必需标题里，原记录没补任何变更行——这次退化是靠 self-audit 发现的，不是靠 recurrence 环。
- **0.3.x 有四次 patch 位承载破坏性契约变更**（0.3.4 closure_criteria、0.3.7 中文标题字面量、0.3.8 severity 枚举替换、0.3.9 必填 provenance）——0.x 语义下破坏性变更应进 minor；0.4.0 起已纠正。
- **手工同步面大而门窄**：bug 契约在 5 处重复、"设计完备性三件套"在 5 处近逐字重复、角色文档 3 处镜像、semver pattern 在 schema 中重复 7+ 次；`validate docs` 只钉住很窄的一组断言——AGENTS.md 漂移正是从这道窄缝漏掉的。
- **公开评测语义自报**：AF-001–015 的 `accepted`/`first_pass_review` 由被测模型自报，harness 只保证 JSON 合法；机器可判定的只有结构校验与业务切片 3 例（种子评分设计好，但纯子串匹配可被答案键过拟合——命中种子而整体判断差仍会被接受，gpt 会话的观点，采纳）。holdout 字段存在但全仓零用例。
- **仓库卫生**：`mock/` 从未入库但 CHANGELOG 0.5.0/0.5.1 引用它（fresh clone 拿不到演示面）；`ANALYSIS-REPORT.md`、`REVIEW-REPORT.md`、`.commandcode/` 长期挂 untracked，且两份旧报告已有多条失效论断（附录 A）——留过时报告在工作区比没有报告更危险。

### 3.5 关于"纯 prompt 治理"的定位裁定

五路评审都点到"治理是声明式的"。合并裁定如下：**这不是缺陷清单，而是产品定位声明，且仓库基本是诚实披露的**——README 明说 canary/自动回滚/遥测未实现，AGENTS.md 明说 `maxTurns` unverified。隔离从来不是 prompt 承诺的（硬边界 7 原文："isolation is a property of the host's enforcement, or it does not exist"），独立评审靠的是角色分离 + 只读工具面 + check 协议（评审者授权命令、回收原始输出），这套设计在 prompt 治理的约束下已接近上限。真正该补的强制力不是把所有 gate 机器化，而是 3.2 节的静默漏报族与 3.3 节的证据落盘层——前者是"警察失职"，后者是"法院没开庭"。

---

## 四、分维度裁定（对应用户的六个维度）

| 维度 | 裁定 | 一段话结论 |
| --- | --- | --- |
| 缺陷 | **存在，两档** | 文字级矛盾 6 处（3.1，正在误导人，半小时可修完）；工具链静默漏报 8 项（3.2，其中 2 项本会话新复现）。没有发现任何"文档声称但代码不存在"的虚增能力——反向问题只有 AGENTS.md 与 mock/ 两处 |
| 架构 | **合理，骨架诚实** | 12 角色无职责真空；三层门（声明+isolation+validate）与文档逐字一致；required⊆declared 方向正确且 validate.py 自身在门内（无"改列表放行自己"的通道）；弱点是 God Object、窄门对宽的重复面、manifest description 无守 |
| 逻辑 | **流程图完整，三处断点** | improve 循环的交接物无落盘面（最大断点）；Claude Code 绑定清单与全序列指令矛盾；plan-architect/bug-recorder 宣称能跑校验器但无 Bash。委派链"无自动触发"（investigator→fixer 靠 supervisor 手动 re-brief）是设计使然，不算缺陷 |
| 自闭环 | **契约层 ✓，证据层 ✗** | schema→validator→test 三位一体、五 manifest 有门、测试目录声明式断言——契约闭环成立且是同类项目上游水平。但 verified 0/9、review 桥零使用、四交接物不落盘、改进循环从未真实跑完一轮——**机制的第一次真实运行本身就是最大的未验证假设** |
| 升级 | **演进纪律好，历史有瑕疵** | 0.4.0 起 semver 纪律正确、每版有 CHANGELOG+iteration-log 双记录、breaking change 均有人工 gate change 留痕；0.3.x 四次 patch 位违例是历史债；schema 无版本字段与弃用策略；registration_ref 退化事件说明执法面需要"降级也要留痕"的规则 |
| 归纳 | **设计好，样本饿死** | recurrence 台账（derived tier、escalated 自动升级、provenance 归因铁律）设计合理，9 条教训逐条核实已落地源码；但台账仅 1 类、consolidation 全人工、无自动聚类、归纳只覆盖 agentflow 自身。归纳机制不缺设计，缺的是喂给它的独立评审过的记录 |

---

## 五、优先级行动清单

### P0——半天内的文字与边界修复

1. 三条 0917 记录的「## 修复」段改写为与 frontmatter 一致（正文已完成的事实用完成时态，历史留给「## 变更记录」）。
2. `AGENTS.md` 计划契约描述改为 Markdown 形态，**并把 AGENTS.md 纳入 `validate docs` 扫描面**（否则下次漂移还是抓不到）。
3. `records/README.md` reviews 索引行改为 feature 锚定布局。
4. improve SKILL 的 Claude Code 绑定清单补全角色；plan-architect / bug-recorder 的 "validated" 措辞改为"交 supervisor 校验"。
5. `host_adapter.validate_business_request` 增加 `target_docs` 路径包含性检查（拒绝绝对路径与 `..`，real run 时 resolve 后必须落在 `business_root` 内；dry run 也查形状）——约十行，附带 pinned 测试。
6. `eval_runner` 加载套件时断言 CLI `--repeat-count` 与每个用例冻结值一致，不一致即拒绝（fail-closed 方向）。

### P1——本周

7. 静默漏报族四项：records 未知路径显式报错；`validate tests` 断言最低测试数；`load_json` 补 `UnicodeDecodeError`；负例 glob 改声明式清单。
8. 补三个零测试面：`policy.py` 裁决矩阵、`check_diff` 阻断末端、三个门完整性检查的负向路径。
9. 给 improve 四交接物定路径与生产者（records/README 已预留 "when the control plane lands" 的措辞，把落点写实），comparison 补 schema，release-record 补实例校验器。
10. 决定 fixed-pending-review 存量（8 条）的独立评审出口——哪怕一轮批量评审，让 verified 状态第一次真实发生。

### P2——结构性

11. 拆分 `validate.py`；指标定义收敛为单一 `$ref` 源（有 ContractPinTests 兜底，不急但值得做）。
12. mock/ 二选一（入库或移除），`.commandcode/` 加 gitignore，两份过时报告归档或删除（其有效论断已并入本文件）。
13. **跑一次最小真实 improve 循环**（baseline → candidate → eval → decision → release record）——这是五路评审共同的最终建议：任何新增设计都不如让机制第一次真实运转更能验证这套体系。
14. 业务 smoke 的三个 P0 未决项（U-01 可信端点、U-02 权限档、U-03 快照放置）排期解决，让业务切片从 instrument-ready 走到 measured。

---

## 附录 A：失效论断明细（避免旧报告继续误导）

以下论断出现在库内 ANALYSIS-REPORT.md / REVIEW-REPORT.md 或外部会话结论中，**当前树已不成立**，处理旧文件时请以此为准：

1. "argparse choices 中 docs 重复" —— 0.6.0 已删（`validate.py:1899`）。
2. "episode provenance 无类型 object、校验漏洞" —— 0.6.0 已加 `additionalProperties: false` + required 字段。
3. "无 GitHub Actions CI" —— `.github/workflows/validate.yml` 已落地并跑全部检查。
4. "小改动/risky work/相同原因无判定标准" —— 0.6.0 已在 SKILL.md 定义（prompt 级；"无机器执法"仍成立）。
5. "repair once 歧义" —— 措辞已被 scoped-delta re-review 替代。
6. "mock/README 引用不存在的文件" —— 复核不成立（文件在盘）。
7. "marketplace.json version:1 类型不一致是缺陷" —— 澄清为清单格式版本，非缺陷。

仍然有效的旧报告论断已全部并入第三节正文，不再重复。

## 附录 B：来源与复核方法

| 来源 | 覆盖面 | 本会话处理方式 |
| --- | --- | --- |
| 本会话四路并行深查 | tools/lab 逐行、agents+skills 全量、records/schemas/evals 全量、docs/tests/manifests 全量 | 关键断言（记录矛盾、静默跳过、零测试 PASS、CI、episode schema、argparse、mock 引用）逐一亲证 |
| mimo 会话 6c34dd64 | 全局合理性 + 对旧报告的反驳 | 其反驳三条全部采纳进 2.1/2.2；指标四定义的 nuance 采纳 |
| gpt-5.6-luna 会话 22eff650 | 业务评测边界 + 评测方法论 | 两项技术发现按硬边界 12 **最小复现确认**后收录为 3.2#7/#8；评分器过拟合与优先级观点采纳 |
| mimo 会话 a7e23bf3（产出 REVIEW-REPORT.md） | 七维度框架 | 其论断逐条对当前树复核，失效项入附录 A，有效项并入正文 |
| ANALYSIS-REPORT.md（外部会话落盘产物） | 同上 | 同上 |

复核命令记录：`validate.py all`（8/8 PASS）、`unittest discover -s tests`（58 项）、针对 3.2#7/#8 的两个最小复现脚本（输出见 2.3 表）。本报告本身未修改任何仓库文件。
