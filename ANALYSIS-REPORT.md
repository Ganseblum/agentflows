# Agentflow 项目全面分析报告

> **[2026-09-17 已被取代]** 本报告为早期评审会话的产物，多条论断已过时：episode provenance 已加约束、GitHub Actions CI 已落地、argparse 重复 choices 已删、"判断词"已在 SKILL 定义、Bugs 记录流转与本批修复均已发生。现行有效的逐条裁定见 [CONSOLIDATED-REVIEW-REPORT.md](CONSOLIDATED-REVIEW-REPORT.md)（其附录 A 专门列表失效论断）。本文件仅作历史参考保留。

> 分析日期：2026-09-17  
> 版本：v0.6.0  
> 范围：架构、逻辑、能力、治理机制

---

## 一、项目概况

**Agentflow** 是一个宿主原生的多智能体开发工作流插件，为 Codex、Claude Code、ZCode 等 AI 编码助手提供：

- 12 个专业角色（前端/后端工程师、技术总监、审查员、Bug 调查员、评估员、发布官等）
- 2 个工作流：`agentflow`（开发任务）和 `improve`（插件自我演进）
- 确定性校验工具链：`tools/lab/` 下的 validate / isolation / eval_runner / policy

---

## 二、做得好的地方

- **角色分工清晰**：12 个角色有明确的读写边界，作者不能自审，reviewer 独立
- **契约驱动**：schema、frontmatter、hard boundary 都有文档化定义
- **自审机制完整**：`protected-paths.txt` + `isolation.py` + `validate.py` 三层防护
- **改进循环有数学基础**：`policy.py` 有明确的指标方向性定义和容差比较
- **自定义 JSON Schema 验证器**：不依赖外部库，实现了 Draft 2020-12 大部分关键字

---

## 三、架构问题

### 3.1 代码结构

| 问题 | 严重度 | 详情 |
|------|--------|------|
| `validate.py` 是 1973 行的上帝对象 | 🔴 高 | 没有模块拆分，包含 schema 验证、frontmatter 解析、plan/bug/review/recurrence markdown 校验、manifest 校验、安装对比、CLI dispatch 等全部职责 |
| argparse `choices` 重复 | 🟡 低 | `"docs"` 出现两次，copy-paste 痕迹 |
| `check-write-scope.sh` 兼容性强但脆弱 | 🟡 低 | `set -eu` + 空数组展开，依赖 bash 版本 |

### 3.2 数据契约

| 问题 | 严重度 | 详情 |
|------|--------|------|
| 8 个指标定义散落在 3 个文件无共享源 | 🔴 高 | `evaluation-result.schema.json`、`release-record.schema.json`、`policy.py` 各自定义同一组指标（acceptance_rate、first_pass_review_rate 等） |
| `adapter-case-result.schema.json` 被内联重复 | 🟡 中 | `evaluation-result.schema.json` lines 83-109 完全重写了这个独立 schema，没有用 `$ref` |
| `episode.schema.json` 的 `provenance` 是无类型 object | 🟡 中 | 没有 `additionalProperties: false` 或属性约束，是校验漏洞 |
| `review.schema.json` 的 `findings` 不验证 bug_id 存在性 | 🟡 中 | 跨文档校验只在 `validate.py` 过程中做，不是声明式的 |

### 3.3 Manifest 一致性

| 问题 | 严重度 | 详情 |
|------|--------|------|
| 5 个 manifest 的 `description` 不一致 | 🟡 低 | plugin.json 说 "host-native multi-agent development"，claude 说 "Run host-native development"，codex 说 "Run host-native multi-agent" |
| `.claude-plugin/plugin.json` 和 `.codex-plugin/plugin.json` 缺少 `license` 字段 | 🟡 低 | 只有 ZCode manifest 声明了 MIT |
| `marketplace.json` 顶层 `version` 是整数 `1`，其他都是字符串 semver | 🟡 低 | 校验器恰好跳过了顶层（通过 `plugins[0]` 指针），所以没报错 |

---

## 四、逻辑 / 工作流问题

### 4.1 Gate 机制缺陷

| 问题 | 严重度 | 详情 |
|------|--------|------|
| Review gate 是声明式的，supervisor 可以选择不执行 reviewer 命令 | 🔴 高 | `skills/agentflow/SKILL.md` line 87-88，"may execute" 不是 "must"，没有校验工具检查命令是否实际执行 |
| "小改动可以跳过 review" 没有定义"小"的标准 | 🔴 高 | `SKILL.md` line 83，supervisor 有动机滥用此例外来规避 review |
| 架构门（technical director）触发条件是"risky work" | 🟡 中 | 主观判断，容易被跳过，没有客观触发条件 |
| Plan 审批中"已关闭"标记是文本字符串 | 🟡 低 | 没有验证关闭是否真的有实际解决方案 |

### 4.2 生命周期 / 状态机缺陷

| 问题 | 严重度 | 详情 |
|------|--------|------|
| Bug 生命周期有空档：fixer → recorder 之间没有状态过渡保证 | 🔴 高 | fixer 不能标记 `fixed-pending-review`，recorder 也不验证 fix 质量就写状态 |
| "双次失败停止"规则中"相同原因"无定义 | 🟡 中 | 无法程序化判定，不同报错但同一根因不算匹配 |
| Review-repair 循环次数有歧义 | 🟡 中 | "repair once" 指一轮还是无限次 reopen？总 cycle time 无上限 |
| Bug fixer 的 "candidate workspace" 隔离模型未定义 | 🟡 中 | 是 worktree？分支？拷贝？没有说明 |

### 4.3 预算与资源

| 问题 | 严重度 | 详情 |
|------|--------|------|
| `maxTurns` 在每个角色 frontmatter 声明了但 host 不验证 | 🔴 高 | `AGENTS.md` line 40 自己承认"declared but unverified"，预算纪律全靠 prompt 遵守 |
| 没有跨角色的累计预算 | 🟡 中 | 整个工作流可以无限燃烧 turns |

### 4.4 委派链缺陷

| 问题 | 严重度 | 详情 |
|------|--------|------|
| Bug investigator → fixer 没有自动触发机制 | 🟡 中 | supervisor 必须手动读诊断并创建 brief |
| Review → implementation 没有自动回路 | 🟡 中 | `changes_requested` 后 supervisor 必须手动 re-brief |
| Supervisor 自写代码时 review 必须做——没有检测 | 🟡 中 | 全靠自觉申报 |
| Contradictory review findings 没有冲突解决机制 | 🟡 低 | 两个 reviewer 意见不一致时无升级路径 |

---

## 五、横向能力缺失（广度）

| 缺失领域 | 现状 | 影响 |
|----------|------|------|
| **CI/CD 集成** | 无 GitHub Actions，无 pre-commit hook，无 push 自动门 | 所有校验靠手动运行，CI 缺失意味着合入门控为零 |
| **部署/发布自动化** | 5 个 manifest 手动同步版本，`release-governor` 只返回决策 | 发布完全人工，与"治理"叙事矛盾 |
| **安全扫描** | 无 SAST、无依赖漏洞扫描、无密钥检测 | Security 只是 reviewer 的一个 prompt checklist |
| **测试生成** | 无测试角色，无自动 scaffolding | 回归测试靠实现角色"记得加"，无 revert experiment |
| **Lint/格式化** | 实现角色不跑 linter，reviewer 也不强制 | 代码风格无保障 |
| **文档生成** | 无文档角色，无 API docs 生成 | 文档与代码同步靠人工记忆 |
| **可观测性** | `latency_ms` 采集但不导出，无监控、无告警、无 dashboard | 无法追踪 agent 表现趋势 |
| **通知系统** | 评估失败、recurrence 升级无通知 | 人类无法及时介入 |
| **ZCode host adapter** | `host_adapter.py` 只支持 codex/claude | 作为主要目标的 ZCode 反而没有运行时适配 |

---

## 六、纵向能力单薄（深度）

| 薄弱点 | 详情 |
|--------|------|
| **Evaluator 角色** | 仅 18 行 prompt 骨架。"contamination risk"未定义、如何检测未说明、无操作指引 |
| **Release Governor** | 只返回决策，不对接安装/回滚机制，决策可被人类忽略 |
| **Feedback Analyst** | 无反馈收集工具、无结构化摄入管道，输出无 schema，"clusters"无存储格式 |
| **Candidate Engineer** | 边界遵守全靠 prompt，`check-diff` 是事后检测，无文件系统级隔离 |
| **Episode 记录** | schema 存在但缺关联——没有链接到代码变更、角色决策、检查结果 |
| **Seed Grader** | 纯子串匹配（`anchor in text`），已知产生假阳性，无语义匹配、无 embedding、无 LLM-as-judge |
| **评测自报告** | `accepted`、`unnecessary_delegation` 等核心指标是模型自己报的，无法交叉验证 |
| **Schema Validator** | 缺少 `dependencies`、`patternProperties`、`unevaluatedProperties`、远程 `$ref` 等 |

---

## 七、核心矛盾

**整套治理是 prompt-based 的规范，不是 enforceable 的约束。**

| 声明 | 现实 |
|------|------|
| "Reviewer 独立审查" | 同一上下文，prompt 说独立就独立 |
| "Fail-closed" | 只有 `seed_grader.py` 真正 fail-closed（exit 2），其他组件 log 后继续 |
| "Deterministic checks" | `validate.py` 是确定性的，但依赖文件处于预期状态，无运行隔离 |
| "Governed improvement" | 候选人决定改保护文件，只有事后 `check-diff` 能发现 |
| "maxTurns 限制" | host 不验证，等于无 |

README 自己也承认：*"Real model dogfood, private holdout service, and installation/release switch are still intentionally pending."*

---

## 八、改进优先级

### 🔴 立即修（影响可信度）

1. 拆分 `validate.py` → 独立模块（schema_validator、frontmatter_parser、markdown_validators、manifest_checker）
2. 合并重复指标定义 → 单一 `$ref` 源
3. 给模糊概念加可判定标准："小改动"、"risky work"、"相同原因"
4. 修复 argparse 重复 `docs`

### 🟡 短期补（补上明显缺口）

5. Evaluator / Feedback Analyst 角色补操作细节和输出 schema
6. Bug 生命周期补 `fixed-pending-review` 过渡 + 质量验证
7. 添加 GitHub Actions CI（至少跑 `validate.py all` + `unittest`）
8. Episode schema 补关联字段（code diff hash、角色列表、检查结果引用）
9. ZCode host adapter

### 🟢 长期建（从规范到可执行）

10. 把声明式 gate 改为工具强制执行（reviewer 命令必须被跑 → 加校验）
11. 完成至少一次完整的 improve 循环（baseline → candidate → eval → decision）
12. 加可观测性和成本追踪 dashboard
13. 安全扫描 / lint / 测试生成集成
14. 发布自动化（manifest 同步、changelog 生成、安装测试）

---

## 九、总结判断

Agentflow v0.6.0 是一个**精心设计的规范框架**，在"应该怎么运作"这个层面思考深入。但在"实际怎么运作"层面：

- **角色是 prompt 骨架**，缺乏操作化细节
- **改进循环从未完成过**，所有 CHANGELOG 都标注 "Development release: no baseline/candidate evaluation evidence"
- **评测是 unmeasured 的**，business slice 有 3 个 P0 blocker
- **治理是声明式的**，不强制执行

**一句话：这是一份写得很好的宪法，但没有法院和警察。**

要让它从设计文档变成生产系统，需要把部分 gate 从"告诉你应该做"改成"你不做就报错"。
