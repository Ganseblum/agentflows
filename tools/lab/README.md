# Agentflow Lab

本目录包含用于 schema 校验、记录编译、文档链检查与隔离检查的维护工具。评测装置
（runner / adapter / policy）已于 2026-10-12 裁撤，其设计知识与恢复清单见
[`docs/design-decisions.md`](../../docs/design-decisions.md) §3。
Lab 工具可以读取证据并调用被显式隔离的宿主 runner，但不得成为第二个聊天 CLI 或模型编排运行时。

第一个无依赖工具校验 P0 契约与公开 fixture：

```sh
python3 tools/lab/validate.py all
```

它校验本仓库使用的 Draft 2020-12 词汇表，然后检查记录状态规则、计划依赖图与公开 fixture 引用。
失败的检查返回退出码 1。

`validate.py artifacts` 额外校验实际写入现行记录根（`docs/issues/`、`docs/features/`、`episodes/`、`docs/releases/`、
`improvements/`、`releases/`、`reviews/`，递归）下的记录实例——issue 记录及其 recurrence 台账
与被拒记录归档、评审记录、episode、计划，以及改进环与发布产物——对照同一批 schema 与正文断言；
各根 README 与两个声明的工作文件（`releases/todo.md`、
`releases/pending-test.md`）按声明放行，其余路径仍按「意外条目」拒绝；`all` 包含它。
这是 supervisor 产物验收的编译步骤：在接受 worker 的记录之前对真实文件运行它，并把失败当作编译
错误。测试记录位于功能批次目录（`features/<batch>/testing/`），本遍历尚未巡检那里。

`validate.py protected` 检查 [`protected-paths.txt`](../../protected-paths.txt) 是否仍覆盖每一条必需
的门路径——evaluator 与 governor 角色、评测套件、测量路径、发布规则、记录 schema，以及门工具的
回归测试。`all` 包含它，因此候选无法悄悄裁剪用来评判它的门范围。

`validate.py manifests` 要求五份手工同步的 manifest（`plugin.json`、`marketplace.json`、
`.zcode-plugin/`、`.claude-plugin/`、`.codex-plugin/`）在插件名称与版本上一致；否则一次漏掉的
bump 只会在宿主重装后才暴露。

`validate.py tests` 断言 `tests/` 的已声明内容，并运行 `python3 -m unittest discover -s tests`，
带上 `PYTHONDONTWRITEBYTECODE=1`。两者都包含在 `all` 中。测试钉住 `validate.py` 与
`isolation.py`，因此失败即门回归。测试文件逐个受保护，而不是按目录前缀保护：直接保护 `tests/` 会
在 `tests/__pycache__/*.pyc` 上阻塞——任何候选在运行检查后都会带上这些文件——而一个让诚实工作
失败的门会招致绕过。声明内容断言拒绝每一个未声明条目（含目录），理由是已被演示的绕过：
`unittest discover` 会导入子目录中发现的包，而导入期代码先于任何断言运行——新增子目录中的模块若
替换了被钉住的测试方法，就能让坏掉的断言通过、让门返回 PASS。（一个游离的 `tests/__init__.py` 在
`discover -s tests` 下是惰性的，只有在发现过程从仓库根启动时才会被导入；条目检查无论如何都会拒绝
它。）在候选工作树内运行 lab 工具仍会把 `__pycache__` 条目留在 `check-diff` 的变更路径中，因为该
检查包含被忽略的文件；它们会被列出，但不被阻塞。

`validate.py docs` 断言手工同步的角色/文档面：每个 agent 文件的 frontmatter name 等于其文件名，
SKILL 引用的每个 `agentflow:<role>` 都解析到一个 agent 文件，docs/现行记录根/skills/agents 面上
点名的每个 `schemas/*.schema.json` 路径都存在，且中文镜像的 schema 引用集合与 `contracts.md` 的
相匹配。它还会扫描现行 Markdown 面（生成的运行时树之外的一切），查找损坏的相对
链接与已退役路径散文。非 mermaid 围栏块与行内代码是引文，保持豁免——mermaid 图属于内容，仍被
扫描；`CHANGELOG.md` 作为历史载体保持豁免于 token 扫描。`all` 包含它。

两张只读的回溯表只打印、不做校验便退出：`validate.py report
[--project X] [--status Y] [--provenance Z]`（缺陷记录表，provenance 作为最后一列）与
`validate.py recurrence`（按类别的合并状态与推导出的档位——`single` / `recurred` /
`escalated`）。

`validate.py installed` 将源码检出（`agents/`、`skills/`、各 manifest）的运行时组件与已安装的插件
快照做比较，默认使用 ZCode 缓存中 `plugin.json` 所写版本的快照（用 `--path <dir>` 覆盖）。过期或
不匹配的快照即为失败；完全没有本地安装时，该检查退出码为 0，并给出 `SKIP`。它刻意**不**属于
`all`：它读取仓库之外的内容，克隆或候选工作树不得让仓库校验失败。在 dogfood 运行之前以及更改
任何角色之后运行它，因为宿主执行角色用的是快照，而不是工作树。

其余工具都是显式且确定性的：

```sh
python3 tools/lab/artifact_digest.py --root .
python3 tools/lab/isolation.py --help
python3 tools/lab/record_store.py --help
python3 tools/lab/doc_chain.py --help
```

候选工作树与私有 holdout 必须位于
公开仓库之外，且互不包含。`isolation.py` 检查该布局，并在发布门
之前拒绝被禁止的候选路径。`isolation.py check-diff` 始终从受信任的检查器仓库读取
`protected-paths.txt`，以 NUL 分帧解析 Git 路径，拒绝检查器根与候选根重叠，并要求
`--base <frozen-parent-revision>`。base 是强制的，这样已提交、已暂存、未暂存、已删除、已重命名、
被忽略与未跟踪的变更都会被考虑；受保护集合没有命令行替代方式。请从受信任的源码检出调用该脚本，
而不是从候选控制的工具副本或受保护清单副本调用。
