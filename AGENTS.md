# Agentflow 仓库规则

适用于所有在本仓库工作的 agent 的规则。无论 `agentflow` skill 是否启用，
它们适用于每一个会话。

## 接受任何产物之前

对实际文件运行确定性检查——而不是对摘要：

```sh
python3 tools/lab/validate.py all
```

`all` 覆盖 schema、examples、现行记录根（`docs/issues/`、`docs/features/`、`episodes/`、
`docs/releases/`、`reviews/`）下的记录产物、
角色/文档面与版本散文守卫、受保护门清单的完整性、文档链 linter 的判别自测、
文档链 linter 对活文档面（`docs/product/`、`docs/features/`）的扫描、
manifest 的名字/版本一致性（外加 `packaging/runtime` 生成树在场时与源面的逐字节
新鲜度——marketplace 装的就是这棵生成树，漂移即静默装出旧角色）、`tests/` 下仓库自身的回归测试，
以及 lint（ruff + mypy 静态检查，依赖 `requirements-dev.txt`）、decision_gate（决策可追溯
与追溯闭环 C15–C18 与 C22–C23，标记启用）。项数与内容以
`python3 tools/lab/validate.py --list` 自报为准，本文件与 `README.md` 都不手写它——历史上手写过的
计数在门项变化时都与实跑对不上（见 `docs/evaluations/AGENTFLOW-EVAL-REPORT-2026-10-20-redo.md` 的
D1 与 D2 两节）。失败的检查
是编译错误：修好它，或把输出退回 worker。无法复现的检查记为未运行，绝不计为通过。

其中的角色/文档面检查（`validate.py docs`）扫描的对象是：`agents/*.md`、两个 `SKILL.md`、
`skills/agentflow/references/roles.md`、现行记录根下的各类 `README.md`，以及根 `AGENTS.md`。
它断言四组事实——每个 agent 文件的 frontmatter `name` 等于其文件名；SKILL 里引用的每个
`agentflow:<role>` 都能解析到一个 agent 文件；这个面上（含 `AGENTS.md`）点名的每个
`schemas/*.schema.json` 路径都存在；`AGENTS.md` 不再携带早期的 JSON 计划契约标记。此外两项面级扫描收口历史残留：全仓 Markdown 的相对链接
必须可解析，散文不得出现退役路径（围栏与行内代码是引文，但 mermaid 图算内容仍扫描；
`CHANGELOG.md` 的历史条目按原样保留）。版本散文守卫另扫 `README.md` 与 `docs/design-decisions.md`
两个文件，禁止其中出现 `x.y.z` 版本字面量——版本只在 manifest 与 `CHANGELOG.md` 声明。

迭代过程中也可以直接运行测试：

```sh
python3 -m unittest discover -s tests
```

文档按风险分档：轻量档仅在六项适用性全部为是、有具体依据且用户未要求整套文档时使用单文件 README，由同一检查器的 C26 核验；任一条件未知或涉及公开契约、持久化、权限、共享时序和不可逆风险时使用完整档。两档都保留实际验证、独立评审与授权要求，不能通过换标记跳过既有完整阶段或目标承接。

**文档链**（一个 feature 的 `README + proposal/ + spec/ + design/ + plan/` 目录）同样
是编译产物：在接受或宣告其完成之前，对实际目录运行文档链 linter——它会让以下情况
失败：只有 `.gitkeep` 的阶段、缺失的再审计清单、未关闭的阻塞行、没有字段级契约 /
失败分支时序图 / 状态图或 ER 图的设计、没有异常矩阵或线框图的 FE 设计，
以及没有代码位置的计划任务：

```sh
python3 tools/lab/doc_chain.py <feature-dir>
```

linter 自测（钉住检查器自身，且由于它已并入 `validate.py all`，自测作为门的一部分
运行）：`python3 tools/lab/doc_chain.py --self-test`。`validate.py doc_chain_live` 进一步把
同一个 linter 跑在本仓的活文档面（`docs/product/`、`docs/features/`）上，任一发现即门红——
自测绿只说明检查器没坏，不说明它照看的文档没漂移。
契约：[skills/agentflow/references/document-chain.md](skills/agentflow/references/document-chain.md)。

## 编辑角色或 skill

- `agents/*.md` 与 `skills/**` 由宿主从其**安装的插件快照**加载，而不是从本工作树
  加载。在插件重装之前，源码编辑不会改变宿主实际运行的内容。用以下命令检查漂移：

  ```sh
  python3 tools/lab/validate.py installed
  ```

  它把过期或缺失的安装报告为失败，并逐文件比对运行时组件。在任何 dogfood 运行之前
  以及改动角色之后运行它。
- 当不存在本地安装（克隆、CI 任务、candidate worktree）时，同一检查以 `SKIP` 退出 0，
  因此在任何地方运行都安全。
- frontmatter 字段是宿主特性：`tools` 与 `disallowedTools` 由宿主强制执行，
  `maxTurns` 只声明、未验证。不得在没有证据的情况下添加字段并期待其被强制执行。

## 绝不编辑门

[`protected-paths.txt`](protected-paths.txt) 声明候选不得编辑的路径：evaluator 与
governor 角色文件、`tools/lab/` 下的测量路径（digest / isolation）、发布规则、`schemas/` 下的
记录 schema、钉住的回归测试，以及清单本身。`tools/lab/isolation.py check-diff`
针对候选 diff 强制执行它，而 `validate.py protected` 在清单不再覆盖某个必需条目时失败。

修改受保护路径、`tools/lab/validate.py` 中的必需条目集合或发布策略属于门变更，
需要显式人工评审。不得绕过该检查。由于 `schemas/` 与钉住的测试在门内，合理的契约
变更或门工具修复属于人工编写的改动；候选提出方案，而不是直接实施。新增测试文件——
或 `tests/` 中的任何其他条目，包括子目录——意味着在同一变更中把它声明进
`validate.py` 的 `EXPECTED_TEST_FILES` 并在 `protected-paths.txt` 中保护它。

## 在本仓库工作

- 记录存放于现行记录根下：`docs/issues/`（缺陷记录、`recurrence/` 台账、`docs/issues/归档/` 存放被拒记录）、
  `episodes/`、`docs/features/`（批次目录，计划在各批次的 `plan/` 下）、`docs/releases/`（在途批次索引与待验收，版本记录已停用）
  与 `reviews/`；改进三件套已随 2026-10-12 瘦身批停用。布局与查询见
  [index.md](index.md)。
- issue 记录与计划是带经过校验的 YAML frontmatter 的 Markdown。计划文件的命名精确为
  `<plan_id>.md`（形态：`docs/features/README.md` 的计划形态节）；issue 记录文件命名为
  `ISS-<YYYY-MM-DD>-<slug>.md`（前缀加中文短语整体就是记录 id：日期取 `recorded_at` 的日期部分，
  `bug_id` 必须与文件名 stem 完全一致；slug 用中文短语描述问题，无中文译法的技术词保留原文），
  位于 `docs/issues/` 下，被拒记录移入
  `docs/issues/归档/<YYYY-MM-DD>/`。Supervisor 为每条记录显式指派路径。
- 新增、移动或删除文档时，在同一变更中更新 [`index.md`](index.md)；新的顶层目录或
  新的文档类型需要先经用户确认——不得自行创建。
- 「等用户拍板」的事项统一登记到 [`docs/PENDING-DECISIONS.md`](docs/PENDING-DECISIONS.md)；
  已决定的事写进各自载体，不留悬空承诺。
- 除非用户要求，不得提交、推送或发布。不得声称走查过自己未观察到的宿主行为——
  应改为把它连同证据、范围与再验证方法记录进
  [docs/host-platform-facts.md](docs/host-platform-facts.md)。

## 决策记录与台账

决策类产出走固定形态，检查由 `validate.py decision_gate`（C15–C18，标记启用）机械把关：

- **拍板口条目用八列**：`来源 | 待决问题 | 现状核验 | 推荐 | 关闭条件 | 优先级 | 影响范围 | 自动决策`。
  模板见 [skills/agentflow/templates/decision/decision-record.md](skills/agentflow/templates/decision/decision-record.md)
  与 `decision-brief.md`（分类头 + 九段简报，≥3 个方案、每个选项写做/不做两种后果）。
  文件加上标记 `agentflow 决策记录` 即进入检查：来源必须可回溯、核验必须带日期+命令、
  影响范围必须列**具体模块/项目名**（只写「单模块」这类级别词会红）、`自动决策=Y` 仅允许 P3。
- **台账只做索引**：问题台账（差异清单、缺陷索引）行内不写状态结论，只给
  `编号 | 一句话 | 记录链接 | 归属`；状态权威在记录 frontmatter。加标记
  `agentflow 问题台账` 进入检查（C15）：无 ISS 链接的行不得携带状态词。
- **核验会过期**：条目「现状核验」引用的仓内路径若在核验日期之后被提交修改过，
  C17 会红，须重跑核验命令并刷新日期——不允许拿旧清单直接问人拍板。
- **未决问题必须有归属**（C18，批次 README 加标记 `agentflow 决策归属` 后检查）：
  `status: open` 的记录要么挂进批次承接表，要么显式 `disposition: deferred/not-doing`。
- **目标必须有承接**（C22，批次 README 加标记 `agentflow 目标承接` 后检查）：提案 §1.2 声明的每个
  目标编号都要出现在批次 README 的目标承接表里（列：目标 / proposal 出处 / spec 承接 / plan 任务 / 状态），
  表里引用的模块号、验收点与任务号必须在 spec 与计划看板真实存在，看板已 ☑/⚠ 的任务不得无人承接，
  表的状态列必须与看板聚合一致。打标即承诺：缺表会红，靠摘标记转绿是禁止动作。
- **「已完成」必须可复核**（C23，不加标记、对全部批次生效）：计划里标 ☑ 已完成的行，证据列必须含
  四类可复核载体之一——仓内存在的路径（反引号或裸写都认）、`仓库@修订:路径`、git 能解析的提交号、
  `N/A: 理由`。只在 `/tmp` 里存在过的证据不算；对象已消失时，如实写 `N/A: 理由 + 出处` 而不是留着假绿。

## 表达与沉淀纪律

- **面向人的输出白话优先**：给用户的文档、报告与会话交付物，写给没跟过这套流程的读者。
  内部自造的概念名与制度词（例如「台账」）不裸用——要么换成白话（「台账」→「清单 / 记录」），
  要么第一次出现时用一句话解释；本仓内部机制文档可用内部术语，但首次出现也应做到可自明。
- **反复提醒要沉淀**：同一个注意事项被用户指出第二次，就在同一轮把它落成可执行条款——
  轻量规则直接写进本文件对应章节（写成明确、可执行的规则，不写模糊描述）；需要机器强制
  或改契约的，走候选 / 批次流程。
- **接入新项目**：由「首次接入（Init）」把这些约定（语言、术语禁忌、分支纪律、检查命令、文档与记录落点）
  写入目标仓的 `AGENTS.md`，只写一次、经用户确认后落笔；形状见
  [skills/agentflow/SKILL.md](skills/agentflow/SKILL.md) 的「首次接入」节。

## 实验与恢复

这些规则来自 ISS-2026-09-15-真树故障注入checkout还原丢工作（在真实树上做故障注入，随后一次基于 checkout 的“还原”
丢弃了未提交的工作）；它们是过程控制，不是建议。

- 故障注入与变异测试只在一次性副本上运行（`cp -r` 检出到 `/tmp`），绝不在工作树
  上运行。
- 绝不用 `git checkout` / `git restore` 撤销真实树上的实验。对受跟踪的文件，它们会
  重置到已提交版本并静默丢弃未提交的工作——与撤销恰恰相反。
- **工作树里有他人未提交的改动时，任何整文件覆盖式写入都先做保全快照。** 这一类包含
  `git checkout` / `git restore` / `git show HEAD:<path> > <path>` / 用脚本把文件重写成
  「以已提交版本为底 + 自己那一行」——它们的效果相同：文件里不属于你的未提交改动被静默
  还原。要改一个新版本的文件，用增量替换（只动你负责的那几行），不要把整份文件重新生成
  一遍。确实需要覆盖式写入时，在**写入前立刻** `python3 tools/dirty-guard.py snapshot <快照> --tar <仓库外目录>`，
  写完 `python3 tools/dirty-guard.py verify <快照>`；verify 报红时先看消失的行是不是你自己
  刚改写的（自己改写同一行也会报红，这是已知局限），不是你的才是真丢。
  2026-10-28 实例：重写 `index.md` 时用 `git show HEAD:index.md` 作底，把同工作树里另一
  批次未提交的 5 处索引改动还原掉了，靠事后逐条重打才恢复。
- **合并、删分支、`git worktree remove`、`git stash drop` 与覆盖式写入同属一类**——它们销毁的
  也是未提交内容，而且 `worktree remove` / `stash drop` 销毁的东西在对象库里**从来没有存在过**
  （未跟踪文件与未解决项的盘上内容不产生 git 对象）。所以不可逆 git 操作前同样先
  `snapshot … --tar …`，并且动手前逐条量化「该内容是否已在目标里」：
  用 `git merge-base --is-ancestor` 判定分支可达、用逐行比对判定 worktree 内容是否已被取代，
  不得凭分支名或目录名推断。
- **快照的基线是 HEAD，不是索引。** 风险内容有三类，缺一类都算没拍：①相对 HEAD 有新增行的
  受跟踪文件（含改名后的新路径——改名把内容同时挪进了「索引 vs HEAD」，只比索引看不见它）；
  ②未跟踪文件；③未解决索引项（记 stage2/stage3 的 blob，核验时按 stage 内容逐行比，
  冲突文件的 combined diff 不能拿来逐行核）。2026-10-28 实测教训：工作树与索引一致、
  294 个文件全在「索引 vs HEAD」时，只比索引的旧口径拍出的快照是空的——
  同一时刻 `git diff` 只见 1 个文件，`git diff HEAD` 见 3 个。
- **快照有生命周期，核验跑完即删，不留「以防万一」。** 判据：快照文件与 `--tar` 归档都是
  **本地临时件，不得提交进版本库**，必须落在**仓库外**（工具对落在仓库内的快照目标或归档目录
  直接报错退出）——未提交内容的副本一旦进仓，临时现场就被固化成历史，还会被下次操作连带。
  `verify` 通过（或确属有意改写、
  用 `--accept "<理由>"` 记录）后，用 `python3 tools/dirty-guard.py cleanup <快照>` 删除原件，
  cleanup 在没有核验标记时拒绝删除；合并与提交完成、承接核验跑完，就是它该删掉的时点。
  `hosts.md` 那套 `<文件名>.agentflow-backup-<时间戳>` 备份同属本地临时件：`realpath` 落在
  某个仓库里时不得提交，`.gitignore` 应忽略该模式。留在树上的备份既会被下次操作连带、又会污染状态，
  还可能被顺手 `tar -x` 解回原路径覆盖别处在用的内容。
  唯一例外：被销毁内容从未进过对象库、且承接核验尚未做完时，才保留归档。
- 恢复或还原只有在相关检查被重新运行并观察到转绿之后才算数。未观察到的恢复不算
  恢复，正如无法复现的检查记为未运行。
- 对于任何你打算声称成功的命令，不得屏蔽命令输出（`2>/dev/null` 及同类写法）。
  关于工具行为的主张需要退出码与逐字输出，而不是推理（硬边界 12）。
- 存在性结论不得用裸 `grep` 下结论：BSD grep 对中文关键词与部分 `--include` 组合会**静默漏报**
  （同一检索换 Python 脚本命中数不同；跨仓复盘曾据此误判「某功能不存在」，后被代码事实推翻）。
  用可计数、可打印命中文件与计数的脚本检索。
- 检查 / 验收脚本必须先打印命中原文再判 PASS/FAIL；否定式表述与验收条目自身的引用式命中要
  排除——关键词命中不等于缺陷。首轮误报要修正判据复跑，不得把误报当发现，也不得把真残留
  当误报放行。
