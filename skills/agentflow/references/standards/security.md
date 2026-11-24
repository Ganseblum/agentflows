# 安全工程与审计标准（agentflow 通用底线）

> **定位**：与 `server-side.md`、`frontend.md`、`data-model.md` 配套的安全工程内容底线。agentflow 的 `review-checklists.md`（Security 模式）定义了评审边界，本册提供具体的**防漏洞、权限隔离、凭据保全与防御性编码**硬判据。
> **来源**：吸收 OWASP Top 10、行业生产安全规范与代码审计实战经验，重写为可证伪、可机检、可独立审计的通用底线。
> **编号**：`SEC-01…SEC-10`，供 Reviewer 在 finding 里直接引用，或研发在技术方案（`design/be`、`design/fe`）中作为安全自检依据。

## 0. 适用范围与何时必查

- **适用**：所有前端/后端代码实现、`spec/be`、`design/be`、`design/fe`、代码评审、外部系统对接与接口改造。
- **MUST 约束**：任何标为 **MUST** 的条款不满足即直接判 `changes_requested`。finding 标注 `defect_class: 代码` 或 `规范`。

## 1. 认证态与凭据生命周期（SEC-01）

**MUST**
- **Token 签名与有效期**：无状态 Token（如 JWT）必须使用强签名算法（禁止 `none` 算法），必须显式设置过期时间（`exp`），且必须校验签发者（`iss`）和受众（`aud`）。
- **凭据注销与黑名单机制**：当用户登出、修改密码或权限收回时，已签发的有效凭据必须有即时失效机制（如 Redis 黑名单、版本号对比或服务端 Session 清除），不能仅靠客户端丢弃 Token。
- **传输安全**：所有认证凭据（Cookie、Token、API Key）必须仅通过安全通道（HTTPS/WSS）传输。存储于 Cookie 时，必须配置 `HttpOnly`（防 XSS 窃取）、`Secure`（仅 HTTPS 传输）以及适用的 `SameSite` 策略。

## 2. 越权防护与租户隔离（SEC-02）

**MUST**
- **水平越权防护（IDOR）**：所有涉及查询、修改、删除业务数据的操作，必须校验当前登录身份对目标数据的主权，绝不能仅依赖客户端传入的 `id` / `user_id` / `tenant_id`。所有 SQL 或持久化查询必须在条件中强绑定上下文中的有效主体：
  ```sql
  -- 正确：强制绑定上下文租户与主体
  SELECT * FROM orders WHERE id = :order_id AND tenant_id = :ctx_tenant_id;
  -- 错误：仅靠目标 ID 检索，易受水平越权探测
  SELECT * FROM orders WHERE id = :order_id;
  ```
- **垂直越权防护**：每个敏感端点（管理端、配置变更、批量导出）必须经过强鉴权中间件或守卫，基于明确的角色（RBAC）或属性（ABAC）判定权限，禁止在业务控制器内漏校验。

## 3. 输入校验与防注入（SEC-03）

**MUST**
- **SQL / NoSQL 注入**：所有数据库查询必须强制使用参数化查询（Prepared Statements）或类型安全的 ORM/Query Builder。禁止任何形式的字符串拼接 SQL。
- **命令注入与路径穿越**：
  - 严禁将用户输入未过滤直接传入系统 Shell（如 `exec`, `system`, `popen`, `child_process.exec`）。必须调用系统原生参数数组形式（如 `execFile` / `subprocess.run(["cmd", arg])`）。
  - 处理文件上传、下载与本地路径时，必须规范化路径（`realpath`）并严格校验目标落在受控根目录内，防御 `../` 路径穿越攻击。
- **强类型与边界校验**：在请求入口处对所有字段做白名单校验（字段长度、数字区间、枚举值合法性、正则表达式格式），非法输入直接拒绝（400），不得进入业务逻辑层。

## 4. 跨站脚本与内容消毒（SEC-04）

**MUST**
- **默认转义**：前端页面渲染必须依靠框架的默认安全转义（React JSX, Vue 模板插值）。
- **富文本与原样 HTML 渲染**：严禁无消毒使用 `dangerouslySetInnerHTML`、`v-html` 或直接操作 DOM `innerHTML`。必须通过经过安全审计的白名单消毒库（如 DOMPurify）清洗输入，并禁止 `javascript:` 伪协议与内联事件挂载。
- **响应头防护**：服务端静态资源与 API 响应必须携带防护头：`Content-Security-Policy`、`X-Content-Type-Options: nosniff`、`X-Frame-Options`。

## 5. 跨域与请求伪造防护（SEC-05）

**MUST**
- **严控 CORS 白名单**：生产环境 API 绝不返回 `Access-Control-Allow-Origin: *` 与 `Access-Control-Allow-Credentials: true` 的组合，不得动态将 `Origin` 请求头原样回显为允许域。必须配置精确的受信任域名白名单。
- **CSRF 防护**：依赖 Cookie 进行身份认证的有状态 Web 服务，所有状态变更请求（POST/PUT/DELETE/PATCH）必须强制实施 CSRF 防御（CSRF Token 校验或 `SameSite=Strict/Lax` 策略）。

## 6. 服务端请求伪造（SSRF）防范（SEC-06）

**MUST**
- **外联地址限制**：当系统需要根据用户提供的 URL 发起网络请求（如 Webhook、图片抓取、数据导入）时，必须配置协议白名单（仅允许 `http`, `https`）。
- **内网与私有 IP 阻断**：必须在解析 DNS 后检查目标 IP，坚决阻断私有地址（`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`）、本地回环（`127.0.0.0/8`）、链路本地（`169.254.0.0/16`）及云厂商元数据服务（如 `169.254.169.254`）。
- **防御 DNS 重绑定**：必须在建立连接的底层 Socket 级别校验 IP，或禁用自动跳转，防止 DNS 重绑定绕过校验。

## 7. 敏感数据保护与加密（SEC-07）

**MUST**
- **密码存储**：密码必须使用强哈希算法存储（Argon2id, bcrypt, PBKDF2），并使用独立随机盐值，严禁使用 MD5, SHA1 或明文存储。
- **敏感数据静态加密**：身份证号、银行卡号、个人健康数据、第三方 API Secret 等高密级数据在落盘数据库时必须使用强对称加密（AES-256-GCM 或 ChaCha20-Poly1305）。
- **传输加密与脱敏展示**：所有外部网络流量强制使用 TLS 1.2+。在前端界面、错误堆栈、业务日志中展示敏感信息时，必须在服务端完成脱敏（如手机号 `138****0000`）。

## 8. 凭据管理与零硬编码（SEC-08）

**MUST**
- **零硬编码**：源代码、配置文件、注释、测试用例、Dockerfile 中严禁硬编码任何真实密码、Private Key、API Secret、Token。
- **环境变量与密钥库注入**：所有凭据必须通过环境变量（Environment Variables）或受信任的外部 Secret 存储（如 Vault, AWS Secrets Manager, K8s Secrets）在运行时注入。
- **日志审计与过滤**：日志打印框架必须配置敏感字段过滤中间件，请求体中的 `password`, `token`, `secret`, `credit_card` 字段不得打印到标准输出或日志收集系统。

## 9. 限流、防刷与资源耗尽保护（SEC-09）

**MUST**
- **公开端点限频**：登录端点、发送验证码、找回密码、公开搜索等端点必须有速率限制（Rate Limiting）和防暴力破解机制（如连续失败锁止、验证码接入）。
- **请求体与文件上传有界**：
  - 必须限制 HTTP 请求体最大体积（如 JSON 限制 1MB）。
  - 文件上传接口必须限制单文件体积、总上传体积、文件类型魔数（Magic Number 校验，不仅校验扩展名），且上传文件必须存放在无脚本执行权限的独立存储（如对象存储或禁用脚本执行的专用静态目录）。
- **避免 ReDoS**：用于输入校验的正则表达式必须避免灾难性回溯（Catastrophic Backtracking），复杂度不可预测的正则禁止上线。

## 10. 第三方依赖与供应链安全（SEC-10）

**MUST**
- **版本锁定**：项目必须提交精确的依赖锁定文件（`package-lock.json`, `pnpm-lock.yaml`, `go.sum`, `poetry.lock`, `Cargo.lock`），禁止浮动版本直接构建生产包。
- **无已知高危 CVE**：提交生产前必须运行依赖安全扫描（如 `npm audit`, `trivy`, `osv-scanner`），存在高危（High/Critical）已知漏洞的依赖包必须修复或升级。

---

## Reviewer 专项核验清单（按条对照）

Reviewer 在启用 Security 专项评审或常规实施复核时，必须按以下清单逐条核对代码 diff：

| 检查项 | 编号 | 核查动作 | 结论必须项 |
| --- | --- | --- | --- |
| 认证状态校验 | SEC-01 | 检查端点是否声明了认证要求，未登录能否访问受保护接口 | 给出受检路由与中间件 `path:line` |
| 越权与多租户 | SEC-02 | 检查 SQL/数据查询是否包含主体/租户强校验 | 引用查询语句证据 |
| 防注入与参数化 | SEC-03 | 检查是否存在拼接 SQL、Shell 执行、路径穿越 | 确认参数化写法 |
| 前端 XSS | SEC-04 | 检查是否存在不安全 HTML 注入与缺少消毒的富文本 | 确认使用了转义或 DOMPurify |
| CORS 与 CSRF | SEC-05 | 检查 CORS 域名配置，检查 Cookie 认证接口是否有 CSRF 防御 | 查看 CORS 策略 |
| SSRF 防范 | SEC-06 | 检查发起外部 HTTP 请求的逻辑是否限制内网 IP | 查看 IP 白名单/拦截代码 |
| 凭据硬编码 | SEC-08 | 检查本次改动是否带入了任何 Secret、Key、Token 明文字符串 | 确认通过环境变量读取 |
| 端点限流防刷 | SEC-09 | 检查高频/高危写入接口是否有并发与频次限制 | 确认限流器挂载点 |
| 依赖漏洞安全 | SEC-10 | 检查新引入的三方包是否有已知严重 CVE | 查看依赖版本锁定 |
