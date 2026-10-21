# Agentflow 项目评测报告（2026-10-20）

> **评测者**：Agentflow 评测组 Supervisor + 8 个只读评测角色（R1–R8），各自独立上下文，以并行独立子代理执行（R1–R7 并行，R8 在其后串行审计证据链）。
> **被评测 revision**：`20724c0`（main，origin/main 同点），工作树干净（`git status --short` 零输出）。
> **基线时间**：2026-10-20 14:12:36 CST（`date` 现取）。
> **声明**：本报告未修改被评测仓库任何既有文件。本文件本身是评测结束后新增的交付件（先例：根目录 `AGENTFLOW-EVALUATION-2026-10-12.md` 等），写入时间在全部实跑与变异实验完成之后，不构成对被评测内容的污染。全部评测过程只读；变异实验仅在 `/tmp` 副本上进行。

---

## 〇、总览

### 十三维分数表（D2 权重 ×2，默认口径）

| 维度 | 分数 | 一句话锚点 |
|---|---|---|
| D1 架构与设计一致性 | **8** | 声明基本有机器支撑、fail-closed 落到工具层细节；三处声明-实现漂移（九/十项、deferred 校验、CI lint） |
| D2 门禁有效性（×2） | **8.5** | 十一项门全实跑、11 组变异全红且报错精确、check-diff 全边界 fail-closed；trend.py 崩溃与 counts.py 游离门外压住满分 |
| D3 代码质量与安全 | **8** | 门禁链 fail-closed 纪律与负例测试真实扎实；gate 之外两个工具零测试、异常逃逸集中在辅助脚本 |
| D4 代码工艺与可读性 | **7.5** | 注释文化全域顶级、零 TODO 零死代码；两个巨型函数（322 行/201 行）与围栏逻辑三处复制 |
| D5 Agent/Skill 契约质量 | **7** | 角色与 schema 零系统性漂移、机器门 PASS；但存在「照指令产出必被自己的门拒」组合（BUG-* vs ISS-* 等） |
| D6 结构合理性 | **8** | 五面相聚、可发现性实测 5 任务全 ≤2 跳；双看板矛盾与根目录滞留文件 |
| D7 逻辑链路 | **7** | 十步闭环、状态机文本完备且记录面真实走过；门旁路靠隐性惯例、死条款簇存在 |
| D8 文档与记录活性 | **7** | 主流记录真实且机器门在跑；最近一次提交在声称「同步」的同时留下十处矛盾 |
| D9 治理与发布闭环 | **8** | 五大治理声明全部有硬证据；3 处未立案的活面文案失真（基线对照残留等） |
| D10 安全与权限边界 | **8** | 候选门机械强制且实测 fail-closed（中文路径正确）；唯一实质 fail-open 是被 ignore 的写入 |
| D11 实现的效果 | **6.5** | 过程疗效有硬实证（评审真推拒、门真拦截）；方法疗效按仓库自述「未测」（G1 样本 1、改进环停用） |
| D12 存在意义 | **6** | 价值真实但集中在三类场景；确定性门主要绑定插件仓自身，不随方法旅行到目标仓 |
| D13 竞品比对 | **8** | 主要竞品全覆盖、差异化结论有据；个别基础数字经 R8 更正 |

**综合分（D2 计两遍）**：(8 + 8.5×2 + 8 + 7.5 + 7 + 8 + 7 + 7 + 8 + 8 + 6.5 + 6 + 8) ÷ 14 = 106 ÷ 14 ≈ **7.6 / 10**

**备选权重（D2 计一遍）**：97.5 ÷ 13 ≈ **7.5 / 10**。两版差异 0.1——D2 是全仓最硬的一维，加权抬升有限，说明短板不在门本身，而在「门照看的文档面活性」与「方法疗效未证」。

### 一句话裁决

**门的成色是真的，疗效的账是欠的**：确定性门禁体系经 11 组变异实证无 fail-open、声明与机器高度一致；但 HEAD 提交的「同步」声称与事实矛盾、改进环停摆后治理机器在空转、方法本身的效果从未被测量。

### 对四个问题的直接回答

**1. 它的门和契约，是否真的抓住它们声称抓住的违规？**
抓住的是机械级的那部分——且抓得很真：schema 未知关键字拒载（`gate/schema.py` 关键字白名单门）、受保护路径 diff 级拦截（`isolation.py check-diff`，`-` base / 非 ASCII / 未跟踪文件全 fail-closed）、manifest 版本与生成树逐字节新鲜度、文档断链。11 组变异实验全部变红且报错精确（附录 A）。但提示词级契约大量未被机器覆盖：`test-records.md` 声称 findings 交叉校验「校验器强制」，实际 deferred（`gate/workspace.py:357-361` 自认）；`gate/docs.py:183-185` docstring 声称断言「中文镜像段落对应」，代码内零实现；14 条硬边界中 1/3/9/10/11 纯提示词级。

**2. 它的结构与链路，是否合理、是否闭环？**
静态结构合理：五面相聚、依赖无环、可发现性实测达标（改角色/查缺陷/抄模板/查批次/跑校验全部 ≤2 跳）。动态链路文本闭环且记录面真实走过，但存在三类裂缝：门旁路（「用户授权实施」）是隐性惯例而非条款；双看板（批次 README vs 计划看板）因同步时点无条款而漂移——HEAD 提交即现行犯；死条款簇（rejected→归档、episode rejected/failed、candidate/release-record 全部零实例）。

**3. 它实际跑出了什么效果，以及为什么值得存在？**
过程疗效可证：56 条 issue 中 40 条 verified（71.4%，但 25 条为 2026-10-19 批量复审补验）；评审 changes_requested 率 50%，证明独立评审真在推拒而非橡皮章；门红后修复有逐字记录；两次用户反馈形成四步闭环。方法疗效未证：G1 实验自述「样本量为 1，不构成结论」，改进环产出 1 候选 0 晋升后停用，trend 工具对现行记录面已崩溃（exit 1）。

**4. 它声称的核心差异点（确定性门 + 受治理发布），兑现到哪一步、还差什么？**
「确定性门」兑现约八成——对本仓自身有效（变异实证），但门不随方法旅行：目标仓拿到的只有提示词纪律 + `check-write-scope.sh` 事后对照，而该脚本存在 .gitignore 盲区。「受治理发布」兑现约七成——none/better 互斥是 schema allOf 编译级强制、晋升规则四处逐字一致，但 none 支发布记录零实例（空转面）、评测装置裁撤后 improve 机器治理着一个不产仪器化证据的流程。**还差的一步：把「门对目标仓也生效」的最小工具化，或诚实把对外叙事收缩到「本仓自身的门」**。

---

## 一、铁律执行自证

- 实跑命令全集（真实仓库，只读）：`git status --short`、`git log --oneline -5`、`date`、`validate.py all`（9 项 PASS + installed PASS + lint 环境性红）、`validate.py docs / manifests / installed / protected` 单项、`doc_chain.py --self-test`（63/63）、`doc_chain.py <feature-dir>`（两批次 PASS）、`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`（78 tests OK）、`python3 tools/lab/trend.py`（**exit 1，崩溃**）、`python3 tools/lab/counts.py`（OK）、`check-write-scope.sh`（含中文路径用例）。逐字输出存于 `/tmp/agentflow-eval/R2-gates.md`、`R3-code.md`。
- 变异实验：11 组，全部在 `/tmp/agentflows-eval-copy` 上 cp 备份-还原完成，无 git checkout（附录 A）。
- 记为未运行及原因：`validate.py lint` 子项在真实仓库（ruff/mypy 缺失，会写缓存目录，违只读铁律——R2 在副本环境定性为环境性红，非静默）；CI 行为未实跑（R1「CI 必红」按 R2 保守口径记为「高概率、未实跑」）。
- 执行事故披露：开工建副本时 `/tmp/agentflows-eval-copy` 已存在旧 revision（f76094a）副本，`cp -r` 成为嵌套复制；R2 发现后将副本工作树 rsync 至 20724c0 内容、重跑基线一致后才做变异。真实仓库全程只读，未受影响。

---

## 二~十四、D1–D13 逐维明细

> 每维列：硬伤（带证据）、亮点、分数依据。完整意图卡片与全文见 `/tmp/agentflow-eval/R1..R7` 各报告。

### D1 架构与设计一致性 —— 8/10

**硬伤**
1. 「九项」口径漂移：`README.md:51`、`AGENTS.md:19`、`docs/system-guide.md` §7、`docs/quickstart.md:48` 均称 `all` 九项，`validate.py`（main 函数分发处）实为十项（lint 已并入）。四处文档未同步。
2. `test-records.md:17,36` 声称 findings 交叉校验「校验器强制」，`gate/workspace.py:301-303` 实际丢弃返回值、`:357-361` 注释自承 deferred。
3. `validate.yml` 无 `pip install` 步，而 lint 门对缺失 ruff/mypy 大声报错——CI 环境下 lint 子项将红（R2 保守口径：未实跑 CI，定「高概率」）。
4. `EP-20261019-001.json` 的 `evidence_ref` 指向 `/tmp` 路径——会话外不可移植，episode 契约无禁绝对路径条款。
**亮点**：fail-closed 贯穿工具层细节——schema 未知关键字拒载（`gate/schema.py:286-405`）、checks 拒 skip（`gate/checks.py:84-86`）、manifests 生成树新鲜度（`gate/manifests.py:122-152`）、build_runtime 危险目标拒绝（`build_runtime.py:61-76`）；诚实披露文化（硬边界 7 自承「角色分离，不是环境隔离」）。

### D2 门禁有效性（×2）—— 8.5/10

**门实测**（真仓 20724c0）：schemas / examples / artifacts / protected / manifests / docs / tests / doc_chain 自测 / doc_chain_live 全 PASS（exit 0）；installed PASS（本机 sha256 逐文件一致）；lint 红（环境性，ruff/mypy 缺失，fail-closed 大声失败）；`trend.py` 红（崩溃，见硬伤 1）。

**变异实验**（副本，11 组全红、报错精确）：M1 schema 加 `exclusiveMinimum` → schemas 红（unsupported keyword）；M2 记录改非法 status → artifacts 红（enum 拒绝）；M3 manifest 版本改坏 → manifests 红（3 错含生成树连带）；M4 动 `tools/lab/validate.py` → check-diff 红（`blocked: ['tools/lab/validate.py']`）；M5 README 断链 → docs 红（broken relative link）；M6 check-diff 边界（`-` base / 坏 base / 非 ASCII / 未跟踪+被忽略）全 fail-closed；M7 删声明测试文件 → tests 红；M8 活面注入 C13/C14 违例 → doc_chain_live 红（带行号）；M9 废 linter 规则一行 → 自测 60/63 → doc_chain 红。

**硬伤**
1. `python3 tools/lab/trend.py` exit 1：`ValueError: reviews/agentflow-product-chain/review-2026-10-19-003.md 评审记录缺少「## 发现摘要」`（`trend.py:76`）——趋势采集对现行记录面已崩溃，且 trend.py 不在 `all` 与 CI 内，红无人看见。
2. `counts.py` 不在 `validate.py all` 与 `validate.yml` 内——计数标记漂移无机器持续支撑。
3. `gate/__pycache__/*.pyc` 进入 check-diff blocked 列表（受保护前缀）——跑门即自陷，与「__pycache__ 不被阻塞」的披露口径只在非保护前缀成立。
4. run-findings→bug_id 交叉核对 deferred（`gate/workspace.py:357-361` 代码自认）。
5. lint 门在无 dev 依赖宿主恒红，「all 全绿」在本环境不可达成（错误处理本身 fail-closed，非 fail-open）。

**评分依据**：无 fail-open 面、变异判别力与报错质量实证充分；四点已知失效模式均有解锁路径，但 trend.py 崩溃是「门照看的观测工具自身失明」，压住 9。

### D3 代码质量与安全 —— 8/10

**硬伤**
1. `tests/` 对 `counts.py`、`mutate.py` 引用数为 0（grep 实测）——两工具零测试保护。
2. `record_store.py:47` `sqlite3.connect` 未捕获 OperationalError（实测 `--db /nonexistent-dir` 裸 traceback）；FTS 非法表达式同样逃逸。
3. `counts.py:114` / `trend.py:74` 读失败未结构化，违背 `gate/common.py:162-174` 自家错误处理模式。
4. `gate/checks.py:70` unittest 子进程无 timeout（同文件 doc_chain 检查有 300s/120s）。
5. `gate/schema.py:91-97` `$ref` 兄弟关键字静默跳过，偏离 Draft 2020-12 语义。
**亮点**：负例测试文化（每条门规则有 mutated fixture 证明会失败 + mutate.py 专司覆盖审计，51/51 全杀）；注释解释为什么并带事故日期（`artifact_digest.py:36-38` 等）；关键字白名单门堵死「声明未实现」整类漏洞。
**实测**：78 tests OK（exit 0）；中文路径经 `check-write-scope.sh` 逐字列出、无 C-quote 失配。

### D4 代码工艺与可读性 —— 7.5/10

**硬伤**
1. `gate/workspace.py:41` `validate_workspace_artifacts` 322 行、圈复杂度 ≈105（AST 实测）。
2. `doc_chain.py:399` lint 201 行 / 圈复杂度 ≈96；`self_test` 449 行且用例编号 42/43 重复。
3. 围栏切换逻辑三处独立实现（`doc_chain.py:173` / `gate/docs.py:146` / `gate/records.py:69`）——复制漂移风险。
4. `doc_chain.py:570` 函数内冗余 `import re as _re`。
5. 布尔命名 is_/has_ 前缀不统一（`lightweight`/`archived` vs `has_prototype`/`is_within`）。
**亮点**：零 TODO、零死代码（全量读毕）；注释解释取舍与事故出处而非复述代码；错误处理模式全域统一（gate 内）。

### D5 Agent/Skill 契约质量 —— 7/10

**硬伤（含「照指令产出必被自己的门拒」组合）**
1. 【高】`test-records.md:36` 与 `templates/testing/run.md:41` 令 findings 列 `BUG-*` id，而 `test-run.schema.json:87,93` 要求 `^ISS-\d{4}-\d{3,}$`——照指令写必被 artifacts 门拒。
2. 【高】`templates/feature/plan/execution.md` 无 frontmatter 信封、无「进展概览」节、标题带编号，对照 `document-chain.md:128-129`、`gate/plan.py:19-23`（整行精确匹配）——照模板写计划必被 plan 门拒；且 plan-architect 要求的「优先级」列在模板任务表中缺失。
3. 【中】`templates/hub/index.md:10` 写 `docs/issues/…`，与同组 `hub/README.md:9` 的枢纽根级 `issues/` 布局矛盾——照模板建枢纽即得悬空索引。
4. 【中】`gate/docs.py:183-185` docstring 与 AGENTS.md 均称 docs 检查断言「中文镜像与英文契约段落对应」，gate/ 与 tests/ 内 grep 零实现。
5. 【低】`design/be/backend.md:114`（§1.6→§3）、`design/fe/frontend.md:143`（§2→§4）节号断档，违反自家反模式条款。
**亮点**：晋升规则三方逐字一致且机器兜底（`improve/SKILL.md:55` ↔ `evidence-and-release.md:152-154` ↔ release-record allOf）；14 角色 tools/disallowedTools 与正文全互证（test-executor 有意禁 Edit 并给理由）；provenance 双形态在两 schema 内互相声明「不可互换」。
**14 角色核对**：全部 PASS（name=文件名、tools 互证、路由不误导、写范围完整）。

### D6 结构合理性 —— 8/10

**硬伤**
1. 质量提升批双看板矛盾：批次 `README.md:29-56`（M-B/M-D/M-E 仍 ☐）vs `PLAN-QUALITY-001.md:29-33`（T05/T08/T09 ☑ approved）。
2. 三份 `AGENTFLOW-EVAL*.md` 滞留仓库根——记录性内容不入记录面。
3. `todo.md:34` 指向 PENDING-DECISIONS 已移出的行，指针悬空。
4. `.mypy_cache/.ruff_cache` 未入 `.gitignore`（check-ignore rc=1）——lint 门使仓库根持续产出缓存目录。
5. `docs/releases` 两工作文件职能划痕靠惯例维持。
**亮点**：可发现性实测 5 任务全 ≤2 跳（每跳路径记录在 R1 报告）；examples 与 schemas fixture 非双份维护；目录引用矩阵无环。

### D7 逻辑链路 —— 7/10

**硬伤**
1. `document-chain.md:178-181`「不得开工实施」vs 批次 README.md:9 实施已落 main——「用户授权旁路」是隐性惯例非条款。
2. `docs/product/README.md:48` 技术方案评审 ☐，而 PLAN-PRODUCT-001 / PLAN-LOOP-SMOKE-001 已执行 11/21——门 4 前置从未满足，链路被实际绕行。
3. SKILL.md:61 只定义计划看板回写，批次 README 同步时点无条款——双看板漂移的根因。
4. 死条款簇：rejected→归档（全库 0 rejected、归档目录不存在）、episode rejected/failed（41 条全 absent）、candidate/release-record 零实例。
5. findings 挂接（测试链→bug 链）在活面无机器保证。
**亮点**：十步闭环、三链切换点、状态机均文本完备且机器钉住（doc_chain linter + plan 门）；主链在记录面真实走过 56 issue / 41 episode / 多批次。

### D8 文档与记录活性 —— 7/10

**硬伤**
1. HEAD 提交 `20724c0` 声称「feature README 同步」，实际批次 README.md:9「T09 仍待排」/ :52「整门变异跑还差」与计划 T05 ☑、T09 ☑ 矛盾——最近一次提交即活性反例。
2. `trend.py` exit 1（同 D2）。
3. `docs/features/README.md:28` 与 `index.md:14` 在途批次括注停留在计划中途状态。
4. AGENTS.md「共九项」vs 实测 10 项。
5. `PLAN-QUALITY-001.md:7` `updated_at` 10-19 vs 正文含 10-20 回写；`EP-20261019-001` 在 T09 approved 后未补 review_roundtrips。
**统计（均抽查验证）**：issue 56（40 verified / 16 open）；episode 41（accepted 36 / partial 5），signals 带证 111/179（62%），轮次 42 轮、changes_requested 50%；计划看板 4/4 算术自洽；台账 single 4 / recurred 5 / escalated 0；PENDING-DECISIONS 真实维护（含回溯评审登记）。

### D9 治理与发布闭环 —— 8/10

**硬伤**
1. `skills/improve/SKILL.md:3` description 仍承诺「独立基线对照」，与同文件 :37「今天没有可跑的对照」直接冲突，未立案。
2. `skills/improve/agents/openai.yaml:4` default_prompt「与 baseline 对照」残留——宿主触发面仍在引导已裁撤流程。
3. `protected-paths.txt:21-22` 注释仍列已删除的 eval-case schema——门自述与实际保护集不符。
4. none 支发布记录形态当前零在盘实例——晋升规则存在空转面（装置裁撤已知代价，恢复清单已在 `docs/design-decisions.md` §3）。
5. `docs/trend.jsonl` 最新行停在 f76094a，HEAD 前两批未落趋势行，断更未登记。
**亮点**：none/better 互斥是编译级强制（release-record allOf），全库零违例；SKILL.md:24 自承原句仍在且成立；负向案例自查闭环（f76094a 受保护面无评审 → EP-20261018-001 自查 → 回溯评审 approved）。
**实跑**：`validate.py manifests` PASS、`installed` PASS；五份 manifest + 生成树全部 0.11.0，与 CHANGELOG 一致。

### D10 安全与权限边界 —— 8/10

**硬伤**
1. `check-write-scope.sh:20,52` 不审计 .gitignore 命中路径（候选门 `isolation.py:113` 特意包含，日常环没堵）——唯一实质 fail-open。
2. `README.md:38` 原句自承「宿主不会对 Write 工具强制任意路径约束」——写范围 = 提示词级 + 事后对照；对照在验收时点，写入时间窗不受限。
3. `schemas/test-plan.schema.json` credentials 字段无 placeholder 校验——真密钥可过全门。
4. contracts.md 硬边界 1/3/9/10/11 纯提示词级（无机制）。
5. `isolation.py:120` 反斜杠替换在对抗性文件名下使禁区匹配失真。
**亮点**：候选门 diff 级机械强制且实测 fail-closed（含中文路径）；自承边界诚实；C13 豁免按完整相对路径匹配，basename 碰撞假设被实测否证。

### D11 实现的效果 —— 6.5/10

**疗效实证**：门拦截有逐字记录（manifests 门 3 次触发、check-diff 拦 gate 改动、变异 51/51 全杀）；changes_requested 50%（21/21 轮）证明独立评审真在推拒；负向证据一等公民（EP-20261018-001 自开 failed claim、REV-002 撤回「无回归」、ISS-038 复审删注水声称）；两次用户反馈四步闭环（反馈→改动→门验→评审）。
**硬伤**
1. 方法疗效自认未决：run-2026-10-19-003「样本量为 1，不构成结论」。
2. 改进环产出 1 候选 0 晋升后停用；trend 观测 3 行且工具停摆。
3. 25/40 verified 为 2026-10-19 事后批量补验，最早滞留 35 天。
**评分依据**：过程疗效扎实但方法疗效空白——这正是 D2 与 D11 的落差来源。

### D12 存在意义 —— 6/10

**场景推演**：① 跨层 feature——裸宿主无评审独立性纪律，recurrence 台账实证「以推演代替最小实验」2 次再犯且曾掩盖门绕过，agentflow 的架构门 + 独立评审 + 台账是真实增益；② 同因再犯缺陷——裸宿主会话消失即遗忘，agentflow 有机器判档 escalated 并触发条款升级（检索范围内独有）；③ 多分支合并——ISS-2026-026 实证裸宿主「只 grep 冲突标记」致重复函数声明进交付（但预防效果未对照验证）。
**成本**：material 改动从 Intake 到 Decision 需产生 issue + episode + 评审 + 计划看板 + 双向校验，对单人开发者的多数日常工作成本倒挂；SKILL 对 trivial single-step work 的跳过划线合理但划得太窄。
**关键限制**：「确定性门」主要绑定插件仓自身（tools/lab + protected-paths），不随方法旅行到目标仓——目标仓用户拿到的只是提示词纪律。
**砍什么更好**：冻结/砍掉 improve 治理机器（evaluator / release-governor 角色、candidate / release-record schema、isolation 候选语义及相应保护面）——它在治理一个不产仪器化证据的流程；保留 episode + bug 记录 + 再犯台账，14 角色收敛至约 9，更诚实更轻。
**翻盘路径**：把 check-diff / write-scope 检查做成可独立安装的最小工具包，让「门」随方法旅行。

### D13 竞品比对 —— 8/10

**对比矩阵**（来源与检索日期 2026-10-20 见 R7 报告）：

| 竞品 | 形态 | 确定性强制力 | 与 agentflow 重叠度 |
|---|---|---|---|
| superpowers | 插件技能库+hooks | 提示词级（Iron Law） | 高：计划/评审/TDD 大面积重叠 |
| BMAD-METHOD | 12+ personas 敏捷框架 | 提示词级（对抗性门问题） | 中高：文档链同构 |
| spec-kit | CLI+斜杠命令 SDD | 提示词级（analyze 由模型判别） | 中高：文档交付链一一对应 |
| Claude Code subagents | 宿主原生机制 | 机制级非流程级（工具白名单） | 互补：agentflow 建于其上 |
| AGENTS.md 约定 | 静态指令标准 | 无 | 互补：Init 的落点 |
| LangGraph/CrewAI | 程序化编排运行时 | 代码级 | 低：层次不同 |

**空白创新点**：① 候选不得编辑评判自己的门的 diff 级执法（protected-paths + isolation.py + mutate.py 负例语料）；② 再犯台账机器升级机制；③ 记录 schema 编译语义（记录即编译）。**重复造轮**：角色化主链、文档链、TDD/worktree 纪律。**叙事押注**：「Agent 不能给自己放权」（可当场演示 check-diff）+「事故语料即方法」（ISS 台账逐条可追溯事故→条款）。

---

## 十五、缺口清单表

| # | 缺口 | 实证 | 压住哪维 | 解锁条件 | 状态 |
|---|---|---|---|---|---|
| G1 | 「九项」→ 实为十项，四处文档未同步 | README.md:51 / AGENTS.md:19 / system-guide §7 / quickstart.md:48 | D1 D6 D8 | 文档同步为十项并复跑 docs 门 | 开放 |
| G2 | trend.py 对现行记录面崩溃 | 实跑 exit 1，review-2026-10-19-003.md 缺「## 发现摘要」 | D2 D8 | 补该节或工具容错，并入 all | 开放 |
| G3 | BUG-* vs ISS-* 模板漂移（照指令必被门拒） | test-records.md:36 / templates/testing/run.md:41 vs test-run.schema.json:87 | D5 | 模板改 ISS-* | 开放 |
| G4 | 计划模板与混合形态脱节 | templates/feature/plan/execution.md vs gate/plan.py:19-23 | D5 | 模板补信封+进展概览+去编号 | 开放 |
| G5 | 双看板同步时点无条款 | 批次 README vs PLAN-QUALITY-001 矛盾 | D6 D7 D8 | 条款化回写时点或砍双看板 | 开放 |
| G6 | improve 活面文案残留（基线对照） | SKILL.md:3 vs :37；openai.yaml:4；protected-paths.txt:21-22 | D9 | 三处文案与裁撤口径对齐 | 开放 |
| G7 | check-write-scope .gitignore 盲区 | check-write-scope.sh:20,52 vs isolation.py:113 | D10 | 对齐审计 ignored 文件 | 开放 |
| G8 | counts.py / mutate.py 零测试且 counts 游离门外 | tests/ grep 0 引用；validate.yml 无 counts | D3 D2 | 补测试 + 入 all | 开放 |
| G9 | CI 无依赖安装步，lint 门恒红 | validate.yml 无 pip install | D1 | CI 加依赖步或 lint 降级 SKIP+警告 | 开放 |
| G10 | findings 交叉校验 deferred | gate/workspace.py:357-361 自认 | D1 D2 | 实现 run-findings→bug_id 核对 | 开放 |
| G11 | 门旁路（用户授权实施）未条款化 | document-chain.md:178-181 vs 批次实施已落 main | D7 | 把旁路条件写成条款 | 开放 |
| G12 | 方法疗效未测（G1 n=1、改进环停用） | run-2026-10-19-003 自述 | D11 D12 | 拍板：接受人工闭环口径或恢复最小测量 | 拍板项 |
| G13 | 巨型函数两处 + 围栏逻辑三处复制 | workspace.py 322 行 / doc_chain lint 201 行 | D4 | 拆函数 + 抽公共围栏工具 | 开放 |
| G14 | gate/__pycache__ 入 check-diff blocked，跑门自陷 | R2 实测 | D2 | 保护清单排除 *.pyc 或清理口径修订 | 开放 |

---

## 十六、勘误节

R8 元评审抽核 93 条证据引用，属实 87 条（93.5%），全部决定扣分的硬伤证据无一错杀。以下 6 条不实引用已更正，不影响任何维度分数方向：

1. R7 称「44 条 ISS」——实测 **56** 条（事故语料规模低估 21%，已在本报告更正）。
2. R1 称「42 条 episode（6 partial）、roundtrips 空 21」——实测 **41 条（partial 5）、空 22**（以 R5 为准）。
3. R3 一处行号错标：`schema.py:305` 实为 `common.py:304`（论断本身成立）。
4. R3 称「64 自测用例」——实测 **63**。
5. R3 称「gate/ 12 模块」——实测 **13**。
6. R1「CI 必红」为部分验证缺席（文件事实属实、CI 行为未实跑），本报告按 R2 保守口径表述。

本轮评测自身无其他发现错误的更正。

---

## 十七、最终裁决

**设计–执行差距**：设计与执行的重合度在「门」上很高（D2 8.5），在「文档面纪律」上中等（HEAD 提交即漂移现行犯，D8 7），在「疗效证明」上最低（D11 6.5）。差距模式不是「没有执行」，而是「执行了但最近一批在声称同步的同时留下十处矛盾」——即机器门照看的范围外（双看板、根目录文件、manifest 外工具）正在成为新的漂移带。

**存在意义结论**：对「多轮迭代、会再犯、要合并」的真实工程场景，agentflow 的独立评审 + 再犯台账 + diff 级门执法是不可替代的组合（检索范围内无竞品同时具备三者）；对单人日常小改动，成本倒挂，跳过划线合理但应放宽。项目的诚实文化（自承边界、负向证据一等公民）是其最稀缺的资产，比任何单一机制都更值得保护。

**最高杠杆下一步**：修复 G2（trend.py 崩溃）+ G1（十项口径同步）——两个都是一小时内可完成的「门照看自身」修复，直接把 D1/D2/D8 的三处硬伤清零；其次是 G3/G4 模板漂移（照指令必被自己的门拒，是契约质量最刺眼的违背）。

**拍板项清单**（每条带推荐默认值）：

| # | 拍板项 | 推荐默认值 | 框定证据 |
|---|---|---|---|
| P1 | improve 治理机器（evaluator / release-governor / candidate·release schema / 候选语义保护面）砍、冻结还是保留 | **冻结**：不再投入，从 SKILL 路由中降权，保留记录面；待恢复条件成熟再启用 | D9 空转面 + R7「砍什么更好」 + design-decisions §3 恢复清单 |
| P2 | 双看板（批次 README vs 计划看板）留哪个、同步条款怎么写 | **保留计划看板为唯一权威**，批次 README 降级为只读索引，回写条款写进 document-chain | G5 + D7 硬伤 3 |
| P3 | 「九项」口径：同步为十项，还是 lint 降回可选 | **同步为十项** + CI 加 `pip install -r requirements-dev.txt` | G1 + G9 |
| P4 | 根目录三份 EVAL 文件（含本报告）的去向 | **移入 `docs/` 或建 `docs/evaluations/`**（需你确认新目录，符合 AGENTS.md「新文档类型先确认」） | D6 硬伤 2 |
| P5 | check-write-scope 忽略盲区是否堵 | **堵**（对齐 isolation.py 的 ignored 文件审计） | G7 |
| P6 | 方法疗效：接受「人工闭环、不测量」口径长期化，还是恢复最小测量（如每批次 1 条 G1 对照） | **接受现口径 + 在 PENDING-DECISIONS 登记为已决**，消除「自认未决」的悬置 | G12 + R6 口径诚信核对 |
| P7 | D2 权重是否维持 ×2 | **维持**——D2 是全仓最高分维，加权与否综合分仅差 0.1，不构成争议 | 本报告总览 |

---

## 附录 A：实跑命令与逐字输出

完整逐字输出（含每条命令退出码与 11 组变异实验的门输出）保存在 `/tmp/agentflow-eval/R2-gates.md`（门与变异）、`R3-code.md`（unittest、check-write-scope 中文路径）中。关键结果摘录：

- `git status --short` → 零输出（干净）；`git log --oneline -5` → `20724c0 (HEAD -> main, origin/main) docs(release): 质量提升批计划回写与发布台账`…
- `validate.py all` → schemas/examples/artifacts/protected/manifests/docs/tests/doc_chain 自测/doc_chain_live 全 PASS，lint 红（ruff/mypy 缺失，大声失败），exit 非 0；`installed` PASS。
- `doc_chain.py --self-test` → 63/63；`unittest discover` → Ran 78 tests, OK；`trend.py` → `ValueError: review-2026-10-19-003.md 评审记录缺少「## 发现摘要」`，exit 1。
- 变异副本：`/tmp/agentflows-eval-copy`（工作树已同步至 20724c0 内容；11 组变异全部 cp 备份-还原，**副本未清理**，留在 /tmp 供复核）。
- 开工事故披露：副本目录建前已存在旧 revision 残留，首次 `cp -r` 为嵌套复制，R2 发现并 rsync 纠正后才开始正式变异；真实仓库全程只读。

## 附录 B：元评审结论（R8 证据链审计）

- 核对规模：93 条「文件:行号 + 逐字引用」（每角色 12–16 条，覆盖全部硬伤级证据），另独立复跑关键统计（trend.py 崩溃、78 单测、63/63 自测、ISS/episode 实数）。
- 属实率 93.5%；**全部决定扣分的证据无一错杀**；6 条不实引用已列入勘误节并更正。
- 验证缺席仅 1 处（R1「CI 必红」，已按保守口径降级表述）；七份报告的「无证据推测」均真实隔离于评分之外（R4「grep 零命中」经复跑确认）。
- 覆盖抽查：抽 3 个被声明「已读」文件，均有行号级内容引用，属实。
- 锚定检查：七份报告分数与自列硬伤数量/严重度自洽，无锚定失准。
- 完整审计：`/tmp/agentflow-eval/R8-meta.md`。

## 附录 C：阅读覆盖清单

| 角色 | 已读 | 未读（含原因） |
|---|---|---|
| R1（D1/D6/D7） | 必读清单全量（README、AGENTS、index、CHANGELOG、design-decisions、system-guide、quickstart、PENDING-DECISIONS、SKILL、五 manifest、packaging 生成器、protected-paths、目录实况） | gate/ 部分模块与 6 份 schema 逐字段（由九项实跑+95 单测代偿）；56 issue/42 episode 正文（frontmatter 全量统计+抽样）；packaging/runtime（铁律排除） |
| R2（D2） | **必读全读，未读清单为空**（tools/lab 全部 .py 含 gate/ 13 模块、protected-paths、tests 两文件，另加读 validate.yml） | 无 |
| R3（D3/D4/D10） | **必读全读，未读清单为空**（tools/lab 全部源码 + tests + check-write-scope.sh） | 无 |
| R4（D5） | **必读全读，未读清单为空**（agents 14、agentflow 全部含 templates 19 件、improve 全部、schemas 7 件；超清单参考 gate 模块与 protected-paths 核实门行为） | 无 |
| R5（D8/D11） | docs 全量、issues 全部（含 recurrence）、features 全部、releases 全部、episodes 全部 .json、reviews 全部 | CHANGELOG 40 行后历史正文、docs/product 链中间件全文、system-guide/design-decisions 部分章节（均受对应机器门覆盖，理由见 R5 报告 §8） |
| R6（D9） | improve 全部、releases 全部、CHANGELOG、trend.jsonl、五 manifest、design-decisions §3 | CHANGELOG 164 行下历史正文（标题枚举+定向 grep）、约 15 份早期 episode（抽读 3 份代表） |
| R7（D12/D13） | README、两个 SKILL、design-decisions、AGENTS、index、protected-paths、近期 issue 抽 5 条、CHANGELOG 头部 + 全部竞品公开资料（来源 URL+检索日期见 R7 报告） | references 契约正文、system-guide、docs/product、tools 源码、tests（必读清单未列或篇幅所限；结论以 SKILL 十步原文为成本基准） |
| R8 | 七份角色报告全文 + 真仓抽查核对 | 无 |

**全局排除项**（全体角色一致）：`.git/`、`__pycache__/`、`*.pyc`、`packaging/runtime/`（生成树，读生成器不读产物）。
**抽样声明**：D4 命名表意性抽样（每文件 5 个标识符）；R5 统计抽查（每条统计 ≥1 条原文核对）；R8 证据抽样 30%（93 条）。其余阅读均为全量。
