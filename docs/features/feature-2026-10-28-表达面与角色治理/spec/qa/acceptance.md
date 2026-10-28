# 验收标准：表达面与角色治理批

## 0. 缺口台账

| 编号 | 缺口 | 来源 | 状态 |
| --- | --- | --- | --- |
| Q-01 | 同一规则三份实质副本，靠「改一处就改另一处」对冲 | 评测 B4 | 已由 M01 承接 |
| Q-02 | `document-chain.md` 494 行，诊断与契约混排 | 评测 B4 | 已由 M02 承接 |
| Q-03 | FE/BE 合并有判据未执行，悬案从 2026-10-19 挂到现在 | 评测 B5 | 已由 M03 承接 |
| Q-04 | 实现角色深度与职责不匹配 | 评测 B5 | 已由 M04 承接 |

无未关闭阻塞项。「`global-rules.md` 必须自带全文」不是阻塞，是设计约束（见 proposal §1.3）。

## 4. 验收点

### G1 规则单一权威

- **G1-AC-01**：`spec/be/backend.md` §1.1 归属表的每一行，其 A 级载体在盘存在且含指定锚点。
  判据：`python3 - <<'EOF'` 逐行断言（表驱动，锚点字符串在该文件里匹配）。
- **G1-AC-02**：C 级载体里该规则段落 ≤ A 级载体的 40% 长度，且含可解析的 A 路径引用。
  判据：脚本比较段落长度 + 用 markdown 链接解析器验证目标存在。

### G2 同步义务退场

- **G2-AC-01**：`grep -c "改一处就改另一处" skills/agentflow/SKILL.md` → 0；
  若保留，须在归属表里显式标注该行属「A↔B 无法指针化」。
  当前值：1（`SKILL.md:102`），目标 0。

### G3 大文档可导航

- **G3-AC-01**：`wc -l skills/agentflow/references/document-chain.md` ≤ 150；且原 `##` 标题集合
  与拆后两文件的并集差集为空。判据：脚本提取标题做双向差集。
- **G3-AC-02**：`doc_chain.py --self-test` 全过（基线 124/124）；
  `validate.py doc_chain_live` 无新增 finding（基线 0 findings）。

### G4 FE/BE 裁决

- **G4-AC-01**：`roles.md` 裁决段含三个条件的实测数字与明确结论。
  判据：`grep -A6 "裁决规则" roles.md` 命中含 `%`、`分歧`、`行` 三个数值标记 + 「已裁决」字样。
- **G4-AC-02**：结论为「保持分立」时，同段含「下次重审触发条件」行。判据：关键词命中。

### G5 实现角色深度

- **G5-AC-01**：三个角色文件逐条覆盖 §4 列出的职责；缺失项有「由谁承担」的交代。
  判据：人工核对 + 在角色文件里每条职责有对应标题或条款（`grep` 关键职责词）。
- **G5-AC-02**：`wc -l agents/backend-engineer.md agents/frontend-engineer.md agents/technical-director.md`
  三者均 ≤ 120；`validate.py docs` PASS。

## 5. 诊断指标（不是验收门槛）

| 指标 | 立项基线 | 期望方向 |
| --- | --- | --- |
| `SKILL.md` 行数 | 135 | 持平或下降 |
| `contracts.md` 行数 | 195 | 只降不升（删重复段） |
| `document-chain.md` 行数 | 494 | ≤ 150（拆出细则） |
| `references/` 总行数 | 按 `wc -l` 实测 | 允许因拆分小增；若增幅 > 10% 判拆分失败 |
| 角色文件行数极差 | 175 − 20 = 155 | 收窄 |

## 6. 验证命令

```sh
python3.12 tools/lab/validate.py all
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-表达面与角色治理"
python3.12 tools/lab/doc_chain.py --self-test
python3.12 -m unittest discover -s tests
```

四项全绿。任一项红按编译错误处理：修好，或如实登记，不得跳过或缩小范围换绿。
