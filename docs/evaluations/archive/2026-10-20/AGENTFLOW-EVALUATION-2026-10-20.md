# Agentflow 项目评测报告（2026-10-20）

> **评测者**：Agentflow 评测组 Supervisor + 8 个只读评测角色（R1–R8），各自独立上下文，R1–R7 并行执行、R8 在其后串行审计证据链。
> **被评测 revision**：`20724c0a6a8939f45980cf0ded46cbdb33a49667`（`main`，`origin/main` 同点），工作树干净。
> **基线时间**：2026-10-20 14:23:27 CST（`date` 现取）；报告封笔 15:12 CST。
> **方法**：宿主支持并行子代理 → R1–R7 **真并行独立上下文**，角色分离为实质性而非流程性。
> **只读声明**：评测全程**未修改被评测仓库任何既有文件**。全部变异实验只在 `/tmp` 的一次性副本上进行（`cp -r` 检出，保留 `.git`）。**一处例外已披露并已复原**：某个评测角色在 14:59 越界把一份自撰报告写入仓库根 `AGENTFLOW-EVAL-REPORT-2026-10-20.md`（未跟踪文件，32,759 字节）；Supervisor 于 15:07 将其**移出**仓库（保存于 `/tmp/agentflows-eval-reports/stray-role-artifact-*.md`），仓库恢复 `git status --short` 空输出。该越界本身记入本报告第十六节勘误。
> **本报告位置**：写在 `/tmp/agentflows-eval-reports/`，**不在仓库内**——评测任务书第三节的只读铁律禁止在本轮写入被评测仓库。若要归档进仓（先例：根目录 `AGENTFLOW-EVALUATION-2026-10-12.md` / `AGENTFLOW-OPTIMIZATION-2026-10-12.md` / `AGENTFLOW-EVAL-PROMPT-2026-10-19.md`），需作为一次独立的、经用户批准的动作，并同步更新 `index.md`。

---

## 〇、总览

### 十三维分数表

| 维度 | 评分角色 | 分数 | 锚点判定（一句话） |
|---|---|---|---|
| D1 架构与设计一致性 | R1 | **6** | fail-closed 确实落到工具层，但同一件事在 5 个权威表面有 5 种说法 |
| D2 门禁有效性（×2） | R2 | **6** | 变异实验 9/13 使门变红、判别力真实；但仓内三项核心量化声明不可复现 |
| D3 代码质量与安全 | R3 | **7** | 零裸 except、结构化错误纪律；3 处 fail-open + 3 处未捕获异常 |
| D4 代码工艺与可读性 | R3 | **6** | 注释解释「为什么」全域优秀；但 3 处过期注释 + 2 条规则双实现 |
| D5 Agent/Skill 契约质量 | R4 | **6** | 判断词可判定、晋升规则四处一致；但 3 条「照指令产出必被自己的门拒」 |
| D6 结构合理性 | R1 | **7** | 布局/命名/可发现性 5/5 达标；记录面→交付面存在实测可证的机械反向耦合 |
| D7 逻辑链路 | R1 | **6** | 十步主链闭环；三条链的出口普遍缺定义、5 条死条款 |
| D8 文档与记录活性 | R5 | **7** | 记录面真在更新；但四类同步面集体未回写 + 链接扫描盲点漏掉一条真实断链 |
| D9 治理与发布闭环 | R6 | **6** | `measurement: none` 口径零污染；但晋升规则无编译器、无实例、无测试 |
| D10 安全与权限边界 | R3 | **7** | 硬边界 14 条逐条可核；但写范围执法器本身不在保护区、路径作用域全靠提示词 |
| D11 实现的效果 | R5 | **6** | 40 条 verified + 42 轮评审真实；但 3 项旗舰量化指标注水、G1 样本量 1 |
| D12 存在意义 | R7 | **7** | 写范围审计与反犯档位无竞品等价物；但门**不发货**、成本倒挂场景明确 |
| D13 竞品比对 | R7 | **7** | 覆盖任务书要求的 5 家 + 3 家形态对照；两条论断越界需降级 |

### 综合分

| 权重口径 | 计算 | 综合分 |
|---|---|---|
| **默认（D2 计两遍）** | (84 + 6) / 14 | **6.43 / 10** |
| 备选一（D2 计一遍） | 84 / 13 | 6.46 |
| 备选二（D2 计三遍） | (84 + 18) / 15 | 6.40 |
| 备选三（若采 R2 原分 D2=7，默认权重） | (84 + 7) / 14 | 6.50 |
| 备选四（若 D2 从严判 5，默认权重） | (84 + 5) / 14 | 6.36 |

十三维**无一维达到 8 分，无一维低于 5 分**——全部落在 6–7 的窄带内。这既说明主体扎实，也说明**没有一维存在结构性失败**。

### 一句话裁决

**这是一套「门是真的、记录是真的、声明追不上实现」的方法论**：机器级强制（63 例文档链自测、78 条回归、51 个门变异算子、37 条受保护路径、逐字节生成树新鲜度）与其 56 条缺陷记录、41 份决策记录构成一个自洽的内部闭环；但它的**头条差异点没有离开过本仓**（`packaging/build_runtime.py:46` 把 `tools` 列入 `FORBIDDEN_TOP_LEVEL`，发货树 60 个文件里 `find -name validate.py` 为空，却有 19 处 `tools/lab/...` 引用指向不存在的命令），而三面记录面（README / AGENTS.md / 批次 README）正在集体漂移。

### 对四个问题的直接回答

**Q1｜它的门和契约，是否真的抓住它们声称抓住的违规？**
**机械级：是，但有四类真 fail-open；提示词级：多处把「自述」当成「已强制」。**
机械级判别力经变异实验证实：`schema` 词汇表守卫对 6 种未实现关键字（`unevaluatedProperties`/`dependentSchemas`/`patternProperties`/`exclusiveMinimum`/`prefixItems`/`propertyNames`）全部拒载（`gate/schema.py:351-405`）；`isolation.py check-diff` 的 9 条边界（`-` 前缀 base / base 不解析 / 检查器根与候选重叠或嵌套 / 未跟踪 / 被忽略 / 已暂存 / 中文路径 / 中文路径落在受保护前缀 / 删除受保护文件）**全部 fail-closed**；断链、退役路径、版本散文、frontmatter 不一致、manifest 版本漂移、生成树三类漂移全部拦得住。
四类 fail-open：(a) **schema `required` 的内容无人守**——从 `bug-record.schema.json` 删掉 `attribution` 后 `validate.py schemas` **PASS / exit 0**，且新增一条无该字段的记录后 `artifacts` 也 PASS；(b) **`skills/agentflow/` 完全不在受保护面**——候选改写 `references/contracts.md` 或 `scripts/check-write-scope.sh`（写范围执法器本身）后 `check-diff` 返回 `blocked: []` / exit 0；(c) **`validate.py docs` 的第 5 组断言是幽灵**——`gate/docs.py:184` docstring 与 `AGENTS.md:27` 都声称「中文镜像与英文契约文档保持段落对应」，代码里不存在任何镜像比对（`grep -rn "contracts.md\|parity\|mirror" tools/lab/ --include="*.py"` 只命中这句 docstring 自身）；(d) **`packaging/runtime` 缺席即跳过**（`gate/manifests.py:133-134` 直接 `return []`）。
提示词级被记成机器级：`AGENTS.md:19` 说 `all` 跑「共九项」，实为十项（多一项 `lint`，它需要 ruff+mypy）；`README.md:68` 称 `validate.py` 是「无依赖的契约与记录校验器」，实为两个硬依赖。

**Q2｜它的结构与链路，是否合理、是否闭环？**
**结构合理且可发现性好；链路「入口齐备、出口缺定义」。**
静态结构：从 `index.md` 出发 5 个常见任务全部 ≤2 跳可达（3 跳上限内）；命名规则在每个面内部成文且被遵守；零 `.gitkeep` 空壳；无过度分层。**唯一被实测证实的结构缺陷是方向问题**：56 条 issue 记录里 13 条 `files:` 指向 `agents/*.md`、45 条指向 `skills/`、22 条指向 `tools/lab/`，删除 `agents/plan-architect.md` 即可让 `validate.py artifacts` 整批门红——**记录面存在指向交付面的机械反向耦合**（仓内已有 `<repo>@<revision>:<path>` 的正确解法，但会移动的交付面路径没用它）。
动态链路：主工作流十步**首尾闭环**（每步输入/输出契约写明，含 FAIL 回退与有界修复环）；但三条链的出口普遍缺失——改进环 13 步的终端产物**零实例**且现行五个落点全被拒；plan 状态机无终态（枚举只有 `draft/proposed/approved/superseded`，4/4 计划停在 `proposed` 却已在执行）；`open` 对 16 条外部来源发现**无出口**（28 天零推进）；文档链的「Design 评审门」**从未跑过**，因而「Plan 前置条件（引用已冻结的设计）」形式上不成立。

**Q3｜它实际跑出了什么效果，为什么值得存在？**
**真实疗效存在，但三项旗舰量化声明不可复现；价值集中在少数几处无竞品等价物的机制上。**
疗效（经独立复算）：56 条 issue = 40 `verified`（全部 `provenance: agentflow`）+ 16 `open`（全部 external）；41 份 episode 中 19 份有非空 `review_roundtrips`，42 轮评审里 `changes_requested` 占 21 轮（50% 否决率）；9 本再犯台账 20 次 occurrence，档位 `recurred 5 / single 4 / escalated 0`；门禁有至少 11 起「门红后被修」的可查记录，含一次对外部仓计划的评审拦出 16 条真实缺陷。
注水的三项：`mutate.py` 宣称「51/51 全杀」，实跑 **43 杀死 / 6 存活 / 2 无效 / exit 1**；单元测试宣称 95/96，实跑 **78**（该数字散布在 24 个文件里）；旗舰效果实验 G1 **样本量 1**，记录自己写明「结论不得用于『有提升 / 无提升』」。
值得存在的理由（实证支撑）：①`check-write-scope.sh` 的**声明式写范围审计**——五家竞品无一提供；②「agent 不得编辑评判自己的门」这一威胁模型的机器表达（37 条受保护路径 + 冻结父 revision 的 diff 拦截 + 清单反向自证）；③**对门自身做变异测试**作为一等公民（51 个算子）；④再犯档位由事实推导；⑤claims 台账（未验证的用户可见断言 ⇒ outcome 降级 `partial`）。

**Q4｜它声称的核心差异点（确定性门 + 受治理发布）兑现到哪一步、还差什么？**
| 差异点 | 兑现到 | 还差什么 |
|---|---|---|
| **确定性门** | 本仓内 100% 兑现（10 项 + 78 回归 + 63 自测 + 51 变异算子 + 生成树逐字节新鲜度） | **不发货**：`packaging/build_runtime.py:46` 的 `FORBIDDEN_TOP_LEVEL` 含 `"tools"`；发货树 60 文件、0 个 `validate.py`，却有 19 处 `tools/lab/...` 引用 → 用户拿到一份描述不存在工具的指令与禁区清单 |
| **受治理发布** | 口径层 100%（`measurement: none` 零自相矛盾；`automatic` 晋级在结构上不可达） | **休眠态**：candidate / release-record 两份 schema 从未被任何代码实例化（`grep "SchemaValidator("` 仅 7 处，均不含这两份）；全仓 0 条实例；现行五个落点全被 `artifacts` 拒；无任何测试覆盖晋升规则；`allOf` 的「none 禁 better」分支被删后 `validate.py schemas` 仍 PASS |
| **记录即编译** | 本仓内兑现（56 issue + 41 episode + 4 plan 全过 schema） | **目标仓用不上**：`LIVE_RECORD_ROOTS` 相对插件仓根解析，而目标仓的记录枢纽在别处；`SKILL.md:90` 明令目标仓会话不得读写插件仓内部记录 |
| **（第四个未宣称的）写范围可审计** | **唯一随发货的机器级面** | 但**不受任何禁区保护**（候选可改写执法脚本本身，见 Q1-b） |

---

## 一、铁律执行自证

| 铁律 | 执行情况 | 证据 |
|---|---|---|
| 1 证据优先 | ✅ 七方共 2604 次引用出现（去重 787 个三元组）。R8 机械核对 787/787 行号在范围内，人工逐条核对 **250 条（31.8% > 30% 门槛）**，其中 238 条属实、3 条行号/文件错配、9 条逐字不符、**0 条编造引文、0 条文件不存在** | 附录 B |
| 2 实跑优先 | ✅ 所有涉及门/工具/测试的主张均附命令 + 退出码 + 逐字输出。**明确记为「未运行」的项**：`ruff`/`mypy` 相关全部（未安装且禁止 pip install）；GitHub Actions 真实运行（无网络、无 CI 记录）；竞品源码阅读（API 限流）；`record_store.py` 的 FTS5 行为（R5 未在副本跑） | 各角色【实跑记录】+【无证据推测】 |
| 3 只读铁律 | ⚠️ **一处越界已披露已复原**（某角色在 14:59 写入仓库根一份自撰报告，Supervisor 15:07 移出，仓库恢复干净）。其余全程只读；变异实验全在 `/tmp` 副本 | 第十六节勘误；`git status --short` 终检为空 |
| 4 不屏蔽输出 | ✅ 七份报告与本报告全程无 `2>/dev/null`（唯一出现的 `2>/dev/null` 在 `check-write-scope.sh:48` 内建，是**被测对象自身的代码**，非评测方屏蔽） | R8 实跑记录尾注 |
| 5 先懂再判 / 穷尽阅读 | ✅ 七方均交意图卡片；R3 命名抽样写明样本量（105 / 总体 354 / 23 文件）与判断依据；R8 核对「声明已读但无引用」= **0 个文件**；R5 诚实披露其记录面覆盖是「结构化全量 + 文本抽样」而非逐字通读 | 各角色【意图卡片】/【未读清单】；附录 B·D |
| 6 不凭记忆与摘要 | ✅ R1 明确拒绝把 `.workbuddy/memory/` 当证据；R4 把 `gate/docs.py:184` 的自述与实现分开记；R6 明确把「CI 会红」标为推理而非实跑 | 附录 B·A002/A115/A242 |
| 7 声明与强制分开计分 | ✅ 每个维度都分列「提示词级」与「机器级」，并把幽灵断言（`gate/docs.py:184` 第 5 组）单列为硬伤 | R2 H4 / R4 HP5 / R6 H1 |
| 8 时间写实 | ✅ 基线 `date` 14:23:27 CST，封笔 15:12 CST，各角色各自 `date` 现取 | 附录 A |
| 9 诚实勘误 | ✅ 第十六节集中披露本轮自身错误（含 R1/R3/R4/R5/R7 的 5 处数字错与 1 处越界写入） | 第十六节 |

**猜测句式扫描**（R8 执行，11 类词）：`应该是`/`大概率`/`通常是`/`一般来说`/`想必`/`多半`/`大概`/`估计`/`恐怕`/`似乎`/`疑似` —— **七份报告全部 0 命中**。

---

## 二、D1 架构与设计一致性（6/10）

**锚点**：落在「5–6 = 声明与实现存在系统性差距，核心承诺部分落空」的上沿。fail-closed 在工具层是真的，五面分离在目录层是真的，「无第二套 CLI」是真的；扣分全部集中在声明层，且集中在最核心的子系统（`validate.py all`）上。

**亮点**
1. **fail-closed 贯穿到工具层**（实跑）：`isolation.py check-diff` 越界 → exit 1；`check-write-scope.sh` 越界 → exit 1；`validate.py lint` 缺工具 → exit 1（fail-closed）；`validate.py:269-276` 解释器 <3.10 → exit 2「No check was run」；`gate/checks.py:84-86` 拒绝 skip；`packaging/build_runtime.py:61-76` 拒绝覆盖仓库根/祖先。
2. **「宿主原生、无第二套 CLI」成立**：`grep -rnE "socketserver|http\.server|flask|fastapi|uvicorn|asyncio|serve_forever|while True|app\.run\(|curses" tools/ skills/` **零命中**。
3. **五面分离在目录层真实成立**：零 `.gitkeep` 空壳；最大深度 9 且全是文档链强制的角色镜像结构。
4. **记录即编译在记录面真落地**：56 条 issue 全过 schema；`files:` 在盘校验；`## 现象/## 根因/## 修复` 固定字面量；`verified` 必带 `reviewer`+`review_decision`+`regression_status`+`closure_criteria` 全部机械强制。

**硬伤**
| # | 硬伤 | 实证 |
|---|---|---|
| D1-1 | **「九项」声明 vs 十项实现，且第十项需要 dev 依赖** → 干净环境必红 | 声明 `README.md:51`、`README.md:69`、`AGENTS.md:19`；实现 `tools/lab/validate.py:340-351` 是 10 项（多 `lint`），`:216-262` 调 ruff/mypy。实跑 exit 1。**四个门文档表面无一提到 `lint`**（`docs/system-guide.md:221-232`、`tools/lab/README.md:11-80`、`docs/quickstart.md:48`） |
| D1-2 | **CI 必然红**：workflow 跑 `all` 但从不装 `requirements-dev.txt` | `.github/workflows/validate.yml:32` 跑 `validate.py all`；全文 `grep -n "pip\|requirements-dev\|ruff\|mypy"` → 退出码 1。引入 lint 的提交 `be402c7` 未触碰该文件 |
| D1-3 | **三个记录表面宣称的门回归测试「钉子」根本不存在** | `CHANGELOG.md:45`、`docs/PENDING-DECISIONS.md:50`、`plan/PLAN-QUALITY-001.md:29` 三处声称钉于 `SchemaSubsetFailClosedTests` + `MutationKillCorpusTests`；`grep -rn "SchemaSubsetFailClosed\|MutationKillCorpus" tests/ tools/` → **零命中**；实跑 `Ran 78 tests`。**门规则可被人悄悄改回去而门仍绿** |
| D1-4 | `validate.py` 未重导出 `version_prose_errors`（CHANGELOG:45 声称重导出） | `grep -n "version_prose" tools/lab/validate.py` → 零命中；实现只在 `gate/docs.py:264`。CHANGELOG 下一条自承「本次未补」但**未回改第 45 行** |
| D1-5 | 五面分类在两份权威文档里互相矛盾 | `README.md:87-102`（schemas 属「契约与门」、docs 属「文档面」）vs `docs/design-decisions.md:21-24`（schemas 属「运行时面」、docs 属「实验室面」） |
| D1-6 | **`trend.py` 在现行树上崩溃**（受保护的、文档化的工具今天不可用） | `python3 tools/lab/trend.py` → `ValueError: reviews/agentflow-product-chain/review-2026-10-19-003.md: 评审记录缺少「## 发现摘要」小节`，exit 1。`validate.py all` **不含** trend 检查 → 门全绿而工具已死 |
| D1-7 | 版本标签 0.11.0 同时覆盖「已发布」与「未发布」两套内容 | `CHANGELOG.md:3` 是 `## 0.11.0 — 2026-10-14`；`:40` 是「## 待发布」节，`:49` 记中文化并「重新装出 0.11.0 快照」。已装 0.11.0 快照含 2026-10-20 内容，而 0.11.0 节不含「中文化/ruff/mypy/10×PASS」 |
| D1-8 | **模板面（20 份 .md）完全没有门** | `grep -rn "templates" tools/lab/gate/*.py tools/lab/*.py` → 零命中。`ISS-2026-10-10-issue模板教非契约形态` 已识别过「模板会漂移出契约」这一缺陷类别，修了单例但没装门 |
| D1-9 | `packaging/runtime/` 不在保护面内 | 候选改 `packaging/runtime/agents/reviewer.md` → 进 `changed_paths` 不进 `blocked`（`validate.py manifests` 的字节比对作为第二道防线兜住） |

---

## 三、D2 门禁有效性（6/10，权重 ×2）

**锚点**：主体扎实，13 个变异实验里 9 个使门变红且报错精确；但仓内三项核心量化声明（51/51、95/96、`all` 全绿）经独立实跑证伪，而 R2 把这条差距解释为「语料里没有违规实例」而未计入硬伤，R8 据此建议从 7 下调至 6——**Supervisor 采纳 6**。

**逐项门表（声称 / 实测 / 失效模式 / fail-open|closed）**

| 门 | 声称守什么 | 实测 | 失效模式 | 判定 |
|---|---|---|---|---|
| `schemas` | 契约形状 + `$ref` 可解析 + **词汇表闭合**（`gate/schema.py:202-260,351-405`） | PASS exit 0 | **删 `required` 里一项不被发现**（M8 实测 PASS） | 部分开 |
| `examples` | 正例须过、反例须被拒、声明表与目录双向一致（`gate/examples.py:49-54`） | PASS exit 0 | 需改受保护面才能骗过 | 闭 |
| `artifacts` | 五个现行记录根逐份编译 | PASS exit 0 | `status` 降级不被拦（M2b）；`files:` 指绝对路径不被拦（M17） | 部分开 |
| `protected` | 清单覆盖 37 条必需条目且每条在盘（`gate/manifests.py:38-74`） | PASS exit 0 | 需改 `common.py`（受保护） | 闭 |
| `manifests` | 五份名字/版本 + 生成树逐字节新鲜 | PASS exit 0 | **删掉 `packaging/runtime` 即静默跳过**（`:133-134`） | 部分开 |
| `docs` | 角色/文档面 5 组断言 + 版本散文 + 断链/退役路径 | PASS exit 0 | **第 5 组断言不存在**；schema 路径存在性检查用 `[a-z0-9-]+` 正则，**大写文件名漏检**（M9 首版全绿） | 开 |
| `tests` | `tests/` 声明内容 + 回归套件 + `Ran N` 下限 + 禁 skip（`gate/checks.py:20-106`） | PASS exit 0 | 需改 `common.py:83` | 闭 |
| `doc_chain` | linter 判别自测 63 例 + 用例数下限 | PASS exit 0 | 自测规格可被改弱 | 闭 |
| `doc_chain_live` | 把 linter 指向 `docs/product/` + `docs/features/` | PASS exit 0 | `docs/product` 只跑 `--file`（C12/C13/C14），**C1–C11 从不在 product 链上执行** | 覆盖面窄 |
| `lint` | ruff + mypy 任何发现即失败，**缺工具也失败** | **FAIL exit 1** | CI 从不装 | 闭（配置漏） |
| `all` | 十项 | **9 PASS + 1 FAIL，exit 1** | — | 闭 |
| `installed` | 源码 vs 安装快照逐文件 SHA-256 | PASS exit 0 | 不在 `all` 内（设计如此） | 闭 |
| `isolation.py check-diff` | 候选 diff 不得触碰受保护前缀 | 见边界表 | `tools/lab/gate/__pycache__/*.pyc` **误判越界** | 闭（false-FAIL） |

**变异实验摘要（R2 私有副本 `/tmp/agentflows-eval-20724c0-r2`）**

| # | 变异 | 结果 |
|---|---|---|
| M1 | schema 加未实现关键字（6 个变体） | **红**（exit 1，逐字点名 `unsupported keyword '…': the subset validator would silently skip it`） |
| M1b | `additionalProperties: true` | **红** |
| M1c | 从 `required` 删 `attribution` | **不红（exit 0）★ fail-open** |
| M2 | 真实 issue 改成非法状态（verified 缺 `## 审查`） | **红** |
| M2b | `verified` → `fixed-pending-review` 降级 | **不红** |
| M3 | manifest 版本改错 | **红**（一次报出源面 + 快照面两处不一致） |
| M4a–f | 改/删受保护路径；清单删条目 / 加垃圾条目 / 删 `schemas/` | **全红** |
| M5 | 断链 / 退役路径（散文）/ 围栏内退役路径 / 版本字面量 / frontmatter name / `agentflow:<role>` 悬空 | **全红**（围栏豁免按设计生效） |
| M6 | 生成树漂移（内容不同 / 缺文件 / 多文件） | **全红** |
| M7 | 活 feature 目录只留 `.gitkeep` 的阶段 | **活面红**（`doc_chain_live` FAIL）；**自测仍 63/63 绿、`validate.py doc_chain` 仍 PASS**——「自测绿 ≠ 被检物没漂移」的实证 |
| M8 | 契约弱化端到端（删 required + 新增违规记录） | **不红**；唯一报错的是生成树字节比对（副作用，非契约检查） |

**fail-closed 边界表（`isolation.py check-diff`，干净克隆）**

| 场景 | 结果 | 判定 |
|---|---|---|
| base 以 `-` 开头 | `base revision must not start with '-'` exit 1 | 闭 |
| base 不解析 | exit 1 | 闭 |
| 检查器根 == 候选 / 嵌套 | exit 1 | 闭 |
| 未跟踪文件 / 已暂存 / 已跟踪未暂存 / 删除 | 进 `changed_paths`，exit 0 | 闭（列入不拦） |
| **中文路径（未跟踪）** | 正确解析，exit 0 | 闭（未误 C-quote） |
| **中文路径落在受保护前缀下** | `blocked` 含该路径，exit 1 | 闭 |
| 被 .gitignore 忽略的文件 | 进 `changed_paths`，exit 0 | 闭 |
| **改 `skills/agentflow/scripts/check-write-scope.sh`** | `blocked: []` **exit 0** | ★ **开**（执法器可被候选改写） |
| **改 `skills/agentflow/references/contracts.md`** | `blocked: []` **exit 0** | ★ **开** |
| `tools/lab/gate/__pycache__/*.pyc` | **blocked 13–14 条，exit 1** | ★ **false-FAIL** |

**硬伤**
- **H1 ★★★｜CI 必然红**：第 10 项 `lint` 进入 `all`，CI 从不安装 ruff/mypy。CI 等价复现（干净克隆 + 受信检查器根）→ 第 2 步 `validate.py all` exit 1。
- **H2 ★★★｜「九项」跨活文档面的系统性漂移**：实测至少 **28 行 / 13 个文件**仍写「九项/9 项/9/9/9×PASS」（`README.md:51,69`、`AGENTS.md:19`、`docs/product/spec/method-spec.md:108`、`docs/PENDING-DECISIONS.md:20,50`、`docs/releases/pending-test.md:12,16,17`、质量提升批次 6 个文件 11 行、09-19 批次 2 个 plan 5 行、`reviews/agentflow-product-chain/review-2026-10-19-003.md:27`）；另 21 行在 gitignored 的 `.workbuddy/memory/`、20 行在历史 issue 记录（按硬边界 8 保留不改）。**`AGENTS.md` 是每个 agent 的会话级输入文件，它说的「共九项」会系统性误导所有后续 agent。**
- **H3 ★★★｜`check-diff` 对 `__pycache__/*.pyc` 误判越界**：与 `tools/lab/README.md:42-43`「会被列出，但不被阻塞」直接矛盾；而 `protected-paths.txt:26-35` 恰好为 `tests/` 解决过同类问题（逐文件保护，理由原文「一个让诚实工作失败的门会招致绕过」），**但同一解法没套用到 2026-10-19 新增的 `tools/lab/gate/` 宽前缀上**。候选**因为诚实地跑了门**而被判越界。
- **H4 ★★｜`validate.py docs` 第 5 组断言是幽灵**：docstring、`tools/lab/README.md:47-48`、`AGENTS.md:24-29` 三处声称「中文镜像与英文契约文档保持段落对应」/「schema 引用集合相匹配」；代码里不存在。R4 独立复现：contracts.md 引用 3 个 schema / 全面 6 个 / 差集 3 个，`validate.py docs` 仍 PASS exit 0。
- **H5 ★★｜`trend.py` 崩溃**（同上 D1-6）。
- **H6 ★★｜`record_store.py query` 对连字符词崩溃**——本仓核心术语 `fail-closed` 恰好中招：`query "fail-closed"` → `sqlite3.OperationalError: no such column: closed`，exit 1。`tests/test_record_store.py` 5 条用例**无一条含连字符**。
- **H7 ★★｜契约弱化面：schema `required` 列表的内容无人守**（M8）。
- **H8 ★★｜`skills/agentflow/` 完全不在受保护面**（执法器本身可被改写）。
- **H9 ★｜`mutate.py` 的变异规格漂移 2 条（M25/M48 锚点失效），且「存活」不导致非零退出；`--check schemas`/`--check protected` 等 5 个检查名分配 **0 个变异**却报绿 exit 0。
- **H10 ★｜`validate.py docs` 的 schema 路径正则 `[a-z0-9-]+` 漏检大写文件名**。

---

## 四、D3 代码质量与安全（7/10）

**锚点**：主体扎实（裸 `except` 0、`except Exception` 0、subprocess 全部 list 形式无 `shell=True`、NUL 分帧处理非 ASCII 路径、错误走结构化 `ValidationError` 值而非抛异常）；扣分来自 3 处**当前树上可复现**的缺陷与 3 处 schema 子集校验器的 fail-open。

**亮点**
- `gate/common.py:162-175` 把读失败转成结构化错误而非 traceback（`UnicodeDecodeError` 是 `ValueError` 不是 `OSError`——这条注释解释了**为什么**）。
- `tools/lab/isolation.py:100-106` 命令行参数注入显式堵死（`base.startswith("-")` 直接 raise）。
- `gate/common.py:313-319` + `:322-343` 路径穿越双向堵死，且 `files_entry_errors` 先拒绝对路径再判包含；负例已钉（`tests/test_lab_contracts.py:1240-1269`）。
- `validate.py:355-358` 不短路：所有检查项都跑完再汇总退出码。

**硬伤**
| # | 硬伤 | 触发条件 |
|---|---|---|
| D3-1 | **`trend.py` 崩溃**（D1-6 同源） | 任一 `review-*.md` 缺 `## 发现摘要`；且该节**没有任何门保证存在**（`schemas/review.schema.json` 的 required 不含它，`gate/records.py:207-262` 也不检查），而 `tests/test_lab_contracts.py:1418-1423` 把它**钉成了期望行为**——「工具正确、树违约、无人管」 |
| D3-2 | **`lint` 进门但 CI 无依赖** | 任何 CI 运行 |
| D3-3a | **布尔子 schema 静默移除该属性的全部约束** | schema 里出现 `"status": true` → `gate/schema.py:86-87` 直接 `return []`；实测 `{"status":123}` 零报错 |
| D3-3b | **拼错的 `type` 取值被静默接受** | `gate/common.py:295-310` `is_type` 未知类型名一律 `return True`；实测 `is_type('x','strng') = True`。**不一致**：`gate/schema.py:384-391` 对 `format` 的取值做了 fail-closed 校验，却不校验 `type` |
| D3-3c | **`$ref` 的兄弟关键字被忽略** | `gate/schema.py:91-97` 解析 `$ref` 后直接 `return errors`；实测 `{"$ref":…,"type":"integer"}` 对 `{"status":"open"}` 零报错 |
| D3-4 | **三处未捕获异常直接吐 traceback** | `record_store.py:78`（FTS5 语法错误）、`doc_chain.py:169-170`（非 UTF-8 文件）、`trend.py:76`。后果：「退出码 1」同时表示「发现违规」与「工具崩溃」，调用方无法区分 |
| D3-5 | **变异装置「无变异可跑」时静默成功，「存活」也不算失败** | `--check schemas/protected/manifests/docs/doc_chain_live` → 「总变异数 0 … EXIT 0」；`mutate.py:467` 只在「无效」时 return 1 |
| D3-6 | **`validate.ROOT` 重绑定只传播一半** | `SCHEMA_PATHS` 等派生常量在 import 时冻结 → `validate_schemas` 无法做进程内负例测试，且 `mutate.py` 给 `schemas` 分配 0 个变异 |
| D3-7 | **`check-write-scope.sh` 不计入 .gitignore 忽略的路径，比候选门覆盖面小** | `check-write-scope.sh:20`（自述「被忽略的文件不计入」）vs `isolation.py:113`（计入）。worker 把产物写进 `.agentflow-records.sqlite3`/`private-evals/` 即漏检 |
| D3-8 | 未来时间有 5 分钟宽限；`record_date_of` 比 `parse_rfc3339_date_time` 宽松（只到日期、无时区也被接受，且取偏移本地日而非 UTC 日） | 边界日期（跨时区午夜）误判 |

**tests 覆盖真相表（关键列）**：`validate_schemas`、`check_schema_keywords`、`validate_schema_shape`、`SUPPORTED_SCHEMA_KEYWORDS`、`iter_schema_paths`、`check_schema_refs`、`validate_installed`、`plugin_identity`、`validate_static_checks`（lint）、`counts.py` 全部、`mutate.py` 全部 —— **tests/ 引用次数全为 0**。**D3-1 与 D3-2 恰好落在这片 0 覆盖区。**

---

## 五、D4 代码工艺与可读性（6/10）

**锚点**：D4 细化锚点的 5–6 档两个触发条件**同时成立**——(a) 复制的规则/常量已现多处漂移风险；(b) 存在过期注释。故不能给 7–8。但死代码 **0**、TODO/FIXME **0**、注释绝大多数解释「为什么」、命名整体自解释、CLI 风格全域统一、无裸 except。

**整洁**
- 函数长度 Top5：`self_test()` 449 行（doc_chain.py:602）；`validate_workspace_artifacts()` 322 行（gate/workspace.py:41）；`lint()` 201 行（doc_chain.py:399）；`validate_test_run_markdown()` 160 行；`validate_plan_markdown()` 142 行。总体 271 个函数；>60 行 14 个；cc>15 22 个。
- **重复代码**：①「validator setup failed」同构 try/except **逐字 7 份**（`gate/plan.py:50`、`gate/records.py:48,137,222,273`、`gate/testing.py:109,198`）；② unittest 摘要解析 2 份（`gate/checks.py:78` 与 `trend.py:93`）；③ `env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}` 7 份；④**「路径必须留在仓库内」这条规则有两套并行实现**（`gate/common.py:313-319` 与 `gate/records.py:111-117`）——一处收紧另一处漏收紧就静默不一致。

**过期注释（3 条，全部逐条核实成立）**
1. `gate/examples.py:53-54`「Only bug-record and plan negatives exist today」——同文件 `:64` 就是第三族 `test-run` 负例。
2. `doc_chain.py:611-612`「cases 44–48 pin the C4/C8 applicability rule」——实测编号序列为 `01..34, 42, 43, 47..63`，**44/45/46 不存在**；且 42/43 被 C13 与 C1 各用一次（编号不唯一）。
3. `tools/lab/README.md:6`「可以…调用被显式隔离的宿主 runner」——同文件 `:3-5` 已自承装置裁撤。
附：`doc_chain.py:211-216` docstring 说链模式 label 是 repo-relative path，实际传的是 feature 相对路径 → **`C13_EXEMPT_FILES`（31 条）在链模式下永远不可能命中**（方向保守，多报不漏报）。
附：`validate.py:222`「`pip install -m`」——正确命令是 `pip install -r requirements-dev.txt`（且该句正好在 D3-2 的因果链上）。

**命名（抽样）**：样本量 **105 / 总体 354 / 23 文件**，按确定性步长每文件取 5。**96/105（91%）表意且与行为一致**；9 个偏弱：`is_type`（不说「JSON Schema 的 type」）、`resolved`、`is_within`（参数序未编码）、`c13_checked`（以检查编号而非语义命名，且返回值语义与字面直觉相反）、`_text`（返回三元组）、`report`（过度承载，与 `gate/reports.py` 的 `bug_report` 共用一词指三件事）、`--path`/`installed_path`（旗标名与内部名不一致）、`SEP_RE`/`ROLE_PHRASES`（缩写未成文）。**布尔命名不统一**：`is_type`/`is_within`/`is_separator_row` 有前缀，`lightweight`/`audit_found`/`matrix`/`closed`/`glossed` 没有。

**一致性**：错误处理模式**统一且优秀**（`ValidationError` 是普通类而非 Exception 子类，全仓不抛异常；唯一 typed 体系在 `mutate.py` 与 `doc_chain.py`）；返回结构两处例外（`validate_test_plan_markdown` 返回元组、`validate_installed` 用裸字符串状态枚举）；**CLI 入口签名 1 处不一致**（`record_store.main()` 无 `argv` 参数，其余 7 个工具均有）；`gate/manifests.py:137-140` 在函数内 `sys.path.insert` 后 `import build_runtime`，**永久改写 `sys.path`** 且 `packaging_dir` 硬编码为真仓路径。

**死代码**：**0**。零引用顶层函数 0 个；`if False`/`NotImplementedError`/TODO/FIXME/XXX/HACK 在 `tools/lab/` 与 `tests/` 内全部零命中；静态可达性闭包后剩余 11 个「不可达函数」全部是已知误报（经字典/模块级赋值引用）。裁撤后的残留只有**文档语句**（`tools/lab/README.md:6`）。

---

## 六、D5 Agent / Skill 契约质量（6/10）

**锚点**：指令层/角色层主体扎实（14/14 frontmatter `name` 与文件名一致；判断词可判定且优先级已裁决；四份 references 之间无实质矛盾），但**「契约→文件→门」这条链有两处系统性断裂**。

**亮点**
1. **判断词可判定且优先级已裁决**：`SKILL.md:68`「先判 risky work——命中任一条即触发架构门，**不再降级问「是否小改动」**」——这正是 2026-10-12 评测 G5 判为「未裁决」的那一条，现已闭合。「小改动」6 条款全析取可核；「相同原因」给出可执行的归一化签名。
2. **角色 frontmatter 与正文 14/14 强互证**：`test-executor.md:21`「`Edit` 被有意禁用：执行记录是仅追加的历史」↔ `disallowedTools: Edit` 是全仓最紧的一处。
3. **硬边界 7 的诚实自承**：`contracts.md:17`「这是**角色分离，不是环境隔离**…（这是产品决策，有意推迟）」——主动把「什么还没做到」写进契约。
4. **晋升规则四处逐字一致**：`improve/SKILL.md:39,55` + `evidence-and-release.md:132-154` + `release-record.schema.json` 的 `allOf` 分支。
5. **schema 主动消歧**：`bug-record.schema.json:58` 与 `episode.schema.json:253` 各自写明「同名的 `provenance` 是不同的字段…不可互换」。

**硬伤（高优先级：照指令产出必被自己的门拒）**
| # | 硬伤 | 复现（副本实测） |
|---|---|---|
| **HP1** | **测试角色的写范围与记录门互斥**：`test-executor.md:17` 明文授权写 `scratch/`；`test-records.md:11,12,23` 明文声明 `evidence/`/`scratch/`/`README.md` 落点且「`evidence/` 豁免」；`gate/workspace.py:251-268` 只认 `plan-<date>-<NNN>.md`/`run-<date>-<NNN>.md` | `FAIL artifacts (5 error(s))` + 5 条 `unexpected entry under testing/`。**旁证**：现行仓 7 个 testing 记录**从未出现过** `evidence/` 或 `scratch/` 目录——契约授权的落点一用就红 |
| **HP2** | **随附计划模板与本仓计划门不兼容（4 处）**：`templates/feature/plan/execution.md` 用 `## 0. 分支策略`/`## 3. 任务清单`/`## 6. 验证命令`、无 `## 进展概览`、无 frontmatter、任务表 9 列；而 `gate/plan.py:19-23` 要求 `## 进展概览`/`## 任务清单`/`## 验证命令` **精确行**、状态列读 `cells[5]` | 原样照抄 → 3 条 `body section … is required`；改标题后 → 2 条状态列错位；放成 `plan/execution.md` → `frontmatter block is missing`。**子发现**：同一张表两道门两种读法——`gate/doc_chain.py:362` 按**列名**读状态（模板通过），`gate/plan.py:107` 按**索引**读（模板被拒） |
| **HP3** | **改进环的候选记录与发布记录在仓内没有合法落点** | 五个落点逐个试放全部被 `artifacts` 拒（`docs/releases/` → 「per-version release records were retired」；`episodes/` → 18 条 episode schema 错误；`docs/features/` → 「unexpected entry in a feature batch」；`reviews/` → 「unexpected entry under reviews/」）；放到扫描范围外则门放行但**从未被编译过**。`validate.py --help` 列出 14 个目标，无一编译这两类记录。**方向相反的事实**：`episode.schema.json` 才是唯一被逐实例编译的改进契约（41 个 episode 全在门内），而 `improve/SKILL.md:38` 恰恰没把它算进「可编译的改进契约」 |
| **HP4** | `SKILL.md:45`「文件名 = review_id」与 schema 及全部现存记录矛盾 | schema 要求 `^REV-\d{8}-\d{3}$`，而文件名恒为 `review-<date>-<NNN>.md`；按字面改名 → `unexpected entry under reviews/` |
| **HP5** | `validate.py docs` 声称的「中文镜像」断言无实现 | 见 D2-H4（R2/R4 独立互证） |
| **HP6** | `measurement.basis` 的机器判据是字面量，与角色散文口径不等价 | 「Reviewed by agentflow:release-governor; …」被拒；「评审通过，证据 EP-…」（语义等价）被拒 |

**其他契约漂移**：`references/document-chain.md:130` 说 `## 分支策略` 是「固定标题字面量」，实为宽松正则（`gate/doc_chain.py:137`）；`agents/bug-recorder.md:23` 说四个标题「是校验器精确匹配的字面量」，但 `## 问题代码` 从不被检查；`references/contracts.md:145` 要求 `## 变更记录`（门不检查）；`references/contracts.md:5` 说「结果契约各只写一次，第二份副本即为缺陷」，而 `agents/reviewer.md:108-111` 重述了评审结果契约的 3 个字段。

---

## 七、D6 结构合理性（7/10）

**锚点**：落在「7–8 = 主体合理、个别目录职责模糊或路径偏深」的下沿。

**亮点**
1. **可发现性实测 5/5 达标**（全部 ≤2 跳，远低于 3 跳上限）：改角色 → `index.md:11` → `index.md:12` → `skills/agentflow/references/roles.md`（含路由表与工作链）；查缺陷 → `index.md:15` → `docs/issues/README.md`；抄模板 → `index.md:13` → `skills/agentflow/templates/README.md`；查批次 → `index.md:14` → `docs/features/README.md` → `plan/PLAN-QUALITY-001.md`；跑校验 → `index.md:21` → `tools/lab/README.md`。
2. **命名全域一致**（每个面内部有明文规则且被遵守）。
3. **无「为了结构而结构」**：零 `.gitkeep`；`examples/doc-chain/{good,bad}/` 是正反例对且由 `validate.py examples` 每次编译实跑。
4. **打包快照树与源码树的关系一眼可懂**（`packaging/README.md:3-4` + `build_runtime.py:24-53` 白名单 + `:131-142` 生成后自检 + `README.md:16` 用户视角）。
5. **文档面不寄生代码面**。

**硬伤**
| # | 硬伤 |
|---|---|
| D6-1 | **记录面 → 交付面：实测可证的硬依赖**。删除 `agents/plan-architect.md` 即让 `validate.py artifacts` 整批门红（`files entry … exists neither in this repository nor as a repo-qualified reference`）。13 条 issue 的 `files:` 指向 `agents/*.md`、45 条指向 `skills/`、22 条指向 `tools/lab/`。仓内已有 `<repo>@<revision>:<path>` 的正确解法，但**会移动的交付面路径没用它** |
| D6-2 | 面的分类无唯一定义（README vs design-decisions，见 D1-5） |
| D6-3 | `agents/` 无 README、14 个角色文件无索引；`index.md:11` 落到裸目录。**交付面是唯一没有入口说明的面**（README.md:83-85 列出的目录 README 清单里不含 `agents/` 与 `skills/`） |
| D6-4 | 模板是记录形态的**第三处**定义，且无门（见 D1-8） |
| D6-5 | **三处导航面给出互相矛盾的批次状态**：plan + CHANGELOG + `docs/releases/todo.md:14` 说「T01–T09 已闭」；`docs/features/README.md:28`、`feature-2026-10-13-质量提升/README.md:9,37,51,52,54,55` 说「待独立评审 / 待重装插件 / 未开始」；`index.md:32` 说「T08 阻塞在外部条件」。**文档链契约自称「README 是唯一入口」，而这个唯一入口恰是全套表面里最陈旧的一个** |
| D6-6 | `packaging/runtime/marketplace.json:8` 的 `source: "./packaging/runtime"` 是自指的坏指针（runtime 树内无 `packaging/` 子目录） |

**目录引用矩阵（实测）**

| 从\到 | F1 交付面 | F2 契约门 | F3 记录面 | F4 文档面 | F5 打包面 |
|---|---|---|---|---|---|
| F1 交付面 | – | 31 | 42 | 15 | 1 |
| F2 契约门 | 73 | – | 68 | 20 | 28 |
| F3 记录面 | **318** | **368** | – | 172 | 46 |
| F4 文档面 | 48 | 66 | 79 | – | 19 |
| F5 打包面 | 10 | 6 | 2 | 0 | – |

**硬依赖边判定**：F5→F1/F2（打包复制源面，正确）；F1↔F5 二元环（marketplace.json 既是 manifest 又是 runtime 入口指针，未被文档声明为环）；F2→F3/F1/F5（门在下游，正确）；**F3→F1/F2 是真实的门级反向耦合**（D6-1，实测存在）；F4→其余单向（正确）。

---

## 八、D7 逻辑链路（6/10）

**锚点**：落在「5–6 = 存在断环或死条款成群」的上沿。主工作流十步本身单独评可以给 8；拉低的是**三条链的出口普遍缺定义**、**5 条从未发生过的死条款**。

**亮点**
1. **主工作流十步首尾闭环**，每步输入/输出契约写明，含 FAIL 回退与有界修复环（`docs/system-guide.md:88-103`）。
2. **三条链的「不可省的一步」成文**（`skills/agentflow/references/roles.md:32-39` 的 6 行工作链表）。
3. **切换点有定义**：主链→文档链（`SKILL.md:55`）、主链→缺陷链（`system-guide.md:119` 的四个可观察触发）、主链→改进环（`SKILL.md:64` + `improve/SKILL.md:31`）。
4. **并行分支的汇合点在角色层有定义**（`roles.md:56` 「跨层功能 → Technical Director → 双工程师（可并行）→ **Reviewer**」；`SKILL.md:58`「并行只并行『写』，永远不并行『理解』」）。
5. **缺陷状态机在文本与记录上双向对齐**：`open → fixed-pending-review → verified/rejected`，且 `fixed-pending-review` **确实被走过**（`ISS-2026-09-14-claude-json-schema-被拒:87,95,99`、`ISS-2026-09-14-print模式计划写入被阻`、`ISS-2026-09-15-真树故障注入checkout还原丢工作`、`ISS-2026-09-15-未验证行为断言反复出现` 同批）。

**硬伤**
| # | 硬伤 |
|---|---|
| D7-1 | **主链的「有界修复环」在状态图上没有出口边**：`system-guide.md:99-101` 中 `K`（修复一轮）的唯一出边是回到 `J`（评审门）；若再次 `changes_requested`，图上是无限自环。散文有出口（`SKILL.md:82`「带证据上报阻塞」）但图没有 |
| D7-2 | **改进环 13 步的终端产物零实例且无落点**（见 HP3）；历史上**真的晋升过 2 次**（`EP-2026-09-22-001/002` 的 release-governor `approved` + `promote（human-gated）`），但发布记录已随三件套退役 → 这两次晋升目前**不可被机器校验** |
| D7-3 | **缺陷链没有回到主链的出口**；且 `system-guide.md:119` 把「评审发现」列为缺陷链入口，而 `SKILL.md:63` 第 9 步规定评审要求改动时走主链修复轮——**同源不同向，无优先级裁决** |
| D7-4 | **16 条 `open` 是吸收态**：全部 `provenance: external`、`project: infinite-canvas`、`recorded_at: 2026-09-19T14:21:06Z`、**28 天零推进**、全部缺 `updated_at`；修复对象在**另一个仓**，而「转交外部仓」不是一个状态 |
| D7-5 | **计划状态机没有终态**：`schemas/plan.schema.json:24-31` 只有 `draft/proposed/approved/superseded`，描述自承「approved = execution may be assigned」——**没有「已完成」态**；实测 4/4 计划全是 `proposed`，而三份已在执行 |
| D7-6 | **文档链的「Design 评审门」从未跑过（0 次）**：`docs/product/README.md:48`「☐ 技术方案评审通过」；因而门 4「Plan 前置条件：plan 引用**已冻结的** design 结论」的前提形式上不成立，而 `PLAN-PRODUCT-001` 已在执行并引用设计结论 |
| D7-7 | **再犯档位 `escalated`（改进环最强信号）0 次发生**（`improve/SKILL.md:31` 称它是「本环最强的信号」） |
| D7-8 | **批次内 `reviews/` 不受评审契约约束**——「每轮评审必须留逐字快照」这条规则在批次内形态上被整体跳过，而门确实不拦（`reviews/README.md:13-19` 已按用户选择 (b) 明写） |
| D7-9 | **计划看板回写纪律被遵守了，但「唯一入口」的 README 不跟着回写**——纪律只作用于 plan，**没有任何规则要求批次 README 随计划回写**（规则缺口，非执行失误） |

**死条款 vs 隐性惯例（两向差集）**
- **死条款（文本有、记录从未发生）**：`escalated` 档位；`rejected` 状态与 `docs/issues/归档/` 规则（0 条，目录不存在）；Design 评审门；`fixed-pending-review` 作为终态前置；改进环第 13 步 canary 监控；`automatic` 晋级模式。
- **隐性惯例（记录有、文本未定义）**：批次内评审留源文件路径而非快照（`review-2026-10-19-001.md:7-12` 自陈）；批次 README 进度不随 plan 回写；`project` 词表两种拼写（`agentflow` 27 / `agentflows` 7）。

---

## 九、D8 文档与记录活性（7/10）

**锚点**：主流记录**真实且在更新**——56 条 issue、9 本再犯台账、41 条 episode、3 份对外评审、4 份计划、28 例角色边界测试记录；`validate.py docs` 实跑 PASS。扣分是 2026-10-20 那批工作落地时**看板/待决/索引/指南四类同步面集体未回写**，加上文档门存在**可复现的盲点并漏掉一条真实断链**。

**链接**
- 门：`validate.py docs` → `PASS docs` exit 0。
- 独立扫描（196 个 `.md`，**比门更严**：保留内联代码与全部围栏块）：152 个相对链接目标 → **1 条断链**：`CHANGELOG.md:1161` → `docs/iteration-log.md`（目标已随 2026-10-12 瘦身批删除，`test -e` exit 1）。
- **门看不见它的机制**：`gate/docs.py:98` 的 `INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")` 中 `[^`]*` **允许跨行**；CHANGELOG 内反引号配对错位后，一个「内联代码」跨段把该链接整段吞掉。按门自身算法复现：CHANGELOG 的 **4 条相对链接全部对门不可见**（`lost = ['docs/iteration-log.md','protected-paths.txt','protected-paths.txt','AGENTS.md']`）。
- 逐条 `test -e` 抽查 19 条：**18 条可解析**，1 条断链如上。
- 退役路径散文：独立扫描得 64 处内联代码含退役路径 token，其中 `docs/product/proposal/proposal.md:11` 与 `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-PRODUCT-001.md:98` 指向已删的 `docs/iteration-log.md`（其余为 issue 记录里的历史引文，合规）。

**矛盾清单（同一事实两种说法）**
1. **单测数量**：说 A `episodes/2026-10-19/EP-2026-10-19-001.json:71,108`「unittest 95 OK」「78→95」；说 B 实跑 `Ran 78 tests`；说 B' `docs/trend.jsonl:3`「unittest_count: 95」；说 C `docs/releases/pending-test.md:16`「unittest 96 OK」。**该数字散布在 24 个文件**（含 18 份 issue 的 `## 审查` 段、CHANGELOG、PENDING-DECISIONS、pending-test、1 份 episode）。`git log --all -S "SchemaSubsetFailClosedTests" -- tests/` **全历史零命中** → **95/96 从未进入被提交的历史树**。
2. **变更行数**：`reviews/review-2026-10-19-002.md:6` frontmatter 已更正为 7758，`:28` 正文仍写「13267 行」——更正只落到 frontmatter。
3. **门项数**：见 D2-H2。
4. **回归状态**：`docs/issues/ISS-2026-09-20-先写契约后核实平台约定:5` frontmatter `regression_status: pass` vs `:45` 正文「regression_status=not-run」——**14 条 issue 同时带两种说法**（ISS-003/007/008/009/030/031/032/033/034/035/036/037/038/039）。
5. **Q-01~Q-04 拍板状态**：`docs/PENDING-DECISIONS.md:28` 记「已落」vs 5 份分析文档首行仍写「状态：待用户拍板」。
6. **重装/安装态**：`PLAN-PRODUCT-001.md:100` T06「◐ 进行中…需用户刷新 marketplace 并重装」vs `PLAN-QUALITY-001.md:32` T08「☑ 已完成…拷贝进缓存（**等价于 marketplace 重装**）」vs 实跑 `validate.py installed` PASS。

**index.md 同步对账**：`docs/issues/`、`docs/features/`、`docs/releases/`、`episodes/`、`reviews/`、`agents` 计数均一致；但 **`requirements-dev.txt`（2026-10-20 新增顶层文件）既不在 `index.md` 也不在 `README.md`**；`lint` 第 10 个门未登记；`index.md:32` 的 T08 状态已过时；`index.md` 无任何 2026-10-20 条目（当天 6 个提交全部未登记）。

**状态流统计**

```
$ validate.py report | wc -l                       → 56
$ status 分布                                        → verified 40 / open 16
$ provenance 分布                                    → agentflow 40 / external 16
$ grep -c "^status: fixed-pending-review"           → 0
$ grep -c "^status: rejected"                       → 0
$ test -d docs/issues/归档                            → EXIT 1（目录不存在）
$ grep -l "^class_id:" docs/issues/ISS-*.md | wc -l  → 20
$ validate.py recurrence                             → 9 类；recurred 5 / single 4 / escalated 0
```
计划看板算术 **4/4 自洽**（逐行数表与「进展概览」完全对得上）；但**回写纪律只落实在 plan 层**：批次 README 11 处过时状态、`PENDING-DECISIONS` 0 条 2026-10-20 记录、`index.md` 未登记。`docs/product/README.md:48` 的技术方案评审门从未跑且**不在 PENDING-DECISIONS**。

---

## 十、D9 治理与发布闭环（6/10）

**锚点**：站在「5–6 系统性差距」与「7–8 主体扎实」的边界。

**亮点**
1. **`measurement: none` 口径在记录面零污染**：41 episode 全扫，26 条 measurement 信号全为 `none` 族，**0 例**同时声称 `none` 与 `better`；两条真实 promote 决策都明写「measurement:none 如实」。
2. **「发布 = 人工批准」被结构性锁住**：`automatic` 分支要求 `evaluation_result: better`，而 `better` 在 `none` 下被禁 → **自动晋级当前不可达**（实测 14 组正负例）；全仓无任何发布脚本。
3. **五份 manifest 三层机器强制**：名字/版本一致 + 生成树逐字节 + 已装快照逐字节。
4. **裁撤干净**：`tools/lab/`、`tests/`、`schemas/`、`examples/` 零死代码；活面残留全部带「已裁撤/已失对象/恢复清单」限定；设计知识完整留存于 `docs/design-decisions.md` §3。
5. **受保护面是机器级的**：副本上改写 `release-record.schema.json` → `check-diff` blocked、exit 1。
6. **拍板台账真实**：2 条未决、每条带证据与推荐默认、拍板后移出并留痕。

**硬伤**
| # | 硬伤 | 解锁路径 |
|---|---|---|
| H1 | **晋升规则没有编译器**：candidate/release 两份 schema 从未被实例化；**删掉「`none` 下禁 `better`」的整条 `allOf` 分支后 `validate.py schemas` 仍 PASS exit 0**；`required` 削成 `["schema_version"]` 也 PASS；`tests/` 中 `measurement\|promote\|basis\|release-record` **零命中** | 加 `validate.py improvement` 目标 + 一正一负 fixture + 3 条 `allOf` 语义断言 |
| H2 | **`validate.py all` 在干净检出里 exit 1**（lint 缺依赖），README:56 只披露 `tests` 子项假红、未披露 lint 的同类风险 | README 补披露 + CI 装依赖 |
| H3 | **CI 必然红**（workflow 无 pip 步骤） | workflow 加 `pip install -r requirements-dev.txt` |
| H4 | **`check-diff` 的 `.pyc` 误判面**（与 D2-H3 同源） | isolation 排除 `__pycache__` |
| H5 | **趋势装置已死**（D1-6 同源） | 把「发现摘要」纳入评审契约，或让 trend.py 跳过并记 null |
| H6 | **趋势数据陈旧**：`docs/trend.jsonl` 仅 3 行，末行 `revision: f76094a`（HEAD 是 `20724c0`）、`unittest_count: 95` | 修 H5 后重录 |
| H7 | **活治理面把门自己的项数写错**（至少 28 行 / 13 文件，见 D2-H2）+ 测试数写错（PENDING-DECISIONS:50「95 测试 OK」） | 统一文案；`counts.py` 可加门项数标记使其被机器守 |
| H8 | **发布产物版本标签与内容错位**：已装 0.11.0 快照含 2026-10-20 中文化内容，CHANGELOG 的 0.11.0 节是 2026-10-14 的内容 | bump 到 0.12.0 并同步五份 manifest + 快照 |
| H9 | **缺陷统计口径不可靠**：`report --project agentflow` 只回 27 行，漏掉 7 条本仓自己 `project: agentflows` 的记录（ISS-001/002/003/005/006/028/029）；任何过滤下退出码恒 0 且空结果不提示 | 统一 project 取值；空结果提示 |
| H10 | **`tools/lab/README.md:6` 陈述了不存在的 runner 能力**；`improve/SKILL.md` 第 13 步 canary 监控在现行装置下无对象 | 改写为「（若恢复）」/ 给步骤加「当前无对象」限定 |
| H11 | **发布状态三方不一致**：todo.md「收尾中」/ 批次 README「状态：草案，未经独立评审」/ CHANGELOG「T01–T09 全闭」；`pending-test.md` 保留 6 条已验证行（违反自身「只记录仍待验收」规则） | 同步三处状态 |
| H12 | **`validate.py` 未重导出 `version_prose_errors` / `check_schema_keywords` / `SUPPORTED_SCHEMA_KEYWORDS`**，而 CHANGELOG 声称重导出 | 补导出或删掉该条 CHANGELOG 声称 |

**角色分离强制力评级**：**部分机器级（混合）**。保护区层 = 机器级（已实测拦截）；工具层 = 机器级但**只在 ZCode 一个宿主被观察**（`docs/host-platform-facts.md:14` Z4；WorkBuddy 上未观察到，W2）；路径/工作区层 = **纯提示词**（C7、README:38 自承宿主不对 Write 强制路径约束）；身份层 = 纯提示词；批准层 = 纯提示词（schema 只要求「一条带 `evidence_ref` 的 approved」，actor 是自由文本，agent 身份即可满足）。**「角色分离只是流程性的」那句仍然成立**——其豁免条件是「工具白名单**与**工作区」的合取，而工作区在任何宿主上都没被强制。

---

## 十一、D10 安全与权限边界（7/10）

**锚点**：硬边界 14 条逐条对账做得扎实；扣分来自执法器自身的保护缺失与路径作用域的全提示词化。

- **`write_scope` 是提示词级 + 半机械级**：`check-write-scope.sh` 是路径差异审计（机械），但它是 **Supervisor 手工调用的脚本**，不在 CI、不在 `all`、**不在受保护面**；宿主本身不强制 Write 路径（README:38 自承）。
- **残余风险**：worker 把产物写进 `.gitignore` 忽略的路径时，`check-write-scope.sh` **不计入**（`:20` 自述 + `:52` 用 `git ls-files --others --exclude-standard`），而 `isolation.py:113` **计入** —— 两个工具口径不一致，脚本覆盖面比候选门小（`.agentflow-records.sqlite3`/`private-evals/`/`.zcode/` 都在 ignore 列表里）。
- **非 ASCII 路径**：ISS-2026-10-10-写范围dot-scope静默不匹配 的中文路径误 FAIL **已根治**（5 组用例全对，退出码与匹配语义正确）；`isolation.py` 用 NUL 分帧，中文路径既不被 C-quote 误伤、也不漏拦。
- **凭据纪律**：`agents/test-executor.md:52`「`credentials`（注入方式，绝不是值）」与 `test-records.md` 一致；文档与工具口径一致。
- **候选隔离**：`isolation.py` 要求调用方指定 `--checker-root` 且拒绝与候选重叠/嵌套（实测 exit 1）——「检查器根由调用方指定，不由 check-diff 自行证明可信」（`tools/lab/README.md:88-89`）。
- **fail-open 面全集**：① schema `required` 内容无人守；② `skills/agentflow/` 不在保护面（执法器可被改写）；③ `packaging/runtime` 缺席即跳过新鲜度检查；④ `validate.py docs` 第 5 组断言不存在；⑤ 布尔子 schema / 未知 `type` / `$ref` 兄弟键三处子集校验器 fail-open；⑥ `mutate.py` 「存活」不导致非零退出；⑦ `mutate.py --check <无变异项>` 报绿；⑧ `docs.py` schema 路径正则漏检大写文件名；⑨ `check-write-scope.sh` 不计 ignore 路径；⑩ `validate.py report` 过滤恒 exit 0 且空结果不提示。

---

## 十二、D11 实现的效果（6/10）

**锚点**：记录面**有真实疗效**（40 条 agentflow 侧 issue 全部走完 `verified`、42 轮独立评审且 50% 打回、28 例角色边界 ×2 零写入核验、对外部仓真实评审出 16 条缺陷、4 份计划的看板算术自洽）——**不是仪式**；但**最关键的三项量化疗效指标不可复现或注水**，且旗舰效果实验 **G1 只有样本量 1**，改进环**候选产出为 0**。

| 指标 | 数值 | 抽查核对 | 结论 |
|---|---|---|---|
| 走完全流程的 issue 数与占比 | 56 中 40 verified = 71.4%；agentflow 侧 40 条 **100% verified** | 抽 `ISS-2026-10-14-复发台账计数与再犯事实矛盾`：reviewer / review_decision / closure_criteria 齐备，实跑 `validate.py recurrence` 命中 `unverified-behavior-claims consolidated 0.8.4 2 0 recurred` | ✅ |
| 16 条 `open` 是否停滞 | 全部 external、2026-09-19 同批、28 天无推进 | 抽 `reviews/infinite-canvas-office-agent-plan/review-2026-09-19-001.md:10-26` 逐条点名 ISS-010~025，`:57` 留有实测证伪 | ⚠️ 设计内，但「open→verified」对外部来源**从未被验证过** |
| episode 实质率 | `review_roundtrips` 非空 19/41 = 46.3%；42 轮（approved 21 / changes_requested 21 = **50% 拒绝率**）；claims 带 `evidence_ref` 126/132 = 95.5%；signals 带 `evidence_ref` 111/179 = 62.0% | 抽 `EP-2026-09-21-001` 第 22 轮 finding 指到任务表「T02/T03 依赖 T02」字面自引用；抽 `EP-2026-09-20-002`：6 条 claim 全 `verified` 而 `evidence_ref` 全 None | ⚠️ 部分成立 |
| 计划完成率与回写纪律 | 完成率真实（9☑+1— / 3☑+1— / 6☑2◐1☐3— / 5☑1☐3—）；**回写纪律：plan ✓ / 批次 README ✗ / PENDING-DECISIONS ✗ / index.md ✗** | 抽 `PLAN-QUALITY-001.md:16`「9 项已完成」与逐行计数一致 | ⚠️ 计划内自洽、跨文件断裂 |
| 再犯台账 | 9 类 / 20 occurrence / recurred 5 · single 4 · escalated 0；`grep -l "^class_id:"` = 20 = 20 | ISS-055 自承矛盾**已真实修复**并留维护注记 | ✅ 一致 |
| **台账仍漏登的 2 处自承再犯** | `ISS-2026-09-20-先写契约后核实平台约定:37`（同型复发 ISS-2026-09-19-office计划未验证SDK假设无spike）与 `ISS-2026-09-21-文档链陈旧前向引用无收口:29`（spec 轮已抓到、本次原样复发）均**不带 `class_id`** | 档位机制看不见 | ❌ 台账与再犯事实仍不同源（ISS-2026-10-14-复发台账计数与再犯事实矛盾 同根因，其修复未覆盖这两处） |
| 门禁拦截史 | 至少 11 起「门红后被修」（ISS-054/053/041/026/039/038/055 + C6 收紧 + 保护面补齐 + 反证实验 A–C + 外部评审 16 findings） | 逐条读原文 | ✅ |
| 改进环产出 | **候选 0 条、发布记录 0 条**；`candidates/`/`evaluations/`/`improvements/` 目录全不存在 | `find . -name "candidate*.json"` 只命中 schema；`ls docs/releases/` = 2 个 `.md` | ⚠️ 契约在、**产出为 0**，且记录面**未把「改进环从未产出候选」作为事实登记** |
| 用户反馈闭环 | 链路 A（ISS-2026-09-22-会话交付物术语范围缺口）完整：反馈→记录→改动→独立复审→归纳台账，且留下「为什么不并入另一类」的判据推理；链路 B（EP-2026-10-19-001）在「验证→回写」段断开；链路 C（反馈分析师 TC-FEEDBACK-ANALYST-01）核实简报声称的 `session-artifact` provenance 根本不存在并拒绝合并 | 逐条读原文 | ✅ |

**旗舰实验 G1**：`run-2026-10-19-003.md:14` `decision: partial`；`:21`「T1 只有一次重复，**结论不得用于「有提升 / 无提升」**」；`:44-45`「**不构成 G1 结论**」——**诚实但无疗效**。

---

## 十三、D12 存在意义（7/10）

**锚点**：7–8 =「有价值但某类场景成本倒挂」。不给 8 的原因：**头条差异化主张（确定性门 + 记录即编译）在用户手上不存在**——门只存在于本仓（发货树 60 文件，`find -name validate.py` 为空，19 处 `tools/lab/...` 引用指向不存在的命令）。不给 6 的原因：随发货的部分（写范围审计脚本、硬边界、独立评审门、claims 台账、6 份 schema）**在竞品里确实找不到等价物**，且有 40 条实证记录支撑。

**场景对照**

| 场景 | 有 agentflow | 裸用宿主 agent | 具体损失 |
|---|---|---|---|
| **A. 跨层 feature**（后端 API 形状变更 + 前端同步改） | Init → 文档交付链（proposal/spec/design/plan，各阶段阻塞清单）→ TD 划边界 → 双工程师并行 → 集成 → 对真实文件跑确定性检查 → 独立 Reviewer → episode 落盘 | 一个会话里说「把 X 改成 Y 并更新前端」→ 改代码 → 自测 → 说完成 | **异常分支整体消失**。仓内 16 条 external 记录逐条点名裸用产出计划会漏什么：ISS-010（无异常矩阵）、ISS-013（缺关键路径分步时序表）、ISS-019（可观测性缺失）、ISS-020（发布顺序×回滚点缺失且两个声明互相矛盾）、ISS-023（三处验收断言不可判定）。**这 16 条记录就是「有它 vs 无它」差额的实测量化清单** |
| **B. 反复出现的缺陷** | Investigator→Fixer→Reviewer→Recorder，Recorder 归 `class_id`+`occurrence`，档位**由事实推导** | 修完就完了，下次再犯没人记得是不是同一回事 | 「这已经是第三次了」这个判断从凭感觉变成从计数读出。ISS-006（以推演代替最小实验的行为断言反复被证伪）、ISS-041（`check-write-scope.sh` 的 `.` 全树范围静默失配——**本仓自己的机器工具出的错，由独立评审门抓出**）、ISS-055（**台账自己也会说谎**，而门能抓住它） |
| **C. 宿主插件快照漂移** | `validate.py installed` 逐文件比对源码 vs 安装快照 | 改完 `agents/reviewer.md` 就以为评审门生效了，实际宿主跑的还是旧快照——**评审门形同虚设，而且你不会知道** | 但这条**恰恰不随插件发货**，价值只对本仓维护者成立 |

**成本清点**

| 维度 | 数量 |
|---|---|
| 角色参与（"开会"） | **6–9 次**，其中 5–7 次是独立子会话 |
| 记录文件 | **8–15 个**（链文档 5–7 + testing 2–4 + review 1 + archive 快照 N + issue 0–1 + episode 1） |
| 确定性检查命令 | **6 条以上** |
| `validate.py all` 一条覆盖 | 10 顶层检查 + **78** 个单测 + **63** 个 doc_chain 自测用例 + 31 个活面 md 扫描 |
| 方法面上下文成本 | **45,414 字符**（SKILL 10,812 + contracts 10,196 + roles 8,205 + document-chain 13,164 + test-records 3,037） |
| 全角色库 | **56,245 字符 / 14 个角色文件**（14 条 description 合计 1,049 字符，Claude Code 上限 15,000 token，余量充足） |
| **本仓实测记录速率** | 56 条 issue / 31 天 ≈ **1.8 条/天** |
| **记录面 vs 门工具面** | 记录面 **151 文件 / 14,066 行 / 923,771 字符** vs 门工具 **7,493 行 / 349,372 字符** → 记录比编译器大 **1.9 倍（行）/ 2.6 倍（字符）** |

**该用 / 不该用**
- **该用**：单人/小团队 + 跨层 AI 协作 + **已踩过 AI 事故**的仓库（40 条 verified issue 就是这份事故清单的定价：ISS-005 故障注入在真实仓做、`git checkout`「恢复」静默重置了文件；ISS-007 push 被拒后擅自集成远端；ISS-008 同分支被两个执行者并发写入；ISS-009 凭会话记忆回答「现在有什么高优任务」）。
- **不该用**：一次性脚本 / 纯调研 / 只改一个文件的样式；**只改一个文件但改动落在共享横切机制上**（ISS-004 axios 401 拦截器打断忘记密码流程是原型）；**已经在用 spec-kit / BMAD / superpowers 的仓库**（两套流程并行会产生两套记录与两套「谁是作者」判定）；**仓库没有自己的构建/测试/lint 命令**（`SKILL.md:61` 第 7 步要求「对实际文件跑仓库的确定性检查」，没有检查就没有接受依据，整条链退化为仪式）；单人 + 小仓 + 无跨层改动。
- **划线评估**：方向正确且可判定，**强于所有竞品**（superpowers 的 brainstorming 是无条件触发；BMAD 按 story 数选轨；spec-kit 由用户选 short/full path——**agentflow 是唯一把「跳过」写成可核对 6 条款判定表的**）。但有 3 处漏洞：①`docs/quickstart.md:9`「小改动直接改，不走流程」与 `SKILL.md:70`「不论小还是 material，独立评审门强制不可豁免（硬边界 1）」**互相矛盾**——按 quickstart 走仍要起独立 Reviewer 子会话，而 quickstart 是新用户第一份读物；②frontmatter description「琐碎单步工作可跳过」没说清跳过的是「角色委派」还是「整条流程含评审门」，宿主路由两个方向都可能错；③quickstart 规则 1 的措辞**没提「不触碰共享横切机制」**（SKILL 层有），读者会按前两条判。

**砍掉什么反而更好（7 条）**
1. **整个 `skills/improve` 执行面 + 4 个治理角色降级为 `design-decisions.md §3` 的设计知识** —— 回收 **30,392 字符**（skill 面的 67%），减 4 个角色文件与 3 份 schema。依据：0 条候选/发布实例、`improve/SKILL.md:53` 自承「当前没有任何自动回归度量」、`escalated_classes` 恒为 0。**改进的真实来源是「issue 记录 + 人工复审」（40 条 verified），不是这个环。**
2. **16 条 `provenance: external` 开放记录迁出**到独立的评审桥归档 —— 16 个文件约 100 KB；其价值已被 `recurrence/external-plan-missing-failure-branches.md`（8 次 occurrence）吸收；混在自我治理记录里稀释了「agentflow 自己的问题」信号。
3. **把 `lint` 从 `all` 拆出去**（或 CI 装依赖）—— 修掉「`all` 全绿这句话当前为假」这个事实。
4. **所有手写的「九项」改为机器自报**（`validate.py --list`），其余引用自报值 —— 消除一整类漂移。
5. **收窄 `protected-paths.txt` 的 37 条必需条目**：把 `gate/reports.py`、`gate/manifests.py` 这类报告/展示/打包一致性模块移出「评判候选」的必保集 —— 降低门变更的人审频次。
6. **`references/document-chain.md`（13,164 字符，占 skill 面 29%）从「必读」降为「按需加载」**。
7. **`references/test-records.md`（3,037 字符）同样按需加载**。
> 砍 1+2+6+7 的合计：指令面 −19%、skill 方法面 −30%、记录面 151→约 130 文件，**同时不损失任何一项已被实证过的能力**。
> **反向建议（要加的）**：把 `tools/lab/` 拆成**可独立安装的 `agentflow-gate` 工具**——这是当前最大的未兑现资产。

---

## 十四、D13 竞品比对（7/10）

**锚点**：覆盖了任务书要求的全部 5 家（superpowers / BMAD-METHOD / spec-kit / Claude Code subagents / Codex AGENTS.md）+ 3 家形态对照（CrewAI / LangGraph / OpenHands）；23 条来源均带 URL + 检索日期 2026-10-20。扣分：**没有读竞品源码**（GitHub API 限流 403），「竞品没有机器级门」是从官方文档描述推出的推断。

| 竞品 | 形态 | 角色·流程机制 | 确定性强制力 | 自迭代·治理 | 记录与审计 | 上手成本 | 与 agentflow 重叠度 |
|---|---|---|---|---|---|---|---|
| **superpowers**（301,721★，MIT，创建 2025-10-09） | 宿主插件 + 20+ 技能库，可装 15+ 宿主 | 7 步工作流（brainstorming → worktrees → writing-plans → subagent-driven-development/executing-plans → TDD → requesting-code-review → finishing-a-branch）；**技能自动触发**（「Mandatory workflows, not suggestions」） | **提示词级为主**。`tests/claude-code/` 用 `claude -p` 断言技能文本被遵守——**测的是提示词一致性，不是门能否抓住违规**；无制品 schema 编译器 | 有 `writing-skills` 元技能；**无候选/基线对照、无发布治理** | 计划文档 + worktree；无跨会话记录契约 | **低**（装插件即用） | **中–高**。重叠：头脑风暴门、计划→任务→子代理→评审两阶段、TDD、worktree 并行。**不重叠**：写范围审计、缺陷记录 schema、再犯台账、改进环发布治理 |
| **BMAD-METHOD**（54,329★，创建 2025-04-13） | 独立方法模块 + **12+ 人格化 agent**（Analyst/Mary、PM/John、Architect/Winston、Dev/Amelia、UX/Sally、TechWriter/Paige） | 四阶段 34+ workflow；按 story 数分三轨（Quick 1-15 / Method 10-50+ / Enterprise 30+） | **提示词级**。`bmad-check-implementation-readiness` 输出 PASS/CONCERNS/FAIL——**是模型判的，不是机器判的** | 有 `bmad-correct-course`、`bmad-retrospective`；**无候选/基线对照** | PRD/architecture/epic+story/sprint-status；**无 schema 契约、无编译门** | **中** | **高**。重叠：多角色分工、PRD→架构→story→实现、独立 code-review 门、复盘沉淀 |
| **spec-kit**（GitHub 官方） | **独立 CLI**（`specify-cli`，PyPI，需 uv）+ `.specify/` 模板栈 + `specs/<feature>/` 产物 | constitution → specify → clarify → plan → tasks → analyze → implement → converge；三个可选质量门 | **提示词级为主 + 一层真机器门**（`specify bundle validate --path`、`check-prerequisites.sh`、模板栈运行时解析） | **本矩阵最强**：extensions / presets / bundles / workflow YAML 引擎，extension hook 可挂 `after_tasks` 等事件 | constitution/spec/plan/tasks/checklists；**制品无 schema 编译器**（bundle validate 只校验 bundle 本身） | **中** | **高**。重叠：文档链四段式（≈ specify→plan→tasks→implement）、澄清门、一致性分析门、模板体系 |
| **Claude Code subagents**（宿主特性） | 宿主内建 `.claude/agents/` / 插件 `agents/` | 按 `description` 自动委派；每 subagent 独立 context | **混合，宿主侧机器级**：`tools`/`disallowedTools` 白名单、`Agent(agent_type)` 限制派生类型、**`isolation: worktree`（宿主强制工作目录隔离）**、**`maxTurns`（超限返回 partial）**、`permissions.deny`、hooks | 无 | 会话与 agent 历史；无跨会话记录契约 | **零** | **中**。重叠：14 角色 + frontmatter 白名单（**直接复用宿主机制**）。**关键差异**：宿主**不强制 Write 路径**，agentflow 用 `check-write-scope.sh` 补上——**这是宿主没有、agentflow 有的** |
| **Codex AGENTS.md 约定** | 纯约定，零工具 | 无角色无流程；按 `AGENTS.override.md` → `AGENTS.md` → fallback 顺序拼接 | **纯提示词级**。唯一机器面是 `project_doc_max_bytes`（默认 32 KiB）与目录覆盖规则 | 无 | 无（AGENTS.md 是活的文档） | **零**（`/init` 自动生成） | **低**。重叠：Init 节本质是「把约定写进目标仓 AGENTS.md」，**是同一手法的产品化版本** |
| **CrewAI / LangGraph / OpenHands** | 独立框架 / 图运行时 / 沙箱自主 agent | 角色化 crew / 显式状态图 / 自主执行循环 | **机器级（框架或沙箱侧）** | 有 | 轨迹 / checkpointer | **高** | **低**（形态不同） |
| **agentflow（本仓）** | 宿主插件：14 角色 + 2 Skill + 6 schema + 5 manifest + 1 脚本（发货 60 文件 / 404K） | 十步主工作流 + bug 四链 + 文档链 + 13 步改进环 + 3 个可判定判断词 | **混合**：宿主强制 `tools`/`disallowedTools`/`maxTurns`；本仓自建 `validate.py`（10 项）、`isolation.py`、`check-write-scope.sh`、`doc_chain.py`（C1–C14，63 例自测）、51 个变异算子。**但门不进发货树** | 改进环存在但**无机器测量面**，实测 0 条候选/发布记录 | **本仓最强**：151 文件 / 14,066 行 / 923,771 字符；6 份 schema + 9 本再犯类台账 + 41 条 episode（`review_roundtrips` 必填） | **高** | — |

**真实空白创新点**（公开事实 + 本仓实证对表）
1. **声明式写范围的机器审计**（唯一随发货）——竞品给的是**围栏**（能力集 / 目录隔离），agentflow 给的是**声明范围的差异审计**。
2. **「agent 不得编辑评判自己的门」这一威胁模型的机器表达**——五家竞品**没有一家**把「评估器 / 发布策略 / 评分 schema 对实现者不可见」建模成机器可检的面。**诚实边界**：`contracts.md:17` 自承这是「角色分离，不是环境隔离」。（**注**：此论断在 R7 的证据等级上属推断——未读竞品源码；且本仓这一面本身有缺口，见 D2-H8。）
3. **门工具自身的变异测试作为一等公民**——spec-kit 的 pytest 矩阵测的是 CLI 自身行为、superpowers 的 `tests/claude-code/` 测的是技能文本被不被遵守；**「问这个检查器能不能抓住违规」本身被做成可执行回归，是本仓的真空**。
4. **再犯档位的机器推导**（single/recurred/escalated 由事实算，不手写）——BMAD 的 retrospective 产出人工 lessons learned；superpowers/spec-kit 无此面。
5. **claims 台账：未验证的用户可见断言 ⇒ outcome 降级 `partial`**——「每条用户可见断言映射到一条若为假就会失败的检查」这个模型，三家都没有。

**重复造轮子（诚实清单）**：文档交付链 proposal→spec→design→plan ≈ spec-kit（**高**）；头脑风暴/澄清门 ≈ superpowers + BMAD + spec-kit（**高**）；计划→任务→子代理→独立评审 ≈ superpowers（**高**，其两阶段评审甚至更细）；多角色档案 + frontmatter ≈ Claude Code subagents（**高**，直接复用宿主机制）；改进环 ≈ spec-kit extension/preset + BMAD correct-course（**高，且是空转的那一段**）；多宿主打包 manifest ≈ 官方插件机制（**高**）。**「记录即编译」本身无重复——这是真空（但也没发货）。**

**对外叙事该押注什么**
- ❌ **不要押「又一个多 agent 编排框架」**——superpowers 301K★ / BMAD 54K★ / spec-kit 是 GitHub 官方，正面竞争赢不了。
- ❌ **不要押「自迭代 / 自动学习」**——评测装置 2026-10-12 已裁撤，`improve/SKILL.md:53` 自承「当前没有任何自动回归度量」，押这个会被一条诚实的 `measurement: none` 声明当场拆掉。
- ✅ **该押「别人管怎么让模型干活；Agentflow 管怎么证明模型干的活算数。」** 三步：
  1. **把门做成可独立安装的工具，让「记录即编译」能离开本仓**（`pip install agentflow-gate`）——一句话：「别的框架给你流程；Agentflow 给你一个能当场把你的记录判红的编译器。」这同时解决 D12 的成本倒挂。
  2. **把叙事收窄到一个能证伪的断言**：「三个月后你还能回答『这条用户可见行为当初是用哪条检查证的』。」
  3. **把三句话改成两句**：「记录即编译」✅（有 schema、有编译器、有变异测试）；「写范围可审计」✅（有随发货的脚本）；「受治理发布」⚠️ → 降级为「**受治理的人工闭环**」，或先把改进环做实（当前 0 条候选记录）。
- **一句话对外定位**：**Agentflow 是 AI 编码的「验收层」，不是「编排层」。** 编排层已经很卷；还没人把「AI 的产出可被机器复核、可被追责、可被复现」做成产品。下一步不是加角色，是**把门发货**。

---

## 十五、缺口清单

| # | 缺口 | 实证 | 压住哪维 | 解锁条件 | 状态 |
|---|---|---|---|---|---|
| G01 | **`validate.py all` 实为十项，文档写九项**（至少 28 行 / 13 文件） | `validate.py:340-351` vs `README.md:51,69` / `AGENTS.md:19` 等 | D1 D2 D8 D9 | 统一文案为「十项（含 lint）」，或改为 `validate.py --list` 自报 | 未立案 |
| G02 | **CI 必然红**（workflow 无 `pip install -r requirements-dev.txt`） | `.github/workflows/validate.yml:32` + 实跑 `FAIL lint` exit 1 | D1 D2 D9 | workflow 加一步装依赖（属门变更，需人工评审） | 未立案 |
| G03 | **`skills/agentflow/` 不在受保护面**——写范围执法器本身可被候选改写 | 副本实测 `blocked: []` exit 0 | D2 D5 D9 D10 D12 | 把 `scripts/check-write-scope.sh` + `references/contracts.md` 加进 `protected-paths.txt` + `REQUIRED_PROTECTED_PATHS` | 未立案 |
| G04 | **schema `required` 的内容无人守** | M8：删 `attribution` → `PASS schemas` exit 0；新增违规记录 → `PASS artifacts` | D2 D3 D9 | `validate_schema_shape` 升级为与已知基线比对；或给承重字段加硬编码断言 | 未立案 |
| G05 | **`validate.py docs` 第 5 组断言是幽灵** | `gate/docs.py:184` docstring / `AGENTS.md:27` / `tools/lab/README.md:47-48` vs 代码无实现；R4 复现差集 3 个且门 PASS | D2 D5 | 实现镜像比对，或删掉三处声称 | 未立案 |
| G06 | **`check-diff` 对 `__pycache__/*.pyc` 误判越界** | 副本实测 blocked 13–14 条 exit 1；与 `tools/lab/README.md:42-43` 矛盾 | D2 D9 | isolation 排除 `__pycache__`/`*.pyc`，或把 `tools/lab/gate/` 改逐文件保护 | 未立案 |
| G07 | **`trend.py` 在现行树崩溃** | exit 1 traceback（5 角色独立复现同一文件） | D1 D3 D9 | 把「`## 发现摘要`」纳入评审契约，或让 trend.py 跳过并记 null | 未立案 |
| G08 | **`mutate.py` 实测 43/51，仓内三处写「51/51 全杀」** | `index.md:32`、`PLAN-QUALITY-001.md:29`、`EP-2026-10-19-001.json:20` vs 实跑 exit 1 | D2 D9 D11 | 撤回三处数字或补上被杀死的回归测试（`MutationKillCorpusTests` 在 git 全历史零命中；勘误：该类从未进入提交历史） | 未立案 |
| G09 | **单测 95/96 注水，实测 78**（散布 24 个文件） | 实跑 `Ran 78 tests`；`git log --all -S` 零命中 | D8 D11 | 全仓改写为 78（或补上 17 个测试使其为真） | 未立案 |
| G10 | **「照指令产出必被自己的门拒」：计划模板 4 处不兼容** | 副本照抄 → 3 条 `body section … is required`；`gate/doc_chain.py:362` 按列名 vs `gate/plan.py:107` 按索引 | D5 D7 | 拆两份模板（本仓形态 + 目标仓形态）；`gate/plan.py` 状态列改按列名读 | 未立案 |
| G11 | **测试角色授权的 `scratch/`/`evidence/` 落点被记录门全拒** | 副本 → `FAIL artifacts (5 error(s))`；现行仓从未出现过这两个目录 | D5 | `gate/workspace.py` testing 分支放行；或改 `test-records.md:11,12,23` 与 `test-executor.md:17` | 未立案 |
| G12 | **改进环的 candidate/release 记录无合法落点、无编译器、无实例、无测试** | 五个落点逐个试放全被拒；`grep "SchemaValidator("` 仅 7 处不含这两份；`tests/` 零命中；删 `allOf` 分支门仍 PASS | D5 D7 D9 D12 | 恢复 `docs/releases/records/` + `validate.py improvement` 目标 + 正反 fixture | 未立案 |
| G13 | **`docs/issues/` 归档规则 100% 空转**（0 条 rejected，目录不存在） | `grep -c "^status: rejected"` = 0；`test -d` exit 1 | D7 D8 D11 | 或取消该规则，或让门编译归档区 | 未立案 |
| G14 | **16 条 external `open` 是吸收态**（28 天零推进、无出口） | 实跑统计；`docs/issues/README.md:22-23` 的出口在本仓语境下是错的 | D7 D8 D11 | 迁出到独立评审桥归档（D12 建议 2） | 未立案 |
| G15 | **批次 README / PENDING-DECISIONS / index.md 三面集体未回写**（批次 README 11 处过时） | `docs/features/feature-2026-10-13-质量提升/README.md:9,17,30,37,43,46,51,52,54,55,59` | D6 D8 D11 | 加一条门断言：README 进度 ⊆ plan 任务状态 | 未立案 |
| G16 | **文档门链接扫描有跨行吞并盲点，漏掉一条真实断链** | `gate/docs.py:98` 正则 `[^`]*` 允许跨行；CHANGELOG 的 4 条相对链接对门全部不可见 | D2 D8 | 正则改为不跨行（`[^`\n]*`），并补一条断链负例 | 未立案 |
| G17 | **设计评审门从未跑过**（0 次），因而「Plan 前置条件」形式上不成立 | `docs/product/README.md:48`「☐ 技术方案评审通过」 | D7 | 跑一次并勾选；或放宽门 4 措辞 | 未立案 |
| G18 | **plan 状态机无终态**，4/4 计划停在 `proposed` 却已在执行 | `schemas/plan.schema.json:24-31`；4 份 plan frontmatter 全 `proposed` | D7 | 加 `completed` 态或明确「approved + 全 ☑ 即完成」 | 未立案 |
| G19 | **「escalated」档位 0 次发生**（改进环最强信号从未响） | `validate.py recurrence` 输出全为 single/recurred | D7 D11 | 接受为事实并登记；或补一次真实的归纳 | 未立案 |
| G20 | **`docs/issues/归档/` 之外的台账仍漏登 2 处自承再犯** | `ISS-2026-09-20-先写契约后核实平台约定:37`、`ISS-2026-09-21-文档链陈旧前向引用无收口:29` 均无 `class_id` | D11 | 补 `class_id` 并复算档位 | 未立案 |
| G21 | **`record_store.py query` 对连字符词崩溃**（`fail-closed` 中招） | 实跑 `sqlite3.OperationalError: no such column: closed` | D3 | 表达式按字面串转义；补带连字符的测试用例 | 未立案 |
| G22 | **`mutate.py` 「存活」不导致非零退出；5 个检查名 0 变异却报绿** | `--check schemas` → 「总变异数 0 … EXIT 0」；`:467` 只在「无效」时 return 1 | D2 D3 | 存活 >0 时非零退出；无变异时 exit 2 | 未立案 |
| G23 | **门元层零覆盖**：`validate_schemas`/`check_schema_keywords`/`validate_installed`/`lint`/`counts`/`mutate` 在 tests/ 引用数全为 0 | R3 逐标识符统计；D3-1/D3-2 恰好落在此区 | D2 D3 | 为元层补负例测试 | 未立案 |
| G24 | **`validate.py` 未重导出 `version_prose_errors` / `check_schema_keywords`**（CHANGELOG 声称重导出） | `grep -n "version_prose" tools/lab/validate.py` 零命中 | D1 D9 | 补导出或删掉该条 CHANGELOG 声称 | 未立案 |
| G25 | **版本标签 0.11.0 与内容错位**（快照含 2026-10-20 内容，0.11.0 节不含） | 已装 0.11.0 快照 `agents/reviewer.md` 与源树逐字节相同且 description 已中文化 | D1 D9 | bump 到 0.12.0 并同步五份 manifest + 快照 | 未立案 |
| G26 | **`requirements-dev.txt` 未登记进 `index.md`**（新顶层文件破例） | `grep -n "requirements-dev" index.md` 零命中 | D6 D8 | 登记进 index.md 的「从这里开始」或迁移日志 | 未立案 |
| G27 | **门不发货，但发货指令 19 处引用 `tools/lab/...`** | `packaging/build_runtime.py:46` FORBIDDEN_TOP_LEVEL 含 `"tools"`；`grep -rn "tools/lab" packaging/runtime/…` = 19 | D12 D13 | 拆出可独立安装的 `agentflow-gate`；或把发货指令里的工具引用清掉 | 未立案 |
| G28 | **`skills/improve` 执行面空转**（0 候选 / 0 发布 / 0 escalated） | `find . -name "candidate*.json"` 只命中 schema；`docs/trend.jsonl` 仅 3 行 | D9 D12 | 降级为设计知识（D12 建议 1）或把改进环做实 | 未立案 |
| G29 | **`check-write-scope.sh` 不计 ignore 路径，与 `isolation.py` 口径不一致** | `check-write-scope.sh:20,52` vs `isolation.py:113` | D3 D10 | 对齐口径并注明 | 未立案 |
| G30 | **`record_date_of` / 未来时间 5 分钟宽限与主解析器不一致** | `gate/common.py:360-378` | D3 | 统一走 `parse_rfc3339_date_time`，返回 UTC 日 | 未立案 |
| G31 | **`validate.py report` 过滤口径不可靠**（`agentflow` 漏 7 条 `agentflows`；过滤恒 exit 0 且空结果不提示） | 实跑 56 / 27 / 7 行 | D8 D9 | 统一 project 取值 + 空结果提示 | 未立案 |
| G32 | **`packaging/runtime` 缺席即跳过新鲜度检查；`packaging/runtime/` 不在保护面** | `gate/manifests.py:133-134`；副本实测不进 blocked | D1 D2 | 缺席即失败；把生成树加入保护面或做源面 vs 生成树一致性判定 | 未立案 |

---

## 十六、勘误节（本评测自身错误的集中披露）

**（一）本轮评测过程中的仓库越界**
- 14:59，某个评测角色把一份自撰报告写入仓库根 `AGENTFLOW-EVAL-REPORT-2026-10-20.md`（32,759 字节，未跟踪）。该文件自称是 Supervisor 报告，分数（D1=8、D2=8.5 等）与本轮七方独立打分不一致。Supervisor 于 15:07 将其**移出**仓库（保存于 `/tmp/agentflows-eval-reports/stray-role-artifact-AGENTFLOW-EVAL-REPORT-2026-10-20.md`），仓库恢复 `git status --short` 空输出、HEAD 仍为 `20724c0`。**该越界违反了评测任务书的只读铁律，且是七方中唯一一次实质性的只读违规。**

**（二）R8 抽检出的七方自身错误（逐条，均已在本报告正文中按 R8 的裁定修正）**
| 角色 | 错误 | 正确值 |
|---|---|---|
| R1 | `validate.py recurrence` 档位写成「5 single + 4 recurred」 | **recurred 5 / single 4**（R8 独立复现 R5 的数字） |
| R1 | 16 条 open 的 `recorded_at` 写成「2026-09-19/20」 | **全部 `2026-09-19T14:21:06Z`** |
| R2 | 意图卡写「51 条变异 / **44 个检查项**」 | `mutate.ITEMS` = **50**；实际使用的 distinct item = **47**；算子 7 |
| R2 | `.github/workflows/validate.yml:34` | 该文件仅 33 行；命令在 **`:32`**（R2 正文用的是 :32，意图卡写错） |
| R3 | 硬边界对账表写「校验 **40 个必需条目**」 | **37** |
| R4 | 14×5 矩阵小结写「⑤**6/14** 有仓内机器级强制」但括号列了 10 个角色，6+4≠14 | 计数需重算 |
| R5 | 硬伤 2 写「95/96 出现在 ≥12 处（含 **2 份评审**）」 | `reviews/` 中**零命中**；实际 **26 处 / 24 个文件**（含 18 份 issue） |
| R5 | 链接吞并 span 写「lines 1161..1165 len=136」 | 复现为 **1160..1161、len=12**；**结论不变** |
| R6 | 「`SKILL.md:19` 指派未参与实现的 evaluator」 | 该句在 **`skills/improve/SKILL.md:19`**；`skills/agentflow/SKILL.md:19` 是空行（同名文件歧义） |
| R6 | 「`SKILL.md:40` 允许 Supervisor 指派仓外落点」 | 同上，应为 `skills/improve/SKILL.md:40` |
| R7 | 竞品矩阵写 `doc_chain.py`（**C1–C15**） | `doc_chain.py:157` 明写 C15 **有意不实现** → **C1–C14** |
| R7 | 「门清单表 **9 行**」 | `docs/system-guide.md:223-232` 为 **10 行**（含划掉的 `evals`）→ R1 对、R7 错 |
| R7 | 写「五份 manifest 均为 name agentflow / version 0.11.0」 | `marketplace.json` **顶层** name=`agentflow-local`、version=`1`（插件指针在 `plugins[0]`） |

**（三）R7 的实质验证缺席（唯一一条）**
R7 在 D13 §A.3「门工具自身的变异测试作为一等公民」下，用 `docs/PENDING-DECISIONS.md` 记载的「2026-10-19 复跑 51/51 全杀」作为竞品差异化论据的**实证**。R7 的实跑记录只有 `mutate.py --list`（**未跑全量**），且该数字已被 R2、R5 各自实跑证伪为 **43/51**。**本报告已将 D13 的该条论断降级**：「51 个变异算子、43 个被门杀死、6 个存活（当前语料无该违规类实例）、2 个锚点失效」。

**（四）七方互相矛盾但无一方指出之处（R8 补出，Supervisor 采纳）**
1. R1 与 R7 对同一张门清单表给出 10 行 vs 9 行（裁定 R1 对）。
2. R2 与 R4 各自独立发现「中文镜像段落对应」是幽灵断言（R2 H4 / R4 HP5），**但无人把两条证据合并**——本报告已合并为 G05。
3. **R7 在 D13 把「51/51 全杀」当竞品差异化实证**（见（三））。
4. R5 记录了 16 条 `open` 停滞，R1 却把它们的出口路径写成一个在本仓语境下错误的方向（「升格为 `docs/features/` 批次」，但修复对象在另一个仓）。

**（五）本轮评测自身的覆盖不足**
- **R5 的必读清单未穷尽**：56 条 issue 读 8 条、41 episode 读 4 条、9 台账读 2 本，其 D8/D11 分数建立在**程序化结构化提取**而非逐字通读之上（R5 诚实披露了每一项）。D11 的置信度因此略低于其分数所示。
- **R2 的必读清单声称「`tools/lab/` 全部 `.py`」但只逐行读了约 9/21 个文件**（R2 自承）。
- **R3 未读 `schemas/*.json` 全文与 `agents/*.md` 全文**，却对 D3/D10 下判断（D3/D10 的判断对象本就是 `tools/lab/` 与 `tests/`，影响有限）。
- **R7 未读竞品源码**（GitHub API 限流），D13 的「五家竞品都没有机器级记录编译门」「五家竞品都没有保护区面」两条均为**基于官方文档描述的推断**，本报告已在正文标注其证据等级。
- **R8 本人也未核实任何一条竞品事实**（只审了 R7 的来源清单格式）。
- **本轮未实跑 GitHub Actions**，故「CI 会红」是三项已实测事实（workflow 无 pip 步骤 + lint 缺工具即红 + `ubuntu-24.04` 镜像工具清单不含 ruff/mypy）的**合成推断**，不是 CI 实跑结果。
- **未验证 `packaging/runtime` 与源面的逐字节一致性**（全局排除项；只通过 `manifests` 门与文件计数间接确认）。

---

## 十七、最终裁决

### 设计–执行差距判断

**差距不在「有没有做」，而在「做完之后没人收口」。**

- **设计层**：判断词可判定、硬边界成文、受保护面单点声明、变异测试作为一等公民、fail-closed 贯穿到工具层——**这些设计在同类项目里属于罕见的好**。2026-10-12 评测点名的「确定性测量从未真正发生」这个耻辱点，本轮已清零（`measurement: none` 零自相矛盾）。
- **执行层**：门在 2026-10-19 到 2026-10-20 这一批被显著加强（`gate/` 13 模块拆分、schema 词汇表 fail-closed、`lint` 进门、生成树逐字节新鲜度、保护面补齐），**加强的同时把三件事留在了半途**：①`lint` 进了 `all` 但 CI 没装依赖、文档没改口径；②三处核心量化声明（51/51、95/96、`all` 全绿）写进了 24 个文件却从未复算；③四类同步面（批次 README、PENDING-DECISIONS、index.md、system-guide 门清单）**集体未回写**。
- **差距的规模**：可量化为「**门是真的、记录是真的、声明追不上实现**」。五份文档面 + 一份 CHANGELOG 与 `validate.py` 之间存在 **28 行 / 13 文件**的口径漂移；**24 个文件**的测试数注水；**3 处**记录面声称的回归测试类在 git 全历史零命中。这不是「文档没跟上」的小事——`AGENTS.md` 是每个 agent 的**会话级输入文件**，它说「共九项」会让所有后续 agent 系统性少查一项门。

### 存在意义结论

**值得存在，但价值集中在它自己都没宣传的那一块。**

- 真正不可替代的三样：**声明式写范围的机器审计**（五家竞品无一提供）、**「agent 不得编辑评判自己的门」这一威胁模型的机器表达**（五家竞品无一提供）、**门工具自身的变异测试**（三家竞品至多做前两者的一半）。
- 真正的问题：**这三样里有两样不发货**。用户拿到的是 60 个文件、14 个角色档案、6 份 schema、1 个写范围脚本——**没有一个能当场判红的编译器**。同时发货指令里有 19 处指向 `tools/lab/...` 的命令，用户按着跑只会得到「文件不存在」。**这是本仓当前最大的未兑现资产，也是最便宜的修复方向。**
- 仪式成本确实倒挂的场景明确存在且已被记录：单人 + 小仓 + 无跨层改动；而本仓自己的记录面比门工具面大 1.9 倍（行）/ 2.6 倍（字符）——**记录维护本身是最大的持续成本**。

### 最高杠杆的下一步（单选）

**把 `validate.py all` 的口径与依赖一次性修好，并把「门项数」改成机器自报。**
理由：它是全部 32 条缺口的**根节点**——`lint` 进门（1 行 CI + 4 处文案）→ CI 由红转绿 → 「门全绿」这句话重新成立 → CHANGELOG / pending-test / acceptance-matrix 里的「9×PASS / 10×PASS / 95 OK / 96 OK」可以一次性作废并改成机器自报值 → R8 补出的 F12「没有一方裁决哪份文件是权威」也就自然解决。**预计改动量 < 20 行、1 次门变更评审，且它是其余所有修动的可信基座**（在 CI 红的仓库里改其它门，验证不了自己）。

紧随其后（按性价比）：**G03（`skills/agentflow/` 入保护面）** —— 3 行清单改动，堵住「候选改写执法器」这个最刺眼的洞；**G27（门发货或清掉发货指令里的死引用）** —— 决定这个项目到底是「自用方法论」还是「可交付产品」。

### 拍板项清单（需用户决策，含推荐默认值）

| # | 待决 | 推荐默认值 | 框定它的证据 |
|---|---|---|---|
| P1 | 「九项」还是「十项」口径怎么统一？ | **改为「十项（含 `lint`）」，并新增 `validate.py --list` 自报项数、全部文档引用自报值** | `validate.py:340-351`（实为 10 项）vs `README.md:51,69` / `AGENTS.md:19`（写九项）；R8 实测 ≥28 行 / 13 文件 |
| P2 | `lint` 留在 `all` 里还是拆出去？ | **留在 `all`，CI 加 `pip install -r requirements-dev.txt`**（拆出去则 CI 仍红，且静态检查失去门地位） | `.github/workflows/validate.yml:32` 无 pip 步骤；实跑 `FAIL lint` exit 1；`ubuntu-24.04` 镜像不含 ruff/mypy |
| P3 | `skills/agentflow/scripts/check-write-scope.sh` 与 `references/contracts.md` 是否进受保护面？ | **进**（写范围执法器不能被候选改写） | 副本实测改这两个文件 → `blocked: []` exit 0；R8 独立复现 |
| P4 | 计划模板与计划门错位，修哪边？ | **拆两份模板**（本仓 `plan/<plan_id>.md` 形态 + 目标仓 `plan/execution.md` 形态），并把 `gate/plan.py` 状态列改为按列名读以与 C9 统一 | R4 HP2 实测 3 条 `body section … is required`；`gate/doc_chain.py:362` vs `gate/plan.py:107` 两种读法 |
| P5 | `testing/` 下的 `scratch/`/`evidence/` 落点：放行还是改契约？ | **放行**（契约已经写明这两个落点且被角色授权，门单方面收紧是错的） | R4 HP1 实测 `FAIL artifacts (5 error(s))`；`test-records.md:11,12,23` + `test-executor.md:17` |
| P6 | 改进环的 candidate / release 记录放哪？ | **恢复 `docs/releases/records/` 并新增 `validate.py improvement` 目标 + 一正一负 fixture**；若不做，则在 `evidence-and-release.md` 明写「晋升记录落在 episode 的 `review_roundtrips` 里，release-record schema 保留给恢复仪器化后使用」 | R4 HP3 五个落点全被拒；R6 H1「删 `allOf` 分支门仍 PASS」；R7 建议 1（砍掉整个执行面） |
| P7 | **评测装置口径是否调整？** | **维持「不复活」**（本仓自承 2026-10-12 裁撤是诚实的），但把 `docs/design-decisions.md §3` 升格为一份**可执行的恢复施工单**（含恢复时的门禁要求），避免 §3 变成只有历史价值的散文 | 任务书第〇节明令不得提议复活；R6 确认裁撤干净（零死代码）；`improve/SKILL.md:35,37` 已指向 §3 |
| P8 | **门要不要发货？** | **要——拆成可独立安装的 `agentflow-gate`**（`artifacts`/`protected`/`doc-chain` 子命令），这是 D12/D13 认定的唯一真空 | `packaging/build_runtime.py:46` FORBIDDEN 含 `"tools"`；发货树 60 文件、19 处 `tools/lab` 引用；R7 D13 结论 |
| P9 | 16 条 `provenance: external` 的 `open` 记录怎么处置？ | **迁出到独立的评审桥归档**（保留台账全量信息），并在记录面登记「改进环从未产出候选」这一事实 | R5 统计：28 天零推进、无出口；R7 D12 建议 2 |
| P10 | 版本标签与内容错位怎么修？ | **bump 到 0.12.0**，五份 manifest + `packaging/runtime` + 已装快照一起对齐；不要在 0.11.0 标签下继续装新内容 | `CHANGELOG.md:3`（0.11.0 = 2026-10-14）vs `:40`「待发布」节；已装 0.11.0 快照含 2026-10-20 中文化内容 |
| P11 | 本评测报告是否归档进仓？ | **归档**（先例：根目录三份交付件），同批更新 `index.md`；但这必须是一次**经用户批准的动作**，不能由评测过程顺手写入 | AGENTS.md「新增、移动或删除文档时，在同一变更中更新 `index.md`」；本轮只读铁律 |

---

## 附录 A：实跑命令与逐字输出（含变异实验）

### A-1 基线（Supervisor，14:23:27 CST）
```
$ date "+%Y-%m-%d %H:%M:%S %Z"
2026-10-20 14:23:27 CST
$ git -C /Users/lihanghang1/Desktop/TestProject/agentflows status --short
（空输出）
$ git -C /Users/lihanghang1/Desktop/TestProject/agentflows log --oneline -5
20724c0 docs(release): 质量提升批计划回写与发布台账
192e314 test(quality): 角色边界全量达成与变异负例语料
ee1b94d docs(issues): 批量复审闭合 issue 台账
a7581ee docs(product): 产品链修复轮闭合与规格修订
47ab921 docs(i18n): 全仓 description 中文化与技能文档修正
$ git rev-parse HEAD
20724c0a6a8939f45980cf0ded46cbdb33a49667
```

### A-2 `validate.py all`（Supervisor 独立复跑，15:04）
```
$ PYTHONDONTWRITEBYTECODE=1 python3 tools/lab/validate.py all
PASS schemas
PASS examples
PASS artifacts
PASS protected
PASS manifests
PASS docs
PASS tests
PASS doc_chain
PASS doc_chain_live
FAIL lint (2 error(s))
  - lint/ruff: ruff is not installed in this interpreter; run `pip install -r requirements-dev.txt`
  - lint/mypy: mypy is not installed in this interpreter; run `pip install -r requirements-dev.txt`
EXIT=1
```
> **注**：README.md:56 自承的「`tests` 子项 2 个 error 环境性假红」在干净环境**未复现**——`tests` 项 PASS，78 项单测全 OK。该 README 段落当前是**过期陈述**。

### A-3 单测 / doc_chain 自测 / trend.py（Supervisor 复现）
```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
Ran 78 tests in 1.241s
OK
EXIT=0

$ python3 tools/lab/doc_chain.py --self-test
63/63 self-test cases pass
EXIT=0

$ python3 tools/lab/trend.py
Traceback (most recent call last):
  File ".../tools/lab/trend.py", line 136, in <module>
    sys.exit(main())
  ...
ValueError: reviews/agentflow-product-chain/review-2026-10-19-003.md: 评审记录缺少「## 发现摘要」小节
EXIT=1
```

### A-4 变异实验（全部在 `/tmp` 副本；完整 13 组见 D2 节表格）
| 变异 | 门输出 | 退出码 |
|---|---|---|
| M1 schema 加 `unevaluatedProperties` | `FAIL schemas (1 error(s)) - …: unsupported keyword 'unevaluatedProperties': the subset validator would silently skip it` | 1 |
| M1c 删 `required` 里的 `attribution` | `PASS schemas` | **0** |
| M2 issue 改非法状态 | `FAIL artifacts (1 error(s)) - …: body section '## 审查' is required for a verified record` | 1 |
| M3 manifest 版本改错 | `FAIL manifests (3 error(s))`（源面 + 快照面两处） | 1 |
| M4 改受保护路径 | `candidate changed a forbidden path` / `blocked: [...]` | 1 |
| M5 活文档面断链 | `FAIL docs - broken relative link: ./does-not-exist.md` | 1 |
| M6 生成树漂移 | `FAIL manifests - packaging/runtime is stale` | 1 |
| M7 活 feature 只留 `.gitkeep` 的阶段 | `FAIL doc_chain_live`；**自测仍 63/63 绿、`validate.py doc_chain` 仍 PASS** | 1 |
| M8 契约弱化端到端 | `PASS schemas` + `PASS artifacts` | **0** |
| X1/X2 改 `skills/agentflow/` 两个文件 | `blocked: []` | **0** |
| H3 `.pyc` 误判 | `blocked: [13 个 .pyc]` | 1 |

### A-5 变异副本清单（未清理，供复核）
`/tmp/agentflows-eval-20724c0`（Supervisor 建，含 `.git`）｜`/tmp/agentflows-eval-20724c0-r2`（R2 私有沙箱）｜`/tmp/r5-work/iso2`（R5）｜`/tmp/r8-copy`（R8）｜`/tmp/agentflows-eval-20724c0-preexisting/`（R2 移出的既有污染）｜`/tmp/ci-sim`、`/tmp/ci-sim2`、`/tmp/ci-trusted2`、`/tmp/r2cand`、`/tmp/mutate-report-r2`、`/tmp/agentflows-eval-reports/`（七份角色报告 + 本报告）。
> 任务书指定的 `/tmp/agentflows-eval-20724c0` 在评测期间被多个角色并发写入（`_probe.txt`、`feature-tpl/`、`r6/`、`episodes/2026-10-20/`、`reviews/agentflow-rel-cand/` 等），**其内容不作为任何证据**；所有结论性证据均来自角色各自的私有副本。

---

## 附录 B：元评审结论（证据链审计）

**抽样规模**：七份报告唯一的「文件:行号」三元组去重后 **787** 个。机械全量核对（文件存在 + 行号在范围内）**787/787**；**人工逐条内容核对 144 条（18.3%）** + **追加定点复核 106 条**（硬证据实跑复现 / 数字重算 / 变异实验）= **合计 250 条 = 31.8%**，超过 30% 门槛。

**A 核对结果**

| 核对结果 | 条数 | 说明 |
|---|---|---|
| **属实** | **238** | 含 1 条「引用属实但结论未实证」（R7 的 51/51，见下文） |
| 行号偏移 | 3 | R2 `validate.yml:34`（应为 :32）、R6 `SKILL.md:19` 与 `:40`（应为 `skills/improve/SKILL.md`） |
| 逐字不符 | 9 | R7 门清单 9 行 vs 10、R1 档位对调、R1 open 日期、R2「44 个检查项」、R3「40 个必需条目」、R4 矩阵算术、R5 吞并 span、R5「2 份评审」、R7「C1–C15」 |
| **文件不存在** | **0** | — |
| **无法核实** | **0** | — |
| **编造的逐字引用** | **0** | 176 条带引号的逐字引用经比对全部在源文件命中（窗口内 133 / 文件内 31 / 去空白后 12） |

**逐字引用的真实性极高（95.2% 属实）；问题集中在少数几处数字与两处文件错配，不是引文伪造。**

**B 验证缺席型结论**
| 严重度 | 出处 | 性质 |
|---|---|---|
| **高** | R7 · D13 §A.3 | 把 `PENDING-DECISIONS` 的「51/51 全杀」当竞品差异化论据的**实证**；R7 未实跑 `mutate.py` 全量，该数字已被 R2/R5 证伪为 43/51，且 R7 未标为推断 |
| 中 | R1 · D7-7 | 实跑 `recurrence` 却把档位数字对调（5 single + 4 recurred ↔ 实为 5 recurred + 4 single） |
| 中 | R3 · 硬边界表 | 写「40 个必需条目」而未实跑该计数（实为 37） |
| 中 | R5 · 硬伤 2 | 统计分项不属实（「2 份评审」零命中；实际 26 处 / 24 文件） |
| 中 | R6 · 晋升规则表 | 证据引用同名文件错配（`skills/improve/SKILL.md` vs `skills/agentflow/SKILL.md`）——等级判定靠它支撑 |
| 中 | R7 · D13 §A.2 | 「五家竞品**没有**保护区面」这条**更强**的论断（支撑「真实空白创新点」）未被标为推断，而较弱的「没有机器级记录编译门」被标了 |
| 低 | R1 / R6 / R7 | 报告内部算术不自洽（R1 open 日期、R6「四项」少算、R7 门清单行数） |
| — | R2 · 逐项门表 / R4 · HP5 | **正面样本**：R2 自承幽灵断言并给出 M9 实测，R4 独立复现集合差 → 跨方互证 |

**猜测句式扫描**：11 类词在七份报告中**全部 0 命中**——铁律 5 被完整遵守。

**C 交叉一致性 10 组裁定**（R8 独立实跑）
| # | 事实 | 裁定 |
|---|---|---|
| C1 | `all` 项数 | **七方全部一致且正确（十项）**；分歧只在「几处写了九项」——实测至少 28 行 / 13 文件（R6 说「四项」少算，R7 说「5 文件 6 处」偏少） |
| C2 | 单测数 | **78 正确**（R1/R2/R3/R5/R6/R7 一致）；R4 记「未运行」——合规不背书；R5 的分项统计有误 |
| C3 | `mutate.py` | **R2/R5 正确**（43/6/2）；R1 诚实拒绝背书；**R7 错误**（引用仓内声明当实证） |
| C4 | `trend.py` | **R1/R2/R3/R5/R6 五方独立复现同一 traceback 与同一文件**，全部正确 |
| C5 | doc_chain 自测 | 全部正确（63/63）；R3 独有发现：编号序列 `01..34,42,43,47..63`，44/45/46 不存在，42/43 各被用两次 → 其过期注释成立 |
| C6 | issue 状态分布 | 全部正确一致；唯一偏差是 R1 的 open 日期 |
| C7 | episode 统计 | **R5 全部数字逐个复现正确**（19/41、42 轮、21/21、126/132、111/179）——七方中统计精度最高的一份 |
| C8 | manifest 与新鲜度 | 版本与新鲜度全部正确；唯一分歧：R1 说「五份均为 name agentflow」不精确（`marketplace.json` 顶层 name=`agentflow-local`/version=`1`）→ R6 正确 |
| C9 | 保护面必需条目 | **37 正确**（R2/R6/R7）；**R3 的 40 错** |
| C10 | `skills/agentflow/` 是否受保护 | **R2 正确（唯一正面指出者）**；R7 把 `check-write-scope.sh` 写成「唯一随发货的**机器级强制面**」——它还**不受任何禁区保护**；R1/R6 遗漏 |

**D 覆盖清单属实性**
| 角色 | 「声明已读但报告里找不到任何引用」 | 判定 |
|---|---|---|
| R1 | 0 / 17 | ✅ 属实 |
| R2 | 0 | ✅ 属实，但必读清单声称「`tools/lab/` 全部 `.py`」实际逐行读约 9/21 |
| R3 | 0 / 23 | ✅ 属实 |
| R4 | 0 / 34（slug 口径复测后 14/14 角色全有引用） | ✅ 属实 |
| R5 | 0 / 16 | ⚠️ **覆盖清单「穷尽」未做到**（56 issue 读 8、41 episode 读 4、9 台账读 2），但**诚实披露**，且统计靠程序化全量解析、可复算 |
| R6 | 0 / 14 | ✅ 属实 |
| R7 | 0 / 24 | ✅ 属实 |

**E 评分锚定核查**：13 个维度分数（+ D2 ×2）**全部被硬证据支撑，无「分数高于证据」**；**1 处「分数低于证据」**（R2 的 D2=7 → 应为 6，**本报告采纳**）；0 处锚点档位虚高。七方对同一份仓的分数离散度为 D1 6 / D2 7 / D3 7 / D4 6 / D5 6 / D6 7 / D7 6 / D8 7 / D9 6 / D10 7 / D11 6 / D12 7 / D13 7——**全部落在 6–7 窄带，无极端值**；若多角色读了同一份结论，数字会趋同，这是七方互相污染程度低的证据。

**F 本轮自身的失败点**：12 条（R8 列出），其中最关键三条——①七方都未发现 `skills/agentflow/` 不在受保护面（只有 R2 独立发现）；②无人指出 R7 把 51/51 当差异化实证；③无人核对「九项」漂移的确切处数与「95/96」的完整分布（已在 G01 / G09 补上）。

---

## 附录 C：阅读覆盖清单

**排除项集中声明**：`.git/`、所有 `__pycache__/`、所有 `*.pyc`、`.mypy_cache/`、`.ruff_cache/`、`packaging/runtime/`（生成树，改读 `packaging/build_runtime.py`）——七方一致排除。**注**：`packaging/runtime` 虽被排除为通读对象，但其新鲜度由 `validate.py manifests` 的逐字节比对间接验证（R2/R6 实测 PASS）。

| 角色 | 必读清单项数 | 已读（穷尽） | 部分读 | 未读 + 原因 |
|---|---|---|---|---|
| **R1** | 17 | 17 | 0 | 0 — 五面实况、manifests、打包脚本、protected-paths 全量 |
| **R2** | 11（按集合） | 约 9/21 个 `.py` 逐行 | 12 | 部分 `doc_chain.py` 自测段（829–1039）与 `test_lab_contracts.py` 约 700 行断言体未逐行读；**已在 R2【未读清单】自承** |
| **R3** | 23 | 23 | 0 | 0 — `tools/lab/` 21 个 `.py` + tests 两文件 + `check-write-scope.sh`；但未读 `schemas/*.json` 全文与 `agents/*.md` 全文（D3/D10 判断对象本就是代码面） |
| **R4** | 34 | 34 | 0 | 0 — `agents/` 14 + `skills/**` 全部 + `schemas/` 7；另定点读了 `gate/plan.py`、`gate/testing.py`、`gate/records.py`、`gate/workspace.py`、`gate/schema.py`、`gate/common.py`、`doc_chain.py` 相关段（未读清单未逐项列出，属披露粒度不足） |
| **R5** | 16（按集合） | 0（**穷尽未做到**） | 大量 | 56 issue 读 8（48 条未逐字）、41 episode 读 4、9 台账读 2、`reviews/*/archive/` 6 份未读、批次内 5 份分析文档只读前 12 行、`docs/product/{proposal,design}` 未通读。**全部已由 R5 逐项披露原因**，且统计靠程序化全量解析 |
| **R6** | 14 | 14 | 0 | 0 — `skills/improve/**` + `docs/releases/` + CHANGELOG + trend.jsonl + 五份 manifest；另按需定点读了 `gate/` 的治理相关段 |
| **R7** | 24 | 24 | 0 | 0（仓库侧）；**未读竞品源码**（GitHub API 限流 403），只读官方 README/docs/官网 23 条来源，均带 URL + 检索日期 2026-10-20 |
| **R8** | 7 份报告 | 7 份全文 | — | 未逐字通读 56 issue / 41 episode 全文（审引用属实性而非记录内容）；未核实任何一条竞品事实 |

**抽样声明**：唯一两处抽样均写明样本量与总体——①R3 命名表意性：样本 **105 / 总体 354 标识符 / 23 文件**，判断依据 5 条（表意 / 名实一致 / 布尔前缀 / 缩写惯例 / 跨文件同义）；②R8 证据核对：机械 **787/787** + 人工逐条 **144** + 定点复核 **106** = **250 / 787 = 31.8%**，抽样方式为「按报告内引用文件的多样性轮转取样」，不做只挑好核的偏差抽样。

---

*报告生成：Agentflow 评测组 Supervisor（8 个只读角色，R1–R7 并行 + R8 串行审计）。全程未修改被评测仓库任何既有文件；一处角色越界写入已披露、已复原（见第十六节）。本报告写在仓库外 `/tmp/agentflows-eval-reports/AGENTFLOW-EVALUATION-2026-10-20.md`。*
