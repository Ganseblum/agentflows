# 规格验收矩阵（spec/acceptance-matrix）

> 用途：把 `spec/method-spec.md` 的每条承诺映射到**会失败的具体检查**。右列是检查本体，
> 不是"已验证"的声明——状态列才表达当前结论，且只写机器可复现或人工门已发生的事实。
> 机器标尺状态以最近一次 `python3 tools/lab/validate.py all` 为准（版本史见 `CHANGELOG.md`）；
> 本文不维护通过次数快照，避免与台账漂移。

| 规格 | 验收方式（会失败的东西） | 标尺落点 | 当前状态 |
| --- | --- | --- | --- |
| S1 角色面 | 14 个角色文件存在、frontmatter name=文件名、SKILL 引用可解析 | `validate.py docs`、`validate.py manifests` | 绿 |
| S2 十步流程 | episode 落盘过编译（material 变更必带 `review_roundtrips`） | `validate.py artifacts` + episode schema | 绿（抽查可复核） |
| S3 委派契约 | 候选 diff 触碰保护门被拒；越界写入被 `check-diff` 拒绝 | `isolation.py check-diff`、`contracts.md` | 绿（/tmp 注入实验历史证据见台账） |
| S4 独立评审门 | 无 `review_roundtrips` 的 material episode 编译失败 | episode schema + `validate.py artifacts` | 绿 |
| S5 失败语义 | 三类语义文本在 contracts 单点成文（作者不自证/超预算重试=主会话 缺陷） | 人工评审 + episode 抽查 | 绿（文本）；注入演练未做（见待建标尺） |
| S6 记录体系 | 每类记录样例过 schema；坏记录（如引用断链）编译失败 | `validate.py schemas` + `artifacts` | 绿 |
| S7 改进环 | ~~未知/重复 `--case-ids` 退出 1；digest 对贴被 policy 拒；候选碰保护门被拒~~ | 原 `eval_runner.py` + `policy.py`（已删） | **机制已停用**（2026-10-12：改进三件套、发布记录与评测装置整线退役） |
| S8 确定性验证面 | 任一检查红则 `all` 退出非 0；CI 缺门则 `protected` 失败 | `validate.py all` + `.github/` | 绿 |
| S9 打包安装 | 生成树缺组件、与源面不一致或 sha256 对不上即 FAIL | `validate.py manifests`（新鲜度）+ `installed` | 绿（生成树与源逐字节一致；2026-10-22 `installed` PASS，0.12.0 快照） |
| S10 业务仪器 | ~~被测树含 seeds 即 fail-closed；缺 allowed-tools/隔离参数被大声拒绝~~ | 原 `seed_grader.py` 与 `evals/` 已删 | **已裁撤**（2026-10-12：用户拍板「保公开、裁业务」） |
| S11 文档交付链 | 契约文件存在且被 SKILL 引用；本目录自身即首个全链样例 | `validate.py docs`（引用存在性）+ 人工评审门 | 绿（成稿）/ 评审门未跑 |
| S12 宿主证书 | 声称"宿主 X 已验证"须能指到该宿主 evaluation 记录，否则编译/评审可判失败 | `validate.py artifacts` | 当前无任何宿主证书（诚实状态：live 证据均为端点健康类——claude 侧一词探测 3/3 与 AF-001×3 试水见 C12、codex 侧一词探测见 X1；采集装置已随评测装置裁撤） |
| S13 链条映射 | 链内相对链接与 schema 引用存在 | `validate.py docs` | 绿 |
| S14 评审桥 | 归档快照或被引发现不存在即 `artifacts` 失败 | `validate.py artifacts` | 绿（infinite-canvas 评审为活样例） |
| S15 诚实声明 | 状态/回归字段与声明强度不一致的记录被 `recurrence`/`report` 揪出 | `validate.py recurrence`、`report` | 绿 |

## 待建标尺（诚实缺口）

| 缺口 | 属于 | 关闭条件 |
| --- | --- | --- |
| crash/timeout 注入演练脚本化 | S5 | `/tmp` 一次性副本注入实验，证据落台账 |
| ~~用户侧收益基线（返工率/逃逸率）~~ | proposal OQ-1 | 业务尺子已裁撤，该口径暂无仪器来源（保留为开放问题） |
| 宿主证书第一份（Claude） | S12 | U-01 已解除（`docs/host-platform-facts.md` C12）；采集装置随 2026-10-12 评测装置裁撤——恢复仪器与否由用户决定 |
