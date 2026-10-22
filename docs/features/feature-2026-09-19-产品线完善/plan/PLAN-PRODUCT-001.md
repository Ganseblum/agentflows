---
plan_id: PLAN-PRODUCT-001
plan_version: 0.1.0
status: proposed
objective: 把 Agentflow 做成跨宿主方法插件：记下架构结论、收口第一次 improve 噪声底、再按产品卫生与宿主认证完善，不重做运行时
recorded_at: 2026-09-19T10:31:00Z
updated_at: 2026-10-22T00:00:00+08:00
---

# Agentflow 产品完善路线

> **2026-10-13 状态更正**：本计划中凡提及 `eval_runner.py`、`host_adapter.py`、`policy.py`、`evals/` 的内容，均指 2026-10-12 评测装置裁撤（ISS-2026-052）之前的状态，仅作历史参照；现存替代以任务行与 docs/design-decisions.md §3 为准。

> 执行契约，不是改代码授权。架构评审结论与 2026-09-19 已拍板事项写在本文件，避免只活在会话里。
> 第一次闭环的任务级看板仍是 [`PLAN-LOOP-SMOKE-001.md`](PLAN-LOOP-SMOKE-001.md)；业务尺子已随
> 2026-10-12 精简批裁撤（原 `plans/PLAN-BUSINESS-EVAL-001.md` 随瘦身批删除，git 历史可回溯）。
> 本文件管顺序与范围。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。

## 进展概览

**本期进度**：**7 / 12 已完成** · **1 进行中** · **0 阻塞** · **1 未开始** · **3 本期不做**（T10、T11、T12）
**统计口径**：按任务表 T01–T12 逐行计数（12 项：☑7 / ◐1 / ☐1 / —3）；T13–T14 同为本期不做，不计入上述分母。概览表前两行是已经发生的事实（架构拍板 + 噪声底离线），对应任务格只有 T01。
（2026-10-10 回写：T04/T05 按实况置完成——版本与提交已随后续批次发生；T02 置进行中——端点复测通过、试水实跑启动。2026-10-13 复核：T06 状态由「未开始」改为「进行中」，T10/T12 因 `host_adapter.py` 已删除改为「本期不做」。2026-10-22 回写：T06 安装快照已同步到 0.12.0，`installed` PASS，置完成。）

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 产品是什么已经说清 | 方法插件，不是运行时/可视化 Flow/14 角色组织图 | 本计划「已拍板」与「架构结论」两节可核对 | ☑ |
| 2 | 第一次闭环不必等业务 18 次 | 公开噪声底仪器；`--case-ids`；候选只改版本串 | dry-run 9 次；candidate 记录在盘；live 仍停 | ☑ |
| 3 | 仪器真的出过 better/neutral/worse | `PLAN-LOOP-SMOKE-001` T05–T09 | 原 `improvements/` 四类工件（已停用） + 人批 | — |
| 4 | 用户装的不是整仓死重 | 运行时面 vs 实验室控制面分开打包 | marketplace `source` 指向生成树；瘦快照等重装后 `ls` 核实 | ☑ |
| 5 | 换宿主方法不断 | 方法写一次，测量证书一个一个发 | Claude 先；ZCode 次；Codex 只发基线证 | ☐ |
| 6 | 方法改动有业务尺子 | `evals/business` smoke 对照（已随精简批退役，待替代） | `measurement: complete` 或仍诚实标 none | ☐ |

**我们在哪**：架构已评、打包与默认路径已落、T04/T05 按实况回写；端点 2026-10-10 复测通过（U-01 解除），第一次噪声底试水实跑已启动；2026-10-12 评测装置随 ISS-2026-052 整线删除，噪声底的执行对象已失（见 `PLAN-LOOP-SMOKE-001`）。2026-10-22 复核：宿主安装快照已同步到 0.12.0，`validate.py installed` PASS，T06 闭合。
**下一步**：（1）T02 随评测装置裁撤收口（已失对象）；（2）T09 日常 Intake 检索作为后续可选假设。
**阻塞/风险**：无阻塞；生成目录 gitignore，克隆后需先跑 `packaging/build_runtime.py`。

### 已拍板（2026-09-19）

| 问题 | 决定 |
| --- | --- |
| 做成产品还是只服务业务仓 | 做成产品 |
| 主宿主 | 不绑死一个；方法通用，测量按宿主发证书 |
| 自迭代 | 尽快跑通；第一次是仪器噪声底，不是方法优劣结论 |
| 靠谱 vs 可审计 | 都要：硬边界进默认 Skill；episode 只在大事落盘 |

### 架构结论（对照市面后保留）

| 结论 | 含义 |
| --- | --- |
| 该留方法，不该重做运行时 | LangGraph/CrewAI/Dify 管循环；本产品管协作纪律、证据编译、改自己时不能改评分规则 |
| 独立评审叙事要诚实 | 边界 7：评测官/发布官是角色分离，不是另一模型/另一工作区 |
| 14 个角色是能力不是默认流水线 | 默认路径短；完整角色表进阶文档 |
| 检索先 FTS5 | 记录量不够上向量；原始对话不得当 RAG 语料 |
| policy 禁止相同 digest 对贴 | 噪声底候选必须改版本串，不能对同一棵树贴两次标签 |

### 已做（工作树，未提交）

| 项 | 落点 | 证据 |
| --- | --- | --- |
| `--case-ids` 门变更 | `tools/lab/eval_runner.py`（已失对象：随 ISS-2026-052 删除，见 `docs/design-decisions.md` §3）、`tests/test_lab_contracts.py`、`tools/lab/README.md` | `CaseIdSubsetTests` 6 OK；`validate.py all` 9×PASS |
| 噪声底计划 | `PLAN-LOOP-SMOKE-001.md` | T01–T04 ☑；T05 ⚠ |
| 候选预声明 | `improvements/candidates/0.8.1+smokeloop.json` | parent `0.8.1`；digest 异于基线 |
| 本次执行 episode | `episodes/2026-09-19/EP-20260919-001.json` | outcome `partial` |
| 仓库外候选树 | 不入仓 | `check-diff` blocked=[]；仅五份 manifest |

源码基线（历史基线，2026-09-19）：`plugin.json` `0.8.1`，HEAD `ceb639f56c940939c36c745e739c237167048159`。ZCode 安装快照当时仍为 `0.8.0`。
当前基线（2026-10-22 复核）：五份 manifest 均为 `0.12.0`；ZCode 安装缓存目录为 `0.12.0`，`validate.py installed` PASS。

### 没做

| 项 | 为什么还没做 |
| --- | --- |
| 一行模型探测 / live 对照 / policy 建议 / 人批 | U-01；本次执行不能替用户打外部 Claude |
| 提交、bump 五份源码 manifest、CHANGELOG 0.8.2 | 用户未要求提交；live 数字未出 |
| 重装 ZCode 到与源码一致 | 对照用冻结源码树，不读过期缓存；dogfood 另做 |
| 独立评审 `--case-ids` | 由执行方实施，`review_roundtrips=[]` |
| 业务 18 次 | 第二次尺子，见业务计划 |
| 插件打包 allowlist | 产品卫生，不挡噪声底 |
| ZCode/Cursor 评测适配器、Codex 评 candidate | 先闭合一个能绑候选源的宿主 |
| 日常 Skill 强制 FTS5、缩短默认角色路径 | 适合作为噪声底之后的第一个真假设 |
| 向量 RAG、Canary、Execution Coordinator、合并 D1 三角色 | 明确不做，直到有数据或产品 API 决策 |

## 分支策略

- 工作分支：`main`。复核时 `git branch` 仅见 `main` 与 `workbuddy/main-b0d8652c`，无 `feature-*` 分支。
- 本批在 `main` 上直接执行，不另开分支。依据：近期批次提交（如 `8996016`、`fb98b21`）直接落在 `main`；`main` 不属于用户级规则的四类环境前缀，按仓库 `AGENTS.md` 与用户当次指示执行。
- 不合并、不推送：本批不执行 merge / rebase / push；提交与推送需用户另行授权（见 T05）。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | 把架构结论、已拍板事项、已做/没做写入本计划 | P0 | `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-PRODUCT-001.md` | — | ☑ 已完成 | 本文件落盘；`python3.12 tools/lab/validate.py all` 9×PASS |
| `T02` | 收口第一次噪声底：探测 → 基线/候选实跑 → compare → policy → 人批 | P0 | `docs/features/feature-2026-09-19-产品线完善/plan/PLAN-LOOP-SMOKE-001.md` T05–T09 | `T01` | ◐ 进行中 | 2026-10-10：端点复测 3/3 通过（一词探测 21.6/23.7/23.1s 返回 `pong`）；AF-001×3 试水实跑已启动（结果回写噪声底计划 T05 证据列）；权威看板 `PLAN-LOOP-SMOKE-001` T05 |
| `T03` | 独立评审 `--case-ids` 门变更（作者不审自己） | P0 | 待核实：`tools/lab/eval_runner.py` 已随 ISS-2026-052 删除；`tests/test_lab_contracts.py` | `T01` | ☑ 已完成 | 独立 Task 评审 `approved`；`CaseIdSubsetTests` 6 OK；`suite_revision` 不由 id 列表改写；残余见评审（CLI help / 业务套件 / 已加载套件内重复 id 未测） |
| `T04` | 源码版本 bump 与 CHANGELOG：记下门变更与 `measurement: none`（live 未出前不得写成已验证改进） | P1 | 五份 manifest、`CHANGELOG.md`（待核实：原 `docs/iteration-log.md` 已删） | `T03` | ☑ 已完成 | 由后续发布批覆盖（0.8.2–0.10.0 均完成 bump + CHANGELOG 且 `measurement: none`）；本批相关的 `--case-ids` 条目缺口经 2026-10-10 复核确认并按书面豁免（不改写历史条目）；2026-10-10 `CHANGELOG`「待发布」节已含新批 |
| `T05` | 用户授权后再提交本批；默认不 push | P1 | 待核实（无固定代码落点：提交步骤） | `T03` | ☑ 已完成 | 用户授权提交：3f902a3（PLAN-LOOP-SMOKE-001 T01 的 `--case-ids` 门变更）/ 4543b69（PLAN-PRODUCT-001 打包批）（2026-09-19）及后续批次（4ae68bd、4c767eb 等）均已落地。a6fd485 为 PLAN-PY-GUARD-001 的解释器守卫修复（`validate.py`），与本批无关，已移出本批归属（2026-10-13 更正） |
| `T06` | 刷新 marketplace 重装，使安装快照与源码版本一致 | P1 | 待核实（安装快照位于宿主缓存，不在仓库内） | `T04` | ☑ 已完成 | 2026-10-22 复核：ZCode 缓存已有 `0.12.0` 快照，`PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lab/validate.py installed` → PASS（exit 0）；`manifests` → PASS。2026-10-13 记录的 0.10.0 差异已随 0.11.0/0.12.0 重装闭合 |
| `T07` | 产品打包：运行时（skills/agents/manifest）与实验室（tools/evals/tests/docs 审计）分开，消除整目录快照死重 | P1 | `packaging/build_runtime.py`、`marketplace.json` | `T01` | ☑ 已完成 | `source`=`./packaging/runtime`；生成树仅含运行时面，`docs/`、`episodes/`、`reviews/`、`tests/`、`tools/`、`evals/` 均排除；独立评审 `approved`；评审后补目的地禁写源码树 |
| `T08` | 默认路径缩短：Skill 强调只启用有工作的角色；14 角色留作可选能力 | P1 | `skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md` | `T01` | ☑ 已完成 | Bind 段不再枚举 14 个 `agentflow:*`；独立评审 `approved`；`validate.py docs` PASS；ZCode 重装提示保留 |
| `T09` | 日常 Intake 显式检索再犯类（FTS5）；不作为向量 RAG | P2 | `skills/agentflow/SKILL.md`、`tools/lab/record_store.py` | `T02` | ☐ 未开始 | 适合噪声底之后的第一个真假设候选 |
| `T10` | ZCode 评测适配器（本机已在用 marketplace，无 adapter） | P2 | `tools/lab/host_adapter.py`（已失对象：随 ISS-2026-052 删除，见 `docs/design-decisions.md` §3） | `T02` | — 本期不做 | 已失对象（2026-10-13）：无替代，评测装置整线删除；原「门变更，需人审」议题一并取消 |
| `T11` | 业务切片第一次对照（方法级尺子） | P2 | `evals/business/`、`plans/PLAN-BUSINESS-EVAL-001.md` | `T02` | — 本期不做（2026-10-12 裁撤：业务尺子退役，原计划随瘦身批删除） | 已失对象 |
| `T12` | Cursor 测量适配；Codex 在 CLI 能按次绑本地插件之前只发基线证书 | P2 | `tools/lab/host_adapter.py`（已失对象：随 ISS-2026-052 删除，见 `docs/design-decisions.md` §3） | `T02` | — 本期不做 | 已失对象（2026-10-13）：无替代，本期不做 |
| `T13` | 向量库 / 会话全文 embedding / 第二套 CLI | — | — | — | — 本期不做 | 记录量不够；产品边界已禁止 |
| `T14` | Canary/自动发布、Execution Coordinator、合并 Investigator/Analyst/TD 为 Reviewer | — | `agents/` | — | — 本期不做 | 缺统计与产品 API 决策（D1 已声明过渡态） |

### 未决项

| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | 最短模型调用的可信端点 | 不阻塞 | 未关闭（权威跟踪 `PLAN-LOOP-SMOKE-001` 的 U-01，阻塞的是那份计划的 T05–T08，不是本路线的打包/记录） |
| U-02 | 本批 `--case-ids` 与计划/记录是否现在提交 | 不阻塞 | 未关闭（T03 已 `approved`；仍等用户明确要求提交） |
| U-03 | 打包是独立发布来源还是 marketplace allowlist | 不阻塞 | 已关闭（生成拷贝 `packaging/runtime`，不是 host allowlist；脚本不进 `tools/lab/`） |

## 接口与共享机制

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| 本计划 vs 噪声底计划 | 本文件管产品顺序；噪声底计划管 T05–T09 任务格 | 两份计划任务 ID 不混用 | 噪声底 T10 与本计划 T11 都指向业务切片，不双跑 |
| 本计划 vs 业务计划 | 业务计划管仪器与 18 次调用 | 噪声底未出前把业务数字当权威 | 业务计划 U-01 与噪声底 U-01 是同一类端点问题 |
| 候选禁区 | `protected-paths.txt` | 真假设候选不得改 runner/evals/schemas | `--case-ids` 已在受信任源，不进 `0.8.1+smokeloop` 树 |

| 共享机制 | 注册点 | 行为 | 受影响表面 |
| --- | --- | --- | --- |
| 作者不验证自己 | `skills/agentflow/references/contracts.md` 硬边界 1 | `--case-ids` 的作者不能给 T03 当评审 | 执行方只准实施，不准自批发布 |
| 安装快照 | ZCode marketplace | 源码改角色不生效直到重装 | T06；对照不把 0.8.0 缓存当 0.8.1 基线 |
| FTS5 记录索引 | `tools/lab/record_store.py` | 一次性索引，源文件权威 | T09 只加 Intake 纪律，不上向量 |

**异常矩阵（关键链路：按本路线推进）**：

| 异常场景 | 检测 | 处理 | 重试 | 幂等前提 | 用户可见 |
| --- | --- | --- | --- | --- | --- |
| 超时 | 噪声底实跑 all-or-nothing 失败 | 不造 evaluation 文件；停在 T02 | 不自动重试 | 同一 result_id | 闭环未闭合 |
| 重复请求 | 用户再问「现在做了什么」 | 回写本计划看板，不新开平行计划 | — | 本 `plan_id` 唯一 | 以本文件为准 |
| 状态冲突 | 会话记忆与 `git status` 不一致 | Intake 先 `git status`/`log` | — | HEAD + 工作树 | 未提交文件列表以 git 为准 |
| 回调失败 | 端点 502/403 | 只更新噪声底计划 T05 证据，不改本计划 U-01 为已关闭 | 换端点 | — | live 仍停 |

**发布顺序与回滚**：

1. 探测通过 → 噪声底对照 → 人批（不安装）。
2. 独立评审 `--case-ids` → 用户要求则提交/bump。
3. 重装快照。
4. 打包方案（T07）与默认路径（T08）可与 2–3 并行设计。
5. 业务对照（T11）只在噪声底仪器可信之后。

回滚：未提交 diff 可弃；`/tmp` 候选树可删；parent 仍是 `0.8.1` @ `ceb639f56c940939c36c745e739c237167048159`。已提交后回滚=回到该 revision，不是改安装目录。

**评审门**：T03 必须独立 Reviewer；T04/T05 提交与 bump 需用户当次授权；T07/T10 触及 `tools/lab/` 或发布源时按门变更人审。本文件由执行方落盘，不自批 T03。

## 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/validate.py artifacts
git status --porcelain
git worktree list
```

预期：`all` 全套 PASS；`git status` 仅含本批未提交文件（`eval_runner.py`、测试、lab README、噪声底计划、本计划、episode、candidate）；worktree 列表可含噪声底基线/候选树。
