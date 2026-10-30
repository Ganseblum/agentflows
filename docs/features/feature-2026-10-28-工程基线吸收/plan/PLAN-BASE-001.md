---
plan_id: PLAN-BASE-001
plan_version: 1.1.0
status: approved
objective: 把两处外部语料的可复用能力接进 agentflow（工程基线模板与 Init、后端数据与配置核对、原型可点性、测试设计三维、前端实现纪律与设计核对）
recorded_at: 2026-10-28T15:30:00+08:00
---

# PLAN-BASE-001 — 工程基线吸收批执行计划

## 进展概览

- 总任务 12 项：☑ 12 项已完成；T12（FE 增量独立评审）于 2026-10-29 经独立委派 L2 `approved` 闭环（用户此前拒绝委派，本次已授权）。
- 阻塞：无。
- 权威状态：本表即唯一任务状态源；批次 README 只作索引。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 新增工程基线模板并在模板索引与 `index.md` 登记 | P0 | `skills/agentflow/templates/engineering/baseline.md`、`skills/agentflow/templates/README.md`、`index.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T01-baseline-template.txt`（由 `scratch/verify.py` 生成，可复跑；10/10 小节、两处指针、生成树逐字节一致） |
| T02 | Init 由五项改为六项并写明工程基线入口要件 | P0 | `skills/agentflow/SKILL.md` | T01 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T02-init.txt`（由 `scratch/verify.py` 生成；六项、入口、模板指针均命中） |
| T03 | `design/be` 补字段与数据核对、配置项与运行边界；`backend-engineer` 补执行纪律 | P0 | `skills/agentflow/templates/feature/design/be/backend.md`、`agents/backend-engineer.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T03-design-be.txt`（由 `scratch/verify.py` 生成；配置 12 列且含占位行、边界 7 列且含占位行、核对 8/8 含 `<填写>`、角色纪律 1 处） |
| T04 | 原型自检补 P1–P5；链契约原型节补同一判据 | P1 | `skills/agentflow/templates/feature/prototype/README.md`、`skills/agentflow/references/document-chain.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T04-prototype.txt`（由 `scratch/verify.py` 生成；P1–P5 五行、链契约两处；并检查不再出现未经换算的误报率） |
| T05 | 计划模板补三维覆盖方向与最小必测集说明；`test-planner` 补取舍纪律 | P1 | `skills/agentflow/templates/testing/plan.md`、`agents/test-planner.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T05-testing-plan.txt`（由 `scratch/verify.py` 生成；三方向 + 最小必测集 + 角色 1 处 + 链契约十一方向） |
| T06 | 批次文档链五段成文并通过 linter | P0 | `docs/features/feature-2026-10-28-工程基线吸收/` | T01、T02、T03、T04、T05 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T06-doc-chain.txt`（PASS，退出码 0） |
| T07 | 五份 manifest 升版、`CHANGELOG.md` 记条目、重建生成树并跑全量门 | P0 | `plugin.json`、`marketplace.json`、`.zcode-plugin/plugin.json`、`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`packaging/runtime/`、`CHANGELOG.md` | T01、T02、T03、T04、T05、T06 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T07-validate-all-clean-base.txt`（干净副本 153cd2b + 本批改动：11/11 PASS，退出码 0）；共享树 16:10 复跑同为 11/11 PASS，见 `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T07-validate-all-shared-tree.txt` |
| T08 | 四处索引同步：本仓在途表、`index.md` 批次索引、`docs/releases/pending-test.md`（如涉及）、批次 README 状态 | P1 | `docs/features/README.md`、`index.md`、`docs/releases/pending-test.md` | T07 | ☑ 已完成 | `docs/features/README.md`（在途批次行）、`index.md`（批次索引行）、`docs/releases/pending-test.md`（第 7 行） |
| T09 | 需求评审门与技术方案评审门（L1 档独立 reviewer） | P0 | `docs/features/feature-2026-10-28-工程基线吸收/reviews/` | T06 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/reviews/review-2026-10-28-001.md`（四轮收敛，最终 approved） |
| T10 | FE 实现纪律：`frontend-engineer` 五组纪律；`design/fe` 表与自检；`spec/fe` 行为口径；工程基线请求层与 UI 基线 | P0 | `agents/frontend-engineer.md`、`skills/agentflow/templates/feature/design/fe/frontend.md`、`skills/agentflow/templates/feature/spec/fe/frontend.md`、`skills/agentflow/templates/engineering/baseline.md` | — | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T10-frontend-discipline.txt`（由 `scratch/verify.py` 生成：角色 14/14、design/fe 7/7 + 自检 4/4、spec/fe 7/7、工程基线 6/6） |
| T11 | FE 证据扩展（`verify.py` 增 FE 检查）、重建生成树、干净副本与共享树全量门 | P0 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/scratch/verify.py`、`packaging/runtime/` | T10 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T07-validate-all-clean-base.txt`（干净副本 11/11 PASS）与 `docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/evidence/T07-validate-all-shared-tree.txt`（共享树 16:24 11/11 PASS）；`verify.py` 6/6 PASS |
| T12 | FE 增量独立评审（G5），记录落 `reviews/` | P0 | `docs/features/feature-2026-10-28-工程基线吸收/reviews/` | T11 | ☑ 已完成 | `docs/features/feature-2026-10-28-工程基线吸收/reviews/review-2026-10-28-002.md`（L2 `approved`：FE 增量 T10/T11 在 source_revision `256ea64` 干净副本 verify.py 6/6 PASS、批次 doc_chain PASS、无摘标记转绿；P1 注记 10-29 批在途瘦身改 `frontend-engineer.md` 使 main 上 verify.py 暂为 3/6，FE 纪律已迁至 `execution.md` 前端执行清单，待 10-29 批落定后复跑） |

> 2026-10-28 范围追加：用户指出第一轮只补后端与测试、FE 不对称；追加 M05/G5 与 T10–T12，`plan_version` 升到 1.1.0。原 T01–T09 的状态与证据不变。

## 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施与测试 | main | c134d0b2 | feature-2026-10-28-评审欠账清偿 | 已确认 | 用户 2026-10-28 指定范围后在本分支继续 | 分支上另有欠账修复批的提交 `153cd2b`；本批改动不与其混提，不推送、不合并、不重装 |

## 验证命令

```sh
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-工程基线吸收"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 packaging/build_runtime.py
python3.12 tools/lab/validate.py all   # 共享树有其它会话未提交改动时，以干净副本复跑为准
sh "docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/scratch/replay_clean_base.sh"
python3.12 -m unittest discover -s tests
```

## 门与回滚点

- **门 1**：T01–T05 完成后逐个打印改动文件的命中原文，落 `testing/agentflow-baseline/evidence/`。
- **门 2**：T06 完成后跑批次 linter，红则退回修文档，不改 linter。
- **门 3**：T07 的生成树重建必须在全量门之前；`validate.py all` 的 manifest 与生成树新鲜度两项必须绿。
- **门 4**：T09 的独立评审由读者自己核对证据文件，不接受实施者自述。
- **回滚点**：本批改动已于 2026-10-28 并入 `main`（`d5b52ce`、`256ea64`），且与另一会话的 id 改名同批提交。回滚须按 README「并发环境」节登记的本批文件清单逐个 `git revert` 或还原该文件，**不能用整提交回退**——那会连带回退不属于本批的改动。回滚后重建生成树并复跑 `validate.py all`。
