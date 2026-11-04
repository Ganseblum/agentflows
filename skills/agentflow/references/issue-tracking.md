# 问题闭环机制：发现 → ISSUE → 复发台账 → 反哺升级

> **加载者**：`skills/agentflow/SKILL.md` 路由「问题闭环」行与工程内容标准节；`execution.md` 与 `templates/host/maker.md` 指向它。缺陷落账、复发台账与按层归因时读。

> **解决什么**：痛点 5d / 6——评审、代码评审、测试执行发现的 F/B/N/P 系列问题，**只进 changelog 与评审文件，从不登记 ISSUE**，导致「同样的坑反复踩、无法归纳成 agentflow 升级项」。本册把「发现」强制闭环到 `issues/`，并接上既有的 `class_id` / `occurrence` 复发台账。
>
> **与既有体系的关系**：`templates/issue/issue-template.md`（bug 记录，带 `error_kind` / `attribution` / `provenance` / `class_id` / `occurrence`）已存在；本册是**强制触发协议**——把评审 / 测试发现也转化为该模板的 ISSUE 记录，并新增 `defect_class` 维度（规范 / 模板 / 流程 / 代码）。

## 0. 强制规则（分级落账）

落账分级——不是每条 finding 都升级成永久记录，但**确认缺陷不允许只活在会话里**：

1. **必须落账**：确认且需改代码（或确认需改规范 / 模板 / 流程）的缺陷，二选一——
   ① ISS 记录（复制 `templates/issue/issue-template.md` 到 `issues/ISS-<YYYY-MM-DD>-<slug>.md`）；
   ② 评审记录的缺陷表（位置 / 原因 / 处置 / 复验证据四字段齐全）。
   来源包括：独立评审的 finding（F/B/N/P 系列）、测试执行发现、运行中识别的流程 / 模板 / 规范缺陷。
2. **留在评审记录即可**：同轮立即修复、无外部影响、复验由确定性检查覆盖的低风险细节（错别字、
   措辞、临时未完成项）。不升 ISS，但批次收口的缺陷台账要在说明里给出这类条目的计数与去向。
3. **不得**：把确认缺陷只写进评审文件 / changelog / 会话而两处落账都没有；批次收口时
   issues/ 零记录、台账空表，而评审出现过 `changes_requested`。

同根因合并：同一根因的多个 finding 立一条记录，保留复现与影响面，`occurrence` 递增。

## 1. defect_class 维度（核心新增）

在 `issue-template.md` frontmatter 中**新增**字段（模板见 §4）：

```yaml
defect_class: 规范 | 模板 | 流程 | 代码
```

- `规范`：agentflow 的工程内容标准缺失 / 错（如「design/be 没要求幂等」）→ 升级对象是 `references/standards/*`。
- `模板`：某模板骨架缺失 / 误导（如「plan 把 curl 当会话闭环」）→ 升级对象是 `templates/*`。
- `流程`：工作流某环节缺 / 错（如「评审发现不登记 ISSUE」）→ 升级对象是 `SKILL.md` / `references/*` 流程。
- `代码`：目标仓被评审对象的代码缺陷 → 升级对象是目标仓。

配套维度 `escape_stage`（缺陷在哪一阶段逃逸，用于评估各门的拦截率）：

```yaml
escape_stage: 需求 | 设计 | 实现 | 测试 | 评审
```

「设计期发现的缺陷逃逸到评审才被抓」记 `评审`——同类逃逸反复出现，说明前一阶段的门或自检缺条款，
按 §3 升级。

> 用户原话：「方便知道具体的问题是规范问题还是模板设计缺陷、还是流程缺陷，好用来总结更新升级 agentflow」——`defect_class` 就是为此而生。

## 2. 复发台账（接既有 class_id / occurrence）

- 若同一类问题再次出现，复用同一 `class_id`（纯 ASCII 小写，如 `doc-drift`、`curl-as-e2e`、`no-data-model`），`occurrence` 递增（第 2 次 = `2`）。
- 台账落 `issues/recurrence/<class_id>.md`，每类一文件，记录：首次出现、各次 `ISS-*`、共性根因、是否已推动 agentflow 升级（PR / commit 链接）。
- 检索：`记录检索` 后 `query '<关键词>'`（默认覆盖 `记录根` 与 `再犯类记录根`）。

## 3. 闭环到升级

- `defect_class: 规范 | 模板 | 流程` 的 ISSUE 在 `verified` 后，**必须**提一条 agentflow 自身的改进（改 `references/` / `templates/` / `SKILL.md`），并把 commit / PR 填回 `fix_revision`；否则只修目标仓、根因仍在。
- 改进落点反馈到 `CHANGELOG.md`（不在 SKILL.md 写版本号）。

## 4. 模板补丁（加到 issue-template.md frontmatter）

在 `provenance` 之后新增一行（其它字段不变）：

```yaml
defect_class: <规范 | 模板 | 流程 | 代码>
```

并在填写说明中补一句：「`defect_class` 必填；规范 / 模板 / 流程类在 verified 后须回填 agentflow 改进 commit 到 `fix_revision`。」
