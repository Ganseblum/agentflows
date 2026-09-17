---
plan_id: PLAN-DEMO-SHARE-001
plan_version: 0.1.0
status: approved
objective: 对话分享——登录用户创建不可猜链接，他人免登录只读打开；含管理面作废/改期与灰度开关
recorded_at: 2026-09-17T03:30:00Z
updated_at: 2026-09-17T03:30:00Z
---

# 对话分享 — 实施计划（示例）

> 本文件是 Markdown 计划的正例。frontmatter 是机器信封；正文三节是执行与回写面。
> 状态图例：`☐ 未开始` / `◐ 进行中` / `☑ 已完成` / `⚠ 阻塞` / `— 本期不做`。
> 回写纪律：完成后只改**状态**与**证据**两列（最小 diff），不改写已完成的任务行。

## 进展概览

**本期进度**：**4 / 6 已完成** · **1 进行中** · **1 阻塞** · **0 未开始**
**统计口径**：T01–T06 计入本期；T07（运营后台二期）为远期，见任务清单末行。

| 序号 | 业务侧解读 | 技术侧解读 | 交付效果（完成后可验证） | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 分享数据有地方存，回滚可丢表 | 时间戳 migration 建表，不 AutoMigrate | `check-migrations.sh` 通过；表结构与 Design §1.3 一致 | ☑ |
| 2 | 对话页复制链接得到不可猜地址；连点/超时不出两条 | `POST /sessions/:id/shares` 必带 Idempotency-Key，同 key 同指纹重放同一 `share_path` | 同 key 重放返回同一行；缺 key 400 不写表 | ☑ |
| 3 | 对方免登录能打开正文；已登录帐号 B 也不能用自己的身份读 | 公开 GET 忽略 Authorization，剥掉 object_key/qid | 无痕 200；带 B 的 Authorization 仍只按 token | ☑ |
| 4 | 改动可回归，不能改坏对话页 WPS | 领域/handler 单测 + 现网 WPS 可写回归 | `make test`；含 `web_office` 可写断言 | ☑ |
| 5 | 值班能作废或改到期 | gRPC `AdminService.PatchConversationShare` | `revoked=true` 后公开 404 | ⚠（等 idl 合并；见 T05） |
| 6 | 发版顺序不错：先库后服务，开关最后开 | migration → Nexus(关) → Web(关) → 开 Nexus → 验证 → 开前端入口 | 联调清单走完；默认配置 `enabled=false` | ◐ |
| — | 运营后台分享管理页 | 二期 | — | — 本期不做 |

**我们在哪**：编码与测试完成，剩 IDL 联动与发版窗口。
**下一步**：T05 的 idl 合入打 tag → T06 按序发版。
**阻塞/风险**：T05 依赖 `safe-agent-nexus-idl` 仓的评审节奏；不阻塞时先跑 T06 的预发部分。

## 任务清单

| ID | 任务 | 优先级 | 代码落点 | 依赖 | 状态 | 证据回写 |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | 建 `agent_conversation_share` 表：19 列 6 键（含 `uk_app_qid_idem` 幂等三列键、`schema_version` 默认 1） | P0 | `migrations/20260914233000_agent_conversation_share.sql` | — | ☑ 已完成 | 逐行核对与 Design 一致；不在 `check-migrations.sh` 失败列表 |
| `T02` | 创建 handler：登录 + 本会话未 deleted；Idempotency-Key 必填；读回逐 ID 对账（缺失/跨会话 → 400 不落库） | P0 | `controller/share.go` | `T01` | ☑ 已完成 | `TestShareCreateFlowWithDB`：重放三字段全等总行数=1；同 key 换指纹 409 |
| `T03` | 公开 GET/下载：忽略 Authorization；文件按现状表 ready 签发；响应无 object_key/qid | P0 | `controller/share.go`、`server/router/share_public.go` | `T02` | ☑ 已完成 | `TestSharePublicHandlersIgnoreAuthorization`（4 种登录头变体逐字段一致） |
| `T04` | 回归：创建幂等 + 公开三接口安全用例 + 现网 WPS 可写不被改坏 | P0 | `controller/share_test.go`、`wps_test.go` | `T02`、`T03` | ☑ 已完成 | 58 包 `go test` 全绿；WPS 双 aud 分支锁定 |
| `T05` | gRPC 管理面：`PatchConversationShare`（revoked/expires_at wire 规则、重复作废保首次时间） | P0 | `safe-agent-nexus-idl`（proto）+ `rpc/nexus/admin_share.go` | `T01` | ⚠ 阻塞 | idl MR 待评审合入（见未决项 U-01） |
| `T06` | 发版顺序：migration → Nexus(`enabled=false`) → 回归现网下载/WPS → Web(入口关) → 开 Nexus 开关 → 验证公开三接口 → 开前端入口 | P0 | 环境配置 + 发布单 | `T04` | ◐ 进行中 | 迁移已在测试库落地并复验（19 列 6 索引逐项核对）；部署待流水线 |
| `T07` | 运营后台分享管理页（列表/搜索/作废） | P2 | `fe/safe-chat-admin` | `T05` | — 本期不做 | — |

### 未决项


| 编号 | 问题 | 是否阻塞 | 状态 |
| --- | --- | --- | --- |
| U-01 | idl MR 评审意见（字段命名 `revoke_reason` 可选性）何时关闭 | 阻塞 T05 | 已关闭（2026-09-17 评审通过，命名维持原案） |
| U-02 | 撤销接口是否需要审计日志独立表 | 不阻塞 | 未关闭（二期再议，写入 backlog） |

## 接口与共享机制

| 接口 | 契约 | 错误行为 | 兼容性 |
| --- | --- | --- | --- |
| `POST /sessions/:id/shares` | 返回 `share_path`/`content_types`/`expires_at`；信封 `{code, message}` | 409=同 key 换指纹；404=开关关/会话不存在；429=超用户频次 | 新增路由，向后兼容 |
| `GET /api/v1/public/shares/:token` | 公开 JSON + `available` 按现状表 | 六种失效（过期/作废/乱 token/不存在/未过审/关）同一 404 | 新增，不影响目录路由 |

| 共享机制 | 注册点 | 行为 | 受影响表面 |
| --- | --- | --- | --- |
| axios 401 响应拦截器 | `fe/src/api/client.ts:12` | 401 统一跳登录页 | 忘记/重置密码页（未登录是合法态）——公开分享页**不走**该 axios 实例，已单独验证 |

**异常矩阵（关键链路：创建）**：

| 异常场景 | 检测 | 处理 | 重试 | 幂等前提 | 用户可见 |
| --- | --- | --- | --- | --- | --- |
| 下游超时 | ctx 超时 | 500/10002，不写库 | 不重试（客户端可携同 key 重发） | Idempotency-Key | 「服务繁忙」 |
| 重复请求 | 幂等三列键冲突 | 同指纹重放原行 200 | — | 同 key 同指纹 | 同一链接 |
| 状态冲突 | 同 key 换请求指纹 | 409/60105 不写新行 | — | — | 「请求已变更」 |
| 回调失败 | WPS callback 失败计数 | 不影响主链路；告警 key 触发 | 平台侧重试 3 次退避 | 票据 aud | 无感 |

**发布顺序与回滚**：见 T06；每步配对回滚点——库可弃表（增量无删改）、服务回退镜像、开关一键关。

## 验证命令

```sh
cd be/safe-agent-nexus && make test          # 全部通过，含幂等与公开安全用例
python3 scripts/check-migrations.sh          # 本迁移不在失败列表
npm run test:e2e -- share                    # 公开页未登录态渲染正常
```
