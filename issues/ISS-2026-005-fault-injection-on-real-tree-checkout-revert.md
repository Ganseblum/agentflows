---
bug_id: ISS-2026-005
title: 故障注入在真实仓库执行；git checkout「恢复」把 protected-paths.txt 静默重置回提交版
status: verified
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflows
files:
  - protected-paths.txt
  - AGENTS.md
  - _archive/handoff-2026-10/next-session-handoff.md
affected_slices:
  - gate-maintenance
  - lab-tooling
recorded_at: 2026-09-15T03:23:11Z
updated_at: 2026-09-17T16:00:00Z
source_revision: 33962ee
agentflow_version: 0.3.3
regression_status: pass
reviewer: agentflow:reviewer
review_decision: approved
closure_criteria: 评审人指定检查符合预期：一次性副本（/tmp/af-protected-demo.*）上从 protected-paths.txt 删除自保护行后，`python3 tools/lab/validate.py protected` FAIL（1 error）并报 `required gate path 'protected-paths.txt' is no longer covered by any declared prefix`，退出码 1——检测路径实证；真实工作区演示前后 `python3 tools/lab/validate.py all` 均退出码 0。
fix_revision: agentflow 0.3.4
---

## 现象

第六批评审中验证「清单删掉 improve references 前缀必须 FAIL」时，故障注入被错误地执行在
真实仓库而非 /tmp 副本上。随后的"恢复"更糟：

```sh
# 注入（错误：目标是真实仓库的 protected-paths.txt）
python3 - <<'EOF'
t=open('protected-paths.txt').read().replace('skills/improve/references/\n','')
open('protected-paths.txt','w').write(t)
EOF
# 恢复（错误：该文件已提交，checkout 将其重置到提交版，
# 冲掉本会话全部未提交编辑；stderr 被 2>/dev/null 吞掉）
git checkout protected-paths.txt 2>/dev/null
```

结果 `protected-paths.txt` 回退到 0.3.3 提交版（16 条旧条目），本会话对它的未提交编辑
（`schemas/` 整体、`tests/` 文件级保护、注释块）全部丢失。操作者在未验证的情况下声称
"恢复中"。

发现方式：下一条 `validate.py protected` 立即 FAIL（4 个必需条目不再被覆盖）——必需条目
检查正确地把"清单回退"当成了门回归报警。随后手工重建文件到目标状态，`all` 七项复验全
绿。

## 根因

三个缺失的约束叠加，没有任何一条写在当时的纪律里：

1. **注入无沙箱要求**：前几轮注入都在 /tmp 副本上做，但那是习惯不是规则；本轮换了执行
   位置后没有任何东西拦截。
2. **恢复无验证要求**：`git checkout <path>` 对已跟踪文件的语义是"丢弃工作区改动、回到
   提交版"——恰好是最坏方向；且错误被 `2>/dev/null` 吞掉，输出未被观察。
3. **未提交工作跨越过多文件**：~25 个文件的会话成果没有分批提交，单文件 mishap 的爆炸
   半径因此是"全部丢失"而不是"一条命令恢复"。

归因 `workflow_policy` 而非 `model_limit`：操作者当时具备全部知识（知道要用副本、知道
checkout 语义），缺的是强制这些动作的流程约束。

## 修复

`AGENTS.md` 新增实验与恢复规则（本记录同批落地）：

- 故障注入/变异测试只在一次性副本（`cp -r` 到 /tmp）上执行，永不碰工作区；
- 禁止用 `git checkout` / `git restore` 在真实树上撤销实验——对已跟踪文件它们是重置而非
  撤销，会静默丢弃未提交工作；
- 恢复/还原只有在重跑相关检查并观察到绿之后才算完成；未观察的恢复不算恢复（与"无法
   复现的检查记为未运行"同构）。

实务建议（对仓库所有者）：每个确认批次尽早提交。本次事故的损失面取决于 ~25 个未提交
文件；分批提交后同类 mishap 的恢复就是一条 `git checkout`。

## 回归检查

- 规则已写入 `AGENTS.md`；`python3 tools/lab/validate.py all` 七项 PASS。
- 检测路径已实证：清单被回退时 `validate.py protected` 在一条命令内 FAIL——防线是"预防
  失败、检测成功"，本次事故本身就是该检测的回归证据。

## 备注

- 状态 `fixed-pending-review`：规则修复尚无独立 Reviewer 判定。
- 完整事故叙述与教训另见 `_archive/handoff-2026-10/next-session-handoff.md` 第六批。

## 审查

评审人 `agentflow:reviewer` 于 2026-09-17 批量评审本批 8 条 `fixed-pending-review` 记录。
本条指定检查 C0（真实工作区全量确定性检查）与 C3（一次性副本上的门检测路径注入），由
supervisor 执行并回传原始输出；结论 `approved`，本记录转 `verified`，`fix_revision` 据实
回填为 agentflow 0.3.4。

决定性证据（supervisor 回传，逐字输出）：

C0 —— 真实工作区 `python3 tools/lab/validate.py all`，演示前后各一次，均：

```
8/8 PASS, exit 0
```

C3 —— 一次性副本（/tmp/af-protected-demo.*）上从 protected-paths.txt 删除自保护行后，
`python3 tools/lab/validate.py protected`：退出码 1，门检测路径报警命中：

```
FAIL protected (1 error(s))
  - required gate path 'protected-paths.txt' is no longer covered by any declared prefix
```

## 变更记录

- 2026-09-17 · 独立评审通过 · agentflow:reviewer 批量评审指定检查（C0–C8），supervisor 执行并回传原始输出，转 verified。
