# 变更日志

> 0.22.1 及更早版本的历史条目已移入 [docs/changelog-archive.md](docs/changelog-archive.md)（按原样保留）。
> 2026-10-30 按 T21 压缩为每版 ≤10 行；详细记录移入归档，原始提交历史可回溯。

## 未发布 — 2026-10-31

- 评估整改：修复 C5/C6 两条空转判据与写范围工具误报（3010→仅真实变更），补 3 条判别夹具（自测 154），变异 19/19 杀死；模板补齐目标承接表、清 C13 会话词、修决策表与埋点表头、补可选层说明与 hub/releases 骨架。
- 计数漂移收口：门 1–10（4 处）、README schema 计数改用标记、roles 五条链、repo-audit 补 D12、角色文件手抄 schema 计数改为以 schema 为准。
- 脚本统一 fail-closed：publish/upgrade 缺 lint 依赖默认拦下（显式环境变量放行），删除三处死变量；安装提示不再写死门项数。
- contracts 明确 `task_id`/`baseline_revision` 适用于产出交付物的 worker；todo.md 镜像回写 4 条已清偿缺陷。
- 新增 **C27 模板骨架**判据（用户批准的门变更）：阶段文档与随插件模板的行级相似度 ≥0.85 即判红。此前把 11 份模板逐字复制成一条链**零发现**通过（形状判据全在模板自带的示例里），而真实批次 123 份文档相似度最高 0.41；补 3 条判别夹具（自测 154→157）、变异项 M61 已杀死。模板侧配合改动：README 段落映射落点出厂为「—」（照抄不再免检 C1）、checklist 不留占位行、计划模板补 frontmatter 五必填与七列默认、`V-F1`/`V-1` 方言统一为 `V-01`、`M01-AC-01` 与 proposal §1.2 目标编号双向闭合。
- 门项数 11→12：`installed` 纳入 `all`（无本地安装打印 SKIP、不冒充通过；快照存在而漂移即判红）。实证根因是本机 11/11 全绿旁边挂着 `FAIL installed (49 errors)`——宿主仍在跑 0.23.0 旧快照，内含 2026-10-29 已裁撤的 `skills/improve` 与 4 个候选角色。publish/pre-push 早已排除该项，推送与发版时序不受影响。
- 交付面版本守卫（第 12 项门的一部分）：`agents/*.md` 与 `skills/agentflow/**` 内不得出现本插件版本族的字面量；全量 `x.y.z` 口径实测在模板小节号（`§1.4.3`）上有 60 处假阳性，故按 manifest 声明的主版本号判定，围栏与行内代码按引文豁免；SKILL.md 的宿主版本改指 `docs/host-platform-facts.md` Q1–Q6。
- 角色面自相矛盾与歧义收口：`bug-recorder` 的 `status: consolidated` 明确归再犯类清单（缺陷记录四值不变，照旧写会被校验器拒）、`test-executor` 的「更新注册表」改为「记缺口并交回」（与 `disallowedTools: Edit` 一致）、`reviewer` 严重度补 P3 并写明与缺陷记录四级的对应、三个只读角色的产物归属统一为 `## 产物归属` 节、`technical-director` 补返回字段与备选下限及预算页脚。
- references 与代码事实对齐：`review_tier` 载体改为评审记录（episode schema 无该字段）、C13 豁免改为逐文件清单的真实描述（`docs/features/**` 不在豁免面内）、退役残留清除（两条工作流、holdout 禁区、反馈环/评测用例、`docs/evaluations` 归档路径）、批次计数按 2026-10-31 实跑刷新、`measurement: none` 标明是书写口径而非记录字段、`review-checklists.md` 接进 SKILL 路由表。

## 未发布 — 2026-10-30

- 关闭「产品线完善」批：`docs/product` 结论并入 `docs/design-decisions.md` §4，产品链与批次目录删除（原文 git `40147df`）。
- 完成 T18–T22：evaluations 留三归档五、16 条 office 记录汇总、评审快照按 schema 保持、episode/CHANGELOG 收口。
- 已推送 origin/main（`bfd93ea`）；全量门 11/11、unittest 259、self-test 151/151、整门变异 60/60。

## 0.23.0 — 2026-10-29

- 发布 0.23.0（`f73a4e9`）；并入「全面修正与瘦身」批已落内容。
- 第二段（改进环裁撤 / 凭据 pattern / C17 变异 / 定位即预算 / 对照实验 / 判据分册）随 2026-10-30 收口推送 origin/main（`bfd93ea`）。
- 两轮 findings 已修复，第三轮 delta 复审 L2 `approved`；详情见归档与批次 README。
