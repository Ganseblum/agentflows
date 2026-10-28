# 验证方案：评审欠账清偿批

## 1. 验证矩阵

| 目标 | 验收点 | 验证方式 | 真实前置 |
| --- | --- | --- | --- |
| G1 | G1-AC-01 | 逐文件读两批 `reviews/*.md` frontmatter，断言 `review_tier`/`reviewed_revision`/`decision` 三字段且在 {L1,L2} | 委派能力可用（T01 探测通过） |
| G1 | G1-AC-02 | findings 集合 × `docs/issues/` 文件名交集断言 | 评审记录已产出 |
| G2 | G2-AC-01 | 清点命令输出行数 × 清单表「未清偿」行数，逐值相等 | 清单节已写入 `docs/releases/todo.md` |
| G2 | G2-AC-02 | 两份反向夹具：伪降级必红、带 `dispatch_errors` 的 L0 必绿 | 校验器改动已落地（需授权） |
| G3 | G3-AC-01 | 五条 ISS 逐条读 frontmatter + 正文「复核结论」节存在性 | 五条已被独立评审 |
| G3 | G3-AC-02 | 四条 `fix_revision` 存在且 `git cat-file -e` 可解或形如 `N/A: …` | 同上 |

## 2. 反例（必须让它红）

| 反例 | 期望 | 归属验收点 |
| --- | --- | --- |
| `reviews/` 放一份 `review_tier: L0` 无 `dispatch_errors` 的记录 | 记录校验器红 | G2-AC-02 |
| 五条 ISS 直接改 `verified` 不补 `reviewer` | `validate.py artifacts` 红 | G3-AC-01 |
| 清单写「已清偿」而 `reviews/` 仍空 | 清点脚本打印矛盾行并非零退出 | G2-AC-01 |
| 清点命令输出行数与清单未清偿行数不等 | 判红 | G2-AC-01 |
| 把 16 条外部 `open` 缺陷批量改状态 | 评审拒收（超范围，见 proposal §1.4） | 范围守卫 |

## 3. 环境预检

- 解释器：`python3.12`；`python3` 为 CLT 3.9.6，跑 `validate.py` 会 `exit 2`「No check was run」。
- lint：仓内 `.venv` 已就绪，立项时 `validate.py all` 实测 11/11 PASS。
- 委派：2026-10-28 实测已恢复（`reviewer` 探测任务成功返回）；实施时须由 T01 重新探测一次，
  不复用立项时的探测结论。
- 安装面：`validate.py installed` 红（无 0.20.0 快照）。本批不改角色面，不重装；该项不计入本批验收。

## 4. 失败分流

| 观察 | 分类 | 动作 |
| --- | --- | --- |
| T01 探测失败（`model concurrency limit exceeded`） | 前置缺失 | T02/T03/T05/T06/T07 置 ⚠ 阻塞，如实登记原始错误；**不得**用主审自审冒充清偿 |
| 评审结论 `changes_requested` | 本批要处理的对象 | findings 转 ISS；此前被接受的改动回到待修状态（`contracts.md` 不变式 3） |
| T04 未获受保护面授权 | 授权缺失 | T04 置 ⚠；G2 结论上限 `partial`，G2-AC-01 退到批次内脚本口径 |
| `validate.py all` 仅 `installed` 红 | 环境/未重装 | 按既有口径单独记录，不并入本批结论 |
| 五条中某条经复核修复不成立 | 预期内 | 退回 `open` 并在 `## 修复` 节追加「复核结论」，写明缺什么 |

## 5. 证据落点

| 证据 | 落点 |
| --- | --- |
| 委派探测的原始返回 | 批次 `testing/delegation-probe.txt` |
| 两批独立评审记录 | 各批次 `reviews/`（批次内材料，不受评审契约四项校验） |
| 清点命令的原始输出 | 批次 `testing/review-debt-count.txt` |
| 两份反向夹具的红绿输出 | 批次 `testing/pseudo-downgrade-red.txt` / `-green.txt` |
| 五条 ISS 的复核结论 | 各 ISS 记录的 `## 修复` 节 |
