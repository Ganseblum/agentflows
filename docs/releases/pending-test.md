# 待验收

> 规则：代码已落 ≠ 已验收。每一项要么标已验证（附验证方式与结果），要么显式写「未做 / 未验证」。
> 只记录当前仍待人工验收的批次；已验收批次的历史见 git 历史与 `../../CHANGELOG.md`。

## 待人工验收

| # | 变更 | 验证方式（可复现的命令或步骤） | 结果 |
| --- | --- | --- | --- |
| 1 | 首次接入（Init）章节 + 表达与沉淀纪律（`skills/agentflow/SKILL.md`、`AGENTS.md`） | 阅读两处新增条款：Init 约定（当时为五项；现为六项，见第 7 行）与「面向人的输出白话优先」；重装后由用户在新项目试用 | 条款在盘已核（2026-10-19：SKILL.md Init 当时的五项与 AGENTS.md 表达纪律条款 grep 在场）；待用户在新项目试用（用户阅读向，仓内不可闭环） |
| 2 | 接入 / 触发面修复 + 模板角色目录化 + 典型案例 | 重装后在新目标仓发起一个 feature 任务，观察：①先问产品前沿 ②落点建 `<repo>-workflow-ai/` 枢纽 ③对 feature 目录 `doc_chain.py` PASS；另抽查 `skills/agentflow/templates/feature/` 为角色目录命名 | 静态项已达成（2026-10-20：`installed` PASS；模板目录为 design/{be,fe,qa,ui}、plan、proposal、spec/{be,fe,qa,ui}）；端到端新仓 feature 任务观察仍待用户侧发起，判为「静态达成 / 端到端待用户」 |
| 3 | 追溯闭环批 0.13.0 的门变更（C22 目标承接闭环 + C23 证据在场 + 记录契约 `disposition`，提交 `861b6ef`） | ① 在真实新批次立项当天只打 `agentflow 目标承接` 标记、不写承接表，跑 `python3 tools/lab/doc_chain.py <批次目录>`，应报「标记启用却没有承接表」；② 把某已完成任务从承接表删掉，应报「孤儿任务」；③ 把某任务行的证据只写 `/tmp/x.txt`，应报 C23；④ 拿一个未打标记的历史批次跑同命令，确认不产生 C22 findings；⑤ 读 `docs/PENDING-DECISIONS.md` 的八列，判断是否真的能凭它拍板（不用回翻来源） | ①②③④已由 `tools/lab/doc_chain.py --self-test` 与 `tests/test_doc_chain.py` 的 `GoalTraceabilityEvidenceTests` 实跑覆盖（self-test 110/110、92 tests OK），⑤属阅读向判断，须用户本人确认（仓内不可闭环）；另：7 个变异存活项的逐项处置、以及「锚点漂移应做成机器判据」两项已分别登记为 `docs/issues/ISS-2026-10-23-变异存活项长期无逐项处置.md` 与 `docs/issues/ISS-2026-10-23-变异语料锚点漂移致判据不可观察.md` 的备注，本批不做 |
| 4 | 宿主级接入（Host Init）0.14.0：`skills/agentflow/references/hosts.md`、`skills/agentflow/templates/host/`、SKILL 的「宿主级接入」节 | ① 重装插件后按 `hosts.md` 做 dry-run，确认打印 `realpath`、托管块、块外变动；② 用户当次确认后写入真实 `~/.zcode/AGENTS.md`（先备份），按第 6 条做三项校验；③ 新开 ZCode 会话，让宿主逐字复述块内首行 `## Agentflow 全局规则（托管块，勿手改）`；④ 把结果回写 `docs/host-platform-facts.md` H1 | 未做：真实宿主写入与加载验证须用户当次确认并在新会话执行；仓内只完成协议文本、副本演练与生成树重建，不得记为已验收。0.14.0 已被 0.15.0 取代，安装面以第 5 行复核为准 |
| 5 | 测试链路 Ego Light 切换批 0.15.0：Ego Light 执行路线、真实数据优先与 `## 数据来源` 节、用例来源/测试功能/实际结果列、bug 回归用例与 `regression_status` 状态联动（`skills/agentflow/references/test-records.md`） | ① 重装插件（本地 marketplace → `packaging/runtime`）后 `python3 tools/lab/validate.py installed` 转绿（0.15.0 快照逐文件一致）；② 新会话对真实 UI 用例跑一轮 test-executor，确认先执行 `ego-browser skill`、用 ego-browser 操作、证据落 `evidence/`；③ 按 `skills/agentflow/templates/testing/plan.md` 建含 `## 数据来源` 节的计划并跑 `python3 tools/lab/validate.py artifacts` 确认不红；④ bug 链走通一遍：investigator 产出 Ego 操作序列 → fixer 修前复现修后重跑 → 回归用例 pass 后按联动核对 bug 状态前进 | ① 已达成（2026-10-25：宿主缓存已有 0.15.0 快照，`python3 tools/lab/validate.py installed` → PASS）；②③④ 未做：端到端 Ego Light 实跑与 bug 回归链走查须用户侧执行，不记为已验收。仓内完成契约/角色/模板/示例改动与门验证（当前 `validate.py all` 项数以 `--list` 自报为准、`unittest` 实跑为准、`doc_chain.py --self-test` 实跑为准，版本与计数不在此处固化为字面量） |
| 6 | 评测整改批 0.20.0（提交 `51e6754`+`86b7105`，两者均已在 `main` 历史中）：整改状态列 / 评审能力分级 L0–L2 / 表达面收敛 / 四脚本 `.venv` 探测 / 改进环首份真实记录 | ① 重装双端后 `validate.py installed` 转绿（合并与生成树重建已完成）；② 新会话确认 SKILL 第 8 步要求记录 `review_tier`（阅读向，须用户确认）；③ 删掉仓内 `.venv` 后跑 `validate.py lint`，应回到 `FAIL lint`（fail-closed 未被削弱）；④ 用真实委派恢复后的第一轮评审，验证 L2 档能正常落 `review_tier: L2` | **部分达成**：2026-10-28 已并入 `main`（合并提交 `26988a4`；合并后 `validate.py all` 11/11 PASS，unittest 172 OK），但**未推送、未重装宿主**——2026-10-28 实测 `validate.py installed` 报「无 0.21.0 快照」（源面已升至 0.21.0），已装版本停留 0.19.3。①②④ 待用户授权发布后执行；③ 已在 `/tmp` 副本实证（坏 venv 与无 venv 均 EXIT=1，见批次 `testing/agentflow-eval/evidence/T07-venv-probe.txt`），真实树删 `.venv` 未做（会破坏本机 lint 基线）。不记为已验收 |
| 7 | 工程基线吸收批 0.21.0（提交 `d5b52ce`+`256ea64`，均已在 `main` 历史中）：工程基线模板与 Init 六项 / 后端数据与配置核对 / 原型可点性 / 测试设计三维 | ① 重装后 `validate.py installed` 转绿（生成树已重建，`manifests` 门 PASS）；② 新目标仓接入时确认 Init 确实问到工程基线并落入口路径；③ 按 `templates/engineering/baseline.md` 在一个真实仓落一份基线，检查每条 `<填>` 是否都有事实来源 | **未做**：原四项已完成独立评审；FE 增量实现与门验证完成（干净副本与共享树均 `validate.py all` 11/11 PASS），但 **FE 增量独立评审未运行**（用户拒绝派发子代理，T12 ⚠），不写成已批准。见批次 `testing/agentflow-baseline/evidence/`；2026-10-28 已并入 `main`，未推送、未重装宿主。①②③ 待发布与真实接入后执行，不记为已验收 |

## 已验收（历史，2026-10-19/20）

- 全仓中文本地化：`installed` PASS，agents/skills 正文与 `description` 均为中文（2026-10-20）。
- 结构文档登记：`index.md` 与 `tools/lab/README.md` 一致，`manifests` PASS（2026-10-19）。
- 发布待办 / 待验收 / 待拍板三件启用：`artifacts` PASS，拍板口走通（2026-10-19）。
- 端点复测与第一次改善闭环试水：探测 3/3，试水 3 轮 21.7 分钟（成本未落盘，装置已裁撤）。
- `check-write-scope.sh` 的「.」修复：`HEAD .` → OK exit 0；`HEAD skills` → FAIL exit 1（ISS-2026-10-10-写范围dot-scope静默不匹配）。
- 精简批 / 瘦身批二期：`validate.py all` PASS，unittest 78 OK，业务残留零命中。

## 未做与残余

- `schemas/*.schema.json` 内部 description 字段未汉化——已拍板关闭：不翻（EP-2026-10-10-002）。
- 试水成本未落盘——随 2026-10-12 评测装置裁撤失去对象关闭（观测缺口留存）。
