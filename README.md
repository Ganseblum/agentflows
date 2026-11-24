# Agentflow

Agentflow 是宿主原生的多智能体开发插件。它帮助团队明确验收、按风险准备文档、测试先行，并让独立评审核对结果。模型、工具和权限由编码宿主管理。

## 使用

脚本需要 Python 3.10+。依赖仓库版本或执行证据的命令需要 Git。运行进程并采集测试证据的 workflow run 需要 POSIX 环境（macOS 或 Linux）。

| 宿主 | 安装或升级 | 工作入口 |
| --- | --- | --- |
| Codex | 已配置本地 marketplace 后，通过 upgrade-codex 升级。现有适配器支持本地来源。 | $agentflow |
| Claude Code | 在源码根运行 claude --plugin-dir .，或加载与项目约定一致的插件目录。 | /agentflow:agentflow |
| ZCode | 构建 packaging/runtime 后使用 upgrade-zcode。auto 沿用配置来源，也可显式指定 local 或 remote。 | 在宿主中调用 Agentflow skill。 |
| Qoder | 用 qoder plugins install packaging/runtime --scope user 安装。只有桌面端时从扩展安装入口载入该目录打包的 ZIP。 | 在宿主中调用 Agentflow skill 或已注册角色。 |
| Cursor | 运行 python3 skills/agentflow/scripts/export_cursor_rules.py 导出规则至目标仓 .cursor/rules/。 | 规则自动生效或在提示词中调用。 |

升级命令、载荷校验和新会话确认见[打包与安装指南](packaging/README.md)。工具白名单的实际执行取决于宿主，已有实测范围见[宿主平台事实](docs/host-platform-facts.md)。跨项目全局规则单独走[宿主接入](skills/agentflow/references/hosts.md)。

## 第一次使用

在目标项目中说明要实现的用户行为、不能动的范围和验收方式，例如：

> 先确认这个改动的用户行为和失败分支，按风险选择材料。行为改动先复现验收用例为什么失败，再实现、回归和独立评审，给我实际命令和结果。

小型低风险行为改动用一个 README。跨层契约、数据、权限或难回退的改动使用提案、规格、设计和实施计划。优先复用目标项目现有的文档和测试入口。 [快速开始](docs/quickstart.md) · [文档分档](skills/agentflow/references/document-chain.md#文档档位) · [模板](skills/agentflow/templates/README.md)

## 仓库布局

agents/ 与 skills/ 是插件源码，packaging/runtime 是安装生成包。仓库维护入口集中在[索引](index.md)，版本变更见[变更日志](CHANGELOG.md)。参与修改前先读[仓库规则](AGENTS.md)。
