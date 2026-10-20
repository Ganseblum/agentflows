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
五份 manifest 的名字/版本一致性（外加 `packaging/runtime` 生成树在场时与源面的逐字节
新鲜度——marketplace 装的就是这棵生成树，漂移即静默装出旧角色），以及 `tests/` 下仓库自身的回归测试——共九项。失败的检查
是编译错误：修好它，或把输出退回 worker。无法复现的检查记为未运行，绝不计为通过。

其中的角色/文档面检查（`validate.py docs`）扫描的对象是：`agents/*.md`、两个 `SKILL.md`、
`skills/agentflow/references/roles.md`、现行记录根下的各类 `README.md`，以及根 `AGENTS.md`。
它断言五组事实——每个 agent 文件的 frontmatter `name` 等于其文件名；SKILL 里引用的每个
`agentflow:<role>` 都能解析到一个 agent 文件；这个面上（含 `AGENTS.md`）点名的每个
`schemas/*.schema.json` 路径都存在；`AGENTS.md` 不再携带早期的 JSON 计划契约标记；
中文镜像与英文契约文档保持段落对应。此外两项面级扫描收口历史残留：全仓 Markdown 的相对链接
必须可解析，散文不得出现退役路径（围栏与行内代码是引文，但 mermaid 图算内容仍扫描；
`CHANGELOG.md` 的历史条目按原样保留）。版本散文守卫另扫 `README.md` 与 `docs/design-decisions.md`
两个文件，禁止其中出现 `x.y.z` 版本字面量——版本只在 manifest 与 `CHANGELOG.md` 声明。

迭代过程中也可以直接运行测试：

```sh
python3 -m unittest discover -s tests
```

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
  `ISS-<YYYY>-<NNN>-<slug>.md`（slug 用中文短语描述问题，无中文译法的技术词保留原文），
  位于 `docs/issues/` 下，被拒记录移入
  `docs/issues/归档/<YYYY-MM-DD>/`。Supervisor 为每条记录显式指派路径。
- 新增、移动或删除文档时，在同一变更中更新 [`index.md`](index.md)；新的顶层目录或
  新的文档类型需要先经用户确认——不得自行创建。
- 「等用户拍板」的事项统一登记到 [`docs/PENDING-DECISIONS.md`](docs/PENDING-DECISIONS.md)；
  已决定的事写进各自载体，不留悬空承诺。
- 除非用户要求，不得提交、推送或发布。不得声称走查过自己未观察到的宿主行为——
  应改为把它连同证据、范围与再验证方法记录进
  [docs/host-platform-facts.md](docs/host-platform-facts.md)。

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

这些规则来自 ISS-2026-005（在真实树上做故障注入，随后一次基于 checkout 的“还原”
丢弃了未提交的工作）；它们是过程控制，不是建议。

- 故障注入与变异测试只在一次性副本上运行（`cp -r` 检出到 `/tmp`），绝不在工作树
  上运行。
- 绝不用 `git checkout` / `git restore` 撤销真实树上的实验。对受跟踪的文件，它们会
  重置到已提交版本并静默丢弃未提交的工作——与撤销恰恰相反。
- 恢复或还原只有在相关检查被重新运行并观察到转绿之后才算数。未观察到的恢复不算
  恢复，正如无法复现的检查记为未运行。
- 对于任何你打算声称成功的命令，不得屏蔽命令输出（`2>/dev/null` 及同类写法）。
  关于工具行为的主张需要退出码与逐字输出，而不是推理（硬边界 12）。
