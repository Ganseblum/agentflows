# feature-demo 实施计划

## 0. 分支策略

分支 `feature/feature-demo`，单点写入；合入前 rebase 到目标分支最新。

## 1. 任务表

| ID | 任务 | 代码落点 | 依赖 | 状态 |
| --- | --- | --- | --- | --- |
| T01 | 联合索引改造 | `migrations/20261013_task_cursor.sql` | — | ☐ |
| T02 | 游标分页接口 | `internal/api/task_list.go` | T01 | ☐ |
| T03 | 前端翻页与失败态 | `web/src/features/task/List.tsx` | T02 | ☐ |

V-1 由 T01 承接。

## 2. 发布顺序与回滚点

| 步 | 动作 | 回滚点 |
| --- | --- | --- |
| 1 | 执行 T01 迁移 | 迁移可回滚脚本 |
| 2 | 发布 T02 接口 | 切回上一镜像 |
| 3 | 发布 T03 前端 | 前端回滚到上一版本 |
