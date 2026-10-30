# 变更日志

> 0.22.1 及更早版本的历史条目已移入 [docs/changelog-archive.md](docs/changelog-archive.md)（按原样保留）。

## 未发布 — 2026-10-29

0.23.0 已发布（提交 `f73a4e9`，`publish.sh` 走完门禁与推送），但「全面修正与瘦身」批仍
部分在途：计划 19 个任务，发版时点 12 ☑ / 3 ◐ / 3 ☐ / 1 本期不做（现行值以
`docs/features/feature-2026-10-29-全面修正与瘦身/plan/PLAN-FIX-001.md` 看板为准）；第二轮
独立评审待跑，批结论上限 `partial`。本节承接其后续收尾（T15–T17 实施与两个评审门关闭）。

### 全面审查修复批（2026-10-29 下午，四路审查 → 修复）

对仓库做了一次全面审查（skills/模板、agents/schemas/examples、tools/tests、docs/记录四路并行
只读调查），随后按审查结论实施修复。`measurement: none`。要点：

- **门禁假绿路径修复（受保护面门变更，用户授权）**：opt-in 标记防摘除断言从「决策记录」
  一种推广到全部四族（`tools/lab/docchain/checks.py` 的 `decision_marker_presence_findings`，
  活树实测抓出并回写了 2 个旧批次 README 的散文式声明）；计划看板状态列改为按行所属表的
  表头就近解析、空状态单元格由静默跳过改为报错（`tools/lab/gate/plan.py`）；`record_date_of`
  接受小写 `z`（`tools/lab/gate/common.py`，此前小写时间戳让日期核对全部静默失效）；`--file`
  模式的 C25 收口检查改为按文件自身标记 opt-in（`tools/lab/docchain/cli.py`）。
- **门覆盖扩展**：`lint` 门纳入 `tests/`（顺带清掉 55 处死 import 等 65 项 ruff 发现与 1 处
  mypy 报错）；测试文件下限改用 AST 的 TestCase 归属判定（与 `counts.py` 同一方言）；
  run 记录的 `findings`/`flow_findings` bug-id 交叉检查接线（原三返回值无消费者）；
  examples 的用例注册表解析错误不再丢弃；`counts.py` 计数标记接入门（`docs` 项）；
  carrier-map 读取改 fail-closed。
- **评测装置残件裁撤**：删除 `tools/lab/trend.py` 与 `docs/trend.jsonl`（零消费者、真实语料
  上已抛异常而测试全绿）、`tools/review-cost-baseline.py`（宿主私有 DB 的一次性评测残留）；
  `protected-paths.txt` 与 `REQUIRED_PROTECTED_PATHS` 同步移除，新增防复活回归测试。
- **导航面时效回写**：0.23.0 发版后四处导航面（releases/todo、pending-test、features/README、
  index）按已提交事实回写；拍板口第 17/18 条与链内 Q-03 的状态脱节修正；0.20.0 版本口径统一
  （`git tag -l` 实证从未单独发布）；CHANGELOG 拆分——0.22.1 及更早移入
  `docs/changelog-archive.md`（179KB → 现行文件约 40 行）并加历史载体豁免。
- **角色与模板面**：test-planner/test-executor 的 schema 必填清单逐字对齐（此前把必填错标
  「可选」）；reviewer 补 `maxTurns` 与预算纪律（此前是唯一两者皆无的角色）；frontend-engineer
  补浏览器核实的可达机制与 fallback；doc_chain 命令两种互斥写法统一并注明 cwd 前提；
  模板编号断档/坏标题/悬空自检修复；repo-audit 铁律重编号；9 份预算纪律、5 处 provenance
  复述、6 处原型规则等重复纪律上收单点。
- **杂项**：episodes 2026-10-08→10-28 归档；测试重复覆盖与恒真断言收敛；mutate.py 登记
  快照覆盖边界（D9）；examples 正例的悬空 `evidence_ref` 改指真实评审记录。


## 0.23.0 — 2026-10-29

并入「2026-10-29 全面修正与瘦身」批的已落内容。`measurement: none`。

**该批仍在进行中**（发版时点看板 12 ☑ / 3 ◐ / 3 ☐ / 1 本期不做，共 19 个任务；现行值以
`plan/PLAN-FIX-001.md` 看板为准），本次升版只为让三端与源面一致——
这批改了 `agents/` 与 `skills/`，若不升版，同版本号下的内容与其他机器上的缓存会不一致。

- **判据与工具**：`tools/lab/gate/records.py`（+128）与 `tools/lab/validate.py`（+6）新增判据，
  另 7 处 gate / docchain 调整。
- **方法面**：`agents/reviewer.md` 精简约 68 行，检查清单外移为
  `skills/agentflow/references/review-checklists.md`；新增 `references/carrier-map.md`
  （载体归属表），`SKILL.md` 与 `document-chain.md` 同步引用。
- **记录面**：3 条 `ISS-2026-10-29-*`（均 `fixed-pending-review`）、`episodes/2026-10-29/`，
  以及 episodes 归档与 docs 的同步修改。
- **瘦身**：删除 `feature-2026-10-26-L3工作流增强/testing/agentflow-workflow/` 下 184 个证据文件
  （−14045 行），同步改该批 README 与计划摘掉引用；删除后 `doc_chain_live` 与 C23 证据在场仍绿。
- **发布方式**：`publish.sh`（门 → 推送 → Codex → ZCode）；Qoder 无 CLI，按
  `docs/host-platform-facts.md` Q6 手工同步缓存目录与登记表。

## 未发布 — 2026-10-29（该批已随 0.23.0 提交发布，以下为其工作树时点的原始记录）

全面修正 + 升级瘦身：四条「写了但执行不了」的规则变成会判红的判据，议程收成一个批次，
记录面的重复噪声退场。`measurement: none`（方法级改动，无仪器化业务对照）。
（历史口径说明：本节写作时该批为「经授权不提交、不推送、不重装」的工作树改动；其后已由
0.23.0 发版提交 `f73a4e9` 收编发布。）

- **议程归并**：10-25 / 治理批 / 欠账批的未完成收敛项并入
  `docs/features/feature-2026-10-29-全面修正与瘦身/`（18 行任务表），治理批计划置 `superseded`；
  四处导航面（`docs/features/README.md`、`index.md`、`docs/releases/todo.md`、三批 README）状态同步，
  不再并存三套「谁还没做」。
- **拍板口重新成为唯一入口**：`docs/PENDING-DECISIONS.md` 新增第 19…25 条（必读面取值、文档链默认档、
  剩余删档授权、角色合并、归属表核验形态、角色行数上限、拍板口移出与追加），
  10-25 批 §六 与本批提案 §4 的未关闭行逐条补条目编号；`AGENTS.md` 与 `document-chain.md` 各加一条
  「链内台账 / 拍板口」分工，消除两个「单一入口」互相覆盖。
- **门变更四条（受保护面，用户 2026-10-29 授权）**：① episode 的 `evidence_ref`/`ref`/`path`/`artifact`
  字段级路径必须真实存在，消失对象须写 `N/A: 理由` 或 `仓库@修订:路径`（裸 `N/A` 不豁免）——
  计划证据列自 C23 起有该判据而档案载体没有，实测 445 条字段值中 14 条悬空；
  ② `schemas/review.schema.json` 增 `review_tier`/`dispatch_errors` + 一条 `allOf`，
  「声明 L0 而无失败派发留痕」由 schema 与校验器两层各自独立判红（反证：任删一层仍红，两层都删即转绿）；
  ③ C18 归属家族扩射程——打标批次内「需用户抉择且尚未关闭」的台账行缺拍板口编号即判红，
  并新增「拍板口必须有独立标记声明行」断言（散文提及不算声明）；④ 任务状态字形→词映射双拷贝
  收为 `docchain/constants.py` 单一定义，`gate/plan.py` 导入同一份。门项数不变（11 项），判据号不新增。
- **载体归属表**：新建 `skills/agentflow/references/carrier-map.md`（23 行），核验并入 `validate.py docs`；
  `SKILL.md` 的「改一处就改另一处」同步义务退场，由断言取代人工记忆。首轮该表 6 行锚点是猜的、
  1 行指向未创建的文件，被自己的断言当场判红后修正。
- **记录面删除与引用改写**：L3 批 184 个原始证据件（1.2M）移出工作树，36 处引用先改写成
  `agentflows@6229a65:…` 再删（引用先改 → 门先绿 → 删 → 门仍绿）；`index.md`「L3 合并后修正」整节、
  `docs/PENDING-DECISIONS.md` 表头 8 段与表尾 27 行已闭合注记移出并留可解析出处；
  现行导航面的会过期手写计数改为「当日时点值 + 以实跑为准」。
- **未达成（如实）**：必读面四文件实测 606 行 / 39,439 字符（基线 663 / 42,652），
  验收值 ≤450 行未达成且该值本身未经用户拍板（拍板口第 19 条）；`document-chain.md` 判据细则拆分未做；
  `reviews/` 内部重复快照经实测是 `reviewed_docs` 判据的承载件，不能删，转为计划 T18 本期不做。
- **本批自纠记录**：`docs/issues/ISS-2026-10-29-拍板口改写中两处自述超出事实.md`——移出历史注记时
  连带摘掉 `agentflow 决策记录` 标记，`decision_gate` 当场转为「不检查所以绿」；
  另有一处把用户没选过的必读面值写成「已关闭」。两处均在本轮内改正并把「摘标记转绿」做成判据。
- 验证：`validate.py all` 11 项 PASS、`doc_chain.py --self-test` 132/132（基线 124）、
  `unittest` 194 OK（基线 178）、本批链 linter PASS、`installed` 按预期报漂移（未重装）。
