# agentflows 结构改造方案（评审稿）

- **状态**：已执行（2026-10-09）；四项决策与一个待定项均按默认落地（见第六节）。执行产物：本目录 `migration-mapping.md`、`migration-spec.md`、`batch3-gate-change-spec.md`、`baseline-2026-10-09.md`；版本 0.9.0 记录于 `CHANGELOG.md`；episode 见 `episodes/2026-10-09/EP-20261009-001.json`。
- **日期**：2026-10-09
- **依据**：WorkProject 七个来源的规范与机制调查；`youc-workflow-ai` 及其冻结归档的实测结构；本仓现状逐项核对（见附录）；冻结归档规则的讨论结论。外部调查材料不在本仓保存副本，来源见附录。
- **范围**：本仓的文档与目录结构（第一至三节），以及方法文本的同步修改（3.5）。机制面（`skills/`、`agents/`、`schemas/`、`tools/`、`evals/`、`examples/`、`mock/`、`packaging/`、`tests/` 与四个宿主目录）的**结构与职责不变**；其中涉及记录路径的引用随迁移同步修复，逐项清单以 4.2 为准。
- **编号约定**：汉字序号为章节；「批 0–5」为执行批次；「L1–L3」为冻结级别；`BUG-`/`EP-`/`RL-` 为既有记录编号。

---

## 一、为什么改

### 1.1 三个来源给出一致结论

1. **两次同题调查**（一次覆盖 WorkProject 七个来源，一次针对 Youc 工作区）得出同一判断：真正欠缺的不是更多条文，而是「把已有约定变成机器门禁」的装置——目录校验、勾选一致性、契约冻结测试、「只减不增」白名单等。
2. **`youc-workflow-ai` 是这条文档链方法目前最新一代的落地形态**，且经过真实使用：需求与缺陷双轨（`features/` + `issues/`）、单索引（`index.md`）、模板按实际使用收缩为真文件、历史冻结进 `_archive/`、发布用双文件（`todo.md` + `pending-test.md`）。它的简化值得本仓对齐。
3. **同一个仓库也暴露了四个反面教训**，正好是本仓要补的门：
   - **没有骨架模板**——19 个需求目录格式漂移，出现了约定之外的结构目录；
   - **没有一致性检查**——顶层 `user/` 的 11 条链接长期断链无人发现；
   - **冻结没有先迁走活跃落点**——记录树冻结后，新的评审记录无处落档（一处评审结论未落档）；
   - **清单与实物不一致**——索引写 8 组评审、实际 11 组，计数对不上。

### 1.2 本仓现存问题

| 问题 | 现状 |
| --- | --- |
| 记录树形态冲突 | `records/` 下设 bugs、episodes、improvement、plans、reviews、tests 六个子树；已决定不再保留 `records/` 这一层 |
| 文档没有索引 | `docs/` 顶层文档平铺，另有 `product/` 内部文档链与 `audit-2026-09-18/` 历史目录；历史件与活文档混放，没有「什么时候该动哪份」的入口 |
| 模板是单体文件 | 12 件模板挤在 `skills/agentflow/references/document-chain-templates.md` 一个文件里，不能按件复制、没有清单可供核对（同类问题曾在 `aiwork-workflow-ai` 的模板清单上发生过：清单引用了不存在的模板文件） |
| 两条门没有成文 | ① 评审结论必须落档；② 验收状态不得把「已实现」写成「已验证」 |

### 1.3 已定前提

- 不再保留 `records/`，记录按新结构落位；
- 本仓与方法面统一改为 `youc-workflow-ai` 同族结构；
- 新增结构按家族命名（见 3.3）；
- 缺陷与事项统一为 `ISS-<YYYY>-<NNN>` 单一编号家族；
- 模板放在 `skills/agentflow/templates/`（随插件发布，避免双源）；
- `docs/` 保留现名，范围收窄为「设计·指南·事实」三类（见 3.4）；
- 冻结归档用三级规则（见 3.6），不做定时冻结。

---

## 二、改什么（总览）

| 面 | 改动 |
| --- | --- |
| **本仓目录** | 新增 `index.md`（唯一索引）、`features/`（批次）、`issues/`（缺陷与事项）、`releases/`（发布）、`reviews/`（对外评审落点）、`_archive/`（冻结历史）；`records/` 按 3.2 撤换 |
| **本仓文档** | `README.md` 更新目录职责表；`AGENTS.md` 增两条纪律；`docs/` 保留目录名、补索引登记与归档段 |
| **模板** | 单体文件拆为真文件 + 清单，放在 `skills/agentflow/templates/`；拟增 issue、releases 双文件、index 骨架、README 轻量模式段（见 3.4） |
| **记录落点** | 缺陷进 `issues/`；计划、评审、测试、决策记录、改进三件套跟随批次目录；发布进 `releases/`（见 3.2） |
| **方法文本** | 目录布局默认值、证据记录去向、评审落档条款、验收口径条款、轻量模式、冻结规则（见 3.5、3.6） |
| **不变** | 文档链现有阶段门与质量条款、记录格式的内容定义、角色职责、四宿主打包方式；其引用面随迁移修复（见 4.2） |

---

## 三、前后对比

### 3.1 目录结构：前 → 后

```text
（前）                                   （后）
agentflows/                              agentflows/
├── records/           记录树            ├── index.md        唯一索引（场景→入口 + 维护纪律 + 待迁移清单）
│   ├── bugs/                          ├── features/        批次：feature-<日期>-<主题>/
│   ├── episodes/                      │                    {README.md, proposal/, spec/, design/, plan/, reviews/, testing/, episodes/, improvement/}
│   ├── improvement/                   ├── issues/          缺陷与事项：ISS-<YYYY>-<NNN>-<slug>.md + 归档/ + recurrence/
│   ├── plans/                         ├── releases/        发布记录 + 待验证清单（todo.md、pending-test.md）
│   ├── reviews/                       ├── reviews/         对外评审落点：<项目>-<需求>/
│   └── tests/                         ├── _archive/        冻结历史：<类型>-<年月>/
├── docs/              顶层文档平铺      ├── docs/            保留现名：设计·指南·事实三类（见 3.4）
├── skills/agentflow/                  ├── skills/agentflow/templates/   模板真文件 + 清单
│   └── references/                    ├── skills/ agents/ schemas/ tools/ evals/ examples/ mock/ packaging/ tests/   （结构不变）
│       └── document-chain-templates.md ├── .claude-plugin/ .codex-plugin/ .commandcode/ .zcode-plugin/   （不变）
└── （无索引、无归档、无批次）           └── README.md AGENTS.md CHANGELOG.md protected-paths.txt（前两者有更新）
```

批次目录的内部形态（示例）：

```text
features/feature-2026-10-09-结构改造/
├── README.md           批次入口：元信息 + 推进进度 + 当前步骤
├── proposal/           需求提案
├── spec/{fe,be,qa}/    规格（按角色；ui 轨可选）
├── design/{fe,be,qa}/  技术方案（按角色；ui 轨可选）
├── plan/{fe,be,qa}/    实施计划（按角色）
├── reviews/            批次自身的评审记录
├── testing/            测试计划与运行记录
├── episodes/           决策记录
└── improvement/        改进三件套：候选、评估、对比
```

### 3.2 记录撤换映射

| 现路径 | 新落点 | 说明 |
| --- | --- | --- |
| `records/bugs/<日期>/<slug>.md` | `issues/ISS-<YYYY>-<NNN>-<slug>.md` | 编号统一为 `ISS-<YYYY>-<NNN>`（单一编号家族，含缺陷）；旧 `BUG-` 编号与新编号的对照表由迁移脚本生成，台账、决策记录与校验中的引用同批改指（属批 3 保护清单范围） |
| `records/bugs/archive/<日期>/` | `issues/归档/<日期>/` | 归档规则沿用现有台账约定：仅 `rejected` 类记录移入归档、`verified` 原地保留，不改状态语义、只换目录前缀 |
| `records/bugs/recurrence/` | `issues/recurrence/` | 复发台账职责不变，仍是改进环的输入 |
| `records/plans/PLAN-*.md` | 所属批次的 `plan/` | 计划文件内容格式不变；暂无归属的历史件按冻结规则处理，逐件清单在迁移脚本里 |
| `records/reviews/<组>/` | 对外评审 → `reviews/<项目>-<需求>/`；批次自身评审 → `features/<批次>/reviews/` | 「评审必落档」门保留，只换落点（补上 `youc-workflow-ai` 记录冻结后评审无处落档的洞） |
| `records/tests/` | 批次内 `testing/` | 当前该目录只有说明文件，迁移成本低 |
| `records/episodes/<日期>/` | 批次内 `episodes/`；历史件按冻结规则处理 | 决策记录格式不变，逐件清单在迁移脚本里 |
| `records/improvement/{candidates,evaluations,comparisons}/` | 批次内 `improvement/` | 三件套跟随批次；现有历史件按批次归属或冻结规则处理，逐件清单在迁移脚本里 |
| `records/improvement/releases/` | `releases/` | 发布记录；同时引入待验证清单双文件 |
| `records/` 六份类级 README（bugs、episodes、improvement、plans、reviews、tests） | 并入新结构的对应说明与索引（`issues/README.md`、批次 README、`releases/README.md`、`reviews/README.md` 等） | 其中 `plans/README.md`、`tests/README.md` 被角色文件引为契约，引用随批更新 |
| `records/README.md` | 并入 `index.md` 与 `README.md` 的纪律 | 原文件按冻结规则处理 |

**迁移期引用处置（对既有记录约定的修订）**：记录正文与 `files` 字段里因迁移而失效的路径引用，做**机械改指**（只改路径，不改结论、证据与时间戳），并在索引登记一条迁移说明。这把「append-only」精确化为「结论与证据不改，失效路径可机械改指」。该口径写入 `index.md` 与 `README.md`（批 1），迁移执行随批 4。

### 3.3 命名对比

| 对象 | 现在 | 改造后 |
| --- | --- | --- |
| 索引 | 无 | `index.md`（仓根，唯一索引） |
| 批次 | 无此概念 | `features/feature-<YYYY-MM-DD>-<主题>/` |
| 缺陷与事项 | 缺陷：`records/bugs/<日期>/<kebab-slug>.md`（无事项类） | `issues/ISS-<YYYY>-<NNN>-<slug>.md`（两类统一编号；仅 `rejected` 进 `issues/归档/<日期>/`） |
| 评审 | `records/reviews/<组>/review-<日期>-<NNN>.md` | `reviews/<项目>-<需求>/review-<日期>-<NNN>.md`（批次自身评审在批次内） |
| 测试 | `records/tests/` | `features/<批次>/testing/` |
| 决策记录 | `records/episodes/<日期>/EP-*.json` | `features/<批次>/episodes/` |
| 发布 | `records/improvement/releases/<版本>.json` | `releases/` + `todo.md`、`pending-test.md` 双文件 |
| 归档 | 无 | `_archive/<类型>-<YYYY-MM>/` |
| 模板 | 单体文件里 12 件 | `skills/agentflow/templates/` 真文件 + `templates/README.md` 清单；拟增项见 3.4 |
| 索引纪律 | 无成文 | 文档的新增、移动与删除必须同步维护 `index.md`；不得自动创建顶层目录 |

编号（已定）：缺陷与事项统一为 `ISS-<YYYY>-<NNN>` 单一家族；全量改名与记录格式变更属批 3 保护清单范围。

### 3.4 文档面变化

- **新增 `index.md`**：场景→入口表（改角色去 `agents/`、看方法去 `skills/agentflow/references/`、查记录去 `features/` 与 `issues/`、查评审去 `reviews/`、看发布去 `releases/`、看产品设计去 `docs/product/`、翻历史去 `_archive/`）、维护纪律、待迁移清单。
- **新增 `_archive/`**：首个归档桶（`_archive/` 下按「类型-年月」分目录）。批 1 先建桶骨架；`docs/audit-2026-09-18/` 目录与其跟进件 `docs/audit-2026-09-18-followups.md` **同桶迁入**（保持两者相对布局，避免跟进件指向审计对话记录链接断开）；两件含未决项的文档（跟进件与 `docs/next-session-handoff.md`）先做**未决项出表**（转 `issues/` 或后续批次，索引保留「冻结原文」指针）再入桶，出表之前只做索引登记（L1）。跟进件的入链（根 `README.md`）与交接件的入链（`docs/iteration-log.md`）在迁移同批改指。
- **`AGENTS.md` 增两条纪律**（原文）：
  1. 「文档的新增、移动与删除必须同步维护 `index.md` 的登记；」
  2. 「新增顶层目录或新的文档类型须先经用户确认，不得自动创建。」
- **`README.md` 更新目录职责表**：该表已存在（每个顶层目录一句话职责），按新结构更新条目。
- **`docs/` 保留目录名**：范围收窄为三类——产品设计族（`product/`、`agent-product-boundary`、`host-native-plugin-design`、`self-improvement-design`、`spec-fact-check-design`）、指南与镜像（`system-guide`、`agent-roles`）、事实与日志（`host-platform-facts`、`iteration-log`）；审计目录与会话交接件出表后入归档桶；不再接收其他类别（其余均有专门落点）。
- **模板增补（拟）**：现有 12 件保留；拟增 4 件——① issue 模板（`ISS-<YYYY>-<NNN>` 编号、关闭条件可验证、看板字段）；② releases 双文件骨架（`todo.md`、`pending-test.md`）；③ `index.md` 骨架（场景→入口 + 维护纪律 + 待迁移清单）；④ README 模板补「轻量模式」声明段。

### 3.5 方法面（条文前后）

| 位置 | 现在 | 改造后 |
| --- | --- | --- |
| 目录布局默认值 | `docs/features/feature-<slug>/`（无约定时的默认） | **文档中枢仓**（如 `youc-workflow-ai` 式仓库）：默认改为仓根 `features/`（不再放在 `docs/` 前缀下）的同族形态：`features/` + `issues/` + `releases/` + `templates/` + `_archive/` + `index.md`；批次内部维持标准文档链（proposal、spec/design/plan 按角色分目录）；**普通业务仓**（无文档中枢）的默认仍为仓内 `docs/features/feature-<slug>/`，不因本方案改变 |
| 证据记录去向 | 跟随 `records/` 的契约 | 批次内 {plan, reviews, testing, episodes, improvement} + `issues/` + `releases/` + 对外评审落点 `reviews/` |
| 模板 | 单体文件 12 件 | 真文件 + 清单（「先抄模板」） |
| 评审落档 | 落在 `records/reviews/` | 落点改为 `reviews/` 与批次内 `reviews/`；落档门保留并写成明文条款 |
| 验收口径 | 无成文条款 | 收口条款：发布带待验证清单；「已实现」不得写成「已验证」 |
| 轻量模式 | 无 | 只有入口文档与提案、没有独立规格/方案轨的批次，在入口文档声明即可，机检按声明模式执行 |
| 冻结规则 | 无成文 | 三级规则（见 3.6） |
| 阶段门与质量条款 | Spec 反审、需求评审、技术方案评审、计划前置、方案带契约、链路收口通读 | 不变 |

### 3.6 冻结归档规则（定稿）

**三级**：

- **L1 只登记**：索引里一行（日期 + 说明），文件原地保留；
- **L2 就地冻结**（日常默认）：文件头一行冻结声明（冻结日期、被谁承接、承接位置）+ 索引登记，**不搬家**；
- **L3 整树进 `_archive/<类型>-<年月>/`**：归档桶内放只读声明（命名、写入者、冻结原因）。

**两条判据**（满足其一才冻）：① 读者可能把历史当现行真源；② 有不再生效但需要被解释的约定。两条都不满足 → 不冻，git 本身就是完整历史。

**四步（L3）**：先迁活跃落点 → 未决项出表（转 `issues/` 或批次，索引保留「冻结原文」指针）→ 登记 → 只读化。

**冻结原文的引用**：迁入归档桶的原文保留其历史引用、不改写（与 `CHANGELOG.md` 同款「不改写历史」登记）；迁移期的引用核对把这类命中单独分类，不算未覆盖项。

**反例**：在途件不得冻结；不得按时间冻结；单份文档不搬家式冻结（记录引用会断——本仓校验要求记录正文与 `files` 字段里的引用可解析）。本仓的首次 L3 就是 records 撤换（整树退役）；此后常态按 L1/L2。

---

## 四、怎么改

### 4.1 批次

| 批 | 内容 | 是否触及保护清单 | 验证 |
| --- | --- | --- | --- |
| 0 | 基线：`python3 tools/lab/validate.py all` 输出与当前修订号存档 | 否 | 原样留存 |
| 1 | `index.md`；`docs/` 索引登记与归档段；`_archive/` 建桶（骨架）；`AGENTS.md` 两条纪律；`README.md` 目录职责表更新 | 否 | 新增索引与本次移动涉及文件及其入链的相对链接逐条核对（人工清单，命令与输出留档）+ `validate.py all` |
| 2 | 模板拆真文件 + 清单 + 增补（issue、releases 双文件、index 骨架、README 轻量模式段）；方法文本同步修改（3.5 各行） | 否 | `validate.py all` + `doc_chain.py --self-test` + `packaging/build_runtime.py` 重建预览 |
| 3 | 保护清单逐项改动**产 diff、不落地**（见 4.2）；diff 以补丁文件固定并随评审记录归档 | 是（人工评审） | 逐项 diff + 静态复核；不动树，不留验收失败窗口 |
| 4 | 落地批 3 已评审的同一份 diff，并按映射表移动 + 引用修复（含机械改指与登记）+ 检索索引重建 | 是（随迁移落地） | `validate.py all` + `doc_chain.py --self-test` + 全仓引用扫描未覆盖项归零（口径见 4.4） |
| 5 | 发布收口：版本号 + 五个清单文件 + 打包重建 + `validate.py installed` | 发布门 | 全绿 + 独立评审 + 决策记录落档 |

批 4 不重新生成门更改 diff：落地评审确认的同一份；若落地时确需调整，调整部分重新评审。

### 4.2 需人工评审的保护清单（变更内容）

| 文件 | 为什么需要改 |
| --- | --- |
| `tools/lab/validate.py` | 记录路径校验、期望面清单、交叉引用 |
| `tests/test_lab_contracts.py`、`tests/test_record_store.py` | 钉住校验与检索工具的回归测试 |
| `schemas/`（`bug-record`、`plan`、`recurrence`、`review`、`test-plan`、`test-run` 六件） | 格式描述文本内嵌 `records/` 路径 |
| `agents/evaluator.md`、`agents/release-governor.md` | 角色文本引用 `records/`（含复发台账回写要求） |
| `evals/` | 公开用例引用受影响路径（如 `AF-009`） |

落地方式：保护清单成员的改动由人工评审后落地（对应仓库约定：门变更需人工评审，不由候选改动自我豁免）。批 3 只产 diff；批 4 与迁移同批落地，避免批间出现验收失败窗口。

**非门同步文件**（随批 2 或批 4 更新）：`skills/agentflow/SKILL.md` 与 `references/*`（含 `document-chain.md`、`roles.md`）、`skills/improve/SKILL.md`、`agents/*.md`（14 个角色文件中除上述两件外的 12 件）、`docs/**`（含 `system-guide.md`、`self-improvement-design.md`）、`mock/**`（`mock/records/` 与校验器的编译方式随新树重构）、`examples/**`、`tools/lab/README.md`、`packaging/README.md`、根 `README.md`、`AGENTS.md`（更新时保持计划契约探针通过）、`tools/lab/record_store.py`（未受保护）、`packaging/build_runtime.py`、`CHANGELOG.md`（历史条目不改写；如需要，加一句不改写说明）。判定依据：以全仓 `records/` 引用扫描输出为准（口径见 4.4），未覆盖项在批 4 归零。

### 4.3 迁移机制

一张「旧路径 → 新路径」映射表驱动全部移动；移动用脚本而不是零散手工；引用同批更新（含 3.2 的机械改指与登记，以及 3.4 点名的入链改指）；重建检索索引（`.agentflow-records.sqlite3`）；每批完成后跑验证命令并留存原文输出。

### 4.4 风险与对策

| 风险 | 对策 |
| --- | --- |
| 引用断链 | 映射表驱动 + 全仓引用扫描（口径见下）+ `validate.py all` 全绿才收 |
| 保护面漏改 | 人工评审 diff + 反向核对（以全仓引用扫描输出对照 4.2 清单，未覆盖项归零） |
| 批间验收失败窗口 | 批 3 只产 diff、批 4 原子落地（门更改与迁移同批） |
| 宿主快照漂移 | 发布后跑 `validate.py installed` 并重装 |
| 回滚 | 逐批独立提交，批内可整体回退 |

**扫描口径**（批 4 验收用；按此口径当前实测 54 件）：

```sh
grep -rn "records/" --include='*.md' --include='*.json' --include='*.py' --include='*.yml' . \
  | grep -vE '^(\./)?records/' \
  | grep -vE '^(\./)?packaging/runtime/' \
  | grep -vE '^(\./)?\.commandcode/' \
  | grep -v 'command-code-session-' \
  | grep -v 'structure-overhaul-plan'
```

排除项：`records/`（迁移源）、`packaging/runtime/`（生成物）、`.commandcode/` 与会话 HTML（`.gitignore` 覆盖；是否被自动跳过因环境而异，故显式排除）、本方案文档。路径前缀两种形式（`records/` 与 `./records/`）都已兼容。其余命中逐项对照 4.2 清单；按此口径当前实测 54 个文件命中。迁入归档桶的冻结原文保留历史引用（见 3.6），这类命中单独分类。

本仓目前没有常设的文档链接检查工具；上述扫描为一次性脚本。若要把链接检查变成常设门，属批 3 候选。

---

## 五、影响与不做

- **机制面结构不变**：宿主装载、角色职责、记录格式的内容定义、评测工具链结构不受影响；其中记录路径相关引用随迁移修复（清单以 4.2 为准）。
- **评测口径**：本次属结构与方法文本变更（方法级），发布记录按惯例注明无 instrumented 业务任务（`measurement: none`），不宣称已验证的提升。
- **明确不做**：git 钩子、多仓编排、运行时语义、前端门禁脚本（属被服务仓的素材，不进本仓）；不新建仓；不按时间冻结；单份文档不搬家式冻结。

---

## 六、已定与待定

**已定（2026-10-09）**：

1. **范围**：本仓与方法面都做；
2. **编号**：缺陷与事项统一为 `ISS-<YYYY>-<NNN>` 单一编号家族（全量改名与格式变更属批 3）；
3. **模板放置**：随插件发布放在 `skills/agentflow/templates/`；
4. **`docs/`**：保留现名，范围收窄为「设计·指南·事实」三类（见 3.4）。

**已处理（原待定）**：

5. **历史记录路径改指**：**已按默认执行**——活跃记录机械改指（结论/证据/时间戳不改，清单见 `migration-mapping.md` 表 3），冻结原文保留历史引用（`_archive/` 单点豁免）。

---

## 附录：证据与核对

- **本仓内核对件**：`protected-paths.txt`、`records/`（含六份类级 README 与台账规则）、`docs/`、`skills/agentflow/`、`skills/improve/`、`tools/lab/validate.py`、`tools/lab/doc_chain.py`、`tools/lab/README.md`、`mock/`、`examples/`、`packaging/README.md`、根 `README.md` 与 `AGENTS.md`。
- **本仓外背景材料**（不随本仓归档，仅作来源说明）：WorkProject 七个来源——`ts/fe/total-security/agents/spec`、`ts/fe`、`aiwork/fe`、`ts/be`、`aiwork/be`、`ts/ts-workflow-ai`、`aiwork/aiwork-workflow-ai`；Youc 工作区的 `youc-workflow-ai`（含 `index.md`、`README.md`、`_archive/records-2026-10/`、`features/feature-2026-09-22-文档与结构治理/`）。如拍板需要，可将其中关键证据另行归档进本仓。
