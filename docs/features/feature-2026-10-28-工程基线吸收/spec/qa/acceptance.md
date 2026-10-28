# 工程基线吸收批 — 验收标准（spec/qa）

> 前置输入：proposal、spec/be。
> 来源优先级：本文件逐条验收口径按「proposal 原文 > spec/be」的顺序裁决；冲突登记进 §0.1，不静默择一。

## 0. 来源对齐缺口（GAP）

### 0.1 GAP 台账

| 编号 | 待对齐文档/实现 | 影响阶段 | 关闭条件 | 关联 Q 编号 |
| --- | --- | --- | --- | --- |
| GAP-01 | 工程基线模板在目标仓的具体落点（独立文件 vs `AGENTS.md` 节） | Design/接入 | Init 与用户确认后写入接入小节；本批只要求「落点由用户拍定」的口径存在 | 无 |

## 1. 目标范围与不做

| 类型 | 内容 | 依据/承接方 |
| --- | --- | --- |
| 实现改动范围 | 工程基线模板 + Init 六项；design/be 字段与配置核对 + backend-engineer；prototype 自检 + 链契约指针；testing/plan 三维 + test-planner | proposal §1.3 |
| 范围外 | 复制项目规范正文、部署/Fork/迁移约定、域技能、`UPGRADE_RECORD`、中文注释强制、脚本门、跨批次流程总览 | proposal §1.3 逐条理由 |

## 2. 边界与异常覆盖

| 类型 | 条件/触发 | 正确结果 | 关联 AC |
| --- | --- | --- | --- |
| 模板缺失事实 | 目标仓没有某项事实（如无钩子、无多站点） | 写「不适用 + 理由」或「无钩子」，不留空、不套默认值 | G1-AC-02 |
| 既有规范冲突 | 目标仓已有规范与模板形态冲突 | 以目标仓为准并登记例外；不覆盖既有规范 | G1-AC-03 |
| 配置表空填 | 新增配置项但核对表只写表头 | 视为未完成，评审可退回；计划模板要求逐项结论 | G2-AC-02 |
| 原型无脚本 | 原型没有构建链或自动化 | 人工/浏览器走查仍必须做；不因「没有脚本」跳过 P1–P5 | G3-AC-01 |
| 测试维度不适用 | 纯文档或纯类型改动 | 写「不适用 + 理由」，不机械新增用例 | G4-AC-01 |
| 生成树漂移 | 模板改动后未重建 `packaging/runtime` | `validate.py all` 的生成树新鲜度检查失败 | G1-AC-01 |

## 3. 模块验收点

### M01 目标仓工程基线（G1）

| 验收点 | 验收目标 | 场景/条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G1-AC-01 | 工程基线模板存在且十个固定小节（0–9）齐备 | 检查 `skills/agentflow/templates/engineering/baseline.md` | 十个固定标题全部出现；模板索引与 `index.md` 各有一条指针；`packaging/runtime` 有同一文件 | P0 | spec/be §1 M01 |
| G1-AC-02 | Init 由五项变六项并写明基线入口 | 检查 `skills/agentflow/SKILL.md` 的 Init 节 | 出现「六项」与「工程基线」；接入小节要件写明「已有规范入口 / 最小基线路径」；缺失按缺口上报 | P0 | spec/be §1 M01 |
| G1-AC-03 | 不复制项目事实、不覆盖既有规范 | 阅读模板与 Init 文字 | 模板所有事实项都是 `<填>`；有「形态不是默认值」「冲突以目标仓为准」的显式声明 | P1 | proposal §1.3、spec/be §2 |

### M02 后端数据与配置核对（G2）

| 验收点 | 验收目标 | 场景/条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G2-AC-01 | `design/be` 含字段与数据核对表 | 检查 `templates/feature/design/be/backend.md` | 新增核对小节，覆盖 spec/be §1 M02 的 8 类核对项；§4 自检多一条 | P0 | spec/be §1 M02 |
| G2-AC-02 | 配置项与运行边界表可填 | 同上 | 配置表含 12 列；边界表含 7 列；`backend-engineer` 有对应执行纪律段 | P0 | spec/be §1 M02 |

### M03 原型可点性与 Mock 约定（G3）

| 验收点 | 验收目标 | 场景/条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G3-AC-01 | 自检含 P1–P5 五项 | 检查 `templates/feature/prototype/README.md` | 五个核对项全部出现；保留「人工执行、无机器门」声明 | P0 | spec/be §1 M03 |
| G3-AC-02 | 链契约有同一判据指针 | 检查 `references/document-chain.md` 产品原型节 | 出现控件反馈/隐藏态/假数据形态/「脚本只作线索」的判据句 | P1 | spec/be §1 M03 |

### M04 测试设计三维（G4）

| 验收点 | 验收目标 | 场景/条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G4-AC-01 | 计划模板含三行方向 | 检查 `templates/testing/plan.md` | 「并发与竞态」「生命周期与清理」「契约与兼容」三行存在，且表下有最小必测集说明 | P0 | spec/be §1 M04 |
| G4-AC-02 | `test-planner` 指明取舍要写进计划 | 检查 `agents/test-planner.md` | 有三维度与按功能形态取最小必测集的句子 | P1 | spec/be §1 M04 |

### M05 前端实现纪律与设计核对（G5）

| 验收点 | 验收目标 | 场景/条件 | 可观察结果 | 优先级 | 来源 |
| --- | --- | --- | --- | --- | --- |
| G5-AC-01 | 角色含五组 FE 纪律 | 检查 `agents/frontend-engineer.md` | 请求/缓存/生命周期、契约字段与类型边界、性能/可访问性/媒体/配置、注释与拆分四段齐备；关键判据（取消、晚到响应、缓存键、失效、401、零值、必需回调、unknown、可访问名称、Blob URL、公开配置）逐项命中 | P0 | spec/be §1 M05 |
| G5-AC-02 | `design/fe` 表与自检含对应行 | 检查 `templates/feature/design/fe/frontend.md` | §1.3 两行、§1.4.3 两行、§1.4.5 三行、§4 四条自检齐备 | P0 | spec/be §1 M05 |
| G5-AC-03 | `spec/fe` 有可观察的前端行为口径 | 检查 `templates/feature/spec/fe/frontend.md` | §2.1 六行表齐备（刷新/并发/身份/空值/键盘/媒体） | P1 | spec/be §1 M05 |
| G5-AC-04 | 工程基线含请求层与 UI/文案/可访问性基线 | 检查 `templates/engineering/baseline.md` | 请求层与客户端边界段存在；多站点、i18n、可访问性、格式与命名四条齐备 | P1 | spec/be §1 M05 |

## 4. AC×用例覆盖映射

| 验收点 AC | 关联用例/覆盖项 | 状态 |
| --- | --- | --- |
| G1-AC-01 | `testing/agentflow-baseline/evidence/T01-baseline-template.txt`（标题计数 + 可填性 + 指针 + 生成树逐字节） | 已覆盖 |
| G1-AC-02 | `testing/agentflow-baseline/evidence/T02-init.txt`（Init 节逐字输出） | 已覆盖 |
| G1-AC-03 | 人工评审项：模板占位与冲突声明逐条核对（`reviews/review-2026-10-28-001.md`） | 已覆盖（独立评审） |
| G2-AC-01 | `testing/agentflow-baseline/evidence/T03-design-be.txt`（表头、占位行与核对项计数） | 已覆盖 |
| G2-AC-02 | 同 T03 证据 + `agents/backend-engineer.md` 纪律段 | 已覆盖 |
| G3-AC-01 | `testing/agentflow-baseline/evidence/T04-prototype.txt`（P1–P5 命中） | 已覆盖 |
| G3-AC-02 | 同 T04 证据（document-chain 段） | 已覆盖 |
| G4-AC-01 | `testing/agentflow-baseline/evidence/T05-testing-plan.txt`（三行命中） | 已覆盖 |
| G4-AC-02 | 同 T05 证据（test-planner 段） | 已覆盖 |
| G5-AC-01 | `testing/agentflow-baseline/evidence/T10-frontend-discipline.txt`（五组纪律逐项命中） | 已覆盖 |
| G5-AC-02 | 同 T10 证据（design/fe 表与自检行） | 已覆盖 |
| G5-AC-03 | 同 T10 证据（spec/fe §2.1 六行） | 已覆盖 |
| G5-AC-04 | 同 T10 证据（工程基线请求层与 UI 基线） | 已覆盖 |

覆盖映射中的证据由 `testing/agentflow-baseline/scratch/verify.py` 生成，可复跑；「已覆盖」只说明已有对应证据，不替代独立评审。

## 5. 发布要求与结论

| 判断项 | 通过条件 | 未满足时 |
| --- | --- | --- |
| 核心能力与主链路 | G1-AC-01/02、G2-AC-01/02、G3-AC-01、G4-AC-01 全部通过 | 阻塞 |
| 边界与异常 | §2 六类边界在模板与角色文字中有明确处置 | 阻塞 |
| 文档链与门 | `doc_chain.py` 对本批 PASS；`validate.py all` 全绿；生成树新鲜 | 阻塞 |
| 独立评审 | 需求评审门与技术方案评审门各有一份独立记录 | 阻塞（L0 时按契约登记并承诺补门） |
| 遗留风险 | 模板内容依赖接入方填写，方法仓无法验证填得对不对 | 登记为已知残余，不冒充已验证 |

**结论**：原四项（G1–G4）已由独立评审通过（`reviews/review-2026-10-28-001.md`），本地实现、干净副本与共享树 11/11 PASS。FE 增量（G5）的实现与确定性门已完成（`T10-frontend-discipline.txt`、`T07-validate-all-clean-base.txt`、`T07-validate-all-shared-tree.txt`），但 **FE 增量的独立评审未运行**：用户 2026-10-28 明确拒绝派发子代理，T12 记 ⚠。不得把 G5 写成已批准；恢复条件见计划 T12。
