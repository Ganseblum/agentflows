# 宿主平台事实

下表每一行都在本机直接观察得到，除非其证据标记为 `doc`；`doc` 行来自宿主官方指南，尚未经运行检验。每行都标明其证据与适用范围。不得把一条事实推广到超出其适用范围。重新验证请重跑该行指名的检查，而不是编辑本文件。

最后验证：2026-10-24（H1 已观察；H2–H4 登记为 `doc` / 未验证）；2026-10-13（W1/W2 行）；2026-10-10（C12 行）；2026-09-18（Z5 行更正、Z7–Z9 行；C8 行 2026-09-17；其余各行 2026-09-14）；X1/C10 行为 2026-09-19 的现场探测。宿主：Claude Code `2.1.268`、Codex CLI `0.154.0`、ZCode（桌面版）、WorkBuddy（CodeBuddy IDE，macOS 桌面版）。

## ZCode（桌面版）

| # | 事实 | 证据 | 适用范围 | 后果 |
| --- | --- | --- | --- | --- |
| Z1 | 插件从本地目录 marketplace 安装，并缓存为以版本号为键的快照副本；编辑源文件不会更新已安装副本。 | Observed: `known_marketplaces.json` 记录 `source: directory`；缓存中保存 `agentflow-local/agentflow/0.3.1/`；已安装文件与源文件 inode 不同而字节完全一致。 | ZCode 桌面版，本地目录 marketplace | 更新需要刷新 marketplace 并重新安装；工作区技能符号链接（`<repo>/.zcode/skills/`）仍是**仅限技能**的即时生效编辑路径。运行 `python3 tools/lab/validate.py installed` 查看漂移。 |
| Z2 | 技能发现顺序把工作区 `.zcode/skills/` 排在插件提供的技能根之前，同名的第一个技能胜出。 | `doc`（ZCode 配置指南）+ 观察到的符号链接布局 | ZCode | 在本仓库中，工作区副本遮蔽了已安装插件中的 `agentflow`/`improve` 副本；请在另一个工作区测试插件副本。 |
| Z3 | 技能触发由模型根据 `name`、`description`（呈现时截断到约 250 个字符）与 `when_to_use` 决定；不存在关键词匹配器。 | `doc`（diagnosing-skills） | ZCode | 触发措辞必须前置在前约 250 个字符以内；描述超过 1024 个字符会导致技能被整体丢弃。 |
| Z4 | 插件提供的 agent **确实**会作为子代理出现，frontmatter 的 `tools` 允许列表**确实**被强制执行：宿主呈现 `bug-fixer` 时带有 `(Tools: Read, Glob, Grep, Write, Edit, Bash)`，而未声明 `tools` 字段的三个 agent 则呈现为完整工具集。带命名空间的名称（`agentflow:bug-fixer`）与裸名称都会注册。 | Observed: 宿主子代理注册表列表，2026-09-14 的会话（解决了早先相互冲突的 `doc` 行） | ZCode 桌面版，插件安装 | 没有 `tools` 允许列表的角色会继承委派（`Agent`）、网络与 MCP 工具。对每个不应拥有这些工具的角色声明 `tools:`。 |
| Z5 | 插件角色文件从已安装的插件快照加载，插件的 `agents/` **没有**即时生效编辑路径。因此，陈旧快照在角色运行期间是不可见的。（2026-09-18 更正：原行从插件 agent 的情形推广出 "no `.zcode/agents/`"；代码显示该目录**正是**宿主的工作区文件 agent 根——见 Z9。仅快照的论断对插件角色文件成立，且 `config.json` 仍没有 `agents` 键。） | Observed: 源与缓存 diff（全部 12 个 agent 与两个技能均有差异）；`validate.py installed` 可复现。更正证据：宿主 bundle 代码 `resolveWorkspaceSubagentRoot`（`uk(e,".zcode","agents")`），读取于 2026-09-18。 | ZCode 桌面版，插件安装 | 角色编辑在插件重新安装之前不会生效。在 `validate.py installed` 通过之前，把 "the role behaves as before" 视为未验证。文件定义的 agent（Z9）是另一条即时生效路径。 |
| Z6 | agent frontmatter 中的 `maxTurns` 仅被声明，其在本宿主的执行情况未验证；该字段沿用自 Claude Code agent 格式。 | 未实际触发——未观察到截断 | ZCode 桌面版 | 在运行演示出截断之前，不要把轮次上限当作安全控制。角色契约中的预算纪律弥补这一缺口。 |
| Z7 | 宿主恰好内置两个子代理：`general-purpose`（工具 `["*"]`，注入 AGENTS.md，设置 `readOnly`）与 `Explore`（"Read-only search agent for broad fan-out searches"，工具恰为 `Bash/Glob/Grep/Read/WebFetch/WebSearch/TodoWrite`，不注入 AGENTS.md）；保留名称集合只包含这两个。 | Observed: 已安装 app bundle 的宿主代码——`createBuiltInAgents` 返回双元素数组，保留集合为 `new Set(["general-purpose","Explore"])`（app.asar 解包读取，2026-09-18）；现行子代理注册表将两者都列出。 | ZCode 桌面版（本安装），代码阅读 + 注册表；未端到端实际触发 | 读密集的扇出调查有宿主原生载体：委派给内置 Explore 并只保留结论——agentflow 不需要重复的侦察角色。Agentflow 自身的只读角色不带 web 工具，因此 Explore 也是唯一具备 WebFetch/WebSearch 的侦察 agent。 |
| Z8 | `judge` 子代理由 document-skills 插件提供，而非宿主提供；它同时以带命名空间的名称（`document-skills:judge`）与裸名称注册，与 Z4 记录的插件 agent 双名称行为一致。 | Observed: 现行子代理注册表列表，2026-09-18 的会话；`createBuiltInAgents` 中不含 `judge`（见 Z7）。 | ZCode 桌面版，且安装了 document-skills 插件 | 不要把 `judge` 当作宿主能力；它的可用性取决于插件的安装，而非宿主。 |
| Z9 | 宿主支持文件定义的 agent：agent markdown 在 `~/.zcode/agents`（用户范围，仅桌面版）与 `<workspace>/.zcode/agents`（工作区范围）下递归发现，匹配 `*.md`/`*.markdown`；agent 状态（模型覆盖、已禁用的 id）存于 `~/.zcode/v2/agents-state.json`，惰性创建。 | Observed: 已安装 app bundle 的宿主代码——`resolveUserSubagentRoot`（`uk(await cE(e),"agents")`，带 `userScopeReason:"desktop_only"`）、`resolveWorkspaceSubagentRoot`（`uk(e,".zcode","agents")`）、`resolveSubagentStateFile`（`uk(await cE(e),"v2","agents-state.json")`）；2026-09-18 现场检查：两个目录都尚不存在，也没有状态文件（默认值在内存中）。 | ZCode 桌面版（本安装），代码阅读；发现机制未端到端实际触发 | 存在一条不经过插件的路径，用于个人/工作区 agent（例如私有的 Explore 式侦察 agent），无需触碰插件。这取代了 Z5 原行中针对文件 agent 的 "no `.zcode/agents/`" 括注；插件角色文件仍仅来自快照。 |
| Z10 | 本地目录 marketplace 会快照 `marketplace.json` 指定为 `source` 的那个目录。2026-09-18 该 source 为 `"./"`，0.7.5 缓存中含有审计转录、REVIEW/ANALYSIS 报告、`mock/`、`tests/`、`tools/`、`records/`、`evals/` 与 `docs/`。 | Observed 2026-09-18: 对 0.7.5 缓存目录执行 `ls`。宿主加载的组件仍为 `agents/` + `skills/` + 各 manifest。 | 本机上的 ZCode 本地目录 marketplace | 多余文件只增加缓存体积，不改变加载行为。更改 `source` 后，通过列出一个新安装的快照来重新验证；不要假设旧缓存是精简的。现状：source 已改指精简生成树（`packaging/runtime`）。 |
| Z11 | 提供商凭证静态加密存储：`~/.zcode/v2/credentials.json` 与 `provider_config.json` 中的 blob 带有 `enc:v1:` 前缀，且 `config.json` 的 `builtin:bigmodel.options.apiKey` 为空。ZCode 不提供 headless CLI（`which zcode` 不存在；`~/.zcode/cli/` 只存放应用数据），也不会向子进程环境注入可用的 key。内嵌浏览器 localStorage（`zcode-coding-plan` 分区）中存在一份明文凭证：`oauth:bigmodel:access_token` JWT——它能对 `open.bigmodel.cn` **完成认证**（越过 401），但直接 API 路径返回 429 `1113 余额不足或无可用资源包,请充值`（`/api/anthropic`、`/api/coding/paas/v4`），且所有 coding-plan 的 anthropic 路径都 404（`/api/coding/paas/anthropic`、`api.z.ai`、`zcode.z.ai` 各变体）：coding-plan 配额只能通过 ZCode 自身客户端消耗，无法经任何直接 API 面消耗。 | Observed 2026-09-19: 凭证矩阵（4 份已存凭证 → 密文被 401 拒绝）、内存中的 localStorage JWT 提取（不落盘/不持久化）→ 对五种端点形态的 429/1113 与 404 探测；同日中继重探测返回快速 502（上游故障），而非 C10 的挂起。 | ZCode 桌面版（本安装），截至 2026-09-19 的 bigmodel 中国平台响应 | 外部 CLI（包括已裁撤的评估适配器，见 [design-decisions.md](design-decisions.md) §3）无法搭用 coding plan；需要一把有余额的直接 API key、一次充值，或一个已恢复的中继。不要尝试解密 `enc:v1` blob；该 JWT 仅在所有者明确授权的会话中于内存中使用。重新验证：每种路径形态各一条 curl。 |

## Claude Code

| # | 事实 | 证据 | 适用范围 | 后果 |
| --- | --- | --- | --- | --- |
| C1 | `--json-schema` 拒绝带有 Draft 2020-12 `$schema`/`$id` 声明的 schema 文档。 | 适配器冒烟约 1 秒即失败，报错 `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`；在传入 schema 前剥离 `$schema`/`$id` 则成功（原 `host_adapter.host_output_schema`，该适配器已裁撤，见 [design-decisions.md](design-decisions.md) §3）。 | `claude --print` 配 `--json-schema` | 传入结构化输出 schema 时不要带元声明；schema 主体仍能完整约束输出。 |
| C2 | 在 `--print` 模式下，`--permission-mode acceptEdits` 不会自动批准敏感路径写入或需审批的 Bash。 | AF-002 诊断：子代理对 `plans/…json` 路径的 `Write` 返回 `classified as sensitive and not created`；一次校验器 `Bash` 调用返回 `required approval and was not run`。 | `--print` 评估调用 | `read-write-workspace` 配置在评估中不保证对 `plans/` 的写访问；在计划写入类用例的结果有意义之前，必须先对齐配置语义（例如显式工具权限）。 |
| C3 | `claude --print` 继承用户级配置：已连接的 MCP 服务器与全局斜杠命令会出现在会话的 `init` 事件中。 | AF-002 流：`mastergo-magic-mcp` 已连接，列出约 40 个全局斜杠命令。 | 本机上的任何调用 | 在隔离之前，评估运行会带上用户配置噪声（延迟、成本、可复现性）；`--strict-mcp-config` 与 `--setting-sources` 作为候选隔离标志存在（`flag`，未验证）。 |
| C4 | 经 `--output-format json` 的结构化输出把受约束对象作为 JSON 字符串放在 `.result` 内返回。 | 原适配器的 `parse_structured_output` 对其解包（适配器已裁撤）；AF-001/AF-002 运行产生了有效对象。 | `--print` + `--json-schema` | 解析 `result` 字段，而不是原始 stdout 对象。 |
| C5 | 单个用例可能耗时数分钟到数十分钟，并派生子代理。 | AF-001：每次调用 137–212 秒。AF-002：约 23.8 分钟、40 轮、4 个子代理、约 $4.05。 | 本机网关（`api.360.cn` ccmax）、`fable`/opus 级路由；不是 Claude Code 的性质 | 每次调用的超时必须覆盖最慢的多 agent 用例（900 秒不够）；原适配器一旦有一次超时就中止整个运行（全有或全无）——该适配器已裁撤，此条作为测量经验保留。 |
| C6 | 经过自定义网关时模型标签不可信：同一次运行中 assistant 事件报告 `model: gpt-5.5`，而 CLI `modelUsage` 记录的是 `anthropic-ccmax/claude-opus-4-6`。 | AF-002 流分析（157 个 assistant 事件 vs. 最终 `modelUsage`）。 | 仅限本机网关 | 把模型标签视为未验证；记录观察到的上下文；不要声称本环境能给出可比的基线/候选结果。 |
| C7 | Agent frontmatter 工具允许列表（`tools`、`disallowedTools`）只到工具层级；该格式没有路径作用域。 | `agents/*.md` 中的 frontmatter 格式；声明中不存在路径语法。 | 插件 agent 格式 | 路径边界（例如 "only `issues/`"）无法由宿主按 agent 强制执行；它们仍依靠角色矩阵 + 监督者 diff 检查。 |
| C8 | 在 `--print` 模式下，宿主把工具的文件访问限制在调用的工作目录内：对 cwd 之外路径的 `Read` 会以 `permission not granted` 被拒，`Bash` 会被以 `only files under <cwd> are permitted` 阻止，而 `permission_denials` 保持为空。 | Observed: 2026-09-17 业务冒烟，单次调用诊断——四个快照目标文档全部被拒，例如 `Read tool denied for snapshot/docs/features/feature-A/spec/be/spec-backend.md (permission not granted)`；`Bash nl/cat` 被以 `only files under <cwd> are permitted` 阻止；宿主自报 `num_turns: 3`、`permission_denials: []`、`tool_failures: 9`、`accepted: false`、"intentionally not written because zero target-document bytes were readable"。2.1.268 上的 `claude --help` 把 `--add-dir <directories...>` 列为 "Additional directories to allow tool access to"。 | 本机上的 `claude --print` + `--permission-mode acceptEdits`，Claude Code `2.1.268` | 任务需要读取 cwd 之外内容的调用必须传入 `--add-dir <root>`；`permission_denials` 为空意味着审批层看不到这种失败模式——要检查工具结果，而不是审批计数器。原 `host_adapter.run_claude` 只为带 `business_root` 的请求添加该标志（适配器已裁撤，见 [design-decisions.md](design-decisions.md) §3）。 |

| C9 | `claude --print` 支持 `--output-format stream-json`、`--verbose`、`--allowed-tools <tools...>`（"Comma or space-separated list"）、`--strict-mcp-config`（"add --strict-mcp-config to skip" 加载其他配置源）以及 `--mcp-config <configs...>`；`CLAUDE_CONFIG_DIR` 重定向配置根。 | 已安装 CLI 上的 `claude --help`（2026-09-18），选项文本逐字引用。 | 文档级（`--help`），尚未现场运行 | 适配器（已裁撤，见 [design-decisions.md](design-decisions.md) §3）曾用 stream-json + 这些标志实现隔离与工具作用域；**组合运行时行为**（stream-json 配合 `--json-schema`、strict-mcp 且无 `--mcp-config` 文件、临时 `CLAUDE_CONFIG_DIR`）：stream-json × `--json-schema` 已于 2026-10-10 随 AF-001×3 实跑首次现场验证（结果解析正常）；strict-mcp / 临时配置目录组合见 C12（按变体执行）。 |

| C10 | 为 `claude --print` 提供服务的第三方网关在模型调用上失败关闭：2026-09-14 一次最小 AF-007 冒烟两次返回结构化 `API Error: 502`（约 195 秒、约 203 秒）；2026-09-19 一次单词探测立即返回 `API Error: 502 status code (no body)`，20 秒后的一次重试挂起超过 180 秒且无输出，2026-09-19T12:46Z 的重新验证挂起 90 秒、stdout/stderr 皆空（`TimeoutExpired`，退出码 124）；2026-09-19T14:15Z/14:17Z 的另外两次探测（各 90 秒超时、相隔 20 秒）都挂起且流为空。本机为该 CLI 只配置了一个端点（`~/.claude/settings.json` 中单一 `ANTHROPIC_BASE_URL`；未配置备选）。 | 直接经 `claude --print --output-format json` 观察（502 当天：shell 退出码 0，`is_error: true`；挂起当天：无 JSON 体）。 | 本机网关（`fable`→`anthropic-ccmax/...` 系列） | 端点问题（U-01）不是形式主义：权威评估与 C9 现场验证都卡在一个能完成调用的网关上。在任何评估会话之前，重跑单词探测来重新验证。切换端点需要用户提供的 URL + token；本地不存在。 |
| C11 | 本安装的认证解析与失败语义：`--settings <file>` 的 `env` 块覆盖用户 `settings.json` 的 `env`，后者覆盖进程环境（一次 `--settings` 探测到达了新端点并得到其快速 401；一次仅用进程环境的探测仍命中已配置的中继并挂起）。伪造的 base URL 会挂起（连接重试）；可达端点配空 key 或无效 key 会快速返回 HTTP 401，CLI 将其渲染为 `result: "Not logged in · Please run /login"`，并带 `terminal_reason: api_error`。 | Observed 2026-09-19: 针对 `https://open.bigmodel.cn/api/anthropic` 的临时配置探测（settings env / `ANTHROPIC_API_KEY` / 整个 config-dir 副本 / `--settings` / 进程环境 / 伪造 URL）外加一次 curl 认证矩阵；除两类挂起外，所有延迟均为 1 秒。 | 本机上的 `claude --print`，CLI `2.1.268`；目标端点的响应措辞来自 bigmodel | 端点切换必须经由 `--settings` 或用户 settings 文件——仅靠进程环境无效。快速 401 与挂起可区分坏 key 与死端点；在任何评估会话之前用这一点判断。重新验证：一次故意用坏 key 的探测与一次用伪造 URL 的探测。 |

| C12 | 端点切换后的一词探测恢复：`claude --print` 在 `ANTHROPIC_BASE_URL=https://api.360.cn`（凭证与模型映射同在 `settings.json` 的 `env`）上 3/3 返回 `pong`（21.6s / 23.7s / 23.1s，`stop_reason: end_turn`，单次约 $0.02）；隔离对照：空 scratch `CLAUDE_CONFIG_DIR` 快速失败（rc=1，1.5s），scratch 目录内置一份 `settings.json` 副本的变体成功（39.6s）。 | Observed 2026-10-10：三次一词探测 + 隔离变体 A/B 对照；同日 AF-001×3 试水实跑完成（3 轮 21.7 分钟，结果 manifest 解析正常）。 | 本机 `claude --print`，CLI `2.1.268`，`api.360.cn` 网关 | U-01 解除（C10/C11 的当时结论按其时效保留）；试水采用「scratch + settings 副本」变体，且为 C9 组合（stream-json × `--json-schema`）的首个现场验证（`--strict-mcp-config` 未随行）；原 `host_adapter` 隔离路径暴露的空目录认证失败曾待处置，随适配器裁撤失去对象（见 [design-decisions.md](design-decisions.md) §3）。重新验证：一词探测 ×1。 |

## Codex CLI

| # | 事实 | 证据 | 适用范围 | 后果 |
| --- | --- | --- | --- | --- |
| X1 | `codex exec` 支持 `--ephemeral`、`--skip-git-repo-check`、`--cd`、`--model`、`--sandbox`、`--output-schema`、`--output-last-message`、`--color`。 | 0.154.0 上的 `codex exec --help`（组合使用属 `flag`）；2026-09-19 现场单词探测：`codex exec --ephemeral --skip-git-repo-check` 在约 20 秒内返回 `pong`（模型 `gpt-5.6-luna`，provider `openai`，沙箱 `workspace-write`）。 | `codex exec` | 原适配器的命令形态兼容（适配器已裁撤）；一次最小的真实 Codex 模型运行现已完成（单词、ephemeral，2026-09-19），而 claude 系列网关在同一时间窗内挂起——codex 是本机唯一可用的模型端点，但按 X2 它无法评估候选。完整 dogfood 仍待进行。 |
| X2 | Codex 没有每次调用的本地插件绑定；候选源评估按设计失败关闭。 | 原 `host_adapter.validate_request` 在 codex 上拒绝 `source_kind=candidate`；记录于已裁撤的 `tools/lab/adapter-protocol.md`（见 [design-decisions.md](design-decisions.md) §3）。 | 当前 Codex CLI | Codex 只能评估已安装基线；绝不要把已安装源的结果标为候选结果。 |

## WorkBuddy（CodeBuddy IDE，macOS 桌面版）

| # | 事实 | 证据 | 适用范围 | 后果 |
| --- | --- | --- | --- | --- |
| W1 | 会话内可直接执行 Bash / Read / Edit / Write / Grep / Glob 并派生子代理；本仓的确定性检查、安装构建与检索工具都能在该会话内运行并观察到原始输出。 | Observed 2026-10-13（本仓工作树，`fb98b21`）：`python3 tools/lab/validate.py all` → 9 项全 PASS、退出码 0；`python3 -m unittest discover -s tests` → `Ran 60 tests` / `OK`；`python3 packaging/build_runtime.py` → 退出码 0 并生成 `packaging/runtime`（14 个角色 + 6 份 schema + 四份 manifest）；`python3 tools/lab/record_store.py index` → 索引 106 条记录，`query` 返回带上下文的 FTS5 命中。 | WorkBuddy 会话（本安装），对插件仓工作树的命令执行 | 该宿主足以承载 agentflow 的门、构建与检索面——跑门不必依赖 Claude Code / Codex CLI 端点。它不提供插件安装面，因此 Z1–Z11 / C1–C12 / X1–X2 各行不适用于它。 |
| W2 | agentflow 插件未在该宿主上安装：未观察到角色加载、技能触发或 frontmatter 工具白名单被宿主强制执行的任何行为。 | 未实际触发——该宿主无插件安装通道，本次只做门与工具层面的执行 | WorkBuddy | 不得把「门在本会话跑绿」外推为「角色在该宿主上按契约运行」。角色面、技能触发与工具白名单的强制执行仍待 dogfood；README 的 dogfood 前置条件（先跑 `validate.py installed` 并记录结果）不变。 |

## 宿主全局指令文件

| # | 事实 | 证据 | 适用范围 | 后果 |
| --- | --- | --- | --- | --- |
| H1 | ZCode 在会话启动时加载用户级 `~/.zcode/AGENTS.md`，其内容作为「user default instructions」进入系统提示。 | Observed 2026-10-24：2026-10-24 的 ZCode 会话系统提示逐字包含 `Contents of /Users/lihanghang1/.zcode/AGENTS.md (user default instructions)`，并附该文件全文。 | ZCode 桌面版（本安装） | 写在其中的跨仓规则对每个工作区生效，不依赖插件安装；插件升级不会更新这份文件，需要按 `hosts.md` 重跑 Host Init。 |
| H2 | Codex 是否加载用户级 `~/.codex/AGENTS.md`，本仓尚未观察。已知 Codex 会话会读取仓库 `AGENTS.md`；2026-10-23 的合并会话加载了 `~/.codex/plugins/cache/personal/agentflow/0.13.0/skills/agentflow/SKILL.md`。 | `doc`（Codex 指令文件约定）+ 本仓尚未做过用户级加载实验 | Codex CLI / Codex 宿主 | 不要把「仓库 `AGENTS.md` 生效」外推为「用户级文件生效」。Host Init 写入后必须按 `hosts.md` 第 6 条验证，拿不到复述记 `blocked`。 |
| H3 | Claude Code 的用户级指令文件为 `~/.claude/CLAUDE.md`；本仓未做过加载实验。 | `doc`（Claude Code 项目/用户记忆文件约定），未现场验证 | Claude Code | 同 H2：写入后必须验证加载，不得声称已生效。 |
| H4 | Cursor 的规则载体与加载行为未验证：项目级候选为 `.cursor/rules/*.mdc`，全局规则位置未知；是否读取 `AGENTS.md` 亦未验证。 | 未实际触发——本仓未做过 Cursor 安装或加载实验 | Cursor | 在完成「写一条最小规则 → 新会话复述」的实验前，不提供 Cursor 适配器、不声称支持。 |

## 重新验证

- C1/C4：重跑一次 `claude --print --output-format json --json-schema <schema>` 调用，看带 `$schema`/`$id` 的 schema 是否仍被拒，以及受约束对象是否仍包在 `.result` 里返回（原适配器冒烟已随装置裁撤，改用一次直接 CLI 调用）。
- C2/C3/C5/C6：用 `--output-format stream-json` 重跑一个调用，检查 `init` 事件、工具结果与最终 `modelUsage`。
- C8：用一个会 `Read` cwd 之外某个文件的提示运行 `claude --print --permission-mode acceptEdits`，一次带 `--add-dir <its directory>`、一次不带；比较工具结果与 `permission_denials`（该标志的效果体现在工具结果里，而不是审批计数器里）。
- X1：`codex exec --help`；X2：原适配器已裁撤，该条改为对 `codex exec` 是否支持按调用绑定本地插件源复核（当前不支持），不要据旧适配器行为推断。
- Z1/Z4/Z5：`python3 tools/lab/validate.py installed`（快照落后于源时会失败）；检查子代理注册表以复核 `tools` 允许列表。
- Z6：用一个故意很大的任务运行某个角色，观察宿主是否在 `maxTurns` 处停止它。
- Z7/Z8：解包已安装 bundle（`npx @electron/asar extract /Applications/ZCode.app/Contents/Resources/app.asar <tmp dir>`）并 grep `createBuiltInAgents` 与 `new Set(["general-purpose","Explore"])`；打开某个会话的子代理注册表列表，确认恰好出现这两个内置项（且 `judge` 不出现）。
- Z9：把一份最小 agent markdown 放入 `<workspace>/.zcode/agents/` 或 `~/.zcode/agents/`，观察子代理注册表是否拾取它，然后删除。
- C9：端点决策之后，运行一次 `--print --output-format stream-json --verbose --json-schema <schema>` 调用，确认最终 `result` 事件可解析且拒绝文本出现在出错的工具结果中；再用 `--strict-mcp-config` 与临时 `CLAUDE_CONFIG_DIR` 重复，确认没有 MCP 服务器初始化（系统 init 事件未列出任何 MCP 服务器）。
- C12：一词探测（`claude --print --output-format json --no-session-persistence "Reply with the single word: pong"`）；隔离变体：`CLAUDE_CONFIG_DIR=<含 settings.json 副本的临时目录> claude …`（空目录变体预期快速失败）。
- Z10：任何重新安装之后执行 `ls ~/.zcode/cli/plugins/cache/agentflow-local/agentflow/<version>/`。
- H1–H4：经用户当次确认，在副本或真实全局指令文件上写入一条带唯一标记的最小规则（真实文件先备份），新开一次会话让它复述该标记。能复述的，把该行证据改为 Observed 并写上日期与文件路径；不能复述的保持未验证，先查文件路径与加载机制。Cursor 另需先确认规则文件格式与全局位置，不得照搬 `AGENTS.md` 的结论。
- Z10/C9 于 2026-09-18 插入（0.8.0 批次）。
