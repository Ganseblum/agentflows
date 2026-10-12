# features — 批次与实施计划

成批 / 跨层工作以批次目录组织（形态对齐 youc-workflow-ai 与 aiwork-workflow-ai）：每个批次
一个目录，命名 `feature-<YYYY-MM-DD>-<主题>/`，按文档链五段落位。

```text
docs/features/
  feature-<YYYY-MM-DD>-<主题>/
    README.md      # 批次入口：背景、范围、段落映射、推进进度
    proposal/      # 提案：为什么做、做什么
    spec/          # 规格：验收口径与契约
    design/        # 方案：怎么做（异常矩阵、时序图、状态图随需要）
    plan/          # 计划：任务表与执行契约
    reviews/       # 评审落点（可选）
    testing/       # 测试计划与运行记录（可选）
```

段落可为空但必须在批次 README 的「段落映射」表里写明落点——若 proposal/spec/design 由
其他活文档承载（如产品链的 `docs/product/`），在表里指向它，不重复造册。

## 在途批次

| 批次 | 性质 | 状态 |
| --- | --- | --- |
| [`feature-2026-09-19-产品线完善`](feature-2026-09-19-产品线完善/) | 方法自身产品线（proposal/spec/design 见 `docs/product/`） | 在途（计划在册，评审修复轮待排） |

## 纪律

- 目录由「首次接入 / 批次立项」创建；对实际目录跑
  `python3 tools/lab/doc_chain.py <feature-dir>` 接受文档链，全绿才算链完成。
- 批次内的 `plan/<plan_id>.md` 受计划契约校验（文件名 = `plan_id`、固定状态枚举、任务表
  依赖图无环——完整断言见下节）；其他段落由文档链 linter 管。
- 完成批次不长期留存：结论写进 `CHANGELOG.md` 与 episode 后随瘦身批删除，git 历史
  即归档（2026-10-12 起本仓不保留归档桶）。
- 开放事项：缺陷走 `docs/issues/`，跨批次待拍板走 `docs/PENDING-DECISIONS.md`。

## 计划形态（原 `docs/plans/README.md`，随 2026-10-12 归位并入）

`plan-architect` 仅在 supervisor 提供明确输出路径时才写入版本化执行计划。计划是
**Markdown 混合体**——frontmatter 是机器校验的信封，正文是给人读的叙述与进展看板。它是
执行契约，不是改动代码的授权。

```text
---
plan_id / plan_version / status (draft|proposed|approved|superseded)
objective / recorded_at / updated_at   (+ superseded_by when superseded)
---

## 进展概览            # 一行进度 + 三视角概览表 + 我们在哪/下一步/阻塞
## 任务清单            # T01… 任务表：优先级/代码落点/依赖/状态/证据回写 + ### 未决项
## 接口与共享机制       # 契约表 + 异常矩阵 + 发布顺序×回滚点 + 评审门
## 验证命令            # 验收命令与预期
```

机器断言：文件名 = `plan_id`；`status` 固定枚举；`superseded` 要求 `superseded_by`；任务 ID
唯一且依赖图无环；任务状态固定枚举 `☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做`；
`### 未决项` 中阻塞行未关闭则阻止 `status: approved`；三个必需小节存在。

进展回写纪律：任务完成后**只**编辑它的 状态 与 证据回写 两列——最小 diff；绝不重写已完成
的任务行，绝不用自由文本状态散文替换表格。会话死亡恢复协议读取这张表，从工作区重新推导
每个任务的状态。

## 升格与登记

- **issue → feature 升格**：中/大问题经用户确认后升格为批次，在 `docs/issues/README.md` 的
  升级通道处置，并在**两处**登记：原 issue 记录的状态节写「已升格并入 `<批次目录>`」，
  批次 README 的「元信息」节写「升格来源：ISS-YYYY-NNN（原由）」。升格即留痕，不靠记忆。
- **批次完成**：结论入 `CHANGELOG.md` 与 episode，批次目录删除（git 历史即归档）。
