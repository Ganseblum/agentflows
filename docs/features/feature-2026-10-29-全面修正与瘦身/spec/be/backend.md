# 规格：全面修正与瘦身批（后端与门判据轨）

## 0. Proposal 反审 checklist

对照 `proposal/proposal.md` 逐节挑缺口。阻塞项 = 会导致判据无法判定或实现范围不明确的缺口。

| 提案节 | 挑到的缺口 | 是否阻塞 | 处置 |
| --- | --- | --- | --- |
| §0 文档信息 | 六项发现的实测数字未指明复核命令的完整形态，评审无法复跑 | 否 | 本文件 §1 各模块「标尺」列逐条给出可照抄命令 |
| §1.1 现状 3 | 「删不动」的两种后果（链接判红 / 证据列判红）未区分由哪个判据抓 | 是 | 已在 §1 M-F 写明两条判据分别归属 `validate.py docs` 与 C23，并各配一条会失败的检查 |
| §1.1 现状 4 | episode 与 records 的字段名口径未列全，判据会漏字段或误伤正文 | 是 | 已在 §1 M-C 给出字段白名单与豁免形态；正文散文不在判据范围内，理由随行 |
| §1.2 G5 | 「≤450 行」未说明四文件清单是否与 2026-10-25 批 T24 同一套 | 是 | 已在 §1 M-E 固定四文件路径清单，并写明与 T24 的差值（663 vs 587）来源 |
| §1.3 约束四 | 「现行导航面」与「已闭合记录」的边界用例未列举 | 否 | 已在 §1 M-F 用一张判定表给出四类载体归属 |
| §1.4 不做 | 「删档需与引用改写一并规划」未说明本批是否留下可执行的删档规则 | 是 | 已在 §1 M-F 增加一条行为：引用改写口径由本批做成判据，删档本身另批执行 |
| §4 台账 Q-06 | 角色合并裁决的复跑口径未定（三条件的阈值） | 否（本批不做该裁决） | 保持未确认并登记，随 T13 一并处理；不阻塞其余任务 |
| §3 埋点 | 埋点 N/A 需三处一致声明 | 否 | proposal / 本文件 / `design/qa/testing.md` 三处均写 N/A 及理由 |

**反审结论**：阻塞项 5 条已全部在本文件对应模块的口径里关闭，无遗留 ☐。

## 1. 行为条目

条目索引：M-A 议程归并 · M-B 待决项归口 · M-C 记录引用可复核性 · M-D 评审档位执法 ·
M-E 必读面收敛 · M-F 噪声退场与引用改写。

### M-A 议程归并

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-A-01 | 本批实际吸收的项在本批计划里各有唯一任务号 | 以 `design/qa/testing.md` §2.1 的吸收映射表为准：表内每一条在本批计划任务表中出现且仅出现一次；表外的旧批任务留在原批，不要求进本表，也不得声称已吸收 | `python3.12 tools/lab/validate.py doc_chain` 绿 + 人工按 §2.1 映射表逐行核 |
| M-A-02 | 旧批次不保留第二套「谁还没做」的说法 | 三批各自 README 的推进进度节末尾指向本批计划；`docs/features/README.md` 在途表、`index.md` 批次索引节、`docs/releases/todo.md` 批次索引三处对该批的状态与本批 README 一致 | `python3.12 tools/lab/validate.py all` 绿；`grep -c "已并入本批\|未完成任务并入" 三批 README` 各 ≥1 |
| M-A-03 | 归并后不产生新的顶层记录类型 | 只新增一个批次目录，位于既有 `docs/features/feature-<date>-<topic>/` 形态下 | `python3.12 tools/lab/doc_chain.py <本批目录>` PASS 即证 |

### M-B 待决项归口

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-B-01 | 拍板口收录本批全部散落未决项 | 10-25 批 Q-01…Q-05、GOV 批 3 条实施前确认项在本批 `docs/PENDING-DECISIONS.md` 各有条目或在提案 §4 台账内已按授权关闭并记日期；仍开放的每一条都能在拍板口检索到编号 | 可计数检索脚本（非裸 `grep`）：对每条未关闭未决项，拍板口命中其编号或本批提案 §4 台账命中「已关闭（日期」二者必居其一 |
| M-B-02 | 链内台账与拍板口的分工有明文 | `AGENTS.md` 的决策记录节与 `skills/agentflow/references/document-chain.md` 的 spec 节各有一行写明：链内 `spec/checklist.md` 承载需求侧待决行的运行时台账，凡属主为用户且未关闭的行必须携带 `docs/PENDING-DECISIONS.md` 的条目编号 | 两文件各命中该行原文；`validate.py docs` 与 `decision_gate` 绿 |
| M-B-03 | 「未关闭待决行必须带拍板口编号」进门 | 批次 README 打 `agentflow 决策归属` 标记后，其计划 `### 未决项` 与 `spec/checklist.md` 中带「阻塞」且状态未关闭、属主为用户的行，若不含拍板口编号则判红；未打标的存量批次不触发 | `python3.12 tools/lab/doc_chain.py --self-test` 的正负例夹具各 1 条通过；对本批目录实跑 PASS |

### M-C 记录引用可复核性

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-C-01 | 记录的路径字段必须指向真实对象 | episode JSON 的 `evidence_ref` / `ref` / `path` / `artifact` 字段值中形如 `<顶层目录>/...` 的仓内路径（**一个值里并列多条路径时逐条判**），指向不在盘上的对象即判红；`check` 字段不吃——它承载的是「当年跑过什么命令」的引文，不是指针（2026-10-29 评审 P2-1 定的取舍，spec 与 design 统一按此口径） | 新增回归用例：造一条指向 `docs/does-not-exist.md` 的记录 → 判红（finding 带字段名）；改写成两种豁免形态 → 判绿 |
| M-C-02 | 已消失对象有两种诚实写法 | `仓库@修订:路径`（git 可解析该修订）与 `N/A: 理由` 两种形态均放行；`N/A` 必须紧跟理由文本，裸 `N/A` 放行视为缺陷 | 同上夹具：`N/A` 无理由 → 判红；`N/A: 随 2026-10-12 装置裁撤删除，出处见 CHANGELOG 同日节` → 判绿 |
| M-C-03 | 判据只作用于字段值，不作用于散文 | episode 的 `signals`/`claims` 叙述文本、issue 正文里的历史引文不因指向退役路径判红；仅字段级路径值受校验 | 夹具：同一退役路径出现在正文与字段中，只有字段那条产生 finding（finding 数 = 1） |
| M-C-04 | 现存记录的失效引用逐条如实改写 | 本批完成后，全仓扫描「字段级路径指向不在盘上」的命中数为 0；确属历史现场的写 `N/A: 理由 + 出处`，不得口头宣称已修 | 改写前后各跑一次同一脚本，两个计数都要落进计划证据列 |

### M-D 评审档位执法

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-D-01 | `review_tier` 与 `dispatch_errors` 进入评审记录契约 | `schemas/review.schema.json` 声明两字段（枚举 L0/L1/L2、字符串数组），且 `additionalProperties: false` 保持 | `python3.12 tools/lab/validate.py schemas` 绿；生成树逐字节同步（`manifests` 绿） |
| M-D-02 | 伪降级判红 | 记录声明 `review_tier: L0` 而 `dispatch_errors` 缺失或为空数组 → 一条 finding 指向该记录；L0 且该字段非空 → 通过；L1/L2 → 通过；字段缺席 → 标注「未声明」，不红不绿 | `tests/test_gate_records.py` 四例（含缺席不判红）实跑通过；`validate.py all` 绿 |
| M-D-03 | 本批自身的评审门按实测档位落字段 | 评审记录含 `review_tier` 与其档位的实测依据（派发调用的原始返回留档）；不预设档位 | 记录文件存在且 `python3.12 tools/lab/validate.py artifacts` 绿 |

### M-E 必读面收敛

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-E-01 | 四文件的同一规则不再有第二份副本（2026-10-29 拍板 C：不设总量上限） | `skills/agentflow/SKILL.md`、`skills/agentflow/references/roles.md`、`skills/agentflow/references/contracts.md`、`agents/reviewer.md` 中，同一规则只在一个权威载体出现，其余位置只留指针；`wc -l` 只作观测值记录，不作判据 | `carrier-map.md` 的副本处置列逐行核对；`wc -l` 输出落证据列 |
| M-E-02 | 同步义务退场 | 上述文件与 `skills/agentflow/templates/host/global-rules.md` 中不再出现「改一处就改另一处」及其等价表述；改为指向唯一权威载体 | 可计数检索：命中数 0（判据先打印命中原文再判） |
| M-E-03 | 每条跨载体规则有唯一权威载体 | 载体归属表落在 `skills/agentflow/references/carrier-map.md`，由并入既有 `validate.py docs` 项的 `validate_carrier_map` （`tools/lab/gate/docs.py`）逐行断言：权威路径存在、锚点在该文件内命中、`agentflow:<role>` 指针可解析、副本处置列非空 | `python3.12 tools/lab/validate.py docs` 绿，且 `tools/lab/gate/docs.py` 的 `validate_carrier_map` 逐行打印命中 |
| M-E-04 | 收敛不等于删判据 | 链契约的判据细则可拆到独立文件，但 `AGENTS.md` 引用的每个 `schemas/*.schema.json` 路径仍真实存在、每个 `agentflow:<role>` 仍可解析（既有 `validate.py docs` 断言） | `validate.py docs` 与 `decision_gate` 绿；文档链门对本批全绿 |

### M-F 噪声退场与引用改写

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-F-01 | L3 批原始证据件删除 | `docs/features/feature-2026-10-26-L3工作流增强/testing/**/evidence/` 下的原始 stdout/stderr/txt/json/diff 件删除，仅保留该目录的 `README.md` 说明与指向改写后的记录 | 删除前后 `find … -type f \| wc -l` 计数落进证据列；批次正文目录未被触碰 |
| M-F-02 | 对被删对象的引用不留悬空 | 指向被删路径的字段与链接同批改写为 `N/A: 理由 + 出处` 或 `仓库@修订:路径`；改后全仓「字段级路径不在盘」计数为 0（与 M-C-04 同一条判据） | 同 M-C-04 脚本；`validate.py docs` 与 `doc_chain_live` 绿 |
| M-F-03 | 重复导航面退场 | `index.md` 的「L3 合并后修正」整节、`docs/PENDING-DECISIONS.md` 尾部已移出条目的历史注记删除；`reviews/` 内部重复快照去重（外部逐字快照保留） | 删除前后行数与文件数落证据列；`index.md` 相对链接全部可解析 |
| M-F-04 | 现行导航面无手写计数 | `docs/releases/pending-test.md`、`docs/releases/todo.md`、`docs/host-platform-facts.md` 中会过期的 self-test / unittest 计数字面量改为「以实跑为准」的口径引用；已闭合记录里的历史计数保留为引文 | 三文件逐个计数字面量的**同行无时点括注**命中 0（允许保留数字，但必须与「当日时点值 / 以实跑为准」同行共存）；判定表见本模块下方 |
| M-F-05 | 任务状态字形映射单源 | `TASK_STATUS` 字形→中文词映射在 `tools/lab/` 下只有一份定义，其余位置导入它；两处拷贝并存的形态消失 | `python3.12 tools/lab/validate.py tests` 绿；`validate.py all` 绿 |

**M-F-04 的载体归属判定表**（哪些数字算引文、哪些算现行事实）：

| 载体 | 处置 | 理由 |
| --- | --- | --- |
| `CHANGELOG.md` 历史条目 | 保留原样 | 明文口径：历史条目按原样保留 |
| `docs/issues/**` 与批次 `reviews/` 内的当时输出 | 保留原样 | 是记录当时状态的引文，改了就是篡改证据 |
| `index.md`、`docs/features/README.md`、`docs/releases/*`、`docs/host-platform-facts.md` | 改写为实跑口径 | 这些面陈述的是「现在」，数字一过期就误导下一次会话 |
| 本批计划证据列 | 写实测数字 + 日期 | 证据列要求可复核，当日数字必须可复跑 |

### M-G 已拍板存量决策落地（2026-10-29 并入）

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| M-G-01 | 改进环整体裁撤（#10 B） | `skills/improve/` 与四个治理角色（feedback-analyst / candidate-engineer / evaluator / release-governor）不再存在；candidate / release-record 两份 schema 删除；episode 契约迁至 `schemas/episode.schema.json`；manifest、保护清单、gate 必需条目、测试、活文档与产品链同步 | `python3.12 tools/lab/validate.py all` 绿；`test ! -e skills/improve`；活文档检索退役路径命中 0 |
| M-G-02 | `credentials` 字段加凭据形态 pattern（#12 C） | `schemas/test-plan.schema.json` 与 `schemas/test-run.schema.json` 的 `credentials` 字段拒绝 `sk-` / `ghp_` / `Bearer ` / `token=` 等明显凭据形状，正常注入方式仍通过；仅覆盖该字段，不做全正文扫描 | `tests/test_gate_schema.py` 的正反例实跑通过；`validate.py schemas` 绿 |
| M-G-03 | C17 补 1–2 个变异项（#13 A） | `tools/lab/mutate.py` 的 `ITEMS` / `MUTATIONS` 纳入 `doc_chain.C17`，正反夹具覆盖「核验后修改」与「核验前修改」两态；变异实跑全部被杀死 | `python3.12 tools/lab/mutate.py --check doc_chain_selftest` 输出 0 存活 0 无效；`doc_chain.py --self-test` 全过 |
| M-G-04 | 委派契约补「定位即预算」（#14 A） | `skills/agentflow/references/contracts.md` 的 `read_scope` 一节写明定位质量与读取上限口径：`path:line` 或可复核 Grep 模式、大文件片段交付、定位不足先索取；`packaging/runtime` 与源面逐字节一致 | `grep -n "定位即预算"` 命中；`validate.py manifests` 绿 |
| M-G-05 | 同题对照实验（#16 A） | 选一个小型真实任务，with / without Agentflow 各跑一遍，记录执行方式、墙钟时间、门次数、返工轮次与正确性；报告写明代理指标与人时口径的差别，不把代理指标写成已验证的人效收益 | 报告落 `docs/evaluations/`，含协议、原始数字与限制；独立评审复核 |
