---
plan_id: PLAN-QUALITY-001
plan_version: 0.1.0
status: proposed
objective: 把 agentflow 从「门禁绿但效果未测」推进到 8 分：门禁可自证、计数可核、运行态同步、角色行为可测，并按预先写定的判据完成一次效果实验
recorded_at: 2026-10-13T20:30:00+08:00
updated_at: 2026-10-13T21:10:00+08:00
---

# 质量提升批 — 执行计划（PLAN-QUALITY-001）

> 执行契约，不是改代码授权。每完成一项，在「证据」列回写命令与原始输出的关键行。
> 基线（2026-10-13 记录，存于仓库外 `/tmp/quality-baseline/`）：`validate.py all` 9 项 PASS、退出码 0；单元测试 78 项 OK；ruff（默认规则）49 条、mypy 27 条；`tools/lab/validate.py` 2733 行。

## 进展概览
- 总任务 10 项：☑ 1 项已完成，◐ 3 项进行中，☐ 5 项未开始，— 1 项本期不做（M-F，阻塞于 Q-01、Q-03）。
- 阻塞：M-D 需用户重装插件；M-F 需用户确认 Q-01、Q-03。

## 分支策略
本批在 `main` 上直接执行：不新建分支。提交与推送须经用户明确授权（仓库 AGENTS.md：未经指示不提交、不推送）。门禁相关改动（`tools/lab/`、`protected-paths.txt`、`.github/`）完成后须经独立评审，作者不验收自己的改动。

## 任务清单
| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 记录基线：`validate.py all` 输出（去行号）、退出码、单元测试数、ruff/mypy 数量 | P0 | `tools/lab/validate.py` | — | ☑ 已完成 | `/tmp/quality-baseline/validate-all.txt`（sha256 `2bd7e2ca…a60ea78`）：9 PASS；单元测试 78 OK；ruff 49、mypy 27（工具装于仓库外虚拟环境 `/tmp/qtools`） |
| T02 | M-A 门禁拆分：`validate.py` 变为薄入口，检查函数迁入 `tools/lab/gate/` 各模块，单模块 ≤ 600 行；输出逐行与基线一致 | P0 | `tools/lab/validate.py`、`tests/test_lab_contracts.py` | T01 | ◐ 进行中 | 待回写 |
| T03 | M-C 计数脚本：新增 `tools/lab/counts.py`，文档计数用标记包裹，门禁比对 | P1 | `README.md`、`index.md`；新增 `tools/lab/counts.py`（待核实：创建后改为真实路径） | T01 | ◐ 进行中 | 待回写 |
| T04 | M-E 角色场景：每个角色两条「必须拒绝」场景，存于 `examples/roles/<角色>/` | P1 | `examples/`（新增 `roles/` 子目录，待核实：创建后改为真实路径） | — | ◐ 进行中 | 待回写 |
| T05 | M-B 变异测试：`tools/lab/mutate.py`，副本内施加变异，统计存活；清理存活项 | P0 | `tools/lab/validate.py`（待测对象）；新增 `tools/lab/mutate.py`（待核实：创建后改为真实路径） | T02 | ☐ 未开始 | 待回写 |
| T06 | 静态检查进门禁：ruff、mypy 基线清零后纳入 `validate.py all` | P0 | `tools/lab/validate.py`、`protected-paths.txt` | T02 | ☐ 未开始 | 待回写 |
| T07 | 门禁受保护面：`tools/lab/gate/`、`mutate.py`、`counts.py` 纳入 `protected-paths.txt` 与必需条目 | P0 | `protected-paths.txt`、`tools/lab/validate.py` | T02、T03、T05 | ☐ 未开始 | 待回写 |
| T08 | M-D 运行态同步：用户重装插件后 `validate.py installed` 退出码 0 | P0 | 待核实（宿主安装快照位于用户本机缓存，不在仓库内） | — | ☐ 未开始 | 外部条件：需用户重装插件后复跑；待回写 |
| T09 | 独立评审：门禁改动由 agentflow:reviewer 独立评审，评审记录落 `reviews/` | P0 | `reviews/`（待核实：评审记录路径按 reviews/README.md 落点） | T02、T05、T06、T07 | ☐ 未开始 | 待回写 |
| T10 | M-F 实验 harness：`experiment.py`，运行记录写入本批 `testing/` 目录 | P1 | 新增 `tools/lab/experiment.py`（待核实：创建后改为真实路径） | — | — 本期不做 | 外部条件：阻塞于用户确认 Q-01、Q-03，未执行 |

## 验证命令

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lab/validate.py all
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lab/doc_chain.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lab/doc_chain.py docs/features/feature-2026-10-13-质量提升
/tmp/qtools/bin/ruff check tools/lab tests
/tmp/qtools/bin/mypy tools/lab --ignore-missing-imports
```

## 偏差与纠正
- 2026-10-13：spec/be §6 与 design/be §1.1.2 曾把实验记录落点写为 `experiments/`，该目录不在文档链允许的子目录内（允许：proposal、spec、design、plan、reviews、testing），`artifacts` 门因此变红。已撤销该目录，落点改为 `testing/`，spec/design 的对应表述在本计划执行中同步修正。
