# 待验收

> 规则：代码已落 ≠ 已验收。每一项要么标已验证（附验证方式与结果），要么显式写「未做 / 未验证」。
> 只记录当前仍待人工验收的批次；更早批次的历史见 git 历史与 `../../CHANGELOG.md`。

## 可测试变更

| # | 变更 | 验证方式（可复现的命令或步骤） | 结果 |
| --- | --- | --- | --- |
| 1 | 全仓中文本地化（角色 / 技能 / 文档 / CHANGELOG） | ZCode 客户端刷新 marketplace + 重装后：抽查 `agents/reviewer.md`、`skills/agentflow/SKILL.md` 与技能 / 角色描述为中文；随后 `python3 tools/lab/validate.py installed` 应 PASS | 已验证（2026-10-20 重装 + 译中后）：`installed` PASS（0.11.0 快照含中文）；`agents/reviewer.md` / `skills/agentflow/SKILL.md` 的 `description` 已译为中文（抽查 installed 0.11.0 快照第 3 行确认）；全仓 agents/*.md（14）+ skills/**/*.md（27）正文与描述均为中文（可靠 CJK 计数 36–62%）。`validate.py all` 10×PASS。注：早前「agents/skills 全英文」判读系 macOS `grep -P` 失效假阴性——实为仅 frontmatter `description` 字段留英文，本次已补译 |
| 2 | 结构文档登记（`docs/project-structure.md` 已删除，改由 `index.md` 承载）与 `index.md` 登记 | 打开 `index.md` 与 `tools/lab/README.md`，核对目录树 / 五个面 / 安装链路与现行结构一致 | 已验证（2026-10-19 核对：index.md 与 tools/lab/README.md 的目录树 / 五个记录根 / 安装链路与现行结构一致；五份 manifest 在盘且 `manifests` 门 PASS；`counts.py` 四处标记与计算值一致） |
| 3 | 发布待办 / 待验收 / 待拍板三件启用（`todo.md`、`pending-test.md`、`PENDING-DECISIONS.md`） | `python3 tools/lab/validate.py all` 中 `artifacts` PASS；打开 `../PENDING-DECISIONS.md` 确认拍板口可用 | 已验证（2026-10-19：`validate.py all` 九项含 `artifacts` PASS；拍板口本轮实际走通——第 1 条产品链复审经「修复→独立复审→approved→移出」全流程关闭） |
| 4 | 首次接入（Init）章节 + 表达与沉淀纪律（`skills/agentflow/SKILL.md`、`AGENTS.md`） | 阅读两处新增条款：Init 约定（youc 吸收批为四项；本批已扩为五项——见第 9 行）与「面向人的输出白话优先」；重装后可由用户在新项目试用 | 条款在盘已核（2026-10-19：SKILL.md Init 五项与 AGENTS.md 表达纪律条款 grep 在场）；待用户在新项目试用（用户阅读向，仓内不可闭环） |
| 5 | 端点复测与第一次改善闭环试水（观测） | 复跑一词探测；查看 `/tmp/agentflow-trial/{progress.jsonl,result.json}`（本地） | 已完成（探测 3/3；试水 3 轮 21.7 分钟；成本未落盘——已知观测缺口） |
| 6 | `check-write-scope.sh` 的「.」修复（ISS-2026-041） | `bash skills/agentflow/scripts/check-write-scope.sh HEAD .` → `OK` exit 0；`HEAD skills` → `FAIL` exit 1 | 已验证（2026-10-19 复跑双口径：`HEAD .` → OK exit 0（76 个变更路径全部在声明范围内）；`HEAD skills` → FAIL exit 1（70/76 越界，原语义保留）） |
| 7 | 精简批：mock/业务切片裁撤 + 镜像/台账合并（随本批） | `python3 tools/lab/validate.py all` → 9×PASS；`python3 -m unittest discover -s tests` → 全 OK（当时 139；改进环断言退役后为 124；2026-10-13 复跑为 78 项全 OK）；grep 业务残留零命中（原验收步骤「重装后抽查 `evals/public` 15 用例完好」已随 2026-10-12 评测装置裁撤失去对象，作废） | 已验证（2026-10-19 复跑：`validate.py all` 9×PASS；unittest 96 OK；业务残留 grep 仅存于历史记录与迁移日志的引文位（围栏/行内代码豁免），活面零残留） |
| 8 | 瘦身批二期：`_archive/` 归档桶 + 已完成 features 批次裁撤，门豁免收敛（随本批） | `python3 tools/lab/validate.py all` → 9×PASS；`python3 -m unittest discover -s tests` → 139 OK；活面 grep `_archive`/`seed_grader`/`evals/business` 零残留；重装后抽查 `skills/agentflow/references/test-records.md` 在安装快照内、SKILL 测试段引用可解析 | 复跑（2026-10-20 重装后）：`installed` PASS；`skills/agentflow/references/test-records.md` 在 0.11.0 快照内（5767B），SKILL 第 36 行引用可解析。静态部分达成；仍建议用户在真实安装后抽验一次 |
| 9 | 接入 / 触发面修复 + 模板角色目录化 + 典型案例（随本批） | 重装后（刷新 marketplace + 重装）：在新目标仓发起一个 feature 任务，观察——①先问产品前沿 ②落点建 `<repo>-workflow-ai/` 枢纽 ③对 feature 目录 `doc_chain.py` PASS；另抽查 `skills/agentflow/templates/feature/` 为角色目录命名 | 复跑（2026-10-20 重装后）：`installed` PASS；静态项修正路径后已达成——`skills/agentflow/templates/feature/` 实为角色目录命名（design/{be,fe,qa,ui}、plan、proposal、spec/{be,fe,qa,ui}），与判据一致；端到端新仓 feature 任务观察仍待用户侧发起（仓内不可闭环），该项判为「静态达成 / 端到端待用户」 |

## 未做与残余

- 宿主安装快照漂移（2026-10-19 复跑确认 FAIL；2026-10-20 已重装：0.11.0 快照落地，`validate.py installed` PASS，T08 解锁）。第 1 项「中文化」于 2026-10-20 补译 agents/skills 的 `description` 后验收达成（见上表）；第 9 项「templates/feature 角色目录命名」仍缺对象（源侧不存在该目录），非重装可解。
- `schemas/*.schema.json` 内部 description 字段未汉化——已拍板关闭：不翻（EP-20261010-002）。
- 两批版本 bump 未做——随下次发布批（已拍板关闭；`CHANGELOG` 待发布节与 episode 已补）。
- ~~`check-write-scope.sh` 的「.」缺陷未修~~——已修复并双口径实测（ISS-2026-041，见上表第 6 行）。
- ~~试水成本未落盘：`host_adapter` 不记录每次调用 cost~~——已随 2026-10-12 评测装置裁撤失去对象关闭（观测缺口留存）。
