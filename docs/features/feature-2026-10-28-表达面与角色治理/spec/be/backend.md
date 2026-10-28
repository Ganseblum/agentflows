# 规格：表达面与角色治理批

## 0. Proposal 反审 checklist

| 不合规项 | 结论 | 处置 |
| --- | --- | --- |
| 是否把「删除重复」当成唯一解 | 合规 | §1.3 明确「宿主级载体必须自带全文」，本批形态是「权威载体 + 最短自足表述 + 指针」 |
| 是否动了未授权范围 | 合规 | 不做事项表逐条给理由；`contracts.md` 只允许删重复段且需逐项授权 |
| 是否与既有拍板冲突 | 合规 | `roles.md:79` 的「有意不收敛」被保留；FE/BE 结论不预设方向 |
| 是否声称了未验证的疗效 | 合规 | 全批 `measurement: none`；G4 的结论来自实测而非推断 |

## 1. M01 载体归属表（G1/G2 的核心交付物）

对每条跨载体规则指定**唯一权威载体**，其余载体按「自足等级」处理。三个等级的定义：

| 等级 | 含义 | 处理 |
| --- | --- | --- |
| **A 权威** | 规则正文只此一处；其余为指针 | 保留全文，成为唯一可编辑点 |
| **B 必须自足** | 该载体在目标仓/宿主全局独立加载，读不到 A | 保留完整可执行表述；与 A 的差异须是**载体特有**的，不是措辞漂移 |
| **C 摘要指针** | 与 A 同时加载，或只需知道「去哪读」 | 压成一句摘要 + 指向 A 的链接 |

### 1.1 归属表

| 规则 | 权威载体（A） | 必须自足（B） | 摘要指针（C） | 处置 |
| --- | --- | --- | --- | --- |
| 集成/推送/改写历史需当次授权 | `references/contracts.md` 硬边界 3 | `templates/host/global-rules.md` §2（宿主全局） | `SKILL.md:131` | SKILL 压成一句 + 指针 |
| 写操作前先确认分支 | `templates/host/global-rules.md` §1（宿主全局唯一权威） | 同左 | `references/hosts.md:21`（已是指针，保留） | 不再新增副本 |
| 证据纪律（摘要不是验证） | `references/contracts.md` 硬边界 4 + 12 | `templates/host/global-rules.md` §4 | `SKILL.md` 第 7 步 | 各自保留，去掉逐字重合 |
| 检索纪律（裸 grep 静默漏报） | `references/repo-audit.md` | `templates/host/global-rules.md` §11 | `SKILL.md` Init 节 | Init 节已是指针形态，保留 |
| 重试纪律（同一原因两次即停） | `references/contracts.md` 硬边界 10 | 无（非跨仓默认项） | `SKILL.md`「从停滞中恢复」、`improve/SKILL.md` | SKILL 压成指针 |
| 评审能力分级 L0/L1/L2 | `references/contracts.md`「评审能力分级」 | 无 | `SKILL.md` 第 8 步（已是指针） | 已达标，不动 |
| 已裁撤能力说明 | `docs/design-decisions.md` §3（仓内唯一权威） | 无 | `improve/SKILL.md` 6 处 | 收敛为 1 处现状说明 + 指针 |

### 1.2 判据

- **G1-AC-01**：上表每条规则的「权威载体」在盘存在，且其正文包含该规则的**可执行动作**
  （不是仅提及）。判据脚本对每行断言：A 载体路径存在 + 含指定锚点字符串。
- **G1-AC-02**：C 级载体不再包含该规则的完整动作描述。判据：C 载体里该规则段落长度
  ≤ 权威载体的 40%，且含指向 A 的路径引用（markdown 链接可解析）。
- **G2-AC-01**：`SKILL.md` 不再出现「改一处就改另一处」这类同步义务；若必须保留同步义务，
  只允许出现在「A 与 B 之间且 B 无法指针化」的场合，并在归属表里显式标出该行。

## 2. M02 `document-chain.md` 拆分（G3）

**契约**：拆成两份，扫描面显式声明。

| 文件 | 职责 | 上限 |
| --- | --- | --- |
| `references/document-chain.md` | 链契约：接入 → 访谈 → proposal → spec → design → plan → 实施，每段的产出、门、判据速查 | 150 行 |
| `references/document-chain-checks.md` | 判据细则：C 检查逐条含义、夹具、边界，供改门者查阅 | 无上限 |

- **G3-AC-01**：`document-chain.md` ≤ 150 行，且原有每个 `##` 标题都有一个落点（原文件或
  `-checks.md`），用脚本对标题集合做双向差集为空。
- **G3-AC-02**：拆分后 `doc_chain.py --self-test` 全过（当前 124/124），
  `validate.py doc_chain_live` 无新增 finding。

## 3. M03 FE/BE 合并裁决（G4）

用 `docs/features/feature-2026-10-13-质量提升/testing/agentflows-role-boundary/` 的 28 例语料，
按 `roles.md:83` 的三条件判定：

| 条件 | 阈值 | 判定方法 |
| --- | --- | --- |
| ① 同场景判定不一致率 | < 10%（≤2/28） | 对每例分别令 frontend 与 backend 角色文件独立作答，比较结论（拒绝/接受/升级） |
| ② 产物所有权矩阵分歧项 | = 0 | 逐项对照两个角色文件的「产物所有权」表；有分歧即一票否决 |
| ③ 合并后单文件行数 | ≤ 60 | 合并稿实测 `wc -l` |

- **G4-AC-01**：三个条件各有实测数字，写在 `roles.md` 的裁决段，并给「已裁决：合并 / 保持分立」
  的明确结论。**不接受「数据不足」作为结论**——语料不足就写明缺哪几例、缺多少。
- **G4-AC-02**：若结论是「保持分立」，同段落必须写明「下次重审触发条件」（例如角色文件
  任一超过 N 行、或新增角色时）。

## 4. M04 实现角色深度（G5）

**契约**：实现角色的深度缺口要有实测口径，不是凭感觉加字数。

- **G5-AC-01**：对 `backend-engineer` / `frontend-engineer` / `technical-director` 三个文件，
  逐条核对它们是否承载了 `roles.md` 分配给它们的职责（Backend 定对象模型/状态机/接口契约/DDL；
  Frontend 定页面规格/文件落点/类型契约/字段映射；TD 定接口/权限/数据/时序/难回退决策）。
  缺哪条职责，要么补进角色文件，要么在角色文件里写明「该职责由谁承担」。
- **G5-AC-02**：改完后三个文件均 ≤ 120 行（防止把 SKILL 的重复搬进角色文件造成新的膨胀），
  且 `validate.py docs` 的角色面检查（frontmatter name == 文件名、`agentflow:<role>` 可解析）仍 PASS。

## 5. 验证命令

```sh
python3 tools/lab/validate.py all
python3 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-表达面与角色治理"
python3 tools/lab/doc_chain.py --self-test
python3 -m unittest discover -s tests
wc -l skills/agentflow/SKILL.md skills/agentflow/references/document-chain.md agents/*.md
```

五项全绿才算可接受；行数是**诊断指标不是验收判据**，但拆分后若 `document-chain.md` 反而变长，
说明拆分失败。
