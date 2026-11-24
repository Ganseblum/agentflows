# E2E 端到端自动化测试设计与执行模板

> 用法：目标仓涉及用户可见链路、多角色交互或核心业务闭环时，按本模板规范编写端到端（End-to-End）测试脚本与计划。
> 关联规范：落实 [`verification-grading.md`](../../references/verification-grading.md) 的 e2e 证据层级与 [`execution.md`](../../references/execution.md) 的浏览器实测纪律（方法细则由已安装的 Agentflow 插件提供）。
> **铁律**：严禁在 E2E 测试中使用硬编码睡眠（`sleep(3000)`）；必须基于元素可见性、网络请求完成或状态变迁进行显式等待。

## 0. E2E 适用场景与质量门禁

| 适用范围 | 不适用范围 |
| --- | --- |
| 核心业务主干链路（注册→下单→支付→查看账单） | 繁杂的底层数据模型单元验证（下沉至单测） |
| 跨页面多组件状态流转与路由跳转 | 单个表单控件的微小正则校验（下沉至组件测试） |
| 多端协同与多角色权限可见性（管理员 vs 普通用户） | 纯粹的第三方 SDK 逻辑（使用 Mock） |

---

## 1. 现代化 Playwright E2E 测试代码模板

### 1.1 Page Object Model (POM) 设计模式

将页面元素定位与业务动作封装在独立 Page 类中，保持用例代码的高可读性与可维护性：

```typescript
// tests/e2e/pages/LoginPage.ts
import { expect, type Locator, type Page } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    // 优先使用语义化选择器或 data-testid，严禁使用脆弱的深层 CSS/XPath
    this.usernameInput = page.getByTestId('login-username-input');
    this.passwordInput = page.getByTestId('login-password-input');
    this.submitButton = page.getByRole('button', { name: '登 录' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
    await expect(this.submitButton).toBeVisible();
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

### 1.2 完整测试用例编写

```typescript
// tests/e2e/specs/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('用户登录鉴权流程 (TC-E2E-AUTH-001)', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('正确凭据应成功登录并跳转至工作台', async ({ page }) => {
    // 监听网络请求或接口响应
    const responsePromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/auth/login') && resp.status() === 200
    );

    await loginPage.login('test_admin', 'StrongPassword123!');
    await responsePromise;

    // 验证路由跳转与关键页面元素展示
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.getByTestId('dashboard-header')).toContainText('欢迎回来');
  });

  test('错误密码应停留在登录页并给出友好错误提示', async ({ page }) => {
    await loginPage.login('test_admin', 'WrongPassword');

    // 验证错误提示浮现
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('用户名或密码错误');
    // 确认 URL 未发生未授权跳转
    await expect(page).toHaveURL(/.*\/login/);
  });
});
```

---

## 2. 状态隔离与登录凭据重用（Storage State）

为了避免数百个 E2E 用例每次都重复走 UI 登录流程消耗巨量时间，采用 Playwright 的会话持久化机制：

```typescript
// tests/e2e/setup/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('全局登录态预热', async ({ page }) => {
  await page.goto('/login');
  await page.getByTestId('login-username-input').fill(process.env.E2E_USER || 'admin');
  await page.getByTestId('login-password-input').fill(process.env.E2E_PASS || 'secret');
  await page.getByRole('button', { name: '登 录' }).click();
  
  await page.waitForURL('/dashboard');
  await expect(page.getByTestId('user-avatar')).toBeVisible();

  // 保存登录态 Cookie 与 LocalStorage
  await page.context().storageState({ path: authFile });
});
```

在测试配置 `playwright.config.ts` 中复用该状态：

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
```

---

## 3. E2E 执行验收与证据归档

依据 [`test-records.md`](../../references/test-records.md) 的要求，E2E 测试运行后产生的证据必须包含：
1. **测试控制台原始日志**（包含用例 ID、耗时与 exit 码）。
2. **失败用例快照**：自动截取的屏幕截图（`screenshot-TC-xxx.png`）。
3. **网络与操作 Trace**：Playwright Trace 压缩包，可供单步回放请求与 DOM 树。
