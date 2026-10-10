# Agentflow 仓库规则

适用于所有在本仓库工作的 agent 的规则。无论 `agentflow` skill 是否启用，
它们适用于每一个会话。

## 接受任何产物之前

对实际文件运行确定性检查——而不是对摘要：

```sh
python3 tools/lab/validate.py all
```

`all` 覆盖 schema、examples、公开评测用例、现行记录根（`issues/`、`episodes/`、`plans/`、
`improvements/`、`releases/`、`reviews/`）下的记录产物、`mock/` 下的样板 fixture
（通过合并进一次性仓库副本进行编译）、角色/文档面（含版本散文守卫与对现行文档面的
断链 / 退役路径扫描）、受保护门清单的完整性、文档链 linter 的判别自测、
五份 manifest 的名字/版本一致性，以及 `tests/` 下仓库自身的回归测试。失败的检查
是编译错误：修好它，或把输出退回 worker。无法复现的检查记为未运行，绝不计为通过。

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
运行）：`python3 tools/lab/doc_chain.py --self-test`。
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
governor 角色文件、评测套件、`tools/lab/` 下的测量路径、发布规则、`schemas/` 下的
记录 schema、钉住的回归测试，以及清单本身。`tools/lab/isolation.py check-diff`
针对候选 diff 强制执行它，而 `validate.py protected` 在清单不再覆盖某个必需条目时失败。

修改受保护路径、`tools/lab/validate.py` 中的必需条目集合或发布策略属于门变更，
需要显式人工评审。不得绕过该检查。由于 `schemas/` 与钉住的测试在门内，合理的契约
变更或门工具修复属于人工编写的改动；候选提出方案，而不是直接实施。新增测试文件——
或 `tests/` 中的任何其他条目，包括子目录——意味着在同一变更中把它声明进
`validate.py` 的 `EXPECTED_TEST_FILES` 并在 `protected-paths.txt` 中保护它。

## 在本仓库工作

- 记录存放于现行记录根下：`issues/`（缺陷记录、`recurrence/` 台账、`归档/` 存放被拒记录）、
  `episodes/`、`plans/`、`improvements/`、`releases/` 与 `reviews/`；布局与查询见
  [index.md](index.md)。
- issue 记录与计划是带经过校验的 YAML frontmatter 的 Markdown。计划文件的命名精确为
  `<plan_id>.md`（形态：`plans/README.md`）；issue 记录文件命名为
  `ISS-<YYYY>-<NNN>-<slug>.md`，位于 `issues/` 下，被拒记录移入
  `issues/归档/<YYYY-MM-DD>/`。Supervisor 为每条记录显式指派路径。
- 新增、移动或删除文档时，在同一变更中更新 [`index.md`](index.md)；新的顶层目录或
  新的文档类型需要先经用户确认——不得自行创建。
- 除非用户要求，不得提交、推送或发布。不得声称走查过自己未观察到的宿主行为——
  应改为把它连同证据、范围与再验证方法记录进
  [docs/host-platform-facts.md](docs/host-platform-facts.md)。

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
