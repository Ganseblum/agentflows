# 门基线与既有检查的改动前对照（本批 T01 与 T10 的证据载体）

> 为什么需要这份文件：`docs/features/feature-2026-10-13-质量提升/plan/PLAN-QUALITY-001.md` 的 T01 行
> 原本把基线写在 `/tmp/quality-baseline/validate-all.txt`，并在 2026-10-22 自述「已随临时目录散失，
> 不可复核」。本批新增的 C23 检查正是不放过这种状态，所以先把载体落到仓内。
> 本文件的原始输出均在一次性副本里采集，真实工作树只读。

## 采集环境（可复现）

- 副本：`cp -R` 本仓到 `/tmp/base-96e0383`，随后在副本内 `git checkout -- . && git clean -ffd`，
  回到 `96e0383`（`git status --short` 输出为空，`git log -1` =
  `96e0383 docs(cleanup): 角色计数口径修正、0.12.0 状态回写与索引瘦身`）。
- 解释器：`/opt/homebrew/bin/python3.12`（默认 `python3` 是 Xcode CLT 的 3.9.6，
  `validate.py` 会直接拒绝运行并报「interpreter too old」）。
- 静态检查依赖：`python3.12 -m venv /tmp/qtools-312 && /tmp/qtools-312/bin/pip install -r requirements-dev.txt`
  → `ruff 0.17.1`、`mypy 2.4.0 (compiled: yes)`。lint 项以 `sys.executable -m ruff` 调用，
  所以必须用这个 venv 的解释器跑 `validate.py`，否则该项记为未运行而不是通过。
- 采集时间：2026-10-23 00:2x（GMT+8），即 2026-10-22T16:2xZ。

## 改动前基线（`96e0383`，逐字输出）

```text
$ /tmp/qtools-312/bin/python -B tools/lab/validate.py all
PASS schemas
PASS examples
PASS artifacts
PASS protected
PASS manifests
PASS docs
PASS tests
PASS doc_chain
PASS doc_chain_live
PASS decision_gate
PASS lint
```

```text
$ python3.12 -B tools/lab/validate.py all        # 未装 ruff/mypy 的解释器
PASS schemas
...
PASS decision_gate
FAIL lint (2 error(s))
  - lint/ruff: ruff is not installed in this interpreter; run `pip install -r requirements-dev.txt`
  - lint/mypy: mypy is not installed in this interpreter; run `pip install -r requirements-dev.txt`
```

（同一条命令在两种解释器下给出两种结论——这正是「无法复现的检查记为未运行」的现场，
所以本批把带依赖的那次作为基线，不带依赖的那次附在旁边说明差异。）

```text
$ python3.12 -B tools/lab/doc_chain.py --self-test
85/85 self-test cases pass

$ python3.12 -B -m unittest discover -s tests
Ran 78 tests in 1.982s

OK

$ /tmp/qtools-312/bin/python -B tools/lab/doc_chain.py docs/features/feature-2026-09-19-产品线完善/
PASS doc-chain docs/features/feature-2026-09-19-产品线完善/

$ /tmp/qtools-312/bin/python -B tools/lab/doc_chain.py docs/features/feature-2026-10-13-质量提升/
PASS doc-chain docs/features/feature-2026-10-13-质量提升/
```

## 基线里已经存在、但当时没有任何门能看见的两个缺陷

| 编号 | 事实 | 本批的处置 |
| --- | --- | --- |
| 目标失踪 | `docs/features/feature-2026-10-13-质量提升/proposal/prd.md` §1.2 把「CI 在真实 runner 上连续两次通过」列为 G2 目标并在 §四 决策为「做」；同批 `spec/be/backend.md` §5 的六个模块、`spec/qa/acceptance.md` 的验收点与 `plan/PLAN-QUALITY-001.md` 的十个任务行都不含 CI，只在 `design/be/backend.md` 的依赖表里作为「强依赖，结果未知」出现过一次 | 新增 C22 目标承接闭环检查；该批次是否补表按 `docs/PENDING-DECISIONS.md` 第 11 条拍板（推荐只对新批次生效） |
| 证据散失 | `docs/features/feature-2026-10-13-质量提升/plan/PLAN-QUALITY-001.md` 的 T01 与 T05 行把证据指向 `/tmp/…`，并自述已散失，状态仍是 ☑ 已完成 | 新增 C23 证据在场检查；本文件即 T01 类证据的替代载体 |

## 改动后对照（本批落地后复跑，逐字输出附后）

待本批全部检查跑绿后由 T10 回写；在回写之前本节保持空置，不预先写结论。
