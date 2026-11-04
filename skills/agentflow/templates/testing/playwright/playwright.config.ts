import { defineConfig, devices } from "@playwright/test";

/**
 * 复制到目标仓 e2e/playwright.config.ts。
 *
 * 三条刻意的默认值：
 * - baseURL 只从环境读，不写死端口——写死之后换端口就成了「测试坏了」而不是「配置变了」。
 * - 首次重试才留 trace：常态跑不产生大文件，失败时才有可看的证据。
 * - 失败时保留 video/screenshot：给 reviewer 的是可复核的原始产物，不是一句「已通过」。
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false, // 边界用例会改状态（如连续登录失败），并行会互相污染
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:5173",
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
    // 凭据从环境读：不要把这些值写进仓库，也不要在失败输出里打印完整请求体
    extraHTTPHeaders: process.env.E2E_EXTRA_HEADERS ?? {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.E2E_NO_WEB_SERVER
    ? undefined
    : {
        command: process.env.E2E_START_CMD ?? "npm run dev",
        url: process.env.E2E_BASE_URL ?? "http://127.0.0.1:5173",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
