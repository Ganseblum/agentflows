# 迁移规格（批 4 执行件）— 2026-10-09

> 本文件是 `records/` 记录的迁移契约：目标结构、重编号算法、引用改指规则、删除清单。执行结果映射表见 `migration-mapping.md`。

## 1. 目标结构与映射

| 源 | 目标 | 说明 |
| --- | --- | --- |
| `records/bugs/<日期>/<slug>.md` | `issues/ISS-2026-<NNN>-<slug>.md` | 见第 2 节重编号；`rejected` 归档规则不变（`issues/归档/<日期>/`） |
| `records/bugs/recurrence/` | `issues/recurrence/` | 复发台账 |
| `records/bugs/README.md` | `issues/README.md` | 以旧文为底，并入现有 `issues/README.md` 的编号/升级通道条款 |
| `records/episodes/**`（含 README） | `episodes/**` | 决策记录，保持现有格式 |
| `records/plans/**`（含 README） | `plans/**` | 计划契约保持 |
| `records/improvement/candidates/` `evaluations/` `comparisons/` | `improvements/`（同名子目录） | 改进环三件套 |
| `records/improvement/README.md` | `improvements/README.md` | 并入 releases 迁移说明 |
| `records/improvement/releases/*.json` | `releases/` | 发布记录 |
| `records/reviews/**`（含 archive/） | `reviews/**` | 评审桥落点（`reviews/README.md` 已存在，保留） |
| `records/tests/README.md` | `_archive/records-2026-10/tests/README.md` | 后续测试件落 `features/<批次>/testing/` |
| `records/README.md` | `_archive/records-2026-10/README.md`（桶声明；原文件入 `readmes/`） | 记录树退役说明 |
| `docs/audit-2026-09-18/**` | `_archive/audit-2026-09/**` | 冻结（只读） |
| `docs/audit-2026-09-18-followups.md` | `_archive/audit-2026-09/followups.md` | 同上 |
| `docs/next-session-handoff.md` | `_archive/handoff-2026-10/next-session-handoff.md` | 同上 |

迁完后删除 `records/` 空壳与全仓 `.DS_Store`。

## 2. bug 重编号算法

按（日期目录升序，原 `bug_id` 尾段数字升序，文件名）排序，依次赋 `ISS-2026-001` … `ISS-2026-<NNN>`。同步机械替换（不改语义/结论/时间戳）：

1. 文件名与 frontmatter `bug_id`；
2. 复发台账 `occurrences` 与正文交叉引用中的旧编号；
3. 被移动文件正文中的旧编号与 `records/` 路径引用（含 `files:` 条目）。

对照表落 `migration-mapping.md` 表 1。

## 3. 引用改指规则（被移动文件内）

`records/bugs/` → `issues/`；`records/bugs/recurrence/` → `issues/recurrence/`；`records/episodes/` → `episodes/`；`records/plans/` → `plans/`；`records/reviews/` → `reviews/`；`records/improvement/releases/` → `releases/`；`records/improvement/` → `improvements/`。通用形示例一并换算。无法解析的引用逐条列出报告（不外推、不删改）。

## 4. 删除清单

- `records/` 空壳（确认无遗漏文件后删除）；
- 全仓 `.DS_Store`。

## 5. 边界

不改写结论/证据/时间戳；不动 `tools/ tests/ schemas/ skills/ agents/ mock/ examples/ evals/ README.md AGENTS.md index.md CHANGELOG.md docs/`（除第 1 节列明的 docs 迁移件）；不 commit/push；`_archive/` 内只读。
