# 前端与客户端 Mock 接入工程指南（fe-testing-mock）

> 用法：目标仓涉及前端单元测试、组件集成测试、本地独立开发或客户端混合应用（Hybrid App / WebView）时，按本指南配置 HTTP 与 JSBridge Mock。
> 关联规范：落实 [`api-docs.md`](../../references/standards/api-docs.md) 的统一响应信封契约，以及 [`frontend.md`](../../references/standards/frontend.md) 的错误三态要求（标准分册在目标仓落点见 `.agentflow/standards/`）。

## 0. Mock 硬边界纪律（MUST）

1. **严禁 Mock 代码泄露至生产构建**：Mock 注册代码与 Mock 静态数据必须完全由环境条件隔离（如 `process.env.NODE_ENV === 'test'` 或专用启动命令 `npm run dev:mock`），生产打包产物必须通过 Tree-shaking 彻底剔除 Mock 逻辑。
2. **契约强对齐**：Mock 返回的数据结构必须与服务端 Schema（OpenAPI 或 `api-docs.md` 响应信封）100% 对齐，包含 `code`, `message`, `data`, `requestId`，严禁在 Mock 中使用非标散装数据。
3. **支持异常分支覆盖**：Mock 不能只提供“快乐路径”（200 OK），必须具备快速模拟 401 登录失效、403 无权限、500 服务端报错、网络延迟与超时中断的能力。

---

## 1. HTTP 接口 Mock 标准：MSW (Mock Service Worker)

业界推崇的网络拦截方案，在网络传输层（Service Worker 或 Node.js http 模块）拦截请求，无需修改业务请求代码：

### 1.1 接口 Handler 定义 (`src/mocks/handlers.ts`)

```typescript
import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  // 模拟获取用户详情
  http.get('/api/v1/user/profile', async () => {
    // 模拟真实网络延迟 80ms
    await delay(80);

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        userId: 'usr_10029',
        username: 'alice_dev',
        role: 'admin',
        permissions: ['read:orders', 'write:orders'],
      },
      requestId: 'mock-req-profile-001',
    });
  }),

  // 模拟登录失败场景（供错误处理用例测试）
  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = (await request.json()) as { username?: string };

    if (body.username === 'invalid_user') {
      return HttpResponse.json(
        {
          code: 40001,
          message: '用户名或密码错误',
          errorDetail: { field: 'username', reason: 'USER_NOT_FOUND' },
          requestId: 'mock-req-login-err',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { token: 'mock-jwt-token-abcdef' },
      requestId: 'mock-req-login-ok',
    });
  }),
];
```

### 1.2 单元测试与 Node 环境接入 (`src/mocks/server.ts`)

```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// 在 vitest.setup.ts 或 jest.setup.ts 中配置生命周期
// beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());
```

---

## 2. 客户端 JSBridge Mock 桩规范（Hybrid / 桌面端）

在 Web 应用嵌入移动端 App 或桌面跨端容器（如 Electron、Tauri、Android WebView 或 iOS WKWebView）时，浏览器环境缺少原生的 `window.JSBridge` 对象。必须提供统一的开发与测试模拟桩：

```typescript
// src/mocks/jsbridge.mock.ts
interface BridgeCallback {
  (response: { code: number; data?: unknown; error?: string }): void;
}

export function setupMockJSBridge() {
  if (typeof window === 'undefined' || window.JSBridge) {
    return;
  }

  const registeredHandlers = new Map<string, (params: unknown) => unknown>();

  // 预设原生客户端核心能力 Mock
  registeredHandlers.set('getUserToken', () => ({
    token: 'mock-bridge-token-xyz',
    env: 'staging',
  }));

  registeredHandlers.set('getDeviceInfo', () => ({
    deviceId: 'DEV-MOCK-MAC-001',
    os: 'macOS',
    appVersion: '12.4.0',
  }));

  registeredHandlers.set('closeWebview', () => {
    console.log('[MockJSBridge] Native WebView close invoked.');
    return { success: true };
  });

  // 挂载全局 JSBridge 契约对象
  window.JSBridge = {
    invoke: (action: string, params: unknown, callback?: BridgeCallback) => {
      console.log(`[MockJSBridge] Action: ${action}, Params:`, params);
      const handler = registeredHandlers.get(action);

      setTimeout(() => {
        if (handler) {
          const result = handler(params);
          callback?.({ code: 0, data: result });
        } else {
          console.warn(`[MockJSBridge] Unhandled action: ${action}`);
          callback?.({ code: 404, error: `Action ${action} not implemented in mock.` });
        }
      }, 50); // 模拟原生跨进程通信延时
    },

    // 支持 Promise 化封装调用
    invokeAsync: async (action: string, params: unknown) => {
      return new Promise((resolve, reject) => {
        window.JSBridge.invoke(action, params, (res) => {
          if (res.code === 0) resolve(res.data);
          else reject(new Error(res.error || 'Bridge Error'));
        });
      });
    },
  };

  console.info('Mock JSBridge successfully mounted.');
}
```

---

## 3. 动态 Mock 控制与测试用例覆写（Test Overrides）

在特定测试用例中需要临时模拟“网络超时”或“数据为空”时，使用动态覆写机制，保持单测自闭环：

```typescript
// tests/user-profile.test.ts
import { test, expect } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import { server } from '../src/mocks/server';

test('接口超时 5s 时前端应展示网络重试浮窗', async () => {
  // 仅在当前用例中覆写为超长延迟
  server.use(
    http.get('/api/v1/user/profile', async () => {
      await delay(6000);
      return HttpResponse.json({ code: 0 });
    })
  );

  // 执行业务逻辑断言超时状态...
});
```
