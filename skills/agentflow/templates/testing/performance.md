# 性能基线与负载压测模板

> 用法：目标仓涉及高并发接口、大数据量处理、批处理任务或上线前容量评估时，按本模板规范编写性能测试脚本与压测执行记录。
> 关联规范：落实 [`server-side.md`](../../references/standards/server-side.md) 资源有界、无单点与下游超时约束（标准分册在目标仓落点见 `.agentflow/standards/`）。

## 0. 性能指标基线定义（SLA）

任何性能压测必须在执行前明确定义以下四项核心量化指标：

| 指标 | 英文/单位 | 推荐生产基线要求 | 说明 |
|---|---|---|---|
| **吞吐量** | RPS / QPS | ≥ 目标峰值业务流量 × 2 | 系统在单位时间内成功处理的请求数 |
| **P95 延迟** | ms (毫秒) | ≤ 200ms | 95% 的请求响应耗时低于此阈值 |
| **P99 延迟** | ms (毫秒) | ≤ 500ms | 99% 的长尾请求耗时上限（核心防卡顿体验） |
| **错误率** | % | < 0.05% | 压测全周期内的 HTTP 5xx 或超时请求占比 |
| **系统资源** | CPU / 内存 | CPU ≤ 75%, 内存 ≤ 80% | 压测过程中服务宿主机的最大负载水位 |

---

## 1. 现代化 k6 压测脚本模板

采用轻量、脚本化、支持阶梯并发的 k6 编写负载测试用例：

```javascript
// tests/performance/order-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  // 并发阶梯设计：预热 -> 稳态峰值 -> 冲击 -> 恢复
  stages: [
    { duration: '1m', target: 50 },   // 1分钟内平滑预热至 50 并发用户
    { duration: '3m', target: 200 },  // 3分钟内加压至 200 并发峰值
    { duration: '5m', target: 200 },  // 保持 200 并发持续压测 5 分钟（稳态评估）
    { duration: '1m', target: 500 },  // 1分钟脉冲冲击至 500 并发（尖峰考验）
    { duration: '2m', target: 0 },    // 2分钟平滑降压冷却
  ],
  // 质量门禁阈值（任一不达标则压测判定为 FAILED）
  thresholds: {
    http_req_failed: ['rate<0.001'],         // 失败率必须小于 0.1%
    http_req_duration: ['p(95)<200', 'p(99)<500'], // 95% 请求在 200ms 内，99% 在 500ms 内
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    productId: 'prod_998811',
    quantity: 1,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.TEST_TOKEN || 'token_perf_mock'}`,
      'X-Request-Id': `perf-${__VU}-${__ITER}`,
    },
    timeout: '5s',
  };

  const res = http.post(`${BASE_URL}/api/v1/orders`, payload, params);

  check(res, {
    '状态码必须为 200 或 201': (r) => r.status === 200 || r.status === 201,
    '返回体包含成功订单号': (r) => r.json('data.orderId') !== undefined,
  });

  // 模拟真实用户思考时间（50ms ~ 150ms 随机停顿）
  sleep(0.05 + Math.random() * 0.1);
}
```

---

## 2. 性能压测执行记录模板

压测完成后，记录至 `docs/features/<批次>/testing/perf-run-<YYYY-MM-DD>-<NNN>.md`：

```markdown
# 性能压测执行报告（TC-PERF-<YYYYMMDD>-001）

## 1. 压测环境与参数
- **被测环境**：预发压测集群 (2 Pods, 2C4G, Pod Limit: 2C4G)
- **数据库/中间件配置**：RDS MySQL 4C8G (连接池 max: 100)，Redis 单节点 2G
- **压测工具与并发模型**：k6 v0.54.0，阶梯并发 (最大 500 VU，持续 12 分钟)
- **被测接口**：`POST /api/v1/orders`

## 2. 实测结果指标对照表

| 核心指标 | SLA 基线要求 | 实测结果 | 结论 (PASS/FAIL) |
|---|---|---|---|
| **峰值 QPS** | ≥ 1000 QPS | 1342 QPS | PASS |
| **平均延迟** | ≤ 80ms | 46.2ms | PASS |
| **P95 延迟** | ≤ 200ms | 138.5ms | PASS |
| **P99 延迟** | ≤ 500ms | 312.0ms | PASS |
| **错误率** | < 0.05% | 0.00% (0 / 480,210) | PASS |
| **服务 CPU 峰值** | ≤ 75% | 68.4% | PASS |
| **服务内存峰值** | ≤ 80% | 52.1% | PASS |

## 3. 观察到的瓶颈与改进建议
- **数据库连接池**：在 500 VU 冲击阶段，数据库连接池活跃连接数一度达到 89/100，建议高并发大促前将连接池上限扩充至 150。
- **慢查询排查**：未发现超过 100ms 的慢 SQL，联合索引命中率 100%。

## 4. 结论与签字
- **最终结论**：**PASS**（满足全部生产 SLA 性能指标，具备上线条件）。
- **执行人**：<姓名/角色>
- **日期**：<YYYY-MM-DD>
```
