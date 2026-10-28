# 验收标准：评测整改批

## 0. 缺口台账

| 编号 | 缺口 | 来源 | 状态 |
| --- | --- | --- | --- |
| Q-01 | 审计产物无整改状态载体 | 评测 B1 | 已由 M01 承接 |
| Q-02 | 评审能力无分级、降级不可审计 | 评测 B2 | 已由 M02 承接 |
| Q-03 | 表达面重复 | 评测 B4 | 已由 M03 承接 |
| Q-04 | 本机门基线常红 | 评测 B3 | 已由 M04 承接 |
| Q-05 | 改进环零真实记录 | 评测 B2/B5 | 已由 M05 承接 |

无未关闭阻塞项。

## 4. 验收点

### G1 整改可追踪

- **G1-AC-01**：`docs/evaluations/AGENTFLOW-AUDIT-2026-10-26.md` 的发现总表表头含 `整改状态` 与
  `fix_revision` 两列，且 35 行（G01–G35）每行两列均非空。
  判据：`python3 - <<'EOF'` 解析该表，断言列名存在且每行两列非空；输出命中行数应为 35。
- **G1-AC-02**：`skills/agentflow/references/repo-audit.md` 写入「发现总表必须带整改状态列」条款。
  判据：`grep -c "整改状态" skills/agentflow/references/repo-audit.md` ≥ 1。

### G2 评审能力可分级

- **G2-AC-01**：`skills/agentflow/references/contracts.md` 含 L0/L1/L2 三档定义与「降级必须留痕」条款。
  判据：`grep -c "L0" contracts.md` ≥ 1 且三档在同一节。
- **G2-AC-02**：`skills/agentflow/SKILL.md` 第 8 步（评审门）引用该分级协议。
  判据：`grep -n "review_tier\|L0" SKILL.md` 命中位于第 8 步段落内。
- **G2-AC-03**：分级协议明确「L0 不适用于用户可见行为改动的最终放行」。
  判据：`grep -c "最终放行" contracts.md` ≥ 1。

### G3 表达面收敛

- **G3-AC-01**：`SKILL.md` 中 `execution-coordinator` 的「当前不存在」声明合并为一处。
  判据：`grep -c "当前不存在" SKILL.md` 由 2 降为 1（或其中一处改为指针且不重复该断言）。
- **G3-AC-02**：`roles.md` 含 FE/BE 合并的**裁决规则**（可判定条件），而非只有「待议」。
  判据：`grep -A3 "frontend / backend" roles.md` 命中含明确阈值或判据行。

### G4 本地门基线

- **G4-AC-01**：`tools/lab/validate.py` 的 lint 子项在 `AGENTFLOW_LINT_PYTHON` 未设且
  `.venv/bin/python` 存在时使用后者。
  判据：在 `/tmp` 副本上创建伪 `.venv/bin/python` 指向装好 ruff 的解释器，`validate.py lint` 由
  FAIL 转 PASS；无 `.venv` 时仍 FAIL（行为不变）。
- **G4-AC-02**：`README.md` 或 `AGENTS.md` 给出 `.venv` 一行创建命令。
  判据：`grep -c "venv" README.md AGENTS.md` ≥ 1。

### G5 改进环闭环

- **G5-AC-01**：仓内存在一份 `candidate` 记录与一份 `release-record` 记录，且通过
  `python3 tools/lab/validate.py artifacts` 编译。
- **G5-AC-02**：`docs/trend.jsonl` 末行 `recorded_at` 为本批日期，`unittest_count` 与实跑一致。

## 5. 验证命令

```sh
python3 tools/lab/validate.py all
python3 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-评测整改批"
python3 tools/lab/doc_chain.py --self-test
python3 -m unittest discover -s tests
```

四项全绿才算本批可接受；红项如实登记，不用跳过或缩小范围换绿。
