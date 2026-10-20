---
bug_id: ISS-2026-041
title: check-write-scope.sh 的「.」全树范围静默失配——声明的整树口径把全部变更路径判为越界
status: verified
regression_status: pass
severity: P2
error_kind: logic-error
attribution: product_code
provenance: agentflow
project: agentflow
files:
  - skills/agentflow/scripts/check-write-scope.sh
  - tests/test_lab_contracts.py
recorded_at: 2026-10-10T15:13:00+08:00
source_revision: agentflows@4c767eb + uncommitted youc 吸收批工作树（2026-10-10）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-10，用户指示「立 ISS 并修」）
updated_at: 2026-10-19T21:45:00+08:00
reviewer: agentflow:reviewer（2026-10-19 独立批量复审）
review_decision: approved
closure_criteria: check-write-scope.sh HEAD . 输出 OK 且退出 0；窄范围（HEAD skills）仍 FAIL 退出 1；WriteScopeScriptTests 2 用例在 unittest discover 内通过。
---

## 现象

全仓中文化批次中发现（2026-10-10；缺陷本身在翻译前即存在）：`check-write-scope.sh` 的用法说明
承诺 `用 "." 表示允许整棵树`，实际用 `.` 作为范围时把**全部**变更路径判为越界，整树口径不可用。

复现（修复前工作树）：

```text
$ bash skills/agentflow/scripts/check-write-scope.sh HEAD .
FAIL: 共 N 个变更路径中有 N 个在声明的写范围之外：
  <逐条列出全部变更路径>
EXIT=1
```

翻译前原文快照同口径复现（/tmp 一次性副本）：

```text
$ bash /tmp/cws-orig.sh HEAD .
FAIL: 65 of 65 changed path(s) outside the declared write scope:
  AGENTS.md
  README.md
  ...
```

影响面：本脚本是硬边界 14（写范围对照）的随附工具，SKILL 与文档把它列为 Supervisor 验收动作的
标准命令之一；整树场景（一次性允许全仓）会得到假 FAIL，促使人排查一个不存在的越界，或绕开该
检查改用别的方式对照。

## 问题代码

```bash
in_scope() {
  path="$1"
  for scope in ${scopes[@]+"${scopes[@]}"}; do
    normalized="${scope%/}"
    case "$path" in
      "$normalized" | "$normalized"/*) return 0 ;;
    esac
  done
  return 1
}
```

## 根因

`normalized="."` 时模式为 `.` 与 `./*`；git 输出的路径是**仓库根相对路径**（不带 `./` 前缀），
两个模式都不匹配任何路径——整树口径静默失配，逐条落入越界分支。窄范围（`skills`、`plans/x.md`
等）不受影响，因此缺陷只在 `.` 场景暴露。

## 修复

1. `in_scope()` 增一行约定放行（同时覆盖 `.` 与 `./`，后者经 `${scope%/}` 归一为 `.`）：

```bash
    if [ "$normalized" = "." ]; then return 0; fi
```

2. 回归用例（`tests/test_lab_contracts.py` 新增 `WriteScopeScriptTests`）：临时 git 仓库分别验证
   ——`.` 全树口径 → exit 0 且输出 `OK`；窄范围外的变更 → 仍 exit 1 且输出 `FAIL`。

## 回归检查

- 修复后真实仓：`bash skills/agentflow/scripts/check-write-scope.sh HEAD .` → `OK: 共 12 个变更路径，全部位于声明的写范围之内。`，EXIT=0
- 窄范围保留：`bash skills/agentflow/scripts/check-write-scope.sh HEAD skills` → `FAIL: 共 12 个变更路径中有 10 个在声明的写范围之外：…`，EXIT=1（原语义未动）
- `python3 -m unittest tests.test_lab_contracts -k WriteScopeScript` → 2 用例 OK
- `python3 tools/lab/validate.py all` → 全绿（见本批提交前的复跑记录）

## 审查

2026-10-19 独立复审（agentflow:reviewer 子代理，只读）。修复声称核对成立：check-write-scope.sh:72 对归一化为 . 的范围直接放行；tests/test_lab_contracts.py:1370 WriteScopeScriptTests 在册。回归证据（本次实跑）：HEAD . 输出 OK 且退出 0；HEAD skills 输出 FAIL 70/76 越界且退出 1（原语义保留）；unittest -k WriteScopeScript 2 用例 OK。review_decision：approved。

## 变更记录

- 2026-10-10 15:13 · recorded + fixed · 中文化批次发现（翻译前即存在，原文快照同行为）；用户指示「立 ISS 并修」；修复 + 双回归用例落地，检查全绿
- 2026-10-19 21:45 · 独立复审通过 · agentflow:reviewer 批量复审（只读）核对修复声称与回归证据成立，转 verified。
