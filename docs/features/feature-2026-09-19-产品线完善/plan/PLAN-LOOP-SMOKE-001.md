---
plan_id: PLAN-LOOP-SMOKE-001
plan_version: 0.1.0
status: proposed
objective: 用公开用例噪声底闭合第一次 improve 环（仪器可出 better/neutral/worse），不把 18 次业务调用当第一根尺子
recorded_at: 2026-09-19T09:40:00Z
updated_at: 2026-10-10T15:35:00+08:00
---

# 公开用例噪声底 — 第一次 improve 闭环

> **2026-10-13 状态更正**：本计划涉及的评测跑器、适配器、策略评估器与 `evals/` 已随 ISS-2026-10-12-评测装置裁撤（2026-10-12 评测装置裁撤）删除。下文的接口、异常矩阵与验证命令描述的是裁撤前的设计，仅作历史参照；各任务行已按「已失对象」标注。

> 执行契约，不是改代码授权。门变更（`eval_runner.py --case-ids`）已由用户「按照最优解处理」授权，在受信任源码树由执行方实施，不作为候选 diff。
> 产品完善顺序（架构结论、打包、宿主认证、业务尺子）见 [`PLAN-PRODUCT-001.md`](PLAN-PRODUCT-001.md)。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。
> 回写纪律：完成后只改**状态**与**证据**两列。

## 进展概览

**本期进度**：**5 / 10 已完成** · **0 进行中** · **0 阻塞** · **1 未开始**（T09） · **4 本期不做**（T06–T08、T10，已失对象）
**统计口径**：T01–T09 计入第一次闭环；T10 业务切片明确留第二次（本期不做）。

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 不必跑满 15×3×2 次就能测仪器 | `eval_runner.py --case-ids` 失败即停子集 | 未知/重复 id 在 adapter 前退出 1；省略旗标仍跑全套 | ☑ |
| 2 | 对照的两端版本可回滚 | 冻结 `plugin.json` 0.8.1 与源 revision | 基线 revision 与 digest 写入计划证据列 | ☑ |
| 3 | 噪声底不是同一份字节贴两次标签 | 候选 worktree 只改五份 manifest 的版本串 | `check-diff` 不碰保护区；两 digest 不相等 | ☑ |
| 4 | 第一次对照有落盘形状 | candidate + 两份 evaluation + comparison + policy 建议 | 原 `improvements/` 四类工件（记录根已停用，落点改由执行方指派） | — 本期不做 |
| 5 | 业务 18 次不是第一根尺子 | BT 切片保持仪器就绪，本期不跑 | 计划 T10 为「本期不做」 | — 本期不做 |

**我们在哪**：T01–T05 完成（端点 2026-10-10 复测通过，U-01 解除）；AF-001×3 试水实跑完成（3 轮 21.7 分钟；成本未落盘）。2026-10-13 复核：评测装置已随 ISS-2026-10-12-评测装置裁撤 整线删除，T06–T08 失去执行对象，改为「本期不做」。产品路线见 `PLAN-PRODUCT-001`。
**下一步**：噪声底闭环本期不再推进。若要恢复，需另立批次重建仪器（属门变更，须人审），不在本计划内续做。
**阻塞/风险**：无阻塞（U-01 已解除）；成本未落盘为观测缺口；T09 依赖已停用的 T08，同样失去执行前提（待用户决定是否同样标为「本期不做」）。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | 评测跑器增加 `--case-ids`：未知/重复/空列表失败即停；省略则全套；不改写 `suite_revision` | P0 | 待核实：`tools/lab/eval_runner.py`（已随 ISS-2026-10-12-评测装置裁撤 删除）、`tests/test_lab_contracts.py`、`tools/lab/README.md` | — | ☑ 已完成 |  `python3.12 -m unittest tests.test_lab_contracts.CaseIdSubsetTests` 6 OK；未知 id 在 adapter 前退出 1 ｜N/A: 载体已随 2026-10-12 评测装置整线裁撤（`CaseIdSubsetTests` 与被测 runner 均已删除），原始输出不复存在；裁撤依据与恢复清单见 `docs/design-decisions.md` §3 |
| `T02` | 冻结基线：源 revision、插件版本、安装快照是否与源码一致 | P0 | `plugin.json` | — | ☑ 已完成 | `git rev-parse HEAD` = `ceb639f56c940939c36c745e739c237167048159`；`plugin.json` 0.8.1；`validate.py installed` FAIL：缓存仅有 0.8.0，对照不用该缓存 |
| `T03` | 在仓库外建候选 worktree：五份 manifest 版本改为 `0.8.1+smokeloop`；`check-diff`；两侧 digest | P0 | `plugin.json`、`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`marketplace.json`（仅候选树） | `T02` | ☑ 已完成 |  `check-diff` blocked=[]，仅五份 manifest；基线 digest `sha256:47d5c7ceb53719f1351023f0f38ed91cffa25fb5aac63241df834c94779bcf18`；候选 `sha256:b810f06a60fb4143b8c1a4024de548555d19bf32e31d13644162bc3d7e7c3095` ｜N/A: 基线 digest 与被贴对象已随 2026-10-12 装置裁撤失效，digest 值留在本行文本但无从再贴；见 `docs/design-decisions.md` §3 |
| `T04` | `host_adapter.py --dry-run`：公开切片 AF-001,AF-004,AF-011，`--repeat-count 3`，隔离布局合法 | P0 | 待核实：`tools/lab/host_adapter.py`（已随 ISS-2026-10-12-评测装置裁撤 删除） | `T01`、`T03` | ☑ 已完成 |  dry_run exit 0；invocation_count=9；三例 AF-001/AF-004/AF-011；plugin_dir=baseline worktree ｜N/A: dry run 与三例试跑的夹具、runner 已删（2026-10-12 装置裁撤），退出码与 invocation_count 的原始件不在盘；见 `docs/design-decisions.md` §3 |
| `T05` | 一行探测：宿主完成最短模型调用（非 502/403/挂起） | P0 | 待核实（纯宿主探测，无仓库代码） | — | ☑ 已完成 |  历史：2026-09-19T12:46Z 起多次挂起/502（见 C10/C11，逐字留档原证据保留于下）——2026-09-19T12:46Z 90s `TimeoutExpired` 空输出退出 124；13:38Z 同口径复测同结果；14:15Z/14:17Z 两次均 90s 挂起；14:35–14:55Z 端点猎取收窄为三选一。**2026-10-10：端点切换后一词探测 3/3 通过（21.6s / 23.7s / 23.1s 返回 `pong`，`stop_reason: end_turn`）——U-01 解除（host-platform-facts C12），T05 达成** ｜N/A: 同批装置裁撤，本行所载运行证据不复存在；恢复仪器化时按 `docs/design-decisions.md` §3 的重建清单重跑后回填 |
| `T06` | 基线实跑：`--case-ids AF-001,AF-004,AF-011`，`--source-kind baseline`，`--agentflow-version 0.8.1` | P0 | 已失对象：`tools/lab/eval_runner.py`、`tools/lab/host_adapter.py` 已随 ISS-2026-10-12-评测装置裁撤 删除（见 `docs/design-decisions.md` §3）；原落点 `improvements/evaluations/`（记录根已停用） | `T04`、`T05` | — 本期不做 | 已失对象（2026-10-13）：无替代，本期不做。历史证据：2026-10-10 试水：AF-001 × 冻结重复数 3 基线实跑完成（3 轮 21.7 分钟；`accepted=false`×3、`tool_failures` 8/0/6、denials 0；成本未落盘；本地产物 `/tmp/agentflow-trial/`，不产生仓内记录）；完整三例（AF-001/004/011）待用户授权（`docs/PENDING-DECISIONS.md`「试水后授权」条） |
| `T07` | 候选实跑：同切片同宿主同模型，`--source-kind candidate`，`--agentflow-version 0.8.1+smokeloop` | P0 | 已失对象：`tools/lab/eval_runner.py` 随 ISS-2026-10-12-评测装置裁撤 删除（见 `docs/design-decisions.md` §3）；原落点 `improvements/evaluations/` | `T03`、`T06` | — 本期不做 | 已失对象（2026-10-13）：候选实跑依赖已删除的评测跑器，无替代，本期不做。 |
| `T08` | `eval_runner.py compare` + `policy.py`；期望 `neutral`/`revise`（主指标不改善）；显著偏离先修仪器 | P0 | 已失对象：`eval_runner.py compare` 与 `policy.py` 随 ISS-2026-10-12-评测装置裁撤 删除（见 `docs/design-decisions.md` §3）；原落点 `improvements/comparisons/` | `T07` | — 本期不做 | 已失对象（2026-10-13）：无替代，本期不做；不得据此写 neutral/revise 结论。 |
| `T09` | 人批门：不自动 promote；发布记录等用户 `approved` | P0 | `docs/releases/` | `T08` | — 本期不做（改进环已整体裁撤，人批门无对象；见 `docs/design-decisions.md` §3） | |
| `T10` | 业务切片 18 次调用（BT-001/002/003） | P2 | `evals/business/` | `T09` | — 本期不做（2026-10-12 裁撤：业务尺子随精简批退役，原计划随瘦身批删除） | 已失对象 |

### 未决项

| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | 哪条端点能完成最短模型调用（本机 Claude 中转曾 502；本次探测未完成） | 阻塞 T05–T08 | 已关闭（2026-10-10 端点复测 3/3 通过；`docs/host-platform-facts.md` C12） |
| U-02 | 对照用冻结源码树当基线，是否还要先重装 ZCode 快照到 0.8.1 | 不阻塞 | 未关闭（dogfood 另做；评测不读该缓存） |

## 分支策略

本计划的执行均在 main 上直接进行：不新建分支；未经用户授权不提交、不推送（见仓库 AGENTS.md）。

## 接口与共享机制

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| `eval_runner.py run --case-ids` | 逗号分隔 `case_id`，按请求顺序；省略=全套 | 未知 id / 重复 id / 空列表：adapter 前退出 1 | 省略旗标时 `load_suite` 行为不变 |
| `policy.py` 噪声底 | 候选 digest ≠ 基线 digest；候选版本 ≠ parent | 同 digest 或同版本 → `invalid`/`reject` | 故候选必须改版本串，不能对同一棵树贴两次标签 |
| `host_adapter.py --plugin-dir` | 等于 adapter workspace | workspace 必须是被测插件树，且与 `evals/` 所在 repository 隔离 | 不改 |

| 共享机制 | 注册点 | 行为 | 受影响表面 |
| --- | --- | --- | --- |
| 候选禁区 | `protected-paths.txt` | 候选 diff 不得碰 `tools/lab/`、`evals/`、`schemas/` | `--case-ids` 只活在受信任源，不进候选树 |
| 冻结 `repeat_count` | `evals/public/AF-*.json` | 每例声明 3；`--repeat-count` 必须等于冻结值 | 噪声底 3 例 × 3 次 × 2 源 = 18 次，与业务计划次数相同但无企业快照 |

**异常矩阵（关键链路：一次 eval_runner run）**：

| 异常场景 | 检测 | 处理 | 重试 | 幂等前提 | 用户可见 |
| --- | --- | --- | --- | --- | --- |
| 超时 | adapter 超时 | 整次 run 失败（all-or-nothing） | 不自动重试；看 progress JSONL | 同一 result_id 不覆盖成功文件 | 该次对照作废 |
| 重复请求 | 同一 `result_id` 输出路径已存在 | 运行器覆盖写入；对照前人工确认 | — | result_id 唯一 | 文件被替换 |
| 状态冲突 | 基线/候选 context 七字段不一致 | `compare`/`policy` invalid | 重跑对齐的一侧 | 七字段全等 | 不得 promote |
| 回调失败 | 宿主 502/403/`is_error` | 记 U-01，不造结果 | 换端点后再探 | — | 闭环停在 T05 |

**发布顺序与回滚**：不安装、不重装、不 bump 五份源码 manifest。回滚点=parent `0.8.1`（`ceb639f`）。候选树可删。`--case-ids` 若必须撤回：从本批 diff 去掉该旗标并保留「省略=全套」行为。

## 验证命令

```sh
# 已失效（2026-10-13）：CaseIdSubsetTests、BuildRequestRepeatCountTests 与 eval_runner.py 随 ISS-2026-10-12-评测装置裁撤 删除，
# 原 `unittest CaseIdSubsetTests` 与 `eval_runner.py run --help` 两条命令已不可运行，以下为现存替代：
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lab/validate.py all
```
