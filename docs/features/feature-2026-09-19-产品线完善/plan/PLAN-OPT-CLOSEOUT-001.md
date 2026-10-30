---
plan_id: PLAN-OPT-CLOSEOUT-001
plan_version: 0.1.0
status: approved
objective: 收尾 2026-10-12 全仓评审优化批——把 16 处已落盘改动按主题提交入库、修复 T2.12 引入的钉住测试回归、推进 BT 首次真实对照、处理治理收尾小项
recorded_at: 2026-10-12T06:27:17Z
updated_at: 2026-10-22T00:00:00+08:00
---

# 评审优化批收尾 — 提交 / 回归修复 / BT 对照

> **2026-10-22 状态更正**：任务表已全部闭合（T01/T02/T04 完成，T03 本期不做），frontmatter
> `status` 由 `proposed` 更正为 `approved`；任务行与证据回写保持原样。
>
> **2026-10-18 合并说明**：本计划随 `workbuddy/main-b0d8652c` 分支并入 `main`。其中提及的
> 8 指标单点 schema、BT 对照装置、`policy.py` 裁决、逐版本结果 JSON 等，均指 2026-10-12
> 评测装置裁撤（ISS-2026-10-12-评测装置裁撤）**之前**的状态，仅作历史参照，不代表现行仓库结构；现存替代与
> 恢复清单以 `docs/design-decisions.md` §3 为准。本说明只增不改，原任务行与证据回写保持原样。

> 执行契约，不是改代码授权。本计划管理的是 2026-10-12 评审优化批的**收尾动作**：
> 16 处改动已落盘并逐条复核实测（经过与证据见 `AGENTFLOW-OPTIMIZATION-2026-10-12.md`），
> 本计划不重做那些改动，只负责提交、修回归、跑对照、清边角。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。
> 回写纪律：完成后只改**状态**与**证据回写**两列，最小 diff。

## 进展概览

**本期进度**：**3 / 4 已完成** · **0 进行中** · **0 阻塞** · **0 未开始** · **1 本期不做**（T03，2026-10-12 装置裁撤后对象已失）

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 一天的优化成果安全入库，不留痕丢失 | 15 个 tracked 修改 + 1 个新 schema 按「安全/治理/结构/门健全/报告」4+1 结构提交；7 个受保护路径文件（`protected-paths.txt` 清单内的文件，门自己不得改的那批）在提交信息标注人工授权来源 | `git log` 可见 5 个主题 commit；提交前 `validate.py all` 输出留证 | ☑ |
| 2 | 门的信号恢复干净，不再被真回归稀释 | 修 `tests/test_gate_schema.py` 的钉住测试：8 指标钉点移到 `metrics.schema.json` 单点定义，并加钉 `$ref` 接线 | 单测 3 error → 2 error，且剩余全部是宿主环境假红（`PermissionError: EEXIST` 类） | ☑ |
| 3 | 「受治理改进」拿到第一次真实测量 | BT-001/002/003 共 9 个夹具已验证完整可解析；跑 baseline/candidate 对照 | `improvements/` 下落 baseline/candidate 结果 JSON + `policy.py` 裁决 + `measurement` 非 none | — |
| 4 | 治理边角清零 | `.gitignore` 是否收录 `.workbuddy/`；两份报告的归宿；0.8.6 历史矛盾是否补再审计记录 | 三个小项各有明确载体与结论，无悬空承诺 | ☑ |

**我们在哪**：优化批 16 处改动全部落盘并提交入库（7 个主题 commit）；T2.12 回归修复经独立评审 approved、四组变异实验证明断言承重；治理三小项（`.gitignore`/报告归宿/0.8.6 再审计）均已落地。

**下一步**：无剩余任务。T03（BT 首次真实对照）随 2026-10-12 评测装置裁撤改为本期不做——`host_adapter`、`policy.py`、`evals/`、`improvements/` 均不存在，对照装置无替代；如将来恢复仪器化，按 `docs/design-decisions.md` §3 的重建清单另立计划。

**阻塞**：无（T03 已改为本期不做）。

## 分支策略

- 工作分支：原始执行发生在 `workbuddy/main-b0d8652c`（WorkBuddy 工作树，历史线）；2026-10-18 经用户指示并入 `main`。
- 并入方式：`main` ← `workbuddy/main-b0d8652c` 合并；按用户拍板「保留 main 的裁撤」，评测装置类文件不复活，仅并入记录类内容（本计划、两份报告、episode）。
- 本计划不执行 push；推送需用户另行授权。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | Git 提交 4+1 结构：①安全批（`packaging/build_runtime.py`、`tools/lab/isolation.py`、`skills/agentflow/scripts/check-write-scope.sh`）②治理批（`skills/improve/SKILL.md`、`skills/improve/references/evidence-and-release.md`、`agents/bug-recorder.md`、`README.md`、`docs/product/spec/method-spec.md`）③结构批（`tools/lab/validate.py`、`schemas/` 下三个文件、`document-chain.md`、`backend.md`、feature `README.md`）④门健全批（`tools/lab/eval_runner.py`）⑤报告批（两份 AGENTFLOW `.md`，可选）。提交前跑 `validate.py all` 留证；③的提交信息注明已知回归；逐文件 add，防 `.workbuddy/` 误入；不 push | P0 | 待核实（无固定代码落点：提交步骤） | — | ☑ 已完成 | 实际 7 个主题 commit（4+1 基础上扩展：拍板后新增计划记录、`.gitignore`、再审计 episode 三类产物各自独立成批）：`9caf54a` 安全 / `65731d3` 治理 / `9e5396c` 结构（T2.12 回归修复随同批提交，每 commit 均绿）/ `d9f30f7` 门健全 / `327048e` 边角+报告 / `6443887` episode / 本计划与清单出账为第 7 批。提交前留证：`validate.py all` 9×PASS + `FAIL tests (errors=2)`（全 EEXIST 环境假红）；逐文件 add，`.workbuddy/` 已被 `.gitignore` 挡在暂存区外；未 push |
| `T02` | T2.12 回归修复（方案A）：`tests/test_gate_schema.py` 的 `test_metric_names_are_exactly_the_eight_contract_metrics` 改为读 `metrics.schema.json` 的 `$defs/metricSummary` 钉 8 指标，并断言 `evaluation-result`/`comparison` 三处确为该 `$ref`。改动属受保护路径，须单独授权 | P1 | `tests/test_gate_schema.py` | — | ☑ 已完成 |  用户 2026-10-12「先全部修复处理」授权；独立评审 `approved`/`complete`（无 P0/P1，P2-1/P2-2 均闭环）；单测全量 errors 3→2 且剩余全为 `PermissionError: EEXIST` 环境假红；MUT1（$ref 回退）/MUT2（metricSummary 删指标）/MUT3（comparison 接线回退）/MUT4（metricDeltas 删指标）均 `FAILED (failures=1)`、未变异对照 OK；`validate.py schemas`/`artifacts` PASS；详见优化报告 §8.3 第二轮更新 ｜载体补充（2026-10-23 C23 回写）：优化报告落 `docs/evaluations/AGENTFLOW-OPTIMIZATION-2026-10-12.md`；MUT1–MUT4 的对照对象（评测装置与结果记录）已随 2026-10-12 整线裁撤，N/A: 原始件不在盘，仅结论留存，裁撤依据与恢复清单见 `docs/design-decisions.md` §3 |
| `T03` | BT 首次真实对照：用已有夹具跑 baseline/candidate，落 `improvements/` 结果 JSON，过 `policy.py` 裁决，写 measurement 记录 | P1 | 待核实（`improvements/` 与 `policy.py` 已随 2026-10-12 装置裁撤删除，见 `docs/design-decisions.md` §3） | — | — 本期不做（2026-10-12 装置裁撤后对象已失；`host_adapter`、`policy.py`、`evals/` 均不存在） | 已失对象 |
| `T04` | 治理收尾三小项：`.gitignore` 收录 `.workbuddy/`（或明确手动排除并记录）；两份报告的归宿（保持面外 / 登记 `index.md`）；0.8.6 历史矛盾补再审计记录（只增不改） | P2 | `.gitignore` / `index.md` / `reviews/` 或 `episodes/` | `T01` | ☑ 已完成 | 三小项均执行：①`.gitignore` 追加 `.workbuddy/` ②报告归宿=保持受治理文档面外、随提交入库留证（未登记 index.md）③再审计记录 `episodes/2026-10-12/EP-2026-10-12-008.json` 落盘——`policy.py`（已随装置裁撤删除）对 0.8.6 实跑 `invalid`/`reject`（exit=1，digest 相同为首条理由）一手复现，历史 release 记录不翻案；`validate.py artifacts` PASS |

### 未决项

| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | T02 授权与激活时机：用户 2026-10-12 已拍板「记录在案暂不修」（优化报告 §8.3），本项问的是何时激活方案 A | 是 | 已关闭：用户 2026-10-12 晚指示「先全部修复处理」授权激活；修复、独立评审、四组变异证据齐（见 T02 证据列与优化报告 §8.3 第二轮更新） |
| U-02 | T03 三样输入的规格与提供：业务快照根（形态/位置）、可信端点（adapter 调什么、凭据注入）、权限档（`--allowed-tools` 范围、是否 `--isolate-host-config`） | 否 | 已关闭：2026-10-12 评测装置裁撤后对象已失，T03 改为本期不做；如恢复仪器化则另立计划 |
| U-03 | T04 三小项取舍（每项都可单独拍板） | 否 | 已关闭：三小项均按推荐执行——`.gitignore` 收录 `.workbuddy/`、报告保持面外随提交留证、0.8.6 再审计记录补记（EP-2026-10-12-008） |

## 接口与共享机制

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| git 提交面 | 只提交 15 个 tracked 修改 + `metrics.schema.json`（已随 2026-10-12 装置裁撤删除，仅存于历史提交）+ 可选 2 份报告；`.workbuddy/`（本地工作记忆）永不入库 | 发现 `.workbuddy/` 在暂存区 → 立即取消暂存该路径并改为逐文件 add | 不 push；提交后回退用 `git revert`，不用 `git restore`/`checkout` 抹历史 |
| 受保护路径授权 | 7 个文件在 `protected-paths.txt` 内（`schemas/` 下三个、`skills/improve/references/` 下一个、`tools/lab/` 下三个），提交信息须注明「人工授权的门变更」及授权来源（用户 2026-10-12「全部做」） | 授权来源缺失 → 提交信息不予采用 | 与 PLAN-PY-GUARD-001 先例一致（用户明示授权后在受信任源码树实施） |
| 回归判读口径 | 修 T02 后，`tests` 子项从 3 error 降为 2 error 才算修复生效；剩余 2 个必须是 `PermissionError: EEXIST` 类（宿主 path-broker 环境假红，`README.md` 运行环境说明已述） | 剩余 error 出现新类型 → 不算修好，按新回归处理 | 判读不依赖「全绿」绝对值，只看错误数与归类 |

**异常矩阵（关键链路：T01 提交 / T02 修复）**：

| 异常场景 | 检测 | 处理 | 重试 | 用户可见 |
| --- | --- | --- | --- | --- |
| `.workbuddy/` 被误暂存 | 提交前 `git status --short` | 取消暂存该路径，逐文件 add | 重新提交 | 提交说明中注明排除 |
| 提交后 validate 输出变化 | 提交后重跑 `validate.py all` 与留证比对 | 逐项归因（环境差异 vs 真回归），真回归走 T02 或新计划 | — | 留证差异说明 |
| T02 修完仍有第 3 个 error | 单测错误归类 | 若为 EEXIST 类 → 环境假红，记录口径；否则 → 新回归，回写未决项 | — | 修复结论与归类证据 |
| BT 端点挂起/502 | `host_adapter` 探测超时 | 按 PLAN-LOOP-SMOKE-001 T05 既有口径记录，不伪造 measurement | 端点恢复后重跑 | 探测原始输出 |

**发布顺序与回滚**：T01 → T04 →（授权后）T02；T03 本期不做（装置已失）。回滚点：T01 用 `git revert` 逐 commit 回退；T02 用反向 edit 还原测试方法（按 AGENTS.md 禁 `git restore` 真实树）；T03 无代码改动，删结果文件即可（measurement 记录本身只增不改）。

**评审门**：T02 改的是钉住测试（受保护路径），按硬边界 1「作者不自证」——若授权激活，完成后须过独立评审（审原始 diff 与前后单测输出）再回写完成。T01 提交面是已复核实测的 16 处改动，不重复评审。2026-10-18 并入 `main` 的合并本身触及受保护路径（`agents/evaluator.md`、`packaging/build_runtime.py`、`tools/lab/isolation.py`），按门变更人工评审执行；合并后已跑 `validate.py all` 九项全绿留证。

## 验证命令

```sh
# T01 提交前留证（期望：9×PASS + FAIL tests (3 error(s))——2 环境假红 + 1 已知回归）
python3 tools/lab/validate.py all; echo "exit=$?"

# T01 提交后（期望：5 个主题 commit 可见）
git log --oneline -6

# T02 修复后（期望：errors=2 且全部为 PermissionError: EEXIST 类）
python3 -m unittest discover -s tests 2>&1 | grep -E "^ERROR:|PermissionError" | head -10

# T03 跑对照后（期望：measurement 非 none，policy.py 裁决落盘）
ls improvements/evaluations/ improvements/candidates/
```
