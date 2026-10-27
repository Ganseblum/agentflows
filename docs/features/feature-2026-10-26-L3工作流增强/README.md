# L3 工作流增强

> agentflow 目标承接
> 文档档位：完整。UI 轨未启用；埋点 N/A。
> 落点基准：.

## 元信息

用户要求全部实施十四项吸收建议并删除冗余，允许合理结构改造。截至 `17ccbd7` 已随 0.19.1 推送 `origin/main` 并装入 ZCode 与 Codex（`validate.py installed` PASS）。状态以计划任务表为准，不在本文件维护第二份进度。

## 段落映射

| 段落 | 落点 | 说明 |
| --- | --- | --- |
| proposal | `proposal/proposal.md` | 用户原话、目标与范围 |
| spec | `spec/be/backend.md`、`spec/qa/acceptance.md` | 运行规则及验收 |
| design | `design/be/backend.md`、`design/qa/testing.md` | 字段、时序、状态、失败及回滚 |
| plan | `plan/PLAN-L3-001.md` | 唯一任务状态来源 |
| testing | `testing/agentflow-workflow/` | 原始命令输出与实验 |
| reviews | `reviews/` | 独立评审 |

## 阶段检查清单

- [x] 提案及规格成文，待决业务语义为空。
- [x] 需求评审：独立检查需求和验收，见第二轮评审。
- [x] 技术方案成文，字段及失败分支明确。
- [x] 技术方案评审：独立检查设计与实际实现，见第二轮评审。
- [x] 链路收口：实际检查、逐项证据与独立实现复审已完成；最终记录一致性另行核对。

## 目标承接表

| 目标 | proposal 出处 | spec 承接 | plan 任务 | 状态 |
| --- | --- | --- | --- | --- |
| G1 执行方法增强 | `proposal/proposal.md` §1.2 | M01，G1-AC-01、G1-AC-02、G1-AC-03 | T03、T04 | ☑ 已完成 |
| G2 执行证据能力 | `proposal/proposal.md` §1.2 | M02，G2-AC-01、G2-AC-02、G2-AC-03、G2-AC-04 | T02、T05、T06 | ☑ 已完成 |
| G3 去重与合理分档 | `proposal/proposal.md` §1.2 | M03，G3-AC-01、G3-AC-02 | T03、T04 | ☑ 已完成 |
| G4 验证与安装一致 | `proposal/proposal.md` §1.2 | M04，G4-AC-01 | T01、T05、T06、T07、T08 | ☑ 已完成 |

## 十四项落地对照

本表只指向规则与证据，不复制执行方法。逐文件映射见 [实施映射](testing/agentflow-workflow/evidence/adoption-implementation-map.json)。

| 项 | 已吸收内容 | 使用入口 | 验证 |
| --- | --- | --- | --- |
| 1 | 行为变更测试先行 | 执行协议 | 方法核对及真实Node Red→Green |
| 2 | 有效失败与环境失败区分 | 执行协议、run | TC-WF-004 |
| 3 | 按行为切片实施 | 执行协议、计划模板 | 独立方法核对 |
| 4 | 实际环境预检 | 执行协议、preflight | 原生运行中Node预检 |
| 5 | 选测与证据复用依据 | 执行协议、测试记录模板 | 独立方法核对 |
| 6 | 记录合法、执行结果、覆盖复核分开 | 测试记录、run | TC-WF-003、独立评审 |
| 7 | 六组短提示词 | 快速开始 | 独立方法核对 |
| 8 | 已答复选择复用 | Skill入口、执行协议 | 独立方法核对 |
| 9 | 计划指纹与输入重检 | seal、verify、run | TC-WF-002、TC-WF-005 |
| 10 | 原生报告对应精确用例 | run与报告解析 | TC-WF-003、TC-WF-004 |
| 11 | 遗留补测盘点与分批 | inventory、补测模板 | TC-WF-007 |
| 12 | 按实际依赖隔离失败 | run | TC-WF-006 |
| 13 | 托管写入与过期预览保护 | managed-preview、managed-apply | TC-WF-008、TC-WF-009 |
| 14 | 简单任务可判定轻量档 | 轻量模板、文档链检查 | TC-WF-010 |

规则与用法分别见 [执行协议](../../../skills/agentflow/references/execution.md)、[证据工具](../../../skills/agentflow/references/workflow-tool.md)、[快速开始](../../quickstart.md)。0.19.1 已于 `17ccbd7` 完成双端安装核验；后续 0.19.2 修正属于本地 main，尚未发布或重装，不代表宿主已加载这些修正。方法疗效未测量。

## 交付记录

[逐用例结果](testing/agentflow-workflow/run-2026-10-27-001.md) · [首轮发现](reviews/review-2026-10-27-001.md) · [修复后批准](reviews/review-2026-10-27-002.md) · [任务级记录](../../../episodes/2026-10-27/EP-20261027-001.json)。本批已进入 Git 历史（`17ccbd7`），材料保留供审查；证据的复核以该提交为准。

## 合并后修正

本地main在 `57e45d2` 收录备份历史，保留已验证文件树。四条开发分支已在主线；两个旧工作树的28文件与既有集成来源摘要一致，不用旧候选覆盖后续修复。分支和文件证据见 [整合记录](testing/agentflow-workflow/evidence/main-integration-2026-10-27/branch-integration.json)。

后续四项状态分别以缺陷记录为准：[清单读取失败](../../issues/ISS-2026-062-门清单部分输出失败仍被放行.md)、[计划模板标题](../../issues/ISS-2026-063-计划模板验证标题不匹配.md)、[测试方法重复](../../issues/ISS-2026-064-测试入口重复定义失败范围.md)、[安装摘要矛盾](../../issues/ISS-2026-065-L3批次安装摘要前后矛盾.md)。本次不修改既有计划已完成任务的定义，也不回写历史执行结果。

独立收尾见 [四项修正评审](reviews/review-2026-10-27-003.md) 与 [任务级记录](../../../episodes/2026-10-27/EP-20261027-002.json)。
