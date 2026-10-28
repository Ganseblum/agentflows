# 规格：评审欠账清偿批

## 0. Proposal 反审 checklist

| 不合规项 | 结论 | 处置 |
| --- | --- | --- |
| 是否把「清偿」当成可以自审完成 | 合规 | §1.3 约束一明写「不得用主审自审冒充清偿」；T01 以委派探测为完成判据 |
| 是否动了未授权范围 | 合规 | 不做事项表逐条给理由；受保护面动作单列为 T04 并标「需授权」 |
| 是否与既有拍板冲突 | 合规 | §3 明写第 10–16 条均不处理，不以本批结论替代拍板 |
| 是否声称了未验证的疗效 | 合规 | 全批 `measurement: none`；欠账数量来自 `grep`/`ls` 实测，逐条可复跑 |
| 是否新增判据号扩表达面 | 合规 | §2 明写 G2 落在记录 schema 的既有字段与条件上，不新增 C 检查号 |

无未关闭阻塞项。

## 1. M-A 欠账清单的字段级口径（G1 的基础）

「评审欠账」在本批有唯一定义，判据脚本与人工清点都按它算：

| 字段 | 含义 | 取值来源 | 缺失时的判定 |
| --- | --- | --- | --- |
| `欠账编号` | 唯一编号，形如 `DEBT-001` | 表内自增 | 缺失即该行无效 |
| `来源批次` | 欠账所属批次目录路径 | `docs/features/<批次>/` | 路径不在盘即无效 |
| `欠账类型` | L0 自审未补 / 伪降级 / 待评审缺陷 | 固定三值 | 其它取值即无效 |
| `被评审 revision` | 应当接受评审的确切提交 | 40 位或不短于 7 位的提交号，须 `git cat-file` 可解 | 不可解即「无法绑定的欠账」，须写明原因 |
| `清偿条件` | 关闭该欠账所需的最小动作 | 一句话，须可判定 | 空或不可判定即无效 |
| `状态` | 未清偿 / 已清偿 | 二值 | 其它取值即无效 |

### 1.2 判据

- **G1-AC-01**：两个 2026-10-28 批次各有至少一份独立评审记录落在各自 `reviews/` 下。
  判据用**记录契约已有的字段名**（`schemas/review.schema.json` 的 `source_revision`，不是
  `reviewed_revision`——后者只存在于 reviewer 结果信封 `contracts.md:132`，不是记录字段）：
  `review_tier ∈ {L1, L2}` 且 `source_revision` 非空且 `git cat-file -e <值>^{commit}` 退出 0
  且 `decision ∈ {approved, changes_requested, blocked}`。
- **G1-AC-02**：评审记录的 `decision` 为 `changes_requested` 时，其 `findings` 里每个 `ISS-*`
  都必须在 `docs/issues/` 存在。**不设「正文写已就地修复」的旁路**——`reviews/README.md:59-61`
  要求「发现的问题一条一条写进 issues/」，`schemas/review.schema.json:40-45` 也把 findings 定义为
  必须存在于 `docs/issues/` 的 bug_id。判据：`findings ⊆ {docs/issues/ISS-*.md 的 bug_id}`。
- **G2-AC-01**：清点命令的输出必须与**从仓内事实派生的欠账数**一致，而不是与它自己读取的手工表一致
  （后者是自指判据：表里漏行时命令输出 0 行、表也 0 行，仍判绿）。派生口径三条，缺一即判红：
  ①批次 README/计划声明 L0 且 `reviews/` 无记录；②`status: fixed-pending-review` 且无 `reviewer` 的
  `docs/issues/` 记录；③欠账清单里 `状态=未清偿` 的行。判据：`命令输出行数 == ①+②的并集大小`，
  且 `清单未清偿行 ⊆ ①∪②`（清单里写已清偿但 ①∪② 仍计入 ⇒ 红）。
- **G2-AC-02**：伪降级被判红，**且覆盖两处载体**——(a) 评审记录：`review_tier: L0` 且
  `dispatch_errors` 缺失/为空 ⇒ 校验器红；(b) 批次文档：README/计划声明 L0 且对应 `reviews/`
  为空 ⇒ 计入 G2-AC-01 的「未清偿」派生集合，不得被标成已清偿。判据：(a) 两个反向夹具各跑一次断言
  退出码；(b) 拿现存两批实测，断言派生集合恰好含这两条。
- **G3-AC-01**：五条 `fixed-pending-review` 记录（ISS-2026-057/058/060/061/066）逐条有结论：
  转 `verified`（frontmatter 需 `reviewer` + `review_decision: approved` + `regression_status: pass`
  + `closure_criteria`，**且正文含 `## 审查` 节**——`tools/lab/gate/records.py:317` 对 verified
  记录强制该标题）或退回 `open` 并写明缺什么。
  判据：逐条读 frontmatter + 断言正文 `## 审查` 存在（转 verified 的条目）。
- **G3-AC-02**：`fix_revision` 的值域**只有一种合法形态**：可被 `git cat-file -e <值>^{commit}`
  解析的提交号。仓内无版本 tag（`git tag` 只有一个历史 tag `workbuddy-merge-2026-10-18`），
  版本号（如 `0.20.0`）不是 git 对象，不能作为 `fix_revision` 的值。
  记录若保持 `fixed-pending-review` / `verified`，`fix_revision` 必填且必须是提交号；
  记录退回 `open` 时该字段按模板可缺省，若保留则写 `N/A: 复核不成立，修复未落地`（open 状态下
  该字段无「修复已落地」的语义）。判据：逐条 `git cat-file -e <值>^{commit}` 断言退出 0，或状态为
  `open` 且值为 `N/A: ` 前缀。

## 2. M-B `review_tier` 伪降级的校验（G2 的实现形态）

**契约：判据必须覆盖契约点名的载体，而不只是最容易落 schema 的那一处。**
`contracts.md:42-43` 说的是「**决策记录或 episode** 里没有 `review_tier` 字段时，视为未声明」，
并给出伪降级判据。实测这条契约当前无处落地：

| 契约点名的载体 | 现状 | 后果 |
| --- | --- | --- |
| episode | `skills/improve/references/episode.schema.json` 为 `additionalProperties: false`，属性表无 `review_tier` | 写进去即被拒 |
| 决策记录 | 无 schema；`docs/PENDING-DECISIONS.md` 是被 `decision_gate`（C16）校验的台账，八列里没有该字段 | 写进去无人校验 |
| 批次 README / 计划（**两批 L0 声明的真实所在**） | 不受任何记录契约校验 | 伪降级真实发生的地方，恰恰零校验 |

因此 M-B 分两层，且**明确声明覆盖范围与不覆盖的部分**：

| 层 | 落点 | 覆盖什么 | 不覆盖什么 |
| --- | --- | --- | --- |
| 记录层 | `schemas/review.schema.json` + `tools/lab/gate/records.py` | 根 `reviews/` 下的评审记录：`review_tier` 与 `dispatch_errors` 的一致性 | 批次内 `docs/features/<批次>/reviews/`（按 `reviews/README.md:13-18`，该目录 2026-10-19 已决定不纳入契约校验，改变它需另立门变更决策——本批不改变该决定，登记为 Q-03） |
| 欠账层 | 清点命令（M-A 清单为派生视图） | 批次 README/计划声明 L0 而 `reviews/` 为空 ⇒ 计入「未清偿」 | 不在文档链新增 C 判据号 |

- **M-B-01**：`review_tier` 缺省时不得推定已过独立评审——校验器对它只做「未声明」标注，不判红也不判绿。
- **M-B-02**：schema 的 `additionalProperties: false` 意味着新增字段必须同时写进 schema，
  否则既存记录一旦带上该字段即被拒；该约束决定了 T04 必须是一处改动、同时改 schema 与校验器。
- **M-B-03**：`episode.schema.json` 与决策记录两处载体是否补 `review_tier` 字段，**本批不做**。
  理由是它们同属受保护面或需新的决策记录契约，而本批的真实欠账出现在批次 README/计划层；
  把它们并入只会扩大门变更面。该缺口登记为 Q-03，留给用户在「补载体 / 改契约措辞指向新载体」之间选。

**为什么不是新增 C 判据**：C 判据扫的是文档链文本（`docs/features/` 下的 `.md`），而欠账的真身在
`reviews/`、`docs/issues/` 的 frontmatter 与批次 README/计划的声明里。把记录侧规则写进文本 linter，
会造成「判据在 A 处、对象在 B 处」的第二套口径——这正是 ISS-2026-061 记录的失败形态。
批次 README/计划层的覆盖走 M-A 的派生清单（G2-AC-01 的 ①），不新增判据号。

## 3. M-C 五条待评审缺陷的清偿路径（G3）

| 缺陷 | 当前状态 | 清偿动作 | 关闭条件 |
| --- | --- | --- | --- |
| ISS-2026-057 | `fixed-pending-review`，缺 `fix_revision` | 独立评审复核修复是否成立；成立则补 `fix_revision` + `reviewer` + `review_decision` + `closure_criteria`，转 `verified` | `reviewer`、`review_decision: approved`、`regression_status: pass`、`closure_criteria`、`fix_revision`（提交号）五字段齐备 + 正文含 `## 审查` |
| ISS-2026-058 | 同上 | 同上 | 同上 |
| ISS-2026-060 | 同上 | 同上 | 同上 |
| ISS-2026-061 | 同上 | 该条原文本就写着「待独立评审第二轮复跑」，直接走第二轮 | 同上 |
| ISS-2026-066 | `fixed-pending-review`，`fix_revision` 为过期的版本表述 | 评审确认四处不同步是否已消除；`fix_revision` 改写为 `26988a4` 这类可解析的提交号 | 同上，且 `fix_revision` 能被 `git cat-file -e <值>^{commit}` 解析 |

- **M-C-01**：任一条经评审判定「修复不成立」时，退回 `open` 并在正文 `## 修复` 节追加一节
  「## 复核结论（2026-10-28）」写明缺什么，**不得**为了清账而推成 `verified`。
  退回 `open` 的记录不要求 `fix_revision`（该字段的语义是「修复已落地」）。

## 4. 影响面

| 改动 | 影响面 | 说明 |
| --- | --- | --- |
| `review.schema.json` 新增两字段 + 一条 `allOf` | 全部评审记录的校验；`reviews/` 既有记录 | 新增字段可选，存量记录不合规风险为零；但 `additionalProperties: false` 使「加字段」与「用字段」必须同批 |
| **`packaging/runtime/schemas/review.schema.json` 重建** | 安装面快照 | `schemas` 在 `build_runtime.RUNTIME_DIRECTORIES` 内，`validate_runtime_freshness` 逐字节比对源与快照；只改源不重建 ⇒ `validate.py manifests` 红（2026-10-28 实测原文：`packaging/runtime/schemas/review.schema.json: content differs from source`）。T04 必须含 `python3 packaging/build_runtime.py` |
| 记录校验器判据 | `validate.py artifacts` 与相关单测 | 属受保护面（`tools/lab/gate/`、`schemas/`）；新增单测须同批登记进 `validate.py` 的 `EXPECTED_TEST_FILES` 与 `protected-paths.txt` |
| 五条 ISS 的 frontmatter | 缺陷记录面与 `validate.py artifacts` | 状态机迁移须字段齐备，否则门红 |
| 两个批次的 `reviews/` | 批次内文档链材料 | 按 `reviews/README.md` 的「校验范围」条，批次内记录不受评审契约四项校验 |
| `docs/releases/todo.md` 的欠账清单节 | 发布待办索引（人读） | 清单是**派生视图**（来源见 G2-AC-01 ①②），不是手工真源 |

## 5. 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评审欠账清偿"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

四项全绿才算可接受。**注意 `installed` 不在这四项之内**：`validate.py --list` 实测输出 11 项，
逐项为 schemas / examples / artifacts / protected / manifests / docs / tests / doc_chain /
doc_chain_live / decision_gate / lint，`installed` 是独立 target（`tools/lab/validate.py:403-408`），
`all` 不运行它。本批不改角色面，不重装宿主；若需核对安装面，单独跑
`python3.12 tools/lab/validate.py installed` 并把结果与批次的验收结论分开记。
