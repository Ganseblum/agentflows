# 计划

`plan-architect` 仅当 supervisor 提供明确输出路径时才在此写入版本化执行计划。计划是一个
**Markdown 混合体**——frontmatter 是机器校验的信封，正文是给人读的叙述与进展看板。它是
执行契约，不是改动代码的授权。

文件：`plans/<plan_id>.md`（文件名等于 `plan_id`），依
[`schemas/plan.schema.json`](../schemas/plan.schema.json) 以及 `tools/lab/validate.py` 中的
计划校验器校验。

## 结构

```text
---
plan_id / plan_version / status (draft|proposed|approved|superseded)
objective / recorded_at / updated_at   (+ superseded_by when superseded)
---

## 进展概览            # 一行进度 + 三视角概览表（业务侧/技术侧/交付效果）+ 我们在哪/下一步/阻塞
## 任务清单            # T01… 任务表：优先级/代码落点/依赖/状态/证据回写 + ### 未决项
## 接口与共享机制       # 契约表 + 异常矩阵 + 发布顺序×回滚点 + 评审门（谁审什么、在哪个任务前）
## 验证命令            # 验收命令与预期
```

## 机器断言（已校验）

- 文件名 = `plan_id`；`status` 为固定枚举；`superseded` 要求 `superseded_by`；
- 任务 ID 唯一；`依赖` 引用能解析到已列出的任务，且依赖图无环；
- 任务状态为固定枚举 `☐ 未开始 / ◐ 进行中 / ☑ 已完成 / ⚠ 阻塞 / — 本期不做`
  （自由文本状态会被拒绝）；
- `### 未决项` 中标记为阻塞且未关闭的行**阻止 `status: approved`**；
- 三个必需小节存在。

## 进展回写纪律

进展保存在计划自身（看板）里：任务完成后，**只**编辑它的 状态 与 证据回写 两列——最小
diff；绝不重写已完成的任务行，绝不用自由文本状态散文替换表格。会话死亡恢复协议读取
这张表，从工作区重新推导每个任务的状态。
