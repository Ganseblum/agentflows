# 待验收

> 规则：代码已落 ≠ 已验收。每一项要么标已验证（附验证方式与结果），要么显式写「未做 / 未验证」。
> 只记录当前仍待人工验收的批次；更早批次的历史见 git 历史与 `../../CHANGELOG.md`。

## 可测试变更

| # | 变更 | 验证方式（可复现的命令或步骤） | 结果 |
| --- | --- | --- | --- |
| 1 | 全仓中文本地化（角色 / 技能 / 文档 / CHANGELOG） | ZCode 客户端刷新 marketplace + 重装后：抽查 `agents/reviewer.md`、`skills/agentflow/SKILL.md` 与技能 / 角色描述为中文；随后 `python3 tools/lab/validate.py installed` 应 PASS | 待验证（客户端重装已于 2026-10-10 完成，安装记录＝0.10.0；`installed` 已 PASS，界面抽查待做） |
| 2 | 结构文档 `docs/project-structure.md` 与 `index.md` 登记 | 打开 `project-structure.md`，核对目录树 / 五个面 / 安装链路与现行结构一致 | 待验证（待阅读） |
| 3 | 发布待办 / 待验收 / 待拍板三件启用（`todo.md`、`pending-test.md`、`PENDING-DECISIONS.md`） | `python3 tools/lab/validate.py all` 中 `artifacts` PASS；打开 `../PENDING-DECISIONS.md` 确认拍板口可用 | 待验证 |
| 4 | 首次接入（Init）章节 + 表达与沉淀纪律（`skills/agentflow/SKILL.md`、`AGENTS.md`） | 阅读两处新增条款：Init 约定（youc 吸收批为四项；本批已扩为五项——见第 7 行）与「面向人的输出白话优先」；重装后可由用户在新项目试用 | 待验证（待用户阅读） |
| 5 | 端点复测与第一次改善闭环试水（观测） | 复跑一词探测；查看 `/tmp/agentflow-trial/{progress.jsonl,result.json}`（本地） | 已完成（探测 3/3；试水 3 轮 21.7 分钟；成本未落盘——已知观测缺口） |
| 6 | `check-write-scope.sh` 的「.」修复（ISS-2026-041） | `bash skills/agentflow/scripts/check-write-scope.sh HEAD .` → `OK` exit 0；`HEAD skills` → `FAIL` exit 1 | 待验证（双口径已实测，随本批提交） |
| 8 | 精简批：mock/业务切片裁撤 + 镜像/台账合并（随本批） | `python3 tools/lab/validate.py all` → 9×PASS；`python3 -m unittest discover -s tests` → 全 OK（当时 139；现 124，改进环断言随停用退役）；grep 业务残留零命中；重装后抽查 `evals/public` 15 用例完好、improve 触发描述无业务提法 | 待验证 |
| 9 | 瘦身批二期：`_archive/` 归档桶 + 已完成 features 批次裁撤，门豁免收敛（随本批） | `python3 tools/lab/validate.py all` → 9×PASS；`python3 -m unittest discover -s tests` → 139 OK；活面 grep `_archive`/`seed_grader`/`evals/business` 零残留；重装后抽查 `skills/agentflow/references/test-records.md` 在安装快照内、SKILL 测试段引用可解析 | 待验证 |
| 7 | 接入 / 触发面修复 + 模板角色目录化 + 典型案例（随本批） | 重装后（刷新 marketplace + 重装）：在新目标仓发起一个 feature 任务，观察——①先问产品前沿 ②落点建 `<repo>-workflow-ai/` 枢纽 ③对 feature 目录 `doc_chain.py` PASS；另抽查 `templates/feature/` 为角色目录命名 | 待验证（客户端重装已完成：2026-10-10 16:22、安装记录＝0.10.0；runtime / cache 已同步至本批最新；端到端观察待做） |

## 未做与残余

- `schemas/*.schema.json` 内部 description 字段未汉化——已拍板关闭：不翻（EP-20261010-002）。
- 两批版本 bump 未做——随下次发布批（已拍板关闭；`CHANGELOG` 待发布节与 episode 已补）。
- ~~`check-write-scope.sh` 的「.」缺陷未修~~——已修复并双口径实测（ISS-2026-041，见上表第 6 行）。
- 试水成本未落盘：`host_adapter` 不记录每次调用 cost（观测缺口；随 `../PENDING-DECISIONS.md`「试水后授权」条处置）。
