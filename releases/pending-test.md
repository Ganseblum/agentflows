# 待验收

> 规则：代码已落 ≠ 已验收。每一项要么标已验证（附验证方式与结果），要么显式写「未做 / 未验证」。
> 只记录当前仍待人工验收的批次；更早批次的历史见 git 历史与 `../CHANGELOG.md`。

## 可测试变更

| # | 变更 | 验证方式（可复现的命令或步骤） | 结果 |
| --- | --- | --- | --- |
| 1 | 全仓中文本地化（角色 / 技能 / 文档 / CHANGELOG） | ZCode 客户端刷新 marketplace + 重装后：抽查 `agents/reviewer.md`、`skills/agentflow/SKILL.md` 与技能 / 角色描述为中文；随后 `python3 tools/lab/validate.py installed` 应 PASS | 待验证（本机 cache 已同步且 installed PASS；客户端重装未做） |
| 2 | 结构文档 `docs/project-structure.md` 与 `index.md` 登记 | 打开 `../docs/project-structure.md`，核对目录树 / 五个面 / 安装链路与现行结构一致 | 待验证（待阅读） |
| 3 | 发布待办 / 待验收 / 待拍板三件启用（`todo.md`、`pending-test.md`、`PENDING-DECISIONS.md`） | `python3 tools/lab/validate.py all` 中 `artifacts` PASS；打开 `../plans/PENDING-DECISIONS.md` 确认拍板口可用 | 待验证 |
| 4 | 首次接入（Init）章节 + 表达与沉淀纪律（`skills/agentflow/SKILL.md`、`AGENTS.md`） | 阅读两处新增条款：Init 四项约定与「面向人的输出白话优先」；重装后可由用户在新项目试用 | 待验证（待用户阅读） |
| 5 | 端点复测与第一次改善闭环试水（观测） | 复跑一词探测；查看 `/tmp/agentflow-trial/{progress.jsonl,result.json}`（本地） | 已完成（探测 3/3；试水 3 轮 21.7 分钟；成本未落盘——已知观测缺口） |
| 6 | `check-write-scope.sh` 的「.」修复（ISS-2026-041） | `bash skills/agentflow/scripts/check-write-scope.sh HEAD .` → `OK` exit 0；`HEAD skills` → `FAIL` exit 1 | 待验证（双口径已实测，随本批提交） |

## 未做与残余

- `schemas/*.schema.json` 内部 description 字段未汉化——已拍板不翻（`../plans/PENDING-DECISIONS.md` 第 3 条）。
- 两批版本 bump 未做——随下次发布批（第 2 条；`CHANGELOG` 待发布节与 episode 已补）。
- ~~`check-write-scope.sh` 的「.」缺陷未修~~——已修复并双口径实测（ISS-2026-041，见上表第 6 行）。
- 试水成本未落盘：`host_adapter` 不记录每次调用 cost（观测缺口；完整对照前建议补记录）。
