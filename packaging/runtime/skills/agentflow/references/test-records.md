# 测试记录

用户可见功能的自动化测试证据：`test-planner` 写的用例库与 `test-executor` 产出的执行记录。
链路由用户发起或由计划携带（见 agentflow skill 的 *自动化测试* 一节）；这里的记录喂给 bug 链，
并充当评审门的端到端路径证据。

| 产物 | 写入者 | 形态 | 用途 |
| --- | --- | --- | --- |
| `<project>-<feature-slug>/plan-<YYYY-MM-DD>-<NNN>.md` | test-planner | Markdown + frontmatter | 用例库：带级别（smoke/e2e/api/boundary）与优先级的注册表、可执行的步骤表、边界覆盖、流程疑点 |
| `<project>-<feature-slug>/run-<YYYY-MM-DD>-<NNN>.md` | test-executor | Markdown + frontmatter | 一轮执行：逐用例结果与证据、汇总计数、决策、可直接复现的 findings |
| `<project>-<feature-slug>/evidence/` | test-executor | 文件 | 截图、trace、响应转储——由执行记录引用，绝不手工编辑 |
| `<project>-<feature-slug>/scratch/` | test-executor | 文件 | 执行期间写下的一次性自动化脚本（例如 Ego Light 操作脚本）；不是记录 |

## 契约

schema：`schemas/test-plan.schema.json` 与 `schemas/test-run.schema.json`（frontmatter 信封；
frontmatter 的值是平铺字符串——解析器有意不做嵌套）。校验器在 schema 之外还强制以下交叉检查：

- **布局**：两份记录都位于 `docs/features/<批次>/testing/<project>-<feature-slug>/`；文件名与
  id 一致（`TP-<YYYYMMDD>-<NNN>` → `plan-<YYYY-MM-DD>-<NNN>.md`，
  `TR-<YYYYMMDD>-<NNN>` → `run-<YYYY-MM-DD>-<NNN>.md`），且 id 的日期与 `recorded_at` 的日期
  相符。目录锚在被测的 feature 而不是日期：同一个 feature 的计划修订与执行轮次累积在一处。
  直接落在 feature 目录下的意外文件被拒绝；`README.md` 与 `evidence/` 豁免。
- **计划正文**：`## 用例` 以注册表开头（`| 用例 ID | 级别 | 优先级 | 标题 | 来源 |`），
  且每个用例一个 `### <用例 id>` 详情标题；用例 id（`TC-*`）唯一；级别与优先级是固定枚举；
  **来源列指向该用例的验收出处**——proposal 的目标/AC 编号（如 `G2-AC-03`）或工单记录
  （`ISS-<YYYY>-<NNN>`），没有对应出处时写 `无 — <理由>`，不许留空；`case_count` 等于注册表
  行数。每个用例详情块带**测试功能**一行（被测功能点，如「登录-账号密码登录」）、前置条件与
  步骤表（`操作 → 输入 → 预期可观察结果`）。`## 边界覆盖`、`## 数据来源` 与 `## 流程疑点`
  是必需章节。计划就地修订——递增 `test_version`。
- **执行正文**：`## 结果` 是结果表（`| 用例 ID | 状态 | 证据 | 实际结果 | 说明 |`）；状态是
  固定枚举 `pass / fail / blocked / not-run`；`fail` 或 `blocked` 行带证据；**实际结果列写
  观察到的真实行为**（与预期并列，判 pass/fail 的依据），fail 行的实际结果必须与预期结果
  形成可对照的差异；结果里的用例 id 必须存在于被引用的计划的注册表中；平铺的 `summary_*`
  计数与表格相符；`decision: pass` 要求零 fail 且零 blocked。`## 证据` 与 `## 结论` 是必需
  章节。每轮是一个新文件——更正时编辑该记录并刷新 `updated_at`（仅追加的历史：已发生的证据
  绝不为了把故事讲圆而改写）。
- **计划解析**：执行记录的 `test_plan_id` 必须解析到同一 feature 目录下的一份计划记录，且
  `project` 匹配。当执行轮次钉住计划当前的 `test_version` 时，注册表中的每个用例都在结果表里
  有交代（针对旧版本的一次执行则记录它自己的覆盖情况）。
- **Findings**：`findings` / `flow_findings` 列出必须存在于 `docs/issues/` 下的 `ISS-*` id
  （本仓缺陷编号家族是 `ISS-<YYYY>-<NNN>`；schema 以 `^ISS-\d{4}-\d{3,}$` 强制）。
  失败的用例带可直接复现的 findings（步骤、期望与实际、证据引用），让 supervisor 无需重新推导
  即可立 bug 记录；归因遵循标准规则（目标项目缺陷取 `external`，Agentflow 自身方法缺口取
  `agentflow`）。

## 目标项目映射

当目标项目有自己的用例引擎（定位器注册表、可复用 flow、套件注册表、按环境配置——例如一套
YAML 驱动的 e2e 套件）时，执行记录的结论按下面这条对齐链给每个失败分流；每一环写明
什么必须一致、改动落在哪里，使一次修复只碰一个文件：

| 链环 | 什么必须一致 | 改动落在哪里 |
| --- | --- | --- |
| 前端 test id ↔ 定位器注册表 | testid 字符串或动态前缀 | 前端改名 → 只改注册表；用例保留其逻辑名 |
| 注册表 ↔ 计划的用例库 | 用例引用的每个元素都以别名存在 | 新别名随用例一起声明；用例里不出现字面定位器 |
| 用例库 ↔ 引擎用例 | 步骤与期望的语义落成引擎的动作与断言 | 由 executor 落地；不发明新词汇 |
| 用例 ↔ 共享 flow | 可复用的前置被引用，而不是复制粘贴 | 共享前置改动 → 只改 flow 注册表，改一次 |
| 用例 ↔ 套件注册表 | 套件 id、用例目录与 runner 注册表一致——不一致是静默不收集 | 创建用例文件之前先注册套件 |
| 用例 ↔ 环境配置 | origin、账号与密钥按环境解析；值绝不出现在用例内 | 环境改动 → 只改配置 |

失败分流遵循同一张表：产品行为与期望结果矛盾 → bug 链；元素或注册表漂移 → 更新注册表并重跑；
环境或数据问题 → 标 `blocked` 并写明原因。框架文档声明为不支持的能力，在计划里标为 TODO 或
不可自动化——绝不弱化成一条能通过的断言。具体的注册表文件名是目标项目自己的；它们按项目声明，
绝不硬编码进另一个项目的用例或本契约。

## 凭据

凭据按会话提供、运行时注入（env、会话、被 gitignore 的文件）——`credentials` frontmatter 字段
只声明**一行注入方式**，绝不声明值。这些记录中禁止出现密码、令牌与真实账号值；executor 通过
掩码输入录入，并标记任何捕获了密钥的 trace 或截图，以便 supervisor 把该产物按敏感件处理。

只有对实际文件运行 `python3 tools/lab/validate.py artifacts` 通过之后，记录才被接受。

## 执行路线与数据来源

**执行路线，按优先级排序**（2026-10-25 起浏览器自动化默认 Ego Light，不再新写 Playwright spec）：

1. **Ego Light 自动化**——executor 通过命令驱动 `ego-browser`（ego lite）按用例步骤执行 UI
   操作并采集证据（页面截图、DOM 文本、网络日志）。执行前先运行 `ego-browser skill` 获取与
   所装版本匹配的用法；用例步骤中的可操作元素以 testid/别名定位，与目标项目注册表对齐。
   脚本与原始输出落 `scratch/` 与 `evidence/`。
2. **API 用例**——通过命令运行（`curl` 或项目客户端），断言状态码、错误形状与顺序，附原始响应。
3. **宿主浏览器兜底**——Ego Light 覆盖不了的交互（宿主登录态、本机专属环境）由 Supervisor
   在主对话按 Executor 编译的步骤脚本执行并回传原始证据。兜底路线不是目标。

**数据来源策略（真实优先，Mock 逐项声明，禁止全链路 Mock）**：

- **能从真实接口/环境取到的数据一律用真实数据**：staging/真实环境 origin + 按计划注入的账号 +
  真实接口返回。计划在 `## 数据来源` 节逐项声明每个用例（或用例组）的数据来源：真实接口 /
  真实库状态 / Mock。
- **只有真实拿不到才 Mock**：外部第三方依赖、计费动作、真实不可构造的状态（如限流触发、下游
  熔断）等，才对该环节 Mock，且必须写明 Mock 的对象、理由与影响的用例——不允许「省事」型
  Mock，更不允许全链路 Mock 冒充端到端结果。
- **真实环境不可达 ≠ 静默降级**：该用例标 `blocked` 并写明在等什么，而不是悄悄换 Mock 跑出
  一个假绿。

**Bug 链衔接**：失败的用例在 findings 里附**可直接照跑的 Ego 操作序列**（步骤、期望、实际、
证据引用），让 bug 链无需重新推导即可复现；`bug-fixer` 修复后按同一序列重跑验证（见下）。

**Bug 回归用例与状态联动**。bug 立案后，把它的 Ego 复现序列收编为计划的回归用例，形态与
普通用例一致，但三处有固定含义：

- **来源** = 工单 `ISS-<YYYY>-<NNN>`；**测试功能** = 缺陷所在功能点；**预期结果** = 修复后
  的可观察行为（不是缺陷现象——现象进复现轮 fail 行的「实际结果」列，作为 bug 存在的证据）。
- **状态联动**（bug 状态权威在记录 frontmatter，状态机 `open → fixed-pending-review →
  verified`，run 结果是 `regression_status` 的证据载体）：
  - 复现/首轮 run 中该用例 `fail`（实际结果 = 缺陷现象）→ 支撑 bug 处于 `open`；
  - 修复落地后的回归轮 run 中该用例 `pass` → 是 `regression_status: pass` 与转
    `fixed-pending-review` 的证据；
  - 独立评审 `approved` + 回归 `pass` → recorder 才写 `verified`；回归轮 `fail` / `blocked`
    → bug 不前进或退回，绝不在红灯回归上改状态。
- **分工**：executor 只产出 run 证据，并在 `## 结论` 逐条点名「本轮结果支撑哪些 `ISS-*` 的
  状态变化」；改 bug 状态的是 supervisor / recorder——executor 不回写 bug 记录，fixer 不
  关闭自己的修复。
