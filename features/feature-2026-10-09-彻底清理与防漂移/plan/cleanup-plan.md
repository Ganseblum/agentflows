# 彻底清理与防漂移 — 执行计划

- **plan_id**：`feature-2026-10-09-彻底清理与防漂移/plan/cleanup-plan`
- **状态**：执行中
- **基线**：`plan/baseline-2026-10-09.md`（修订号 `72a1b5a`）
- **规格**：`spec/cleanup-spec.md`（L/S/C/N/D/G 编号即本表任务依据）
- **规则**：任务状态枚举 `☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做`；完成时只在「状态」「证据回写」两列做最小回写。

## 进展概览

- 一行进度：T01–T15 完成（评审两轮：round 1/round 2 均 `changes_requested`，逐条修复后收口）。
- 阻塞：无。
- 下一步：无（提交随本批落盘；不推送）。

## 任务清单

| # | 任务 | 优先级 | 代码/文档落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 基线存档：修订号 + `validate.py all`/`installed` 逐字输出 | P0 | `plan/baseline-2026-10-09.md` | — | ☑ 已完成 | `all` 10×PASS EXIT=0；`installed` FAIL（源 0.9.0 无快照，预期漂移）逐字入档 |
| T02 | 批次建档：README/proposal/spec/plan + 修复前快照 | P0 | `features/feature-2026-10-09-彻底清理与防漂移/`、`/tmp/agentflow-prefix-72a1b5a` | T01 | ☑ 已完成 | 五件落盘；快照 md5 与源一致（system-guide.md 双向核对） |
| T03 | 断链修复 L1–L3（L4 入检查排除清单，随 T07） | P0 | `docs/iteration-log.md`、`docs/system-guide.md` | T02 | ☑ 已完成 | L1→`../_archive/handoff-2026-10/…`；L2→`../examples/issues/`；L3→`../_archive/audit-2026-09/followups.md` |
| T04 | 路径收敛 S1–S6 + 计数 C1–C6 | P0 | `index.md`、`docs/system-guide.md`、`README.md`、`docs/product/*`、`docs/spec-fact-check-design.md`、`plans/*` | T03 | ☑ 已完成 | S1 index 收敛一行指针；S2–S4 §6 三节点 + §1/§7/§9 去数字并补 `doc_chain` 行；S5/S6 改指与措辞；C1–C6 全改；复核=现行文档零残留（历史记录与历史载体保留时点数字） |
| T05 | 遗留收口 N4/N6/N7（条款措辞/模板写前提醒/陈旧注释；N6 附定位证据、N7 复核结论） | P0 | `skills/agentflow/references/document-chain.md`、`skills/agentflow/templates/README.md` | T04 | ☑ 已完成 | N4 条款对齐括注两形态（document-chain.md:274-277）；N6 写前自查回归并点名两形态（templates/README.md:4）；N7 复核=0.9.0 重写已消解（validate.py:116-121 注释自记教训），无需改 |
| T06 | 本地残留删除 D1–D3 | P0 | 根目录 `command-code-session-*.html`×2、`.agentflow-records.sqlite3`（已删；对象清单见 `spec/cleanup-spec.md` §5） | T02 | ☑ 已完成 | `rm -v` 输出三件逐字入账 |
| T07 | 门变更 G1/G2：`validate.py` docs 检查扩充（含排除清单与注释声明） | P0 | `tools/lab/validate.py` | T03–T05 | ☑ 已完成 | 新增 `validate_live_doc_references`（链接+mermaid 内容面+退役 token+两处豁免单点声明）；接线 docs 检查；docstring 与 `tools/lab/README.md` 同步 |
| T08 | 门变更：`tests/test_lab_contracts.py` 判别用例（红能力 + near-miss） | P0 | `tests/test_lab_contracts.py` | T07 | ☑ 已完成 | 新增 2 用例（good/bad 夹具 + 豁免夹具含 mermaid）；`-k live_doc` OK；全套 159 OK |
| T09 | 红/绿证据：修复前树叠加新检查器必须命中全部待修项；修复后树零发现 | P0 | `/tmp/agentflow-prefix-72a1b5a` | T07、T08 | ☑ 已完成 | 红=9 项（逐字留档 `plan/evidence-2026-10-09.md`）；绿=当前树 `PASS docs` EXIT=0 |
| T10 | 故障注入：/tmp 副本破坏一处链接 → FAIL；恢复 → PASS | P1 | /tmp 一次性副本 | T09 | ☑ 已完成 | 注入后 FAIL 1 项（no-such-target.md）；还原后 PASS（已观察，原文入证据档） |
| T11 | 全量验证：`all` + self-test + unittest + `isolation.py check-diff` | P0 | — | T09、T10 | ☑ 已完成 | all 10×PASS；self-test 38/38；unittest 159 OK；isolation（两门文件在副本还原后）blocked=[] |
| T12 | 版本刷新：五清单 0.10.0 + CHANGELOG 条目 + iteration-log 新节 | P0 | 五 manifest、`CHANGELOG.md`、`docs/iteration-log.md` | T11 | ☑ 已完成 | 五清单一致（`manifests` PASS）；CHANGELOG 0.10.0；台账 0.10.0 节 + 总览行 + 0.9.0 补记 |
| T13 | 运行时重建 + 本地快照安装 + `installed` 转绿 | P0 | `packaging/`、`~/.zcode/.../cache/agentflow-local/agentflow/0.10.0` | T12 | ☑ 已完成 | `build_runtime.py` WROTE；装入 cache/0.10.0；`validate.py installed` PASS |
| T14 | 独立评审门（author ≠ verifier）：reviewer 审原始 diff 与验证输出；changes_requested 则一轮修复再审 | P0 | 评审结论入批次 `reviews/` 与 episode | T13 | ☑ 已完成 | round 1 `changes_requested`（F1/F2 必改 + F3–F7 建议）→ 修复轮（证据档改围栏、F2–F7 逐条修复、F4 判别力补钉）→ round 2 `changes_requested`（N1 重复行/N2 并发写者本地化/N3 措辞）→ N1/N3 修复、N2 按并发写者纪律保持未提交不纳入提交；复跑全绿后按先例收口；两轮逐条见 `reviews/review-2026-10-09-001.md` 与 EP-20261009-002 |
| T15 | 收口：episode EP-20261009-002 + README 执行记录与变更前后回写 + 单次提交（不推送） | P0 | `episodes/2026-10-09/`、批次 README、批次 `reviews/` | T14 | ☑ 已完成 | EP-20261009-002 落仓（含两轮 review_roundtrips 与并发写者观察）；`reviews/review-2026-10-09-001.md` 落档；单次提交（不含并发写者改动；不推送） |

## 接口与共享机制

- `validate.py` 的 `docs` 检查（`validate_doc_consistency`）是既有门的一部分：本批只做纯加法扩充，保持既有五组断言不变；新增排除清单（`_archive/`、`packaging/runtime/`、历史载体）在代码注释中逐条声明理由。
- `tests/test_lab_contracts.py` 为受保护清单条目；新增用例随本批门变更一并落地并被 `validate.py tests` 的声明内容检查覆盖（不新增测试文件，`EXPECTED_TEST_FILES` 不变）。
- 版本号单一真源：五清单 + `CHANGELOG.md`；`docs` 的版本散文守卫继续生效。

## 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
python3.12 tools/lab/validate.py installed
python3.12 tools/lab/isolation.py check-diff --candidate <tree> --base <frozen-parent>
```

## 未决项

| # | 事项 | 阻塞性 | 关闭条件 |
| --- | --- | --- | --- |
| U1 | ZCode 客户端刷新 marketplace + 重装到 0.10.0 | 非阻塞（客户端动作） | 用户侧完成后 `validate.py installed` 对 0.10.0 快照 PASS |
