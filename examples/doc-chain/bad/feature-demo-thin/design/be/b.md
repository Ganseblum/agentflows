# feature-demo-thin 后端设计

用游标分页，具体字段后面再定。

## 决策

| # | 决策 | 结论 |
| --- | --- | --- |
| D1 | 分页方式 | 游标 |

## 时序

```mermaid
sequenceDiagram
    C->>S: 请求列表
    S-->>C: 返回结果
```
