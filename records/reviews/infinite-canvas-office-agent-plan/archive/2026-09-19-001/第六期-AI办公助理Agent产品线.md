# 第六期执行计划：AI 办公助理（Agent 产品线）

> 状态：待评审。本文档是规划稿，未经确认不进入实施。
> 产品暂定名「AI 办公助理」，最终名称待定（见「待用户决策项」）。

## 一句话定位

基于 Claude Agent SDK 的云端 Agent 产品：用户在网页上发起对话，Agent 在服务端工作区里执行工具（读写文件、跑命令）、产出可预览可下载的成果制品（Artifacts），对标 360「AI 办公助理」与腾讯 WorkBuddy 的产品形态。

## 背景与调研结论

### 对标产品考古结论（2026-09 前端 bundle 分析）

| | 360 AI办公助理（paipai/nexus） | WorkBuddy（genie，腾讯系） |
|---|---|---|
| 前端 | Vite + React SPA，CDN 部署 | Vite + React + zustand + monaco + katex + hljs |
| 模型接入 | 后端「代理 Runtime Cancel」，Runtime 独立部署 | 腾讯云 Token Plan：Anthropic 兼容端点 `/plan/anthropic/v1/messages` |
| Agent 协议 | SSE 事件流：delta / tool_call / tool_result / task_tool_*（子代理）/ plan / clarification / artifact / checkpoint / sandbox_queue_status | Claude Code 同名工具（TodoWrite / AskUserQuestion / ExitPlanMode）+ `<system-reminder data-role="compact-summary">` 压缩 + MCP（bundle 内置完整客户端） |
| 技能 | SKILL.md 格式；市场/安装/导入预览确认 | SKILL.md + frontmatter + allowed-tools；来源 api.skillhub.cn |
| 沙箱 | queue-ticket 排队制执行环境 + workspace-recovery | checkpoint（44 处）+ compact（371 处） |
| 特色 | Artifacts 绑 WPS WebOffice 在线编辑、ASR 语音、速度档位、credits_exhausted | tdrive 网盘、知识库 RAG、组织通讯录、定时任务 |

两家共同范式：**产品层自研 + Agent 能力层用 Claude Agent SDK（或其协议仿制）+ 模型接入走企业网关，Runtime 独立进程部署，业务后端只做代理与编排。**

### 模型接入验证结论（均已在官方文档核实）

| 厂商 | Anthropic 兼容端点 | 模型 | 备注 |
|---|---|---|---|
| 智谱 GLM | `https://open.bigmodel.cn/api/anthropic` | glm-5.3 / glm-5.2 | 官方 SDK 直改 base_url 即用 |
| Kimi | `https://api.moonshot.ai/anthropic` | kimi-k3（1M 上下文）/ kimi-k2.7-code / kimi-k2.6 | 官方文档含完整 Claude Code 配置模板与分层映射 |
| MiniMax | `https://api.minimax.io/anthropic`（国内 `api.minimaxi.com`） | M3（1M+多模态）/ M2.x | 忽略 `top_k`/`stop_sequences`/`mcp_servers` 请求字段；M2.x 无图像输入 |
| GPT (OpenAI) | 无官方 Anthropic 端点 | — | 走 LiteLLM 协议翻译（`/v1/messages` 进、OpenAI 格式出，流式+工具调用均支持） |

结论：**用 Claude Agent SDK 不等于只能用 Claude**。国产三家协议直通；GPT 经网关翻译接入，但有损（工具流式细粒度、interleaved thinking、Anthropic 服务端工具 `web_search` 等退化），需实测。

## 范围界定

### 本期要做（M1–M3）

1. 端到端最小链路：会话 → Runtime → 网关 → 模型 → 流式回复（M1）。
2. 工具执行与工作区：Agent 读写文件/跑命令，过程可视化，产出 Artifacts（M2）。
3. 模型矩阵与计费：GLM/Kimi/MiniMax 直通 + GPT 翻译、按点数计费、配额、admin 管理（M3）。

### 本期不做（后续期）

- 沙箱容器池 + 排队（协议预留，MVP 用容器即沙箱）。
- 子代理（task_tool_*）、计划模式、技能市场与 SKILL.md 导入 UI。
- 语音输入（ASR）、WPS/Office 在线协作编辑、知识库 RAG、组织与团队。
- 智能体公开市场（先做管理员配置的内置智能体）。

## 总体架构

```
web 前端（/office 聊天工作台）
   │  SSE（自定义事件协议，全事件带 seq）
Go 编排层（server/internal/office）── sessions/runs/events 落库、鉴权、点数计量、
   │                                   Last-Event-ID 重放、admin 面
   │  HTTP 内网（POST /v1/runs → SSE 事件流；POST /v1/runs/:id/cancel）
Node Runtime（office-agent/）── @anthropic-ai/claude-agent-sdk 包装、
   │                             SDKMessage → 归一化事件、skills/MCP、工作区目录
   │  ANTHROPIC_BASE_URL → 指向 LiteLLM
LiteLLM 网关 ──┬─ glm-5.3      → open.bigmodel.cn/api/anthropic（直通）
               ├─ kimi-k3      → api.moonshot.ai/anthropic（直通）
               ├─ minimax-m3   → api.minimax.io/anthropic（直通）
               └─ gpt-*        → OpenAI（协议翻译）
```

三层两契约：

- 契约一（前端 ↔ Go）：业务 SSE 协议，事件落库后由 Go 转发，断线用 Last-Event-ID 重放，不依赖 Runtime 存活。
- 契约二（Go ↔ Runtime）：内部 HTTP，四个接口（发起 run、事件流、取消、健康检查）。SDK 细节不泄漏到 Go，更不泄漏到前端。

参照先例：`canvas-agent/` 已验证「express 包 agent CLI 跑 loop + MCP + skills store」的完整模式，本期为同一形状换 SDK；nginx 已有 `/api/v1/ai/` 的 SSE 转发模板。

## 仓库落位

```text
infinite-canvas/
├─ server/internal/office/        # Go 编排域：handler/service/model + Mount*Routes
├─ office-agent/                  # Node Runtime（照 canvas-agent 模板，独立 Dockerfile）
│  ├─ src/index.ts                # express：POST /v1/runs、POST /v1/runs/:id/cancel、GET /healthz
│  ├─ src/run/                    # query() 包装、SDKMessage→归一化事件、AbortController 取消
│  ├─ src/events/                 # 事件协议类型（zod 校验，与 Go 侧共享字段约定）
│  ├─ src/skills/                 # SKILL.md 目录扫描加载（参考 canvas-agent skills store）
│  ├─ src/mcp/                    # MCP server 注册
│  └─ Dockerfile
├─ web/src/pages/office/          # 聊天工作台页面
├─ docker-compose.yml             # 新增 office-agent、litellm 两个 service
└─ nginx.conf                     # 新增 /api/v1/office/ location（SSE 模板照 /api/v1/ai/）
```

不另建 Git 仓库：编排层依赖现有账号/点数/admin/SSE 基建，monorepo 已有 blog、canvas-agent 的「一目录一服务」先例；将来独立拆出时整目录可搬。

不使用 serverless/Worker 形态：SDK 需 spawn CLI 子进程、文件系统工作区、分钟级长任务，必须是常驻 Node 容器 + 持久卷。

## 核心设计

### 会话与运行模型

- `session`（会话）：绑定用户、智能体配置、工作区目录。一次会话多轮对话。
- `run`（运行）：一次 Agent 执行（用户发一条消息触发一个 run），状态机 `queued → running → succeeded | failed | cancelled`。
- 上下文连续性用 SDK 的 `resume`/`fork`：**resume-per-turn**，每个 run 结束 transcript 落持久卷，下个 run 用 resume 续上下文。不做常驻交互式会话进程（内存与粘性路由负担），Runtime 保持近无状态，可水平扩展。
- 取消链路：前端 → Go `POST /runs/:id/cancel` → Runtime AbortController 中断 SDK → 事件流收尾 `error`/`done`，Go 落库终态。

### 事件协议

所有事件统一信封：`{"seq":42,"type":"delta","runId":"r_…","ts":…,"payload":{…}}`。seq 由 Go 落库时分配，`(run_id, seq)` 唯一，Last-Event-ID 按 seq 重放。

| 类型 | 方向 | payload 要点 | 期次 |
|---|---|---|---|
| `run_started` | →前端 | runId、model、agent 摘要 | M1 |
| `delta` | →前端 | 增量文本 | M1 |
| `tool_call` | →前端 | toolCallId、name、inputPreview、status | M2 |
| `tool_result` | →前端 | toolCallId、status、isError、outputPreview | M2 |
| `artifact` | →前端 | artifactId、kind、name、size | M2 |
| `notice` | →前端 | 运行时提示（环境/降级说明） | M1 |
| `done` | →前端 | 用量汇总（tokens、点数） | M1 |
| `error` | →前端 | code、message、可重试标志 | M1 |
| `plan_updated` / `clarification` | →前端 | 计划/结构化提问 | 预留 |
| `task_tool_call` / `task_tool_result` | →前端 | 子代理 | 预留 |
| `sandbox_queue_status` / `environment_rebuilt` | →前端 | 沙箱池 | 预留 |
| `quota_exhausted` | →前端 | 点数不足 | M3 |

MVP 明确不做事件级双向（无 WebSocket），SSE 单向 + HTTP 动作足够。

### 数据模型（MySQL 8.4）

| 表 | 关键字段 |
|---|---|
| `office_sessions` | id、user_id、agent_id、title、workspace_path、status、created_at |
| `office_runs` | id、session_id、status、model、error、started_at、finished_at、tokens/点数汇总 |
| `office_events` | BIGINT 自增、run_id、seq、type、payload JSON；UNIQUE(run_id, seq)，按 session 清理 |
| `office_messages` | id、session_id、role、content JSON、run_id、created_at（用户可见消息，与事件流分离） |
| `office_artifacts` | id、session_id、run_id、kind(markdown/code/html/file)、name、storage_key、size、mime |
| `office_files` | id、session_id、user_id、storage_key、mime、size（用户附件，走现有 storage 域） |
| `office_agents` | id、name、avatar、description、system_prompt、model、tools JSON、skills JSON、visibility、enabled（内置智能体由 admin 配置） |
| `office_skills` | id、slug、version、name、description、frontmatter JSON、storage_key、enabled（本期仅落库与加载，无市场 UI） |

新表/新列按项目注意事项：**交付前必须在真实 MySQL 上跑一次迁移验证**。

### Runtime（office-agent）设计

- 职责边界：只做协议翻译与 agent 生命周期管理；**鉴权、配额、计费、业务规则一律不进 Node**。
- `POST /v1/runs`：入参 session 工作区路径、消息内容、agent 配置（system_prompt/model/tools/skills）、附件清单；出参 SSE 归一化事件流。
- `POST /v1/runs/:id/cancel`：中断当前 query()。
- SDK 配置：`query()` + `resume` 续会话；`canUseTool` 钩子预留审批位；`mcpServers` 静态注册（本期内置文件工具即可）；模型经环境变量 `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` 指向 LiteLLM。
- 分层映射必须配全：`ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_HAIKU_MODEL` / `CLAUDE_CODE_SUBAGENT_MODEL` 等——**漏配是静默失败**（后台轻任务走 haiku 档）。
- 工作区：`/data/workspaces/{sessionId}/`，持久卷挂载；会话内 Read/Write/Bash 工具限制在该目录。
- SDK 版本锁定：`@anthropic-ai/claude-agent-sdk` 固定版本，升级视为独立变更项（SDK 迭代快，事件归一化层就是为隔离它存在）。

### 模型接入（LiteLLM）

- LiteLLM 单容器，配置即路由表，每个模型带能力位：`vision`、`context 档位`、`thinking 开关`、`服务端工具`。前端按能力位过滤可选模型，不让用户选跑不动的组合。
- 国产三家直通各官方 Anthropic 端点（零转换损耗）；GPT 走翻译路径，**上线前用固定任务集对比工具调用保真度**，不达标则 GPT 限场景或延后。
- `web_search`/`web_fetch` 是 Anthropic 服务端工具，第三方端点均无：本期由 Runtime 注册自建搜索工具（接现有或第三方搜索 API，实现时再选型）替代。
- MiniMax 忽略 API 请求中的 `mcp_servers` 字段无影响：SDK 的 MCP 是客户端侧由 Runtime 进程自己跑，不依赖 API 端实现。
- 备选：若不接受 LiteLLM（Python 运维面），退路是自建 Go 翻译层（Anthropic↔OpenAI 映射有界、已知），但首选拿现成的。

### 沙箱（两阶段）

- 阶段一（本期）：`office-agent` 容器本身即沙箱边界，每会话独立工作目录；容器内用 SDK 自带 sandboxed bash（Linux bubblewrap）做文件系统/网络限制，防 agent 误伤宿主。明确：容器边界防的是事故，不是恶意用户，公众开放前必须进阶段二。
- 阶段二（后续期）：沙箱容器池 + 排队（每个会话分配 gVisor/Firecracker 沙箱容器，Runtime exec 进沙箱执行工具），协议已预留 `sandbox_queue_status`/`environment_rebuilt`；届时评估 E2B 自托管替代自建池。

### 文件与 Artifacts

- 用户附件：前端上传走现有 storage 域（presigned），元信息落 `office_files`，run 发起时传清单给 Runtime 注入工作区。
- Artifacts：Agent 在工作区产出的文件，Runtime 识别并上报 `artifact` 事件（按扩展名/内容分类 markdown/code/html/file），Go 落 `office_artifacts`，预览由 Go 提供只读接口，前端渲染 markdown/代码高亮；下载走 storage 签名 URL。WPS 式在线编辑明确不在本期。

### 技能与智能体

- 智能体 = `office_agents` 一行配置（系统提示词 × 模型 × 工具集 × 技能集），admin 后台管理，用户端展示为可切换的「助手」列表；头像/分类字段预留。
- 技能 = SKILL.md 包（frontmatter：name/description/allowed-tools），`office_skills` 落库，Runtime 启动/安装时落盘到技能目录供 SDK 加载；市场、导入预览、用户自装在后续期。

## 前端规划

- 路由 `/office`：左侧会话列表 + 主区对话流 + 右侧 Artifact 抽屉（可关）。
- 对话流组件：文本增量渲染（markdown + 代码高亮 + katex 公式预留）、`tool_call`/`tool_result` 过程卡片（折叠态显示摘要，展开显示输入输出预览）、`artifact` 事件插入产物卡片。
- 断线恢复：EventSource 带 `Last-Event-ID`，重连后由 Go 按 seq 重放补齐，页面刷新后历史从 `office_messages` 拉取。
- 主题遵守画布规范：用 `canvasThemes`/`ConfigProvider` token，不硬编码黑白；弹层颜色走 `app-theme.ts` 全局配置。
- 运行中消息等大对象不做 localStorage 持久化，会话元信息可入 localforage；权威数据在服务端。

## 权限、配额与安全

- 新增权限点：`office.read` / `office.write`（金标权限 30 → 32），默认授予普通用户，admin 管理页复用现有权限体系。
- 计费：按 run 结束回填 token 用量，经 LiteLLM cost 追踪映射为点数扣减，复用 billing 域；点数不足发 `quota_exhausted` 事件并终止 run（防账单失控是硬要求）。
- 内容审核：用户输入经现有 moderation 域审查；Agent 产出物（Artifacts）审核规则在 M3 定义（至少做存储侧标记 + admin 可见）。
- API key 全部服务端保管（LiteLLM 环境变量/密管），前端与 Runtime 均不持有模型 key；office-agent 只在内网，不经 nginx 暴露。
- 限流：每用户并发 run 上限 + 每日消息数上限（复用现有限流器），边界值在实施前按项目注意事项报批。

## 部署

- compose 新增：`office-agent`（build `./office-agent`，挂工作区持久卷）、`litellm`（官方镜像 + config 卷，仅内网）。现有 `app`/`admin`/`api`/`db`/`blog-web` 不动。
- nginx 新增 `location /api/v1/office/`：照抄 `/api/v1/ai/` 的 SSE 模板（`proxy_buffering off`、`proxy_read_timeout 600s`、HTTP/1.1）。
- Runtime 与 Go 之间走 compose 内网服务名，不走 nginx。
- 上线前检查清单：真实 MySQL 迁移验证、LiteLLM 路由表连通性（四家 curl 冒烟）、SSE 断线重连演练、点数扣减对账。

## 里程碑与验收

### M1 端到端最小链路

- 内容：office-agent 骨架（runs/cancel/healthz + 事件归一化）、Go `office` 域（会话/run 落库、SSE 转发与重放、cancel 透传）、LiteLLM + GLM 直通、web 最小聊天页（流式文本 + done/error）、compose/nginx 就位。
- 验收：浏览器发起会话收到流式回复；刷新页面历史完整；杀 Runtime 进程后重连不丢事件（Last-Event-ID 生效）；cancel 秒级生效；`office_events` 有完整 seq 记录。

### M2 工具与工作区

- 内容：文件工具（Read/Write/Bash）+ 每会话工作区、工具卡片 UI、附件上传注入、Artifacts 落库与预览/下载、自建搜索工具。
- 验收：让 Agent「写一份 markdown 调研报告」→ 过程卡片可见 → Artifacts 面板可预览可下载；工作区文件跨 run 持久（resume 生效）；附件能被 Agent 读取。

### M3 模型矩阵与计费

- 内容：Kimi/MiniMax 直通 + GPT 翻译与评测、能力位过滤、点数扣减与配额、admin 智能体/技能/路由管理页、`office.read/write` 权限接入。
- 验收：同一会话切换模型续聊；点数不足收到 `quota_exhausted` 并终止；admin 改智能体配置对用户端即时生效；GPT 任务集评测报告（工具调用成功率）产出并有结论。

### M4（预告，不在本期）

沙箱容器池与排队、子代理与计划模式、技能市场与导入、ASR 语音、RAG 知识库、组织协作。

## 风险与对策

| 风险 | 对策 |
|---|---|
| GPT 经翻译层工具调用保真度不足 | 固定任务集评测门禁，不达标则限场景/延后；国产三家不受影响 |
| 非 Claude 模型上下文压缩质量参差 | resume-per-turn + 窗口配置化；压缩失败降级为截断 + `notice` 事件告知 |
| SDK 版本迭代快、行为变动 | 锁版本；事件归一化层隔离；升级当独立变更走验收 |
| LiteLLM 引入 Python 运维面 | 单容器低维护；退路自建 Go 翻译层已论证可行 |
| 长会话 token 膨胀与成本 | 点数硬闸 + `quota_exhausted`；LiteLLM 成本追踪对账 |
| 容器即沙箱的隔离强度 | 限内测范围；公众开放前必须完成阶段二（写入验收红线） |
| MySQL 特有迁移坑（列名/长度） | 交付前真实 MySQL 跑迁移（项目注意事项硬性要求） |

## 对标功能覆盖对照

> 依据 2026-09 两站前端 bundle 考古得到的功能清单逐项对照，评审结论：核心链路全覆盖，差距集中在四个明示项（见后）。

### 360 AI办公助理（paipai/nexus）功能覆盖

| 对端功能 | 本计划 | 状态 |
|---|---|---|
| sessions/runs/SSE + Last-Event-ID 重放/cancel | M1 事件协议 + Go 编排层 | ✅ 覆盖 |
| tool_call/tool_result 过程可视化、tool-results 接口 | M2 工具卡片 + office_events | ✅ 覆盖 |
| artifacts + 下载 | M2 落库/预览/下载 | ✅ 覆盖（WPS 在线编辑在后续期，对端为增值功能） |
| 文件 presigned 上传下载、attachments | M2 复用现有 storage 域 | ✅ 覆盖 |
| skills（SKILL.md 市场/安装/导入预览） | M3 落库+加载；市场/导入 UI 后续期 | ✅ 核心覆盖，市场明确延后 |
| quota / credits_exhausted | M3 点数 + quota_exhausted 事件 | ✅ 覆盖 |
| 智能体市场/分类/自定义 | M3 admin 内置智能体；公开市场后续期 | ✅ 核心覆盖，市场明确延后 |
| plan/plan-actions、clarification_summary、task_tool_*（子代理）、sandbox-queue、environment_rebuilt | 协议预留 | ⏸ 后续期（计划已列） |
| ASR 语音、速度档位、草稿润色、unread 通知、点踩反馈 | — | ❌ 见差距说明 |
| workspace-recovery / run_recovery | M1 events 落库+seq 重放覆盖事件层恢复；工作区环境重建在沙箱阶段二 | ✅ 分层覆盖 |

### WorkBuddy（genie）功能覆盖

| 对端功能 | 本计划 | 状态 |
|---|---|---|
| Anthropic 兼容多模型接入（Token Plan 等价物） | M3 LiteLLM 网关 + 能力位路由表 | ✅ 覆盖（自建网关替代腾讯 Token Plan） |
| TodoWrite/AskUserQuestion/ExitPlanMode 工具集 | M2 SDK 内置工具 | ✅ 覆盖（AskUserQuestion 见差距说明） |
| system-reminder compact-summary 上下文压缩 | SDK 自带压缩 + 风险表对策 | ✅ 覆盖 |
| checkpoint 会话连续性 | resume-per-turn + transcript 落盘 | ✅ 等效替代（无 UI 级回滚，后续期再评估） |
| MCP 客户端 | Runtime 静态注册 mcpServers | ✅ 覆盖 |
| SKILL.md + 技能市场（skillhub） | M3 落库加载；市场后续期 | ✅ 核心覆盖 |
| monaco 在线编辑 / katex / xtable | M2 只读预览（代码高亮+markdown）；在线编辑后续期 | ✅ 核心覆盖 |
| tdrive 网盘、知识库 RAG、组织/通讯录/团队权限、定时任务、session fork | — | ⏸ 后续期（计划已列） |

### 差距说明（本次审查发现）

1. **结构化提问（clarification/AskUserQuestion）**：只做了事件预留，但它是对话体验的核心交互（360 有专用事件、WorkBuddy 直接带工具），且 SDK 的 `canUseTool`/结构化输入对它有现成支持，实现成本低。**建议评估提前到 M2**，待决策项 6。
2. **生成反馈（点赞/点踩）**：360 有 chat feedback；本仓库已有 `generation_feedbacks` 全套基建（生成点踩弹窗+标签），M3 复用成本很低。待决策项 7。
3. **多模态附件链路**：M2 附件是通用文件，M3 路由表有 vision 能力位，但「图片附件 → vision 模型」的过滤提示未明说，M2 实施时补一句前端过滤即可。
4. **明确不做且无核心损失**：draft-polish、speed-tiers、unread、session fork、多端状态同步——均为对端产品级润色功能，与核心闭环无关，记录在案不再重复评估。

## 待用户决策项

1. 产品名与定位（暂用「AI 办公助理」）；是否需要独立域名。
2. 首发模型组合：建议 glm-5.3 主力 + kimi-k2.7-code 编码 + MiniMax-M3 多模态；GPT 是否进首发取决于评测（建议 M3 先评后定）。
3. `/office` 页面放现有 web 应用（复用登录与主题，本计划默认此项）还是未来独立站。
4. 会话工作区与「我的素材」（浏览器本地体系）的关系：本期默认互不相通，打通留待后续。
5. office-agent 命名（可与产品名联动，目录名影响不大）。
6. 结构化提问（AskUserQuestion 交互）是否从「预留」提前到 M2 实现（审查建议提前，成本低、体验收益大）。
7. 生成反馈（点赞/点踩）是否并入 M3，复用现有 `generation_feedbacks` 基建（审查建议并入）。

## 下一步

1. 用户评审本文档，拍板「待用户决策项」。
2. M1 开工顺序：LiteLLM 配置与四家 curl 冒烟 → office-agent 骨架 → Go `office` 域 → web 聊天页 → compose/nginx → M1 验收清单走查。
3. 实施中新增/调整边界值（限流、超时、并发）按项目注意事项先报批再写入。
