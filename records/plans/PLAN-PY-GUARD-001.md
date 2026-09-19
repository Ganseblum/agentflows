---
plan_id: PLAN-PY-GUARD-001
plan_version: 0.1.0
status: proposed
objective: 消灭默认 python3(3.9) 下 validate.py all 的 8 绿 1 红误导输出——解释器低于声明下限即 fail-closed；顺带复测 U-01 端点现状
recorded_at: 2026-09-19T13:35:48Z
updated_at: 2026-09-19T13:53:00Z
---

# 解释器下限守卫 — 真实问题修复批

> 执行契约，不是改代码授权。T01 是**门变更**（`tools/lab/validate.py` 在保护区内）：
> 用户在 2026-09-19 会话中针对上一轮评审列明的"validate.py 在解释器 <3.10 时直接
> fail-closed"方案明示"直接开始修复"，据此在受信任源码树由 Supervisor 实施，不作为候选 diff。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。
> 回写纪律：完成后只改**状态**与**证据**两列。

## 进展概览

**本期进度**：**5 / 5 已完成** · **0 进行中** · **0 阻塞** · **0 未开始** · **1 本期不做**

**本批认定的真实问题**（2026-09-19 架构评审实测结论，只列可动手的）：

| 问题 | 实测证据 | 本批处置 |
| --- | --- | --- |
| 默认 `python3` 是 3.9（Xcode CLT），`validate.py all` 输出 8×PASS + `FAIL tests`，报错是 PEP 604 TypeError，不指明版本原因 | 本会话实测：3.9 下 `FAIL tests (1 error(s))`，unittest 报 `unsupported operand type(s) for \|`；3.12 下 155 单测 OK、9×PASS | T01–T02 修复 |
| improve 环首次真实对照停在 U-01 可信端点（网关 502/挂起两批） | host-platform-facts C10；PLAN-LOOP-SMOKE-001 T05 ⚠ | T03 复测现状 |
| 改动有效性从未被测量（方法级改动全部 `measurement: none`） | README「instrument-ready, not measured」 | 不在本批——依赖 U-02 端点决策 |
| contracts.md 与 SKILL/README 重述造成的同步税 | iteration-log 每批多处"同步"记录 | 不在本批——方法级改动，须走 improve 环（有量尺后） |
| `maxTurns` 声明无宿主强制 | host-platform-facts Z6（已如实标注） | 不处置——宿主限制，记录即处置 |

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 用错解释器时门说人话 | validate.py 启动即查 `sys.version_info`，<3.10 → stderr 单行报错 + 退出 2，不做任何检查 | 3.9 下退出 2 且报错含版本与 `python3.12` 指引 | ☑ |
| 2 | 换对解释器一切照旧 | 3.12 下 all 9×PASS、155 单测 OK、CI（钉 3.12）不受影响 | 双解释器原样输出留证于本表 | ☑ |
| 3 | 端点问题今天的真实状态 | 90s 一词探测（复现 T05 口径） | 探测结果回写 PLAN-LOOP-SMOKE-001 T05 证据列 | ☑ |
| 4 | Supervisor 亲写的代码过独立评审 | reviewer 子代理审 T01 diff + T02 原始输出（author≠verifier，不可豁免） | 评审轮次进 episode 的 review_roundtrips | ☑ |
| 5 | 会话丢失后本批仍可追溯 | EP-20260919-005 落盘 + 本计划回写收口 | `validate.py artifacts` 过 | ☑ |

**我们在哪**：T01–T05 全部完成；评审两轮 approved（第二轮为确认轮，首次恢复因宿主流错误 crash、一次重试成功）。
**下一步**：用户裁决 U-01（提交与 bump 时机）与 U-02（端点恢复后 T06–T08 的 18 次调用授权）。
**阻塞/风险**：无阻塞。风险：守卫挡掉 3.9 下本可用的 `report`/`recurrence`——接受，理由：声明下限就是 ≥3.10，混合解释器的"部分可用"正是今天误导输出的根源。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | validate.py `main()` 顶部加解释器守卫：`< (3,10)` → stderr 报错（含实测版本、下限、`python3.12` 指引、"No check was run."）并返回 2；≥3.10 行为零改动 | P0 | `tools/lab/validate.py` | — | ☑ 已完成 | diff 仅一个 hunk（纯新增 11 行，2879–2889）；raw diff 已送独立评审 |
| `T02` | 双解释器行为验证：3.9 → 期望 stderr 单行 + exit 2；3.12 → all 9×PASS exit 0 + unittest OK；确认 CI workflow 钉 3.12；记录七个 lab 工具均含 PEP 604 注解（下限事实） | P0 | — | `T01` | ☑ 已完成 | 3.9.6：单行 stderr + `exit_all_39=2`、`exit_report_39=2`；3.12.14：9×PASS exit 0、155 单测 OK；/tmp 副本 A/B 字节 IDENTICAL（exit_before=0、exit_after=0）；`.github/workflows/validate.yml:14` 钉 3.12 |
| `T03` | U-01 复测：`claude --print --output-format json --no-session-persistence` 一词探测、90s 超时；结果回写 PLAN-LOOP-SMOKE-001 T05 证据列 + updated_at | P1 | —（无代码） | — | ☑ 已完成 | 13:38Z 探测：90s `TimeoutExpired`、stdout/stderr 皆空——C10 挂起类持续，U-01 仍开；证据已回写 PLAN-LOOP-SMOKE-001 T05 |
| `T04` | 独立评审门：reviewer 子代理审 T01 的原始 diff 与 T02 原始输出；`changes_requested` 则一轮修复再审 | P0 | — | `T01`、`T02` | ☑ 已完成 | agentflow:reviewer **approved**（status: complete，零必改项，三项残余风险记录在案）；其两项 authored checks 已执行并回传原始输出（porcelain 对账 + A/B IDENTICAL），确认轮回复见 episode review_roundtrips |
| `T05` | 收口：EP-20260919-005 落盘（含 review_roundtrips）+ 本计划回写 + `validate.py artifacts` 过 | P0 | `records/episodes/2026-09-19/` | `T03`、`T04` | ☑ 已完成 | EP-20260919-005 落盘（5 claims 全 verified、E1–E4 含逐字附证、两轮 review_roundtrips）；`artifacts` PASS；最终 `python3.12 validate.py all` 9×PASS（证据见下） |
| `T06` | 提交 + CHANGELOG/iteration-log + 五 manifest bump | P1 | — | `T05` | — 本期不做 | 用户未要求提交；随下次发布批执行（未决项 U-01） |

### 未决项

| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | 本批改动（连同在途 smokeloop 批）的提交与版本 bump 时机 | 不阻塞 | 未关闭 |
| U-02 | 若 T03 探测恢复，PLAN-LOOP-SMOKE-001 T06–T08 的 18 次真实调用成本授权 | 不阻塞 | 未关闭 |

## 接口与共享机制

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| `validate.py <target>`（全部 13 个 target） | 解释器 `< (3,10)` 时：stderr 单行报错，返回 2，不解析参数之后不执行任何检查 | fail-closed，"No check was run." | ≥3.10 下所有 target 行为逐字节不变；CI 钉 3.12 不受影响 |

| 共享机制 | 注册点 | 行为 | 受影响表面 |
| --- | --- | --- | --- |
| 保护区（本改动即 gate change） | `protected-paths.txt` 含 `tools/lab/` | 用户已授权，在受信任源码树由 Supervisor 实施，不进候选树 | 仅 `tools/lab/validate.py` 一个文件；不改 `tests/`、schema、protected 清单 |
| 8 个 lab 工具的 `from __future__ import annotations` | 各文件头部 | 使 3.9 能 import 但语义仍是 ≥3.10（tests 无 future import 故 3.9 即红） | 守卫把"偶然能跑"变成"显式拒绝"，与 docs 声明下限一致 |

**异常矩阵（关键链路：一次 validate.py 调用）**：

| 异常场景 | 检测 | 处理 | 重试 | 幂等前提 | 用户可见 |
| --- | --- | --- | --- | --- | --- |
| 解释器 <3.10 | `main()` 顶部 `sys.version_info` | stderr 单行报错 + exit 2 | 无——换解释器重跑 | — | 一行版本指引，不再是 8 绿 1 红 |
| 检查失败（≥3.10） | 既有 `report()` 语义 | 不变（PASS/FAIL + exit 1） | 按 SKILL 退回修复 | — | 不变 |
| `report`/`recurrence` 在 3.9 下被拒 | 同守卫 | 同上（有意为之，见风险注记） | 换 3.12 | — | 单行报错 |

**发布顺序与回滚**：不安装、不重装、不 bump、不提交。回滚点 = 移除守卫 hunk（手工反向 patch；按 AGENTS.md 禁用 `git restore`/`checkout` 回退真实树）；回滚后 `python3.12 tools/lab/validate.py all` 应仍 9×PASS。

**评审门**：T04，在 T05 收口前。reviewer 审 T01 原始 diff 与 T02 原始输出；Supervisor 亲写 → 门强制不可豁免（硬边界 1）。

## 验证命令

```sh
python3 tools/lab/validate.py all; echo "exit=$?"      # 期望: stderr 单行报错, exit 2
python3.12 tools/lab/validate.py all; echo "exit=$?"   # 期望: 9×PASS, exit 0
python3.12 -m unittest discover -s tests               # 期望: OK
python3 tools/lab/validate.py report >/dev/null; echo "exit=$?"   # 期望: exit 2（守卫全局生效）
```
