# 待验收

> 规则：代码已落 ≠ 已验收。每一项要么标已验证（附验证方式与结果），要么显式写「未做 / 未验证」。
> 只记录当前仍待人工验收的批次；已验收批次的历史见 git 历史与 `../../CHANGELOG.md`。

## 待人工验收

| # | 变更 | 验证方式（可复现的命令或步骤） | 结果 |
| --- | --- | --- | --- |
| 1 | 首次接入（Init）章节 + 表达与沉淀纪律（`skills/agentflow/SKILL.md`、`AGENTS.md`） | 阅读两处新增条款：Init 约定（五项）与「面向人的输出白话优先」；重装后由用户在新项目试用 | 条款在盘已核（2026-10-19：SKILL.md Init 五项与 AGENTS.md 表达纪律条款 grep 在场）；待用户在新项目试用（用户阅读向，仓内不可闭环） |
| 2 | 接入 / 触发面修复 + 模板角色目录化 + 典型案例 | 重装后在新目标仓发起一个 feature 任务，观察：①先问产品前沿 ②落点建 `<repo>-workflow-ai/` 枢纽 ③对 feature 目录 `doc_chain.py` PASS；另抽查 `skills/agentflow/templates/feature/` 为角色目录命名 | 静态项已达成（2026-10-20：`installed` PASS；模板目录为 design/{be,fe,qa,ui}、plan、proposal、spec/{be,fe,qa,ui}）；端到端新仓 feature 任务观察仍待用户侧发起，判为「静态达成 / 端到端待用户」 |

## 已验收（历史，2026-10-19/20）

- 全仓中文本地化：`installed` PASS，agents/skills 正文与 `description` 均为中文（2026-10-20）。
- 结构文档登记：`index.md` 与 `tools/lab/README.md` 一致，`manifests` PASS（2026-10-19）。
- 发布待办 / 待验收 / 待拍板三件启用：`artifacts` PASS，拍板口走通（2026-10-19）。
- 端点复测与第一次改善闭环试水：探测 3/3，试水 3 轮 21.7 分钟（成本未落盘，装置已裁撤）。
- `check-write-scope.sh` 的「.」修复：`HEAD .` → OK exit 0；`HEAD skills` → FAIL exit 1（ISS-2026-041）。
- 精简批 / 瘦身批二期：`validate.py all` PASS，unittest 78 OK，业务残留零命中。
- 宿主安装快照：2026-10-22 复核 0.12.0 快照在场，`validate.py installed` PASS。

## 未做与残余

- `schemas/*.schema.json` 内部 description 字段未汉化——已拍板关闭：不翻（EP-20261010-002）。
- 试水成本未落盘——随 2026-10-12 评测装置裁撤失去对象关闭（观测缺口留存）。
