# 变更日志

> 0.22.1 及更早版本的历史条目已移入 [docs/changelog-archive.md](docs/changelog-archive.md)（按原样保留）。
> 2026-10-30 按 T21 压缩为每版 ≤10 行；详细记录移入归档，原始提交历史可回溯。

## 0.24.0 — 2026-11-02

- 发布 0.24.0：并入 2026-10-30 收口与 2026-10-31 整改的全部已落内容。两棵工作树（主树的早期草稿 57 文件、worktree `fix/remaining-2026-10-31` 的后继版 100 文件）经逐行比对确认主树无独有内容后合为一份（`bb56cb1` 快进进 `main`）。
- 关闭「产品线完善」批与 T18–T22：`docs/product` 结论并入 `docs/design-decisions.md` §4、产品链与批次目录删除（原文 git `40147df`）；evaluations 留三归档五、16 条 office 记录汇总、评审快照按 schema 保持。
- 新增 **C27 模板骨架**判据（用户批准的门变更）：阶段文档与随插件模板的行级相似度 ≥0.85 即判红。此前把模板逐字复制成一条链**零发现**通过（形状判据全在模板自带的示例里），而真实批次 123 份文档相似度最高 0.41；补 3 条判别夹具（自测 154→157）、C27 的变异项为 M62（原自述写作 M61，2026-11-02 按 `mutate.py --check doc_chain_selftest` 逐字输出更正；M61 是既有的 C23 锚点）。模板侧配合改动：README 段落映射落点出厂为「—」（照抄不再免检 C1）、checklist 不留占位行、计划模板补 frontmatter 五必填与七列默认、验收编号方言统一、`M01-AC-01` 与 proposal §1.2 目标编号双向闭合。
- 门项数 11→12：`installed` 纳入 `all`（无本地安装打印 SKIP、不冒充通过；快照存在而漂移即判红）。实证根因是本机 11/11 全绿旁边挂着 `FAIL installed`——宿主仍在跑 0.23.0 旧快照，内含 2026-10-29 已裁撤的 `skills/improve` 与 4 个候选角色。publish/pre-push 早已排除该项，推送与发版时序不受影响。
- 交付面版本守卫（第 12 项门的一部分）：`agents/*.md` 与 `skills/agentflow/**` 内不得出现本插件版本族的字面量；全量 `x.y.z` 口径实测在模板小节号（`§1.4.3`）上有 60 处假阳性，故按 manifest 声明的主版本号判定，围栏与行内代码按引文豁免；SKILL.md 的宿主版本改指 `docs/host-platform-facts.md` Q1–Q6。
- 评估整改：修复 C5/C6 两条空转判据与写范围工具误报（3010→仅真实变更）；模板补齐目标承接表、清 C13 会话词、修决策表与埋点表头、补可选层说明与 hub/releases 骨架。
- 计数漂移与脚本口径收口：门 1–10（4 处）、README schema 计数改用标记、roles 五条链、repo-audit 补 D12、角色文件手抄 schema 计数改为以 schema 为准；publish/upgrade 缺 lint 依赖默认拦下（显式环境变量放行），删除三处死变量；contracts 明确 `task_id`/`baseline_revision` 适用于产出交付物的 worker。
- 角色面与 references 对齐代码事实：`bug-recorder` 的 `status: consolidated` 明确归再犯类清单、`test-executor` 的「更新注册表」改为「记缺口并交回」（与 `disallowedTools: Edit` 一致）、`reviewer` 严重度补 P3、三个只读角色的产物归属统一为 `## 产物归属` 节、`technical-director` 补返回字段与预算页脚；`review_tier` 载体改为评审记录、C13 豁免按逐文件清单真实描述、退役残留清除、`review-checklists.md` 接进 SKILL 路由表。
- 合并后在 `main` 复跑：`validate.py --list` 自报 12 项、其余 11 项 PASS（`installed` 待三端重装转绿）、`unittest` 260 OK、`doc_chain.py --self-test` 157/157、C27 负例复现（12 份模板逐字成链报 12 条 C27；只放 README 报 4 条 C1）、`check-write-scope.sh HEAD .` PASS、`doc_chain_live` 无 C27 命中。

## 0.23.0 — 2026-10-29

- 发布 0.23.0（`f73a4e9`）；并入「全面修正与瘦身」批已落内容。
- 第二段（改进环裁撤 / 凭据 pattern / C17 变异 / 定位即预算 / 对照实验 / 判据分册）随 2026-10-30 收口推送 origin/main（`bfd93ea`）。
- 两轮 findings 已修复，第三轮 delta 复审 L2 `approved`；详情见归档与批次 README。
