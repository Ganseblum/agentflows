# features — 批次与实施计划

成批或跨层工作使用 `feature-<YYYY-MM-DD>-<主题>/`。轻量改动用一个 README，完整批次按需要选轨。

```text
docs/features/
  feature-<YYYY-MM-DD>-<主题>/
    README.md      # 批次入口：范围、文档导航、计划位置
    proposal/      # 提案：为什么做、做什么
    spec/          # 规格：验收口径与契约
    design/        # 方案：怎么做（异常矩阵、时序图、状态图随需要）
    plan/          # 计划：任务表与执行契约
    testing/       # full 测试计划与运行记录；light 内嵌唯一 README
```

阶段已有对应材料时，在批次 README 链接其位置。未选轨标理由；每项进度与依赖只回写计划任务表。

## 批次索引

当前项目批次集中导航在[仓库索引](../../index.md)。早期十个批次正文可从
`agentflows@c8ed0b2:docs/features/<批次目录>` 取回，版本结论见[变更日志](../../CHANGELOG.md)。

## 纪律

- 按[唯一文档档位](../../skills/agentflow/references/document-chain.md#文档档位)选材料：light 用唯一 README；full 建目标→规格→任务承接关系，引用原计划状态，不复制另一看板。旧历史格式不批量回改。
- AC 定义在规格，用例来源/步骤/预期只在 Markdown 注册表与详情，执行结果只在绑定版本的 run；light 使用 README 同义节。spec 不另维护 AC↔TC 映射或本轮执行状态。
- 新增批次时更新索引。改动接口、状态或路径时，核对所有使用它的角色、模板和工具。
- 目录由已授权的接入或立项创建；接受者对实际文件按文档链人工核对。目标仓配置了真实结构或文本检查命令时再运行并附输出，本插件不再提供旧 C1–C14 检查器。
- 本仓批次的 `plan/<plan_id>.md` 由主审与独审核对文件名、状态和任务依赖（完整判据见下节）；目标仓默认 `plan/execution.md`，不套用本仓文件名约定。没有工具时不得把人工核对写成 linter 通过。
- 批次关闭时在 `decision.md` 保留结论、证据和待补项，版本摘要进 `CHANGELOG.md`。整理历史目录时保留可解析的 Git 修订。
- 缺陷与未决事项放该批次的缺陷记录或决策记录。在可访问证据缺失时说明缺口和核验方法。

## 计划形态

`plan-architect` 在获得明确输出路径时写计划。Markdown 元信息里的 `status` 记录审批，任务表记录执行事实。按[文档交付链](../../skills/agentflow/references/document-chain.md)核对两种状态及开始条件。

```text
---
plan_id / plan_version / status (draft|proposed|approved|superseded)
objective / recorded_at / updated_at   (+ superseded_by when superseded)
---

## 进展概览            # 当前阻塞和下一步，可从任务表提取
## 分支策略            # 工作分支与依据（计划契约要求声明分支策略）
## 任务清单            # T01… 任务表：优先级/代码落点/依赖/状态/证据回写 + ### 未决项
## 接口与共享机制       # 契约表 + 异常矩阵 + 发布顺序×回滚点 + 评审
## 验证命令            # 验收命令与预期
```

接受时核对本仓文件名与 `plan_id` 一致、任务 ID 唯一、依赖无环、审批条件满足。实施评审追加实际冻结对象与任务范围的证据；只审早期材料时标清对象和阶段。

进展回写纪律：任务完成后**只**编辑它的 状态 与 证据回写 两列——最小 diff；绝不重写已完成
的任务行，绝不用自由文本状态散文替换表格。会话死亡恢复协议读取这张表，从工作区重新推导
每个任务的状态。

缺陷升格时用缺陷编号与批次入口互相引用。完成项的证据标准见[阶段评审与完成证据](../../skills/agentflow/references/document-chain.md#阶段评审与完成证据)。
