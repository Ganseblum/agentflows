# 验收规格：全面修正与瘦身批（QA 轨）

## 0. 适用范围与不适用声明

- 本批是方法仓的文档、记录与门判据改动，**无用户可见界面**：`spec/ui` 与 `design/ui` 轨未启用，
  理由为无视觉与交互变更（原型 `N/A: 无用户界面`）。
- **埋点 N/A**：不新增用户行为事件、不改事件表结构与看板口径；理由随 proposal §3。
- 结论等级口径：通过 / 有条件通过 / 不通过。**门未全绿时本批只能给「有条件通过」**，
  并附实际覆盖比例。

## 1. 模块验收块

| 验收点 | 关联模块 | 断言（会失败的形态） | 判定方式 | 状态 |
| --- | --- | --- | --- | --- |
| G1-AC-01 | M-A-01 | §2.1 吸收映射表内的项在本批计划出现 0 次或 ≥2 次；表外旧批任务被误报为已吸收 | 逐条核 §2.1 映射表；表外任务留在原批 | ☑ design/qa/testing.md §2.1 吸收映射表 + T02 回写 |
| G1-AC-03 | M-A-03 | 归并后新增了第二个顶层记录类型或第二个批次目录 | `find docs/features -maxdepth 1 -type d` 只多出本批一个目录；`LIVE_RECORD_ROOTS` 未改写 | ☑ 只新增本批目录；LIVE_RECORD_ROOTS 未改 |
| G1-AC-04 | M-A / T17 | 测试链默认序列缺评审角色，或评审范围口径仍写成「由简报决定」 | `roles.md` 工作链「测试」行含 `Reviewer`；`document-chain.md` 与 `agents/reviewer.md` 命中「由 diff 形状决定」 | ☑ roles.md 测试行含 Reviewer；diff 形状口径两处命中 |
| G1-AC-02 | M-A-02 | 四处导航面对同一批次给出互斥状态说法 | 一条命令打印四处原文行对照；出现互斥即红 | ☑ 四处导航面同口径（README/features/index/todo 当日实测） |
| G2-AC-01 | M-B-01 | 拍板口检索不到某条仍开放的未决项 | 可计数脚本逐条比对，命中 0 即红并打印该行 | ☑ PENDING 无未决行，表后逐条出处 |
| G2-AC-02 | M-B-02 | `AGENTS.md` 或链契约缺分工行 | 两文件检索该句原文，缺任一即红 | ☑ AGENTS 与 document-chain 分工行 |
| G2-AC-03 | M-B-03 | 打标批次里「需用户抉择且尚未关闭」的待决行不含拍板口编号，门仍绿 | `doc_chain.py --self-test` 负例夹具（构造该形态必须判红）+ 对本批目录实跑 PASS | ☑ self-test C18 01–08 + 本批目录 PASS |
| G3-AC-01 | M-C-01 | 记录字段指向不在盘上的仓内路径，`validate.py artifacts` 仍 PASS | 新增回归用例（`/tmp` 副本注入 → 判红）；实跑 `validate.py artifacts` 绿 | ☑ tests/test_gate_records.py 通过 |
| G3-AC-02 | M-C-02 | 裸 `N/A`（无理由）被判绿 | 夹具断言 finding 数 = 1 | ☑ 裸 N/A 用例通过 |
| G3-AC-03 | M-C-03 | 正文散文里的退役路径被误判为缺陷（判据过宽） | 夹具断言同一路径在正文与字段各出现一次时 finding 数 = 1 | ☑ 散文不误伤用例通过 |
| G3-AC-04 | M-C-04 | 改写后仍有字段级悬空引用 | 全仓扫描脚本计数 = 0，且改写前后两个计数都落进计划证据列 | ☑ 字段级失效 14 → 0 |
| G4-AC-01 | M-D-01 | 源 schema 改了而生成树未重建（`manifests` 红） | `validate.py schemas` + `validate.py manifests` 双绿 | ☑ schemas + manifests PASS |
| G4-AC-02 | M-D-02 | `review_tier: L0` 且 `dispatch_errors` 缺席的记录被判绿 | `tests/test_gate_records.py` 四例全过；变异式反证：删掉判据后该用例必须转红 | ☑ RT 用例 + 变异反证 |
| G4-AC-03 | M-D-03 | 本批评审记录缺 `review_tier` 或档位无实测依据 | `validate.py artifacts` 绿 + 派发原始返回落 `testing/` | ☑ reviews 001–004 均 review_tier: L2；005 为 L0 降级留痕 |
| G5-AC-01 | M-E-01 | 四文件里同一规则存在多份副本（2026-10-29 用户拍板 C：不设总量上限，判据改为「副本是否消除」） | 逐行比对 `skills/agentflow/references/carrier-map.md` 的「规则 / 权威载体 / 副本处置」三列，副本处置为「保留」或「已移出」以外的行数须为 0；`wc -l` 只作观测值打印，不再作判据 | ☑ carrier-map 副本处置逐行；行数仅观测值 |
| G5-AC-02 | M-E-02 | 同步义务表述仍在（含等价改写） | 先打印命中原文再判；命中 0 才绿 | ☑ 同步义务检索 0 命中 |
| G5-AC-03 | M-E-03 | 归属表某行权威路径不存在或锚点不命中 | `tools/lab/validate.py docs` 绿，且 `tools/lab/gate/docs.py:271` 的 `validate_carrier_map` 逐行打印命中 | ☑ validate.py docs PASS |
| G5-AC-04 | M-E-04 | 收敛把判据删掉了而门仍绿（判据覆盖缩水） | `validate.py docs` + `decision_gate` + `doc_chain_live` 绿；本批链对 `--self-test` 计数不降 | ☑ docs + decision_gate + self-test 136/136 |
| G5-AC-05 | M-E / T15、T16 | 三个实现角色超 120 行，或 FE/BE 裁决没有数字/结论 | 行数 34/44/22；裁决记录 4/6、2 项、79 行 | ☑ 角色行数与裁决报告见 `testing/agentflow-全面修正与瘦身` 同批证据 |
| G6-AC-01 | M-F-01 | 证据件目录仍在盘，或批次正文目录被误删 | 前后 `find … | wc -l` 与 `du -sh` 落证据列；批次正文文件数不变 | ☑ L3 184 件删除；批次正文未动 |
| G6-AC-02 | M-F-02 | 删除后留下悬空链接或悬空字段 | 同 G3-AC-04；另加 `validate.py docs` 与 `doc_chain_live` 双绿 | ☑ artifacts/docs/doc_chain_live PASS |
| G6-AC-03 | M-F-03 | 重复导航面仍在，或外部逐字快照被误删 | 行数/文件数前后差值落证据列；`reviews/infinite-canvas-*` 与 `reviews/*/archive/` 外部快照计数不变 | ☑ 重复导航退场；外部快照保留；内部快照按 T18 保留 |
| G6-AC-04 | M-F-04 | 现行导航面仍有会过期的计数字面量，或历史引文被改写 | 三文件检索命中 0；`docs/issues/**` 与批次 `reviews/**` 的引文计数逐字节不变 | ☑ 三文件计数改为实跑口径 |
| G6-AC-05 | M-F-05 | 字形映射仍有两份独立定义 | `validate.py tests` + `validate.py all` 绿；`validate.py docs` 的归属表断言与该行的锚点核验覆盖它 | ☑ 字形映射单源 |
| G7-AC-01 | M-G-01 | 改进环文件或角色仍在盘，或活文档仍指向退役路径，门仍绿 | `validate.py all` 绿；`test ! -e skills/improve`；全仓检索退役路径命中 0 | ☑ skills/improve 与四角色已删；活方法面检索见 evidence |
| G7-AC-02 | M-G-02 | 明显凭据形状写进 `credentials` 仍被 schema 放行 | `tests/test_gate_schema.py` 正反例全过（删 pattern 后反例必须转红） | ☑ tests/test_gate_schema.py 正反例 |
| G7-AC-03 | M-G-03 | C17 变异项不存在，或变异存活 | `mutate.py --check doc_chain_selftest` 输出 0 存活、0 无效 | ☑ mutate 19/19 杀死 |
| G7-AC-04 | M-G-04 | 契约缺「定位即预算」条，或生成树未重建 | `grep -n "定位即预算"` 命中；`validate.py manifests` 绿 | ☑ 定位即预算命中 + manifests PASS |
| G7-AC-05 | M-G-05 | 对照实验只有协议没有数字，或把代理指标写成已验证人效 | 报告含协议、两组原始数字与限制；独立评审复核 | ☑ 报告 `docs/evaluations/AGENTFLOW-CONTROL-EXPERIMENT-2026-10-29.md`；第二轮评审正文已复核该报告（`reviews/review-2026-10-29-003.md` 残余风险节、`-004.md` 残余风险节），报告 §4 已写明不可外推 |

## 2. 覆盖映射（按方向逐项声明，不默许跳过）

| 方向 | 覆盖点 | 说明 |
| --- | --- | --- |
| 功能 | G1…G7 全部 AC | 每条 AC 都指向一条会失败的检查 |
| 速度与容量 | G6-AC-01 | 记录面体量前后对比（文件数与 `du -sh`）；本批不主张墙钟时间收益 |
| 权限与安全 | G4-AC-02、M-D-02 | 伪降级判据属「谁批准了什么」的审计面 |
| 版本与平台兼容 | 不适用 | 本批不改安装面与版本；交付终点经授权不含 bump 与重装 |
| 异常与恢复 | G3-AC-01/02/03、G6-AC-02 | 判据过宽、判据过窄、删后悬空三类失败分支 |
| 并发与竞态 | M-F-01 的执行顺序 | 删除前跑 `tools/dirty-guard.py snapshot`，写后 `verify`（`AGENTS.md`「实验与恢复」条款） |
| 数据一致性 | G1-AC-02、G2-AC-01、G6-AC-04 | 四处导航面与拍板口的状态口径一致 |
| 日志与监控 | 各 AC 的「打印原文再判定」列 | 检查脚本必须先打印命中原文（`AGENTS.md` 末节纪律） |
| 生命周期与清理 | G6-AC-01/03、M-C-02 | 快照生命周期与 `N/A` 标注口径 |
| 契约与兼容 | G4-AC-01、M-D-01、M-E-04、G7-AC-02/04 | schema 与生成树逐字节一致；收敛不缩判据；凭据 pattern 与契约条款同步重建 |
| 页面操作体验 | 不适用 | 无用户界面（§0 声明） |

## 3. 依赖与分流

- G3 的全部 AC 依赖判据先落地；G6-AC-02 与 G3-AC-04 共用同一扫描脚本，脚本失败时 G6 相关 AC
  全部置阻塞，不得单独放行。
- G4-AC-02 的变异式反证需要先有 `tests/test_gate_records.py` 新用例；反证在 `/tmp` 副本上运行
  （`AGENTS.md`：故障注入只在一次性副本，绝不在工作树）。
- G5 与 G6 互不依赖，可并行；两批都触碰 `index.md` 与 `docs/features/README.md`，
  同一分支同一时刻只允许一个写入者，实际执行按串行处理。

## 4. 结论等级判定

| 条件 | 结论 |
| --- | --- |
| 全部 AC 通过且独立评审 `approved` | 通过 |
| 全量门绿、独立评审为 `partial`（档位 L0/L1 且留派发原始返回）或有 AC 未覆盖 | 有条件通过，逐条列未覆盖项 |
| 任一门项红且未登记显式放行 | 不通过 |
