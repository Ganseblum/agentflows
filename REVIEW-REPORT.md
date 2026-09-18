# Agentflow v0.6.0 全面审查报告

> **[2026-09-17 已被取代]** 本报告为早期评审会话的产物，多条论断已过时（episode schema、CI、argparse、判断词、"repair once" 措辞等——详见 [CONSOLIDATED-REVIEW-REPORT.md](CONSOLIDATED-REVIEW-REPORT.md) 附录 A）；其有效的 "P0/P1/P2 优先级清单" 已被该合并报告吸收并推进。本文件仅作历史参考保留。

> 审查日期：2026-09-17  
> 版本：v0.6.0  
> 范围：缺陷、架构、逻辑、自闭环、升级、归纳、合理性

---

## 一、整体判断

**这是一个设计精良的"规范框架"，但治理是声明式的而非强制执行的。** 架构自洽、契约完备，但在"实际怎么运作"层面存在多处 gap。

**一句话总结：这是一份写得很好的宪法，但没有法院和警察。** 设计的自洽性很高，但执行层的强制力几乎全靠 prompt 遵守。要从设计文档变成生产系统，需要把部分 gate 从"告诉你应该做"改成"你不做就报错"。

---

## 二、缺陷 (Defects)

### 2.1 代码级缺陷

| 问题 | 位置 | 严重度 | 详情 |
|------|------|--------|------|
| **God Object** | `tools/lab/validate.py` | 🔴 高 | 1973 行，承载 schema 验证、frontmatter 解析、plan/bug/review/recurrence markdown 校验、manifest 校验、安装对比、CLI dispatch 全部职责。无模块拆分，维护风险高 |
| **argparse choices 重复** | `tools/lab/validate.py` | 🟡 低 | `"docs"` 在 choices 列表中出现两次，copy-paste 痕迹 |
| **schema 重复定义** | `evaluation-result.schema.json`、`release-record.schema.json`、`policy.py` | 🔴 高 | 8 个指标 (`acceptance_rate`、`first_pass_review_rate` 等) 在三个文件各自定义，无共享 `$ref`，容易漂移 |
| **内联重复** | `evaluation-result.schema.json` | 🟡 中 | 内联重写了 `adapter-case-result.schema.json` 的字段，没有用 `$ref`，形成隐式耦合 |
| **episode schema 漏洞** | `skills/improve/references/episode.schema.json` | 🟡 中 | `provenance` 字段是无类型 `object`，没有 `additionalProperties: false` 或属性约束，是校验漏洞 |

### 2.2 数据契约缺陷

| 问题 | 严重度 | 详情 |
|------|--------|------|
| **manifest description 不一致** | 🟡 低 | `plugin.json` 说 "host-native multi-agent development"，`.claude-plugin/plugin.json` 说 "Run host-native development"，`.codex-plugin/plugin.json` 说 "Run host-native multi-agent" |
| **manifest 版本类型不一致** | 🟡 低 | `marketplace.json` 顶层 `version` 是整数 `1`，其他都是字符串 semver。校验器恰好跳过了顶层（通过 `plugins[0]` 指针），所以没报错 |
| **manifest license 缺失** | 🟡 低 | `.claude-plugin/plugin.json` 和 `.codex-plugin/plugin.json` 缺少 `license` 字段，只有 ZCode manifest 声明了 MIT |
| **review schema 的 findings 不验证 bug_id 存在性** | 🟡 中 | 跨文档校验只在 `validate.py` 运行时做，不是声明式的，schema 层无法表达 |

---

## 三、架构问题

### 3.1 做得好的

- **12 个角色读写边界清晰**：author 不能自审，reviewer 独立，artifact-ownership 矩阵明确
- **三层防护体系**：`protected-paths.txt`（声明）+ `isolation.py`（隔离）+ `validate.py`（校验）
- **自定义 JSON Schema 验证器**：零依赖实现 Draft 2020-12 大部分关键字
- **业务切片隔离设计**：4 位置 isolation + 快照只读 + 脏树打种 + 每次调用后 git diff 摘要复检
- **provenance 字段**：区分"Agentflow 的问题"和"session 自己的问题"，避免改进循环被噪声污染

### 3.2 架构薄弱点

| 问题 | 影响 | 严重度 |
|------|------|--------|
| **角色 prompt 是 skeleton** | Evaluator 仅 18 行、Feedback Analyst 无输出 schema、Candidate Engineer 边界遵守全靠 prompt | 🔴 高 |
| **ZCode 无 host adapter** | `host_adapter.py` 只支持 codex/claude，作为主要目标的 ZCode 反而没有运行时适配 | 🔴 高 |
| **纯 prompt-based 治理** | 整套体系依赖模型"遵守"，而非"强制"——角色说独立就独立，说 fail-closed 就 fail-closed | 🔴 高 |
| **maxTurns 声明但不验证** | `AGENTS.md` 自己承认 "declared but unverified"，预算纪律全靠 prompt 遵守 | 🔴 高 |
| **无跨角色累计预算** | 整个工作流可以无限燃烧 turns | 🟡 中 |
| **check-write-scope.sh 脆弱** | `set -eu` + 空数组展开，依赖 bash 版本 | 🟡 低 |

---

## 四、逻辑问题

### 4.1 工作流逻辑

| 问题 | 严重度 | 详情 |
|------|--------|------|
| **Bug 生命周期有空档** | 🔴 高 | fixer → recorder 之间没有强制状态过渡保证。fixer 不能标记 `fixed-pending-review`，recorder 也不验证 fix 质量就写状态 |
| **"小改动"无判定标准** | 🔴 高 | `SKILL.md` line 83 定义了"small change"但 supervisor 有动机滥用此例外来规避 review |
| **Review-repair 循环次数歧义** | 🟡 中 | "repair once" 指一轮还是无限次 reopen？总 cycle time 无上限 |
| **"相同原因"无程序化判定** | 🟡 中 | "双次失败停止"规则中，不同报错但同一根因不算匹配，无法自动化 |
| **Plan "已关闭"标记是文本** | 🟡 低 | 没有验证关闭是否真的有实际解决方案，字符串匹配即可 |
| **架构门触发条件主观** | 🟡 中 | "risky work" 是主观判断，容易被跳过，没有客观触发条件 |

### 4.2 评测逻辑

| 问题 | 严重度 | 详情 |
|------|--------|------|
| **Seed Grader 纯子串匹配** | 🟡 中 | `anchor in text` 已知产生假阳性，无语义匹配、无 embedding、无 LLM-as-judge |
| **核心指标是模型自报的** | 🔴 高 | `accepted`、`unnecessary_delegation` 等无法交叉验证，模型说 accepted 就是 accepted |
| **first_pass_review 是自报的** | 🟡 中 | 保留自报值但用 evidence_refs 标注，本质上还是信任模型 |

---

## 五、自闭环 (Self-consistency)

### 5.1 契约层自闭环 ✓

- 所有记录有 schema → schema 有 validator → validator 有 regression test
- 5 个 manifest 版本一致性有 `validate manifests` 保护
- 文档-代码一致性有 `validate docs` 保护
- protected gate 有 `validate protected` 保护（必保集合不会悄悄被 trim）
- 测试目录有 `EXPECTED_TEST_FILES` 声明式内容断言（防 import-time 攻击）

### 5.2 运行层自闭环 ✗

| 声明 | 现实 | 差距 |
|------|------|------|
| "Reviewer 独立审查" | 同一上下文，prompt 说独立就独立 | 无进程隔离、无工具隔离 |
| "Fail-closed" | 只有 `seed_grader.py` 真正 fail-closed（exit 2） | 其他组件 log 后继续 |
| "Deterministic checks" | `validate.py` 是确定性的 | 但依赖文件处于预期状态，无运行隔离 |
| "Governed improvement" | 候选者决定改保护文件 | 只有事后 `check-diff` 能发现 |
| "maxTurns 限制" | host 不验证 | 等于没有预算控制 |

### 5.3 改进循环自闭环 ✗

- 所有 CHANGELOG (0.3.2 → 0.6.0) 都标注 **"Development release: no baseline/candidate evaluation evidence"**
- improve 循环从未真正完成过：baseline → candidate → eval → decision
- 业务切片 smoke 实跑被 3 个 P0 阻塞（U-01 可信端点、U-02 权限档、U-03 快照放置）

---

## 六、升级机制 (Improvement/Upgrade)

### 6.1 设计完备

- 4 种 promotion mode：proposal / human-gated / canary / automatic
- 版本 + 回滚策略清晰（rollback_to = parent_version）
- Protected gate 防候选者自改评分标准
- Recurrence escalation 自动触发 re-consolidation

### 6.2 实际缺口

| 缺口 | 影响 |
|------|------|
| canary/automatic 模式未实现 | README 自己承认 "intentionally pending" |
| 没有完成过完整的 improve 循环 | 所有版本都是 "development release" |
| 业务切片 smoke 被阻塞 | U-01/U-02/U-03 三个 P0 未决 |
| 发布完全人工 | 5 个 manifest 手动同步版本，`release-governor` 只返回决策不对接安装 |
| 回滚机制未验证 | 只定义了 rollback_target，没有实际回滚演练 |

---

## 七、归纳机制 (Induction)

### 7.1 设计优点

- **Recurrence ledger 是好设计**：class_id + occurrence + consolidation + escalation
- **tier 是 derived 而非 declared**：`single/recurred/escalated` 由版本推导，不是手标
- **escalated 标记**：新版复发自动触发 improve-loop 升级
- **consolidated_in**：记录哪个 release 吸收了这个失败类

### 7.2 实际缺口

| 问题 | 影响 |
|------|------|
| 只有一条 ledger 记录 | `unverified-behavior-claims`，样本太少，无法验证机制 |
| consolidation 全靠人工判断 | 没有自动化建议或阈值触发 |
| 无跨仓 recurrence 归纳 | 只能归纳 Agentflow 自身的问题，无法归纳业务仓的失败模式 |
| 无 failure class 聚类算法 | 需要人工指定 class_id，无自动归类 |

---

## 八、横向能力缺失

| 缺失领域 | 现状 | 影响 |
|----------|------|------|
| **CI/CD 集成** | 无 GitHub Actions，无 pre-commit hook | 所有校验靠手动运行，合入门控为零 |
| **安全扫描** | 无 SAST、无依赖漏洞扫描、无密钥检测 | Security 只是 reviewer 的一个 prompt checklist |
| **测试生成** | 无测试角色，无自动 scaffolding | 回归测试靠实现角色"记得加"，无 revert experiment |
| **Lint/格式化** | 实现角色不跑 linter，reviewer 也不强制 | 代码风格无保障 |
| **文档生成** | 无文档角色，无 API docs 生成 | 文档与代码同步靠人工记忆 |
| **可观测性** | `latency_ms` 采集但不导出，无监控、无告警 | 无法追踪 agent 表现趋势 |
| **通知系统** | 评估失败、recurrence 升级无通知 | 人类无法及时介入 |
| **ZCode host adapter** | `host_adapter.py` 只支持 codex/claude | 作为主要目标的 ZCode 反而没有运行时适配 |

---

## 九、纵向能力单薄

| 薄弱点 | 详情 |
|--------|------|
| **Evaluator 角色** | 仅 18 行 prompt 骨架。"contamination risk" 未定义、如何检测未说明、无操作指引 |
| **Release Governor** | 只返回决策，不对接安装/回滚机制，决策可被人类忽略 |
| **Feedback Analyst** | 无反馈收集工具、无结构化摄入管道，输出无 schema，"clusters" 无存储格式 |
| **Candidate Engineer** | 边界遵守全靠 prompt，`check-diff` 是事后检测，无文件系统级隔离 |
| **Episode 记录** | schema 存在但缺关联——没有链接到代码变更、角色决策、检查结果 |
| **Seed Grader** | 纯子串匹配，已知产生假阳性，无语义匹配能力 |
| **评测自报告** | 核心指标是模型自己报的，无法交叉验证 |
| **Schema Validator** | 缺少 `dependencies`、`patternProperties`、`unevaluatedProperties`、远程 `$ref` 等 |

---

## 十、合理性评估 (Reasonableness)

### 10.1 合理的设计决策

1. **Markdown hybrid plan** —— 人类可读 + 机器可校验，吸收了 aiwork 的 board model，frontmatter 做机器信封、body 做执行回写面
2. **protected-paths.txt 作为单点真理** —— 候选者不能改自己的评分标准，`isolation.py check-diff` 从可信源读名单
3. **provenance 字段** —— 区分 "agentflow" / "session-artifact" / "user-input" / "external" / "undetermined"，避免改进循环被噪声污染
4. **recurrence 的 derived tier** —— `single/recurred/escalated` 由版本推导，不是手标，杜绝"手工升级"
5. **fail-closed 评分器** —— 未知策略报错不猜，exit code 2 区分"失败"和"零分"
6. **business 切片的脱敏边界** —— 公开仓只放中性路径 + 抽象种子，真实路径只留本地
7. **脏树式打种** —— HEAD 保持 = pin，重建 = checkout + 重放 patch，可复现
8. **测试目录声明式内容断言** —— 防 import-time 攻击（`tests/<subdir>/` 替换 pinned test）

### 10.2 值得商榷的决策

1. **纯 prompt-based 治理** —— 整套体系依赖模型"遵守"，而非"强制"。角色说独立就独立，说 fail-closed 就 fail-closed
2. **maxTurns 声明但不验证** —— 等于没有预算控制，`AGENTS.md` 自己承认这一点
3. **God object validate.py** —— 1973 行的单文件，维护风险高，应该拆分
4. **improve 循环从未实际运行** —— 所有版本都是 "development release"，没有真正产出 baseline/candidate 对照证据
5. **核心指标自报告** —— `accepted`、`unnecessary_delegation` 等依赖模型自觉，无交叉验证
6. **ZCode 优先但无 adapter** —— README 把 ZCode 列为首要目标，但 host_adapter 不支持

### 10.3 架构一致性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 契约一致性 | ★★★★★ | schema + validator + regression test 三位一体 |
| 命名一致性 | ★★★★☆ | 5 个 manifest 的 description 不一致 |
| 状态机一致性 | ★★★★☆ | bug/plan 状态转换有 schema 约束，但运行层无强制 |
| 隔离一致性 | ★★★★☆ | 4 位置 isolation 设计完备，但依赖 prompt 遵守 |
| 文档-代码一致性 | ★★★★★ | `validate docs` 自动检查，第一次运行就发现了真实 drift |
| 版本一致性 | ★★★★★ | `validate manifests` 强制 5 个 manifest 一致 |

---

## 十一、改进优先级建议

### 🔴 立即修（影响可信度）

1. **拆分 `validate.py`** → 独立模块（schema_validator、frontmatter_parser、markdown_validators、manifest_checker）
2. **合并重复指标定义** → 单一 `$ref` 源，消除 `evaluation-result.schema.json`、`release-record.schema.json`、`policy.py` 的三处定义
3. **给模糊概念加可判定标准**："小改动"、"risky work"、"相同原因"——当前全靠主观判断
4. **修复 argparse 重复 `docs`** —— 虽然是低优先级，但是明显的 copy-paste 痕迹
5. **补 episode schema 的 provenance 约束** —— 当前是无类型 object，是校验漏洞

### 🟡 短期补（补上明显缺口）

6. **Evaluator / Feedback Analyst 角色补操作细节和输出 schema** —— 当前是 18 行骨架
7. **Bug 生命周期补 `fixed-pending-review` 过渡 + 质量验证** —— fixer 和 recorder 之间有空档
8. **添加 GitHub Actions CI** —— 至少跑 `validate.py all` + `unittest`
9. **Episode schema 补关联字段** —— 链接到代码 diff hash、角色列表、检查结果引用
10. **ZCode host adapter** —— 作为首要目标平台不应缺失
11. **核心指标交叉验证** —— 不能只依赖模型自报

### 🟢 长期建（从规范到可执行）

12. **把声明式 gate 改为工具强制执行** —— reviewer 命令必须被跑 → 加校验
13. **完成至少一次完整的 improve 循环** —— baseline → candidate → eval → decision
14. **加可观测性和成本追踪 dashboard** —— latency_ms 当前采集但不导出
15. **安全扫描 / lint / 测试生成集成** —— 横向能力补齐
16. **发布自动化** —— manifest 同步、changelog 生成、安装测试
17. **Seed Grader 语义匹配能力** —— 从纯子串匹配升级到 embedding/LLM-as-judge

---

## 十二、总结

Agentflow v0.6.0 是一个**精心设计的规范框架**，在"应该怎么运作"这个层面思考深入：

- 契约驱动（schema + validator + regression test）
- 防护完备（protected-paths + isolation + check-diff）
- 改进循环设计完整（evidence → hypothesis → candidate → eval → decision）
- 业务切片隔离创新（4 位置 + 脏树打种 + 脱敏边界）

但在"实际怎么运作"层面：

- **角色是 prompt 骨架**，缺乏操作化细节
- **改进循环从未完成过**，所有 CHANGELOG 都标注 "Development release"
- **评测是 unmeasured 的**，business slice 有 3 个 P0 blocker
- **治理是声明式的**，不强制执行

**核心矛盾：整套治理是 prompt-based 的规范，不是 enforceable 的约束。**

要让它从设计文档变成生产系统，需要把部分 gate 从"告诉你应该做"改成"你不做就报错"。最关键的下一步是：**完成一次真实的 improve 循环**，哪怕是最小规模的——只有真正跑过一次，才能验证这套机制是否真的能运转。
