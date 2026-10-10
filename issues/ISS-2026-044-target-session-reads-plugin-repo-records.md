---
bug_id: ISS-2026-044
title: 目标仓会话到插件仓检索内部记录——记录根作用域与目标仓边界未划界
status: verified
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/SKILL.md
recorded_at: 2026-10-10T17:45:00+08:00
source_revision: agentflows@af1ba3d + 本批修复工作树（2026-10-10）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-10）
regression_status: pass
reviewer: agentflow:reviewer（独立子代理，只读）
review_decision: approved
closure_criteria: "python3 tools/lab/validate.py all → 10×PASS；grep -n '目标仓会话不读写插件仓的内部记录' skills/agentflow/SKILL.md ≥1 命中；grep -n '在插件仓中进行的方法开发与反馈会话' skills/agentflow/SKILL.md ≥1 命中"
updated_at: 2026-10-10T19:05:00+08:00
---

## 现象

与 ISS-2026-043 同一次运行：在 test-login 工作时，运行读取了插件仓 agentflows 的 `episodes/`、
`plans/` 等内部记录（运行日志出现「插件仓今天已有的 episode 记录」等动作）。用户反馈：
「读了很多没用的文件比如 episodes/、plans/，这些都是 agentflow 的，应该跟那个开发项目无关」。

## 根因

`SKILL.md` 第 10 步要求 material 改动把决策记录落成 `episodes/<日期>/<EP-id>.json`，但没有
声明该记录根属于**插件仓自身**；目标仓会话在自己仓里找不到 `episodes/`，就前往插件仓检索
范式。「目标仓会话不读写插件仓内部记录」这条边界在方法文本中不存在，记录落点与运行会话的
对应关系也没有写清。

## 修复

`skills/agentflow/SKILL.md`：

- 「保持控制与可追溯性」新增条款：skill 与 references 中提到的 `issues/`、`episodes/`、
  `plans/`、`reviews/` 等记录根是 **Agentflow 插件自身仓库**的记录；目标仓会话不读写它们，
  方法契约在 skill 文本内自包含；目标仓的文档与记录落 Init 确认的文档枢纽。
- 第 10 步 episode 条款补适用范围：指在插件仓中进行的方法开发与反馈会话；目标仓会话的决策
  记录落目标仓文档枢纽，运行证据由插件仓一侧在反馈与复盘的环节补记。

## 回归检查

- `python3 tools/lab/validate.py all`：10×PASS（含 docs 面断链 / 退役路径扫描）。
- 条款逐字核对（`skills/agentflow/SKILL.md` 两处）。

## 审查

- 评审：`agentflow:reviewer`（独立子代理，只读；reviewed_revision＝工作树 base `af1ba3dc…` + 案例树）。第 1–3 轮 `changes_requested` 逐轮修复，第 4 轮 `approved`。
- 回归闭合：`python3 tools/lab/validate.py all` 10×PASS；条款逐字核对命中；closure_criteria 闭合（往返与原始输出见 `EP-20261010-004`）。

## 变更记录

- 2026-10-10 · recorded + fixed
- 2026-10-10 · verified：第 4 轮独立评审 `approved`；往返记录见 `EP-20261010-004`。
