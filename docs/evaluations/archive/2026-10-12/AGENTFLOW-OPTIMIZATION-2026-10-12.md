# Agentflow 优化实施计划与变更记录（2026-10-12）

> 本文件是 `AGENTFLOW-EVALUATION-2026-10-12.md` 的后续行动件。**所有行号均经本会话二次复核**；
> 凡原评价报告路径/事实有误的，已在本文件"勘误"一节标明，不沿用错误行号。
> 本文件同样故意排除在受治理文档面之外（不碰 protected-paths.txt），可随时删除。
> **2026-10-18 合并说明**：本文件随 `workbuddy/main-b0d8652c` 并入 `main`（用户拍板只并入记录类内容），落点已在 `index.md`「迁移与清理记录」登记一行；其中提及的 `policy.py`、`eval_runner.py`、`host_adapter.py`、`evals/`、`improvements/` 均指 2026-10-12 裁撤前状态，现行结构以 `docs/design-decisions.md` §3 为准。
> **2026-10-19 现状指针**：§7 汇总表中 G1/G2 的「已修」结论同样只对 `workbuddy/main-b0d8652c` 成立，未随合并带入 `main`；`main` 上的现行状态以 [`PENDING-DECISIONS.md`](../../../PENDING-DECISIONS.md) 第 7 条为准。

---

## 〇、对自评报告的勘误（4 处）

| # | 原报告说法 | 复核后事实 | 处置 |
|---|---|---|---|
| E1 | `resultSet` "四份拷贝"（报告二/3、十/5） | `grep` 实测 `resultSet` 仅在 `skills/improve/references/release-record.schema.json:358` 定义 1 次、`:26/:29` 以 `$ref` 复用（**良好做法**）；当时 `schemas/` 下的 `evaluation-result`/`comparison` 是**独立顶层 schema**（两份均随 2026-10-12 评测装置裁撤删除），其 `summary` 形状与 `resultSet` **同构但未用 `$ref`** | 撤回"四份拷贝"；改为 T2.12「8 指标 summary 形状跨文件重复，应抽共享 `$defs`」 |
| E2 | `isolation.py:124` base 以 `-` 开头会"静默 PASS（fail-open）"（报告二/2、五/3） | 实测 `git rev-parse --verify --help^{commit}` 与 `-x^{commit}` 均 **exit=128 → 抛 RuntimeError → check_diff 返回 1（fail-closed）** | 撤回"活动漏洞"措辞；保留 T0.3 作为**纵深加固**（补 `--` 终止符 + 拒绝 `-` 前缀） |
| E3 | `docs/method-spec.md:52` "12 条硬边界"（报告四、十/7） | 该路径**不存在**；真实文件是 `docs/product/spec/method-spec.md:52`（及 reviews 归档副本）。"12 条"内容**属实**，仅路径写错 | T1.7 改真实路径 `docs/product/spec/method-spec.md:52` 与 `:194` 的"12 条"→"14 条" |
| E4 | `templates/design/be/backend.md` 等"断号导致 linter 必红"（报告六、十/8） | 仓库根 `templates/**` Glob 返回**无文件**；真实模板在 `skills/agentflow/templates/`（feature/hub/issue/releases + index-template.md），**不存在 design/be/backend.md 等文件** | T2.10 撤回原说法；改为"先定位真实模板逐项核查"，本会话已核查见 T2.10 记录 |

---

## 一、T0 安全/正确性硬伤（必修，高风险）

### T0.1 · build_runtime.py 的 `..` rmtree 漏洞
- **为什么改**：破坏性默认值，误用会销毁仓库根及其父目录全部内容。
- **什么问题**：`assert_safe_destination`（:64-77）只拒绝"等于仓库根 / 等于 packaging / 等于或包含某个 RUNTIME_DIRECTORY 源树 / 等于某个 RUNTIME_FILE"。它**不拒绝仓库根的祖先目录**。`--destination ..`（或 `../..`、`/`）会解析为仓库根的父目录，通过检查；随后 `build()`（:110-111）`shutil.rmtree(destination)` **销毁父目录**。
- **怎么改**：在 `assert_safe_destination` 开头加 `if ROOT.is_relative_to(resolved): raise`（覆盖仓库根及其任意祖先，含 `/`）。
- **前后对比**：见"变更记录 T0.1"。

### T0.2 · check-write-scope.sh 中文路径误 FAIL + 失败静默 OK
- **为什么改**：硬边界 14 的随附工具若误判，会让合法变更被拒（误 FAIL）或让越界变更蒙混过关（fail-open）。
- **什么问题**：(a) `git diff --name-only` / `git ls-files` 缺 `-z`，git 默认对**非 ASCII 路径做 C-quote**，`case` 模式拿不到原始路径 → 中文变更**永远越界 FAIL**（ISS-2026-10-10-写范围dot-scope静默不匹配 同根因，修复不完整）；(b) `< <(git ...)` 进程替换吞掉 git 退出码，`set -eu` 不传播其内部失败 → git 报错时循环读到空、`changed` 为空、脚本打印 "OK exit 0"（**fail-open**）。
- **怎么改**：diff/ls-files 加 `-z`，用 `read -r -d ''` 读取；先把输出落临时文件并**检查 git 退出码**，失败即 fail-closed。
- **前后对比**：见"变更记录 T0.2"。

### T0.3 · isolation.py base 选项注入（纵深加固，E2 修正后）
- **为什么改**：调用缺 `--` 终止符，属防御性纵深加固（实测当前 git 已 fail-closed，非活动漏洞）。
- **什么问题**：`changed_paths`（:123-124）拼 `f"{base}^{{commit}}"` 直接传给 git，无 `--` 守卫；以 `-` 开头的 base 会被 git 当作选项解析。
- **怎么改**：`rev-parse --verify -- "${base}^{commit}"`，并在函数入口拒绝以 `-` 开头的 base。
- **前后对比**：见"变更记录 T0.3"。

## 二、T1 诚实性/治理

### T1.4 · policy.py 孤儿门 → 接入改进环（最重的一条）
- **为什么改**：核心差异点（确定性受治理发布）目前只是宣言；release 记录可自证 promote 而无任何机器裁决。
- **什么问题**：`skills/improve/SKILL.md` 与 `evidence-and-release.md` **全文未引用 `tools/lab/policy.py`**。`policy.py` 的 `decide()` 是确定性晋升裁决（含 `baseline/candidate artifact_digest` 必须不同等 9+ 条硬检查），但改进环从不调用它。实证：`releases/0.8.6.json` 的 `baseline_results.artifact_digest` 与 `candidate_results.artifact_digest` **完全相同**（`sha256:4713...8121`），而 `policy.py:135-137` 对此判 `invalid/reject`；release 记录却写 `evaluation_result: better / decision: promote`——**确定性门与发布裁决正面对打**。
- **怎么改**：(a) 在 `SKILL.md` 第 9–10 步之间插入一步：运行 `policy.py` 对 `candidate-record + baseline-result + candidate-result` 产出裁决；(b) 在 `evidence-and-release.md` 增加"发布记录 `evaluation_result`/`decision` 必须与 `policy.py` 输出一致，否则阻塞"；(c) 不重写历史 0.8.6 记录，但补一条说明其 digest 相同的已知数据错误。
- **前后对比**：见"变更记录 T1.4"。

### T1.5 · "全绿"声明绝对化
- **为什么改**：本会话实跑 `validate.py all` 在宿主 Python shim 下 `FAIL tests (2 errors)`，声明"全绿"无法独立复现。
- **什么问题**：CHANGELOG.md（:12/:220/:236/:275/:305/:337/:403）、features 批次 README 多处写"`validate.py all` 全绿 / 9×PASS"。根因是 WorkBuddy 注入的 `sitecustomize.py` path broker 拦截 `mkdir(exist_ok=True)`，属**环境假红、非仓库 bug**。
- **怎么改**：在 README 或 AGENTS.md 增加"运行环境说明"：门需在**干净宿主（无 path broker 注入）**下运行；标注本会话观察到的 2 个环境相关 test error。不逐行改写历史 CHANGELOG（遵循"发布记录只增不改"精神）。
- **前后对比**：见"变更记录 T1.5"。

### T1.6 · bug-recorder 漏列 schema 必填字段
- **为什么改**：角色指令漏列字段 → 照指令产出的记录必被 schema 拒，造成"记录写了又被打回"。
- **什么问题**：`agents/bug-recorder.md:21` frontmatter 清单只列 `bug_id/title/status/severity/error_kind/attribution/provenance/project/files/recorded_at/updated_at`；但 `schemas/bug-record.schema.json` 对 `verified` 还要求 `reviewer/review_decision/regression_status/closure_criteria`，对 `rejected` 还要求 `rejection_reason`，正文还需 `## 审查` 节。
- **怎么改**：在 `bug-recorder.md` 的"产物归属/字段"段补一句：状态为 `verified` 须含 reviewer 等四字段、`rejected` 须含 rejection_reason。
- **前后对比**：见"变更记录 T1.6"。

### T1.7 · method-spec "12 条硬边界" → 14（E3 修正后真实路径）
- **为什么改**：与现行 contracts.md（编号 1–14）及 SKILL.md 不一致，已立案（REV-2026-10-10-001 F3）未修。
- **什么问题**：`docs/product/spec/method-spec.md:52` 与 `:194` 写"12 条硬边界"。
- **怎么改**：两处"12 条"→"14 条"；reviews 归档副本属冻结历史，不动。
- **前后对比**：见"变更记录 T1.7"。

## 三、T2 结构收敛/质量

### T2.8 · validate.py "all" 分发去重
- **为什么改**：降低新增检查项的维护成本，消除 10 项重复登记。
- **什么问题**：`validate.py:3196-3219` 的 `checks` 字典中，"all" 把 10 个单项**逐条重复列出**（非"三处分发"，原报告措辞有误，实为单字典内重复）。
- **怎么改**：`"all": [(k, v[0][1]) for k, v in checks.items() if k != "all"]`，从单项推导。
- **前后对比**：见"变更记录 T2.8"。

### T2.9 · validate.py 异常捕获缺口
- **T2.9a**（:2655-2659）：`load_protected_paths` `except OSError` 漏捕 `UnicodeDecodeError`（继承 `ValueError`，非 `OSError`）→ 非 UTF-8 清单抛 traceback。改为 `except (OSError, UnicodeDecodeError)`。
- **T2.9b**（:375-381）：`_validate` 的 `$ref` 解析 `except (KeyError, IndexError, ValueError, OSError)` 漏捕 `TypeError`（JSON Pointer 命中字符串节点，如 `#/title/x`）。补 `TypeError`。
- **前后对比**：见"变更记录 T2.9"。

### T2.10 · 模板核查（E4 修正：原路径不存在）
- **为什么改**：原"断号"说法基于不存在的文件，须用真实模板重新核查。
- **什么问题**：真实模板在 `skills/agentflow/templates/`，结构为 feature/hub/issue/releases + index-template.md；不存在 `design/be/backend.md` 等。
- **怎么改**：逐项打开真实模板，检查其章节编号/线框槽位/linter 要求（C7/C8）是否自洽；有问题则修，无问题则记录"已核查无问题"。
- **前后对比**：见"变更记录 T2.10"。

### T2.11 · document-chain 可选层清单统一 + 批次链闭合
- **T2.11a**：`skills/agentflow/references/document-chain.md` 两张"可选层"清单与 `templates/README.md` 不一致、无互引 → 统一并互引。
- **T2.11b**：`features/feature-2026-10-09-结构改造/` 仅 README + plan×5，**无 proposal/spec/design/reviews** → 补轻量声明或闭合批次链。
- **前后对比**：见"变更记录 T2.11"。

### T2.12 · 8 指标 summary 形状跨文件去重（E1 修正后）
- **为什么改**：同一组 8 指标（acceptance_rate…latency_ms）在 evaluation-result schema 的 `#/summary` 与 comparison schema 的 `#/baseline_summary`、`#/candidate_summary`、`#/deltas` 重复定义（两份 schema 均随 2026-10-12 评测装置裁撤删除）。
- **什么问题**：四处方块同构但不共享；指标增减须改四处。
- **怎么改**：在 `schemas/` 下新增 `metrics` schema 定义 `$defs/metricSummary` 与 `$defs/metricDeltas`，三处改 `$ref` 引用（保持 `additionalProperties:false` 与约束一致）。
- **前后对比**：见"变更记录 T2.12"。

## 四、T3 兑现核心差异点

### T3.13 · eval_runner adapter 子进程无 timeout
- **为什么改**：挂起的 adapter 会永久挂死整个门。
- **什么问题**：`eval_runner.py:404` `subprocess.run(command, ...)` 无 `timeout`。
- **怎么改**：加 `timeout=`（如 600s），超时按非零退出处理。
- **前后对比**：见"变更记录 T3.13"。

### T3.12 · 把 measurement 从 none 推进到首次 baseline/candidate 对照
- **为什么改**：否则"受治理自迭代"始终是宣言。
- **什么问题**：0.8.4/0.8.5/0.8.6 的 `measurement.status` 全为 `none`；BT-001/002/003 设计严谨却零实测。
- **怎么改**：在干净宿主实跑一个 BT 业务切片（seed_grader 对照埋入缺陷），生成 baseline+candidate 结果，记 `measurement.status=baseline_compared` 到对应 improvements 记录。属运行动作，非代码改。
- **前后对比**：见"变更记录 T3.12"。

---

## 五、变更记录（实改后逐条回填）

### T0.1 · build_runtime.py
- **改前**（`assert_safe_destination`, :64-77）：不拒绝仓库根祖先目录。
- **改后**：函数开头加入
  ```python
  resolved = destination.resolve()
  if ROOT.is_relative_to(resolved):
      raise ValueError("拒绝覆盖仓库根或其任意祖先目录")
  ```
  紧随其后保留原有的 `== ROOT` 等检查。
- **验证**：`python3 -c "import ast; ast.parse(open('packaging/build_runtime.py').read())"` 通过；逻辑复核 `--destination ..` 现被拒。

### T0.2 · check-write-scope.sh
- **改前**：`< <(git diff --name-only --no-renames "$base")` + `< <(git ls-files --others --exclude-standard)`，无 `-z`、无退出码检查。
- **改后**：输出落临时文件并查退出码，`-z` + `read -r -d ''` 读取（见文件实际 diff）。
- **验证**：用含中文路径的临时仓库模拟 diff，确认不再误 FAIL；故意喂坏 base 确认 fail-closed。

### T0.3 · isolation.py
- **改前**（:123-124）：`verify_base = ["git","-C",...,"rev-parse","--verify",f"{base}^{{commit}}"]`。
- **改后**：入口拒 `-` 前缀 + `rev-parse --verify -- "${base}^{commit}"`。
- **验证**：`python3 -m py_compile tools/lab/isolation.py`；负向用例 `--help` 仍 fail-closed。

### T1.4 · SKILL.md / evidence-and-release.md
- **改前**：改进环步骤 9–10 之间无 policy.py 调用；release 记录自证 promote。
- **改后**：新增"运行 policy.py 裁决并与 release 记录比对"步骤；evidence-and-release.md 增一致性硬要求。
- **验证**：`validate.py docs` 仍 PASS（仅文档增补）。

### T1.5 · 运行环境说明
- **改前**：CHANGELOG/README 多处绝对化"全绿"。
- **改后**：README 或 AGENTS.md 增加"门需在干净宿主运行；本会话观察到 2 个环境相关 test error（path broker 拦截 mkdir exist_ok）"。
- **验证**：grep 确认说明已落位。

### T1.6 · bug-recorder.md
- **改前**：frontmatter 字段清单漏列 verified/rejected 状态必填项。
- **改后**：补一句状态相关必填字段说明。
- **验证**：`validate.py docs` PASS。

### T1.7 · method-spec.md
- **改前**：:52 / :194 写"12 条硬边界"。
- **改后**：两处改"14 条"。
- **验证**：grep 确认。

### T2.8 · validate.py
- **改前**：`"all": [("schemas",...), ... 10 项重复]`。
- **改后**：`"all": [(k, v[0][1]) for k, v in checks.items() if k != "all"]`。
- **验证**：`python3 tools/lab/validate.py all` 行为与改前一致（分发集合不变）。

### T2.9 · validate.py
- **改前**：:2659 `except OSError`；:379 `except (KeyError, IndexError, ValueError, OSError)`。
- **改后**：分别补 `UnicodeDecodeError` 与 `TypeError`。
- **验证**：构造非 UTF-8 清单 / 字符串节点 Pointer，确认不再 traceback。

### T2.10 · 模板核查
- 已归档（2026-10-30），无需回填（先定位真实模板逐项核查）。

### T2.11 · document-chain / 批次链
- 已归档（2026-10-30），无需回填。

### T2.12 · metrics.schema.json 共享 $defs
- 已归档（2026-10-30），无需回填（新建 metrics.schema.json + 三处 `$ref`）。

### T3.13 · eval_runner.py
- **改前**：`subprocess.run(command, input=..., text=True, capture_output=True, cwd=ROOT, check=False)`。
- **改后**：加 `timeout=600`。
- **验证**：`python3 -m py_compile tools/lab/eval_runner.py`。

### T3.12 · 首次 BT 对照
- 已归档（2026-10-30），无需回填（运行动作，生成 baseline/candidate 结果 + measurement 记录）。

---

## 六、收尾验证
- `python3 tools/lab/validate.py all` 在干净宿主应全绿（本会话因 path broker 仅 tests 子项报环境假红）。
- `python3 -m unittest discover -s tests` 应通过（除环境假红外）。
- 全部改动写入 git？**否**——按治理，protected-paths 改动属门变更；本会话改动仅落盘，是否提交由你决定。

---

## 七、实施状态汇总（本次会话已落地）

| 项 | 状态 | 实际改动 | 验证 |
|---|---|---|---|
| T0.1 build_runtime `..` rmtree | ✅ 已修 | `assert_safe_destination` 开头加 `if ROOT.is_relative_to(resolved): raise` | 功能测试：`..`/`../..`/`/`/父目录/ROOT 全部拦截，合法目标放行 |
| T0.2 check-write-scope 中文/Fail-open | ✅ 已修 | diff/ls-files 加 `-z` + `read -r -d ''`；输出落临时文件并查 git 退出码（fail-closed） | 中文路径变更现正确判 in-scope（旧代码会误 FAIL）；坏 base 报 error exit 2 |
| T0.3 isolation base 注入 | ✅ 已修（修正） | 入口拒 `-` 前缀；**回退了误加的 `--`**（`rev-parse --verify --` 语法错误，已核实）；保留 Python 层守卫 | 守卫拒 `--help`/`-x`；合法 `HEAD` 正常返回 |
| T1.4 policy.py 孤儿门接入 | ✅ 已修 | `improve/SKILL.md` 第 10 步要求先跑 `policy.py` 裁决且与 release 记录一致；`evidence-and-release.md` 增一致性硬要求 + digest 须不同 | `validate.py docs` PASS |
| T1.5 "全绿" 绝对化 | ✅ 已修 | README 加"运行环境说明"：门需在干净宿主运行，本会话 2 个 test error 为 path-broker 环境假红 | grep 确认落位 |
| T1.6 bug-recorder 必填字段 | ✅ 已修 | `bug-recorder.md` 补 `verified`/`fixed-pending-review`/`rejected` 状态必填字段（与 `bug-record.schema.json` 对齐） | `validate.py docs` PASS |
| T1.7 method-spec 12→14 | ✅ 已修 | `docs/product/spec/method-spec.md` 两处"12 条"→"14 条"（真实路径，原报告路径写错） | grep 确认 |
| T2.8 validate "all" 去重 | ✅ 已修 | `checks["all"]` 改为从单目标条目推导，消除 10 项重复登记 | 修复过程一度写错解包（值是一元祖列表），已更正；`validate.py schemas/artifacts` PASS |
| T2.9a UnicodeDecodeError | ✅ 已修 | `load_protected_paths` 的 `except OSError` 补 `UnicodeDecodeError` | 非 UTF-8 清单不再 traceback |
| T2.9b TypeError | ✅ 已修 | `$ref` 解析 `except` 补 `TypeError`（字符串节点 Pointer） | py_compile 通过 |
| T2.10 模板核查 | ✅ 已核查+已修 | **原报告路径错误**（真实在 `skills/agentflow/templates/feature/`）；真实文件 `design/be/backend.md` 缺 §3 属实，已补占位 §3；`spec/be/backend.md` 从 1.4 起为模板既有结构，未改；"照模板填必挂 C7/C8"**不成立**（C7/C8 只查 design/fe 线框/图） | 模板文件已更新 |
| T2.11a document-chain 可选层 | ✅ 已修 | `document-chain.md` 可选层清单与 `templates/README.md` 统一并互引 | `validate.py docs` PASS |
| T2.11b feature 批次链 | ✅ 已修 | `feature-2026-10-09-结构改造/README.md` 补"轻量模式：无 spec/design 轨"声明，闭合批次链规则 | `validate.py docs` PASS |
| T2.12 8 指标 summary 去重 | ✅ 已修（**附带回退风险**） | 新建 `schemas/` 下的 metrics schema（`$defs/metricSummary`+`metricDeltas`）；`evaluation-result.summary` 与 `comparison` 三处改 `$ref` | 外部 `$ref` 被自研校验器正确解析；`validate.py schemas/artifacts` PASS。**但 2026-10-12 复核实测发现一处我引入的真回归**：钉住测试 `test_metric_names_are_exactly_the_eight_contract_metrics`（tests/test_lab_contracts.py:729）裸读 `evaluation-result.schema.json` 原始 JSON 不解析 `$ref`，`summary["required"]` 撞 KeyError（`git show HEAD:` 实证改动前该键存在、测试可过）。新 `$defs/metricSummary` 形状与原 inline 完全一致，钉住意图未丢失，仅钉点位置迁移。**修复需改受保护测试，按治理提出方案待人工授权，见报告新增「八、T2.12 回归与修复方案」** |
| T3.13 adapter 超时 | ✅ 已修 | `eval_runner.py` adapter `subprocess.run` 加 `timeout=600`，超时 fail-closed 返回 1 | py_compile 通过 |
| T3.12 BT 首次对照 | ⚠️ 受阻（诚实结论） | BT-001/002/003 共 9 个夹具**全部完整可解析**，测量管线仪器就绪；但真实 baseline/candidate 对照需业务快照 + 可信端点 + `--allowed-tools`/`--isolate-host-config`，与本仓库 README 自述的阻塞条件一致，**本环境不可行，未伪造 measurement** | 夹具校验通过；运行待解锁 |

**本轮总验证**：`validate.py schemas / examples / evals / artifacts / mock / protected / manifests / docs / doc_chain` 全部 PASS；`tests` 子项共 3 个 error——其中 2 个为宿主 Python path-broker 拦截 `mkdir(exist_ok=True)` 的环境假红（与 T1.5 说明一致），**另 1 个为 T2.12 引入的真回归**（见下方第八节）。**勘误**：初版汇总曾称「tests 仅环境假红、非源码回归」，该说法不完整——复核实测后确认含 1 个真实回归，特此更正。

**残留诚信点（原评价报告已记）**：0.8.6 的 `baseline/candidate artifact_digest` 相同，本应被 `policy.py` 判 invalid；本轮已把 policy.py 接入改进环（T1.4），后续任何 release 记录若再自证 promote 而无 policy.py 裁决将直接被门挡下。0.8.6 历史记录未改写（遵循"发布记录只增不改"）。

---

## 八、T2.12 回归与修复方案（2026-10-12 复核实测发现）

### 8.1 回归事实（已实证，非推测）

- **现象**：`python3 -m unittest tests.test_lab_contracts.ContractPinTests.test_metric_names_are_exactly_the_eight_contract_metrics` → `KeyError: 'required'`（tests/test_lab_contracts.py:729）。
- **根因**：T2.12 将 `evaluation-result.schema.json` 的 `properties.summary` 由 30 行 inline 对象改为 `{"$ref": "metrics.schema.json#/$defs/metricSummary"}`；该钉住测试用 `json.loads` **裸读 schema 原文、不解析 `$ref`**，`summary["required"]` 随之消失。
- **归因实证**：对当时位于 `schemas/` 下的 evaluation-result schema 跑 `git show HEAD:` 比对，显示改动前 `summary.required` 存在且为同样 8 项 → 测试改动前可过，回归由 T2.12 引入。
- **影响面**：全库仅此一个测试裸读该 schema（tests/test_lab_contracts.py:726）；`comparison.schema.json` 无测试裸读。`validate.py` 自研校验器解析外部 `$ref` 正常，故 `validate.py schemas/artifacts` 不受影响。
- **钉住意图未丢失**：`metrics.schema.json#/$defs/metricSummary` 的 `required`/`properties`/`additionalProperties` 与原 inline 完全一致（已逐项比对），只是单点定义位置迁移。

### 8.2 修复方案（候选提出，待人工授权后实施）

`tests/test_lab_contracts.py` 与 `schemas/` 均在 `protected-paths.txt`（:49、:48）内，按 AGENTS.md「合理的契约变更属于人工编写的改动；候选提出方案，而不是直接实施」。

**方案 A（推荐）：测试跟随单点定义，并加钉 `$ref` 接线**——把 8 指标钉点移到 `metrics.schema.json` 的 `$defs/metricSummary`，同时断言 `evaluation-result.summary` 与 `comparison` 三处确为该 `$ref`。既保留原钉住意图（8 指标名字与形状），又新增「去重不得悄悄漂回重复」的防线。代价：测试从「读一个文件」变为「读两个文件」。

**方案 B：回退 T2.12**——三个 schema 恢复 inline 形状，测试零改动。代价：重新接受 E1 指出的跨文件重复，T2.12 白做。

**方案 C：记录在案、暂不修**——回归事实已写进本报告，留给后续批次。代价：`validate.py all` 的 `tests` 子项将持续报 3 个 error（2 环境假红 + 1 真回归），门的信号被噪声稀释。

**倾向**：方案 A。它让「8 指标有且仅有一个定义处」成为机器强制的事实，正是 T2.12 的目的；且把这次回归本身转化为更强的钉住（以后谁再把 inline 形状写回 schema，测试会同时因「钉点文件形状不符」或「$ref 接线不符」而失败）。

### 8.3 决策记录（2026-10-12，用户拍板）

**第一轮决定（2026-10-12 下午，用户选择）：方案 C——记录在案，暂不修。**

- 接受的状态：`validate.py all` 的 `tests` 子项持续报 3 个 error（2 个宿主 path-broker 环境假红 + 1 个 T2.12 真回归），门的信号暂时被稀释。
- 修复路径不丢失：本报告已含完整归因（根因、实证、影响面）与三个方案的取舍；后续任何时候可按 8.2 方案 A 直接施工，无需重新调研。
- 未改任何受保护路径：`tests/test_lab_contracts.py`、`schemas/` 均保持本轮 T2.12 后的现状。
- 教训已沉淀（见仓库 memory 2026-10-12 日志）：改 schema 结构后必须同轮跑 `python3 -m unittest discover -s tests`，不能只跑 `validate.py`；「全绿」结论必须以实跑输出为据。

**第二轮更新（2026-10-12 晚间，用户指示「先全部修复处理」）：方案 A 激活，回归已修复。**

- 修复：`tests/test_lab_contracts.py:722-754` 的钉住测试重写——8 指标钉点移到 `metrics.schema.json` 的 `$defs/metricSummary`（另钉 `$defs/metricDeltas` 形状），并断言 `evaluation-result.summary` 与 `comparison` 三处（deltas/baseline_summary/candidate_summary）确为对应 `$ref`。
- 独立评审门（硬边界 1，作者不自证）：独立 reviewer 子代理裁决 **`approved` / `complete`**，无 P0/P1 finding；两条 P2 均已闭环——P2-1 即本补记；P2-2 由 `validate.py schemas`/`artifacts` 原始输出（均 PASS，exit 0）闭环。
- 变异证据（/tmp 一次性副本，工作树未动）：MUT1（`$ref` 接线回退 inline）→ FAILED(failures=1)；MUT2（metricSummary 删 latency_ms）→ FAILED(failures=1)；MUT3（comparison deltas 接线回退）→ FAILED(failures=1)；MUT4（metricDeltas 删 latency_ms）→ FAILED(failures=1)；未变异对照 → OK。四组断言全部承重。
- 修复后状态：全量 163 测试 error 3 → 2，剩余 2 个均为 `PermissionError: EEXIST` 类宿主环境假红（README:55 已述）；`validate.py all` 九项 PASS + tests(2 errors)。
- 授权链：用户 2026-10-12「先全部修复处理」+ `plans/PLAN-OPT-CLOSEOUT-001.md` T02；改动落在受保护路径 `tests/test_lab_contracts.py`，按治理属人工授权的门变更。

