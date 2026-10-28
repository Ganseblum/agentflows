---
bug_id: ISS-2026-10-14-轻量链与linter硬冲突
title: 契约允许轻量链（无 spec/design 轨），但 linter 的 C1 无条件要求四个阶段目录非空——降级路径只存在于纸面
status: verified
severity: P2
error_kind: missing-constraint
attribution: workflow_policy
provenance: agentflow
project: agentflow
files:
  - tools/lab/doc_chain.py
  - skills/agentflow/references/document-chain.md
recorded_at: 2026-10-14T00:20:00+08:00
source_revision: agentflows@fb98b21 + 本批工作树（2026-10-13 审计批）
agentflow_version: 0.10.0
fix_revision: 随本批提交（agentflows，2026-10-14）
regression_status: pass
updated_at: 2026-10-19T21:45:00+08:00
reviewer: agentflow:reviewer（2026-10-19 独立批量复审）
review_decision: approved
closure_criteria: doc_chain.py C1 对声明轻量的链收窄阶段集且 proposal 缺失仍红（self-test case 42/43）+ 未声明而 design 空的链仍红（case 63）+ document-chain.md 段落映射豁免与 linter 口径一致 + validate.py all PASS。
---

## 现象

`skills/agentflow/references/document-chain.md` 第 59-61 行允许一个批次「只需要入口文档和一份
proposal（没有独立的 spec 或 design 轨）」，只要在 README 元信息行声明
`轻量模式：无 spec/design 轨`。同一份契约第 205 行又要求「宣布一条链完成之前，运行确定性
linter」：

```sh
python3 tools/lab/doc_chain.py <feature-dir>
```

但 `tools/lab/doc_chain.py` 的 C1 对 `proposal`、`spec`、`design`、`plan` 四个目录无条件要求
非空（修订前 `lint()` 中 `for stage in ("proposal", "spec", "design", "plan")`），全文中不存在
任何「轻量」豁免分支——仅有 C11 的 marker 门。结果是：**一个完全合规的轻量链跑 linter 必定
红灯**，而契约要求它必须跑。降级路径写在文档里，机器上没有。

2026-10-13 的全仓审计把这一条记为架构自洽性的首要扣分点：契约承诺了实现不提供的东西，且
冲突双方（契约段落与 linter 判据）各自都「正确」，靠读者自己发现。

## 根因

1. **降级形态写进契约时未同步判据**：轻量模式是后来补进链契约的，linter 的 C1 早于它，两者
   没有同一份事实来源。契约里也没有任何一条规则要求「新增降级形态时同步 linter」。
2. **没有 fixture 钉住降级形态**：linter 的自测只覆盖完整链（46 个 case 中无一涉及轻量声明），
   因此降级形态从不被执行，也就无从暴露冲突。
3. 与 ISS-2026-09-21-linter存在性检查非形态标准致塞复发（linter 存在性检查 ≠ 形态标准）同族：这类缺口都是「写得出、跑不了」。

## 修复

1. `tools/lab/doc_chain.py` 的 C1 改为**声明门禁**的轻量豁免：README 出现
   正则 `轻量模式[：:][^\n]*无\s*spec/design\s*轨` 时，阶段要求收窄为 `proposal` + `plan`；
   未声明的批次保留全链要求。豁免是「收窄阶段集」，不是关掉 C1——proposal 缺失仍报 C1。
2. 自测新增三个 case：42（声明轻量的链通过）、43（声明轻量但缺 proposal 仍红）、
   44（未声明而 design 空仍红，证明豁免不靠空目录推断）。
3. 依赖 spec/design 的判据（C3–C8、C11）在轻量链下因阶段文件为空自然不触发，无需额外分支；
   C9 的 V-item 闭合是单向的（design 声明的 V-id 必须被 plan 引用），轻量链无 design 不误报。

## 回归检查

- `python3 tools/lab/doc_chain.py --self-test` → 46/46 cases pass（含 42/43/44）。
- `python3 tools/lab/validate.py all` → 9×PASS；`python3 -m unittest discover -s tests` → 60 OK。
- 负向：删掉 README 的轻量声明、保留空的 design/ → C1 仍报「design 下没有任何有效文档」（case 44）。

## 怎么避免

链契约每增加一种降级形态，判据与自测必须同批落地——降级不是文档里的形容词，是 linter 里
的一条分支加一个 case。

## 审查

2026-10-19 独立复审（agentflow:reviewer 子代理，只读）。修复声称核对成立：doc_chain.py:406-426 C1 轻量豁免（声明门禁 + required_stages 收窄为 proposal+plan，proposal 缺失仍红）在盘；自测 case 42/43/63 在册；契约已演进为段落映射统一形态，linter 两条豁免路径口径一致。回归证据：self-test 63/63、validate all 9×PASS、unittest 96 OK。review_decision：approved。

## 变更记录

- 2026-10-14 · recorded + fixed · 轻量链豁免与三个自测 case 随本批提交（fix_revision 同上）
- 2026-10-19 21:45 · 独立复审通过 · agentflow:reviewer 批量复审（只读）核对修复声称与回归证据成立，转 verified。
