# feature-2026-10-09-结构改造 — 批次总览

- **目标**：按 `plan/structure-overhaul-plan.md` 把本仓改为 `youc-workflow-ai` 同族结构：去 `records/`、缺陷与事项统一 `ISS-` 编号、模板真文件化、`docs/` 收窄为「设计·指南·事实」。
- **实施计划**：`plan/structure-overhaul-plan.md` 第 4 节的批 0–5（已执行；过程件见本目录 `plan/`）。
- **文档链模式**：`轻量模式：无 spec/design 轨`（本批次仅 README + `plan/`；符合 document-chain.md 轻量模式条款，故未含独立 proposal/spec/design/reviews 文件）。
- **基线**：`plan/baseline-2026-10-09.md`（修订号与 `validate.py all` 原始输出）。
- **门变更**：批 3 的保护清单改动须经人工评审后随批 4 落地；逐项清单见 `plan/`。

## 执行记录

- 2026-10-09：批 0–2 完成——基线存档；`index.md`、`_archive/README.md`、`issues/`、`releases/`、`reviews/` 骨架与两条仓库纪律落地；模板拆为真文件（13+4 件，含清单）；方法文本与角色条款更新；`validate.py all` 全绿、`doc_chain.py --self-test` 38/38、运行树已重建。批 3 规格见 `plan/batch3-gate-change-spec.md`。
- 过程记录：模板单体删除后历史记录引用失解析（6 条缺陷记录），按「先保路径可解析」恢复为指针文件后校验回绿——该实例支持 3.6 的「单份文档不搬家式冻结/改指先登记」规则。
- 2026-10-09：批 3–5 完成——记录树迁移（107 件移动、40 件缺陷重编号 `ISS-2026-001…040`、273 处机械改指，映射表 `plan/migration-mapping.md`）；校验器/测试/夹具/全仓引用适配（`validate.py all` 10×PASS、self-test 38/38、检索库重建 94 条）；版本 0.9.0（五清单一致）+ CHANGELOG + 本批 episode；`records/` 空壳与 `.DS_Store` 已删除，audit/handoff 冻结进 `_archive/`；`installed` 漂移为预期（重装属用户侧）。
