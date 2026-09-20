---
class_id: doc-chain-generation-density
title: 文档交付链生成缺密度门——四层"齐全"但无契约/无图/未提问/plan 无落点
status: consolidated
consolidated_in: 0.8.3
first_record: BUG-20260920-02
occurrences:
  - BUG-20260920-02
recorded_at: 2026-09-20T05:30:00Z
updated_at: 2026-09-20T06:20:00Z
---

## 类模式

文档交付链按四层骨架生成，产物"每层都存在"但工程密度不达标：design 无字段级契约与
失败分支时序图、无状态机/线框，plan 无分支策略与文件级落点，产品决策类阻塞项被作者
以默认值单方面填掉而不向需求方提问。根因是判据只挂在评审侧（审的一侧）而不在生成
契约（写的一侧），且文档密度无任何会失败的机器检查。首现：2026-09-20 定时任务链首轮
生成被用户判 <30 分（详见首现记录与 EP-20260920-002）。

## 归纳内容（已吸收进 Agentflow 的哪一层）

已归纳于 Agentflow 0.8.2→0.8.3（初版条款随 0.8.2 发布，本类完整吸收——表达纪律/模板/C11 结构检查——随 0.8.3 发布）（随文档链批 7b41cc6 + 后续增量）：`document-chain.md`
门禁 1–5（产品决策必须提问确认、design 必带契约与失败分支时序图）+ Quality density
floor（C1–C10）+ 深度优先推进规则；新增 `tools/lab/doc_chain.py` 判别性自测 18 例；
`AGENTS.md` 增文档链 linter 必跑。回归=自测 case 02（原始薄形态必须失败）+ 真实链 PASS。
