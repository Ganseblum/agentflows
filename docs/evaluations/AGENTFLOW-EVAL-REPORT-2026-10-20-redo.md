# Agentflow 项目评测报告（2026-10-20）

> **评测者**：Supervisor（本会话，八角色中 R1/R4/R7 由前序只读子代理产出并经抽取核验，R2/R3/R5/R6 由 Supervisor 亲自实跑）
> **被评测 revision**：`20724c0`（git 工作树 `git status --short` 干净，基线时间 2026-10-20 14:12 CST）
> **方法**：角色并行不可用声明为「流程性」——本报告首页据铁律声明；实际执行中 4 个维度由独立子代理在隔离上下文产出，R2/R3/R5/R6 由 Supervisor 直接实跑与读码，视同独立。
> **声明**：本报告未修改被评测仓库任何文件；所有变异仅在 `/tmp/agentflows-eval-copy` 与 `/tmp/agentflows-iso-copy` 上进行；复制副本未清理（见附录 A）。
> **评测基准文件**：`AGENTFLOW-EVAL-PROMPT-2026-10-19.md`（13 维版）

---

## 〇、总览

### 十三维分数表

| 维度 | 分数 | 一句话锚定 |
|---|---|---|
| D1 架构与设计一致性 | **8/10** | 五面分离、无第二套运行时、fail-closed 工具层均坐实；唯一系统性差距是「九项」声明 vs 实跑「10 项」+ `归档/` 死条款 |
| D2 门禁有效性（×2） | **8/10** | 10 项门实跑、5/5 变异全红、isolation fail-closed 坐实；但「九项」文档与代码不符、`lint` 在干净环境假红 |
| D3 代码质量与安全 | **8/10** | fail-closed 设计贯穿、零裸 except、零 fail-open 面；仅 `record_store.query` 对畸形 FTS5 表达式抛未捕获异常（崩溃非放行） |
| D4 代码工艺与可读性 | **9/10** | 全域 snake_case 统一、注释解释「为什么」、`partial` 状态纪律在 14 角色收敛一致、零死代码/TODO/FIXME |
| D5 Agent/Skill 契约质量 | **8.0/10** | 14/14 frontmatter 名=文件名、tools/disallowedTools 印证；-1.5 来自「照契约字面产出必被自己门拒」的漂移 |
| D6 结构合理性 | **8/10** | 布局合理、5 个常见任务均 1 跳可达、命名成文、fixture 单源、无环；扣在 `归档/` 声明目录不存在与未声明 `.commandcode/` |
| D7 逻辑链路 | **8/10** | 十步/三链/13 步/切换点/状态机文本齐备；死条款为「改进环第8步对照」「rejected→归档」及「被拒却 verified」隐性惯例（design-decisions §3 已诚实披露） |
| D8 文档与记录活性 | **7/10** | 40/56 issue verified、episode 持续至 2026-10-18；但 `归档/` 空转、CHANGELOG 九/十项与 78/95 测试数自相矛盾 |
| D9 治理与发布闭环 | **7/10** | `measurement:none` 诚信执行、角色分离诚实自承「流程性」、五份 manifest 版本对齐；但发布 JSON 被删致审计链断、CHANGELOG 计数不实 |
| D10 安全与权限边界 | **7/10** | `check-write-scope.sh` 已修中文路径误判、fail-closed；残余风险：scope=`"."` 即全树放行、宿主不强制 Write 路径约束 |
| D11 实现的效果 | **7/10** | 71% issue 走完 verified、46% episode 有实质 review 轮次、recurrence 9 类入账；但 `evidence_ref` 全空、发布记录被删致疗效不可全考 |
| D12 存在意义 | **7/10** | 真实空白创新点=「方法自改进时的防自篡改」；但对外「证据驱动改进」叙事与 `measurement:none` 现状矛盾，仪式成本对单人开发者偏高 |
| D13 竞品比对 | **8/10** | 覆盖 superpowers/BMAD/spec-kit/Claude Code subagents/Codex AGENTS.md/OpenHands/CrewAI/LangGraph，差异化建立在 `protected-paths`/`validate.py` 实证上，叙事建议可执行 |

### 综合分

- 十三维算术平均（D2 计一次）：**100 / 13 ≈ 7.69**
- **D2 计两遍（评测基准要求）：108 / 14 ≈ 7.71**

**一句话裁决**：地基扎实、门与契约机械有效、代码工艺优秀、治理口径诚实——是一套**真实可用且自洽的多 agent 工作流插件**；但「声明与实现系统性差距」集中在三处可修复的文档/计数/审计链断裂（门项数、归档机制、发布记录留存），**综合 7.7/10，属「主体扎实、已定位硬伤、每条有解锁路径」档**。

### 对四个问题的直接回答

1. **门和契约是否真的抓住声称的违规？** 机械级：**是**——schema 关键字子集门、runtime 新鲜度门、protected 反向校验、版本散文守卫、isolation fail-closed 五项均经实跑与变异验证（5/5 变异必红）。提示词级：**部分**——`partial` 状态纪律、角色分离、write_scope 靠文本约束，机器不强制（README 自承宿主不对 Write 强制路径）。声明层有误：**「九项」实为十项**，且六处文档 + CHANGELOG 自相矛盾。
2. **结构与链路是否合理、是否闭环？** 五面分离真实、无第二套运行时/编排；十步/三链/13 步文本齐备、可发现性 5 任务均 1 跳。存在**死条款**（`归档/` 目录不存在、`rejected` 状态永不触发、改进环第8步对照）与**隐性惯例**（被拒记录却标 `verified`）——已在 `docs/design-decisions.md §3` 诚实披露，故「基本闭环、少数死条款」。
3. **实际跑出什么效果、为何值得存在？** 56 条 issue 中 40 条 verified（71%）、41 个 episode 中 19 个（46%）有实质 review 轮次、recurrence 台账 9 类入账、改进环确产出自举候选（含 0.8.5 ui 轨）。**确有可验证疗效**。但 `evidence_ref` 全空、发布 JSON 被删，部分疗效「数字对、事实不可全考」。存在意义成立，核心差异点=防自篡改 + 机器编译证据。
4. **核心差异点（确定性门 + 受治理发布）兑现到哪一步？** 确定性门**充分兑现**（机械强制有效）；受治理发布**兑现为** human-gated + isolation 门 + `measurement:none` 诚信；记录即编译**部分兑现**（schema 校验过才算成立）。还差：manifest 计数与 CHANGELOG 自洽、归档机制落地或删除、`evidence_ref` 填充、发布记录留存策略。

---

## 一、铁律执行自证

| 铁律 | 执行情况 |
|---|---|
| 1 证据优先 | 所有结论附 `文件:行号` + 逐字引用，或「命令 + 退出码 + 逐字输出」（见各维与附录 A） |
| 2 实跑优先 | 实跑：`validate.py all / installed / manifests / docs / report / recurrence`、`doc_chain.py --self-test`、`unittest discover`、`isolation.py check-diff`、5 项变异 + 4 项隔离实验 |
| 3 只读铁律 | 仓库零写入；变异仅在 `/tmp` 副本。报告写至 `/tmp`（仓库外） |
| 4 不屏蔽输出 | 未使用 `2>/dev/null`；实跑输出逐字贴出 |
| 5 先懂再判 | 各维先列意图卡片（见各维开头） |
| 6 不凭记忆 | README/CHANGELOG 声明均重验（如「九项」实跑为 10、「78→95 测试」实跑为 78） |
| 7 声明/强制分开 | D3/D10、D5 均区分提示词级与机器级计分 |
| 8 时间写实 | 基线时间 `date` 现取：`Tue Oct 20 14:12:36 CST 2026` |
| 9 诚实勘误 | 见第十六节（含前序子代理抽取核验的误差说明） |

**记为未运行 / 不可复现的项**：无强制要求而我未跑的命令（如 `doc_chain.py <feature-dir>` 对业务仓的活面扫描）明确标注，未声称通过。网络检索权归 R7，本报告其余维度未使用网络。

---

## 二、D1 架构与设计一致性（8/10）

**意图卡片**：职责=保证「宿主原生、无第二套 CLI」成立、五面真实分离、fail-closed 落到工具层；自述契约=README:7「不调用独立 agentflow CLI」、design-decisions §1「不发展 TUI/Provider/第二套 loop」；消费者=宿主（加载 agents/skills/manifest）+ Supervisor（调门）。

**亮点（证据）**
- 无第二套 CLI/运行时/编排：`grep -ri "runner|replay|subagent|orchestrat" tools` 命中均为 `git`/`ruff`/`mypy`/`unittest`/`doc_chain` 等工具性 subprocess，**无 agent loop**。
- fail-closed 工具层坐实：`gate/schema.py:286 SUPPORTED_SCHEMA_KEYWORDS` + `:351 check_schema_keywords`（未实现关键字一律拒载，docstring `:284`「pretending to check it (fail-closed)」）；`gate/manifests.py:122 validate_runtime_freshness` 逐字节比对；`gate/manifests.py:38-74` protected 反向校验（声明路径须存在否则 FAIL）。
- 五面分离真实：交付/契约门/记录/文档/打包边界清晰，记录面为纯 Markdown 无被依赖代码。

**硬伤（证据）**
1. **「九项检查」声明 vs 实跑「10 项」**：`tools/lab/validate.py:340-351` 的 `all` 列表 = `schemas, examples, artifacts, protected, manifests, docs, tests, doc_chain, doc_chain_live, lint`（10 项，第 10 项 `lint` 跑 ruff+mypy，`:339`）。README:51-54、AGENTS.md:14-19、system-guide.md:225-232、quickstart.md:48、tools/lab/README.md:11-67 均列九项（无 `lint`）。实跑：`9 PASS + FAIL lint`（ruff/mypy 未装）。CHANGELOG 既写 `9×PASS`（行 146/161/342…）又写 `10×PASS`（行 133/237/289）。**核心承诺局部落空**。
2. **`归档/` 目录不存在 + `rejected` 状态死条款**：`ls docs/issues` 无 `归档/`；`grep status:rejected` 全仓 0 条；但 AGENTS.md:85、system-guide.md:33 仍声称其存在、状态机含 `→rejected→归档/` 分支。
3. **未声明宿主目录 `.commandcode/`**：出现在根目录但 README/index/AGENTS 均未声明——设计面描述歧义。

---

## 三、D2 门禁有效性（8/10，权重 ×2）

**意图卡片**：职责=验证「确定性检查门」真能拦违规；自述契约=`validate.py all` 九项、各单项守什么、`isolation.check-diff` fail-closed；消费者=Supervisor 接受产物前。

**实跑（附录 A 全文）**
- `validate.py all` → 10 子项，9 PASS + `lint FAIL`（ruff/mypy 未安装）。**注意：基准 Prompt 自身也写「九项」，与代码不符，属同样的文档漂移。**
- `validate.py installed` → PASS（exit 0）
- `doc_chain.py --self-test` → 63/63 PASS
- `python3 -m unittest discover -s tests` → 78 OK（非 CHANGELOG 声称的 95）
- `validate.py manifests` → PASS（五份 manifest 均 0.11.0）
- `validate.py docs` → PASS（链接/版本散文守卫）

**5 项变异实验（副本 `/tmp/agentflows-eval-copy`，均令门变红）**
| 变异 | 目标门 | 退出码 | 结果 |
|---|---|---|---|
| A. schema 加未实现关键字 `exclusiveMinimum` | `schemas` | 1 | 红（关键字子集拒载） |
| B. 真实记录 `status: verified`→`rejected` | `artifacts` | 1 | 红（非法状态） |
| C. `marketplace.json` `plugins[0].version` 0.11.0→0.11.1（runtime 同步） | `manifests` | 1 | 红（`version '0.11.1' disagrees with plugin.json '0.11.0'`） |
| D. `protected-paths.txt` 加不存在路径 | `protected` | 1 | 红（反向校验 FAIL） |
| E. README 引入断链 `docs/zzz-nonexistent-xyz.md` | `docs` | 1 | 红（相对链接不可解析） |

**隔离 fail-closed 实验（`/tmp/agentflows-iso-copy`）**
- 干净候选 → `blocked:[]`（exit 0）✅
- base 以 `-` 开头（`--base=-badbase`） → 防护 exit 1 ✅
- 改动受保护文件 `schemas/bug-record.schema.json` → `blocked` + exit 1 ✅
- `schemas/` 下未跟踪非 ASCII 文件 `测试.json` → `blocked` + exit 1 ✅
- **过阻发现**：gitignored 的 `__pycache__`（置于 `tools/lab/gate/`）被 `check-diff` 判为 `blocked` + exit 1（`:92` `git ls-files --others --ignored` 未排除忽略项），与基准 Prompt「__pycache__ 出现但不被阻塞」的坑注**相反**——实为偏严的过阻，非 fail-open，但会阻断含缓存的合法候选。

**失效模式 / 扣分项**
- `lint` 在缺 dev-deps 环境必红 → 「九项全绿」在当前默认环境**不成立**；即便修复计数，干净环境也无法 10×PASS。
- 门判别力边界：`doc_chain.py` 只扫**业务仓 feature 链**，不扫本仓自身设计文档——「自测绿 ≠ 本仓文档无漂移」。

---

## 四、D3 代码质量与安全（8/10）

**意图卡片**：职责=`tools/lab/` 各工具的真实 bug/异常逃逸/fail-open/注入/非 ASCII 处理 + `tests/` 覆盖真相；自述契约=异常 typed 且转化或重抛；消费者=CI/ Supervisor。

**亮点（证据）**
- 全仓 `tools/lab/` **零裸 `except:`、零 `TODO/FIXME/XXX/HACK`**（grep 实证）。
- subprocess 调用均显式 `check=False` 并据退出码分支（`isolation.py:92`、`doc_chain.py:673`、`mutate.py:336`），非静默成功。
- `mutate.py` 变异测试：只读真实树、变异落 `cp -R` 副本且事后删除、anchor 必须唯一命中、改写后 `ast.parse` 复验、先跑 control 再信结果——工程扎实。
- `isolation.py` `check-diff` 对 `base` 以 `-` 开头、非 ASCII、未跟踪/忽略文件均 fail-closed。

**硬伤（证据）**
1. **`record_store.query` 畸形 FTS5 表达式未捕获**：`record_store.py:76-84` `MATCH ?` 在表达式语法错时抛 `sqlite3.OperationalError`，无 try → 崩溃（非 fail-open，但缺健壮性）。
2. **`doc_chain.py` 判别力范围局限**：仅校验 feature 链，不覆盖本仓 `docs/` 设计文档漂移（见 D2 失效模式）。
3. **`mutate.py _op_drop_enum_member` 脆弱**：依赖枚举元组末成员恰为字符串字面量且位于行尾的正则（`:234`），对他处枚举形态可能误判为「无效」——属可维护性风险，非安全面。

---

## 五、D4 代码工艺与可读性（9/10）

**意图卡片**：职责=整洁/注释/命名/一致性（答「好不好读改」）；自述契约=全域风格统一；消费者=后续维护者。

**亮点（证据）**
- 命名全域 snake_case，`_validate`/`check_diff` 等表意准确；布尔无歧义。
- 注释解释「为什么」：`doc_chain.py:409-417` 详解轻量模式豁免的来龙去脉与「降级路径曾在纸面」的历史坑；`isolation.py:46-47` 注释中文路径 C-quote 误判根因。
- **`partial` 状态纪律在 14 角色收敛一致**：抽样 `reviewer.md:110`、`bug-fixer.md:26`、`evaluator.md:20`、`release-governor.md`、`technical-director.md:22` 等均写「被截断的运行绝不报告为完成 / partial 绝不是批准」——**非复制漂移，是收敛的契约语言**，正面反证了基准 Prompt 担心的「两文件复制粘贴」旧疾已修复。
- 无死代码、无空壳函数；`mutate.py`/`doc_chain.py` 的 self-test 即活文档。

**扣分项（证据）**
- `doc_chain.py` 单文件 ~1100 行，含 linter + 63-case self-test，函数长度不均（如 `lint` ~200 行）；可读但偏重，可考虑拆分 self-test 为独立模块。属 7–8 微调，不扣分至 8 以下。

---

## 六、D5 Agent/Skill 契约质量（8.0/10）

**意图卡片**：职责=14 角色 frontmatter×正文×路由×schema×模板交叉一致；自述契约=`validate.py docs` 断言；消费者=宿主路由 + 委派规则。

**亮点（证据）**
- 14/14 角色 `frontmatter.name` == 文件名，由 `validate.py docs` 机器校验（exit 0）。
- 14/14 `tools`/`disallowedTools` 与正文「产物归属表」「只读」自述互相印证，无矛盾。
- `skills/agentflow/SKILL.md:66-72` 判断词（小改动/risky/相同原因）**可判定且优先级已裁决**。
- `evidence-and-release.md` 与 `release-record.schema.json` 的 `allOf` 分支逐字一致。
- 仓库诚实区分声明级/强制级：`AGENTS.md:67-68` 明示 `tools`/`disallowedTools` 由宿主强制、`maxTurns` 只声明未验证。

**高优先级发现（证据，声明级→机器级未强制）**
1. **【-1.0】`templates/testing/run.md:41` 与 `test-records.md:36` 声明 `BUG-*` id，而 `test-run.schema.json`/`review.schema.json`/`recurrence.schema.json` 机器强制 `^ISS-\d{4}-\d{3,}$`** → 照契约字面产出必被自己的门拒（双处漂移未被单点改正覆盖）。
2. **【-0.5】`validate.py docs` 第 5 组断言「中文镜像与英文契约文档段落对应」（`AGENTS.md:27`、`docs.py:184` docstring）代码未实现且无英文镜像目录** → 死断言。
3. **【-0.5】`improve/SKILL.md:38` 称「可编译改进契约只有 candidate/release-record 两份」，但 `validate` 的 `IMPROVEMENT_SCHEMA_NAMES` 还含 `episode.schema.json`**（门实际校验它）。

> 说明：以上均属「提示词级声明」层，schema 机器强制本身有效；按铁律 7 不因「声称会拦」记「已强制拦截」。

---

## 七、D6 结构合理性（8/10）

**意图卡片**：职责=静态组织正确性（布局/依赖方向/可发现性）；自述契约=五面目录约定；消费者=新接手者。

**亮点**：布局合理、边界清晰；**可发现性实测 5 任务均 1 跳**（改角色→`agents/`、查缺陷→`docs/issues/`、抄模板→`skills/agentflow/templates/`、查批次→`docs/features/`、跑校验→根 `validate.py`）；命名规则成文且基本遵守；`examples/` fixture 与 `schemas/` 单源（runtime 为生成+新鲜度门守护）。

**硬伤**
1. 同 D1 硬伤 2：`docs/issues/归档/` 声明目录不存在（结构性断链）。
2. `.commandcode/` 未声明目录出现在根（D1 硬伤 3）。
3. `validate.py all` 文档计数（九项）与代码（10 项）不一致（跨 D1/D6）。

---

## 八、D7 逻辑链路（8/10）

**意图卡片**：职责=动态流转闭环（每步输入输出契约、链间切换点、状态机完备）；自述契约=十步/三链/13 步；消费者=执行 agent。

**亮点**：主工作流十步、bug 链/文档链/改进环三链、切换点、状态机文本齐备；`docs/design-decisions.md §3` 已诚实披露历史漂移。

**硬伤（死条款 / 隐性惯例）**
1. `rejected`/`归档/` 状态分支从未触发（死条款，证据同 D1 硬伤 2）。
2. 改进环第 8 步「对照」在记录中未真实发生（死条款）。
3. 隐性惯例：「被拒」记录却标 `verified`（如 ISS-2026-09-15-真树故障注入checkout还原丢工作/006 实质为被拒/证伪，状态仍 verified）——文本未定义此路径，记录中真实发生。

---

## 九、D8 文档与记录活性（7/10）

**意图卡片**：职责=活性（在不在更新）；自述契约=index 与实际同步、链接可解析；消费者=维护者/审计者。

**活性四张清单**
- **链接**：`validate.py docs` PASS → 相对链接基本可解析；但 CHANGELOG 含退役路径散文（如旧 `records/` 树引用，已迁 `docs/`）。
- **冗余**：`docs/design-decisions.md` 由三份设计文档合并，部分背景重述。
- **矛盾**：CHANGELOG 九项/十项混用、`78→95` 测试数与实跑 78 矛盾（D9 同）。
- **状态流统计**：56 issue（40 verified / 16 open）；`归档/` 目录为空 → 归档规则空转；episode 持续至 2026-10-18（活）；`docs/PENDING-DECISIONS.md` 56 行（被维护）。

**结论**：记录面活的，但归档机制空转、CHANGELOG 计数不实，压到 7。

---

## 十、D9 治理与发布闭环（7/10）

**意图卡片**：职责=口径诚信与闭环；自述契约=`measurement:none` 诚信、角色分离机器 vs 提示词、发布=人工批准；消费者=发布治理。

**亮点（实证）**
- `measurement:none` **诚信执行**：`skills/improve/SKILL.md:35/38/53/55` 明确「一条记录不能同时声称 none 与 better」；实跑 grep：episode 记录中 `measurement:none` 与 `better` **无同文件共存**（4 处同现均为 docs 规则解释，非记录违规）→ 记录级诚信成立。
- 角色分离诚实自承：`SKILL.md:24`「除非宿主确实强制分离的工具白名单与工作区，否则角色分离只是流程性的。绝不因为候选的提示词说不编辑受保护文件，就声称它被隔离。」
- 五份 manifest 版本对齐 0.11.0（`validate.py manifests` PASS）。

**硬伤**
1. **发布审计链断裂**：episode `EP-2026-09-22-001` 等引用 `releases/0.8.5.json`/`0.8.6.json`/`0.8.7.json`，但 `docs/releases/` **0 个 .json**（仅 `pending-test.md`/`todo.md`）；per-version 发布 JSON 随 0.11.0 瘦身批停用，致「release governor approved/promoted」声明不可核验（D11 同）。
2. **CHANGELOG 计数不实**：0.11.0 段称「单元测试 78→95」，实跑 78（95 为被后续「还原提交版」撤销的临时态，CHANGELOG 未讲清净结果）。

---

## 十一、D10 安全与权限边界（7/10）

**意图卡片**：职责=worker write_scope 是提示词级还是机械级；自述契约=`check-write-scope.sh` + `gate/` 覆盖、退出码 fail-closed；消费者=Supervisor 接受产物。

**亮点（实证）**
- `check-write-scope.sh` 已修中文路径误判：`:48` 用 `git diff -z` 原始路径，`set -eu`，git 失败 fail-closed（exit 1）。`-z` 直击 ISS-2026-10-10-写范围dot-scope静默不匹配 同根因。
- isolation `check-diff` 对改动受保护文件/非 ASCII/`-` base 均 fail-closed（D2 实验 ✅）。
- `contracts.md` 硬边界 14 条中机械强制部分（protected 反向校验、isolation）经实跑坐实。

**硬伤（残余风险）**
1. **scope=`"."` 即全树放行**：`check-write-scope.sh:72`「`.` 是整棵树约定写法…直接放行」→ 声明 broad scope 即绕过检查。机器强制有效但**可被提示词级 scope 声明轻易失效**，恰是 README 自承「宿主不对 Write 强制路径约束」的残余风险，无机器缓释。
2. 凭据纪律（会话注入、不落记录/脚本/日志）在文档与工具间一致，但依赖人工。

---

## 十二、D11 实现的效果（7/10）

**意图卡片**：职责=疗效（更新是否产生可验证结果）；自述契约=走完全流程占比/证据密度/评审轮次；消费者=方法本身演进。

**疗效取证（统计 + 抽查）**
- **走完全流程 issue**：40/56 verified = **71.4%**（抽查 ISS-2026-09-14-claude-json-schema-被拒/005/026，verified 属实）。
- **episode 实质轮次**：41 episode 中 19 个（46%）有非空 `review_roundtrips`（抽查 `EP-2026-09-22-001`：3 轮，含 2×`changes_requested`+1×`approved`，属实）。
- **`evidence_ref` 密度**：41 episode **0 个**填充顶层 `evidence_ref`（字段存在但恒空；内部 `evidence[]`/`signals[].evidence_ref` 有内容）→ schema 字段空转。
- **recurrence 台账**：9 类（`crammed-contract-table-form` 等），档位 `recurred`(2 occ)/`single`(1 occ)，无 `escalated`。
- **独立评审真实轮次 & changes_requested**：抽查 EP-2026-09-22-001 含 `changes_requested` 两轮 → 评审非走过场。
- **改进环产出**：确产出自举候选（0.8.5 ui 轨经 evaluator+reviewer+release-governor 闭环），但**发布 JSON 被删**（D9 硬伤 1）→ 晋升/拒绝分布不可全考。
- **门禁拦截证据**：CHANGELOG 0.11.0「门健全批」记「51 变异=杀死 51/存活 0」——门红后修复闭环有记录。

**结论**：主流真实、个别注水/不可考（`evidence_ref` 空、发布记录删）→ 7。

---

## 十三、D12 存在意义（7/10）

**意图卡片**：职责=价值主张（为何存在、成本收益比、砍什么更好）；自述契约=确定性门+受治理发布+记录即编译不可替代；消费者=目标用户（单人/小团队开发者）。

**场景对照（有/无 agentflow）**
- 跨层 feature（如 office-agent 文档链）：无 → 缺 contract 表/失败分支/状态机，且「说完就走」；有 → doc_chain 门强制密度下限（ISS-2026-09-20-文档链首轮密度缺口/031/034 即此类缺陷被拦）。
- 反复缺陷（crammed-contract-table 复发 2 次）：无 → 同类错误重复；有 → recurrence 台账定级、改进环加固。

**真实空白创新点（R7 实证）**：**「方法自改进时的防自篡改」**——`improve/SKILL.md:24/55` 明确「候选不得批准自己的证据」「none 与 better 不可同称」，竞品（superpowers/BMAD/spec-kit）均无此机制，回应了「agent 改自己评估规则」的具名风险。

**成本收益比**：material 改动从 Intake 到 Decision 需 ~10 产物 + 9–10 门 + 多角色会（Investigator/Fixer/Reviewer/Recorder/evaluator/governor）。对**单人开发者**仪式成本偏高；对**小团队/受监管场景**划算。

**砍什么更好**：① 删 `归档/` 死约定（或落地）；② 弱化对外「证据驱动改进」叙事（与 `measurement:none` 矛盾）；③ 对 trivial 单步明确走 SKILL 跳过划线（已合理）。

**硬伤**：对外头条「evidence-driven improvement」与 `measurement:none` 现状矛盾，不改会被竞品/用户一眼识破。

---

## 十四、D13 竞品比对（8/10）

**意图卡片**：职责=横向对标、找真实差异化；自述契约=对比矩阵含确定性强制力/治理/记录审计列；消费者=对外叙事。

**对比矩阵（节选，全矩阵见 R7 报告）**

| 竞品 | 形态 | 确定性强制力 | 与 agentflow 重叠度 |
|---|---|---|---|
| superpowers | 方法论+slash | 提示词级检查清单 | 中（角色/步骤） |
| BMAD-METHOD | 方法论+模板 | 提示词级 | 中（文档链） |
| spec-kit | CLI+多 agent | **语义级**合规门（constitution） | **高**（制品即契约、bug 扩展≈bug 链） |
| Claude Code subagents | 宿主能力 | 宿主工具白名单 | 中（角色委派） |
| Codex AGENTS.md | 约定文件 | 提示词级 | 低-中 |
| OpenHands/CrewAI/LangGraph | 框架/平台 | 运行时编排 | 低（形态不同） |

**真实空白创新点**：防自篡改 + 机器编译证据记录 + claims 台账（竞品均无）。

**叙事建议（R7）**：押注「治理/审计唯一性」，弱化「角色库/文档链」宣传（与 spec-kit 高度重叠）。

**硬伤**：同 D12 硬伤 3——头条叙事与 `measurement:none` 矛盾。

---

## 十五、缺口清单表

| # | 缺口 | 实证 | 压住哪维 | 解锁条件 | 状态 |
|---|---|---|---|---|---|
| 1 | 「九项」声明 vs 实跑「10 项」（含未文档化 `lint`） | validate.py:340-351 / README:51-54 / CHANGELOG 混用 | D1/D2/D6 | 统一为 10 项并文档化 `lint`，或将其移出 `all` | 待拍板 |
| 2 | `归档/` 目录不存在、`rejected` 状态死条款 | `ls docs/issues` 无归档 / grep rejected=0 | D1/D6/D7 | 落地目录+状态，或删除相关约定 | 待拍板 |
| 3 | 发布 JSON 被删致审计链断 | `docs/releases/` 0 个 .json，episode 引用 0.8.5/6/7.json | D9/D11 | 以 episode 为唯一审计源，或恢复发布 JSON | 待拍板 |
| 4 | `evidence_ref` 顶层字段全空 | 41 episode 0 填充 | D11 | 填实关键 episode，或删字段 | 待拍板 |
| 5 | CHANGELOG 测试数 78/95 矛盾 | 实跑 78；CHANGELOG 称 95 | D8/D9 | 澄清净测试数=78 | 待修 |
| 6 | `check-write-scope` scope=`"."` 全树放行 | check-write-scope.sh:72 | D10 | 机器校验 scope 不得为 `.`，或要求窄 scope 声明 | 待修 |
| 7 | `lint` 门在干净环境假红 | validate.py all 实跑 FAIL lint（ruff/mypy 缺） | D2 | 环境说明或 dev-deps 默认，或默认跳过并标注 | 待修 |
| 8 | `.commandcode/` 未声明目录 | 根目录出现，设计面未提 | D6 | 确认归属并补入/排除 | 待查 |
| 9 | `validate.py docs` 第5组断言未实现（中英文镜像） | docs.py:184 docstring / AGENTS.md:27 | D5 | 实现或删断言 | 待修 |
| 10 | 模板 `BUG-*` id 与 schema `^ISS-…$` 强制冲突 | run.md:41 / test-records.md:36 | D5 | 统一为 `ISS-` 或放宽 schema | 待修 |
| 11 | isolation 过阻 gitignored `__pycache__` | isolation.py:92 | D2/D10 | `ls-files --others --ignored` 排除忽略项 | 待修 |
| 12 | 对外「evidence-driven」叙事 vs `measurement:none` | SKILL:55 / D12 硬伤 | D12/D13 | 叙事改为「证据驱动但方法级不量化」 | 待拍板 |

---

## 十六、勘误节

- **本轮新发现误差**：前序子代理 R1/R4/R7 报告于上一个会话产出，经本会话从 transcript 抽取核验；抽取时 R5（D8/D11）报告与 Supervisor 自身推理文本混杂，已改由 Supervisor 直接实跑重做 D8/D11，**未采用被污染的抽取文本**。R1/R4/R7 抽取文本经污染检测（grep `Now I got`/`function_call_result`）= 0，判定干净可用。
- **前序自身结论**：R1 已声明「首次独立评测，无前期自身结论需更正」，且复核「五份 manifest 含 .zcode/.claude/.codex 各一份」经 `ls -la`+通读**证实成立**。
- **Supervisor 自查**：实跑 `unittest` 得 78（非 CHANGELOG 95），修正了对 CHANGELOG 计数的轻信；实跑 `validate.py all` 得 10 项（非文档九项），修正了对「九项」声明的采信。
- **抽查规模**：本报告直接实跑命令 9 类、变异实验 5 + 隔离实验 4、文件通读 ~20（含 tools/lab 全量源码、skills、schemas、docs、episodes 抽样 3、reviews 结构），覆盖 13 维证据需求。

---

## 十七、最终裁决

**设计–执行差距判断**：设计声明（宿主原生、fail-closed、记录即编译、受治理发布）**主体兑现**，机器级门有效、代码工艺优秀、治理口径诚实。差距集中在**声明与实现的系统性文档/计数/审计链断裂**（门项数、归档机制、发布记录留存），均非架构性缺陷，属「已定位、有解锁路径」。

**存在意义结论**：值得存在，核心差异点=**方法自改进时的防自篡改 + 机器编译证据**；对受监管/小团队场景价值明确，对单人开发者仪式成本偏高。建议对外叙事锚定治理/审计唯一性。

**最高杠杆下一步（按 ROI）**：
1. 修缺口 #1（门项数统一）→ 消除六处文档自相矛盾，成本极低、影响面最广。
2. 修缺口 #2/#3（归档落地 或 以 episode 为唯一审计源）→ 恢复记录面闭环与可审计性。
3. 修缺口 #12（叙事与 `measurement:none` 对齐）→ 避免对外叙事被一眼识破。

**拍板项清单（含推荐默认值）**

| 拍板项 | 推荐默认值 | 框定证据 |
|---|---|---|
| P1 门项数口径 | 改为「10 项」并文档化 `lint`（或移出 `all`） | 缺口 #1，validate.py:340-351 |
| P2 归档机制 | 落地 `docs/issues/归档/` + `rejected` 状态（优先），否则删约定 | 缺口 #2，D1/D6/D7 |
| P3 发布记录留存 | 以 `episodes/` 为唯一审计源，删除 release JSON 引用 | 缺口 #3，D9/D11 |
| P4 `evidence_ref` | 填实关键 episode 的跨引用，否则删字段 | 缺口 #4，D11 |
| P5 评测装置口径 | **维持 `measurement:none`，不复活评测装置**（基准 Prompt 禁止提议复活） | SKILL:30/53，design-decisions §3 |

---

## 附录 A：实跑命令与逐字输出

**基线（开工三件事）**
```
$ date
Tue Oct 20 14:12:36 CST 2026
$ git -C <repo> status --short      # (clean tree, 无输出)
$ git -C <repo> log --oneline -5
20724c0 (HEAD) ...  (最近提交)
$ cp -r <repo> /tmp/agentflows-eval-copy   # 保留 .git
$ cp -r <repo> /tmp/agentflows-iso-copy
```

**门实跑（真实仓库）**
```
$ python3 tools/lab/validate.py all
[schemas] PASS  [examples] PASS  [artifacts] PASS  [protected] PASS
[manifests] PASS  [docs] PASS  [tests] PASS  [doc_chain] PASS
[doc_chain_live] PASS  [lint] FAIL (2 error(s): ruff/mypy not installed)
EXIT=1   # 10 子项，9 PASS + lint FAIL

$ python3 tools/lab/validate.py installed      # PASS, EXIT=0
$ python3 tools/lab/doc_chain.py --self-test   # 63/63 PASS, EXIT=0
$ python3 -m unittest discover -s tests        # Ran 78 tests, OK, EXIT=0
$ python3 tools/lab/validate.py manifests      # PASS (五份 0.11.0), EXIT=0
$ python3 tools/lab/validate.py docs           # PASS, EXIT=0
$ python3 tools/lab/validate.py report         # 56 issue 列表 (40 verified/16 open)
$ python3 tools/lab/validate.py recurrence     # 9 类台账
```

**5 项变异（副本 /tmp/agentflows-eval-copy，均门变红，EXIT=1）**：A schema 加 `exclusiveMinimum`→schemas 红；B 记录 `status verified→rejected`→artifacts 红；C `marketplace.json plugins[0].version` 0.11.0→0.11.1（runtime 同步）→manifests 红（`version '0.11.1' disagrees with plugin.json '0.11.0'`）；D `protected-paths.txt` 加不存在路径→protected 红；E README 引断链→docs 红。

**隔离 fail-closed（副本 /tmp/agentflows-iso-copy）**：干净候选→`blocked:[]` EXIT=0；`--base=-badbase`→EXIT=1；改 `schemas/bug-record.schema.json`→`blocked` EXIT=1；`schemas/测试.json` 未跟踪→`blocked` EXIT=1；gitignored `__pycache__`→**过阻** `blocked` EXIT=1（偏严，非 fail-open）。

**副本状态**：`/tmp/agentflows-eval-copy`、`/tmp/agentflows-iso-copy` 均未清理（含受保护副本；如需清理可 `rm -rf` 二者）。

---

## 附录 B：元评审结论（证据链审计 / R8）

本会话 Supervisor 兼任 R8，对证据链做抽样核对（目标 30%，实际覆盖：全部实跑输出由 Supervisor 亲跑；R1/R4/R7 抽取报告经污染检测后采用）：

- **可核实证据**：门实跑、5+4 变异、manifest 版本、unittest 78、measurement 诚信 grep、release JSON 缺失——均经独立命令复现，与报告一致。
- **验证缺席型结论**：无「有结论无实跑」项；唯一未跑的 `doc_chain.py <feature-dir>` 活面扫描已显式标注未声称通过。
- **覆盖清单一致性**：见附录 C；未读项均有原因。
- **评分锚定**：13 维分数均附锚点+硬证据；D2 权重 ×2 已计入综合分。
- **残差风险**：R5（D8/D11）因抽取污染改由 Supervisor 重做，未采用前序文本——此点已在第十六节勘误。

---

## 附录 C：阅读覆盖清单

**排除项（全域）**：`.git/`、`__pycache__/`、`*.pyc`、`packaging/runtime/`（读生成器 `build_runtime.py` 替代）。

**R1（D1/D6/D7）**：已读 README/AGENTS/index/CHANGELOG(抽样)/design-decisions/system-guide/quickstart/PENDING-DECISIONS/SKILL.md/五份 manifest/packaging/protected-paths + `ls -R`。未读：CHANGELOG 全文（105KB，仅 grep 关键主张）、episodes/reviews/schemas 体（结构+门 PASS 替代）。

**R2（D2）**：已读 tools/lab/validate.py 与 `gate/` 全模块（schema、manifests、docs、workspace、isolation、common、checks、examples、plan、installed、records、testing、reports）+ 实跑全部门与变异。

**R3（D3/D4/D10）**：已读 tools/lab 全量源码（validate/doc_chain/isolation/artifact_digest/record_store/trend/counts/mutate + gate/ 全模块）、tests/、check-write-scope.sh。未读：`artifact_digest.py`/`trend.py`/`counts.py` 仅抽读（非门核心路径），记为抽样。

**R4（D5）**：已读 agents/ 14 份 + skills/agentflow 全量 + skills/improve 全量 + schemas/6 + README。抽取报告污染检测通过。

**R5（D8/D11）**：Supervisor 亲跑 `validate.py report/recurrence`、issue 状态统计、episode 41 全量 JSON 解析（evidence_ref/review_roundtrips）、reviews 结构、抽样 EP-2026-09-22-001 全文。未读：docs/ 全量散文（仅结构+关键文件）。

**R6（D9）**：已读 skills/improve/SKILL.md、CHANGELOG(抽样)、docs/releases/、五份 manifest、measurement 诚信 grep。未读：docs/trend.jsonl（空/不存在）。

**R7（D12/D13）**：已读 README/AGENTS/index/design-decisions/CHANGELOG/PENDING/SKILL(agentflow+improve)/system-guide/quickstart/manifest/packaging + 网络检索竞品（每条附 URL+日期 2026-10-20）。抽取报告污染检测通过。

---

*报告结束。全文未对被评测仓库执行任何写操作；所有结论附文件路径:行号或「命令+退出码+逐字输出」证据。复制副本保留于 `/tmp/agentflows-eval-copy` 与 `/tmp/agentflows-iso-copy`。*
