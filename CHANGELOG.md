# 变更日志

> 0.22.1 及更早版本的历史条目已移入 [docs/changelog-archive.md](docs/changelog-archive.md)（按原样保留）。
> 2026-10-30 按 T21 压缩为每版 ≤10 行；详细记录移入归档，原始提交历史可回溯。

## 0.30.0 — 2026-11-04（可用性批：init 安全化、评审分档与缺陷落账）

- init 脚本化先行：`scripts/init_workspace.py` 重写为安全安装器（`--dry-run` 计划先行、托管块只追加/替换不覆盖既有文件、载体改为官方入口 AGENTS.md / `.cursor/rules` mdc / `CLAUDE.md` 指针 / copilot，移除不在官方清单的 `.zcode/rules/`，`.agentflow/manifest.json` + `--check` 漂移校验，自测 8/8）；`templates/host/maker.md` 引用全部改为目标仓可解析路径。
- 评审改革：`references/contracts.md` 新增「评审简报必填字段」（review_scope 三态 / 内联对象 / stop_rule / output_budget），reviewer 对不合格简报回 `blocked`；通过项只报 `PASS <检查编号>`，引用义务收窄到 finding；新增 `scripts/review_snapshot.py`（快照钉修订替代 sha256 清单，自测 5/5）。
- `SKILL.md` 新增「分档默认值」节（S/M/L 评审与测试档位、browser 自检前移、缺陷落账分级、收口用户验收）；Init 第 0 步改「脚本先行，AI 只填项目事实」。
- 工程底线接线：backend / frontend / reviewer 角色各加 standards 分册判定行；`issue-tracking.md` 改分级落账并新增 `escape_stage`；proposal 加 §1.4 范围穷举与存量面处置；design/be §1.3.2 堵「N/A 免责」改「DDL 或等效结构契约」必填；testing plan 加必选边界清单与 `ac_refs`；`releases/todo.md` 删批次索引、「状态单点」「缺陷落账」「用户演示收口」三条门条款进 repo-rules；`templates/README.md` 加落地映射表。
- 门内三项检查（C28/C29/C30）按 protected 面规则以 `DEC-2026-002/003/004` 提案登记拍板口，本批未动 `tools/lab/`。
- 根 `AGENTS.md` 新增「规范改动没有重装等于没改」发布链纪律；`check-testcases.py` 修 AC 定义识别（定义表行首匹配，引用不计入定义）并加 `--self-test`（4/4）。
- 验证：`validate.py docs` / `decision_gate` PASS、`unittest discover` 260 OK、三脚本自测合计 17/17；`installed` 待 push 后重装转绿。
- 第二轮八份复盘文档全量对账补齐：design/be 字段表固定十列（补规范化 / 生命周期 / 存储载体 / 代码落点）；standards 增「按规模分级」（单进程批次声明即放行，防 demo 照字面即红）；`releases/todo.md` 改发布队列（状态列只许引用）、hub/index 批次清单删状态列、feature README 进度总览改指针；testing plan 接 `testcases.yaml` 机读权威、run 实际结果按步骤号对齐；契约增「跨阶段不复用 reviewer」；SKILL 增「原型前置」义务；门提案扩至七条（DEC-2026-002…007：AC 闭合 / 实体字段表+C4 松绑 / 状态单点 / 执行期立案 / 候选集门 / 门清单声明补齐）。

## 0.29.0 — 2026-11-02（设计图能力独立成 skill）

- 新增第二个 skill [`skills/design-diagram/`](skills/design-diagram/SKILL.md)：时序图、流程图、状态图、架构图、ER 图的画、改、评。此前「要哪些图」已由文档链的形态要求覆盖，但「画成什么样算合格」散落在各目标仓的图示规范里，每接一个新仓就要重写一遍。
- 内容取舍按**不新增图种、不改形态判据**：三条铁律（主干化 ≤15 节点、事件号/状态号锚点、同一主题只画一次）、四步顺序（选层 → 画 → 验 → 登记回链）、反例四条（均有真实事故出处）、交付前自检按「门禁项 / 人工项」分开——门禁绿不等于图合格，这是最容易误判的一条。
- 模板三份：[时序图](skills/design-diagram/templates/sequence.md)（含 `par` / `critical` / `break` 的选用判据）、[状态图](skills/design-diagram/templates/state.md)（九列明细表逐行填满，含裸 `S01 -->` 会被判未命名的坑）、[ER 图](skills/design-diagram/templates/er.md)（基数、多对多中间表、逻辑关联与物理外键的区分）。三份都带无障碍字段与主题块——这两项是多数门禁的强制项，缺了模板复制出去必然红。
- [`references/gate-findings.md`](skills/design-diagram/references/gate-findings.md)：报错原文、原因、修法三段对照，含两类实战经验——SSRF 网段表会被误判成真实内网地址（不要为消警告删网段表），以及「硬提示」类告警改不了级（严格模式也不变红，必须人工判断）。
- 登记：`skills/agentflow/SKILL.md` 入口表与 `references/carrier-map.md` 各加一行指针；`index.md` 加「画、改、评设计图」一行。**要哪些图仍归文档链**，本 skill 不复述形态判据。
- 验证：`validate.py all` 全 PASS（docs 对象数 206 → 211，即新增 5 份文档被纳入扫描），`packaging/runtime` 已重建。


## 0.28.0 — 2026-11-02（开工提问与设计压测内化）

- 把原先独立的个人级 `ask` / `grilling` 能力收进插件，作为 Intake 与架构门的正式方法，而不是另一套用户级 skill：新增 [`references/intake.md`](skills/agentflow/references/intake.md)（六要素、红线、证据层级、提问预算、任务简报输出）与 [`references/grilling.md`](skills/agentflow/references/grilling.md)（设计树、前沿、逐轮推荐、收尾门）。
- `SKILL.md`：规则表加「需求不清」「方案压漏洞」两行；运行工作流第 1 步（Intake）与第 2 步（架构门）各加一句指针——需求不清先按 intake 六要素补全，方案边界不清先按 grilling 压一轮再让 TD 出决策。
- `technical-director.md`：输入不足时要求 Supervisor 先压设计，TD 只做决策，不替用户回答，也不把「按推荐默认」写成已拍板。
- `index.md` 与 `carrier-map.md` 登记两份新载体；`grilling.md` 标注改编自 mattpocock/skills（MIT，Copyright (c) 2026 Matt Pocock），去掉个人档案/复盘，补了与 `PENDING-DECISIONS.md`、决策记录的衔接。
- 规则落点：`templates/host/global-rules.md` §7 补「先查后问 / 一次最多 2 问 / 红线原样保留 / 验收证据层级」，`templates/hub/repo-rules.md` §4 补验收层级，根 `AGENTS.md` 加指针；宿主安装态是托管块副本，改模板后需 bump 版本并重跑 Host Init 才更新。
- 与 0.27.0 的 QA 契约咬合：intake 的验收要素要求写证据层级（`api/browser/file/manual`），用户可见入口只接受 `browser`/`manual`；计划与执行记录的入口/层级列仍是机器强制点。
- 验证：`validate.py` 的 schemas / examples / artifacts / protected / manifests / docs / tests / doc_chain / doc_chain_live / decision_gate / lint 全 PASS，`unittest discover -s tests` 260 OK；`packaging/runtime` 已重建。未重装宿主快照，`installed` 在重装前如实报漂移。

## 0.27.0 — 2026-11-02（QA 入口与证据层级契约）

- 起因是 ISS-2026-050 类事故：登录弹窗入口从上线到被发现一次端到端都没验过，而执行记录仍报「登录 PASS」——用 `curl` 协议链 200 顶替了浏览器里的用户入口。本版把「入口」与「证据层级」写进测试契约，让门能判「这条用例到底从哪进、用什么层级测的」。
- 测试契约 v2（`recorded_at >= 2026-11-02` 起强制，存量不追溯）：计划注册表加 `入口` 列并逐条非空；执行结果表加 `层级` 列（`browser / api / file / manual`）；`e2e` 用例的 `pass` 只接受 `browser` / `manual`；`decision: pass` 从「零 fail 零 blocked」收紧为「零 fail、零 blocked、零 not-run」；`not-run` 行必须写清阻塞什么。
- QA 策略层补齐（`templates/feature/design/qa/testing.md`）：新增 §2.1 入口矩阵（按钮 / 弹窗含 iframe / 整页跳转 / 深链 / 回调页 / 脚本 / 纯接口）、§2.2 证据层级与断言独立性、§2.3 掩盖条件（旧数据 / 遗留 cookie 或缓存 / 构建期内联 / 功能开关），发布判断加「P0/P1 的 not-run 为 0」。
- 角色增强：`test-planner` 产出入口矩阵与逐用例断言依据；`test-executor` 记录实际层级、`blocked` 必须写已尝试的替代路径、不得降级为观察项；`reviewer` 与 `review-checklists` 的 Test depth 加入口/层级/循环自证三项固定检查；`bug-investigator` 增加 M1–M5 验证缺口归因；`bug-fixer` 要求「红→绿」与同构多端逐端验；`technical-director` 增加跨域会话契约（接收方义务）；`plan-architect` 要求用户可见任务写验收层级。
- 缺陷模板加 `## 验证缺口`（`attribution: product_code` 必填），把「为什么没被拦住」随诊断带进修复简报。
- **门变更（受保护面，人工评审）**：`tools/lab/gate/testing.py` 的上述四条判据；`schemas/` 未改（新列在正文，不在 frontmatter）。负向验证在 `/tmp` 一次性样本上实跑：`pass + not-run`、`e2e + api`、缺 `层级` 列、缺 `入口` 列、`not-run` 无阻塞说明五例均判红，正例零 error。
- 验证：`validate.py` 的 schemas / examples / artifacts / docs / doc_chain / doc_chain_live / decision_gate / lint 全 PASS，`unittest discover -s tests` 260 OK；`packaging/runtime` 已重建。未重装宿主快照，`validate.py installed` 在重装前会如实报漂移。

## 0.26.0 — 2026-11-02（自述一致性全量核对批）

- 两路只读审计 + 主代理逐条对着代码验真，把「文档说的执法点 / 模板教的写法」与「门实际强制的东西」全量对了一遍：**新出 13 处对不上**（加上归档口径那 4 处，累计 17 处），**没有一处是门代码写错**——全是散文与模板漂移。修法一律以代码为权威，不动门。
- 文档侧 8 处：`DECISION_MARKER` 的行号引用过时（实在 `checks.py:836`，旧述 `:719` 现在是 C19 报错字面量）、三个实现角色行数旧值（`bug-fixer` 28 非 22）、`doc_chain_live` 覆盖面写成含 `docs/product/`（实在 `gate/checks.py:237` 只有 `docs/features`）、「本仓不保留归档桶」未限定层级并补四义对照、`episodes/README.md` 把门的递归扫描写反（`root.rglob` 实扫到 `归档/` 下 46 个文件）、`escalated` 档位「触发 improve 环」（该环 2026-10-29 已裁撤，`reports.py` 只推导打印）、`todo.md` 把 C18/C22 的载体写成导航表（实读各批次 README）、`document-chain.md` 的 C1–C26 应为 C1–C27。
- 交付面 5 处会教出红线的写法：轻量降档必须有字面标记行（`checks.py:540` 的识别式），段落映射写「—」不顶替；proposal 的「spec/qa 按需」需 README 声明 `qa 不适用`/`无 qa 轨` 才豁免 C19；拍板口模板补上 `DEC编号/修订/撤回/等价/终态` 五个生命周期列（`decisions.py:292` 缺列即报，本仓实表 15 列）；`templates/testing/run.md` 补 `findings`/`flow_findings`（schema 有该字段且 `additionalProperties: false`，bug 去向靠它校验）；hub issues 模板的台账标记改为给出**独立声明行**并解释开关语义。
- C18 的接口此前无处可查：判据要表头含 `记录编号 | 任务号`（`checks.py:1090`），而 AGENTS.md 只说「挂进批次承接表」、模板里根本没这张表、分册也完全没写 C15–C18 各读哪张表——新仓照模板做，开放记录登记当天必红。本轮三处补齐：AGENTS.md 写明列名与「两张表别混用」、`document-chain-checks.md` 加四标记 × 四张表对照、`templates/feature/README.md` 加记录归属表骨架。
- 我自己本轮引入又当场改掉的一处：改 hub 模板时在散文里裸提了一次 `agentflow 问题台账` 词面——按 `checks.py:1252` + `:1194-1196`，目标仓的 issues README 只散文提及、无独立声明行即判「提及但未声明」。同类缺陷记进记录第 11 条。
- **未闭合的门覆盖缺口**：没有任何检查把「文档点名的执法点」与「代码实际执法点」对照起来，C27 只管阶段文档与模板的相似度、不管模板口径是否与门一致。补这条属门变更，未擅自实施，登记在缺陷记录的「修复方案」节等你授权。
- 记录：`docs/issues/ISS-2026-11-02-归档口径的执法点与模板互相打架.md` 追加「全量核对」节（13 处逐条含 `文件:行` 与实况）。
- 发布 0.26.0（提交 `bfbf9a3`，已推送 origin/main）并三端重装：`validate.py all` **12 项全 PASS（退出码 0）**、`unittest` 260 OK、`doc_chain.py --self-test` 157/157、`artifacts` 137 objects；ZCode / Codex / Qoder 均为 0.26.0，Qoder 侧 `installed --path` PASS 且 `agents`+`skills` 与源面逐字节一致。

## 0.25.1 — 2026-11-02（归档口径统一）

- 实测钉口径：在一次性 worktree 副本上跑两例，逐字命中 `a rejected record must be moved into issues/归档/` 与 `only rejected records may be archived; verified records stay in place`——确认「只有被拒进归档、已验证原地保留」是机器约束而非惯例，副本跑完即 `git worktree remove --force` 拆除，真实树全程未动。
- 定义收拢到单点：`docs/issues/README.md` 的「归档规则」节写明四件事——只有 `rejected` 进 `归档/<recorded_at 日期>/`、关闭态不搬的理由（id 即文件名，台账与评审按路径引用）、执法点分两处（状态↔位置在 `tools/lab/gate/workspace.py`，形状与 id 在 `records.py::validate_bug_layout`）、以及本仓「归档」一词的四义对照（缺陷被拒桶 / `episodes/归档/` 按月下沉 / 评测件 `archive/` / 评审快照 `archive/<轮次>/`，后三者与记录状态无关）。
- 更正三处打架的自述：`docs/issues/README.md` 旧节把两条判据一并归给 `validate_bug_layout`（实测证明位置耦合在 `workspace.py`）；`episodes/README.md` 声称 episode 归档「采用与 `docs/issues/归档/` 一致的口径」（两者并不一致，改为「不同义，别互相套用」）；本文件 0.25.0 节把「口径禁止」写成「改门需授权」，已附勘误。`reviews/agentflow-关闭证据门/archive/2026-10-28-001/` 内的旧归属作为当轮逐字快照原样保留，由定义节声明其已过时。
- 模板侧修正与本仓相反的规则（接入新仓会被教错）：`templates/hub/issues-README.md` 与 `templates/hub/index.md` 原写「关闭或被拒条目移入归档」——照做即在 `verified` 上进归档、门直接判红；改为「只有被拒进归档，已验证原地保留」，并把看板表头对齐 `AGENTS.md` 的台账四列（编号 / 一句话 / 记录链接 / 归属，行内不写状态结论），去掉与 C15 打架的「状态」列。
- 立缺陷记录：`docs/issues/ISS-2026-11-02-归档口径的执法点与模板互相打架.md`（`fixed-pending-review`，待独立评审后推进状态）。
- 发布 0.25.1（提交 `c5eae26`，已推送 origin/main）并三端重装：`validate.py all` **12 项全 PASS（退出码 0）**、`unittest` 260 OK、`doc_chain.py --self-test` 157/157、`artifacts` 137 objects PASS（含新记录）；ZCode（`Updated plugin ... from 0.25.0 to 0.25.1`，需重启加载）、Codex、Qoder 缓存均为 0.25.1，Qoder 侧 `installed --path` PASS 且 `agents`+`skills` 与源面逐字节一致。

## 0.25.0 — 2026-11-02

- 本版的实际内容是一轮瘦身：交付面（`agents/`、`skills/`）只有 `roles.md` 的两处语料地址改为 git 载体，其余全部是仓内记录面的收拢。
- 删除 10 个已完成批次目录（`docs/features/feature-2026-10-{13,22,25,26,28×4,29}-*`，175 个文件、6.1 万行）：逐批看板已 23–30 ☑ 或「本期不做」、入口门与独立评审均闭环，按 `docs/features/README.md`「完成批次不长期留存」的既有口径删除，原文以 `agentflows@c8ed0b2:docs/features/<批次>/` 取回。`docs/features/README.md` 的在途批次表随之收拢为一句指针——不留与已删看板打架的第二份状态结论。
- 记录面引用改写：8 条缺陷记录的 `files` 移出 12 条批次路径（取回地址记在正文），1 条（L3 安装摘要矛盾）保留仓限定引用并嵌入决定性片段以自证；episodes 41 条证据字段 + 13 处内嵌路径限定为 `agentflows@c8ed0b2:`；index.md 8 条批次索引的 17 个仓内链接改为载体串。
- 连带后果（如实记）：`doc_chain_live` 的活文档面从 124 份降到 1 份（只剩 `docs/features/README.md`），C27 与本仓真实文档的对照在本轮之后不再有对象，直到下一个新批次建立；待验收第 11 行 ⑥ 的「123 份真实文档无一命中 C27」其对象已消失。
- 评测面收口：活跃面按既有「留三」口径落成实际——10-19 任务书、10-20 评测、10-21 行动件、10-23/10-26 审核共 5 份下沉 `docs/evaluations/archive/<文件日期>/`，活跃面只留 10-28 评测、10-28 耗时基线、10-29 对照实验三份；`README.md` 收存清单补齐此前漏记的对照实验一行（清单与在盘文件各写各的，属本仓记录过的同一形态），index.md 与 changelog-archive.md 的两个失效链接随迁。
- 更正一条虚假自述：`ISS-2026-09-19-office计划采纳汇总` 声称 16 份外部记录「已迁入 `docs/issues/归档/2026-09-19/`」，实为该目录在盘为空、git 从未含该路径，原件随 `bf5ae9d` 删除——17 处取回地址改为只引用 git 历史载体，并在记录的变更记录节留痕。
- **未做的两项（如实记）**：54 条 `verified` 缺陷记录不搬 `docs/issues/归档/`——归档桶只覆盖 `rejected`，两个方向都由门判红（`verified` 放进归档即 `FAIL artifacts: only rejected records may be archived; verified records stay in place`），且搬动只是换目录、不减体量。`docs/changelog-archive.md`（184K）无新的早期节可并——现行 CHANGELOG 只含 0.23.0 之后的节。
  - 勘误（2026-11-02 同日下午实测）：本条原写「由 `tools/lab/gate/records.py` 的 `validate_bug_layout` 强制，且…要改受保护的 schema，属门变更需显式评审」——执法点应为 `tools/lab/gate/workspace.py:159-167`（状态↔位置耦合），`validate_bug_layout` 只管文件名形状与 id 唯一；`schemas/bug-record.schema.json` 里那句只是 `description` 散文、不构成约束，搬 `verified` 不需要也不允许改门。原句把「口径禁止」写成了「需授权」，已随口径统一批更正。

- 发布 0.25.0（提交 `81463c7`，已推送 origin/main）并三端重装：`validate.py all` **12 项全 PASS（退出码 0）**、`unittest` 260 OK、`doc_chain.py --self-test` 157/157、`artifacts` 136 objects PASS；ZCode（`Updated plugin agentflow@agentflow-local from 0.24.0 to 0.25.0`，需重启加载）、Codex（`personal/agentflow/0.25.0`）、Qoder（拷 `cache/local/agentflow/0.25.0` + 改登记表，`installed --path` PASS、`agents`+`skills` 与源面逐字节一致）。

## 0.24.0 — 2026-11-02

- 发布 0.24.0：并入 2026-10-30 收口与 2026-10-31 整改的全部已落内容。两棵工作树（主树的早期草稿 57 文件、worktree `fix/remaining-2026-10-31` 的后继版 100 文件）经逐行比对确认主树无独有内容后合为一份（`bb56cb1` 快进进 `main`）。
- 关闭「产品线完善」批与 T18–T22：`docs/product` 结论并入 `docs/design-decisions.md` §4、产品链与批次目录删除（原文 git `40147df`）；evaluations 留三归档五、16 条 office 记录汇总、评审快照按 schema 保持。
- 新增 **C27 模板骨架**判据（用户批准的门变更）：阶段文档与随插件模板的行级相似度 ≥0.85 即判红。此前把模板逐字复制成一条链**零发现**通过（形状判据全在模板自带的示例里），而真实批次 123 份文档相似度最高 0.41；补 3 条判别夹具（自测 154→157）、C27 的变异项为 M62（原自述写作 M61，2026-11-02 按 `mutate.py --check doc_chain_selftest` 逐字输出更正；M61 是既有的 C23 锚点）。模板侧配合改动：README 段落映射落点出厂为「—」（照抄不再免检 C1）、checklist 不留占位行、计划模板补 frontmatter 五必填与七列默认、验收编号方言统一、`M01-AC-01` 与 proposal §1.2 目标编号双向闭合。
- 门项数 11→12：`installed` 纳入 `all`（无本地安装打印 SKIP、不冒充通过；快照存在而漂移即判红）。实证根因是本机 11/11 全绿旁边挂着 `FAIL installed`——宿主仍在跑 0.23.0 旧快照，内含 2026-10-29 已裁撤的 `skills/improve` 与 4 个候选角色。publish/pre-push 早已排除该项，推送与发版时序不受影响。
- 交付面版本守卫（第 12 项门的一部分）：`agents/*.md` 与 `skills/agentflow/**` 内不得出现本插件版本族的字面量；全量 `x.y.z` 口径实测在模板小节号（`§1.4.3`）上有 60 处假阳性，故按 manifest 声明的主版本号判定，围栏与行内代码按引文豁免；SKILL.md 的宿主版本改指 `docs/host-platform-facts.md` Q1–Q6。
- 评估整改：修复 C5/C6 两条空转判据与写范围工具误报（3010→仅真实变更）；模板补齐目标承接表、清 C13 会话词、修决策表与埋点表头、补可选层说明与 hub/releases 骨架。
- 计数漂移与脚本口径收口：门 1–10（4 处）、README schema 计数改用标记、roles 五条链、repo-audit 补 D12、角色文件手抄 schema 计数改为以 schema 为准；publish/upgrade 缺 lint 依赖默认拦下（显式环境变量放行），删除三处死变量；contracts 明确 `task_id`/`baseline_revision` 适用于产出交付物的 worker。
- 角色面与 references 对齐代码事实：`bug-recorder` 的 `status: consolidated` 明确归再犯类清单、`test-executor` 的「更新注册表」改为「记缺口并交回」（与 `disallowedTools: Edit` 一致）、`reviewer` 严重度补 P3、三个只读角色的产物归属统一为 `## 产物归属` 节、`technical-director` 补返回字段与预算页脚；`review_tier` 载体改为评审记录、C13 豁免按逐文件清单真实描述、退役残留清除、`review-checklists.md` 接进 SKILL 路由表。
- 合并后在 `main` 复跑并通过 `publish.sh --bump minor` 发布（提交 `93d46c7`，已推送 origin/main）：`validate.py --list` 自报 12 项、**12 项全 PASS（含第 12 项 `installed`）**、`unittest` 260 OK、`doc_chain.py --self-test` 157/157、`--check doc_chain_selftest` 变异 20/20 杀死、C27 负例复现（12 份模板逐字成链报 12 条 C27；只放 README 报 4 条 C1）、`check-write-scope.sh HEAD .` PASS、`doc_chain_live` 无 C27 命中。三端已重装 0.24.0：ZCode（CLI 升级，需重启生效）、Codex（缓存 `personal/agentflow/0.24.0`）、Qoder（本机无 `qodercli`，按 `docs/host-platform-facts.md` Q6 拷缓存 + 改登记表，`installed --path` 对照 PASS）。

## 0.23.0 — 2026-10-29

- 发布 0.23.0（`f73a4e9`）；并入「全面修正与瘦身」批已落内容。
- 第二段（改进环裁撤 / 凭据 pattern / C17 变异 / 定位即预算 / 对照实验 / 判据分册）随 2026-10-30 收口推送 origin/main（`bfd93ea`）。
- 两轮 findings 已修复，第三轮 delta 复审 L2 `approved`；详情见归档与批次 README。
