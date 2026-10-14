# reviews — 对外评审落点（外部文档二次评审桥）

这里存放 agentflow 作为**独立评审层**对其他系统产出文档的二次评审记录。典型场景：方案/
计划/规格在业务仓（如 `aiwork-workflow-ai`，走它自己的 rule/agent/template 生成），再用
agentflow 的 reviewer 契约做第二道评审，评审记录与证据回收到本仓。

## 落档要求

- **评审必落档**：评审结论必须落在本目录（或批次内 `reviews/`）的记录文件里，只写进
  计划正文不算数。
- 批次自身的评审记录放 `docs/features/<批次>/reviews/`；本目录用于评审外部仓库文档等跨项目
  轮次。
- **迁移说明**：历史评审记录（原记录树的 reviews 子树）已随 2026-10 结构改造迁移执行
  批次迁入本目录。

## 目录布局（锚是 feature，不是日期）

目录锚定被评审的特性：`reviews/<项目>-<需求>/`，每轮一份 `review-<日期>-<NNN>.md`；
需要不可变快照时，按轮存 `archive/<日期>-<NNN>/` 子目录。同一 feature 可能被反复
评审——今天一轮、明天一轮、修完再一轮——所以**目录挂在 feature 上，轮次是文件**：

```text
reviews/
  aiwork-2026-09-04-对话分享/          # <target_project>-<feature-slug>，一个 feature 一个目录
    review-2026-09-16-001.md           # 一轮评审一个文件：review-<日期>-<NNN>.md
    review-2026-09-17-002.md           # 明天再评同一 feature = 追加一轮（review_id REV-20260917-002）
    archive/
      2026-09-16-001/                  # 每轮自己的快照目录（日期+序号），同名文档跨轮不冲突
        design-be.md
      2026-09-17-002/
        design-be.md
        plan-fe.md
  README.md
```

- 再评审（re-review）聚焦自上一轮以来的 delta，`review.md` 正文可引用上轮 `review_id`；
- 每轮的快照进 `archive/<该轮日期>-<序号>/`——评审针对的是快照而非业务仓当前文件，
  业务仓后续演变不追溯改变评审对象；
- 校验器强制：文件名 = `review_id`（REV-YYYYMMDD-NNN，日期与文件名一致）、目录名形如
  `<project>-<feature-slug>`、`reviewed_docs` 列出的快照必须在盘。

## 工作流

```text
业务仓（产出层：按它自己的 rule/template 生成文档）
   │  挑选要评审的文档 + 记录业务仓当前 commit
   ▼
agentflow（评审层）
   1. supervisor 定位/新建 reviews/<project>-<feature>/，本轮快照进
      archive/<日期>-<序号>/，review-<日期>-<NNN>.md 写评审记录（源 revision 记入 source_revision）
   2. reviewer 按本仓契约评审快照（同 feature 的上一轮记录先读，聚焦 delta）；按被评审文档的
      类型选择检查档（proposal/PRD、spec、design——清单在 `agents/reviewer.md` 的 document
      review modes），每条检查项须引用原文句或 `path:line`，无法引用即未过
   3. 发现的问题一条一条写进 issues/（frontmatter 见下）
   4. python3 tools/lab/validate.py artifacts 全绿后才算收口
   ▼
升级回路
   - provenance: external + files 指向业务仓模板/文档 → 升级业务仓 rule/template 的证据池
   - provenance: agentflow → agentflow 自己的 review 该抓没抓 → 升级本仓 reviewer 契约
   - 业务仓落地升级后回填 bug 记录的 fix_revision（业务仓 commit）闭环
```

## bug 记录的归因约定（评审发现专用）

| 发现根因 | provenance | attribution | files 指向 |
| --- | --- | --- | --- |
| 业务仓模板没逼问出该信息（缺章节/缺矩阵） | `external` | `product_code` | 业务仓模板或文档（见下方引用格式） |
| 文档有对应章节但内容错（写错了/没对齐代码） | `external` | `product_code` | 业务仓文档 |
| agentflow 的 review 清单本应抓住但漏了 | `agentflow` | `role_prompt` | 本仓 agents/reviewer.md 等 |
| 会话内临场分析失误，两边规则都没覆盖 | `session-artifact` | `unknown` | — |

升级优先级查询：`python3 tools/lab/validate.py report | awk -F'\t' '$7=="external"' | cut -f5 | sort | uniq -c | sort -rn`
——哪类 `error_kind` 反复出现，就先补业务仓哪个模板的强制章节。

## 引用自包含（把仓库给别人时记录仍可读）

记录里的引用分三类，前两类随本仓走，第三类是外部引用、必须显式限定：

1. **仓内路径**：`agents/reviewer.md` —— 校验器检查它在盘；**评审发现的 `files` 优先用
   这种**：指向本仓快照 `reviews/<feature>/archive/<轮次>/<doc>.md`（整份 copy
   已在 archive 里），原始地址（`aiwork-workflow-ai@3930ebb:docs/...`）写进正文；
2. **仓限定引用**：`<repo>@<revision>:<path>` —— 校验器跳过磁盘检查，但**含此类引用的
   记录正文必须内嵌片段**（代码围栏块、文档引用块），且片段旁标注该仓限定地址原文
   （校验器强制）；
3. 禁止裸外部路径：既不在本仓又没仓限定的 `files` 条目直接 FAIL——它对拿到记录但没有
   那个仓库的人是悬空引用。

仓限定是地址，内嵌片段才是证据——两者都要，缺一即 FAIL。整份文档的 copy 由
`archive/` 承担，记录自身只嵌决定性片段。

**正文引用规则（评审记录同样强制）**：正文散文里的路径要么在盘、要么仓限定；围栏块
与内联代码是引文（含历史路径）不扫；个人绝对路径禁止；URL 至多作补充、不得作证据。
评审记录引用被评审文档一律写本仓 archive 快照路径，不写业务仓当前路径——评审对象
是快照，不是会漂移的现场。

## 已知边界

- 跨仓再犯类的档位（`escalated`）暂不能自动推导：`consolidated_in` 绑定 Agentflow semver，
  业务仓没有版本号。跨仓类先用 `report` 按 `project` + `error_kind` 聚类观察；是否把
  `consolidated_in` 放宽为 `repo@ref` 是后续选项。
- `@<revision>` 本身不自检——它只是让悬空显式化；快照完整性由 `archive/` 承担。
