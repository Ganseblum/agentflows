---
bug_id: BUG-20260920-02
title: 文档交付链首轮产出密度不合格——design 无字段级契约与失败分支时序图、plan 无分支落点、阻塞项未向需求方提问确认
status: verified
severity: P1
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: aiwork-workflow-ai
files:
  - skills/agentflow/SKILL.md
  - skills/agentflow/references/document-chain.md
  - tools/lab/doc_chain.py
  - AGENTS.md
  - aiwork-workflow-ai@worktree-2026-09-20:docs/features/feature-2026-09-18-定时任务/design/be/定时任务-后端技术方案.md
affected_slices:
  - document-chain
  - generation-contract
  - alignment-discipline
  - review-gate
recorded_at: 2026-09-20T05:30:00Z
updated_at: 2026-09-20T07:20:00Z
source_revision: agentflows@5da90f2
agentflow_version: 0.8.2
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: python3 tools/lab/doc_chain.py --self-test → 18/18 exit 0；真实链 doc_chain PASS exit 0；validate.py all → 9×PASS exit 0
fix_revision: agentflow 0.8.3
class_id: doc-chain-generation-density
occurrence: "1"
---

## 现象

用户要求以 agentflow 文档交付链为 aiwork `feature-2026-09-18-定时任务` 生成完整
proposal→spec→design→plan 并评价质量。首轮产出四层"都存在"但被用户判定
"可能连 30 分都没有"，点名四缺口（用户原话，见 EP-20260920-002 E5）：

1. design/be 与 design/fe **无任何接口契约、无字段定义**——写为"字段级契约评审通过后
   回填，当前不虚构"，把信息缺口当作免写理由；
2. **一张时序图、流程图、状态机、线框图都没有**（仅一张模块 flowchart），前端无异常
   边界、无调用处理；
3. plan "几句话就说完"，无分支策略、无文件级落点、无伪代码；
4. proposal/spec 阶段**未把阻塞项作为问题向需求方提出**——B-1～B-3（原文状态机矛盾、
   每小时档首触未定义、熔断周期口径）被作者以"工程默认值待评审确认"单方面填掉。

## 根因

三层（详见 EP-20260920-002 signals.loop_closure 的归因）：

1. **生成契约缺密度条款**（主因）：0.5.1 吸收 aiwork 评审判据时只挂在 reviewer 文档
   评审模式（审的一侧），`document-chain.md` 生成骨架（写的一侧）只有粗粒度名词，
   没有字段级契约、失败分支时序图、S 步骤表、DDL、文件落点、影响面定级等可检查要求。
2. **作者未执行方法自己的纪律**：material 产出未派独立评审门（硬边界 1 的作者不自证
   在文档形态下被跳过）；"worker 交付先编译"对文档无等价物。
3. **无确定性验证面**：`validate.py docs` 只查链接存在性，文档密度没有任何会失败的
   机器检查，骨架文档畅通无阻。

## 问题代码

修复前的 `skills/agentflow/references/document-chain.md` Stage skeletons 节（本轮已重写）。
**引证说明（诚实约束）**：该文件与 `tools/lab/doc_chain.py` 在犯错时点均为未跟踪文件，
git 历史不含其修复前形态（`7b41cc6^` 对两者报 fatal: not in revision）——修复前形态的
逐字证据以 EP-20260920-002 E5 用户原话与本记录现象为准，无独立工件留存（这本身即
BUG-20260920-04 类的一个面向）。可从 git 取证的修复前形态：`AGENTS.md@7b41cc6^`
（无文档链 linter 验收段，`git show '7b41cc6^:AGENTS.md' | grep -c doc_chain` = 0）。
SKILL.md 的关联 hunk：接线段「Document delivery chain」+ description 路由短语由
`7b41cc6` 落地（`git show --stat 7b41cc6 -- skills/agentflow/SKILL.md`），属本记录修复面
的触发接线部分；密度条款本体在 document-chain.md。

## 修复

1. `document-chain.md` 门禁重构为 1–5：新增**产品决策类阻塞项必须以"问题+推荐默认值"
   向需求方提出**（禁止作者填默认值了事）；**design 必须携带字段级契约与含失败分支
   （alt）的时序图**；Quality density floor 节固化 C1–C10 密度底线 + 深度优先推进规则
   （代码事实未读不写 design）。
2. 新增 `tools/lab/doc_chain.py`（C1–C10 交叉闭合 linter）+ 18 例判别性自测；
   `AGENTS.md` 验收节增文档链 linter 必跑。
3. 真实链重做：定时任务链按沙箱熔断基准补齐（S1–S9 步骤表带观测点、字段级 DDL 三张
   表、契约 A1–A11 汇总表+散文细节、异常策略/告警编号/排障预案/影响面 L2 定级、FE 的
   TS 契约/字段映射表/testid/Mock 方案、15 张图），用户在线确认 B-1/B-2/B-3。
4. 独立评审三轮（changes_requested×2 → approved，AC1–AC6 逐项核对，见
   EP-20260920-002 review_roundtrips）。

外部引用现状片段（修复后密度，节选自引用文件）：

> aiwork-workflow-ai@worktree-2026-09-20:docs/features/feature-2026-09-18-定时任务/design/be/定时任务-后端技术方案.md §1.1.3.1
>
> | S3 | scheduler → TiDB | **唯一键插入** `automation_run(queued, fire_at)`；冲突=已生成，跳过 | Run 行落地 | 撞车（有在途 Run）→ skipped/previous_running；余额不足 → skipped/insufficient_quota | `automation_run_created{origin}` / `automation_run_skipped{reason}` |

**回归证据**：`python3 tools/lab/doc_chain.py --self-test` → 18/18（含"原始薄形态
必须失败"判别夹具 case 02：缺契约表/缺 alt 时序/线框不足/任务无落点四项各自命中）；
真实链 `PASS doc-chain …exit=0`；`validate.py all` 9×PASS。

## 变更记录

- 2026-09-20 初版立账（本会话 supervisor，作者不自证——记录自身待评审）。
- 2026-09-20 补录用户后续反馈的修复扩展：④以 aiwork 语料 30 feature 全普查为标尺补
  颗粒度（S 步骤表/字段级 DDL/契约汇总表/影响面定级/FE 字段映射与 TS 契约， reviewer
  终裁 approved）；⑤用户指出"一句话会偏移"→ 增 document-chain-templates.md 填空模板
  （固定标题字面量）+ linter C11 结构检查（README 声明启用）+ HTML 原型形态（C7）；
  同轮按 0.7.3 表达纪律清理「爆炸半径」（见 BUG-20260920-03）。

## 审查

- [x] 修复面过独立评审：agentflow:reviewer 三轮，终轮 approved（delta 含 C6 夹具补齐
      与 check6 复验，逐字回传见会话记录）
- [x] 回归：自测 18/18、真实链 PASS、all 9×PASS（本轮复核口径与上同）
- [x] 独立评审核对通过（agentflow:reviewer approved，2026-09-20 终裁）
