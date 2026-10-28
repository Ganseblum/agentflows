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
  每份 frontmatter 含 `review_tier`（值为 `L1` 或 `L2`）、`reviewed_revision`、`decision`。
  判据：逐文件读 frontmatter，四断言全部为真。
  当前值：两目录均为空（0 份）。
- **G1-AC-02**：两份记录 `decision` 为 `changes_requested` 时，findings 引用的每个 `ISS-*`
  在 `docs/issues/` 存在；或记录正文逐条写「已就地修复 + fix_revision」。
  判据：findings 集合与 `docs/issues/` 文件名的交集断言。

### G2 评审欠账可机器清点

- **G2-AC-01**：存在一条命令，输出「未清偿欠账」清单，行数等于欠账清单表中 `状态=未清偿` 的行数。
  判据：`wc -l` 与表格计数逐值相等，且命令退出码为 0。
- **G2-AC-02**：伪降级被拒。构造 `review_tier: L0` + `dispatch_errors: []` 的夹具，
  校验器必须红；构造 `review_tier: L0` + `dispatch_errors: ["model concurrency limit exceeded"]`
  的夹具，校验器必须绿。判据：两个反向夹具各跑一次，断言退出码。
  当前值：无任何校验器读 `review_tier`（`grep -rn review_tier tools/ schemas/ tests/` 零命中）。

### G3 五条待评审缺陷逐条清偿

- **G3-AC-01**：ISS-2026-057/058/060/061/066 五条各自的状态要么是 `verified` 且带
  `reviewer` + `review_decision: approved` + `regression_status: pass` + `closure_criteria`，
  要么是 `open` 且正文 `## 修复` 节追加了「复核结论」写明缺什么。判据：逐条读 frontmatter
  与正文小节存在性。
  当前值：五条均为 `fixed-pending-review`，无一为 `verified`。
- **G3-AC-02**：ISS-2026-057/058/060/061 四条补 `fix_revision`（可解析提交号或版本）或
  显式 `N/A: 理由`；ISS-2026-066 的 `fix_revision` 现值为「0.20.0（分支 …未发布）」，
  须改写为已并入 `main` 的提交号。判据：字段存在、非空、`git cat-file -e` 可解或形如 `N/A: …`。
  当前值：四条缺该字段；ISS-2026-066 的值指向已并入的分支表述。

## 2. 反例（必须让它红）

| 反例 | 期望 |
| --- | --- |
| 往 `reviews/` 放一份 `review_tier: L0` 且不写 `dispatch_errors` 的记录，冒充已清偿 | G2-AC-02 判红；G1-AC-01 判红（值不得为 L0） |
| 把五条 ISS 直接改成 `verified` 但不补 `reviewer` | `validate.py artifacts` 红（schema `allOf` 要求 verified 带 reviewer/review_decision/closure_criteria） |
| 欠账清单写「已清偿」但 `reviews/` 仍为空 | G1-AC-01 与清单状态矛盾 → 判红 |
| 清点命令输出 0 行而清单有未清偿行 | G2-AC-01 判红（行数不等） |
| 顺手把 16 条 `open` 的外部计划缺陷改成 `verified` | 超出范围；`disposition: deferred` 与 `verified` 冲突，评审须拒 |

## 3. 诊断指标（不是验收门槛）

| 指标 | 立项基线 | 期望方向 |
| --- | --- | --- |
| 两批 `reviews/` 文件数 | 0 / 0 | 各 ≥1 |
| `fixed-pending-review` 记录数 | 5 | 降至 0（全部转 verified 或退回 open） |
| 缺 `fix_revision` 的记录数 | 4 | 降至 0 |
| `grep -rn review_tier tools/ schemas/ tests/` 命中数 | 0 | ≥1（校验器读它） |

## 4. 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评审欠账清偿"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

四项全绿。任一项红按编译错误处理：修好，或如实登记为未运行，不得跳过或缩小范围换绿。

## 5. 环境预检

- 解释器：`python3.12`（`python3` 为 CLT 3.9.6，`validate.py` 对本机 3.9 直接 `exit 2`「No check was run」）。
- lint：仓内 `.venv` 已就绪，`validate.py all` 立项时实测 11/11 PASS。
- 委派：2026-10-28 实测**已恢复**（向 `reviewer` 派发探测任务成功返回），故本批按 L1 档立项。
- 安装面：`validate.py installed` 当前红（无 0.20.0 快照）。本批不改角色面，不重装。
