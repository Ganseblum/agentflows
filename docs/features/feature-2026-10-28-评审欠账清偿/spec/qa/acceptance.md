# 验收标准：评审欠账清偿批

## 0. 缺口台账

| 编号 | 缺口 | 来源 | 状态 |
| --- | --- | --- | --- |
| Q-01 | 两个 2026-10-28 批次的 L0 自审未补，`reviews/` 为空 | 评测 B2 | 已由 M-A 承接 |
| Q-02 | `review_tier` 零机器校验，伪降级无法被检出 | 评测 B2 + 实测 grep 零命中 | 已由 M-B 承接 |
| Q-03 | 五条 ISS 停在 `fixed-pending-review`，四条缺 `fix_revision` | 实测 66 条记录的状态统计 | 已由 M-C 承接 |

无未关闭阻塞项。「委派能力必须可用」不是阻塞项，是执行前置（见 spec §1.3 约束一与 plan T01）。

## 1. 验收点

### G1 两个批次的 L0 欠账被清偿

- **G1-AC-01**：`docs/features/feature-2026-10-28-评测整改批/reviews/` 与
  `docs/features/feature-2026-10-28-表达面与角色治理/reviews/` 各有 ≥1 份 `.md` 记录，
  每份 frontmatter 满足四项：`review_tier ∈ {L1, L2}`；`source_revision` 非空且
  `git cat-file -e <值>^{commit}` 退出 0；`decision ∈ {approved, changes_requested, blocked}`；
  `recorded_at` 存在。字段名取 `schemas/review.schema.json` 的既有契约（`source_revision`），
  不引入该契约不存在的 `reviewed_revision`。
  判据：逐文件读 frontmatter，四断言全部为真。
  当前值：两目录均为空（0 份）。
- **G1-AC-02**：记录 `decision` 为 `changes_requested` 时，`findings` 里每个 `ISS-*`
  都必须在 `docs/issues/` 存在。**无「正文写已就地修复」旁路**。
  判据：断言 `findings ⊆ {docs/issues/ISS-*.md 的 bug_id}`，差集非空即红。

### G2 评审欠账可机器清点

- **G2-AC-01**：清点命令输出行数等于**从仓内事实派生的欠账数**（不是它自己读的手工表）：
  ①批次 README/计划声明 L0 且 `reviews/` 无记录；②`status: fixed-pending-review` 且无 `reviewer`
  的 ISS；③清单里 `状态=未清偿` 的行。断言 `输出行数 == |①∪②|`，且 `③ ⊆ ①∪②`
  （清单把 ①∪② 中仍存在的项写成已清偿 ⇒ 红）。这条替代了前一版的「输出行数 == 清单行数」
  ——那是自指判据，清单漏行时会 0 对 0 判绿。
  当前值：①∪② = 2 批 + 5 条 = 7 项；清单尚不存在（0 行）。
- **G2-AC-02**：伪降级在**两处载体**都被判红：
  (a) 评审记录 `review_tier: L0` + `dispatch_errors` 为空 ⇒ 校验器红；
  (b) 批次 README/计划声明 L0 且 `reviews/` 为空 ⇒ 计入 G2-AC-01 的未清偿派生集合。
  判据：(a) 两个反向夹具各跑一次断言退出码；(b) 拿现存两批实测，断言派生集合恰含这两条。
  当前值：(a) 无校验器读 `review_tier`（`grep -rn review_tier tools/ schemas/ tests/` 零命中）；
  (b) 两批 L0 声明在盘但 `reviews/` 为空，无任何判据统计它。

### G3 五条待评审缺陷逐条清偿

- **G3-AC-01**：ISS-2026-057/058/060/061/066 五条各自的状态要么是 `verified` 且 frontmatter 带
  `reviewer` + `review_decision: approved` + `regression_status: pass` + `closure_criteria`
  + `fix_revision`，**且正文含 `## 审查` 节**（`tools/lab/gate/records.py:317` 对 verified 强制该标题），
  要么是 `open` 且正文 `## 修复` 节追加了「## 复核结论」写明缺什么。
  判据：逐条读 frontmatter 与正文小节存在性，两条路径之外即红。
  当前值：五条均为 `fixed-pending-review`，无一为 `verified`。
- **G3-AC-02**：`fix_revision` 唯一合法形态是**可解析的提交号**
  （`git cat-file -e <值>^{commit}` 退出 0）。版本号不是 git 对象，不能作为该字段的值——
  仓内也无对应版本 tag（`git tag` 仅 `workbuddy-merge-2026-10-18` 一个历史 tag）。
  保持 `fixed-pending-review`/`verified` 的记录该字段必填；退回 `open` 时可按模板缺省，
  若保留须写 `N/A: 复核不成立，修复未落地`。
  判据：逐条断言 `git cat-file -e` 退出 0，或（状态为 `open` 且值以 `N/A: ` 开头）。
  当前值：ISS-2026-066 的值为 `0.20.0（分支 feature-2026-10-28-评测整改批，未发布）`——
  既非提交号、句中的分支也已并入 `main`；其余四条缺该字段。

## 2. 反例（必须让它红）

| 反例 | 期望 |
| --- | --- |
| 往 `reviews/` 放一份 `review_tier: L0` 且不写 `dispatch_errors` 的记录，冒充已清偿 | G2-AC-02(a) 校验器红；G1-AC-01 判红（值须 ∈ {L1,L2}） |
| 把五条 ISS 直接改成 `verified` 但不补 `reviewer` 或正文无 `## 审查` | `validate.py artifacts` 红（schema `allOf` + `records.py:317` 双重要求） |
| 欠账清单写「已清偿」但 `reviews/` 仍为空 | G2-AC-01 判红（①∪② 仍计入而清单写已清偿） |
| 清点命令只回读自己写的手工表（漏行即 0 对 0） | G2-AC-01 判红（判据锚在仓内派生事实，不锚在清单） |
| `fix_revision` 填 `0.20.0` 这类版本号 | G3-AC-02 判红（`git cat-file -e 0.20.0^{commit}` 失败） |
| 顺手把 16 条 `open` 的外部计划缺陷改成 `verified` | 超出范围；`disposition: deferred` 与 `verified` 冲突，评审须拒 |

## 3. 诊断指标（不是验收门槛）

| 指标 | 立项基线 | 期望方向 |
| --- | --- | --- |
| 两批 `reviews/` 文件数 | 0 / 0 | 各 ≥1 |
| `fixed-pending-review` 记录数 | 5 | 降至 0（全部转 verified 或退回 open） |
| 缺 `fix_revision` 的（非 open）记录数 | 4 | 降至 0 |
| `grep -rn review_tier tools/ schemas/ tests/` 命中数 | 0 | ≥1（校验器读它） |
| `manifests` 生成树新鲜度 | PASS（源与快照一致） | 改 schema 后仍 PASS（须重建） |

## 4. 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评审欠账清偿"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

四项全绿。任一项红按编译错误处理：修好，或如实登记为未运行，不得跳过或缩小范围换绿。

**`installed` 不在上述四项内**：`validate.py --list` 实测 11 项（schemas / examples / artifacts /
protected / manifests / docs / tests / doc_chain / doc_chain_live / decision_gate / lint），
`installed` 是独立 target（`tools/lab/validate.py:403-408`），`all` 不运行它。
核对安装面须单独执行 `python3.12 tools/lab/validate.py installed`，结果与本批验收结论分开记。

## 5. 环境预检

- 解释器：`python3.12`（`python3` 为 CLT 3.9.6；`validate.py all` / `--list` / `installed` 在 3.9 下
  均 `exit 2`「No check was run」，实测；`doc_chain.py` 在 3.9 下可运行）。
- lint：仓内 `.venv` 已就绪，立项时 `validate.py all` 实测 11/11 PASS。
- 委派：2026-10-28 实测**至少 1 个只读角色可派**（向 `reviewer` 派发探测任务成功返回）。
  **但一次成功不足以定 L1**——按 `contracts.md:34-38`，L2 要求「至少能派出 2 个只读角色」。
  档位由 T01 的两组探测决定（1 成功 + 第 2 个失败 ⇒ L1；2 个都成功 ⇒ L2），不按成本偏好选档。
- 安装面：`validate.py installed` 当前红（无 0.20.0 快照，已装至 0.19.3）。本批不改角色面，不重装。
