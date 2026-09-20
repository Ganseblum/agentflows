---
class_id: full-rewrite-drop-promised-content
title: 整文件重写丢失已承诺内容——图目录/章节/夹具在覆盖式重写中蒸发
status: consolidated
consolidated_in: 0.8.2
first_record: BUG-20260920-04
occurrences:
  - BUG-20260920-04
recorded_at: 2026-09-20T06:50:00Z
updated_at: 2026-09-20T06:50:00Z
---

## 类模式

为对齐新基准做整文件覆盖式重写时，已存在且已对外承诺的内容被静默丢弃（图目录列出的
图、既有章节、自测判别夹具），且当时无任何机器检查覆盖"承诺 vs 兑现"。首现三例：
design/fe 丢图 1/5/6（linter C8 真实链复跑抓出）、design/be 丢执行通道节（评审发现）、
doc_chain.py 自测丢 C6 夹具（独立评审 round-2 点名）。

## 归纳内容（已吸收进 Agentflow 的哪一层）

已归纳于 Agentflow 0.8.2 工作树：`doc_chain.py` 图覆盖检查（C4 数据模型图可落 spec、
C7 线框或 prototype HTML 二选一、C8 fe 三类图必须齐）+ 18 例判别性自测；
`document-chain.md` 图目录纪律（所列必须逐张兑现）。流程约束：整文件重写前先列
"已承诺内容清单"，重写后逐项对照。
