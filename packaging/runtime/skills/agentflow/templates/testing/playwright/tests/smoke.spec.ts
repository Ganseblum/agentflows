import { expect, test } from "@playwright/test";

/**
 * 可复制骨架：把 data-testid 换成目标仓真实值即可用。
 *
 * 每个用例对应 plan 注册表里的一条 AC（在用例名开头写 AC 编号，方便回写「来源」列），
 * 并覆盖边界清单里的一条或多条：连点 / 超时 / 竞态 / 空值 / 过期 / 退出失败。
 * 断言必须落在**用户能观察到的东西**上（可见文本、跳转后的 URL、元素可见性），
 * 不要断言「接口返回 200」——那是 api 层证据，关不掉用户可见路径。
 */

const EMAIL = process.env.E2E_EMAIL ?? "demo@example.test";
const PASSWORD = process.env.E2E_PASSWORD ?? "demo-pass";

test.describe("登录关键路径", () => {
  test("AC-01 正确凭据进入工作台", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("login-email").fill(EMAIL);
    await page.getByTestId("login-password").fill(PASSWORD);
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("workbench")).toBeVisible();
    await expect(page).toHaveURL(/\/workbench/);
  });

  test("AC-02 空值提交给出字段级错误而不是静默失败", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("login-email-error")).toBeVisible();
    // 反例保护：不能只靠「页面没崩」当通过
    await expect(page.getByTestId("login-submit")).toBeEnabled();
  });

  test("AC-03 错误凭据提示且不跳转（失败态可达）", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("login-email").fill(EMAIL);
    await page.getByTestId("login-password").fill("wrong-password");
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("login-error")).toBeVisible();
    await expect(page.getByTestId("workbench")).toHaveCount(0);
  });
});

test.describe("边界清单", () => {
  test("连点：提交按钮在请求中禁用，双击只发一次", async ({ page }) => {
    let submits = 0;
    await page.route("**/api/login", async (route) => {
      submits += 1;
      await new Promise((r) => setTimeout(r, 300)); // 人为拉长窗口，暴露未加锁的连点
      await route.continue();
    });
    await page.goto("/");
    await page.getByTestId("login-email").fill(EMAIL);
    await page.getByTestId("login-password").fill(PASSWORD);
    const submit = page.getByTestId("login-submit");
    await submit.click();
    await expect(submit).toBeDisabled();
    await submit.click({ force: true }).catch(() => {});
    expect(submits).toBe(1);
  });

  test("超时：后端不响应时给出可重试提示，不无限转圈", async ({ page }) => {
    await page.route("**/api/login", (route) => route.abort("timedout"));
    await page.goto("/");
    await page.getByTestId("login-email").fill(EMAIL);
    await page.getByTestId("login-password").fill(PASSWORD);
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("login-error")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("login-submit")).toBeEnabled();
  });

  test("过期：会话失效后受保护页面回到登录而不是空白页", async ({ page, context }) => {
    await context.addCookies([]);
    await page.goto("/workbench");
    await expect(page.getByTestId("login-submit")).toBeVisible();
  });

  test("退出失败：退出请求失败时本地会话仍被清除", async ({ page }) => {
    await page.route("**/api/logout", (route) => route.abort("failed"));
    await page.goto("/");
    await page.getByTestId("login-email").fill(EMAIL);
    await page.getByTestId("login-password").fill(PASSWORD);
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("workbench")).toBeVisible();
    await page.getByTestId("logout").click();
    await expect(page.getByTestId("login-submit")).toBeVisible();
  });
});
