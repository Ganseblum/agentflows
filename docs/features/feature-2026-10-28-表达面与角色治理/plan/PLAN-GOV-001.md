---
plan_id: PLAN-GOV-001
plan_version: 1.0.0
status: superseded
superseded_by: PLAN-FIX-001
objective: 给每条跨载体规则指定唯一权威载体，让同步义务退场；实测裁决 FE/BE 合并悬案；对齐实现角色深度
recorded_at: 2026-10-28T12:10:00+08:00
---

# PLAN-GOV-001 — 表达面与角色治理执行计划

## 进展概览

- 总任务 8 项：☐ 8 项未开始（T01–T08）。本批当前只交付范围与判据，不含实施。
- 阻塞：无。
- 权威状态：本表即唯一任务状态源。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 建载体归属表核验脚本（表驱动：断言权威路径存在 + 锚点命中 + 指针可解析） | P0 | `tools/lab/gov_carrier.py`（待核实：新文件，实施时创建并登记进 `tools/lab/validate.py` 与 `protected-paths.txt`） | — | — 本期不做（已由 FIX T07（carrier-map + validate docs 断言） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T02 | 压缩 `SKILL.md:131` 为一句摘要 + 指向 `contracts.md` 的链接（第三份副本退场） | P0 | `skills/agentflow/SKILL.md` | T01 | — 本期不做（已由 FIX T12（只消副本、去除第三份副本） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T03 | 删除 `SKILL.md:102` 的「改一处就改另一处」同步义务；把 A↔B 无法指针化的场合写进归属表 | P0 | `skills/agentflow/SKILL.md`、`docs/features/feature-2026-10-28-表达面与角色治理/spec/be/backend.md` | T02 | — 本期不做（已由 FIX T12（同步义务退场，归属表承载） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T04 | 拆分 `document-chain.md` → `document-chain.md`（≤150 行契约）+ `document-chain-checks.md`（判据细则）；同步 4 处引用 | P1 | `skills/agentflow/references/document-chain.md`、`skills/agentflow/references/document-chain-checks.md`（待核实：拆分时新建）、`skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md` | — | — 本期不做（已由 FIX T12（document-chain 拆分与引用同步） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T05 | 复跑 28 例边界语料，实测 FE/BE 三条件（不一致例数 / 所有权分歧项数 / 合并稿行数） | P0 | `docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/` | — | — 本期不做（已由 FIX T16（28 例边界语料复跑与裁决） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T06 | 按实测结论更新 `roles.md` 裁决段：写数字 + 明确结论 +（若保持分立）重审触发条件 | P0 | `skills/agentflow/references/roles.md` | T05 | — 本期不做（已由 FIX T16（roles.md 裁决段更新） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T07 | 对齐三个实现角色的深度：逐条核对职责覆盖，补缺或写明「由谁承担」 | P1 | `agents/backend-engineer.md`、`agents/frontend-engineer.md`、`agents/technical-director.md` | — | — 本期不做（已由 FIX T15（实现角色深度对齐） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |
| T08 | 全量门 + 生成树重建 + 独立复核（L2 恢复后补） | P0 | 五份 manifest、`packaging/runtime/` | T01、T02、T03、T04、T05、T06、T07 | — 本期不做（已由 FIX T14（全量门 + 生成树 + 独立复核） 承接） | 见 `docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 对应任务行 |

## 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施与测试 | feature-2026-10-28-评测整改批 | e31699a | feature-2026-10-28-表达面与角色治理 | 已确认 | 用户 2026-10-28「可以，先成立独立批次吧」 | 不推送、不合并、不重装 |

## 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-表达面与角色治理"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

## 门与回滚点

- **门 1（实施前）**：T01 的核验脚本落地前，不得开始 T02——没有脚本就无法证明「压缩后锚点仍命中」。
- **门 2（受保护面）**：若实施中需删 `contracts.md` 的重复段，那是门变更，须逐条列出拟删段落并单独授权
  （本计划不含该动作；归属表已把 `contracts.md` 定为权威载体，因此它不需要删减）。
- **门 3（T04 拆分）**：拆分后 `--self-test` 必须仍是 124/124，`doc_chain_live` 0 finding；
  任一红则回滚拆分。
- **门 4（交付）**：T08 前端到端走一遍「新批次立项 → 跑 linter」的真实路径，确认拆分后的
  文档链对作者仍可用（不是只有改门者看得懂）。
- **回滚点**：本批基线为 `feature-2026-10-28-评测整改批` 的 `e31699a`（0.20.0）。
- **评审档位**：L0（委派不可用）。T08 的独立复核在能力恢复后补；补门之前结论上限 `partial`。

## 未决事项（实施前需用户确认）

| # | 事项 | 推荐 | 说明 |
| --- | --- | --- | --- |
| 1 | T01 新增 `tools/lab/gov_carrier.py` 是否登记进受保护清单 | 登记 | 它决定「载体是否单一权威」，按 `protected-paths.txt` 的既有纳入规则应保护 |
| 2 | T07 是否允许把角色文件从 22–40 行扩到 ≤120 行 | 允许但需守 120 上限 | 加深度与防膨胀是一对约束，上限防止把 SKILL 的重复搬进角色文件 |
| 3 | T05 若 28 例语料不足判定 | 给保守结论 + 重审触发条件 | 不伪造数字，不无限期悬空 |
