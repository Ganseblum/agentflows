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

- **G1-AC-01**：两个 2026-10-28 批次各有至少一份独立评审记录落在各自 `reviews/` 下，
  且记录含 `review_tier: L1`（或能力更强时 `L2`）、`reviewed_revision`、`decision` 三个字段。
  判据：对 `reviews/` 逐个文件读取 frontmatter，断言三字段存在且 `review_tier` 不为 `L0`。
- **G1-AC-02**：两份评审记录的 `decision` 为 `changes_requested` 时，其 findings 全部能在
  `docs/issues/` 找到对应 `ISS-*` 记录（或记录正文逐条列出「已就地修复」并给 fix_revision）。
  判据：交叉校验 findings 与 `docs/issues/` 的存在性，缺失即红。
- **G2-AC-01**：「当前欠几次独立评审」可由一条命令输出，输出行数等于欠账清单里 `状态=未清偿` 的行数。
  判据：命令输出与清单计数逐行比对。
- **G2-AC-02**：`review_tier: L0` 且 `dispatch_errors` 为空的评审记录被判红（伪降级）。
  判据：构造一份伪降级夹具，断言校验器拒绝它；再构造一份带 `dispatch_errors` 的 L0 记录，断言通过。
- **G3-AC-01**：五条 `fixed-pending-review` 记录（ISS-2026-057/058/060/061/066）逐条有结论：
  转 `verified`（带 `reviewer` + `review_decision: approved` + `regression_status: pass`）或退回 `open`
  并写明缺什么。判据：逐条读 frontmatter，断言状态与所需字段齐备。
- **G3-AC-02**：四条缺 `fix_revision` 的记录补齐 `fix_revision`（可解析的提交号或版本）
  或显式写 `N/A: 理由`。判据：逐条断言字段存在且非空。

## 2. M-B `review_tier` 伪降级的记录侧校验（G2 的实现形态）

**契约**：不给文档链 linter 新增 C 检查号。伪降级的判断对象是**评审记录**，因此判据落在
记录侧，分两层：

| 层 | 落点 | 内容 |
| --- | --- | --- |
| schema 层 | `schemas/review.schema.json` | 新增可选字段 `review_tier`（枚举 L0/L1/L2）与 `dispatch_errors`（字符串数组）；`allOf` 加一条：`review_tier` 为 `L0` 时 `dispatch_errors` 必须非空且每项非空字符串 |
| 校验器层 | `tools/lab/gate/records.py`（或评审记录校验入口） | 对缺 `review_tier` 的记录不判红（存量记录兼容），对 `review_tier: L0` 且 `dispatch_errors` 缺失/为空判红 |

- **M-B-01**：`review_tier` 缺省时不得推定已过独立评审——校验器对它只做「未声明」标注，不判红也不判绿。
- **M-B-02**：schema 的 `additionalProperties: false` 意味着新增字段必须同时写进 schema，
  否则既存记录一旦带上该字段即被拒；该约束决定了 T04 必须是一处改动、同时改 schema 与校验器。

**为什么不是新增 C 判据**：C 判据扫的是文档链文本（`docs/features/` 下的 `.md`），而欠账的真身在
`reviews/` 与 `docs/issues/` 的 frontmatter 里。把记录侧规则写进文本 linter，会造成「判据在 A 处、
对象在 B 处」的第二套口径——这正是 ISS-2026-061 记录的失败形态。

## 3. M-C 五条待评审缺陷的清偿路径（G3）

| 缺陷 | 当前状态 | 清偿动作 | 关闭条件 |
| --- | --- | --- | --- |
| ISS-2026-057 | `fixed-pending-review`，缺 `fix_revision` | 独立评审复核修复是否成立；成立则补 `fix_revision` + `reviewer` + `review_decision`，转 `verified` | frontmatter 五字段齐备 |
| ISS-2026-058 | 同上 | 同上 | 同上 |
| ISS-2026-060 | 同上 | 同上 | 同上 |
| ISS-2026-061 | 同上 | 该条原文本就写着「待独立评审第二轮复跑」，直接走第二轮 | 同上 |
| ISS-2026-066 | `fixed-pending-review`，`fix_revision` 过期表述 | 评审确认四处不同步是否已消除；`fix_revision` 改写为已并入的提交号 | frontmatter 五字段齐备且 `fix_revision` 可解析 |

- **M-C-01**：任一条经评审判定「修复不成立」时，退回 `open` 并在正文 `## 修复` 节追加一节
  「## 复核结论（2026-10-28）」写明缺什么，**不得**为了清账而推成 `verified`。

## 4. 影响面

| 改动 | 影响面 | 说明 |
| --- | --- | --- |
| `review.schema.json` 新增两字段 + 一条 `allOf` | 全部评审记录的校验；`reviews/` 既有记录 | 新增字段可选，存量记录不合规风险为零；但 `additionalProperties: false` 使「加字段」与「用字段」必须同批 |
| 记录校验器判据 | `validate.py artifacts` 与相关单测 | 属受保护面（`tools/lab/gate/`、`schemas/`） |
| 五条 ISS 的 frontmatter | 缺陷记录面与 `validate.py artifacts` | 状态机迁移须字段齐备，否则门红 |
| 两个批次的 `reviews/` | 批次内文档链材料 | 按 `reviews/README.md` 的「校验范围」条，批次内记录不受评审契约四项校验 |

## 5. 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评审欠账清偿"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

四项全绿才算可接受。`validate.py all` 中 `installed` 项在未重装宿主时会红——本批不改角色面，
不得因此重装；该项按既有口径单独判断，不并入本批验收结论。
