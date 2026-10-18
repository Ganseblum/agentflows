# 待用户拍板的事项

> 跨计划的「等用户拍板」事项统一登记在本文件（来源、问题、推荐、状态）。会话与计划会有
> 很多份，拍板口只有一个——这里是唯一需要用户逐条回复的清单。
>
> 规则：新事项登记为 `未决`；拍板后写成 `已拍板（日期 · 结论）`，并在各自载体落证据后
> **从本表移出**（本表只保留未决与未完结项）；实现若偏离被拍板的结论，不得回写成已拍板，
> 另行登记新条目再向用户确认。
>
> 2026-10-10：原十项已全部拍板/执行完毕（证据：提交 `4c767eb`、`6d10b14`、EP-20261010-001/002、
> `CHANGELOG`「待发布」节），已从本表移出。2026-10-12 精简批：第 5 条已随 mock/ 整体裁撤关闭
> （证据随本批提交）；业务尺子随本批裁撤，原第 2/3 条失去对象关闭；当前保留 2 条未决。
>
> 2026-10-13 核实：两条未决仍成立——产品链需求评审门（`docs/product/README.md` 第 3 节）仍是
> `☐`，`method-spec.md` 的会话角色词命中仍在；回溯独立评审在 `reviews/` 下无对应记录。
> 第 1 条的复审命令已更新为现行活面门（旧写法 `doc_chain.py docs/product` 需该目录另有 `plan/`
> 才可能通过，而产品链计划落在 `docs/features/<批次>/plan/`，故换用 `validate.py doc_chain_live`）。
>
> 2026-10-18 合并批：`workbuddy/main-b0d8652c` 已并入 `main`（按用户拍板保留 `main` 的裁撤，
> 评测装置不复活，只并入记录类内容；`validate.py all` 九项全绿留证）。该次合并带出三条新事项，
> 登记为下表第 5–7 条。

| # | 来源 | 待决问题 | 推荐 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | `reviews/agentflow-product-chain/review-2026-10-10-001.md`（REV-20261010-001） | 产品链需求评审 `changes_requested`（6 P1 + 6 P2）：修复轮怎么排 | 一轮直改 12 项文本（F1–F12）→ 复跑 `python3 tools/lab/validate.py doc_chain_live`（现行活面门，逐文件跑文本形态检查）与 `doc_chain.py --file` 三份 → 复审勾门。注：F3（硬边界 12→14）已随 2026-10-12 内容质量批改完；F5（会话角色词 6 处，`method-spec.md` 六处仍在）与 F1/F2/F4/F6 及其余 P2 仍待修 | 未决 |
| 4 | 本地化批、youc 吸收批与 2026-10-12 结构改造五批 | 受保护面改动的回溯独立评审：validator（`validate.py` 多次）、`tests/`、角色文件、规则书与 `protected-paths.txt` 覆盖面 | 排一轮 reviewer 复核上述提交的受保护面 diff（`4c767eb`、`6d10b14` 与 2026-10-12 改造批提交）。核实 2026-10-13：`reviews/` 下仍只有两条既有评审记录，本题尚无对应回合 | 未决（范围已并入 2026-10-12 五批） |
| 5 | 2026-10-18 合并批（本批） | `tools/lab/gate/` 包未纳入 `protected-paths.txt`：2026-10-13 把 `validate.py` 的单体逻辑拆成 `tools/lab/gate/*.py`，清单仍只保护 `tools/lab/validate.py` 本身；候选可改 `gate/schema.py` 等门逻辑而不触碰受保护路径 | 把 `tools/lab/gate/`（或其逐文件条目）补进 `protected-paths.txt` 与 `REQUIRED_PROTECTED_PATHS`。**这是门变更（改 `protected-paths.txt` + `gate/common.py` 的必需集合），须显式人工评审后再落**；本批未自行实施 | 未决 |
| 6 | 2026-10-18 合并批（本批） | `workbuddy/main-b0d8652c` 合并完成后的分支处置：删除本地分支 / 打 tag 留底 / 保留不动（该分支无 upstream，从未推送） | 合并已在 `main` 落地且内容可经 `git log` 回溯，建议打一个轻量 tag 留底后删除本地分支；用户未要求前不执行 | 未决 |
| 7 | 2026-10-18 合并批（本批） | `workbuddy` 侧两项代码改进未随合并带入（其宿主文件已随装置裁撤删除）：G1「schema 子集未实现关键字 fail-closed 守卫」的对象 `tools/lab/gate/schema.py` 在 `main` 仍存在，可另立候选移植；G2「快照 digest 加 `--no-renames --no-textconv`」的对象 `artifact_digest.py` 亦存在 | G1 值得移植（正是第 5 条保护的同一处门逻辑）；建议与第 5 条一并作为一轮「门健全」批次处理，不在合并批里夹带 | 未决 |

> 2026-10-12：原第 5 条（examples/mock 计划样板逐字节重复的单源化）已关闭——本批直接删除整个
> `mock/`（用户授权的精简批），examples/ 侧自然成为唯一样例；`MOCK_RECORD_ROOTS` 与 mock 检查
> 一并摘除。
>
> 2026-10-12：业务尺子随精简批裁撤（用户授权「保公开、裁业务」），原第 2 条（完整切片闭环与业务
> 尺子授权）、第 3 条（`host_adapter` 隔离路径认证）失去对象关闭；原计划 `plans/PLAN-BUSINESS-EVAL-001.md`
> 随瘦身批删除（git 历史可回溯）。
