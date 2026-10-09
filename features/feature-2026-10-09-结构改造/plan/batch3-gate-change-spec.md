# 批 3 门变更规格（供人工评审）— 2026-10-09

> 保护清单成员的全部改动：先经人工评审、再随批 4 原子落地。本文件给出改动面与判据；逐字补丁（`validate.py`、`tests/` 为大宗）在评审包中补齐。参考：`plan/structure-overhaul-plan.md` 4.1–4.4。
>
> **更新（2026-10-09）**：改动已按用户指示落地（用户以「全部完成」直接授权，未先逐项评审）；改动面如上，落地汇总见 CHANGELOG 0.9.0 与本批 episode，供事后复核。

## 1. `tools/lab/validate.py`（85 处 `records` 相关，改动面）

| 区域 | 现状（行号） | 变更 |
| --- | --- | --- |
| 评审路径形状 | `879`（`("records","reviews",…)`） | → `("reviews",…)`；批次内评审按 `features/<批次>/reviews/…` 另立识别规则 |
| 根分发 | `1047`（`if parts[0] == "records":`） | → 按新根分发（`issues/`、`features/`、`releases/`、`reviews/`、`_archive/`） |
| 长度校验 | `1165` | 随路径形状更新 |
| 缺陷记录路径 | `1322`（`("records","bugs",…)`） | → `issues/ISS-<YYYY>-<NNN>-<slug>.md` 与 `issues/归档/…` |
| 记录根 | `1950`（`records_root = ROOT/"records"`） | → 多根集合 |
| 子树分类 | `1993–2126`（bugs/episodes/reviews/tests/plans/improvement 六支） | → 按新落点重写：缺陷与事项在 `issues/`；计划、决策、评审、测试、改进件在批次目录；发布在 `releases/` |
| 引用面 | `2343–2350`（`reference_surface` 含 `ROOT/"records"`） | → 新目录集 |
| mock 编译 | `2424–2445`（`mock/records` 覆盖副本 `records/`；`{"records","README.md"}` 断言） | → 夹具目录与编译方式随新树重构 |
| 复发台账根 | `2847`、`2885` | → `issues/recurrence/` |
| 期望文件集与计划契约探针 | `2308–2366` 区域 | 核对后按需同步（测试文件集不变则不动） |
| 其余文案 | 其余 60+ 处 | 随迁移机械改指 |

**判据**：改后对「新树 + `_archive/` 冻结原文」两侧全绿；**归档件豁免规则单点声明**（冻结原文保留历史引用，不散落豁免）。

## 2. `tests/`（`test_lab_contracts.py` 51 处、`test_record_store.py` 11 处）

- `test_lab_contracts.py`：记录路径夹具与断言（`:196/215/240` 的 `ROOT/"records"/…`、`:246` 文案、`:257/275` reviews、`:346/390` plans）随新路径重写；「钉住门工具」的职责不变。
- `test_record_store.py`：参数化根目录夹具（`root/"records"`），预计无需改——与 `record_store.py` 默认根变更一并复核后定稿。

## 3. `schemas/` 六件（`bug-record`、`plan`、`recurrence`、`review`、`test-plan`、`test-run`）

描述文本内嵌 `records/` 路径逐条改指，例如：
- `bug-record.schema.json:5`：`…under records/bugs/.` → `…under issues/ (ISS-<YYYY>-<NNN>).`
- `bug-record.schema.json:74`：`records/bugs/recurrence/<class_id>.md` → `issues/recurrence/<class_id>.md`
- 其余：`records/reviews/… → reviews/…`；`records/tests/… → features/<batch>/testing/…`；`records/plans/… → features/<batch>/plan/…`；`records/improvement/… → features/<batch>/improvement/ 与 releases/`。
- **字段结构不变**；若启用统一编号，`bug_id` 的说明/pattern 改为 `ISS-<YYYY>-<NNN>`（见第 7 节决策点）。

## 4. `agents/evaluator.md`、`agents/release-governor.md`

- `evaluator.md:12`：`result records, `records/`.` → `result records, the improvement artifact paths.`
- `release-governor.md:12`：同上；`release-governor.md:20`：`records/bugs/recurrence/<class_id>.md` → `issues/recurrence/<class_id>.md`。

## 5. `evals/`

- `evals/public/AF-009.json`、`evals/public/inputs/AF-009.md`：所引 `records/` 路径改指新落点；用例语义不变。

## 6. 落地顺序（与批 4 原子）

1. 本规格评审通过 → 2. 评审包补齐逐字补丁 → 3. 批 4 同批落地（门更改 + 迁移 + 引用改指含机械改指与登记 + 检索索引重建）→ 4. `validate.py all` 全绿 + `doc_chain.py --self-test` + 全仓扫描未覆盖项归零。

## 7. 待拍板的两个决策点

1. **统一编号后的 `bug_id` 字段**：pattern/说明改为 `ISS-<YYYY>-<NNN>`（推荐，全仓单一编号族），还是保留字段名与旧格式、仅路径改指？影响 `validate.py` 的 `bug_id` 交叉校验与复发台账。
2. **归档件豁免的单点表述**：`_archive/` 内路径校验规则的落点（建议写在 `validate.py` 顶部常量区，单一位置）。
