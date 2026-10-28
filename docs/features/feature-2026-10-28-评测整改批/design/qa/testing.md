# 验证方案：评测整改批

## 1. 验证矩阵

| 目标 | 验收点 | 验证方式 | 真实前置 |
| --- | --- | --- | --- |
| G1 | G1-AC-01 | 解析审计报告发现总表，断言 7 列且 35 行非空 | 审计报告在盘且本批已回写 |
| G1 | G1-AC-02 | `grep` repo-audit.md | 审核契约已改 |
| G2 | G2-AC-01~03 | `grep` contracts.md 与 SKILL.md | 分级节已写入 |
| G3 | G3-AC-01~02 | `grep -c` 前后计数对比 | 去重与裁决规则已改 |
| G4 | G4-AC-01 | `/tmp` 副本上造伪 `.venv`，跑 `validate.py lint` | 需要一份可写副本；不在真实树注入 |
| G4 | G4-AC-02 | `grep venv` README/AGENTS | 文档已改 |
| G5 | G5-AC-01 | `validate.py artifacts` 编译两份记录 | 记录文件已写 |
| G5 | G5-AC-02 | `trend.py --append` 后核对末行 | 前序检查已跑 |

## 2. 反例（必须让它红）

| 反例 | 期望 |
| --- | --- |
| 把 G14 行的 `整改状态` 清空 | 本批的解析脚本判不合格（列非空断言失败） |
| 伪 `.venv` 指向未装 ruff 的解释器 | `validate.py lint` 仍 FAIL（探测不改变 fail-closed） |
| 删除 `.venv` 后跑 lint | 行为与本批之前完全一致（FAIL + 安装提示） |
| 候选记录把 `measurement` 改为 `complete` 但无评测结果 | schema `allOf` 拒绝（依赖既有 schema，不新增判据） |

## 3. 环境预检

- 解释器：本机 `python3` 为 CLT 3.9.6，不足以运行 `tools/lab/`（要求 ≥3.10）；本批所有命令用
  `python3.12`。这是一条必须随证据一起记录的边界，不把 3.9 的报错算作门失败。
- lint 依赖：PEP 668 受管环境拒绝 `pip install`；本批为此落地 `.venv` 约定（G4），
  若 `.venv` 仍不可建，则 lint 记为「未运行（环境缺依赖）」，绝不计为通过。

## 4. 失败分流

| 观察 | 分类 | 动作 |
| --- | --- | --- |
| `validate.py all` 仅 lint 红 | 环境缺失 | 记未运行；先试 `.venv` 路径 |
| `doc_chain` 对本批红 | 链缺陷 | 修文档，非改 linter |
| `tests` 红 | 回归 | 先用 `git stash` 在父提交复跑对照，区分既存与本次新增 |
| `/tmp` 副本实验失败 | 夹具问题 | 修正夹具后重跑；不把无效记录计为结论 |
