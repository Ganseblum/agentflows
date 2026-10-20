# Agentflow 方法行为规格（spec）

> 适用阶段：`spec/`。前置依赖：`proposal/proposal.md`（原文不改）、`../README.md`。
> 文档状态：待需求评审（独立评审，文档模式 review spec）。
> 冻结语义：本文件的条目即方法的行为承诺。条目变更 = 方法变更，走版本批（CHANGELOG）+
> 独立评审；不悄悄改。当前版本以五份 manifest 与 `CHANGELOG.md` 为准，本文不复述版本号。

## 0. Proposal 反审 checklist

> 纪律：对照 proposal 逐节挑缺口，登记如下。**标「阻塞」的项全部关闭后才能进入 Design**。
> 关闭方式三种：当场修复 proposal、由本 spec 条目承接、登记进 proposal §五台账。

| # | 缺口（对照 proposal 原文） | 阻塞 | 关闭方式 |
| --- | --- | --- | --- |
| C-1 | §1.3「宿主认证矩阵」承诺了"按宿主发测量证书"，但通篇未定义**什么是一份证书**、验收口径是什么 | 阻塞 | 由本 spec **S12** 承接：定义证书的构成与验收 |
| C-2 | §1.3「产品文档链」说四层，但没说产品线的 **plan 层放哪**（本仓 plan 契约在各批次 `plan/`，业务仓在目标仓约定位置） | 阻塞 | 由本 spec **S13** 承接：定义链条的目录映射 |
| C-3 | 旧设计文档与本链的内容冲突裁决规则写在 `README.md` 而不在 proposal | 非阻塞 | 已在 `README.md` 声明，接受现状；若评审认为应上收，回填 proposal |
| C-4 | §三 用户场景缺用户侧收益量化口径（OQ-1） | 非阻塞 | 已登记 proposal §五台账（OQ-1），待业务尺子跑通后定 |
| C-5 | §五台账 U-02「调用授权与预算」没有授权粒度定义（按次/按批/按预算上限） | 非阻塞 | 属执行期用户决策，不属产品规格；评测装置与三件套 2026-10-12 裁撤后失去对象，台账行已同步关闭 |

阻塞项 C-1、C-2 已由本文件承接关闭，本节全关。

## 1. 行为规格

> 每条：陈述（承诺什么）→ 验收口径（怎么算做到）→ 标尺（机器或流程用什么验证）。
> 状态枚举：`生效`（当前实现满足且有机器标尺）/ `在建`（实现或标尺缺一，缺什么写明）/
> `待验证`（有实现有标尺，但未在真实条件下跑过——如 live 评测）/ `已停用` / `已裁撤`（终态，注明日期与出处）。

### S1 触发与角色面

- **陈述**：方法以 Skill 形式被宿主加载；14 个角色是按需取用的能力清单（backend-engineer /
  frontend-engineer / plan-architect / technical-director / reviewer / test-planner / test-executor /
  bug-investigator / bug-fixer / bug-recorder / candidate-engineer / evaluator /
  feedback-analyst / release-governor），默认路径不启动不降低风险的角色。
- **验收口径**：角色文件齐全且 frontmatter name 与文件名一致；「不经点名获得正确路由」为
  设计意图——宿主侧未实测，按 S15 不作已验证声明。
- **标尺**：`validate.py docs`（角色引用解析 + name 一致性）；`validate.py manifests`。
- **状态**：生效。

### S2 主工作流十步

- **陈述**：Intake → 架构门 → Plan → Delegate → Implement → Integrate → 验证工件 → 评审门
  → 单轮修复 → Decide，十步为一次开发任务的默认骨架。
- **验收口径**：任意一次 material 改动能按十步还原出对应证据（计划、工件、评审、决定记录）。
- **标尺**：episode 落盘契约（`skills/improve/references/episode.schema.json`）+ `validate.py
  artifacts`。
- **状态**：在建（缺：十步顺序本身的独立机器标尺；证据还原由 episode 契约与 `validate.py
  artifacts` 覆盖，见 S15）。

### S3 委派契约与硬边界

- **陈述**：每次委派带独立声明的 `write_scope` 与 `read_scope`（读范围必须覆盖共享机制）；
  14 条硬边界对全部角色生效（作者不自证、授权不扩权、无授权不 push/发布、摘要不算验证、
  编译失败即退回、不改评判自己的门、隔离声明须有执法面、证据不改写只追加、无任务不启动
  角色、同因两次即停等）。
- **验收口径**：worker 交付被接受前，实际变更面与 `write_scope` 比对无越界；边界条款
  单点声明可审计。
- **标尺**：`tools/lab/isolation.py check-diff`；`contracts.md` 作为审计面文本。
- **状态**：生效。

### S4 独立评审门

- **陈述**：material 变更必须过独立评审；主会话 自己写了部分时该门不可豁免；评审者
  给 `approved` / `changes_requested` / `blocked` 且不静默修码；评审前端到端主路径至少
  真实执行一次。
- **验收口径**：material 变更的 episode 里 `review_roundtrips` 可追溯；用户可见路径有
  执行证据。
- **标尺**：episode schema 的 `review_roundtrips` 必填约束（0.8.0 起）+ `validate.py artifacts`。
- **状态**：生效（浏览器等主会话专属通道的"端到端执行"以 主会话 代跑 + 原始证据移交
  评审为准）。

### S5 失败语义

- **陈述**：worker 失败三类成文——crash → `blocked` + 具名原因（先做环境 vs 工作分诊）；
  timeout → `partial` 且丢弃未验证的在途工作；empty/invalid return → 带缺陷名退回一次再
  记 bug。编排层**不做**保底执行路径；降级 = 结果降级（partial/blocked + 丢弃在途）。
  由 主会话 依证据分类，崩溃的 worker 不自分类；超预算静默重试或给 crash 换标签是
  主会话 缺陷。
- **验收口径**：任一 worker 失败事件能归入三类之一且有对应记录动作。
- **标尺**：`contracts.md` Worker failure semantics 节 + episode 落盘。
- **状态**：待验证（条款与落盘标尺在案；真实 crash/timeout 注入演练未做，登记 design §2）。

### S6 记录体系

- **陈述**：记录各有 schema 与落点——bug（`docs/issues/`，含 `recurrence/` 再犯台账）、plan（批次内
  `docs/features/<批次>/plan/`）、review（`reviews/`）、episode（`episodes/`）、
  test-plan / test-run（`docs/features/<批次>/testing/`）、批次（`docs/features/<批次>/`）、
  在途与待验收工作文件（`docs/releases/`）。改进三件套与逐版本发布记录已停用
  （2026-10-12）。记录是 Markdown+YAML 或 JSON，过编译门才存在。
- **验收口径**：任何新记录落盘即可被检索与校验；失效记录不删除只改状态。
- **标尺**：`validate.py schemas` + `validate.py artifacts` + `record_store`（FTS5 读侧）。
- **状态**：生效。

### S7 改进环

- **陈述**：反馈 → episode → 归因 → 假设（预声明指标与拒绝条件）→ 候选（只动候选树，
  `check-diff` 拒绝触碰保护门）→ 独立评测 → policy 建议 → **人批门**发布。policy 拒绝
  基线与候选 digest 相同的对贴；候选不得松自己的评分 schema。
- **验收口径**（停用前口径，留存备查）：一次完整闭环产出四类工件（candidate / evaluations /
  comparison / policy 建议）且全部过编译门；发布由用户 `approved` 触发。
- **标尺（停用前口径）**：原 `validate.py evals` + runner + policy；`isolation.py check-diff` 保留为通用工具。
- **状态**：**已停用**（2026-10-12 用户拍板：改进三件套记录根与逐版本发布记录退役；
  方法级改动一律 `measurement: none`；恢复仪器化时落点由 主会话 显式指派）。

### S8 确定性验证面

- **陈述**：`validate.py all` 全套检查（schemas / examples / artifacts / protected /
  manifests / docs / tests / doc_chain 自测 / doc_chain_live 活面，9 项）全绿是任何交付的最低门槛；保护门清单
  （`protected-paths.txt`）覆盖评测官/发布官角色、测量路径、记录 schema、钉住
  回归测试；门变更须人工评审。
- **验收口径**：`python3 tools/lab/validate.py all` 退出码 0；`validate.py protected`
  拒绝清单失去覆盖。
- **标尺**：validate.py 自身 + `.github/` CI 门进（fail-closed）。
- **状态**：生效。

### S9 打包与安装

- **陈述**：marketplace 源指向 `packaging/build_runtime.py` 生成的瘦快照（含 agents /
  skills / schemas / 五份 manifest / 宿主包装 / protected-paths；排除 `docs/`、`episodes/`、
  `reviews/` 与 tests / tools / evals / examples / packaging/CHANGELOG）；五份 manifest 是唯一
  版本事实源；源码编辑在重装前不改变宿主行为。
- **验收口径**：生成目录存在且组件齐全，与源面逐字节一致（`validate.py manifests` 门内
  新鲜度检查）；宿主安装面由 `validate.py installed` 在重装后核实；克隆后先跑构建脚本
  （gitignore 产物）。
- **标尺**：`validate.py manifests`（名称/版本五处一致 + runtime 与源面新鲜度）；`validate.py
  installed`（宿主安装面，重装后适用）。
- **状态**：生效（生成树与源逐字节一致）；宿主安装快照落后——2026-10-13 复核 `installed`
  FAIL（cache 停留 0.10.0），重装后复跑核实（`PLAN-PRODUCT-001` T06）。

### S10 业务评测仪器（已裁撤）

- **原陈述**：业务任务度量切片以种子缺陷确定性评分；被测树含 `*.seeds.json` 时
  fail-closed；请求级 `allowed_tools` 与 `isolate_host_config` 为运行前置；claude 侧
  `observed_permission_denials` 宿主观测通道，缺失键 = 未观测而绝非 0。
- **状态**：**已裁撤**（2026-10-12 用户拍板「保公开、裁业务」）：`evals/business/`、
  `seed_grader.py` 与相关机器已删除，原文留存备查。同批公开套件也一并裁撤——
  `evals/public/`（15 用例）与 `evals/` 整树、runner/adapter/policy 及三个相关 schema
  已于同日**删除**，不再保留为仪器存量；恢复条件与重建清单见
  `docs/design-decisions.md` §3。

### S11 文档交付链（对外生成）

- **陈述**：用户要求产出文档集（需求提案/规格/技术方案/实施计划）时，方法按
  proposal → spec → design → plan 四层生成，各层骨架、质量判据与阶段门禁按
  `skills/agentflow/references/document-chain.md` 执行；spec 反审 proposal、独立评审在
  design 冻结前介入；目标仓已有模板体系时按目标仓的，本链是下限不是替代。
- **验收口径**：一次文档交付能指出四层文件、反审 checklist、评审记录（评审桥或目标仓
  约定位置）；跳门即违约。
- **标尺**：`references/document-chain.md`（本文 S11 的契约源）+ 评审桥
  `reviews/`（跨仓评审时）。
- **状态**：生效（本批建立；骨架由内部链自举验证——本目录即第一个完整样例）。

### S12 宿主认证证书（承接 C-1）

- **陈述**：一份"宿主测量证书"= 针对单一宿主的一次公开套件实跑记录：声明宿主与适配器、
  套件 revision、用例集、每用例结果与原始证据、guardrail 观测值，落在
  主会话 指派的落点并过编译门（三件套记录根已停用）。方法文本全宿主通用；**证书按宿主逐个发**，
  未发证书的宿主只声明"骨架兼容"，不声明行为等价。顺序：Claude 先、ZCode 次、Codex 基线证。
- **验收口径**：每个声称"已在宿主 X 验证"的结论能指到一份该宿主的 evaluation 记录；
  指不出的按未验证处理。
- **标尺**：`validate.py artifacts`（evaluation 编译门）。
- **状态**：生效（条款）；尚无首份证书——U-01 已解除（C12）但评测装置 2026-10-12 裁撤、无采集
  装置；现存 live 证据均为端点健康类（claude 侧一词探测 3/3 与 AF-001×3 试水见 C12；codex 侧
  一词探测见 X1），无套件级评测证据。

### S13 产品文档链条目映射（承接 C-2）

- **陈述**：产品线的文档链落在本目录（`docs/product/`）；执行契约层不另建，复用
  批次 `docs/features/<批次>/plan/`（机器校验契约不变）；业务仓的文档链落目标仓约定位置
  （无约定时 `docs/features/feature-*/`），其评审证据经评审桥落回本仓 `reviews/`。
- **验收口径**：任一产品线任务能在本链找到设计出处、在批次 `plan/` 找到执行契约；
  链内引用不断链。
- **标尺**：`validate.py docs`（引用/schema 引用存在性）。
- **状态**：生效。

### S14 外部文档评审桥

- **陈述**：对外部系统产出的文档做第二道评审时，按 feature 锚定目录
  `reviews/<project>-<feature-slug>/` 归档逐字快照（每轮一个 archive 子目录）、
  记录 source_revision、发现以 bug 记录落 `docs/issues/` 并按 provenance/attribution
  双维归因。
- **验收口径**：评审记录与全部归档文件存在且交叉引用可解析。
- **标尺**：`validate.py artifacts`（快照与发现存在性交叉检查）。
- **状态**：生效（2026-09-19 infinite-canvas 第六期计划评审为首个真实样例）。

### S15 诚实声明条款

- **陈述**：角色分离不是环境隔离（评测官/发布官同模型同宿主族，靠只读工具面 + 保护门
  分立）；`measurement: none` 是方法级改动的合法且诚实的取值；记录状态 `fixed-pending-review`
  在回归未跑前不得自称 verified。文档与记录不得声称未观察到的宿主行为。
- **验收口径**：抽任何记录/文档，其强度声明与证据等级一致。
- **标尺**：`validate.py recurrence` / `report`（状态与回归字段一致性）+ 人工评审。
- **状态**：生效。

## 2. 条目索引

| 条目 | 一句话 | 状态 |
| --- | --- | --- |
| S1 | 14 角色能力库，默认路径短 | 生效 |
| S2 | 十步主工作流 | 在建（流程标尺缺口） |
| S3 | 写/读范围分离 + 14 条硬边界 | 生效 |
| S4 | 独立评审门（作者参与不可豁免） | 生效 |
| S5 | 失败语义三类，编排层不做保底 | 待验证（注入演练未做） |
| S6 | 记录体系 + 编译门 | 生效 |
| S7 | 改进环：预声明 → 独立评测 → 人批门 | **已停用**（2026-10-12） |
| S8 | 确定性检查全套 + 保护门 | 生效 |
| S9 | 瘦快照打包，manifest 为版本事实源 | 生效（重装复核待做） |
| S10 | 业务尺子 | **已裁撤**（2026-10-12） |
| S11 | 文档交付链（对外生成） | 生效 |
| S12 | 宿主测量证书按宿主发 | 生效（条款）；尚无证书（装置裁撤） |
| S13 | 产品链目录映射 | 生效 |
| S14 | 外部文档评审桥 | 生效 |
| S15 | 诚实声明条款 | 生效 |
