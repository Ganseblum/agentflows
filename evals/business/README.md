# 业务评测切片（evals/business）

这个目录放的是「业务任务」评测用例：让被评测的 agent 去读一个真实企业产品的文档集（只读快照），把文档里的缺陷报出来，再由确定性评分器对着事先埋好的种子清单算命中率。

和 `evals/public/` 的区别：`evals/public/` 测的是流程决策与权限边界，输入是脱敏小文本；`evals/business/` 测的是在真实业务文档上做审查，输入是只读快照加一份任务简报。

## 目录布局

| 路径 | 内容 |
| --- | --- |
| `BT-001.json`、`BT-002.json`、`BT-003.json` | 三个用例的用例文件（机器读的契约） |
| `inputs/BT-001.md`、`inputs/BT-002.md`、`inputs/BT-003.md` | 给被评测 agent 看的脱敏任务简报 |
| `seeds/BT-001.seeds.json`、`seeds/BT-002.seeds.json`、`seeds/BT-003.seeds.json` | 抽象化种子清单（评分答案键，路径用中性符号） |
| `README.md` | 本文件 |

三个用例的公共设定：`slice` 都是 `business-doc-review`；`holdout` 都是 `false`；`repeat_count` 都是 3；`target_id` 都是 `aiwork-workflow-ai`；`target_pin` 都是同一个 40 位全 sha，把快照钉死在某个提交上。

| 用例 | 任务 | 文档集范围 | 种子条数 |
| --- | --- | --- | --- |
| `BT-001` | 种子缺陷文档审查 | feature-A 的 4 份文档 | 3 |
| `BT-002` | 内部矛盾需求审查 | feature-B 的 5 份文档 | 3 |
| `BT-003` | 跨文档一致性核查 | feature-C 的 3 份文档 | 3 |

## 用例契约

用例文件用 `skills/improve/references/business-case.schema.json` 校验（Draft 2020-12）。它在公共评测用例契约（`eval-case.schema.json`）的字段之上，新增了业务字段：

| 字段 | 含义 | 校验方式 |
| --- | --- | --- |
| `target_id` | 目标企业仓的代号 | 只校验结构，不查仓库是否存在 |
| `target_pin` | 目标仓的提交全 sha，正则 `^[0-9a-f]{40}$` | 只校验格式 |
| `target_docs` | 本次要评审的文档，元素是快照相对的中性路径 | 只校验结构，不查文件是否存在 |
| `seeds_ref` | 本仓内的种子清单路径 | 只校验结构，不查文件是否存在 |
| `findings_contract` | 被测 agent 要写出的 findings 工件的位置与字段 | 取值固定，见下一节 |
| `grading` | 判定阈值，目前只有 `min_seed_recall`（0 到 1） | 数值范围 |

`target_docs`、`target_pin`、`seeds_ref` 只做结构校验，是刻意的：这套校验跑在公开仓里，不能因为企业快照不在本机就报错，也不能把企业路径拉进公开面。

## findings 产出契约

被测 agent 在本次运行的工作目录下写出：

```text
findings/<case_id>/rep-<重复序号>/findings.json
```

内容形如：

```json
{
  "schema_version": 1,
  "case_id": "BT-001",
  "findings": [
    {
      "path": "docs/features/feature-A/spec/be/spec-backend.md",
      "issue": "问题描述",
      "evidence": "文档原文的逐字引文"
    }
  ]
}
```

`path` 是快照相对路径；`findings` 允许为空列表。三个用例的简报里都写明了同样的契约。

## 种子清单与评分语义

种子清单形如：

```json
{
  "schema_version": 1,
  "case_id": "BT-001",
  "seeds": [
    {
      "seed_id": "BT-001-S1",
      "doc_ref": "docs/features/feature-A/design/be/tech-design-backend.md",
      "category": "terminology-ambiguity",
      "description": "缺陷的抽象描述，不含企业原文",
      "strategy": {
        "type": "path_and_anchor",
        "anchors": ["示例锚点-替换成打种时写入的 token"],
        "mode": "any"
      }
    }
  ]
}
```

评分语义（先冻结，评分器按这个实现）：

- 一条种子命中，当且仅当存在一条 finding 同时满足两点：finding 的 `path` 以该种子的 `doc_ref` 结尾，且 `issue` 或 `evidence` 里按字面包含该种子 `anchors` 里的至少一个。
- 锚点在两字段内出现即可命中：`issue` 与 `evidence` 之间以换行分隔，锚点跨字段拼出来不算命中。
- 锚点匹配是宽松的字面子串匹配，评分只看命中与否、不计精度（同一处缺陷换一种措辞写，判定不变）；这是已知局限，不视为评分缺陷。
- `mode` 目前只有 `any`；未知的 `strategy.type` 一律按失败处理（fail-closed），不猜。
- 命中率 = 命中种子数 / 该用例种子总数。`accepted` 取「命中率 ≥ 用例的 `grading.min_seed_recall`」。
- 命中不了任何种子的 finding 记为 unmatched，只记录、不扣分——真实文档里本来就可能有种子之外的缺陷。

三个用例各 3 条种子，阈值都是 `0.5`，因此「至少命中 2 条」才算通过。

种子类别分四类，前两类是本期必须覆盖的测量面：

| 类别（slug） | 中文名 | 测什么 |
| --- | --- | --- |
| `terminology-ambiguity` | 术语歧义 | 行话有没有就地说明（表达纪律） |
| `cross-document-value-mismatch` | 跨文档值不一致 | 同一约束在多份载体里复述时是否同步（载体扫描） |
| `intra-document-contradiction` | 文档内自相矛盾 | 同一份文档前后是否一致 |
| `table-cell-not-self-contained` | 表格单元格不自包含 | 表格单元格能不能单独读懂（表达纪律） |

## 打种约定（快照准备，配方只留本地）

公开仓里的种子用中性路径；快照准备时把真实 feature 目录改名成 `feature-A`、`feature-B`、`feature-C`，中性路径在快照内因此真实存在。真实目录名与中性符号的对应关系只留本地，不进公开仓。

确定性的要求：

- 每条种子的 `anchors` 都必须能在打种后的目标文档里按字面找到；第一个 anchor 是打种时逐字写入的主形态，其余是同一处置的等价写法（例如带不带空格）。
- anchor 在打种后的快照里只能出现在打种位置。打种配方要用 grep 自查：某个 anchor 若在目标文档的其他地方也出现，判定就不再确定，必须换 token。
- 跨文档类种子，`doc_ref` 指向取值偏离其余载体的那一份文档；简报也要求被测 agent 把这类 finding 记在越界方名下，两边口径一致。
- 术语歧义类种子，anchor 就是打种时引入的那个未定义说法本身。
- 打种只改文档内容，不改目录结构；HEAD 保持等于 `target_pin`（脏树式打种），重建方式 = 检出 pin 后重放打种补丁。

## 脱敏边界

| 位置 | 内容 |
| --- | --- |
| 进公开仓 | 用例文件、脱敏任务简报、抽象化种子清单（中性路径）、本文件 |
| 只留本地 | 企业文档原文；打种补丁与配方；pin 快照本体；中性符号到真实路径的映射；raw 结果、progress 日志与 findings 工件 |

简报只描述任务与产出契约，不抄企业文档原文，不含内部主机名与内部链接。

## 怎么校验

本套件的结构校验挂在仓库的确定性检查里：

```sh
python3 tools/lab/validate.py all
```

这套校验已接进 `validate all`：`evals/business/` 走 `business-case.schema.json` 分支，`validate.py evals` 校验三个用例与三个种子清单，并检查 `input_ref`、`seeds_ref` 在仓内可解析、每条种子的 `doc_ref` 属于本用例的 `target_docs`、`strategy.type` 是评分器已实现的类型。`target_pin`、`target_docs` 指向的目标是否存在仍不检查——快照不在公开仓里。
