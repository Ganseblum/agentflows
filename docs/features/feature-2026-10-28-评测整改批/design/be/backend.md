# 设计：评测整改批（工具与契约面）

## 1. 决策表

| 决策 | 选项 | 选定 | 理由 |
| --- | --- | --- | --- |
| D1 整改状态载体 | A 新建追踪文件 / B 审计表加列 / C 登记进 PENDING | **B** | 状态与发现同址，不会两处漂移；PENDING 只承载待拍板项 |
| D2 分级档位形态 | A 百分比覆盖率 / B 三档枚举 / C 布尔 has_review | **B** | 可判定、可复核；百分比无真源 |
| D3 分级协议落点 | A 新建 reference / B `contracts.md` 新节 / C SKILL 正文 | **B** | `contracts.md` 是硬边界的唯一权威，分级是边界的补充而非新机制 |
| D4 `.venv` 探测 | A 改 lint 为 SKIP / B 新增解释器探测 / C 只写文档 | **B** | 保持 fail-closed（G01 结论），只扩大「能找到工具」的路径 |
| D5 候选记录落点 | A `examples/` 合成 / B 批次 `improvement/` 真实 | **B** | 目标是给两份 schema 第一份**真实**消费者，合成例已在 G10 补齐 |

## 2. 评审分级状态机

```mermaid
stateDiagram-v2
    [*] --> Probe: 需要独立评审
    Probe --> L2: 派发成功（≥2 角色可用）
    Probe --> L1: 仅 1 个只读角色可用
    Probe --> L0: 全部派发失败（额度/加载）
    L2 --> Recorded: 评审记录落盘
    L1 --> Recorded: review_tier=L1
    L0 --> SelfReview: 主审自审 + 全套确定性门
    SelfReview --> Recorded: review_tier=L0 + 原始错误留痕
    Recorded --> PendingReopen: 门未真正关闭
    PendingReopen --> Probe: 能力恢复后补门
    Recorded --> [*]: 门关闭
```

**不变式**：`L0` 状态下不得对**用户可见行为改动**做最终放行；`Recorded` 转 `[*]` 前，
若 `review_tier ∈ {L0, L1}`，必须存在一条「补门」记录或显式的用户接受。

## 3. 主流程

```mermaid
flowchart TD
    A[需要独立评审] --> B{派发只读角色}
    B -->|成功 r≥2| C[L2 独立评审]
    B -->|成功 r=1| D[L1 单角色评审]
    B -->|全部失败| E[L0 主审自审]
    C --> F[评审记录 + review_tier]
    D --> F
    E --> G[确定性门全套实跑]
    G --> H{用户可见行为改动?}
    H -->|是| I[标注待补门 + 不得最终放行]
    H -->|否| F
    I --> F
    F --> J{门是否真正关闭}
    J -->|否| B
    J -->|是| K[接受产物]
```

## 4. 失败分支时序

```mermaid
sequenceDiagram
    participant S as 主审
    participant H as 宿主委派
    participant R as Reviewer
    participant G as 确定性门
    S->>H: 派发只读评审角色
    alt 派发成功
        H->>R: 装载角色 + 简报
        R-->>S: approved / changes_requested / blocked
        S->>G: 按 reviewer 给出的命令实跑
        G-->>S: 原始输出
    else 派发失败（额度耗尽 / 角色加载失败）
        H-->>S: 错误原文（model concurrency limit exceeded 等）
        S->>S: 记录 review_tier=L0 与错误原文
        S->>G: 自审 + 全套确定性门
        G-->>S: 原始输出
        S->>S: 若涉用户可见行为，标注待补门且不得最终放行
    else 评审返回 blocked
        S->>S: 升级阻塞点与最小决策，不自行放行
    end
```

## 5. 字段级契约

整改状态列与分级记录字段的契约如下（本批不新增对外接口，以下为记录字段口径）。

| 契约项 | 请求字段 | 响应字段 | 失败行为 |
| --- | --- | --- | --- |
| 审计发现表（C01） | `#`、`严重度`、`发现`、`位置`、`解锁条件`、`整改状态`、`fix_revision` | 表格行，7 列 | 缺列或空值 → 人工复核判不合格；本批不新增机器门（避免门变更扩容） |
| 分级记录（C02） | `review_tier`（L0/L1/L2）、`dispatch_errors[]`（失败原文） | 决策记录/episode 字段 | L0 且无 `dispatch_errors` → 视为伪降级，评审无效 |
| lint 解释器解析（C03） | `AGENTFLOW_LINT_PYTHON`（env，可选） | 实际使用的解释器路径 + lint 结果 | 未设且无 `.venv` → 原行为 FAIL，不新增放行 |

## 6. 影响面与回滚

| 改动 | 影响面 | 回滚 |
| --- | --- | --- |
| `contracts.md` 新增分级节 | 所有委派的评审纪律读取面 | 删除该节，恢复原文；无机器依赖 |
| `SKILL.md` 去重与引用 | 主流程第 8 步 | 恢复两处原文 |
| `document-chain.md` 判据速查 | 轻量档入口 | 删除速查块 |
| `roles.md` 裁决规则 | FE/BE 角色边界 | 删除规则段 |
| `validate.py` / `pre-push.sh` JSON 探测 | 门执行路径（受保护面） | 恢复原解释器选择逻辑 |
| 新增批次 `improvement/` 记录 | 改进环输入面 | 删除记录，schema 不受影响 |

**回滚点**：本批在分支上以单一提交序列交付，任一步失败可回到 `de80694`（0.19.3）。

## 7. 分支策略

| 仓库 | 用途 | 基线 | 基线提交 | 开发分支 | 确认状态 | 确认依据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentflows | 实施与测试 | main | de806947d22665d347007b690d22136a1a442dca | feature-2026-10-28-评测整改批 | 已确认 | 用户在 2026-10-28 批准五批方案后由本次实施建分支 | 不推送、不合并、不重装 |
