---
recorded_at: 2026-11-05T12:34:31Z
source_revision: "agentflows@511b9ef7b66a4b23cb859345d1810981aa083f5b + feature-audit-fixes-0.41.0 未提交修复"
version: 0.41.0
outcome: partial
implementation_outcome: complete
measurement: none
review_tier: L2
---

# 0.41.0 审计修复交付决策

G01—G15 的实现修复、回归及独立评审已完成，三端本地插件载荷已同步为 0.41.0。G16 已补真实产品缺陷闭环、四类材料对照及本机浏览器/API样本，最后三项浏览器扩展变体未运行；新建替代空间的确认未收到，故整批结论为 partial，不能宣称全部验收完成。

工作分支为 `feature-audit-fixes-0.41.0`，没有提交、合并回 main、推送或远端发布。开发候选与原始证据保留于本轮证据目录，没有删除未提交工作。原审核的59分及正文不追溯改写，本轮没有重新评分。

## 逐项修复结果

| 来源 | 实现结果 | 验证与独审依据 | 当前结论 |
| --- | --- | --- | --- |
| G01 用户内容保全 | bytes归属块替换，保留附录、CRLF、尾空白与旧Claude指针外内容 | 同例旧2/14→新14/14，init20项，独立G01字节case，工具snapshot-2批准；[真实缺陷记录](issues/ISS-2026-11-05-初始化用户内容丢失.md) | 已修且验证 |
| G02 目标路径边界 | 拒绝用户symlink及祖先、slug/date逃逸，完整写前预检，立项目录独占 | CLI外部哨兵不变；slug1/80/81与首末界；generator22项；工具独审 | 已修且验证 |
| G03 冲突假绿 | 冲突整计划零写，旧manifest保留，完整期望清单及宿主记录不缩水 | conflict/check持续非零、显式接管后转绿；31CLI与init自测；工具独审 | 已修且验证 |
| G04 冻结对象混绑 | 严格MANIFEST、唯一稳定外部映射、snapshot/commit读取同一冻结bytes，差分同源 | OLD/NEW有效red→green、提交变更/删除、清单损坏与同名来源回归；brief22/snapshot15；工具独审 | 已修且验证 |
| G05 进程清理 | 固定未回收leader，POSIX组TERM/KILL有界清理；父正常退出遗子失败；查询失败尽力终止并拒绝完成 | E8/lifecycle真实red→green；输出超限；ps持续失败反例绿；31CLI；工具独审 | 已修且验证，保证限本组 |
| G06 沉默默认授权 | 必要行为/权限/高代价选择等明示答复；只允许已有授权低风险可逆细节作明示假设 | 具体情景独审；全局模板与项目规则一致；全局块已同步且新会话复述 | 已修且验证 |
| G07 退役能力主张 | 现行消费者改为人工义务或目标仓真实命令，不伪称旧schema/门已强制 | 原文分类、refs、独立具名消费者旧红新绿；规则独审 | 已修且验证 |
| G08 宿主依赖与多块 | Claude-only建立AGENTS依赖，foreign保留、唯一自有块幂等，畸形/重复拒绝 | 五宿主生成物、自测20项、foreign/Claude实际CLI；工具独审 | 已修且验证 |
| G09 轻量与选轨 | 一个六风险判据，--tier显式，light唯一README，full显式轨道补QA，prototype可选 | light1文件；BE+QA8、BE+FE+QA10；12组选轨×prototype补测；规则/工具独审 | 已修且验证 |
| G10 评审门槛与任务集合 | 作者无关风险阈值，受评任务及真实前置终态、后继可pending，映射沿原计划ID | task图闭包/unknown/cycle拒绝；完整12任务映射已独核；light消费者对照 | 已修且验证 |
| G11 重试、降级与状态单源 | 自检/独审/批准分开，去固定一次修复，L0明确partial，承接表只引用计划行 | 两轮真实changes_requested→聚焦修复→delta批准；状态指针文本与cost场景核对 | 已修且验证 |
| G12 安装内容核验 | 唯一载荷清单、递归文件/bytes/执行位；已有local/remote来源不自动重绑；超时分类JSON | 6类载荷、独立8根契约、删agents变异、假成功拒绝、source-drift拒绝；三端真实102文件核验 | 已修且验证；安装≠加载 |
| G13 用例权威 | Markdown注册表/详情唯一TC、AC来源、步骤/预期；YAML只引用case_id/automated及参数，run绑定版本 | 计划/run引用、TC/native对账、designQA不复制TC、轻量README同义节；规则独审 | 已修且验证 |
| G14 技术等效策略 | MUST限定业务不变量，技术/TTL/SQL/useRef等为带前提示例，乐观锁不充当天然幂等证明 | 规范逐条独审；原生DOM与进程内Map样本提供等效机制；未声称全部框架实测 | 已修且验证，样本范围明示 |
| G15 设计图语义 | as-is/to-be冲突先裁决，拒绝分支不继续换票，取消有恢复边，图表事件一致 | 逐事件语义独审与14项独立指定成本对照 | 已修且验证，非真实认证系统测试 |
| G16 真实效果证据 | 真实初始化缺陷red→green→独审→verified；四类材料旧新对照、小修原生TAP、UI/API/同键样本 | 原始JSON、96自测、31CLI、17补测、首次browser证据；[第二轮验收](testing/agentflows-audit-fixes/run-2026-11-05-002.md)保留3项未运行 | 部分完成，不能外推普遍提效 |

## 实现与验证

主源码与安装面已升级0.41.0，生成树不是权威源，构建使用与安装核验共享的载荷定义。最终运行载荷为102文件。主要变更在 `skills/agentflow/scripts/`、角色/规则/模板及安装适配，未新建独立运行时、角色、旧schema或强门禁。

- 全部七组最终自测96/96，完整stdout/stderr/argv/exit在 `E/final-selftest-*.log`。
- 跨工具31/31，含本轮评审追加的持续查询失败和两端超时JSON永久回归；`E/regression-evidence/supervisor-all-02/report.json`。
- 补充非浏览器17/17：12组选轨形态、缺case/skip/exit-only/stale报告拒绝、安装中source漂移；`E/supplemental-acceptance/report.json`。
- 根集合变异原生命令exit2，表示独立契约拒绝，不把六条未运行用例写成通过。
- 源/生成树/三端cache最终逐文件字节和执行位相等；没有把版本同号代替内容检查。
- 首次浏览器样本实际使用Ego space25/p1，顺序四态/表单/同键与实际指针双击已经运行。扩展补测在查不到space25时失败，未操作页面；只读清单证实剩余是用户空间及另一任务空间，没有接管。

`E` 为 `/Users/lihanghang1/.zcode/v2/artifacts/agentflows-fixes-20261105-184849`；[首轮执行记录](testing/agentflows-audit-fixes/run-2026-11-05-001.md)与[第二轮验收](testing/agentflows-audit-fixes/run-2026-11-05-002.md)按当时事实保留，不将后续批准和安装回填成首轮已完成。

## 独立评审与轮次

批准绑定：工具 `E/snapshots-tools/snapshot-2`（14文件），规则 `E/snapshots-docs/snapshot-2`（57文件）。两组不同只读reviewer均approved/complete。后续只改索引、事实记录与交付记录；产品代码与被审规则保持已批准内容，冻结核验原始输出为 `E/final-*-freeze.log`（索引后续导航变化另作交付记录核对，不冒充行为改动复用批准）。

| 轮次 | 决定与问题 | 处置 |
| --- | --- | --- |
| 工具首轮 | changes_requested/partial：ps持续不可用遗留进程；升级超时逃逸JSON；载荷期望同源 | 定向三文件修复；同assert红绿、永久用例、独立载荷根变异；不拿初次缺reports依赖错误算有效red |
| 规则首轮 | changes_requested/partial：light/真页/静态例外未贯通；TC/状态副本；旧检索命令现行主张 | 定向13文件修复；原计划真实ID映射；独立指定14项旧0/14→新14/14 |
| 工具delta | approved/complete，3项P1 closed，无新阻塞 | 只核delta、cost replay及完整任务/入口映射，沿用已过范围 |
| 规则delta | approved/complete，3项P1及FE示例P2 closed | 只核delta、独立语义演算与原始命令，不声称普遍宿主行为效果 |

元信息勘误：增量简报§4漏传上轮finding文件，仍显示“首轮无遗留”，本表及 `E/review-decisions.json`保留真实两轮，不用该标签抹掉负向结果；变异原生命令 exit=2，独立载荷契约拒绝签名已确认；外层驱动退出码未由原始输出明确给出，记为 `unverified`，不从未报非零推断退出0。

### review_roundtrips

以下 `at` 为精确模型决定时刻；原始结果未暴露可靠时刻，写 `unknown`。可观察的简报文件时间另存本轮证据 `review-roundtrips.json`，不替代决定时间。

```yaml
review_roundtrips:
  - at: unknown
    reviewer: REVIEW-TOOLS-041
    decision: changes_requested
    finding: "snapshot-1三项P1：ps失败遗留进程、安装超时JSON逃逸、载荷期望同源"
    resolution: "聚焦三文件修复，原场景与31项回归验证后提交snapshot-2"
  - at: unknown
    reviewer: REVIEW-DOCS-041
    decision: changes_requested
    finding: "snapshot-1三项P1：light消费者例外、TC/状态副本、退役检索现行命令"
    resolution: "聚焦13文件修复，14项指定旧红新绿、原任务映射核对后提交snapshot-2"
  - at: unknown
    reviewer: REVIEW-TOOLS-041
    decision: approved
    finding: "snapshot-2三项P1全部closed，无新增阻塞"
    resolution: "工具实现独审完成；不扩大为安装或父目标全部完成"
  - at: unknown
    reviewer: REVIEW-DOCS-041
    decision: approved
    finding: "snapshot-2三项P1及FE摘要P2全部closed"
    resolution: "规则文本独审完成；新会话与G16剩余验收另外记录"
```

## 本机同步

| 宿主/载体 | 已观察结果 | 仍未知 |
| --- | --- | --- |
| ZCode | 真实marketplace刷新及update，0.41.0；102/102；只读新会话实际报告0.41.0技能路径和全局块 | 当前旧会话不会因此被宣称已热更新；其他宿主/机器不外推 |
| Codex | 真实本地plugin add成功，0.41.0；102/102 | 新会话启动后账户usage limit，原始exit1；实际模型加载未取得结果 |
| Qoder | 既有本地缓存与唯一插件登记更新，0.41.0；102/102；其他插件和启用设置不变 | 无可用CLI/新会话加载证据 |
| ZCode全局 | 仅改已有块，块外与原文逐字相同，块内精确等于模板；新会话复述首行和版本，exit0 | 无其他全局文件改动；不推断全部规则在未来任务中均强制执行 |

## 断言与检查绑定

“初始化不删用户字节”对应G01 bytes/hash与重装；“不写授权根外”对应symlink/slug/date和外部哨兵；“评审对象冻结”对应OLD/NEW/删除/损坏；“任务结束无本组晚写”对应ready握手及时间窗后的进程/文件；“装进去是本版内容”对应102文件/执行位读回；“ZCode新会话已加载”对应不调用工具的真实新会话原文。任一断言为假时相应检查失败。

“这些方法普遍提高开发效率/降低缺陷率”仍为未验证；“四类代表任务全部扩展变体已覆盖”不成立；Codex/Qoder实际加载也未验证。它们使整批outcome保持partial，不与已修G01—G15混同。

## 剩余动作与恢复

- 得到新建替代浏览器空间的明确答复后，重跑已落盘的 `representative-browser-extended.mjs`，补TC23/24/25；不使用已消失的spaceId，也不接管其他用户或任务空间。
- Codex配额恢复后做同一只读加载探针；Qoder有可用新会话入口后核实际版本。不改账号/模型绕过配额。
- 没有可靠token/费用、完整模型工作时间和人工介入计量时写not-reported；没有同任务有无Agentflow因果对照，不给普遍提效结论。
- 停止了本轮四个已核实PID/命令的临时HTTP服务；未删除真实仓或未提交候选。全局备份在三项校验后只清本轮两份，原文仍保存在pre-install证据中。
- 回滚只可按已保全状态与当前内容核对后执行，不用 `git restore/reset --hard` 覆盖工作树；旧安装版本保留。
