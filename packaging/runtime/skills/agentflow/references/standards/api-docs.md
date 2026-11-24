# API 规范与接口契约标准（agentflow 通用底线）

> **定位**：与 `server-side.md`、`data-model.md` 配套的 API 设计与契约标准。agentflow 的 `design/be` 要求研发在编写任何新接口之前说明契约来源；本册提供**接口协议、路径动词、响应信封、统一错误模型、分页排序与版本演进**的硬判据。
> **来源**：吸收业界现代 RESTful 设计规范与 OpenAPI 规范最佳实践，重写为与 agentflow 评审链对齐的通用底线。
> **编号**：`API-01…API-08`，供 Reviewer 在 finding 里直接引用，或 Backend Engineer 编写接口规格时的强制基线。

## 0. 适用范围与何时必查

- **适用**：`spec/be`、`design/be`、所有 HTTP/REST/RPC 接口设计与实现、API 文档生成、前后端联调接口。
- **契约来源原则**：实现前必须明确契约来源（既有 openapi/IDL 定义、或在 `design/be` §1 中冻结定义）。自行在业务代码中发明未经审批的信封或错误码属于缺陷。

## 1. RESTful 资源与 HTTP 动词语义（API-01）

**MUST**
- **动词与幂等性匹配**：严格按照 HTTP 规范使用方法动词，保证语义与幂等契约对齐：
  - `GET`：纯读取，安全且幂等，严禁产生持久化副作用。
  - `POST`：创建新资源或执行非幂等业务操作。
  - `PUT`：全量替换资源，必须幂等。
  - `PATCH`：部分更新资源（提交需变更的字段子集）。
  - `DELETE`：删除指定资源，必须幂等（对已删除资源重复调用应返回成功或 404/204，不应报错 500）。
- **资源路径命名**：URL 路径必须全部小写、使用连字符（kebab-case），使用名词复数表达资源集合，层级关系清晰：
  - 正确：`/api/v1/users/{id}/order-items`
  - 错误：`/api/v1/getUserInfo`、`/api/v1/do_payment`（严禁在 RESTful 路径中使用 RPC 式动词，除非是极少数无对应资源的特殊动作，如 `/api/v1/users/{id}/actions:activate`）。

## 2. 契约先行与 OpenAPI 单一真源（API-02）

**MUST**
- **Schema-first 契约**：接口必须在实现前在 `spec/be` 或规范文档中完整冻结字段类型、空值策略、单位与枚举。禁止「边写代码边通知前端改字段」的反向设计。
- **OpenAPI / IDL 一致性**：项目使用 OpenAPI/Swagger 或 Protobuf/Thrift 时，IDL 文件是接口的单一真源。生成的客户端代码与服务端骨架必须从 IDL 自动构建，禁止手动修改生成的契约代码。

## 3. 统一响应信封与错误模型（API-03）

**MUST**
- **成功响应信封**：所有业务 API 统一使用结构化信封包装响应，包含数据载荷、业务状态与追踪 ID：
  ```json
  {
    "code": 0,
    "message": "success",
    "data": { ... },
    "requestId": "req-20261124-abcdef01"
  }
  ```
- **统一错误契约**：当请求失败时，必须返回具有可操作性的错误信息，明确区分 HTTP 状态码与业务错误码，禁止返回 HTML 错误页或空 500：
  ```json
  {
    "code": 40001,
    "message": "用户手机号格式不正确",
    "errorDetail": {
      "field": "phoneNumber",
      "reason": "MUST_BE_E164_FORMAT"
    },
    "requestId": "req-20261124-abcdef01"
  }
  ```
- **HTTP 状态码正确映射**：
  - `200 OK`：标准成功返回。
  - `201 Created`：新资源成功创建。
  - `204 No Content`：成功操作但无返回体（如删除成功）。
  - `400 Bad Request`：客户端参数校验失败。
  - `401 Unauthorized`：未提供有效认证凭据。
  - `403 Forbidden`：认证有效但无操作该资源的权限。
  - `404 Not Found`：目标资源不存在。
  - `409 Conflict`：并发冲突或业务规则互斥（如唯一键重复、状态机流转非法）。
  - `429 Too Many Requests`：超出限流阈值。
  - `500 Internal Server Error`：服务端未捕获异常（必须包含 requestId 供排查）。

## 4. 分页、过滤与排序契约（API-04）

**MUST**
- **标准化分页参数**：列表查询必须显式支持分页，严禁无限制全表返回。必须提供默认页大小（如 20）和最大上限（如 100）：
  - 偏移量分页：`page`（从 1 开始）、`pageSize`（最大限制强制截断）。
  - 游标分页（大数据流/防跳页）：`cursor`、`limit`。
- **标准分页响应信封**：
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [ ... ],
      "pagination": {
        "page": 1,
        "pageSize": 20,
        "total": 156,
        "totalPages": 8,
        "hasMore": true
      }
    },
    "requestId": "req-xxx"
  }
  ```
- **安全过滤与排序**：排序字段（`sortField`）和方向（`sortOrder: asc|desc`）必须在服务端设置白名单，禁止直接将客户端传入的字符串拼接到 SQL 的 `ORDER BY` 之后。

## 5. 接口版本控制与向下兼容（API-05）

**MUST**
- **URI 版本前缀**：主版本号变更（重大契约变更）必须在 URL 中显式体现（如 `/api/v1/...`）。
- **向后兼容原则（Backward Compatibility）**：在同一主版本号下：
  - 允许：增加新的可选请求参数、在响应体中增加新字段。
  - 禁止：删除已有字段、重命名已有字段、修改已有字段数据类型、将可选参数改为必填参数。
- **平滑废弃流程**：废弃旧接口时，必须在响应头中增加 `Deprecated: true` 以及 `Sunset` 截止日期头，并在文档中提供新接口的迁移指南，保留至少一个周期的兼容缓冲期。

## 6. 批量操作与部分成功语义（API-06）

**MUST**
- **批量接口明确事务边界**：批量操作接口（如 `/api/v1/items:batch-create`）必须在契约中明确是「全成功全失败（原子性事务）」还是「允许部分成功（Partial Success）」。
- **部分成功时提供清晰回执**：若允许部分成功，响应必须包含每个操作项的成功状态与失败原因：
  ```json
  {
    "code": 0,
    "data": {
      "successCount": 2,
      "failedCount": 1,
      "results": [
        { "id": "1", "status": "success" },
        { "id": "2", "status": "failed", "reason": "ITEM_ALREADY_EXISTS" }
      ]
    }
  }
  ```

## 7. 字段敏感性与数据脱敏（API-07）

**MUST**
- **权限裁剪**：接口返回的数据结构必须按调用方身份最小化裁剪。管理端接口与普通用户端接口不得共用同一个不过滤的全量实体 DTO。
- **禁止泄露敏感底表字段**：密码哈希、Salt、内部私钥、数据库内部逻辑删除标记等绝对禁止在 API 响应中透出。用户手机号、身份证号、银行卡号在公共 API 中必须服务端脱敏后返回。

## 8. 文档完备性与联调自检（API-08）

**MUST**
- 每个提供给外部或前端的接口文档必须包含：
  1. 准确的 HTTP Method 与完整的 URL Path。
  2. 完整的 Headers 声明（包含 `Authorization`、`Content-Type`、自定义业务头）。
  3. 请求体 JSON Schema（标注字段类型、必填项、默认值、枚举说明）。
  4. 成功响应示例（200 OK JSON）。
  5. 常见业务失败码表格（说明触发条件与客户端推荐处置）。
  6. 可直接运行的 `curl` 调用示例。
