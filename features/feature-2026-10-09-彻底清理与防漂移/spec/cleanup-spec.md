# 清理规格（spec）— 逐项清单 + 门变更规格

> 每条：现状（带 `file:line` 证据）→ 目标状态 → 验证方式。执行状态与证据回写在 `plan/cleanup-plan.md`。

## 1. 断链修复（相对链接解析失败）

| # | 位置 | 现状 | 目标 |
| --- | --- | --- | --- |
| L1 | `docs/iteration-log.md:6` | 链到 `next-session-handoff.md`（已迁 `_archive/`） | 改指 `../_archive/handoff-2026-10/next-session-handoff.md` |
| L2 | `docs/iteration-log.md:10` | 链到 `../examples/bug-records/`（已退役） | 核实后改指现行 `../examples/issues/`（或去链改文字） |
| L3 | `docs/system-guide.md:8` | 链到 `audit-2026-09-18-followups.md`（已迁 `_archive/`） | 改指 `../_archive/audit-2026-09/followups.md` |
| L4 | `packaging/runtime/skills/.../SKILL.md` | 生成树内指向记录根的链接（`packaging/README.md` 已声明限制） | 不改生成树；断链检查把 `packaging/runtime/` 列入排除清单并在检查注释声明理由 |

## 2. 退役路径提及收敛（现行文档不得以现行口吻使用旧路径）

| # | 位置 | 现状 | 目标 |
| --- | --- | --- | --- |
| S1 | `index.md:29-31` | 已完成迁移清单逐条列出 `records/*` 旧路径 | 收敛为一行指针（指向迁移对照表），删除旧路径枚举 |
| S2 | `docs/system-guide.md:193` | §6 流程图节点写 `bugs/<日期>/<slug>.md` | 改为 `issues/ISS-<YYYY>-<NNN>-<slug>.md` |
| S3 | `docs/system-guide.md:197` | 同图节点写 `tests/<项目>-<功能>/` | 改为 `features/<批次>/testing/<项目>-<功能>/` |
| S4 | `docs/system-guide.md:198` | 同图节点写 `improvement/{...}/` | 改为 `improvements/` + `releases/`（两个记录根） |
| S5 | `docs/spec-fact-check-design.md:190` | 悬空引用 `next-session-handoff.md:227` | 加 `_archive/handoff-2026-10/` 限定 |
| S6 | `plans/PLAN-BUSINESS-EVAL-001.md:94` | 未决项行写「进 `records/` 还是 examples/」 | 改为现行术语（记录根 / examples） |
| 保留 | `docs/host-platform-facts.md:39` | 历史引文、位于内联码（引文豁免） | 不改写；由检查的内联码豁免覆盖 |

## 3. 陈旧计数（「九项」/「9 项」/「nine checks」）

统一改法：**去数字**，清单以 `validate.py all` 运行输出与 `AGENTS.md` 为真源；确需枚举处补上 `doc_chain` 一行。清零口径仅指现行文档；历史记录与历史载体按设计保留时点数字。

| # | 位置 | 处理 |
| --- | --- | --- |
| C1 | `docs/system-guide.md:43`（§1 图）、`:218`（§7 标题）、`:301`（§9 第 3 条） | 去数字；§7 表补 `doc_chain` 行 |
| C2 | `README.md:58`（"runs nine checks" 且漏 `doc_chain`） | 改「全套检查」并补 doc-chain self-test 项 |
| C3 | `docs/product/spec/method-spec.md:106`（S8）与 `:199` | 去九项计数、清单补全 |
| C4 | `docs/product/spec/acceptance-matrix.md:17`（S8） | 去计数 |
| C5 | `docs/product/design/product-design.md:112` | 去计数 |
| C6 | `docs/product/proposal/proposal.md:73`（OQ-1） | 去计数 |

## 4. 0.8.6 评审遗留收口

| # | 项 | 现状 | 目标 |
| --- | --- | --- | --- |
| N4 | 条款与机器豁免字面歧义 | `document-chain.md:275` 写「白话（代号）」或「代号+白话」成对；机器豁免为括注两形态（`code` 前后成对） | 条款改写为与机器一致的两个括注形态（`白话（代号）`/`代号（白话）`），明确非括注并排不算豁免；不动 `doc_chain.py`（机器行为已由自测 case 27/30 钉住） |
| N6 | 「模板写前提醒」未点名两新形态 | 2026-09-22 评审遗留：模板侧提醒未含「代号裸用 / 模式词分域」 | 定位「写前提醒」落点后补齐两形态点名（定位证据回写计划） |
| N7 | `validate.py:99` 陈旧注释 | 受保护文件，待人工门 | 复核当前 HEAD：若 0.9.0 重写已消解则记「已消解 + 证据」；若仍在则随本批门变更修复 |

## 5. 本地残留删除

| # | 对象 | 判定 |
| --- | --- | --- |
| D1 | `command-code-session-26f9cd50.html`（574 KB） | 已被 `.gitignore` 忽略、非仓库内容；用户批准删除 |
| D2 | `command-code-session-78915404.html`（2.5 MB） | 同上 |
| D3 | `.agentflow-records.sqlite3`（1.5 MB） | 一次性 FTS5 索引，可 `record_store.py index` 重建；用户批准删除 |

## 6. 门变更规格（`validate.py` 的 `docs` 检查扩充，纯加法）

在 `validate_doc_consistency()` 内新增两组断言（沿用既有错误上报形态）：

**G1 断链解析**：遍历全仓 `*.md`（排除：`_archive/`、生成树 `packaging/runtime/`、`.git/`），剥离围栏代码块（mermaid 图除外，图是内容）与行内代码后解析 `](target)`；跳过 `http(s)://`、`mailto:`、`#`、`<…>` 与绝对路径；其余相对目标按文件所在目录解析，不存在即报错。

**G2 退役路径扫描**：同一遍历范围内（另排除历史载体 `CHANGELOG.md`、`docs/iteration-log.md`——其旧路径为历史原文），逐行扫描退役 token：`records/`、`bugs/`、`improvement/`、`docs/audit-2026-09-18`、`next-session-handoff`；跳过非 mermaid 围栏内与内联码内内容（引文不扫；mermaid 图是内容，照扫）；另豁免迁移执行记录目录 `features/feature-2026-10-09-结构改造/`（旧→新映射是其内容，机器面单点声明）；`next-session-handoff` 出现在 `_archive/handoff-2026-10/` 路径前缀下时豁免（指向冻结原文的合法引用）。

**判别要求（写入 `tests/test_lab_contracts.py`）**：

- 修复前树（`/tmp/agentflow-prefix-72a1b5a` 叠加新检查器）运行 `docs`：必须命中现存全部待修项（红）；
- 修复后树运行 `docs`：零发现（绿）；
- near-miss 反例不误报：`_archive/` 内旧路径、围栏/内联码引文、`_archive/handoff-2026-10/next-session-handoff.md` 合法引用、`improvements/`（含 `improvement` 前缀但非退役 token）、`releases/`。

## 7. 验收命令（收口时逐条执行并留原始输出）

```sh
python3.12 tools/lab/validate.py all          # 全套全绿（exit 0）
python3.12 tools/lab/doc_chain.py --self-test # 自测全过
python3.12 -m unittest discover -s tests      # 回归全绿
python3.12 tools/lab/validate.py installed    # 装入 cache/0.10.0 后 PASS
```

故障注入（一次性副本）：在 `/tmp` 修复后树的副本中故意破坏一处链接 → `docs` 必须 FAIL；恢复后复跑必须 PASS（未观察的恢复不算恢复）。
