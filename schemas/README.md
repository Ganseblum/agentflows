# Agentflow 契约

本目录存放 Agentflow 工作流、维护工具与评测 fixture 共享的跨宿主契约。

改进环专用契约仍在 `skills/improve/references/` 下，因为 Improve Skill 直接链接到它们。
校验器加载两处位置，并检查单份 JSON Schema 无法表达的跨文档不变量。

这些契约描述证据与执行计划。计划本身不构成修改代码或发布插件的授权。

评测结果绑定到产物 digest、套件基数、观测到的执行上下文，以及逐用例的 holdout/重复元数据。
runner 拒绝不能精确覆盖冻结套件的 adapter 输出。
