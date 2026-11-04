# Playwright 可回归用例（browser 证据的可重复形态）

> **什么时候用**：`verification-grading.md` 要求用户可见路径的通过证据必须是 `browser` 或 `manual`。
> `manual` 每次都靠人重跑、`browser` 若只在会话里现场点一次，第二次改动就没人重跑——本模板把那次
> 现场点击固化成可回归的脚本，让「链路通没通」从一次性观察变成一条可重跑的命令。
>
> **铺开范围（2026-11-04 决定）**：先在一个**新项目**铺，老项目不动。理由是既有项目往往已有自己的
> e2e 栈或没有稳定入口，硬塞第二套 runner 会制造两套并行套件（`execution.md` 已把「平行套件」
> 列为反模式）。新项目从第一天就只有一套，才有单一真源。

## 文件

| 文件 | 用途 |
| --- | --- |
| `playwright.config.ts` | runner 配置：`baseURL` 从环境读、失败留 trace、CI 下重试一次 |
| `tests/smoke.spec.ts` | 关键路径 + 边界清单的可复制用例骨架（选择器一律 `data-testid`） |

## 落地步骤

1. 目标仓安装：`npm i -D @playwright/test && npx playwright install --with-deps chromium`。
2. 复制两个文件到目标仓 `e2e/`（或仓内既有的 e2e 目录），把 `tests/smoke.spec.ts` 里的
   `data-testid` 换成该仓真实值——**不要为了测试改产品代码加 testid 之外的钩子**。
3. 在 `package.json` 加 `"test:e2e": "playwright test"`，并把这条命令写进目标仓 `AGENTS.md`
   的「仓库检查命令」槽位（接入六问之一）。
4. 首次运行必须**真的跑通**再记为证据：把命令与逐字输出贴进 `run-*.md`，不贴摘要。

## 与测试链路的接法

- 用例库仍由 `test-planner` 写在 `<批次>/testing/<项目>-<功能>/plan-*.md`；本目录只提供**执行载体**，
  不代替用例设计（AC 权威在 plan 注册表的「来源」列，见 [`testcases.md`](../../../references/testcases.md)）。
- `test-executor` 跑 `npm run test:e2e`，把退出码、失败用例名与 trace 路径写进 `run-*.md` 的
  证据列。`fail` 不前进，与 `test-records.md` 的 bug 状态联动一致。
- 边界清单（连点 / 超时 / 竞态 / 空值 / 过期 / 退出失败）在计划中必选，不适用要逐项写理由；
  `tests/smoke.spec.ts` 里给了其中四条的写法，其余按同样形态补。

## 不作为什么

- 不替代 `manual` 目视验收：视觉与文案问题脚本判不了，批次收口仍需一次实操演示。
- 不替代 API 层用例：`api` 通过只许表述为「api 层通过」，反过来 `browser` 通过也不证明接口契约。
- 不在本模板里放凭据：账号从环境变量读，失败时不要打印完整请求体。
