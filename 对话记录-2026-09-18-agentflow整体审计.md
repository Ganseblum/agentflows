# 对话记录：Agentflow 整体机制审计

- **日期**：2026-09-18
- **工作区**：`/Users/lihanghang1/Desktop/TestProject/agentflows`（git 仓库，分支 `main`）
- **执行者**：ZCode（模型 `new-provider/glm-5.3`）
- **对话性质**：用户要求对 Agentflow 仓库做整体审查（只读评估）。全程未改动仓库任何文件；所有实验在 `/tmp` 一次性副本上进行，实验结束后副本已删除，真实工作树经复核未被触碰（`git status` 与会话开始时一致，`validate.py all` 保持 8×PASS）。

**收录说明（力求一字不拉）**：

- 用户消息、助手全部可见文本、全部工具调用（含命令与参数）、全部工具返回——包括四份子代理审计报告**全文**、全部复核实验的命令与输出、最终评估报告**全文**——均逐字收录。
- 唯一未逐字收录的：随首条用户消息由宿主注入的系统上下文（用户级/工作区 AGENTS.md 全文、环境信息、可用技能清单、工具 JSON Schema 等）。该部分属于宿主运行时注入内容而非对话产出；其中与对话直接相关的仓库规则（AGENTS.md）在仓库内可按路径查阅。
- 两个整文件读取结果（`skills/agentflow/SKILL.md` 与 `README.md` 的 `cat -n` 原文，合计约 276 行）为仓库内既有文件的逐字副本，为避免整段复制仓库文件，收录于**文末附录**；除这两处外全部内容逐字收录。

---

## 0. 用户消息（逐字）

> 整体看看当前的agentflow的整体机制、架构、agent loop、rag、编排、决策、以模治模等实现是否合理、还有什么问题以及不合理、冗余、bug、链路问题吗，

---

## 1. 助手 · 状态播报

> 我先把仓库整体摸一遍，再分头深挖各条链路，最后给你一份评估（只看不改）。

**工具调用 ① —— `Bash`（列仓库结构）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && echo "=== TREE (depth 3, no .git) ===" && find . -path ./.git -prune -o -type d -print | grep -v '/\.git' | sort | head -80 && echo && echo "=== FILE COUNT BY DIR ===" && find . -path ./.git -prune -o -type f -name '*.md' -print | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -40
```

**返回：**

```text
=== TREE (depth 3, no .git) ===
.
./.claude-plugin
./.codex-plugin
./.commandcode
./.commandcode/taste
./.zcode
./.zcode-plugin
./.zcode/skills
./agents
./docs
./evals
./evals/business
./evals/business/inputs
./evals/business/seeds
./evals/public
./evals/public/inputs
./examples
./examples/bug-records
./examples/evaluation-results
./examples/invalid
./examples/plans
./examples/policy
./examples/test-records
./mock
./mock/records
./mock/records/bugs
./mock/records/bugs/2026-09-17
./mock/records/bugs/archive
./mock/records/bugs/archive/2026-09-17
./mock/records/bugs/recurrence
./mock/records/episodes
./mock/records/episodes/2026-09-17
./mock/records/plans
./mock/records/reviews
./mock/records/reviews/demo-project-feature-demo
./mock/records/reviews/demo-project-feature-demo/archive
./mock/records/reviews/demo-project-feature-demo/archive/2026-09-17-001
./records
./records/bugs
./records/bugs/2026-09-14
./records/bugs/2026-09-15
./records/bugs/2026-09-17
./records/bugs/recurrence
./records/episodes
./records/episodes/2026-09-16
./records/episodes/2026-09-17
./records/episodes/2026-09-18
./records/improvement
./records/plans
./records/reviews
./records/tests
./schemas
./skills
./skills/agentflow
./skills/agentflow/agents
./skills/agentflow/references
./skills/agentflow/scripts
./skills/improve
./skills/improve/agents
./skills/improve/references
./tests
./tests/__pycache__
./tools
./tools/lab
./tools/lab/__pycache__

=== FILE COUNT BY DIR ===
  15 ./evals/public/inputs
  14 ./agents
   8 ./docs
   6 .
   5 ./mock/records/bugs/2026-09-17
   3 ./records/bugs/2026-09-17
   3 ./records/bugs/2026-09-15
   3 ./records/bugs/2026-09-14
   3 ./examples/invalid
   3 ./evals/business/inputs
   2 ./tools/lab
   2 ./skills/agentflow/references
   2 ./records/plans
   2 ./examples/test-records
   1 ./skills/improve/references
   1 ./skills/improve
   1 ./skills/agentflow
   1 ./schemas
   1 ./records/tests
   1 ./records/reviews
   1 ./records/improvement
   1 ./records/episodes
   1 ./records/bugs/recurrence
   1 ./records/bugs
   1 ./mock/records/reviews/demo-project-feature-demo/archive/2026-09-17-001
   1 ./mock/records/reviews/demo-project-feature-demo
   1 ./mock/records/plans
   1 ./mock/records/bugs/recurrence
   1 ./mock/records/bugs/archive/2026-09-17
   1 ./mock
   1 ./examples/policy
   1 ./examples/plans
   1 ./examples/bug-records
   1 ./examples
   1 ./evals/public
   1 ./evals/business
   1 ./evals
   1 ./.commandcode/taste
```

**工具调用 ② —— `Bash`（根目录文件与行数）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && echo "=== ROOT FILES ===" && ls -la && echo && echo "=== WC of key md ===" && find . -path ./.git -prune -o -type f \( -name '*.md' -o -name '*.py' -o -name '*.json' -o -name '*.txt' \) -print | grep -v '/\.git' | xargs wc -l 2>/dev/null | sort -rn | head -60
```

**返回：**

```text
=== ROOT FILES ===
total 3584
drwxr-xr-x@ 33 lihanghang1  526858981    1056 Sep 18 16:09 .
drwxr-xr-x@ 45 lihanghang1  526858981    1440 Sep 17 23:30 ..
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 17 15:22 .claude-plugin
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 17 15:22 .codex-plugin
drwxr-xr-x@  4 lihanghang1  526858981     128 Sep 17 20:23 .commandcode
-rw-r--r--@  1 lihanghang1  526858981    6148 Sep 17 11:44 .DS_Store
drwxr-xr-x  18 lihanghang1  526858981     576 Sep 18 16:08 .git
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 14 18:12 .github
-rw-r--r--@  1 lihanghang1  526858981     113 Sep 18 00:15 .gitignore
drwxr-xr-x@  3 lihanghang1  526858981      96 Sep 14 10:27 .zcode
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 17 15:22 .zcode-plugin
drwxr-xr-x  16 lihanghang1  526858981     512 Sep 18 11:26 agents
-rw-r--r--@  1 lihanghang1  526858981    4252 Sep 17 21:36 AGENTS.md
-rw-r--r--@  1 lihanghang1  526858981   10557 Sep 18 00:15 ANALYSIS-REPORT.md
-rw-r--r--@  1 lihanghang1  526858981   57408 Sep 18 16:07 CHANGELOG.md
-rw-r--r--@  1 lihanghang1  526858981  731467 Sep 17 21:15 command-code-session-22eff650.html
-rw-r--r--@  1 lihanghang1  526858981  488584 Sep 17 21:15 command-code-session-6c34dd64.html
-rw-r--r--@  1 lihanghang1  526858981  453355 Sep 17 21:15 command-code-session-a7e23bf3.html
-rw-r--r--@  1 lihanghang1  526858981   23324 Sep 18 00:15 CONSOLIDATED-REVIEW-REPORT.md
drwxr-xr-x  10 lihanghang1  526858981     320 Sep 18 16:04 docs
drwxr-xr-x   5 lihanghang1  526858981     160 Sep 17 14:53 evals
drwxr-xr-x   9 lihanghang1  526858981     288 Sep 18 00:55 examples
-rw-r--r--@  1 lihanghang1  526858981     633 Sep 18 16:07 marketplace.json
drwxr-xr-x@  4 lihanghang1  526858981     128 Sep 18 16:07 mock
-rw-r--r--@  1 lihanghang1  526858981    240 Sep 18 16:07 plugin.json
-rw-r--r--@  1 lihanghang1  526858981    3134 Sep 17 15:07 protected-paths.txt
-rw-r--r--@  1 lihanghang1  526858981    7615 Sep 17 15:48 README.md
drwxr-xr-x  10 lihanghang1  526858981     320 Sep 18 16:07 records
-rw-r--r--@  1 lihanghang1  526858981   16363 Sep 18 00:15 REVIEW-REPORT.md
drwxr-xr-x  12 lihanghang1  526858981     384 Sep 18 00:45 schemas
drwxr-xr-x   4 lihanghang1  526858981     128 Sep 14 10:27 skills
drwxr-xr-x@  4 lihanghang1  526858981     128 Sep 18 00:50 tests
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 14 10:27 tools

=== WC of key md ===
   19377 total
    3006 ./tests/test_lab_contracts.py
    2838 ./tools/lab/validate.py
     935 ./tools/lab/host_adapter.py
     763 ./CHANGELOG.md
     539 ./docs/next-session-handoff.md
     505 ./tools/lab/eval_runner.py
     409 ./docs/agent-roles.md
     406 ./docs/iteration-log.md
     367 ./skills/improve/references/release-record.schema.json
     335 ./records/plans/PLAN-BUSINESS-EVAL-001.md
     309 ./docs/spec-fact-check-design.md
     274 ./tools/lab/policy.py
     270 ./REVIEW-REPORT.md
     210 ./tools/lab/isolation.py
     183 ./CONSOLIDATED-REVIEW-REPORT.md
     183 ./ANALYSIS-REPORT.md
     162 ./docs/agent-product-boundary.md
     161 ./skills/improve/references/episode.schema.json
     158 ./records/bugs/2026-09-15/axios-interceptor-401-redirect-conflict.md
     156 ./skills/agentflow/SKILL.md
     151 ./schemas/bug-record.schema.json
     150 ./records/README.md
     142 ./schemas/evaluation-result.schema.json
     140 ./evals/business/README.md
     131 ./skills/improve/references/business-case.schema.json
     131 ./records/bugs/2026-09-17/unauthorized-git-integration-after-push-rejected.md
     123 ./records/bugs/2026-09-14/claude-json-schema-rejected.md
     122 ./skills/agentflow/references/contracts.md
     120 ./records/bugs/2026-09-14/eval-run-all-or-nothing.md
     120 ./README.md
     117 ./records/bugs/2026-09-17/concurrent-writers-same-branch.md
     115 ./schemas/comparison.schema.json
     115 ./records/bugs/2026-09-15/fault-injection-on-real-tree-checkout-revert.md
     110 ./records/bugs/2026-09-15/unverified-behavior-claims-recurring.md
     109 ./docs/self-improvement-design.md
     108 ./records/bugs/2026-09-17/stale-repo-state-in-status-advice.md
     106 ./docs/host-native-plugin-design.md
      99 ./tools/lab/README.md
      98 ./schemas/test-run.schema.json
      97 ./records/bugs/README.md
      96 ./examples/test-records/plan-2026-09-17-001.md
      93 ./agents/reviewer.md
      91 ./records/reviews/README.md
      90 ./skills/agentflow/references/roles.md
      90 ./mock/records/plans/PLAN-DEMO-SHARE-001.md
      87 ./agents/test-executor.md
      86 ./agents/test-planner.md
      85 ./tools/lab/artifact_digest.py
      81 ./skills/improve/SKILL.md
      81 ./AGENTS.md
      79 ./tools/lab/adapter-protocol.md
      79 ./records/tests/README.md
      78 ./mock/records/bugs/2026-09-17/full-record-demo.md
      78 ./agents/plan-architect.md
      72 ./schemas/test-plan.schema.json
```

---

## 2. 助手 · 状态播报

> 仓库不大但层次多，我先读核心编排文件，同时派几路并行深挖。

**工具调用 ① —— `Read`（读 `skills/agentflow/SKILL.md`，返回文件全文，收录在文末附录 A）：**

```text
file_path: /Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md
（返回 156 行，cat -n 格式全文 → 见附录 A）
```

**工具调用 ② —— `Read`（读 `README.md`，返回文件全文，收录在文末附录 B）：**

```text
file_path: /Users/lihanghang1/Desktop/TestProject/agentflows/README.md
（返回 120 行，cat -n 格式全文 → 见附录 B）
```

**工具调用 ③ —— `Bash`（列角色/技能/schema/工具目录）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && ls -la agents/ skills/agentflow/ skills/agentflow/agents/ skills/agentflow/references/ skills/agentflow/scripts/ skills/improve/ skills/improve/agents/ skills/improve/references/ schemas/ tools/lab/ tests/ 2>&1
```

**返回：**

```text
agents/:
total 152
drwxr-xr-x  16 lihanghang1  526858981   512 Sep 18 11:26 .
drwxr-xr-x@ 33 lihanghang1  526858981  1056 Sep 18 16:09 ..
-rw-r--r--@  1 lihanghang1  526858981  2289 Sep 16 18:16 backend-engineer.md
-rw-r--r--@  1 lihanghang1  526858981  1740 Sep 14 20:51 bug-fixer.md
-rw-r--r--@  1 lihanghang1  526858981  3344 Sep 16 23:06 bug-investigator.md
-rw-r--r--@  1 lihanghang1  526858981  4637 Sep 17 21:33 bug-recorder.md
-rw-r--r--@  1 lihanghang1  526858981  2640 Sep 14 20:50 candidate-engineer.md
-rw-r--r--@  1 lihanghang1  526858981  1154 Sep 14 19:51 evaluator.md
-rw-r--r--@  1 lihanghang1  526858981  1702 Sep 16 23:06 feedback-analyst.md
-rw-r--r--@  1 lihanghang1  526858981  2735 Sep 16 18:16 frontend-engineer.md
-rw-r--r--@  1 lihanghang1  526858981  5299 Sep 18 00:52 plan-architect.md
-rw-r--r--@  1 lihanghang1  526858981   991 Sep 14 19:51 release-governor.md
-rw-r--r--@  1 lihanghang1  526858981  7449 Sep 18 00:52 reviewer.md
-rw-r--r--@  1 lihanghang1  526858981  1597 Sep 16 23:06 technical-director.md
-rw-r--r--@  1 lihanghang1  526858981  5854 Sep 18 11:26 test-executor.md
-rw-r--r--@  1 lihanghang1  526858981  6155 Sep 18 11:26 test-planner.md

schemas/:
total 96
drwxr-xr-x  12 lihanghang1  526858981   384 Sep 18 00:45 .
drwxr-xr-x@ 33 lihanghang1  526858981  1056 Sep 18 16:09 ..
-rw-r--r--   1 lihanghang1  526858981  1081 Sep 14 10:27 adapter-case-result.schema.json
-rw-r--r--@  1 lihanghang1  526858981  5136 Sep 16 21:22 bug-record.schema.json
-rw-r--r--@  1 lihanghang1  526858981  4057 Sep 17 23:59 comparison.schema.json
-rw-r--r--   1 lihanghang1  526858981  5102 Sep 14 10:27 evaluation-result.schema.json
-rw-r--r--@  1 lihanghang1  526858981  2224 Sep 17 11:29 plan.schema.json
-rw-r--r--   1 lihanghang1  526858981   761 Sep 14 10:27 README.md
-rw-r--r--@  1 lihanghang1  526858981  2066 Sep 16 19:55 recurrence.schema.json
-rw-r--r--@  1 lihanghang1  526858981  2510 Sep 16 21:41 review.schema.json
-rw-r--r--@  1 lihanghang1  526858981  2705 Sep 18 00:45 test-plan.schema.json
-rw-r--r--@  1 lihanghang1  526858981  4027 Sep 18 00:45 test-run.schema.json

skills/agentflow/:
total 40
drwxr-xr-x  6 lihanghang1  526858981    192 Sep 18 14:38 .
drwxr-xr-x  4 lihanghang1  526858981    128 Sep 14 10:27 ..
drwxr-xr-x  3 lihanghang1  526858981     96 Sep 14 10:27 agents
drwxr-xr-x  4 lihanghang1  526858981    128 Sep 18 00:53 references
drwxr-xr-x@ 3 lihanghang1  526858981     96 Sep 16 18:10 scripts
-rw-r--r--@ 1 lihanghang1  526858981  19323 Sep 18 14:38 SKILL.md

skills/agentflow/agents/:
total 8
drwxr-xr-x  3 lihanghang1  526858981   96 Sep 14 10:27 .
drwxr-xr-x  6 lihanghang1  526858981  192 Sep 18 14:38 ..
-rw-r--r--  1 lihanghang1  526858981  259 Sep 14 10:27 openai.yaml

skills/agentflow/references/:
total 56
drwxr-xr-x  4 lihanghang1  526858981    128 Sep 18 00:53 .
drwxr-xr-x  6 lihanghang1  526858981    192 Sep 18 14:38 ..
-rw-r--r--@ 1 lihanghang1  526858981  15540 Sep 17 10:53 contracts.md
-rw-r--r--@ 1 lihanghang1  526858981   9824 Sep 18 00:53 roles.md

skills/agentflow/scripts/:
total 8
drwxr-xr-x@ 3 lihanghang1  526858981     96 Sep 16 18:10 .
drwxr-xr-x  6 lihanghang1  526858981    192 Sep 18 14:38 ..
-rwxr-xr-x@ 1 lihanghang1  526858981  2581 Sep 16 18:10 check-write-scope.sh

skills/improve/:
total 24
drwxr-xr-x  5 lihanghang1  526858981    160 Sep 18 00:08 .
drwxr-xr-x  4 lihanghang1  526858981    128 Sep 14 10:27 ..
drwxr-xr-x  3 lihanghang1  526858981     96 Sep 14 10:27 agents
drwxr-xr-x  8 lihanghang1  526858981    256 Sep 18 14:37 references
-rw-r--r--@ 1 lihanghang1  526858981  10651 Sep 18 00:08 SKILL.md

skills/improve/agents/:
total 8
drwxr-xr-x  3 lihanghang1  526858981   96 Sep 14 10:27 .
drwxr-xr-x  5 lihanghang1  526858981  160 Sep 18 00:08 ..
-rw-r--r--  1 lihanghang1  526858981  330 Sep 14 10:27 openai.yaml

skills/improve/references/:
total 64
drwxr-xr-x  8 lihanghang1  526858981   256 Sep 18 14:37 .
drwxr-xr-x  5 lihanghang1  526858981   160 Sep 18 00:08 ..
-rw-r--r--@ 1 lihanghang1  526858981  2566 Sep 17 14:53 business-case.schema.json
-rw-r--r--  1 lihanghang1  526858981  2342 Sep 14 10:27 candidate.schema.json
-rw-r--r--@  1 lihanghang1  526858981  3240 Sep 18 14:37 episode.schema.json
-rw-r--r--  1 lihanghang1  526858981  1290 Sep 14 10:27 eval-case.schema.json
-rw-r--r--@  1 lihanghang1  526858981  5151 Sep 18 00:08 evidence-and-release.md
-rw-r--r--  1 lihanghang1  526858981  8131 Sep 14 10:27 release-record.schema.json

tests/:
total 288
drwxr-xr-x@  3 lihanghang1  526858981      96 Sep 18 00:50 __pycache__
drwxr-xr-x  4 lihanghang1  526858981     128 Sep 18 00:50 .
drwxr-xr-x  33 lihanghang1  526858981    1056 Sep 18 16:09 ..
-rw-r--r--@  1 lihanghang1  526858981  146162 Sep 18 00:50 test_lab_contracts.py

tools/lab/:
total 512
drwxr-xr-x  9 lihanghang1  526858981     288 Sep 18 08:23 __pycache__
drwxr-xr-x 12 lihanghang1  526858981     384 Sep 18 08:22 .
drwxr-xr-x   3 lihanghang1  526858981      96 Sep 14 10:27 ..
-rw-r--r--@  1 lihanghang1  526858981    3568 Sep 14 16:26 adapter-protocol.md
-rw-r--r--   1 lihanghang1  526858981    2869 Sep 14 10:27 artifact_digest.py
-rw-r--r--@  1 lihanghang1  526858981  21654 Sep 17 21:42 eval_runner.py
-rw-r--r--@  1 lihanghang1  526858981  43080 Sep 17 21:42 host_adapter.py
-rw-r--r--@  1 lihanghang1  526858981   8881 Sep 17 14:48 isolation.py
-rw-r--r--   1 lihanghang1  526858981  12316 Sep 14 10:27 policy.py
-rw-r--r--@  1 lihanghang1  526858981   6534 Sep 17 15:43 README.md
-rw-r--r--@  1 lihanghang1  526858981  13946 Sep 17 15:37 seed_grader.py
-rw-r--r--@  1 lihanghang1  526858981 128151 Sep 18 08:22 validate.py
```

---

## 3. 助手 · 工具调用（无文本播报）

**工具调用 ① —— `Bash`（核对五份 manifest 版本一致性）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && echo "=== MANIFEST VERSIONS ===" && for f in plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json .zcode-plugin/plugin.json marketplace.json; do echo "--- $f"; cat "$f"; echo; done && echo "=== README version mentions ===" && grep -rn "0\.[0-9]\.[0-9]" README.md | head -20
```

**返回：**

```text
=== MANIFEST VERSIONS ===
--- plugin.json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "agentflow",
  "version": "0.7.4",
  "description": "Host-native multi-agent development and evidence-driven improvement workflows for coding agents."
}

--- .claude-plugin/plugin.json
{
  "name": "agentflow",
  "description": "Run host-native development and governed improvement workflows with specialized implementation, evaluation, and release roles.",
  "version": "0.7.4",
  "author": {
    "name": "Ganseblum"
  },
  "keywords": [
    "multi-agent",
    "development-workflow",
    "architecture",
    "code-review",
    "continuous-improvement"
  ]
}

--- .codex-plugin/plugin.json
{
  "name": "agentflow",
  "version": "0.7.4",
  "description": "Run host-native multi-agent development and governed evidence-driven improvement workflows.",
  "author": {
    "name": "Ganseblum"
  },
  "keywords": [
    "multi-agent",
    "workflow",
    "code-review",
    "audit"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "Agentflow",
    "shortDescription": "Coordinate multi-agent coding with review and traceability.",
    "longDescription": "Use the coding host's native agents as a bounded engineering team with frontend, backend, technical director, supervisor, and reviewer roles. Agentflow defines the workflow and contracts without invoking a separate orchestration CLI or requiring another provider credential.",
    "developerName": "Ganseblum",
    "category": "Developer Tools",
    "capabilities": [
      "Multi-agent task coordination",
      "Frontend and backend role delegation",
      "Independent implementation review",
      "Architecture decision gates",
      "Evidence-driven improvement candidates"
    ],
    "defaultPrompt": "Use $agentflow to coordinate this coding task with bounded delegation, independent review, and a concise decision record."
  }
}

--- .zcode-plugin/plugin.json
{
  "name": "agentflow",
  "version": "0.7.4",
  "description": "Host-native multi-agent development and evidence-driven improvement workflows: supervisor, frontend/backend engineers, technical director, reviewer, bug roles, plan architect, and governed improvement roles.",
  "author": {
    "name": "Ganseblum"
  },
  "license": "MIT",
  "skills": "skills",
  "agents": "agents"
}

--- marketplace.json
{
  "name": "agentflow-local",
  "version": 1,
  "description": "Local marketplace for testing the Agentflow plugin in ZCode.",
  "plugins": [
    {
      "name": "agentflow",
      "source": "./",
      "description": "Host-native multi-agent development and evidence-driven improvement workflows with specialized implementation, evaluation, and release roles.",
      "version": "0.7.4",
      "author": {
        "name": "Ganseblum"
      },
      "category": "developer-tools",
      "keywords": [
        "multi-agent",
        "development-workflow",
        "code-review",
        "continuous-improvement"
      ]
    }
  ]
}

=== README version mentions ===
README.md:23:Version `0.6.0` provides:
README.md:116:The source checkout currently declares version `0.6.0`. This is not by itself proof that a host is
```

**工具调用 ② —— `Bash`（运行仓库确定性检查，第一次尝试失败）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && timeout 600 python3 tools/lab/validate.py all 2>&1 | tail -40; echo "EXIT=$?"
```

**返回：**

```text
/bin/bash: line 2: timeout: command not found
EXIT=0
```

---

## 4. 助手 · 工具调用（无文本播报）：重跑检查 + 派出第一、二路并行审计子代理

**工具调用 ① —— `Bash`（重跑仓库确定性检查）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows && python3 tools/lab/validate.py all 2>&1 | tail -50; echo "EXIT=${PIPESTATUS[0]}"
```

**返回：**

```text
PASS schemas
PASS examples
PASS evals
PASS artifacts
PASS protected
PASS manifests
PASS docs
PASS tests
EXIT=0
```

**工具调用 ② —— `Agent`（子代理①：角色系统与编排契约审计，`Explore` 类型）—— 派发提示词全文：**

```text
You are auditing the repository at /Users/lihanghang1/Desktop/TestProject/agentflows (a multi-agent workflow plugin called "Agentflow"). Your scope: the ROLE SYSTEM and the ORCHESTRATION/AGENT-LOOP contracts. Read these files fully:

- /Users/lihanghang1/Desktop/TestProject/agentflows/agents/*.md (all 14 role files)
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/roles.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/contracts.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/scripts/check-write-scope.sh

Produce a critical assessment (this is a review, not a summary). Specifically identify, with file:line evidence:

1. CONTRADICTIONS: places where two documents state incompatible rules (e.g. SKILL.md says X, roles.md or a role file says Y). Pay attention to: who may write where, who closes a bug, review gate waivability, parallelism rules, browser automation ownership, write_scope enforcement.
2. REDUNDANCY: the same rule restated in 3+ places. Quantify how much text is duplicated between SKILL.md, references/contracts.md, references/roles.md, docs/agent-roles.md, and the individual agents/*.md frontmatter+body. Note where duplication creates drift risk (i.e. one copy already differs from another).
3. GAPS in the agent loop: what happens on worker failure/timeout, what happens if a subagent returns a malformed result contract, retry/bounded-loop semantics, who owns state between steps, resumability. Is there any actual state machine or is it all prose?
4. ROLE OVERLAP: roles whose responsibilities substantially overlap (e.g. reviewer vs evaluator vs technical-director; bug-investigator vs reviewer; test-planner vs test-executor). Are 14 roles justified by distinct capability, or are some ceremonial?
5. ENFORCEABILITY: which rules are actually machine-checked vs merely stated as prose the model is asked to obey. List the "hard boundaries" and mark each as ENFORCED (name the check) or PROSE-ONLY.
6. Frontmatter/tool-allowlist issues: does each role's declared `tools` match what its body instructs it to do? (e.g. a role told to run a command but without Bash, or a read-only role that has Write.)

Report concrete findings with file:line citations. Be specific and skeptical. Do not fix anything. Do not summarize what the system does — focus on what is wrong, contradictory, redundant, or unenforced. Length: detailed, but every claim needs a citation.
```

**工具调用 ③ —— `Agent`（子代理②：测量与治理工具审计，`Explore` 类型）—— 派发提示词全文：**

```text
You are auditing the repository at /Users/lihanghang1/Desktop/TestProject/agentflows (a multi-agent workflow plugin called "Agentflow"). Your scope: the MEASUREMENT / SELF-IMPROVEMENT ("以模治模" — using models to govern models) TOOLING. Read these files:

- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/validate.py (2838 lines — read strategically: the CLI dispatch, the check registry, the required-entry sets, and any place it can exit 0 without actually checking)
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/eval_runner.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/host_adapter.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/seed_grader.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/policy.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/isolation.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/artifact_digest.py
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/README.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/tools/lab/adapter-protocol.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/protected-paths.txt

Produce a critical assessment with file:line evidence. Specifically:

1. FAIL-OPEN / SILENT-SKIP PATHS: every place a check can pass (exit 0) without having verified anything — SKIP branches, empty iteration over an empty set, try/except that swallows, missing-file treated as OK, unreachable/never-registered checks. This is the most important finding class.
2. THE GATE: protected-paths.txt + isolation.py check-diff. Can it actually be bypassed? Consider: file renames, symlinks, path normalization, `..`, case sensitivity on macOS (APFS is case-insensitive by default), files added rather than modified, directory-vs-file entries, and whether check-diff is ever run automatically or only if a human remembers.
3. DETERMINISM claims: seed_grader.py claims deterministic offline scoring. Check the matching strategy (substring anchors?) for false positives/negatives and gameability — could a candidate trivially "hit" seeds by echoing anchor text? Is there any anti-gaming control?
4. DEAD CODE / UNREACHABLE: functions, CLI subcommands, config keys, schema fields that nothing calls or reads. Check whether eval_runner/host_adapter's business path has ever actually been exercised (look for evidence: records, result artifacts, tests).
5. COMPLEXITY SMELL: validate.py is 128KB in one file, tests/test_lab_contracts.py is 146KB in one file. Assess whether the structure is sustainable — count the number of distinct check functions, look for copy-pasted check bodies.
6. BUGS: actual defects — wrong comparison operators, unhandled None, path joins that break, regexes that don't anchor, ordering assumptions, exception types.

Report concrete findings with file:line citations. Be specific and skeptical. Do not fix anything. Prioritize by severity. Every claim needs a citation.
```

**工具调用 ② 的返回 —— 子代理审计报告①（角色系统与编排契约），全文逐字如下：**

# Agentflow Role System & Orchestration Contracts — Critical Audit

## 1. CONTRADICTIONS

### 1.1 "Supervisor alone" vs. "the supervisor's own change always opens a non-waivable review gate" — the sharpest one

Three documents state incompatible rules for the single most common task shape:

- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/roles.md:12` — routing table row: `| Single-layer small fix, clear reproduction | Supervisor alone |`
- `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md:34` — `| 单层小修、复现明确 | Supervisor 自己做 |`
- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md:128` — "when the supervisor wrote part of a change — **small or material** — the independent reviewer gate for it is mandatory and cannot be waived (hard boundary 1)."
- `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md:48` — same rule in Chinese, 14 lines *after* the routing table that contradicts it.

"Supervisor alone" and "mandatory non-waivable independent reviewer for anything the supervisor wrote" cannot both be true. `docs/agent-roles.md` contradicts itself internally between line 34 and line 48. `roles.md:12` is the row an agent will actually read first (it is the top row of the routing table), and it wins by position.

Note also `SKILL.md:105`: "A small change (see *Judgement calls made checkable* below) can stay with the supervisor" — reinforcing the wrong reading, with the correction hidden 23 lines later at `SKILL.md:128`.

### 1.2 Who may collapse the reviewer step for a small bug — three different answers

- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md:25-28` — "the supervisor may combine **the investigator or recorder step**, but must preserve the same diagnosis, regression, **review**, and state evidence." Review is explicitly *not* collapsible.
- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/roles.md:19` — "Small bug with a verified reproduction | Fixer + **Supervisor-side check**".
- `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md:79` — the risk-tailoring table puts "**可由 Supervisor 自检**" (supervisor may self-check) directly in the **Reviewer** column.

`docs/agent-roles.md:79` licenses exactly the substitution `SKILL.md:26` forbids. Worse, the same row's Investigator column says "Supervisor 可合并" — so a supervisor that merges investigation *and* self-checks review is following `docs/agent-roles.md` and violating `SKILL.md`.

### 1.3 Browser automation ownership — stated as a universal fact in one place, host-conditional in another, and contradicted by the route directly above it

- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md:53` — "browser automation is main-conversation-only **on Claude Code and ZCode**" (host-scoped fact).
- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md:110` — "**When** the host's browser automation is main-conversation-only (subagents cannot load it)…" (conditional).
- `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/test-executor.md:33` — "the host's browser automation is main-conversation-only and a subagent cannot load it" (**unconditional, stated as fact**).

`test-executor.md:33` asserts a host capability as established fact, which is itself a violation of hard boundary 12 (`contracts.md:22`: "A claim about how a tool, framework, or host behaves is a hypothesis until a minimal experiment reproduces it"). On a host where subagents *can* load browser tooling, the role file is simply wrong and there is no conditional to fall back on.

Separately, `SKILL.md:50-51` tells `test-executor` to run "scripted automation first (Playwright or the project's own e2e suite, **headless**)" — that *is* browser automation, performed by a subagent, two lines before `SKILL.md:53` declares browser automation main-conversation-only. The same contradiction sits inside `test-executor.md` between route 1 (lines 29-32) and route 3 (lines 33-36). The rule the authors mean is "the *host's browser-use skill* is main-conversation-only"; what is written is broader and false.

### 1.4 Who may write under `records/` — the ownership Notes are stale

- `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/bug-fixer.md:19` — "| `records/` | ❌ | **Recorder and Plan Architect own those** |"
- `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/candidate-engineer.md:20` — identical string, identical claim.
- But `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/test-planner.md:16` and `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/test-executor.md:16-17` both declare write ownership under `records/tests/`, and `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md:17-18` lists Test Planner and Test Executor as records writers.

Two role files carry a two-owner statement that has been false since the 0.7.0 testing chain landed. This is drift already realized, not hypothetical.

### 1.5 Budget discipline: "every role" vs. "every writable role" vs. what is actually in the files

- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/contracts.md:90` — "**Every role** reserves its last turn for the worker result."
- `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/agent-roles.md:368` — "此外**每个可写角色**必须遵守预算纪律" (every *writable* role).
- Reality: 8 of 14 role files carry a Budget-discipline paragraph. Missing from `agents/bug-investigator.md`, `agents/evaluator.md`, `agents/feedback-analyst.md`, `agents/release-governor.md`, `agents/reviewer.md`, `agents/technical-director.md`.

Hard boundary 11 (`contracts.md:21`) — "A run stopped by a turn, time, or token budget reports `partial`" — binds all roles, but the six read-only roles are never told this in their own prompt, and their result enums have no `partial` value at all (`reviewer.md:93` = `approved|changes_requested|blocked`; `evaluator.md:18` = `better|neutral|worse|invalid`; `release-governor.md:16` = `promote|revise|reject|rollback`). A truncated reviewer run has **no legal way to report truncation**. It must emit one of three verdicts or nothing.

### 1.6 `cost` / `duration` exist in the contract and in zero role prompts

`/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/references/contracts.md:75-76` adds `cost` and `duration` to the worker result, and `docs/agent-roles.md:201-203` explains the rationale. But the only two role files that enumerate the result fields — `agents/backend-engineer.md:24` and `agents/frontend-engineer.md:26` — list "status, summary, files, checks, risks, and next_action" and omit both. Grep across `agents/*.md` finds no role instructed to report them. The field was added to the contract document and never propagated.

### 1.7 Hard boundary 2 (no re-delegation) is absent from half the roles — including the one with `Bash`

`contracts.md:12` states "A worker does not re-delegate either". The clause "This role does not delegate further" appears in 7 of 14 role files (`bug-recorder`, `bug-fixer`, `backend-engineer`, `frontend-engineer`, `candidate-engineer`, `plan-architect`, `test-planner`). Missing from `agents/test-executor.md` — which holds `Bash` and `Write` (`test-executor.md:6`) and is the role most likely to shell out. Also missing from `reviewer`, `technical-director`, `evaluator`, `feedback-analyst`, `release-governor`, `bug-investigator`.

### 1.8 Parallel writers on branches vs. per-instance merge authorization

`SKILL.md:106` instructs: "parallel writers get separate branches or worktrees, one writer holds a branch at a time". `SKILL.md:108` then has the supervisor "resolve cross-layer conflicts" at integration. But `contracts.md:13` (hard boundary 3) and `SKILL.md:153` say `git merge`/`rebase`/`cherry-pick` "requires **per-instance** user authorization, not an inference from an earlier instruction." So the parallelization strategy the method mandates creates, by construction, an integration step that requires a fresh user approval on every batch — and step 6 never mentions needing it. `docs/agent-roles.md:241-247` repeats both halves without reconciling them either.

### 1.9 `protected-paths.txt` protects the *improvement* gate but not the *development* gate

`contracts.md:16` (hard boundary 6): "Never let an agent edit the gate that judges its own work: evaluator rules, release policy, **approval thresholds**…". `/Users/lihanghang1/Desktop/TestProject/agentflows/protected-paths.txt:42-43` protects `agents/evaluator.md` and `agents/release-governor.md` — but **not** `agents/reviewer.md`, and `protected-paths.txt:14-15` explicitly rules it out: "Role prompts that only describe how work is done are NOT protected." Yet `reviewer.md` *is* the approval gate for the entire development line (`SKILL.md:110`). A candidate-engineer improving the loop can rewrite the checklist that judges development work; the boundary text says it cannot.

## 2. REDUNDANCY — quantified

Five surfaces restate the same rule set: `skills/agentflow/SKILL.md` (156 lines), `skills/agentflow/references/contracts.md` (122), `skills/agentflow/references/roles.md` (90), `docs/agent-roles.md` (409), the 14 `agents/*.md` bodies (~650 lines total), plus `AGENTS.md` (81) and `README.md` as further partial copies. `docs/agent-roles.md` is described nowhere as a translation but functions as a full Chinese mirror of `SKILL.md` + `contracts.md` + `roles.md` combined.

Rule families restated **3+ times**:

| Rule | Locations | Count |
|---|---|---|
| Worker summary ≠ verification / compile-before-accept | `contracts.md:14`, `contracts.md:86`, `contracts.md:88`, `SKILL.md:109`, `docs/agent-roles.md:90-94`, `docs/agent-roles.md:361-362`, `AGENTS.md:8-18` | **7** |
| Design-completeness triad (timing / exception matrix / release order) | `contracts.md:58-62`, `SKILL.md:39-41`, `agents/plan-architect.md:61-71`, `agents/reviewer.md:78-85`, `agents/technical-director.md:16`, `docs/agent-roles.md:173-184` | **6** |
| Browser automation is main-conversation-only | `SKILL.md:52-53`, `SKILL.md:110`, `roles.md:16`, `roles.md:79`, `agents/test-executor.md:33-36`, `docs/agent-roles.md:38`, `docs/agent-roles.md:290-293` | **7** |
| Implicit-behavior / registration-point check | `contracts.md:42-48`, `roles.md:33`, `roles.md:39`, `roles.md:59`, `agents/frontend-engineer.md:22`, `agents/backend-engineer.md:22`, `agents/bug-investigator.md:19-25`, `agents/reviewer.md:30`, `agents/plan-architect.md:42`, `docs/agent-roles.md:151-159` | **10** |
| Author is not the verifier / non-waivable gate | `contracts.md:11`, `SKILL.md:110`, `SKILL.md:128`, `roles.md:25`, `docs/agent-roles.md:46`, `docs/agent-roles.md:48`, `docs/agent-roles.md:405-409` | **7** |
| Provenance enum + justification rules | `roles.md:57`, `agents/bug-investigator.md:30-41`, `agents/bug-recorder.md:51-55`, `agents/feedback-analyst.md:16`, `docs/agent-roles.md:121-129`, `SKILL.md:84-88` | **6** |
| Budget discipline ("last turn for the result", `partial`) | 8 role files + `contracts.md:90-94` + `docs/agent-roles.md:368-369` + `skills/improve/SKILL.md:71` | **11** |
| `write_scope` enforcement by diff | `contracts.md:24`, `SKILL.md:109`, `docs/agent-roles.md:144-149`, `check-write-scope.sh:4-8` | **4** |
| Routing table (identical 10-row table) | `roles.md:10-21` and `docs/agent-roles.md:32-42` | **2 verbatim** |
| Bug chain sequence | `SKILL.md:21-28`, `roles.md:18`, `docs/agent-roles.md:40`, `docs/agent-roles.md:57-69`, `README.md:61` | **5** |

**Drift already realized in the duplicates** (each is a copy that has diverged from another copy):

1. `agents/bug-fixer.md:19` / `agents/candidate-engineer.md:20` ("Recorder and Plan Architect own `records/`") vs. `docs/agent-roles.md:17-18` (four owners). §1.4.
2. `contracts.md:90` "Every role" vs. `docs/agent-roles.md:368` "每个可写角色" vs. 8/14 files. §1.5.
3. `contracts.md:75-76` `cost`/`duration` vs. `backend-engineer.md:24` / `frontend-engineer.md:26` field lists. §1.6.
4. `roles.md:12` / `docs/agent-roles.md:34` "Supervisor alone" vs. `SKILL.md:128`. §1.1.
5. `docs/agent-roles.md:79` "Reviewer: 可由 Supervisor 自检" vs. `SKILL.md:26`. §1.2.
6. `SKILL.md:53` host-scoped vs. `test-executor.md:33` unconditional. §1.3.
7. `SKILL.md:15-16` lists 10 plugin agent ids for Claude Code/ZCode and omits `candidate-engineer`, `evaluator`, `feedback-analyst`, `release-governor` — yet `roles.md:21`, loaded by the same SKILL, routes to all four by name. An agent following `SKILL.md` has no agent id for the roles `roles.md` tells it to use.

The `docs` validator does **not** catch any of this. `tools/lab/validate.py:2263-2345` (`validate_doc_consistency`) checks exactly five things: frontmatter `name` == filename; `agentflow:<role>` resolves to a file; `schemas/*.schema.json` paths exist; an AGENTS.md pre-0.5.0 tripwire string; and that the *set of schema filenames mentioned* in `docs/agent-roles.md` equals that in `contracts.md` (line 2334-2344). That last check is the only "Chinese mirror parity" assertion and it compares **schema filename sets only** — no rule, table, or enum parity. The docstring at line 2272 claims it verifies "the Chinese mirror keeps section parity with its English contract documents"; the code does not do that.

## 3. GAPS IN THE AGENT LOOP

**There is no state machine. It is entirely prose plus one Markdown table.** The only structured state carrier is the plan board (`agents/plan-architect.md:34-39`, `records/plans/README.md`), with a 5-value status enum (`☐ ◐ ☑ ⚠ —`) checked by `tools/lab/validate.py:559-668`. Everything else in the loop — briefs, results, retries, failures — is unstructured text in a conversation.

**3.1 Worker failure/timeout is undefined below the `partial` verdict.** `contracts.md:90-94` covers budget exhaustion. Nothing covers: subagent crash, host tool error, a worker that returns nothing, or a worker whose turn cap (`maxTurns`) fires. `contracts.md:93-94` says "Treat a missing result … as the same defect: the work is not accepted, and the next brief starts from the last verified state" — but "the last verified state" is not defined anywhere, and no artifact records it (see 3.4). There is no timeout value, no escalation path, and no distinction between "worker failed" and "worker's change failed a check".

**3.2 A malformed result contract has no handling rule at all.** The worker result (`contracts.md:70-79`) and review result (`contracts.md:104-109`) have **no JSON Schema** — confirmed: `schemas/` contains only `adapter-case-result`, `bug-record`, `comparison`, `evaluation-result`, `plan`, `recurrence`, `review`, `test-plan`, `test-run`. `schemas/review.schema.json:37-39` looks like it covers the review gate but its `required` list (`review_id`, `target_project`, `target_feature`, `source_revision`, `reviewed_docs`, line 8) shows it is the **external-document second-pass review record**, not the development-line review verdict. So: if a reviewer returns `decision: looks fine`, or a worker returns prose with no `status`, nothing detects it. The single rule that comes closest — `contracts.md:93` "a `complete` whose files do not exist in the workspace" — covers one specific malformation.

**3.3 Retry semantics are a one-line heuristic, not a bounded loop.** `SKILL.md:111` — "**Repair once**: when review requests changes, assign one focused repair round and review again. Keep the loop bounded." The bound is `once`, but `SKILL.md:110` says "Any later change that affects user-visible behavior re-opens the gate" — an unbounded outer loop wrapping a bounded inner one. The only counter is the "two consecutive failures with the same cause" rule (`contracts.md:20`, `SKILL.md:134-138`), whose trigger requires comparing "the same check id or command, and the same error text or `error_kind` after timestamps and absolute paths are stripped" — a normalization the model performs by hand, with no retry counter persisted anywhere. There is no attempt count in the brief, the result, or the plan row.

**3.4 State ownership between steps is unassigned, and the resumability claim depends on it.** `SKILL.md:148` — "A session that dies mid-orchestration resumes from the versioned plan under `records/plans/` … each task row carries its status and evidence, so the state is re-derivable". But:
- `agents/plan-architect.md:37` describes write-back mechanics ("Progress is written back **only** into the 状态 and 证据回写 columns (minimal diff); never rewrite a completed task row") — yet `roles.md:71` says the architect "writes the plan only — the supervisor decides approval, assigns execution".
- The implementing roles are forbidden from `records/`: `agents/backend-engineer.md:18`, `agents/frontend-engineer.md:18`, `agents/bug-fixer.md:19`.
- So during execution, **no role has declared write ownership of the status column**. The supervisor must do it, but nothing in `SKILL.md`'s 10 steps instructs it to update the plan board after step 5, 6, 7, or 8.

Consequence: the resume point `SKILL.md:148` relies on is written by nobody on the documented path. `SKILL.md:148` hedges this itself — "re-derive each work package's state from the workspace … and treat a package without observed evidence as not started" — i.e. the actual recovery mechanism is re-deriving from `git diff`, and the plan board is decorative for resumption.

**3.5 The delegation baseline revision — required by hard boundary 14 — is not a field in any contract.** `contracts.md:24` and `SKILL.md:109` both require recording "the baseline revision at delegation time" so the write-scope diff can run. The worker task brief (`contracts.md:29-35`) has seven fields: `objective`, `write_scope`, `read_scope`, `constraints`, `deliverable`, `verification`, `dependencies` — **no baseline**. The worker result (`contracts.md:71-78`) has no revision either. The one machine check that enforces boundary 14 takes the baseline as `argv[1]` (`check-write-scope.sh:33`) and there is no contract field that carries it. The enforcement is structurally unable to run from the artifacts the method produces.

**3.6 No join key between plan tasks and worker results.** Plan tasks carry IDs `T01…` (`plan-architect.md:35`, enforced at `validate.py:585-594`). The worker brief and result carry no `task_id`. Evidence write-back into the 证据回写 column therefore has no automatable source, and a parallel batch's results cannot be mechanically mapped back to rows.

**3.7 `execution-coordinator` is named as the owner of every hard orchestration property — and does not exist.** `SKILL.md:34-35`, `roles.md` (implied), `docs/agent-roles.md:211-213`, `docs/agent-roles.md:237-239`: "Durable queues, leases, dependencies, retries, and resumable parallel batches are the future `execution-coordinator` role; today the plan file plus the repository state is the only checkpoint." This is an honest disclosure, but it means retries, leases, and resumable batches are documented as **out of scope**, not as gaps — while `SKILL.md:111` and `contracts.md:20` simultaneously assert retry rules. The retry semantics are both "prose rules that exist" and "a future role's job".

## 4. ROLE OVERLAP — are 14 roles justified?

**Genuinely distinct by capability (tool surface + independence):** `frontend-engineer` / `backend-engineer` (write+Bash), `reviewer` (read-only, independence-critical), `technical-director` (read-only, pre-implementation), `plan-architect` (Write-only, one path), `test-planner` / `test-executor` (distinct: designer has no Bash, executor has Bash — the split is enforced by frontmatter, `test-planner.md:7` vs `test-executor.md:6`).

**Overlapping or ceremonial:**

- **`frontend-engineer` vs `backend-engineer`.** Identical frontmatter (`Read, Glob, Grep, Write, Edit, Bash`, `maxTurns: 30`), identical artifact-ownership table shape, identical closing paragraphs. The only substantive difference is the mechanism list in the implicit-behavior paragraph (`frontend-engineer.md:22` names interceptors/route guards; `backend-engineer.md:22` names middleware/ORM hooks) and one extra paragraph at `frontend-engineer.md:24` on runtime wiring. These are the *same* role with a domain hint; the scope is set by the brief's `write_scope`, not by the role.
- **`bug-fixer` vs the engineers.** `bug-fixer.md` frontmatter is identical to `backend-engineer.md` except `maxTurns: 20`. Its distinguishing content — "make the smallest compatible fix, and add or update a focused regression check" (`bug-fixer.md:22-26`) — is a brief constraint, not a capability. The only real difference is the extra ownership rows (`bug-fixer.md:18,20`: evaluator/holdout ❌, git history ❌) which arguably *should* apply to the engineers too and don't.
- **`reviewer` vs `technical-director`.** Identical tool surface (`Read, Glob, Grep` / disallow `Bash, Write, Edit`). Both demand the same design-completeness triad (`reviewer.md:78-85` vs `technical-director.md:16` — near-identical sentences including "retry cells must name owner, count, backoff, and idempotency precondition; blanket fallback phrases are rejected"). The distinction is *temporal* (before vs after implementation), not capability. `technical-director.md` is 16 lines and its only unique output is "implementation sequence" — `SKILL.md:104` itself warns "Do not use this role as a ceremonial approval step," which is an admission that it reads as ceremonial.
- **`reviewer` vs `evaluator`.** Both read-only verdict-returners with no Bash. `evaluator.md:16` ("Verify from immutable result records that baseline and candidate use the same host, model, permissions, fixtures, and repeat count") is a genuinely distinct capability — comparing frozen records — so this pair is justified.
- **`evaluator` vs `release-governor`.** Both read-only (`Read, Glob, Grep`), both return a single enum, both consume the same frozen evidence. `release-governor.md:14` ("Confirm candidate identity, baseline identity, evaluation-suite revision, evidence provenance, risk class, guardrails, required approvals, rollout limits, and rollback target") overlaps heavily with `evaluator.md:16`. The separation-of-duties argument at `roles.md:90` is asserted, not demonstrated: both are subagents of the same supervisor with the same tools reading the same files. Per hard boundary 7 (`contracts.md:17`), "Never claim isolation from prompt text alone" — this separation is exactly prompt-text isolation. `release-governor.md` is 16 lines; `evaluator.md` is 18.
- **`bug-investigator` vs `reviewer`.** Both read-only, no Bash, both produce attributed findings with citations. `bug-investigator.md:19-25` (enumerate implicit mechanisms at registration points) is verbatim the same discipline as `reviewer.md:30`. The distinguishing artifact is the provenance/attribution taxonomy (`bug-investigator.md:30-41`) — a *briefing* difference, deliverable by scoping the reviewer role, exactly as `roles.md:53` already argues for security/test-depth/documentation audits: "Specialist audits … run through the same reviewer role with a brief scoped to the matching specialist checklist … they do not need separate roles." **That argument applies with equal force to `bug-investigator`, and the system does not apply it.**
- **`feedback-analyst` vs `bug-investigator`.** Both read-only (`Read, Glob, Grep`), both produce attribution + "the smallest falsifiable hypothesis" (`feedback-analyst.md:18` vs `bug-investigator.md:32`). `feedback-analyst.md` is 18 lines, of which line 16 (provenance filtering) duplicates `bug-investigator.md:30-41`. This is a reviewer-mode-shaped role.
- **`bug-recorder`.** Its capability is "write one Markdown file to one assigned path with correct frontmatter." That is a formatting task. `roles.md:90` concedes the improvement roles "are inert list noise" for most users; the same is defensible for `bug-recorder`, whose output is fully specified by `schemas/bug-record.schema.json` and machine-validated afterwards anyway.

**Verdict:** by *capability* (tool allowlist × read-only-ness × independence-from-author), there are **five** distinct kinds: writer-with-shell, record-writer-without-shell, read-only-analyst, read-only-verdict-returner, and shell-runner-that-must-not-edit-source. The 14 roles collapse to those 5 plus briefing differences. `roles.md:53` states the collapse principle explicitly for reviewer specialities and then declines to apply it to `bug-investigator`, `feedback-analyst`, `technical-director`, and `release-governor` — all of which are sub-100-word briefing variants of roles that already exist.

## 5. ENFORCEABILITY — hard boundaries, ENFORCED vs PROSE-ONLY

`AGENTS.md:40-41` is the honest baseline: "`tools` and `disallowedTools` are enforced by the host, `maxTurns` is declared but unverified." `docs/agent-roles.md:24-26` also concedes "路径级强制仍依赖宿主工具权限… 矩阵的作用是让 Supervisor 的检查可逐行执行，而不是替代宿主强制."

| # | Boundary (`contracts.md`) | Status |
|---|---|---|
| 1 | Producer never approves/closes its own change; supervisor's own change ⇒ non-waivable gate (`contracts.md:11`) | **PROSE-ONLY.** No check binds author identity to reviewer identity. No schema records who authored what. Contradicted by `roles.md:12` (§1.1). |
| 2 | Delegation never expands authority; no re-delegation (`contracts.md:12`) | **PARTIALLY ENFORCED.** The "no new tools" half is enforced by host `tools`/`disallowedTools` frontmatter (`AGENTS.md:40`; `docs/agent-roles.md:365-367` claims "ZCode 实测生效"). The "no re-delegation" half is **PROSE-ONLY** and absent from 7 role prompts (§1.7). |
| 3 | No push/deploy/publish/merge without per-instance authorization (`contracts.md:13`) | **PROSE-ONLY.** No hook exists — the only `settings.json` in the tree (`/Users/lihanghang1/Desktop/TestProject/agentflows/.commandcode/settings.json`) is a per-command permission allowlist for a different client, with `"deny": []`. `test-executor` holds `Bash` (`test-executor.md:6`) and its ownership table has **no** git-history row (contrast `bug-fixer.md:20`). |
| 4 | Worker summary ≠ verification; unreproducible check = not run (`contracts.md:14`) | **PROSE-ONLY** as a rule; the *checks themselves* are enforced (`python3 tools/lab/validate.py all`, `AGENTS.md:11`). Nothing forces the supervisor to run them. |
| 5 | Artifact failing its compile step is returned (`contracts.md:15`) | **ENFORCED for record artifacts only** — `validate.py artifacts` → `validate_workspace_artifacts` (`tools/lab/validate.py:1920`). Not enforced for code deliverables. |
| 6 | Never edit the gate judging your own work (`contracts.md:16`) | **ENFORCED for the improvement loop**: `tools/lab/isolation.py check-diff` (`isolation.py:145`) reads `protected-paths.txt`, and `validate.py protected` (`validate.py:2348`) asserts coverage. **NOT enforced for the development gate**: `agents/reviewer.md` is deliberately unprotected (`protected-paths.txt:14-15`) — §1.9. |
| 7 | Never claim isolation from prompt text alone (`contracts.md:17`) | **PROSE-ONLY** — and self-violating: the evaluator/governor separation (`roles.md:90`) rests on prompt text. |
| 8 | Recorded evidence is never rewritten; corrections append (`contracts.md:18`) | **PARTIALLY ENFORCED.** `test-executor` is denied `Edit` (`test-executor.md:7`) with the append-only rationale stated at `test-executor.md:21-23` — a genuine tool-level enforcement. But `bug-recorder.md:31` requires "refresh `updated_at` on every later change", i.e. in-place mutation of records, and the `## 变更记录` append rule (`contracts.md:64`) is unchecked. |
| 9 | No role started without a job (`contracts.md:19`) | **PROSE-ONLY.** Unfalsifiable as written. |
| 10 | No cycling on unchanged inputs; two same-cause failures stop the loop (`contracts.md:20`) | **PROSE-ONLY.** No attempt counter exists in any artifact (§3.3). |
| 11 | Budget exhaustion ⇒ `partial`, never `complete` (`contracts.md:21`) | **PROSE-ONLY**, and `maxTurns` is explicitly unverified (`AGENTS.md:41`, `docs/agent-roles.md:394-396`). Six roles have no `partial` value in their return enum (§1.5). |
| 12 | Tool/host behavior claims are hypotheses until reproduced (`contracts.md:22`) | **PROSE-ONLY.** Violated by `test-executor.md:33` (§1.3). |
| 13 | Absence claims require reading the authoritative sink (`contracts.md:23`) | **PROSE-ONLY.** |
| 14 | Write scope enforced by diff, not restatement (`contracts.md:24`) | **PARTIALLY ENFORCED.** `skills/agentflow/scripts/check-write-scope.sh` exists and is executable (mode 755). But: (a) it is never invoked by any hook or by `validate.py` — the only non-narrative references in the tree are the doc mentions at `SKILL.md:109` and `docs/agent-roles.md:146`; (b) it requires a baseline revision that no contract field carries (§3.5); (c) its own header (`check-write-scope.sh:19-21`) concedes "Paths already dirty at delegation time also appear as changes; either delegate from a clean tree or **subtract the known-dirty paths when reading the report**" — i.e. the mechanism `SKILL.md:109` calls "the enforcement" ends in a human subtraction step; (d) it has no `-C`/repo argument, so for `bug-fixer`, which works "inside the assigned candidate workspace" (`bug-fixer.md:15`), the caller must know to invoke it from that worktree — undocumented. |

**Actually machine-checked, end to end** (`validate.py:2819-2828` = `all`): JSON-schema validity of the 9 record schemas; example records; eval-suite cases; record instances under `records/` including unknown-entry rejection (`validate.py:1948-1960`); protected-path coverage; manifest name/version agreement across five manifests; the five doc-consistency assertions (`validate.py:2263-2345`); the repository's own unit tests. Plus: plan task-ID uniqueness, dependency cycle detection, status enum, and blocked-unresolved-item-vs-`approved` (`validate.py:559-668`); the `attribution: workflow_policy|role_prompt ⇒ provenance: agentflow` implication (`schemas/bug-record.schema.json:111`); `test-run` decision enum with "pass requires zero fail and zero blocked in the summary; the checker enforces this" (`schemas/test-run.schema.json:79-82`).

**Not machine-checked at all:** which role wrote which path (`validate_workspace_artifacts` validates content, never authorship — so "Supervisor assigns every record path explicitly", repeated in `bug-recorder.md:17`, `plan-architect.md:17`, `test-planner.md:17`, `test-executor.md:19`, `AGENTS.md:63`, is PROSE-ONLY ×5); the worker brief; the worker result; the development-line review verdict; the final decision record; the claims ledger.

## 6. FRONTMATTER / TOOL-ALLOWLIST MISMATCHES

| Role | `tools` | Mismatch |
|---|---|---|
| `reviewer` | `Read, Glob, Grep` (`reviewer.md:6`), `disallowedTools: Bash, Write, Edit` (`:7`) | **`reviewer.md:26` "Inspect the actual diff" and `:28` "Review the actual diff and surrounding code" — a diff requires `git diff`, i.e. Bash, which `:12` explicitly denies ("runs no commands"). Nothing in the file says the diff must be *supplied*; `SKILL.md:110` doesn't say so either. The reviewer is instructed to inspect an artifact it has no tool to produce.** |
| `bug-recorder` | `Read, Glob, Grep, Write` (`:6`), disallow `Bash, Edit` (`:7`) | **`bug-recorder.md:43-44` "When a record is rejected, move it into `records/bugs/archive/<same-date-dir>/`." A move needs `mv` (Bash) or write+delete; the role has neither delete nor Bash.** Also `:31` "refresh `updated_at` on every later change" requires modifying an existing file with `Write`-only (full overwrite) after `Edit` was removed. |
| `plan-architect` | `Read, Glob, Grep, Write` (`:6`), disallow `Bash, Edit` (`:7`) | **`plan-architect.md:37` "Progress is written back **only** into the 状态 and 证据回写 columns (**minimal diff**); never rewrite a completed task row." A minimal-diff column edit is precisely what `Edit` does and `Write` cannot — `Write` rewrites the whole file.** Also `:28` "refresh `updated_at` on every revision" — same problem. Also `:23` says the plan is "the shape the supervisor validates against `schemas/plan.schema.json` and the plan checker" — the architect cannot run the checker (no Bash), correctly delegated, but the file never says to hand it back for validation until `:78`. |
| `test-planner` | `Read, Glob, Grep, Write` (`:6`), disallow `Bash, Edit` (`:7`) | `:30` "`test_version` (bump on every revision)" and "refresh `updated_at` on every revision" — in-place revision of an existing plan with no `Edit`. Same class as `plan-architect`. |
| `test-executor` | `Bash, Read, Write, Glob, Grep` (`:6`), disallow `Edit` (`:7`) | **Ownership table `:18` "Source code, product tests, configuration ❌ never edit" and `:19` "Any other path in `records/` ❌" vs. body `:44-45` "**Register the suite before creating its case files**" and `:30` "write the specs against the case steps" — registering a suite means writing into the target project's registry/config, which the table forbids. The table and the body of the same file disagree.** Also: holds `Bash` with **no** git-history prohibition row (contrast `bug-fixer.md:20`) and **no** "does not delegate further" clause — the only writer-with-shell role missing both. Also `Edit` is disallowed but `:48` says "do not inline a raw locator into the case: record it as a registry gap" — consistent, fine. |
| `bug-investigator` | `Read, Glob, Grep` (`:6`), disallow `Bash, Write, Edit` (`:7`) | `SKILL.md:22-23` says the investigator "establishes a **reproducible** symptom"; `roles.md:57` "returns a structured diagnosis with **reproduction steps**". It cannot run a reproduction. `bug-investigator.md:16-17` handles this correctly ("describe the exact check for the supervisor to run") — so the *role file* is right and the *two summary documents* overstate its capability. |
| `technical-director` | `Read, Glob, Grep` (`:6`) | Consistent — `:14` correctly routes command output through the supervisor. |
| `backend-engineer` / `frontend-engineer` / `bug-fixer` / `candidate-engineer` | `Read, Glob, Grep, Write, Edit, Bash` | Tooling matches the body. But all four hold `Bash` with `"deny": []` in the only settings file present, so hard boundary 3 (no push/publish) is unenforced for all of them; only `bug-fixer.md:20,25` restates it in-prompt. |
| `evaluator` / `release-governor` / `feedback-analyst` | `Read, Glob, Grep`, disallow `Bash, Write, Edit` | Consistent with their bodies. Note `evaluator.md:12` "runs no candidate-controlled commands" is weaker than the frontmatter (it runs *no* commands) — harmless, but the prose implies a discretion the tools remove. |

**Systemic frontmatter observations:**
- Every role declares `model: inherit` and a `maxTurns` value (12–30) that `AGENTS.md:41` and `docs/agent-roles.md:394-396` both admit is "declared but unverified". Six roles carry no compensating prose budget rule (§1.5), so for `reviewer` (`maxTurns: 15`), `technical-director` (12), `evaluator` (20), `release-governor` (12), `feedback-analyst` (15), `bug-investigator` (15) there is **neither** a verified host limit **nor** an in-prompt truncation rule.
- The `Edit`-removal pattern is applied inconsistently: it is justified for `test-executor` (`:21-23`, append-only history) but applied to `plan-architect`, `test-planner`, and `bug-recorder` where the body explicitly requires in-place revision. Three of the four `Edit`-denied writing roles are told to do something `Edit` exists for.

## Summary of the most load-bearing defects

1. `roles.md:12` / `docs/agent-roles.md:34` license "Supervisor alone" for the most frequent task shape, directly negating the system's flagship invariant at `SKILL.md:128` / `contracts.md:11`.
2. Hard boundary 14's enforcement (`check-write-scope.sh`) cannot run from the artifacts the method produces: the brief contract (`contracts.md:29-35`) has no baseline-revision field, and the script is invoked by nothing.
3. The two core agent-loop contracts — worker result and review verdict — have no schema and no validator, so 11 of 14 hard boundaries are PROSE-ONLY.
4. There is no state machine; the plan board is the only structured state and no role owns writing to it during execution (`plan-architect.md:37` vs `roles.md:71` vs `backend-engineer.md:18`).
5. `docs/agent-roles.md` is an unmarked 409-line mirror of three other documents; the only parity check on it (`validate.py:2334-2344`) compares schema filenames and nothing else, while its docstring (`validate.py:2272`) claims section parity.

*（子代理①运行统计：约 1,465,638 tokens，46 次工具调用，约 13.6 分钟。）*

**工具调用 ③ 的返回 —— 子代理审计报告②（测量与治理工具，"以模治模"），全文逐字如下：**

# Audit: Agentflow measurement / self-improvement tooling ("以模治模")

Scope read in full: `isolation.py`, `seed_grader.py`, `policy.py`, `artifact_digest.py`, `eval_runner.py`, `host_adapter.py`, `protected-paths.txt`, both `.md` files; `validate.py` read strategically (header/constants, `SchemaValidator`, every `validate_*` entry point, the CLI dispatch, plus the full artifact/protected/tests/installed bodies).

**Headline:** the tooling is unusually well-commented and the *negative* test discipline is real, but the loop's two load-bearing claims do not hold. (1) The gate is advisory — nothing runs it. (2) The measurement is the candidate's own self-report, and the business-slice answer key ships inside the tree the candidate under test is handed.

## S0 — Measurement validity: the metrics that drive promote/reject are self-reported by the subject

Every metric in `policy.py`'s decision comes from the model under test, schema-shape-checked and otherwise unverified.

- `host_adapter.py:463-479` — `parse_structured_output` validates the host's JSON against `schemas/adapter-case-result.schema.json` and returns it. That is the only gate.
- `schemas/adapter-case-result.schema.json` requires `accepted`, `first_pass_review`, `correction_count`, `escaped_defects`, `permission_violations`, `unnecessary_delegation`, `tool_failures` — all supplied by the model.
- `eval_runner.py:213-294` (`validate_adapter_response`) checks presence/coverage/counts, never plausibility.
- `eval_runner.py:133-149` (`summarize`) sums those self-reports into the eight `METRIC_NAMES`.
- `policy.py:26-35, 138-151` compares exactly those sums to decide `promote` / `revise` / `reject`.

So `permission_violations` — a guardrail — is the answer to "did you violate permissions?" asked of the violator. `permission_args` (`host_adapter.py:382-393`) sets host flags but nothing counts denials; the code even notes it *observed* `permission_denials` and did not read it (`host_adapter.py:571-573`).

Only the business slice partially repairs this: `host_adapter.py:724-730` overwrites `accepted` and `escaped_defects` from the grader. `first_pass_review` (a `HIGHER_IS_BETTER` primary metric, `policy.py:26`) stays self-reported even there — see `host_adapter.py:860-863`, which files the self-report into progress JSONL and keeps it in the result.

For `evals/public`, **nothing** is overwritten. 100% of the promotion evidence is the candidate grading itself.

## S0 — The answer key is inside the candidate's working directory

`host_adapter.py:594-597` runs `claude --plugin-dir <workspace>` with `cwd=workspace` (`host_adapter.py:603`). The workspace must be the candidate plugin tree — i.e. a `git worktree` created by `isolation.py:104-120`, which does `git worktree add --detach` and therefore checks out the whole tree.

`evals/` is tracked (42 files, verified via `git ls-files evals`), so the worktree contains:
- `evals/business/seeds/BT-00N.seeds.json` — the literal seed anchors
- `evals/public/AF-0NN.json` — objectives, acceptance criteria, guardrails

`isolation.layout_errors` (`isolation.py:42-75`) only guarantees that *repository*, *candidate*, *holdout*, *business_root* do not nest. It says nothing about the answer key being a file inside the candidate tree. `protected-paths.txt:43` protects `evals/` from being *edited*; it does not stop it being *read* by the subject.

Concretely for BT-001, the three anchors are `"静默重投"`, `"≤30"`, `"§12.4"` (`evals/business/seeds/BT-001.seeds.json`). A model with filesystem read access to its own cwd reaches 100% recall by reading that file. `grading.min_seed_recall` is `0.5` (`evals/business/BT-001.json`).

## S0 — The gate is never executed automatically

`.github/workflows/validate.yml` runs exactly two steps: `python3 tools/lab/validate.py all` and `python3 -m unittest discover -s tests`. **`isolation.py check-diff` is not in CI.** `.git/hooks/` contains only `*.sample` files — no installed hook.

Enforcement is prose only:
- `skills/improve/SKILL.md:27, 37` — "Enforce it with `isolation.py check-diff` before the candidate is evaluated"
- `agents/candidate-engineer.md:25`, `AGENTS.md:48`, `README.md:48-52`

And `validate.py protected` (`validate.py:2367-2390`) does **not** verify the protected files; it only verifies the *list still names them*. So a candidate that edits `tools/lab/validate.py` to weaken a check passes `validate.py all` (currently green: `PASS protected`, exit 0) and passes CI. The only thing that would catch it is the one check nothing runs.

## S0 — `check-diff` reads the gate from whichever tree you point the script at

`isolation.py:13-14`:
```python
ROOT = Path(__file__).resolve().parents[2]
PROTECTED_PATHS_FILE = ROOT / "protected-paths.txt"
```
`check_diff` (`isolation.py:145-149`) hardwires that file. If a human runs `python3 <candidate>/tools/lab/isolation.py check-diff --candidate <candidate>`, `ROOT` **is the candidate worktree** — the candidate supplies both the checker and the list. `tools/lab/README.md:98-99` and `skills/improve/SKILL.md:37` warn "invoke from a trusted source checkout", but `check_diff` never compares its own `ROOT` against `--candidate`, even though `is_within` (`isolation.py:34-39`) is right there and `layout_errors` already forbids exactly this nesting for other positions.

## S1 — `check-diff` bypass: non-ASCII filenames under a directory prefix

`isolation.py:131-142` runs `git diff --no-renames --name-only` and two `git ls-files --others` variants, with no `-z` and no `-c core.quotepath=false`. Git's default `core.quotepath=true` (verified: `git config --get core.quotepath` is unset in this repo) makes git emit non-ASCII paths **double-quoted and octal-escaped**: `"evals/public/AF-\346\265\213.json"`.

The block test is a literal prefix comparison (`isolation.py:159-163`):
```python
if any(path == prefix or path.startswith(prefix + "/") for prefix in forbidden)
```
A string beginning with `"` does not start with `evals/`, so it is **not blocked**. This is exploitable today for the three directory prefixes — `evals/`, `schemas/`, `skills/improve/references/` (`protected-paths.txt:43-47`) — by *adding* a file rather than modifying one. `evals/public/AF-测试.json` even matches the `AF-*.json` glob in `validate_evals` (`validate.py:1532`), and the 10–20 count bound (`validate.py:1550`) has headroom at 15 cases, so the injected easy case would be picked up by the suite.

Note the internal inconsistency: `parse_status_paths` in `host_adapter.py:124-145` *does* use `-z` (`host_adapter.py:151, 166`), so the business-snapshot check is quoting-safe while the gate is not.

## S1 — `REQUIRED_PROTECTED_PATHS` is narrower than the list it guards

`validate.py:50-75` is the enforced floor. Missing from it, yet materially part of the gate:

| Path | Why it matters | Currently covered by |
|---|---|---|
| `schemas/adapter-case-result.schema.json` | the only validation of host output (`host_adapter.py:41, 476`) | the broad `schemas/` prefix |
| `schemas/comparison.schema.json` | comparison contract (`validate.py:1729`) | the broad `schemas/` prefix |
| `skills/improve/references/business-case.schema.json` | business case contract (`validate.py:83`, `eval_runner.py:37`) | the broad `skills/improve/references/` prefix |
| `.github/workflows/validate.yml` | **the only automated gate execution** | *nothing* |

The first three survive only because `protected-paths.txt` happens to declare directory prefixes. Replace those two prefixes with the exact required entries and `validate.py protected` still returns `PASS` — while three contracts become candidate-editable. `protected-paths.txt:20-22` argues the broad prefixes are deliberate; `REQUIRED_PROTECTED_PATHS` does not encode that decision.

`.github/` is worse: it is in neither the list nor the required set. A candidate can edit the workflow today and both gates report clean.

## S1 — `MIN_UNIT_TEST_COUNT` is spoofable, and skips count as runs

`validate.py:2497-2529`:
```python
ran = re.search(r"Ran (\d+) tests?", f"{completed.stderr}\n{completed.stdout}")
count = int(ran.group(1)) if ran else None
```
Two defects:

1. **Spoof.** `unittest` writes its summary to stderr *at the end of the run*; any test that writes `Ran 500 tests` to `sys.stderr` *during* the run puts that string earlier in `completed.stderr`, and `re.search` returns the **first** match. The floor, the `count == 0` guard (`2507`) and the `count is None` guard (`2515`) all consume the spoofed number.
2. **Skips count.** `Ran N tests` includes skipped tests. Decorating 99 of the 119 test methods with `@unittest.skip` yields `Ran 119 tests ... OK (skipped=99)` and passes. Nothing reads the skip count.

Separately the floor itself is weak: the comment at `validate.py:93-97` says the suite runs 108 tests (actual: 119 `def test_` methods) against a floor of 20 — ~83% of the regression suite can be deleted and the gate stays green.

Also `validate.py:2484`:
```python
if entry.name.startswith(".") or entry.name in allowed:
```
The declared-contents assertion that `protected-paths.txt:26-33` and `validate.py:2465-2472` describe at length as the counterweight to not protecting `tests/` **exempts every dotfile and dot-directory** in `tests/`, and unconditionally allows `__pycache__` (`validate.py:2482`).

## 1. Fail-open / silent-skip inventory

Ordered by how much verification is lost.

| # | Location | Behaviour |
|---|---|---|
| 1 | `validate.py:1923-1925` | `validate_workspace_artifacts` returns `errors` (empty) when `records/` is absent → **`PASS artifacts` having compiled nothing.** This is the "compile step for supervisor artifact acceptance" (`tools/lab/README.md:19-20`). `rm -rf records/` ⇒ green. |
| 2 | `validate.py:2603-2627` → `2803-2808` | `validate_installed` returns `"skip"` and `main` prints `SKIP installed` and `return 0`. Reached whenever `~/.zcode/.../cache/<mkt>/<plugin>` does not exist (`validate.py:2585-2586`). Documented (`tools/lab/README.md:58-59`), but it is a 0-exit that verified nothing. |
| 3 | `validate.py:2052-2057` | Reviews: `if len(parts) != 4 or not re.fullmatch(r"review-\d{4}-\d{2}-\d{2}-\d{3}\.md", ...): continue`. A review record one directory deeper, or misnamed, is **silently invisible** — never validated, never reported as an unexpected entry. |
| 4 | `validate.py:2065-2071` | Same shape for `records/tests/`: `if len(parts) != 4 or not path.is_file(): continue`. A test plan/run at the wrong depth vanishes. |
| 5 | `validate.py:1944-1947` | Any record under a dot-prefixed path component (`records/.x/bug.md`) is skipped entirely. Renaming a directory to `.old` removes its contents from validation. |
| 6 | `validate.py:441-448` | `iter_schema_paths`: `if directory.name == "references" and path.name not in IMPROVEMENT_SCHEMA_NAMES: continue`. A new schema under `skills/improve/references/` is **silently excluded from schema self-validation** — no `$schema`/`$id`/`$ref` checks. The project knows this (`records/plans/PLAN-BUSINESS-EVAL-001.md:66`: "未登记会被 schema 自检静默跳过") but the failure remains silent rather than an unknown-entry error. |
| 7 | `validate.py:336-337` | `SchemaValidator._validate`: `if not isinstance(schema, dict): return []`. A JSON Schema boolean `false` (= reject everything) is treated as **no constraint**. |
| 8 | `validate.py:329-438` | The mini-validator silently ignores `prefixItems`, `patternProperties`, `propertyNames`, `dependentRequired`/`dependentSchemas`, `unevaluatedProperties`, `min/maxProperties`, `exclusiveMinimum/Maximum`, `multipleOf`, `maxContains`, and every `format` except `date-time` (`validate.py:374`). I grepped all 14 schemas: none currently use them, so this is latent — but adding a keyword the validator does not know produces **silent non-enforcement**, not an error. |
| 9 | `validate.py:1593-1594` | `validate_business_seeds`: `if not isinstance(seeds_ref, str): return errors` (empty) — relies on the schema check having already fired. If the schema ever stops requiring `seeds_ref`, seed validation silently disappears. |
| 10 | `validate.py:2555-2556, 2566-2567` | `component_manifest`: missing component directory / missing manifest file ⇒ `continue`, contributing nothing to the compared manifest. |
| 11 | `seed_grader.py:48, 256-261` | `REPETITION_DIR_PATTERN = ^rep-([1-9][0-9]*)$`. A directory named `rep-01` (zero-padded) or `rep_1` **is not a repetition and is not an error** — it is simply skipped. With `rep-1`, `rep-2`, `rep-03` present, `max()` is 2, two reps are graded, `reps_failed` is 0, and `exit_code` (`seed_grader.py:301-303`) returns **0**. This directly contradicts the docstring at `seed_grader.py:244-247` ("a missing artifact must not silently shrink a run"). The `host_adapter` caller happens to catch it (`host_adapter.py:706-723`), so the hole is only in standalone CLI use. |
| 12 | `seed_grader.py:301-303` | `exit_code` returns 0 whenever all reps *graded*, regardless of recall. A repetition with recall 0.0 and `accepted: false` exits 0. The docstring calls this "the CLI contract shared with importers" — no importer uses it (only `main` and tests). Any wrapper reading the exit code as pass/fail is misled. |
| 13 | `policy.py:124` | `if baseline.get("case_results", []) and candidate.get("case_results", []):` — the case/slice/holdout coverage equality check is **skipped** when either side is empty. |
| 14 | `policy.py:270` | `return 0 if decision["decision"] in {"promote", "revise", "reject"} else 1` — `decide` can only produce those three values (`policy.py:208-221`), so **`policy.py` always exits 0, including on `reject`**. The condition is dead. |
| 15 | `validate.py:2691, 2748` → `2793-2801` | `bug_report` and `recurrence_report` always `return []`; `main` then evaluates `return 1 if errors else 0` on a provably empty list. Dead branches. |

## 2. The gate, point by point (as asked)

| Vector | Verdict | Evidence |
|---|---|---|
| Renames | **Handled.** `--no-renames` (`isolation.py:132`) so both old and new paths appear; comment at `129-130` is accurate. |
| Added (not modified) files | **Handled** for ASCII names — `ls-files --others` both with and without `--ignored` (`isolation.py:133-134`); pinned by `tests/test_lab_contracts.py:2339-2352`. **Not handled** for non-ASCII names under a directory prefix (see S1 above). |
| Symlinks | **Handled indirectly.** Replacing a protected file with a symlink changes that path (blocked). Writing *through* a symlink placed elsewhere mutates the real file, which git reports under its real protected path. `artifact_digest.py:33-34` independently rejects symlinks. |
| `..` / path normalization | Git never emits `..` paths, so `check_diff` is safe. `validate.py:2359-2360` rejects `..`/absolute *list entries*; `isolation.py:28` does **not** (it merely `strip("/")`s) — an asymmetry, though in this direction `validate.py` is the stricter of the two, so a poisoned list fails `validate.py protected`. |
| macOS case-insensitivity (`core.ignorecase=true`, verified) | Mostly self-defeating for an attacker: `tools/lab/VALIDATE.PY` resolves to the same inode and git reports the tracked lowercase path. On a case-**sensitive** runner, `Evals/x.json` evades the prefix — but nothing reads `Evals/`, so it is inert. `REQUIRED_PROTECTED_PATHS` matching is exact-case (`validate.py:2382`), so re-casing the list *fails* the check. Low risk. |
| Directory-vs-file entries | Both sides normalize trailing `/` (`isolation.py:28`, `validate.py:2380`). Consistent. |
| Run automatically? | **No.** Not in `.github/workflows/validate.yml`, not in `.git/hooks/`. Prose-only (`skills/improve/SKILL.md:27,37`). This is the gate's decisive weakness. |
| Checker provenance | **Unenforced.** `isolation.py:13-14` trusts `parents[2]`; nothing rejects `candidate == ROOT`. |

## 3. Determinism / gameability of `seed_grader.py`

The scoring is deterministic in the narrow sense (pure functions, no model, stable ordering). It is not *sound*.

**a) Bidirectional suffix path matching.** `seed_grader.py:67-77`:
```python
return is_suffix(seed, finding) or is_suffix(finding, seed)
```
A finding whose `path` is just `spec-backend.md` matches `docs/features/feature-A/spec/be/spec-backend.md`. Two seeds in different directories sharing a basename become indistinguishable. Guessing the basename is enough to satisfy the path half of the rule.

**b) Anchors are bare substrings, and the anchors are tiny.** `seed_grader.py:80-90`:
```python
text = f"{finding['issue']}\n{finding['evidence']}"
return any(anchor in text for anchor in seed["strategy"]["anchors"])
```
BT-001's anchors are `"静默重投"`, `"≤30"`, `"§12.4"`. No word boundary, no requirement that the *issue* be correct, no category check, no cap on `evidence` length.

**The trivial exploit (no answer-key access needed):** emit one finding per `target_doc` whose `evidence` is the **entire document text**. Every anchor that the seeder planted in that document is by construction present verbatim (`evals/business/README.md:117-118` requires exactly that), so path-match + anchor-in-evidence ⇒ every seed in that document hits. Recall 1.0, `escaped_defects` 0, `accepted` true — with zero review performed.

**c) No precision control, by design.** `seed_grader.py:17-18` and `221-225`: findings matching no seed go to `unmatched` and "are never penalized." `evals/business/README.md:96` confirms. So there is **no cost to spamming findings** and no metric that punishes false positives. The only anti-gaming pressure in the whole scheme — precision — is explicitly disclaimed.

**d) The disclaimer understates it.** `evals/business/README.md:93` calls loose substring matching "已知局限，不视为评分缺陷" (a known limitation, not a scoring defect). Combined with (c) and with the answer key sitting in the agent's cwd (S0), it is not a limitation — it is the removal of the property the seed mechanism exists to provide.

**e) Anchor uniqueness is a manual rule.** `evals/business/README.md:118` requires the seeder to `grep` that each anchor appears nowhere else in the target doc. Nothing checks it: `validate_business_seeds` (`validate.py:1580-1665`) is explicitly structural only (`validate.py:77-81`), because the snapshot is absent from the repo. So the one invariant that makes a hit meaningful is enforced by human discipline.

**f) No anti-gaming control exists anywhere.** I grepped for caps on findings count, evidence length, or duplicate-finding collapse: none in `seed_grader.py`, `host_adapter.py`, or the schemas. `evals/business/BT-001.json`'s `acceptance_criteria[2]` ("同一处问题只报一条") is prose in the prompt, not a check.

## 4. Dead / unexercised code

**The business path has never run.** `records/improvement/` contains exactly one file — `README.md` (`find records/improvement -type f`). Zero candidate records, zero evaluation results, zero comparisons, zero release records. There is no run artifact, no progress JSONL, no `grading.json`, no `findings/` anywhere in the tree. The only evaluation-result JSON is `examples/evaluation-results/{baseline,candidate}.json`, i.e. hand-written fixtures. So `eval_runner run` → `host_adapter` → `seed_grader` → `policy` has been exercised only by unit tests and `--dry-run`, never end to end against a real host.

`artifact_digest.py` **is never wired into the measurement path.** It is imported only by `validate.py` (`validate.py:24`, used at `2558` for the *installed-snapshot* comparison). `eval_runner.py` takes `--artifact-digest` as a free string (`eval_runner.py:460`) and copies it into the result (`354`); `policy.py:101-106` compares those strings to each other. **Nothing ever computes a digest of the workspace actually evaluated.** The digest chain that `adapter-protocol.md:61-64` describes as binding candidate identity is, in practice, operator-typed text. Same for `--suite-revision` (`eval_runner.py:462`): a free string, never derived from the suite content.

Other dead or unreferenced surface:

- `isolation.py create-worktree` (`isolation.py:104-120`, registered at `194-198`) — grepped across `.py`/`.md`: **no caller, no doc reference, no test**.
- `artifact_digest.py --manifest-output` (`artifact_digest.py:63, 73-79`) — unreferenced outside the file; `tools/lab/README.md:70` shows only `--root .`.
- `validate_review_markdown`'s `len(parts) != 4` branch (`validate.py:853-856`) — **unreachable** from production: the only caller already `continue`s on that condition (`validate.py:2052-2057`). Reachable only from `tests/test_lab_contracts.py:258-262`.
- `validate_document_with_schema` (`validate.py:1563-1577`) — reachable only via `validate_business_evals` on an out-of-root directory (`validate.py:1692-1695`), i.e. only from tests.
- `seed_grader.exit_code` — no importer despite the docstring's claim (`seed_grader.py:302`).
- `case_results[].protected_guardrails` — collected (`eval_runner.py:201`), equality-checked against the frozen suite (`eval_runner.py:275-277`), stored in the result schema as `required` (`schemas/evaluation-result.schema.json:69`) — and then **never read by `policy.py`**. Per-case protected guardrails have no effect on any decision. The candidate instead declares its own `guardrails` and `protected_slices` (`policy.py:131-132, 174`), so the subject chooses which guardrails bind it.
- `eval_runner.py:117-119` and `validate.py:1319-1320` reject `holdout: true`, but `evals/` contains no holdout case at all — the holdout mechanism is untested against real data (`private-evals/` is gitignored).

## 5. Complexity

`validate.py`: 2838 lines / 128 KB, one file, 71 `def`s, 32 top-level `validate_*` functions — of which the CLI exposes **8** checks (`validate.py:2810-2829`). `validate_workspace_artifacts` alone is **326 lines** with a 6-way `elif parts[0:2] == (...)` dispatch (`validate.py:1963-2154`) followed by four separate cross-reference passes (`2156-2234`).

Duplication markers:
- 57 inline `errors.append(ValidationError(...))` constructions.
- 10 copies of the `try: SchemaValidator(...) except (OSError, ValueError): "validator setup failed"` block (`validate.py:1362-1366`, `1573-1576`, `1772-1775`, `833-835`, `969-971`, …) — plus a divergent copy in `policy.py:45-48` and `eval_runner.py:74-78`, and another in `host_adapter.py:476` that has **no** try/except at all.
- 6 copies of `if path.name == "README.md": continue`.
- `validate_test_plan_markdown` (115 lines, `validate.py:956`) and `validate_test_run_markdown` (186 lines, `validate.py:1071`) are structurally parallel — frontmatter load → schema → timestamp → layout regex → table parse → cross-reference — with the logic copied rather than shared.

`tests/test_lab_contracts.py`: 3006 lines / 146 KB, 19 classes, 119 tests, **61** separate `tempfile.TemporaryDirectory()` fixtures with per-class ad-hoc tree builders (`_candidate_repo` at `2307`, `_write_manifests` at `2386`, …) and no shared fixture layer.

Assessment: not sustainable. The single-file structure is why the floor is set at 20 (`validate.py:97`) instead of pinning per-check coverage; why three dispatch tables (`REQUIRED_PROTECTED_PATHS`, `EXPECTED_TEST_FILES`, `INVALID_EXAMPLES`) must be hand-synced with `protected-paths.txt`; and why `validate.py:853` is dead without anyone noticing. The comments are excellent and doing the job a module boundary should do. Note also that `validate.py` is itself protected (`protected-paths.txt:56`), so splitting it is a human-reviewed gate change — the structure is self-locking.

## 6. Concrete bugs

| # | Sev | Location | Defect |
|---|---|---|---|
| B1 | High | `validate.py:2505-2506` | `re.search` on `stderr + stdout` takes the **first** `Ran N tests` match; test-time stderr output precedes the summary ⇒ `MIN_UNIT_TEST_COUNT` spoofable. |
| B2 | High | `validate.py:2497-2529` | Skipped tests count toward `Ran N`; no skip-count check ⇒ `@unittest.skip` on the whole suite passes the floor. |
| B3 | High | `policy.py:270` | `decision` is always one of `{promote, revise, reject}` (`policy.py:208-221`) ⇒ the expression is constant and **`policy.py` exits 0 on `reject`**. |
| B4 | High | `isolation.py:131-141` | No `-z` / `core.quotepath=false`; quoted non-ASCII paths defeat the `startswith(prefix + "/")` test. Contrast `host_adapter.py:151` which does use `-z`. |
| B5 | Med | `validate.py:746-748` | `BODY_PATH_PATTERN` (`validate.py:704-706`) admits a leading `../`, and the check is `(ROOT / token).is_file() or (path.parent / token).is_file()` — **no containment test**. `../secret.md` resolves outside the repository and passes, defeating the "portable evidence" rule the function exists to enforce (`validate.py:726-732`). `path_inside_root` (`validate.py:462-468`) is the correct helper and is not used here. |
| B6 | Med | `validate.py:215-219` | `load_bug_markdown` catches **only `OSError`**. A non-UTF-8 `.md` under `records/` raises an uncaught `UnicodeDecodeError` (a `ValueError`) → traceback instead of a `ValidationError`. `read_document_text` (`validate.py:137-147`) documents this exact hazard and catches both; `load_json` (`133`) catches both. The bug record / review / plan / recurrence path was missed. Also crashes `bug_report` (`2668`) and `recurrence_report` (`2704, 2717`). |
| B7 | Med | `host_adapter.py:517-519` vs `611-613` | **Asymmetric validation between hosts.** Codex: `json.loads` → inject `latency_ms` → validate once. Claude: validate `completed.stdout` (`611`) **before** injecting `latency_ms` (`612`), then validate again (`613`). Since `latency_ms` is `required` in `schemas/adapter-case-result.schema.json`, identical model output passes on codex and fails on claude, and claude forces the model to invent a latency the adapter then discards. |
| B8 | Med | `host_adapter.py:517-518` | `payload = json.loads(result_text)` then `payload["latency_ms"] = elapsed` with no type check. A host returning a JSON array/string/number raises **`TypeError`**, which is not in the caught tuple at `812` or `929` (`OSError, ValueError, RuntimeError, TimeoutExpired`) ⇒ uncaught traceback instead of the structured per-repetition failure path. |
| B9 | Med | `eval_runner.py:298` | `suite_dir = (ROOT / args.suite).resolve()` — an absolute `--suite` **replaces** `ROOT` (`Path("/a") / "/tmp/x" == "/tmp/x"`). No containment check. Combined with the free-text `--suite-revision`, the "frozen suite" is frozen by convention only. |
| B10 | Med | `validate.py:2484` | `entry.name.startswith(".")` exempts all dotfiles/dot-dirs from the `tests/` declared-contents assertion that `validate.py:2465-2472` and `protected-paths.txt:26-33` present as the safeguard against import-time test hijacking. |
| B11 | Low | `policy.py:76-80` | `compare_direction` falls through to lower-is-better for **any** metric not in `HIGHER_IS_BETTER`, including unknown ones. `policy.py:133-136` flags unknowns as invalid but the loop still computes and reports directions for them. |
| B12 | Low | `policy.py:196-204` | Non-guardrail primary metrics in protected slices use exact float equality (`direction == "regressed"`) with **no tolerance**, while guardrails get one. `acceptance_rate`/`first_pass_review_rate`/`latency_ms` are divisions (`eval_runner.py:141-148`) — a last-bit difference reads as a regression. |
| B13 | Low | `policy.py:174` | `candidate_record.get("protected_slices") or sorted(available_slices)` — a falsy-but-present value (`[]`, `null`) silently becomes "all slices". Sloppy, though in the safe direction. |
| B14 | Low | `host_adapter.py:139-141` | `status = entry[:2]; if status[0] in "RC" or status[1] in "RC"` — `IndexError` on a 1-character record. Practically unreachable from `git status --porcelain -z`, but unguarded. |
| B15 | Low | `artifact_digest.py:38-44` | The digest includes `stat.S_IMODE`. Git preserves only the exec bit, so umask differences (`0644` vs `0664`) change the digest for the *same commit* on two machines. A "deterministic" identity that is not reproducible across checkouts. |
| B16 | Low | `artifact_digest.py:23-25` | `should_exclude` matches `__pycache__`/`.git` at **any** depth, so `agents/__pycache__/**` is excluded from both the digest and `validate.py`'s installed-snapshot comparison (`validate.py:2558`). |
| B17 | Low | `eval_runner.py:186` | `if "repeat_count" in case and case["repeat_count"] != args.repeat_count` — a case that *omits* `repeat_count` gets `args.repeat_count` silently written in (`203`). The comment at `181-183` describes the check as preventing exactly that overwrite. |
| B18 | Low | `eval_runner.py:420-423` vs `policy.py:125-126` | `compare` matches on `(case_id, slice)`; `policy.decide` matches on `(case_id, slice, holdout)`. Two gatekeepers, two coverage definitions. |

## What I would fix first

1. Put `isolation.py check-diff` in `.github/workflows/validate.yml` and protect `.github/`. Without this nothing else in the gate matters.
2. Move `evals/` (at minimum `evals/business/seeds/`) out of the candidate worktree — or stop using the worktree as `--plugin-dir`/`cwd`. As shipped, the subject holds the answer key.
3. Make `check_diff` refuse to run when its own `ROOT` is inside (or equal to) `--candidate`; add `-z` to the three git invocations.
4. Derive at least one decision metric from observation rather than self-report (`permission_violations` is the cheapest: parse host denial output). Until then, `promote` means "the candidate says it improved."
5. `validate.py:1923-1925` → error, not empty list. `policy.py:270` → non-zero on `reject`.
6. Add a precision term (or an evidence-length cap and a per-document findings cap) to `seed_grader`, so pasting the document is not a winning strategy.

**Note on prior audits:** `CONSOLIDATED-REVIEW-REPORT.md:89-90` already records the `isolation.py` quoting issue and the `validate.py`/`isolation.py` normalization asymmetry as *potential* (「潜在 fail-open 而非现实绕过」). For directory prefixes such as `evals/`, adding a non-ASCII-named file makes it an actual bypass today, not a latent one.

*（子代理②运行统计：约 2,517,431 tokens，48 次工具调用，约 17.4 分钟。）*

---

## 5. 助手 · 状态播报 + 派出第三、四路并行审计子代理

> 两路已回，发现不少实质问题。继续深挖检索/记忆闭环与文档一致性，同时我自查仓库卫生与版本漂移。

**工具调用 ① —— `Agent`（子代理③：记录/检索/记忆层与自改进闭环审计，`Explore` 类型）—— 派发提示词全文：**

```text
You are auditing the repository at /Users/lihanghang1/Desktop/TestProject/agentflows (a multi-agent workflow plugin called "Agentflow"). Your scope: the KNOWLEDGE / MEMORY / RETRIEVAL layer (what the project calls records, episodes, recurrence — effectively its RAG substitute) and the SELF-IMPROVEMENT ("以模治模") workflow that consumes it. Read:

- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/improve/SKILL.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/improve/references/evidence-and-release.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/skills/improve/references/*.schema.json (episode, candidate, eval-case, release-record, business-case)
- /Users/lihanghang1/Desktop/TestProject/agentflows/records/README.md and every README under records/*/
- /Users/lihanghang1/Desktop/TestProject/agentflows/records/bugs/**/*.md (all actual bug records)
- /Users/lihanghang1/Desktop/TestProject/agentflows/records/episodes/**/*.json (all episodes)
- /Users/lihanghang1/Desktop/TestProject/agentflows/records/bugs/recurrence/*
- /Users/lihanghang1/Desktop/TestProject/agentflows/schemas/bug-record.schema.json and recurrence.schema.json
- /Users/lihanghang1/Desktop/TestProject/agentflows/docs/self-improvement-design.md
- /Users/lihanghang1/Desktop/TestProject/agentflows/agents/feedback-analyst.md, candidate-engineer.md, evaluator.md, release-governor.md, bug-recorder.md

Assess critically, with file:line evidence:

1. RETRIEVAL: Is there any actual retrieval mechanism? When a new task starts, what causes a relevant past bug record or episode to be READ? Is it grep-based, index-based, or purely "the model is told to look"? Quantify: how many records exist now, and at what volume does the current scheme break (e.g. linear scan of N markdown files in context)? Is there any recency/relevance ranking, dedup, or summarization/compaction tier?
2. WRITE-SIDE vs READ-SIDE ASYMMETRY: the project has elaborate rules for WRITING records. Find out how much is specified for READING them back. Is the recurrence mechanism (records/bugs/recurrence/) actually computed, or hand-maintained? Who updates it and when? Does anything detect a recurring bug automatically?
3. EPISODE LOOP: episodes are said to be mandatory for material changes since 0.7.2. Check: how many episodes actually exist, are they consistent with the schema, do they cover the recent material changes in the git log? Is there drift between "mandatory" and actual practice in this very repo (self-dogfooding failure)?
4. EVIDENCE CHAIN INTEGRITY: bug record -> candidate -> evaluation -> release record. Check whether the chain is actually linked by ids, and whether any instance of the full chain exists in the repo. Are there dangling references (a record pointing to an id that does not exist)?
5. FEEDBACK LOOP CLOSURE: does anything measure whether a released improvement actually reduced the failure it targeted? Look for the rollback/regression detection path.
6. SCHEMA vs REALITY drift: fields in the schemas nothing writes; fields written that no consumer reads.

Report concrete findings with file:line citations. Be specific and skeptical. Do not fix anything. Count things — give numbers. Every claim needs a citation.
```

**工具调用 ② —— `Agent`（子代理④：跨切面一致性、文档真实性与仓库卫生审计，`Explore` 类型）—— 派发提示词全文：**

```text
You are auditing the repository at /Users/lihanghang1/Desktop/TestProject/agentflows (a multi-agent workflow plugin called "Agentflow"). Your scope: CROSS-CUTTING CONSISTENCY, DOCUMENTATION TRUTHFULNESS, and REPOSITORY HYGIENE. Do NOT re-audit role contracts or the python tooling internals (other auditors cover those).

Investigate and report with file:line evidence:

1. VERSION / STATE DRIFT: All five manifests declare 0.7.4. README.md:23 and README.md:116 still say 0.6.0. Sweep the whole repo for other stale version/state claims: docs/*.md, CHANGELOG.md, skills/**/*.md, records/**, examples/**, mock/**. List every location where a claim about "current version", "what exists now", "not yet implemented", or "pending" contradicts the actual tree. Note which of these `python3 tools/lab/validate.py docs` does and does not catch.

2. ROOT-LEVEL ARTIFACT JUNK: The repo root contains ANALYSIS-REPORT.md, REVIEW-REPORT.md, CONSOLIDATED-REVIEW-REPORT.md, three command-code-session-*.html files (~1.6MB total), and .DS_Store. Determine for each: is it tracked by git (`git ls-files`)? Is it referenced by anything? Does .gitignore cover it? Are these leftover session artifacts that contradict the repo's own rule (AGENTS.md) that trace files are only created when the user asks? Also check whether these reports duplicate each other and whether their findings were ever actioned (compare their claims against current code).

3. mock/ vs examples/ DUPLICATION: compare /mock/records/** against /examples/** and /records/**. Are these three parallel copies of the same fixtures? Quantify overlap (diff identical files). What is mock/ for, is it documented, is it validated, and does it drift from examples/?

4. DOC LINK INTEGRITY: check every relative markdown link and every file path mentioned in docs/*.md, README.md, AGENTS.md, skills/**/*.md, records/**/README.md. Report dangling links and paths that do not resolve. Note especially SKILL.md's link `[records/reviews/README.md](../../../records/reviews/README.md)` — verify whether that relative depth is correct from both the source tree location AND the installed-plugin snapshot location.

5. DOCS SIZE / OVERLAP: docs/ has 8 files including next-session-handoff.md (539 lines) and iteration-log.md (406 lines). Assess: is next-session-handoff.md stale (it describes a session that already happened)? Does it contradict current state? Is iteration-log.md redundant with CHANGELOG.md (763 lines)? Quantify overlap.

6. .github/ and CI: read .github/workflows/*. Does CI match what the docs claim is enforced?

7. Anything else that is plainly wrong, stale, orphaned, or self-contradictory at the repository level.

Report concrete findings with file:line citations and actual command output (e.g. git ls-files results, diff results). Be specific and skeptical. Do not fix anything. Every claim needs evidence.
```

**工具调用 ① 的返回 —— 子代理审计报告③（记录/检索/记忆层与自改进闭环），全文逐字如下：**

## AUDIT: Agentflow knowledge/memory/retrieval layer + self-improvement loop

Repo state: `plugin.json` v0.7.4, HEAD `4644582` (= 0.7.1). Versions 0.7.2/0.7.3/0.7.4 are uncommitted working-tree changes; 4 of 9 episodes are untracked (`git status`: `?? records/episodes/2026-09-18/EP-20260918-00{2,3,4,5}.json`). All numbers below are from the live tree.

---

## 1. RETRIEVAL — there is none. There is a *writing* system with a documentation page of shell one-liners attached.

**Corpus inventory (exact counts):**

| Subtree | Non-README files | Spec lines in its README |
|---|---|---|
| `records/bugs/*/​*.md` | **9** bug records + **1** recurrence ledger | 97 |
| `records/episodes/*/​*.json` | **9** | 48 |
| `records/plans/` | **1** | 40 |
| `records/reviews/` | **0** | 91 |
| `records/tests/` | **0** | 79 |
| `records/improvement/{candidates,evaluations,comparisons,releases}/` | **0** (the four directories do not exist) | 56 |

561 lines of README specifying record formats; **19 actual records**. `records/reviews/` and `records/tests/` have 170 lines of contract and zero instances.

**No mechanism causes a past record to be read at task start.** The intake step is `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/agentflow/SKILL.md:103` — it mandates reading "repository instructions, current diff, relevant architecture, and tests" and calibrating status against `git fetch`/`log`. It never mentions `records/`. The only repo-wide pointer is `/Users/lihanghang1/Desktop/TestProject/agentflows/AGENTS.md:60` ("Records live under `records/`; see records/README.md for layout and queries") — a pointer to a doc, not a step.

**The only two roles told to read records at all:**
- `/Users/lihanghang1/Desktop/TestProject/agentflows/agents/bug-investigator.md:38-41` — "Before attributing, check `records/bugs/recurrence/` for an existing class". Fires only on a bug task. `records/bugs/recurrence/` currently contains **1 file**, so this "check" is reading one 37-line markdown.
- `/Users/lihanghang1/Desktop/TestProject/agentflows/skills/improve/SKILL.md:32` — "The recurrence ledger is a first-class episode source".

**The retrieval surface is 7 shell one-liners** (`records/README.md:108-150`, 7 ```sh blocks) plus 2 in `records/episodes/README.md:45-48` and 3 in `records/improvement/README.md:52-56`. It is grep/jq/awk over a flat directory:
- `records/README.md:113` `validate.py report`
- `records/README.md:119` `report | awk -F'\t' '$7=="agentflow"'`
- `records/README.md:125` `report | cut -f5 | sort | uniq -c`
- `records/README.md:137` `validate.py recurrence`
- `records/README.md:143` `grep -rl "tools/lab/host_adapter.py" records/bugs --include="*.md"`

**Fatal wiring bug: the roles that need these cannot run them.** `agents/feedback-analyst.md:6-7` is `tools: Read, Glob, Grep` / `disallowedTools: Bash, Write, Edit`. Same for `agents/evaluator.md:6-7`, `agents/release-governor.md:6-7`, `agents/bug-investigator.md:6-7`. `python3 tools/lab/validate.py report|recurrence` — the *only* aggregation/ranking surface in the repo — is **unreachable from every read-only role**. Retrieval degrades to raw Grep over `records/`, i.e. "the model is told to look."

**Ranking / dedup / compaction: zero.** `grep -c "difflib\|similar\|cluster\|dedup\|fuzzy" tools/lab/validate.py` = **0** across 2,838 lines. The only ordering is `rows.sort()` on `recorded_at` (`tools/lab/validate.py:2688`) and on `class_id` (`:2745`). Filters are three exact-string matches (`--project`, `--status`, `--provenance`, `tools/lab/validate.py:2654-2677`). No text index, no embeddings, no sqlite, no summarization tier — confirmed by `find` (no hooks dir) and by the design doc's own admission below.

**Silent-drop defect in the read path:** `tools/lab/validate.py:2668-2670` — `if errors or not frontmatter: continue`. A record that fails to parse is **omitted from the retrospective table without any message**, and `report` still exits 0. Same at `:2705-2706` and `:2718-2719` for the recurrence table. A record corrupted by a bad edit silently disappears from the memory surface.

**Volume math — where it breaks.** Measured: bug records = 56,319 bytes / 36,478 chars (8,500 CJK) ≈ **15.5k tokens for 9 files** (~1,720 tokens/record); episodes = 30,623 bytes / 20,569 chars ≈ **8.4k tokens for 9 files** (~930/episode). Full corpus scan today ≈ **24k tokens**, plus 7k more if the 6 record READMEs are loaded to interpret them. Against a realistic ~30k retrieval budget (the agentflow SKILL, `contracts.md`, and role files already load first), linear scan breaks at roughly **17-20 bug records**. Observed production rate: 18 artifacts across 5 calendar days (2026-09-14 → 2026-09-18) ≈ **3.6/day**. The scheme has on the order of **one to two weeks** of headroom.

The project knows this. `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/self-improvement-design.md:3`: "持久检索…尚未实现". `:108`: full-text search is step **5 of 6** in the next-steps order. `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/next-session-handoff.md:442-444`: "原计划的 store/检索仍不做，待落盘密度观察". `:451-452` "本地 Episode Store + SQLite FTS5 检索" is still `[ ]`. `:491` "不要先做向量检索".

## 2. WRITE-SIDE vs READ-SIDE ASYMMETRY

Write side: 46,477 bytes of JSON Schema across 10 + 6 schema files; 561 lines of record README; `bug-recorder.md` is 68 lines of writing discipline; `validate.py` enforces schema, status transitions, date-dir/`recorded_at` agreement, filename-slug, id uniqueness, timestamp order, fixed Chinese heading literals, body-path resolution (`tools/lab/validate.py:725-757`), personal-path bans, external-fragment embedding.

Read side: 12 shell one-liners in READMEs, unreachable from the analyst roles, plus one sentence each in two role files.

**The recurrence mechanism is hand-maintained. Only the *tier* is computed.**
- `recurrence_report()` (`tools/lab/validate.py:2694-2748`) derives `single`/`recurred`/`escalated` by comparing each occurrence's `agentflow_version` against the ledger's `consolidated_in` (`:2722-2734`). That part is genuinely automatic.
- But **class membership is entirely hand-assigned**. `agents/bug-recorder.md:55-57`: "When the supervisor assigns a recurrence ledger … the record carries `class_id`". `tools/lab/validate.py:2178-2201` only cross-checks records that **already declare** a `class_id`. There is no check that a record which *should* belong to a class declares one. **Nothing detects a recurring bug automatically.**
- Evidence it is under-applied: 7 of 9 bug records share `error_kind: missing-constraint`, 6 of 9 share `attribution: workflow_policy`, and `BUG-20260917-01/02/03` are three same-session clause-gap failures — yet `grep -rn "^class_id:" records/bugs/*/*.md` returns exactly **1** record (`records/bugs/2026-09-15/unverified-behavior-claims-recurring.md:10`). One class ledger exists for nine records.
- **No write-back trigger.** `grep -c recurrence` per file: `skills/improve/SKILL.md` = **1** (read-only, line 32), `agents/feedback-analyst.md` = **0**, `agents/release-governor.md` = **0**, `agents/candidate-engineer.md` = **0**, `agents/evaluator.md` = **0**. The 13-step improve loop (`skills/improve/SKILL.md:31-43`) reads the ledger at step 2 and **never updates `consolidated_in` at steps 11-13**. Nobody owns the update.
- Consequence: `records/bugs/recurrence/unverified-behavior-claims.md:9-10` has `recorded_at == updated_at == 2026-09-16T11:57:15Z`. The ledger has not been touched in 2 days and 11 version bumps (0.3.4 → 0.7.4). Its one occurrence is at version 0.3.3, below `consolidated_in: 0.3.4`, so `post=0` and `python3 tools/lab/validate.py recurrence` outputs `unverified-behavior-claims consolidated 0.3.4 1 0 single`. **The `escalated` alarm can never fire unless a human first files a new record and hand-tags `class_id`.**
- Leak confirmed: `records/episodes/2026-09-18/EP-20260918-002.json` records "bug-recorder 越界改写 BUG-20260917-02「## 现象」段一个词（同时→并发），supervisor 按记录纪律回退为原文" — an Agentflow role violating the append-only record discipline. There is **no `records/bugs/2026-09-18/` directory**; no bug record was filed. The failure exists only inside an episode signal string, so it can never reach `validate.py report`, the recurrence ledger, or any cluster.

## 3. EPISODE LOOP — the mandate is honored only after it was written

**9 episodes**, covering **6 distinct versions** (0.4.0, 0.6.0×3, 0.7.0, 0.7.2, 0.7.3×2, 0.7.4) out of **20 versions in `CHANGELOG.md`** (`grep -c '^## ' CHANGELOG.md` = 20, 0.3.2 → 0.7.4) = **30% coverage**.

Schema conformance: `python3 tools/lab/validate.py artifacts` → `PASS`. All 9 validate.

Drift against git log — commits whose own message declares an independent review gate but which have **no episode**:
- `4644582` "0.7.1 …（含独立评审与 governor promote）" — **0 episodes**
- `8199a69` 0.7.0 has 1 episode; `9015d6f` 0.5.2, `f4c32b8` 0.5.1, `e03d4cd` 0.5.0, `779f9d4` 0.4.2, `b0b5f2e` 0.4.1 — **0 episodes each**
- `b0b5f2e` "0.4.1 文档一致性门与 **episode 落盘**" — the version that *introduced* episodes has no episode.

Post-mandate (≥0.7.2) coverage is 3/3 versions, so the rule is currently followed. But the schema cannot enforce it: `review_roundtrips` is **absent from the `required` list** (`skills/improve/references/episode.schema.json:7-19`) while `skills/agentflow/SKILL.md:112` declares each reviewer round mandatory. Actual state: 5 of 9 episodes omit the field entirely; `records/episodes/2026-09-18/EP-20260918-004.json` carries `"review_roundtrips": []`. Nothing checks it.

**Survivorship bias — a direct violation of the project's own rule.** `skills/improve/references/evidence-and-release.md:13`: "Keep positive and negative episodes. Do not train the workflow only on failures or only on tasks that reached completion." Actual distribution: **`outcome` = `accepted` in 9/9 episodes** (0 `rejected`, 0 `partial`, 0 `failed`, 0 `unknown`). `source_type`: 7 `user_feedback`, 1 `acceptance`, 1 `review` — **0 `test`, 0 `incident`, 0 `rollback`**, i.e. none of the three highest-signal source types. Bug pool is the same shape: **9/9 `provenance: agentflow`**, 8 `verified` + 1 `open`, **0 `rejected`**.

**Episodes have no revision pin.** `episode.schema.json` properties (lines 20-160) contain no `source_revision`, unlike `schemas/bug-record.schema.json:85`. `validate_episode_document` (`tools/lab/validate.py:760-777`) checks schema + filename==id only; `validate_body_references` is never applied to JSON. So `records/episodes/2026-09-18/EP-20260918-005.json`'s claim about "`records/README.md:12` 仍是旧口径" is now false against the current file and is unpinned and unverifiable.

## 4. EVIDENCE CHAIN INTEGRITY — the chain has zero instances, and the one release it claims could not have been recorded

**`records/improvement/` contains exactly one file: `README.md`.** Zero candidates, zero evaluations, zero comparisons, zero release records. Repo-wide: `grep -rl '"rollback_to"' --include="*.json"` matches **only the schema**; `grep -rl '"baseline_result_id"'` matches **only the schema**. `mock/records/` has bugs, episodes, plans, reviews — but **no `improvement/`**. `examples/` has a candidate record and two evaluation results but **no comparison and no release record**. There is no worked example of the full chain anywhere, real or demo.

Meanwhile `/Users/lihanghang1/Desktop/TestProject/agentflows/records/README.md:18-21` asserts: "The improvement control plane's artifact handoff **is implemented** … **no longer planned, part of the validated tree**." It is a validated *schema* tree with zero inhabitants.

**The 0.7.1 release violated its own promotion gate, and the artifact that would have caught it was never written.** `CHANGELOG.md:148-151`: "an independent evaluator verified … (verdict **`neutral`** …), and the release governor returned **`promote`**". Against:
- `skills/improve/references/release-record.schema.json:108-152` — `if decision == "promote"` then `evaluation_result` must be **`const: "better"`**.
- `tools/lab/policy.py:217-221` — `neutral` deterministically yields `decision: "revise"`, never `promote`.
- `agents/evaluator.md:18` and `skills/improve/SKILL.md:81` — "A neutral result is not an improvement."

A schema-valid release record for 0.7.1 is **structurally impossible**. No release record exists. The gate was satisfied in CHANGELOG prose instead of in the artifact plane, and `validate.py artifacts` passes because there is nothing to validate.

**Ids do not link the pools.**
- `schemas/bug-record.schema.json` has `additionalProperties: false` and **no episode field**; `episode.schema.json` has `additionalProperties: false` and **no bug field**. The only edge is `candidate.evidence_ids` (`candidate.schema.json:47-55`) — and there are no candidates.
- Actual cross-references are prose: `grep -o "BUG-[A-Z0-9-]*" records/episodes/*/*.json` → **2 episodes** mention a bug id inside a Chinese sentence. `grep -o "EP-" records/bugs/**` → **0**. Episode `signals[].evidence_ref` values are free-form Chinese (e.g. "会话最终决策记录：三纪律四处落点、评审桥落盘、负向实验全过") — not resolvable identifiers.
- The resolver has a silent escape hatch: `tools/lab/validate.py:1907-1908` — any `evidence_id` not prefixed `EP-`/`BUG-` hits `continue  # other evidence shapes are outside this tree's resolver`. The repo's single candidate example uses exactly such an id: `examples/policy/candidate-record.json` → `evidence_ids: ['E-POLICY-001']`, which resolves to nothing and is not checked.

**Dangling references that do exist (nothing detects them):**
- `fix_revision` values are `agentflow 0.3.2` / `0.3.4` / `0.4.2` (8 of 9 records). `git tag -l | wc -l` = **0**. `git rev-parse 0.4.2` → `fatal: ambiguous argument`. **All 8 `fix_revision` values are unresolvable**, while `source_revision` values (`f2ea05c`, `33962ee`, `8665ca3`) all resolve as commits.
- `closure_criteria` is schema-required for `verified` (`schemas/bug-record.schema.json:125`) but the string `closure_criteria` appears **0 times in `tools/lab/validate.py`** — its content is never checked. Sampling its `path:line` citations:
  - `BUG-20260917-02` cites `skills/agentflow/SKILL.md:84` as "git 层写入隔离条款原文命中". Line 84 today reads `repository. Attribution separates the two upgrade loops: ...` — the wrong section. The clause is now at **line 106**.
  - `BUG-20260917-03` cites `skills/agentflow/SKILL.md:81` for the status-calibration clause. Line 81 today is document-mode review text. The clause is now at **line 103**.
  - `contracts.md:13` and `contracts.md:22` still resolve correctly.
  - **2 of 4 sampled closure-criteria citations are dangling**, and the validator's body-path check (`tools/lab/validate.py:746-747`) tests `(ROOT / token).is_file()` only — line numbers are never verified, and frontmatter strings are not scanned at all.

## 5. FEEDBACK LOOP CLOSURE — open

**Nothing measures whether a released improvement reduced the failure it targeted.**
- `skills/improve/SKILL.md:43` step 13: "Monitor after promotion: compare canary outcomes with the baseline guardrails. Roll back … when a declared threshold fails." `grep -rn "canary\|monitor" tools/lab/*.py` → **0 matches**. No implementation of any kind.
- `tools/lab/eval_runner.py` subcommands are exactly `run` / `validate` / `compare` (`:484`, `:490`, `:494`). There is no post-release, monitor, or rollback command.
- `tools/lab/policy.py:210-221` can return `promote`, `reject`, or `revise` — **never `rollback`**, although `rollback` is in the enum at `release-record.schema.json:39-45` and in the governor's contract (`agents/release-governor.md:16`). `policy.py:270` then does `return 0 if decision["decision"] in {"promote","revise","reject"} else 1` — a branch `decide()` cannot reach. `rollback_target` (`policy.py:233`) is just `candidate_record["parent_version"]` echoed back, with no check that the parent is installable, contradicting the gate requirement "a rollback target is available **and verified**" (`evidence-and-release.md:108`).
- The only regression-detection path that exists is the `escalated` tier — which, per §2, requires a human to notice the recurrence and hand-tag `class_id` first.
- Eval suite can't close the loop either: **18 cases** (15 `evals/public/AF-*.json` + 3 `evals/business/BT-*.json`), and `grep -h '"holdout"' evals/*/*.json | sort | uniq -c` → **`18 "holdout": false`**. Zero holdout cases, against `evidence-and-release.md:91` ("Keep holdout answers unavailable to the candidate engineer"). Exactly **1** of 18 cases derives from a bug record (`AF-015`, from `BUG-20260915-001`); the `unverified-behavior-claims` ledger's own escalation promise — "同类再犯时升级为评测用例" (`records/bugs/recurrence/unverified-behavior-claims.md:28`) — has produced no case.
- `evals/public/inputs/AF-009.md:3` instructs the agent to "Record the accepted parser bug at `records/bugs/BUG-PARSER-001.json`" — a JSON path directly contradicting the current contract (`records/bugs/<YYYY-MM-DD>/<kebab-slug>.md`, `records/README.md:32-36`). The frozen suite measures against a superseded record format.

## 6. SCHEMA vs REALITY DRIFT

**Schema fields nothing has ever written (0 instances repo-wide):**
- Entire `release-record.schema.json` (367 lines) and `schemas/comparison.schema.json` — 0 instances anywhere.
- `candidate.schema.json`'s 14 required fields — 1 instance, in `examples/policy/`, never in `records/`.
- `eval-case.schema.json:44` `holdout` — 18/18 written as `false`; the true branch is dead.
- `release-record.schema.json:186-265` — the `canary` and `automatic` rollout branches; `rollout.task_slice`, `rollout.rollback_thresholds` — unreachable, no rollout has been recorded.
- `episode.schema.json:78-118` `review_roundtrips` — present in 4/9 episodes, one of them empty.
- `bug-record.schema.json:95` `rejection_reason` — 0 records are `rejected` (and `records/bugs/archive/` does not exist in the real tree, only in `mock/`).
- `recurrence.schema.json` `status: unconsolidated` — 0 instances (the only ledger is `consolidated`).

**Fields written that no consumer reads:**
- `affected_slices` — present in all 9 bug records (e.g. `records/bugs/2026-09-15/axios-interceptor-401-redirect-conflict.md:18-21`), but `bug_report()` (`tools/lab/validate.py:2679-2688`) emits only 7 columns and drops it; no protected-slice consumer exists because no evaluation ever ran.
- `closure_criteria` — required for `verified`, 0 occurrences in `validate.py`, no consumer.
- `fix_revision` — written 8×, unresolvable (no tags), no consumer.
- `signals[].evidence_ref` and `feedback_summary` — free text, never parsed.

**Documented shapes that contradict their own schemas:**
- `skills/improve/references/evidence-and-release.md:56-76` presents "the release gate produces a record of this shape". Checked mechanically against `release-record.schema.json` (`additionalProperties: false`): **10 illegal top-level keys** (`candidate_version`, `parent_version`, `source_revision`, `artifact_digest`, `hypothesis`, `evidence_ids`, `changed_components`, `risk_class`, `evaluation_suite_revision`, `protected_slices` — all of which the schema nests under `candidate`) and **2 missing required keys** (`candidate`, `evaluation_result`). **The documented release record would fail the schema the same document points to two lines later (`:80`).**
- `skills/improve/SKILL.md:62-64` mandates that a method-level release record "must state `measurement: none (method-level change, no instrumented business task)`". `release-record.schema.json` has `additionalProperties: false` and **no `measurement` property** (allowed keys: `approvals`, `baseline_results`, `candidate`, `candidate_results`, `decision`, `evaluation_result`, `rollback_to`, `rollout`, `schema_version`). A record obeying the SKILL is rejected by the schema.
- Deeper: `release-record.schema.json:271-286` requires full `baseline_results`/`candidate_results` result-sets with `sha256` digests and all 8 summary metrics. For the `measurement: none` class — which is what **every 0.5.x-0.7.x release actually was** (`CHANGELOG.md:91,156,211`) — a valid release record is **structurally unwritable**. That is the mechanical reason `records/improvement/releases/` is empty, and it explains why 20 versions shipped with zero release records while `records/README.md:18` calls the control plane "implemented".

## Bottom line

The knowledge layer is a **well-validated append-only write buffer with no reader**. Nineteen records, one hand-maintained recurrence class, no index, no ranking, no compaction, and a retrieval CLI that the four read-only improvement roles are forbidden by their own frontmatter from executing. The "以模治模" loop has a complete schema plane and **zero instances of any artifact in it**; the one release that claims a governor verdict (`CHANGELOG.md:148-151`, 0.7.1, `neutral` → `promote`) is precisely the case its own schema forbids, and it shipped because the artifact that would have blocked it was never written. The feedback loop is open at both ends: no retrieval in, no post-release measurement out.

*（子代理③运行统计：约 3,546,187 tokens，81 次工具调用，约 21.4 分钟。）*

**工具调用 ② 的返回 —— 子代理审计报告④（跨切面一致性、文档真实性与仓库卫生），全文逐字如下：**

# Cross-cutting consistency / documentation truthfulness / repo hygiene audit

## 0. The framing fact everything else sits on: HEAD is 0.7.1, the tree claims 0.7.4

```
$ git show HEAD:plugin.json | grep version
  "version": "0.7.1"
$ grep version plugin.json
  "version": "0.7.4",
$ git log -1 --format='%H %ad %s'
4644582c00cef55261c9ea6abe970feadf3a7fc2 Fri Sep 18 11:35:16 2026 +0800 feat: 0.7.1 ...
```

Versions **0.7.2, 0.7.3, 0.7.4 exist only as uncommitted working-tree state** — 18 modified files + 4 untracked episodes:

```
$ git status --short
 M .claude-plugin/plugin.json      M docs/agent-roles.md          M records/README.md
 M .codex-plugin/plugin.json       M docs/host-platform-facts.md  M records/episodes/README.md
 M .zcode-plugin/plugin.json       M evals/business/README.md     M records/plans/PLAN-BUSINESS-EVAL-001.md
 M CHANGELOG.md                    M examples/...                 M skills/agentflow/SKILL.md
 M marketplace.json                M mock/README.md               M skills/improve/references/episode.schema.json
 M plugin.json                     M mock/records/plans/...
?? records/episodes/2026-09-18/EP-20260918-00{2,3,4,5}.json
```

`git show HEAD:CHANGELOG.md` top heading is `## 0.7.1`. The installed plugin snapshot is at `agentflow/0.7.4/` — built from an **uncommitted tree**. Nothing in `validate.py` notices this; `validate.py all` returns 8× PASS and `validate.py installed` returns PASS, because both compare the working tree to itself and to the snapshot, never to git.

---

## 1. VERSION / STATE DRIFT

### Confirmed stale version claims (actual = 0.7.4)

| Location | Text | Evidence |
|---|---|---|
| `/Users/lihanghang1/Desktop/TestProject/agentflows/README.md:23` | ``Version `0.6.0` provides:`` | caller-supplied, confirmed |
| `/Users/lihanghang1/Desktop/TestProject/agentflows/README.md:116` | ``The source checkout currently declares version `0.6.0``` | confirmed |
| `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/host-native-plugin-design.md:3` | ``> 状态：`v0.6.0` 已形成 Codex + Claude Code + ZCode 共用的…`` | **not in the caller's list — new finding** |
| `/Users/lihanghang1/Desktop/TestProject/agentflows/docs/self-improvement-design.md:3` | ``> 状态：`v0.6.0` 已落地自迭代 Skill、角色分工…`` | **new finding** |

Ironically both of the latter two were explicitly "closed" as U-06 in `/Users/lihanghang1/Desktop/TestProject/agentflows/records/plans/PLAN-BUSINESS-EVAL-001.md:95` ("已关闭（2026-09-17 两处横幅已更新为 0.6.0）") — the fix was version-pinned rather than made self-maintaining, so it re-broke on the next four bumps.

### Stale "what exists now" claims that are not version numbers

**`README.md:26-30` — role and schema inventory is 0.6.0-era.**
README lists 8 implementation roles: "frontend, backend, technical-director, reviewer, bug-investigator, bug-fixer, bug-recorder, and plan-architect". `agents/` holds **14** files; `test-planner.md` and `test-executor.md` (added 0.7.0) are absent from README. `grep -i test README.md` returns only two hits, both about `tests/` the Python directory:
```
47:test, and the list itself — is declared once in [`protected-paths.txt`]
58:...runs the repository's regression tests.
```
The entire 0.7.0 testing slice (`records/tests/`, `schemas/test-plan.schema.json`, `schemas/test-run.schema.json`, Test Planner → Test Executor flow) is invisible in README. Contrast `skills/agentflow/SKILL.md:15-16`, which *does* bind `agentflow:test-planner` and `agentflow:test-executor` on both Claude Code and ZCode, and `docs/agent-roles.md:17-18`, which *does* carry both rows. README is the only surface that missed it.

Same file, same paragraph: README:29-30 lists "bug, plan, episode, candidate, evaluation-case, evaluation-result, and release-record schemas". `schemas/` actually contains 9 files; missing from the README list are `review.schema.json`, `recurrence.schema.json`, `comparison.schema.json`, `adapter-case-result.schema.json`, `test-plan.schema.json`, `test-run.schema.json`.

**`docs/iteration-log.md` stops at 0.6.0 — five versions missing.**
```
CHANGELOG versions: 20  ['0.3.2' … '0.6.0','0.7.0','0.7.1','0.7.2','0.7.3','0.7.4']
iteration-log versions: 16 ['0.3.1' … '0.6.0']
in CHANGELOG only: ['0.7.0','0.7.1','0.7.2','0.7.3','0.7.4']
$ grep -c -E '0\.7\.[0-9]' docs/iteration-log.md
0
```
`README.md:114` still routes the reader there: "[`docs/iteration-log.md`](docs/iteration-log.md) for why each version changed." For the last five versions it answers nothing.

**`docs/iteration-log.md` — 12 headings each claim to be "current source".**
```
$ grep -c '当前源码' docs/iteration-log.md
12
```
`iteration-log.md:88`, `:117`, `:147`, `:167`, `:196`, `:220`, `:276`, `:301`, `:322`, `:347`, `:364`, `:385` all end with `（…，当前源码，宿主快照待重装）`. Twelve mutually exclusive "this is the current source" markers in one file; at most one could ever be true and none is (current is 0.7.4). The literal is also factually wrong on the second half: the snapshot is *not* pending reinstall — it is installed at 0.7.4 and `validate.py installed` returns PASS.

**`docs/next-session-handoff.md` — wrong machine, wrong remote, self-contradicting.**
- `:3` `更新时间：2026-09-17` — last write was 2026-09-18 00:15 (mtime) and content stops at batch 19 / 0.5.2. Zero mentions of 0.7.x anywhere in 539 lines.
- `:7` `Agent 项目目录（当前机器）：/Users/hang/Documents/myProject/agentflow` — actual working directory is `/Users/lihanghang1/Desktop/TestProject/agentflows`. Not a historical note; it is labeled **"当前机器"**.
- `:483` `> 继续处理 /Users/hang/Documents/myProject/agentflow（remote: Ganseblum/my-agents.git）` — contradicts `:8` in the same file (`Ganseblum/agentflows.git`) and contradicts reality:
  ```
  $ git remote -v
  origin  https://github.com/Ganseblum/agentflows.git (fetch/push)
  ```
  This is the copy-paste prompt the doc tells the next session to start from.
- `:510-511` `本机尚未建立可由默认检查发现的宿主安装源` directly contradicts `:11-12` of the same file (`本机 ZCode 已有可被 validate.py installed 默认发现的安装源`) and contradicts `validate.py installed` → PASS.
- `:491` `之后才配置本机安装源` — already configured, at 0.7.4.
- `:427-438` P0 checklist all `[ ]`; `:451-454`, `:457-469` P1 open items — none re-checked since 0.6.0. Notably `:437` "`maxTurns` 在 ZCode 实测一次" is still open and is still honestly open (`host-platform-facts.md:19` Z6 agrees), so the list is not uniformly stale — which makes the stale parts harder to spot, not easier.

**`docs/agent-product-boundary.md:124-129` — describes a migration that already happened.**
```
124: ## 迁移顺序
127: 2. 使用 `git subtree split --prefix=plugins/agentflow` 保留 Plugin 的提交历史。
128: 3. 将提取结果作为新仓库根目录…
129: 4. 更新 Manifest 中仍指向 `multi-agent-cli` 的仓库地址。
```
There is no `plugins/` prefix in this tree; this *is* the standalone repo; the remote is `agentflows.git`; no manifest mentions `multi-agent-cli`. Written as a forward-looking plan, presented as current.

**`evals/README.md:3` — the index for `evals/` omits `evals/business/` entirely.**
```
$ grep -c 'business' evals/README.md
0
```
It describes only `public/` (fifteen cases — correct) while `evals/business/` with BT-001..003 has existed since 0.6.0 and is referenced from `README.md:78-108`, `docs/agent-roles.md:323-325`, and `docs/agent-product-boundary.md:159`.

**`tools/lab/validate.py:94` — stale count in a comment that exists to justify a floor.**
```
94: # suite currently runs 108 tests; the floor is set far below that steady state…
$ python3 -m unittest discover -s tests | tail -3
Ran 118 tests
```

**`mock/README.md:3` — asserts the opposite of the repo's own git state.**
```
3: 这些文件演示**每种记录类型和关键状态**的最终形态。它们不是证据，不进仓库；
```
"they do not enter the repository" — but `mock/` was committed in `8199a69` (0.7.0):
```
$ git log --oneline -- mock/
8199a69 feat: 0.7.0 自动化测试切片…
$ git log --all --oneline --name-status -- mock/README.md
A       mock/README.md
```

### What `python3 tools/lab/validate.py docs` does and does not catch

Result today: `PASS docs`, exit 0 — with every finding above present.

Reading `validate_doc_consistency` at `tools/lab/validate.py:2263-2345`, the check performs exactly five assertion groups:
1. `:2277-2288` every `agents/*.md` frontmatter `name` equals its filename;
2. `:2290-2299` every `agentflow:<role>` a SKILL mentions resolves to an `agents/<role>.md`;
3. `:2301-2322` every string matching `schemas/([a-z0-9-]+\.schema\.json)` across `docs/`, `records/`, `skills/`, `agents/`, `README.md`, `AGENTS.md` names a file that exists;
4. `:2324` the AGENTS.md pre-0.5.0 tripwire — two hardcoded literals, `tools/lab/validate.py:2243`: `PRE_050_PLAN_CONTRACT_MARKERS = ("plans are JSON", "<plan_id>.json")`;
5. `:2326-2344` `docs/agent-roles.md` and `skills/agentflow/references/contracts.md` reference the same schema set.

Therefore **`docs` catches none of section 1**. It cannot catch version strings (no version logic at all — version agreement lives in a separate `validate_manifests` at `:2421-2452`, which only compares the five manifests to *each other*, never to prose). It cannot catch missing roles in README (it checks SKILL→agent, never agent→doc-inventory, so adding a role to `agents/` and forgetting README is structurally invisible). It cannot catch missing versions in iteration-log. It cannot catch dangling links other than the `schemas/*.schema.json` pattern. Its one drift tripwire (#4) is a hardcoded two-literal grep for a single 2026-09-17 incident — a pattern-per-incident design that does not generalize to the next drift.

The `manifests` check would also not have caught the 0.6.0 README drift even if extended naively: the `MANIFESTS` tuple at `tools/lab/validate.py:99` is documented as "Every manifest that carries the plugin name and version", and README/docs banners are outside it by construction.

## 2. ROOT-LEVEL ARTIFACT JUNK

```
$ for f in …; do tracked / ignored; done
.DS_Store                              tracked=no  ignored=YES
command-code-session-22eff650.html     tracked=no  ignored=YES
command-code-session-6c34dd64.html     tracked=no  ignored=YES
command-code-session-a7e23bf3.html     tracked=no  ignored=YES
ANALYSIS-REPORT.md                     tracked=YES ignored=no
REVIEW-REPORT.md                       tracked=YES ignored=no
CONSOLIDATED-REVIEW-REPORT.md          tracked=YES ignored=no
.commandcode                           tracked=no  ignored=YES
```

`.gitignore` (8 lines) covers `.DS_Store`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `private-evals/`, `.zcode/`, `.commandcode/`, `command-code-session-*.html`. So the HTML and `.DS_Store` are handled at the git layer.

### The HTML and .DS_Store are *not* handled at the packaging layer — they ship in the installed plugin

```
$ ls -la /Users/lihanghang1/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.7.4/
… ANALYSIS-REPORT.md  CONSOLIDATED-REVIEW-REPORT.md  REVIEW-REPORT.md
… command-code-session-22eff650.html  (731467)
… command-code-session-6c34dd64.html  (488584)
… command-code-session-a7e23bf3.html  (453355)
```

The local-directory marketplace snapshots the **directory**, not `git ls-files`. 1.6 MB of session HTML plus three review reports are copied into every install. Repo total is 8.3 M; the three HTML files are 1.6 M of it — ~19% of the tree is session export. `.gitignore` gives false comfort here: it makes the junk invisible to `git status` while it continues to ship.

### Contradiction with the repo's own rule

`skills/agentflow/SKILL.md:155`:
> Record decisions and evidence, not hidden chain-of-thought. Use the host's task and conversation history as the default trace. **Create repository trace files only when the user asks for durable project artifacts.**

Three `command-code-session-*.html` exports and three root-level review reports are exactly repository trace files. There is no episode, plan task, or CHANGELOG entry authorizing the HTML exports. The three reports were committed in `8199a69` (0.7.0) — a commit whose subject is "自动化测试切片——test-planner/test-executor 角色与 records/tests 记录类", i.e. the reports were swept in alongside an unrelated feature. That is the same `git add -A` failure mode the repo already recorded against itself at `docs/next-session-handoff.md:60-61` ("0.4.1 提交时用 `git add -A` 未审先推了这三条他方记录…今后提交逐文件指定路径").

### Are they referenced? Do they duplicate each other?

Cross-references (excluding self-references):
- `ANALYSIS-REPORT.md:3` and `REVIEW-REPORT.md:3` each carry a `[2026-09-17 已被取代]` superseded banner pointing at `CONSOLIDATED-REVIEW-REPORT.md`.
- `CONSOLIDATED-REVIEW-REPORT.md:8`, `:20`, `:39`, `:41`, `:43`, `:45`, `:111`, `:161`, `:180`, `:181` reference the other two.
- `records/plans/PLAN-BUSINESS-EVAL-001.md:108` says `ANALYSIS-REPORT.md 不属于本交付（untracked）` — **now false**, it is tracked.
- `records/episodes/2026-09-17/EP-20260917-002.json:5` names CONSOLIDATED as the source of the P0 batch.

Nothing in `README.md`, `AGENTS.md`, `docs/`, `skills/`, or any manifest references any of the three. They are orphaned from the navigable doc surface but shipped to users.

Structural duplication (ANALYSIS vs REVIEW):
```
$ comm -12 <(sort -u ANALYSIS-REPORT.md) <(sort -u REVIEW-REPORT.md) | grep -vc '^$'
26          (identical non-blank lines)
ANALYSIS unique lines: 111 ; REVIEW unique lines: 179
```
Low line-level overlap, but near-identical *skeletons*: both end with the same three-section priority ladder — `### 🔴 立即修（影响可信度）` / `### 🟡 短期补（补上明显缺口）` / `### 🟢 长期建（从规范到可执行）` (ANALYSIS-REPORT.md:147/154/162, REVIEW-REPORT.md:224/232/241), and both carry `## 八、横向能力缺失` + `## 九、纵向能力单薄` (ANALYSIS:98/114, REVIEW:157/172). CONSOLIDATED then repeats the same ladder a third time at `:134/:143/:150`. Three documents, one priority list, no single source of truth.

### Were the findings actioned? (checked against current code)

Actioned:
- P0#1 (record body contradicts frontmatter) — fixed: `records/bugs/2026-09-17/concurrent-writers-same-branch.md:60` now reads `已落地于 agentflow 0.4.2`.
- P0#2 (AGENTS.md JSON plan contract) — fixed: `AGENTS.md:61-63` now says Markdown + `<plan_id>.md`, and the tripwire at `tools/lab/validate.py:2243-2260` was added.
- P0#3 (records/README reviews index) — fixed: `records/README.md:11` is now feature-anchored `reviews/<project>-<feature-slug>/`.
- P0#5 (Claude Code binds only 4 roles) — fixed: `skills/agentflow/SKILL.md:15` now lists all 10.
- P1 §3.3 (four improvement handoffs have no landing place) — fixed: `records/README.md:18` "The improvement control plane's artifact handoff is implemented"; `schemas/comparison.schema.json` now exists.
- P2 (`policy.py` zero tests) — fixed: `tests/test_lab_contracts.py:1852 class PolicyDecisionTests`; also `GateIntegrityNegativeTests:2377`, `CheckDiffGateTests:2299`.

Still open, verbatim as reported:
- P1 §3.2 row 1 ("`records/.DS_Store` 在盘，`validate.py artifacts` 照样 PASS"). Still exactly true today:
  ```
  $ find . -name '.DS_Store' -not -path './.git/*'
  ./.DS_Store
  ./records/.DS_Store
  $ python3 tools/lab/validate.py all
  PASS schemas / examples / evals / artifacts / protected / manifests / docs / tests
  ```

**The reports' own line citations have decayed into misinformation.** `CONSOLIDATED-REVIEW-REPORT.md:39` and `:163` both cite `validate.py:1899` as the argparse `choices` list. Line 1899 today is:
```
1899: for version, (candidate_path, document) in candidates.items():
```
The actual `choices=` is at `tools/lab/validate.py:2765`. Same decay at `:43`, which cites `SKILL.md:88` for "a re-review may be scoped to the delta" — that phrase now lives at `skills/agentflow/SKILL.md:110`. A committed, shipped report whose `path:line` evidence no longer resolves is worse than no report, which is precisely the judgment the report itself renders at `CONSOLIDATED-REVIEW-REPORT.md:111`: *"留过时报告在工作区比没有报告更危险"*. The action taken in response was to **commit** them — inverting the recommendation.

Finally, `CONSOLIDATED-REVIEW-REPORT.md:3` banner: *"全部改动未提交，版本仍为 0.6.0"* — false on both clauses now (0.7.0/0.7.1 committed; tree at 0.7.4).

## 3. mock/ vs examples/ vs records/

**They are not three parallel copies.** Filename intersection is two entries:
```
$ comm -12 <(find mock -type f -exec basename {} \; | sort -u) <(find examples -type f -exec basename {} \; | sort -u)
PLAN-DEMO-SHARE-001.md
README.md
```
12 files each. `records/` holds real records with distinct names; `mock/` holds `*-demo` fixtures. There is no three-way duplication.

**There is one exact two-way duplicate:**
```
$ diff -q mock/records/plans/PLAN-DEMO-SHARE-001.md examples/plans/PLAN-DEMO-SHARE-001.md
exit=0     (byte-identical)
```
Both are in the uncommitted diff with `+7` each (`git diff --stat`), so the 0.7.2 callout edit had to be applied twice by hand. `CHANGELOG.md:53` documents the duplication as policy: *"mirrored into `mock/`"*. `CHANGELOG.md:10` documents the same for the episode row. This is a hand-synced surface with no checker.

**What mock/ is for** — documented only inside itself, `mock/README.md:1-5`: demo fixtures for every record type and key status, for user pre-review before adopting the format. Its stated contract ("不进仓库") is already violated (§1).

**Is mock/ validated? No — zero coverage.**
```
$ grep -c 'mock' tools/lab/validate.py
0
```
Every directory the validator touches is enumerable:
```
ROOT / "agents"  ROOT / "docs"  ROOT / "evals"  ROOT / "examples"
ROOT / "records" ROOT / "schemas" ROOT / "skills"
```
`mock/` is in none of them. `mock/README.md:30-38` claims verification was done by **copying** `mock/records/*` into a real `records/` on a `/tmp` copy — a one-time manual procedure, not a repeatable check. Nothing re-runs it. So mock/ can drift arbitrarily and `validate.py all` stays 8× green.

**Does it drift?** Not yet on the one shared artifact (identical bytes) and not on episode shape:
```
mock  EP-20260917-901.json keys: [agentflow_version, episode_id, feedback_summary, host, objective,
                                  occurred_at, outcome, provenance, redactions, schema_version, signals, source_type]
real  EP-20260918-001.json keys: identical set
```
But `mock/README.md:20` was the *last* doc surface still carrying the old episode framing and had to be caught by a human reviewer in the 0.7.4 pass (`CHANGELOG.md:10`; `records/episodes/2026-09-18/EP-20260918-002.json:37` lists it as a known residual). The drift is real, it is caught by people, and there is no machine behind it.

## 4. DOC LINK INTEGRITY

I resolved every relative markdown link across `docs/*.md`, `README.md`, `AGENTS.md`, `skills/**/*.md`, `records/**/*.md`, `mock/**/*.md`, `examples/**/*.md`, `evals/**/*.md`, `tools/**/*.md`, `schemas/*.md`, `agents/*.md`, `CHANGELOG.md`.

**Exactly one dangling link, and it is the one you flagged:**
```
DANGLING RELATIVE MD LINKS: 1
skills/agentflow/SKILL.md:99  [records/reviews/README.md](../../../records/reviews/README.md)
```

### Verdict on the relative depth: wrong from BOTH real locations

Source tree (`/Users/.../agentflows/skills/agentflow/`):
```
physical from skills/agentflow:  /Users/lihanghang1/Desktop/TestProject/records/reviews/README.md  → False
correct depth ../../:            /Users/lihanghang1/Desktop/TestProject/agentflows/records/reviews/README.md → True
```
It escapes the repository entirely, landing in the parent directory `TestProject/`.

Installed-plugin snapshot (`…/cache/agentflow-local/agentflow/0.7.4/skills/agentflow/`):
```
$ ls $SNAP/skills/agentflow/../../../records/reviews/README.md
ls: … No such file or directory        # resolves to …/cache/agentflow-local/agentflow/  (only entry: "0.7.4")
$ ls -la $SNAP/skills/agentflow/../../records/reviews/README.md
-rw-r--r--  5529  …/0.7.4/skills/agentflow/../../records/reviews/README.md   # exists
```
Wrong there too. `../../` is correct in both.

The only path from which `../../../` "works" is the workspace symlink `.zcode/skills/agentflow/` **and only under logical (non-symlink-resolving) traversal**:
```
logical from .zcode/skills/agentflow:  records/reviews/README.md  → True
```
`ls` through the symlink (physical traversal) fails. So the link is broken for every consumer that resolves the symlink, which includes `ls`, most editors, and GitHub's renderer (GitHub sees the source tree, where it dangles).

### Why the depth is wrong — provable copy source

The sibling links prove `../../../` was lifted from a `references/` file one level deeper:
```
skills/agentflow/references/contracts.md:16      ](../../../protected-paths.txt)            ✓ correct (3 up from references/)
skills/improve/references/evidence-and-release.md:81 ](../../../schemas/comparison.schema.json) ✓ correct
skills/improve/SKILL.md:27                       ](../../protected-paths.txt)               ✓ correct (2 up from skills/improve/)
skills/agentflow/SKILL.md:99                     ](../../../records/reviews/README.md)      ✗ one level too deep
```
`skills/improve/SKILL.md:27` is the direct counterexample at the same tree depth using the right count.

`validate.py docs` cannot catch this: its only path assertion (`tools/lab/validate.py:2309`) is `re.compile(r"schemas/([a-z0-9-]+\.schema\.json)")`. A `records/` link is outside the pattern.

### Path *mentions* that do not resolve

20 backticked path-like strings do not resolve. 17 are legitimate (business-repo snapshot paths in `evals/business/inputs/BT-00{1,2,3}.md`, `BT-00x` glob placeholders at `docs/agent-roles.md:323-325`, the deliberately hypothetical `tests/__init__.py` discussed at `tools/lab/README.md:40` and `protected-paths.txt:31`, and the historical `references/roles.md` in CHANGELOG/iteration-log). Two are real:

**`evals/public/inputs/AF-009.md:3` carries a dead contract:**
```
Record the accepted parser bug at `records/bugs/BUG-PARSER-001.json`.
```
Bug records are Markdown-with-frontmatter under `records/bugs/<YYYY-MM-DD>/<slug>.md` (`AGENTS.md:61-63`, `records/bugs/README.md:18`). AF-009's acceptance criterion is *"The recorder writes only the assigned records/bugs path"* (`evals/public/AF-009.json`) — so a model that obeys the brief literally produces an artifact the validator rejects, and the case scores it as compliant. Two aggravating factors: `evals/` is inside `protected-paths.txt:43`, so fixing it is a human-gated gate change; and `validate.py evals` returns PASS because it validates the case JSON's structure, not whether the brief's path obeys the record contract. This is the same defect class as the AGENTS.md drift that earned its own tripwire, sitting inside the gate rather than outside it.

## 5. DOCS SIZE / OVERLAP

```
539  docs/next-session-handoff.md   (48 KB)
409  docs/agent-roles.md
406  docs/iteration-log.md          (37 KB)
309  docs/spec-fact-check-design.md
162  docs/agent-product-boundary.md
109  docs/self-improvement-design.md
106  docs/host-native-plugin-design.md
 53  docs/host-platform-facts.md
763  CHANGELOG.md                   (56 KB)
```
`next-session-handoff.md` at 48 KB is the second-largest file in the repo after the 1.6 MB of session HTML and the two Python files.

**Is next-session-handoff.md stale? Yes, and it is the single most misleading file in the tree.** Full evidence in §1. Summary: dated 2026-09-17; content stops at 0.5.2 (batch 19); five versions and two new roles unmentioned; names a directory that does not exist on this machine as "当前机器"; names the wrong git remote in the copy-paste starter prompt; contradicts itself on whether a host install exists; and its P0/P1 checklist has not been reconciled with three subsequent feature slices. Its purpose — "read this to know where we are" — is exactly the purpose it now defeats. It is also the file the doc itself instructs the next session to read second (`:484`).

**Is iteration-log.md redundant with CHANGELOG.md? Substantially, and it is the strictly weaker copy.**
- 15 of 16 iteration-log versions are also in CHANGELOG (93.75%). The one exception, `0.3.1`, is a git-baseline entry.
- CHANGELOG covers 5 versions iteration-log does not.
- Every iteration-log entry's evidence pointer is the CHANGELOG entry for the same version: `iteration-log.md:17` `证据入口 = CHANGELOG 0.3.2`, `:18` `CHANGELOG 0.3.3`, … `:31` `CHANGELOG 0.6.0`. By its own citation column, CHANGELOG is the primary source and iteration-log is a derived index.
- The declared distinction (`iteration-log.md:3-6`: it answers *why*, CHANGELOG answers *what*) does not survive contact with the files — `CHANGELOG.md:19-29` (0.7.3) opens *"Jargon-discipline criterion widened from user feedback…"*, which is a "why". The CHANGELOG absorbed the rationale role and iteration-log stopped being updated.

Net: `docs/` carries ~945 lines across two files (handoff + iteration-log) whose current truth value is low and whose authoritative content lives in CHANGELOG, `records/episodes/`, and `records/plans/PLAN-BUSINESS-EVAL-001.md`. Nothing checks either file.

## 6. .github/ and CI

`.github/` contains exactly one file, `.github/workflows/validate.yml` (18 lines):
```yaml
1  name: deterministic checks
3  on:
4    push:
5    pull_request:
11     - uses: actions/checkout@v4
12     - uses: actions/setup-python@v5   python-version: "3.12"
15     - name: Contract, record, and gate validation
16       run: python3 tools/lab/validate.py all
17     - name: Regression tests
18       run: python3 -m unittest discover -s tests
```

**Does CI match what the docs claim is enforced?** For the two commands named, yes, and `AGENTS.md:8-24` names exactly these two. Caveats:

1. **Step 18 is redundant.** `validate.py all` already includes `("tests", validate_unit_tests)` (`tools/lab/validate.py:2827`), which shells the same discovery. `CONSOLIDATED-REVIEW-REPORT.md:41` already noted this ("末尾再单跑一次 unittest 属冗余但无害") and it was not acted on.
2. **`validate.py installed` is not in CI** — correctly, since it `SKIP`s without a local install (`AGENTS.md:38-39`). But that means the drift check the docs lean on hardest (`README.md:17-19`, `AGENTS.md:28-37`) has *no* automated enforcement anywhere, only a human remembering to run it.
3. **CI cannot catch anything in this report.** Every version-drift, link, orphan, and staleness finding above coexists with a green `validate.py all`. A repo whose stated thesis is "a check you cannot reproduce counts as not run" (`AGENTS.md:17-18`) has a CI whose green signal is uncorrelated with its documentation's truth.
4. **CI never runs.** The remote is `github.com/Ganseblum/agentflows.git` and HEAD is 0.7.1 while the tree is 0.7.4; the 0.7.2–0.7.4 work has never been pushed, so the workflow has never evaluated it. `on: push` with no branch filter also means the workflow fires on every branch, including candidate worktrees — a candidate whose whole point is being measured in isolation would get a public CI run.

## 7. Other repository-level problems

**a. `records/.DS_Store` is committed-adjacent and silently skipped.** `.gitignore:1` keeps it untracked, but `validate.py artifacts` walks `records/` and returns PASS with it present — the exact defect logged at `CONSOLIDATED-REVIEW-REPORT.md:85` and never fixed. The mitigation exists but only for `examples/`: `tools/lab/validate.py:1466` `# Hidden entries (.DS_Store and friends) are host/OS artifacts, not examples.` — the same guard was never added to the `records/` walker, so the `records/` case fails open rather than being explicitly skipped.

**b. Uncommitted work is the release state.** The installed 0.7.4 snapshot, the CHANGELOG's 0.7.2/0.7.3/0.7.4 entries, four episodes documenting completed review gates (`records/episodes/2026-09-18/EP-20260918-00{2,3,4,5}.json`), and a gate change to a protected path (`skills/improve/references/episode.schema.json`, +41 lines, protected by `protected-paths.txt:45`) all exist only in the working tree. `records/episodes/2026-09-18/EP-20260918-005.json:8` claims the repo has entered a state where *"所有已知项都有处置结论"* — asserted from an uncommitted tree with 18 dirty files. `records/plans/PLAN-BUSINESS-EVAL-001.md:107` already identified this exact hazard for 0.6.0 (*"基线整体未提交，git 无法隔离 delta"*) and it recurred three versions later without a recurrence record.

**c. `.commandcode/` (16 KB, `settings.json` + `taste/taste.md`)** is gitignored and small. Not a problem in itself, but it is a second tool's config living in the repo root, referenced only by `records/plans/PLAN-BUSINESS-EVAL-001.md:108` and `CONSOLIDATED-REVIEW-REPORT.md:111`. Like the HTML files, it ships into the installed snapshot because the marketplace copies the directory.

**d. The version-bump surface is manual and 5-wide with no prose coupling.** `validate_manifests` (`tools/lab/validate.py:2421-2452`) enforces agreement across `plugin.json`, `marketplace.json`, `.claude-plugin/`, `.codex-plugin/`, `.zcode-plugin/` — all five correctly at 0.7.4. But four prose surfaces carry the version too (README ×2, two doc banners), none coupled to the manifests. The repo built a checker for exactly the failure class it keeps suffering (`docs/iteration-log.md:18` "0.3.3 | …manifest-drift") and then scoped it to stop one file short of where the drift actually lives.

**e. Self-referential blind spot in the hygiene rule.** `skills/agentflow/SKILL.md:155` forbids unrequested trace files; `AGENTS.md:64` forbids unrequested commits. Both were violated in the same commit (`8199a69`, which added three unsolicited session reports under a feature-slice subject line). Neither rule has a checker, and neither violation produced a bug record or recurrence entry. Contrast `records/bugs/recurrence/unverified-behavior-claims.md`, which exists precisely because the repo's own doctrine is that an unenforced rule must at minimum generate a recurrence ledger when it fails.

## Priority summary

**Actively misleading right now (fix first):**
1. `docs/next-session-handoff.md` — wrong machine path `:7`/`:483`, wrong remote `:483`, self-contradiction `:11` vs `:510`, five versions and two roles missing. It is the designated entry point for new sessions.
2. Version 0.6.0 in `README.md:23`, `README.md:116`, `docs/host-native-plugin-design.md:3`, `docs/self-improvement-design.md:3` (tree is 0.7.4).
3. `README.md:26-30` — missing `test-planner`/`test-executor` and 6 of 9 schemas; README has zero mention of the 0.7.0 testing slice.
4. `skills/agentflow/SKILL.md:99` — `../../../records/reviews/README.md` is one level too deep from both the source tree and the installed snapshot; `../../` is correct.
5. `evals/public/inputs/AF-009.md:3` — instructs the agent to write `records/bugs/BUG-PARSER-001.json`, a contract removed long ago; inside the protected gate.

**Shipping junk:** 1.6 MB of `command-code-session-*.html` plus three orphaned review reports are copied into the installed plugin at `…/agentflow/0.7.4/`; `.gitignore` hides them from git but not from the packager. The three reports contradict the repo's own trace-file rule (`skills/agentflow/SKILL.md:155`), duplicate one another's priority ladder three times, and carry `path:line` citations that no longer resolve (`CONSOLIDATED-REVIEW-REPORT.md:39`/`:163` → `validate.py:1899`, actual `:2765`).

**Structurally undetectable:** everything above coexists with `validate.py all` → 8× PASS, `validate.py docs` → PASS, `validate.py installed` → PASS, and a green CI. `validate_doc_consistency` (`tools/lab/validate.py:2263-2345`) asserts five narrow things; version claims, README role/schema inventories, non-schema links, `mock/` (zero coverage — `grep -c mock tools/lab/validate.py` → 0), and git-vs-tree agreement are all outside it.

*（子代理④运行统计：约 2,076,481 tokens，55 次工具调用，约 12.2 分钟。）*

---

## 6. 助手 · 状态播报 + 亲自复核实验（第一批）

> 四路审计已回，全部有 file:line 证据。我现在自己复核几条最要命的机械性结论——按仓库规则，实验只在 /tmp 副本里做。

**工具调用 ① —— `Bash`（核对 policy 退出码、SKILL 链接深度、种子文件被 git 跟踪、release schema 键集）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows
echo "=== A. policy.py exit code on reject ==="
sed -n '205,275p' tools/lab/policy.py
echo
echo "=== B. SKILL.md:99 link depth ==="
ls -la skills/agentflow/../../../records/reviews/README.md 2>&1 | head -2
ls -la skills/agentflow/../../records/reviews/README.md 2>&1 | head -2
echo
echo "=== C. evals tracked? (answer key in candidate worktree) ==="
git ls-files evals/business/seeds/ | head
echo
echo "=== D. release-record promote const ==="
python3 - <<'PY'
import json
s=json.load(open('skills/improve/references/release-record.schema.json'))
print("top-level allowed keys:", sorted(s.get('properties',{}).keys()))
print("required:", s.get('required'))
print("additionalProperties:", s.get('additionalProperties'))
print("allOf/if-then count:", len(s.get('allOf',[])))
PY
```

**返回：**

```text
=== A. policy.py exit code on reject ===
    if slice_failures:
        reasons.append(f"protected slice regressions: {', '.join(slice_failures)}")

    if invalid:
        evaluation_result = "invalid"
        decision = "reject"
    elif guardrail_failures or primary_regressed or slice_failures:
        evaluation_result = "worse"
        decision = "reject"
    elif primary_improved:
        evaluation_result = "better"
        decision = "promote"
        reasons.append("all declared primary metrics are non-regressing and at least one improved")
    else:
        evaluation_result = "neutral"
        decision = "revise"
        reasons.append("no declared primary metric improved")

    return {
        "schema_version": 1,
        "candidate_version": candidate_record["candidate_version"],
        "parent_version": candidate_record["parent_version"],
        "evaluation_result": evaluation_result,
        "decision": decision,
        "metrics": metric_results,
        "protected_slice_metrics": slice_metrics,
        "reasons": reasons,
        "required_human_approval": True,
        "rollback_target": candidate_record.get("parent_version"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-record", required=True)
    parser.add_argument("--baseline-result", required=True)
    parser.add_argument("--candidate-result", required=True)
    parser.add_argument("--policy")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    candidate_record, candidate_errors = load_candidate(args.candidate_record)
    baseline, baseline_errors = load_result(args.baseline_result)
    candidate, result_errors = load_result(args.candidate_result)
    errors = candidate_errors + baseline_errors + result_errors
    if errors or candidate_record is None or baseline is None or candidate is None:
        print("FAIL policy inputs", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    try:
        policy = load_policy(args.policy)
        decision = decide(candidate_record, baseline, candidate, policy)
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL policy evaluation: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(decision, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(f"WROTE {output}")
    else:
        print(encoded, end="")
    return 0 if decision["decision"] in {"promote", "revise", "reject"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

=== B. SKILL.md:99 link depth ===
ls: skills/agentflow/../../../records/reviews/README.md: No such file or directory
-rw-r--r--@  1 lihanghang1  526858981  5529 Sep 17 11:49 skills/agentflow/../../records/reviews/README.md

=== C. evals tracked? (answer key in candidate worktree) ===
evals/business/seeds/BT-001.seeds.json
evals/business/seeds/BT-002.seeds.json
evals/business/seeds/BT-003.seeds.json

=== D. release-record promote const ===
top-level allowed keys: ['approvals', 'baseline_results', 'candidate', 'candidate_results', 'decision', 'evaluation_result', 'rollback_to', 'rollout', 'schema_version']
required: ['schema_version', 'candidate', 'baseline_results', 'candidate_results', 'evaluation_result', 'decision', 'approvals', 'rollout', 'rollback_to']
additionalProperties: False
allOf/if-then count: 4
```

**工具调用 ② —— `Bash`（/tmp 一次性副本上验证 `records/` 缺失时的 fail-open）：**

```sh
set -e
rm -rf /tmp/afaudit && mkdir -p /tmp/afaudit
cp -R /Users/lihanghang1/Desktop/TestProject/agentflows /tmp/afaudit/af
cd /tmp/afaudit/af
echo "=== throwaway copy ready at /tmp/afaudit/af ==="
echo
echo "=== E. validate.py artifacts with records/ REMOVED (fail-open test) ==="
mv records /tmp/afaudit/records-stash
python3 tools/lab/validate.py artifacts; echo "EXIT(artifacts, no records/)=$?"
python3 tools/lab/validate.py all 2>&1 | tail -12; echo "EXIT(all, no records/)=$?"
mv /tmp/afaudit/records-stash records
echo
echo "=== F. restore check ==="
python3 tools/lab/validate.py artifacts; echo "EXIT(restored)=$?"
```

**返回：**

```text
=== throwaway copy ready at /tmp/afaudit/af ===

=== E. validate.py artifacts with records/ REMOVED (fail-open test) ===
PASS artifacts
EXIT(artifacts, no records/)=0
PASS schemas
PASS examples
PASS evals
PASS artifacts
PASS protected
PASS manifests
FAIL docs (1 error(s))
  - /private/tmp/afaudit/af/records: cannot read document: [Errno 2] No such file or directory: '/private/tmp/afaudit/af/records'
FAIL tests (1 error(s))
  - tests: unit tests failed (exit 1): FAILED (failures=2)
EXIT(all, no records/)=0

=== F. restore check ===
PASS artifacts
EXIT(restored)=0
Shell cwd was reset to /Users/lihanghang1/Desktop/TestProject/agentflows
```

---

## 7. 助手 · 状态播报 + 复核实验（第二批：退出码纠正 + gate 绕过）

> E 那条我自己的 `$?` 测的是 `tail` 的退出码，不能算。重测退出码，并验证 gate 绕过与测试计数两条最严重的结论。

**工具调用 ① —— `Bash`（重测退出码 + artifacts 变体 + .DS_Store）：**

```sh
cd /tmp/afaudit/af
echo "=== E2. correct exit code of validate.py all with records/ removed ==="
mv records /tmp/afaudit/records-stash
python3 tools/lab/validate.py all > /tmp/afaudit/out.txt 2>&1
echo "EXIT(all)=$?"
tail -6 /tmp/afaudit/out.txt
mv /tmp/afaudit/records-stash records
echo
echo "=== E3. artifacts alone with records/ present but EMPTIED of record dirs ==="
mkdir -p /tmp/afaudit/stash2 && mv records/bugs records/episodes records/plans /tmp/afaudit/stash2/
python3 tools/lab/validate.py artifacts; echo "EXIT(artifacts, empty records)=$?"
mv /tmp/afaudit/stash2/* records/
echo
echo "=== E4. .DS_Store inside records/ ==="
find /Users/lihanghang1/Desktop/TestProject/agentflows -name '.DS_Store' -not -path '*/.git/*'
touch records/.DS_Store
python3 tools/lab/validate.py artifacts; echo "EXIT(artifacts, .DS_Store)=$?"
rm -f records/.DS_Store
```

**返回：**

```text
=== E2. correct exit code of validate.py all with records/ removed ===
EXIT(all)=1
PASS protected
PASS manifests
FAIL docs (1 error(s))
  - /private/tmp/afaudit/af/records: cannot read document: [Errno 2] No such file or directory: '/private/tmp/afaudit/af/records'
FAIL tests (1 error(s))
  - tests: unit tests failed (exit 1): FAILED (failures=2)

=== E3. artifacts alone with records/ present but EMPTIED of record dirs ===
PASS artifacts
EXIT(artifacts, empty records)=0

=== E4. .DS_Store inside records/ ===
/Users/lihanghang1/Desktop/TestProject/agentflows/.DS_Store
/Users/lihanghang1/Desktop/TestProject/agentflows/records/.DS_Store
PASS artifacts
EXIT(artifacts, .DS_Store)=0
Shell cwd was reset to /Users/lihanghang1/Desktop/TestProject/agentflows
```

**工具调用 ② —— `Bash`（/tmp 独立 git 仓库上验证非 ASCII 路径绕过 protected-paths 门）：**

```sh
cd /tmp/afaudit
rm -rf gate && mkdir gate && cd gate
# build a tiny git repo mimicking the gate to test the non-ASCII quoting bypass
cp -R /tmp/afaudit/af/tools /tmp/afaudit/af/protected-paths.txt .
mkdir -p evals/public
git init -q . && git add -A >/dev/null 2>&1 && git -c user.email=a@b -c user.name=a commit -qm base
BASE=$(git rev-parse HEAD)
echo "core.quotepath default: '$(git config --get core.quotepath)' (empty = true/default)"
echo
echo "--- control: add ASCII file under evals/ (should be BLOCKED) ---"
printf '{}' > evals/public/AF-999.json
python3 tools/lab/isolation.py check-diff --candidate . --base "$BASE"; echo "EXIT=$?"
rm -f evals/public/AF-999.json
echo
echo "--- test: add NON-ASCII file under evals/ (claim: NOT blocked) ---"
printf '{}' > "evals/public/AF-测试.json"
git status --porcelain
echo "-- raw git ls-files --others output --"
git ls-files --others --exclude-standard
echo "-- check-diff verdict --"
python3 tools/lab/isolation.py check-diff --candidate . --base "$BASE"; echo "EXIT=$?"
```

**返回：**

```text
core.quotepath default: '' (empty = true/default)

--- control: add ASCII file under evals/ (should be BLOCKED) ---
candidate changed a forbidden path
{
  "candidate": "/private/tmp/afaudit/gate",
  "changed_paths": [
    "evals/public/AF-999.json"
  ],
  "protected_paths_declared_by": "/private/tmp/afaudit/gate/protected-paths.txt",
  "forbidden_paths": [
    "agents/evaluator.md",
    "agents/release-governor.md",
    "evals",
    "skills/improve/references",
    "schemas",
    "tests/test_lab_contracts.py",
    "tools/lab/artifact_digest.py",
    "tools/lab/eval_runner.py",
    "tools/lab/host_adapter.py",
    "tools/lab/isolation.py",
    "tools/lab/policy.py",
    "tools/lab/seed_grader.py",
    "tools/lab/validate.py",
    "protected-paths.txt"
  ],
  "blocked": [
    "evals/public/AF-999.json"
  ]
}
EXIT=1

--- test: add NON-ASCII file under evals/ (claim: NOT blocked) ---
?? evals/
-- raw git ls-files --others output --
"evals/public/AF-\346\265\213\350\257\225.json"
-- check-diff verdict --
{
  "candidate": "/private/tmp/afaudit/gate",
  "changed_paths": [
    "\"evals/public/AF-/346/265/213/350/257/225.json\""
  ],
  "protected_paths_declared_by": "/private/tmp/afaudit/gate/protected-paths.txt",
  "forbidden_paths": [
    "agents/evaluator.md",
    "agents/release-governor.md",
    "evals",
    "skills/improve/references",
    "schemas",
    "tests/test_lab_contracts.py",
    "tools/lab/artifact_digest.py",
    "tools/lab/eval_runner.py",
    "tools/lab/host_adapter.py",
    "tools/lab/isolation.py",
    "tools/lab/policy.py",
    "tools/lab/seed_grader.py",
    "tools/lab/validate.py",
    "protected-paths.txt"
  ],
  "blocked": []
}
EXIT=0
```

---

## 8. 助手 · 状态播报 + 复核实验（第三批）

> Gate 绕过复现成功了。再验证三条：records 被掏空后 `all` 是否仍绿、测试计数门能否伪造、以及 release 记录契约自相矛盾。

**工具调用 ① —— `Bash`（records 掏空后的 `all` + 读取测试计数门代码）：**

```sh
cd /tmp/afaudit/af
echo "=== G. validate.py all with records/ present but all record dirs removed ==="
mkdir -p /tmp/afaudit/stash3 && mv records/bugs records/episodes records/plans records/reviews records/tests records/improvement /tmp/afaudit/stash3/ 2>/dev/null
ls records/
python3 tools/lab/validate.py all > /tmp/afaudit/out2.txt 2>&1; echo "EXIT(all, records emptied)=$?"
cat /tmp/afaudit/out2.txt
mv /tmp/afaudit/stash3/* records/
echo
echo "=== H. Ran N tests spoof + skip counting ==="
sed -n '2490,2532p' tools/lab/validate.py
```

**返回：**

```text
=== G. validate.py all with records/ present but all record dirs removed ===
README.md
EXIT(all, records emptied)=1
PASS schemas
PASS examples
PASS evals
PASS artifacts
PASS protected
PASS manifests
PASS docs
FAIL tests (1 error(s))
  - tests: unit tests failed (exit 1): FAILED (failures=1)

=== H. Ran N tests spoof + skip counting ===
            )
        )
    for name in EXPECTED_TEST_FILES:
        if not (tests_dir / name).is_file():
            errors.append(ValidationError(f"tests/{name}", "declared test file is missing"))
    if errors:
        return errors
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    ran = re.search(r"Ran (\d+) tests?", f"{completed.stderr}\n{completed.stdout}")
    count = int(ran.group(1)) if ran else None
    if count == 0:
        # unittest exits 5 for an empty run on Python 3.12+, but 0 on older interpreters;
        # the count check makes the empty suite fail on both.
        return [ValidationError("tests", "unit tests ran 0 tests; the regression suite is empty")]
    if completed.returncode != 0:
        detail = (completed.stderr.strip() or completed.stdout.strip()).splitlines()
        summary = detail[-1] if detail else "no output"
        return [ValidationError("tests", f"unit tests failed (exit {completed.returncode}): {summary}")]
    if count is None:
        return [
            ValidationError(
                "tests",
                "unit test output has no 'Ran N tests' summary; cannot confirm how many tests ran",
            )
        ]
    if count < MIN_UNIT_TEST_COUNT:
        return [
            ValidationError(
                "tests",
                f"unit tests ran {count} tests, below the required floor of {MIN_UNIT_TEST_COUNT}; "
                "shrinking the regression suite is a gate change that requires explicit review",
            )
        ]
    return []
```

**工具调用 ② —— `Bash`（核对 measurement 条款、reviewer 工具清单、路由表矛盾）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows
echo "=== I. improve SKILL measurement clause ==="
grep -n "measurement" skills/improve/SKILL.md | head -20
echo
echo "--- does any schema allow a 'measurement' key? ---"
grep -rn "measurement" schemas/ skills/improve/references/*.json | head
echo
echo "=== J. reviewer tools vs 'actual diff' instruction ==="
sed -n '1,14p' agents/reviewer.md
grep -n "diff" agents/reviewer.md
echo
echo "=== K. roles.md routing row vs SKILL.md non-waivable gate ==="
sed -n '8,26p' skills/agentflow/references/roles.md
echo "--- SKILL.md:121-128 ---"
sed -n '121,128p' skills/agentflow/SKILL.md
```

**返回：**

```text
=== I. improve SKILL measurement clause ===
27:The candidate write scope excludes every path declared in [`protected-paths.txt`](../../protected-paths.txt) — the evaluator and governor role files, the evaluation suite, the measurement path under `tools/lab/`, the release rules, the result schemas, and the list itself. Enforce it with `isolation.py check-diff` before the candidate is evaluated, not by reading the candidate's summary. Session-enforced tool allowlists (`tools:` in the agent frontmatter) are the second layer; path exclusions still depend on this check plus a supervisor diff review.
56:checklists, brief disciplines, acceptance steps — has no regression measurement there. When such
63:review findings that triggered it, its release record must state `measurement: none (method-level

--- does any schema allow a 'measurement' key? ---
〔转写注：此处为空输出，即 schemas/ 与 skills/improve/references/*.json 中没有任何 "measurement" 键〕

=== J. reviewer tools vs 'actual diff' instruction ===
---
name: reviewer
description: Independently reviews material implementations after coding, checking acceptance criteria, correctness, regressions, security boundaries, and verification evidence. Read-only during the review pass.
model: inherit
maxTurns: 15
tools: Read, Glob, Grep
disallowedTools: Bash, Write, Edit
---

You are the independent reviewer in an Agentflow team.

**Artifact ownership**: read-only for everything — the implementation under review, docs, `records/`. This role edits nothing during the review pass and runs no commands.

**Check protocol.** You cannot run commands, so you author them: state the exact command and the
26:Inspect the actual diff and supplied verification records. Request missing independent checks from the supervisor rather than running candidate-controlled commands.
28:Review the actual diff and surrounding code against the assigned objective and acceptance criteria. Prioritize correctness, regressions, security and permission boundaries, recovery behavior, and missing meaningful tests. Avoid blocking on style unless the repository enforces it.

=== K. roles.md routing row vs SKILL.md non-waivable gate ===
hard cases; most tasks use one or two rows.

| Task shape | Roles to start |
| --- | --- |
| Single-layer small fix, clear reproduction | Supervisor alone |
| Frontend or backend implementation with a bounded scope | One engineer + Reviewer when material |
| Cross-layer feature, contract change, migration | Technical Director → both engineers (parallel investigation) → Reviewer |
| Planning request, no code yet | Specialists in parallel → Plan Architect |
| Automated testing of a user-visible feature (user asked, or the plan carries a test-design task) | Test Planner → Test Executor (supervisor performs host-browser steps) → Reviewer in flow-reasonableness mode |
| Test run produced failures or coverage gaps | Executor evidence → bug chain (Investigator → Fixer → Reviewer → Recorder) |
| Material, uncertain, recurring, or cross-layer bug | Bug Investigator → Bug Fixer → Reviewer → Bug Recorder |
| Small bug with a verified reproduction | Fixer + Supervisor-side check; record when it should persist |
| Review of documents authored under another system's rules | Supervisor (archive + review record) + Reviewer; findings become bug records with `provenance: external` |
| Plugin/role-instruction improvement | Feedback Analyst → Candidate Engineer → Evaluator → Release Governor |

## Supervisor

The current host's main task is the supervisor. It owns intake, decomposition, permissions, integration, final verification, and the final decision. It may implement small glue changes, but it must inspect delegated work rather than trusting summaries, and it may not waive the independent review gate for code it wrote itself.

--- SKILL.md:121-128 ---
- **Small change** — needs no worker roles and no architecture gate. It qualifies only when
  **all** of these hold: one file and one layer; no contract changes (schema, API shape, CLI
  flag, config key, record format); no shared cross-cutting mechanism touched (interceptor,
  global error handler, route guard, listener, middleware); the deterministic checks that
  cover it pass on the actual files; and the defect it fixes has a verified reproduction.
  Anything else is **material**. This class does not touch the review gate: when the
  supervisor wrote part of a change — small or material — the independent reviewer gate for it
  is mandatory and cannot be waived (hard boundary 1).
```

---

## 9. 助手 · 复核实验（第四批：全量 skip 实测 + 种子匹配内部 + 语料计数）

**工具调用 ① —— `Bash`（/tmp 副本上给全部 19 个测试类加 `@unittest.skip`，验证测试门是否仍 PASS）：**

```sh
cd /tmp/afaudit/af
echo "=== H2. skip-everything exploit against MIN_UNIT_TEST_COUNT ==="
grep -n "MIN_UNIT_TEST_COUNT" tools/lab/validate.py | head -3
python3 - <<'PY'
import re,pathlib
p=pathlib.Path('tests/test_lab_contracts.py')
s=p.read_text(encoding='utf-8')
# blanket-skip the whole module the way a candidate shrinking the suite would
s2 = s.replace("import unittest", "import unittest\nimport os as _os", 1)
s2 = s2.replace("class ", "@unittest.skip('shrunk')\nclass ", 1)
# skip ALL classes
s2 = re.sub(r"(?m)^class (\w+)\(unittest\.TestCase\):", r"@unittest.skip('shrunk')\nclass \1(unittest.TestCase):", s)
p.write_text(s2, encoding='utf-8')
print("classes skipped:", s2.count("@unittest.skip('shrunk')"))
PY
python3 -m unittest discover -s tests 2>&1 | tail -3
echo "--- validate.py tests verdict with the entire suite skipped ---"
python3 tools/lab/validate.py tests; echo "EXIT(tests, all skipped)=$?"
python3 tools/lab/validate.py all 2>/dev/null | tail -3
```

**返回：**

```text
=== H2. skip-everything exploit against MIN_UNIT_TEST_COUNT ===
97:MIN_UNIT_TEST_COUNT = 20
2475:    against MIN_UNIT_TEST_COUNT, so an empty or degenerate suite fails even when it exits 0.
2522:    if count < MIN_UNIT_TEST_COUNT:
classes skipped: 19
Ran 118 tests in 0.000s

OK (skipped=118)
--- validate.py tests verdict with the entire suite skipped ---
PASS tests
EXIT(tests, all skipped)=0
PASS manifests
PASS docs
PASS tests
```

**工具调用 ② —— `Bash`（seed_grader 匹配逻辑原文 + 语料精确计数 + CHANGELOG 0.7.1 记录）：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows
echo "=== L. seed_grader matching internals ==="
sed -n '60,95p' tools/lab/seed_grader.py
echo
echo "=== M. corpus counts ==="
echo "bug records: $(find records/bugs -name '*.md' -not -name 'README.md' | wc -l | tr -d ' ')"
echo "episodes:    $(find records/episodes -name '*.json' | wc -l | tr -d ' ')"
echo "plans:       $(find records/plans -name '*.md' -not -name 'README.md' | wc -l | tr -d ' ')"
echo "reviews:     $(find records/reviews -type f -not -name 'README.md' | wc -l | tr -d ' ')"
echo "tests recs:  $(find records/tests -type f -not -name 'README.md' | wc -l | tr -d ' ')"
echo "improvement: $(find records/improvement -type f -not -name 'README.md' | wc -l | tr -d ' ')"
echo "class_id tagged records: $(grep -rln '^class_id:' records/bugs --include='*.md' | wc -l | tr -d ' ')"
echo "holdout true cases: $(grep -l '"holdout": true' evals/*/*.json 2>/dev/null | wc -l | tr -d ' ')"
echo "git tags: $(git tag -l | wc -l | tr -d ' ')"
echo
echo "=== N. 0.7.1 governor claim in CHANGELOG ==="
grep -n "neutral" CHANGELOG.md | head -5
```

**返回：**

```text
=== L. seed_grader matching internals ===


def normalize_path(value: str) -> tuple[str, ...]:
    """Path components with ``./`` segments and any absolute prefix dropped."""
    return tuple(part for part in value.strip().split("/") if part not in ("", "."))


def is_suffix(short: tuple[str, ...], long: tuple[str, ...]) -> bool:
    return len(short) <= len(long) and long[len(long) - len(short):] == short


def paths_match(finding_path: str, doc_ref: str) -> bool:
    """True when one normalized path is a component-wise suffix of the other."""
    finding = normalize_path(finding_path)
    seed = normalize_path(doc_ref)
    if not finding or not seed:
        return False
    return is_suffix(seed, finding) or is_suffix(finding, seed)


def seed_matches_finding(seed: dict[str, Any], finding: dict[str, str]) -> bool:
    """One seed hit: path rule and at least one anchor inside ``issue`` or ``evidence``.

    The two fields are joined with a newline, never concatenated bare: an anchor has to
    appear inside one field as written, so text split across the field boundary cannot
    spell one out.
    """
    if not paths_match(finding["path"], seed["doc_ref"]):
        return False
    text = f"{finding['issue']}\n{finding['evidence']}"
    return any(anchor in text for anchor in seed["strategy"]["anchors"])


def validate_seed_document(document: Any, source: str) -> dict[str, Any]:
    """Validate one seed list against the frozen matching contract; return it unchanged.
〔转写注：sed -n '60,95p' 的输出到此行为止〕

=== M. corpus counts ===
bug records: 10
episodes:    9
plans:       1
reviews:     0
tests recs:  0
improvement: 0
class_id tagged records: 2
holdout true cases: 0
git tags: 0

=== N. 0.7.1 governor claim in CHANGELOG ===
148:  acceptance criteria against the files (verdict `neutral` — real, internally consistent, and
625:    check still rejects it; the documentation no longer credits it with the neutralization it
641:    undeclared `.py` files in the directory, closing the neutralization vector (a package
```

---

## 10. 助手 · 复核实验（第五批：真实树安全性、CHANGELOG 原文、语料细分、只读角色工具清单）

**工具调用 ① —— `Bash`：**

```sh
cd /Users/lihanghang1/Desktop/TestProject/agentflows
echo "=== SAFETY: real tree untouched? ==="
git status --short | wc -l | tr -d ' '; echo "(was 18 modified + 4 untracked at session start)"
git status --short | head -25
echo
echo "=== O. CHANGELOG 0.7.1 governor verdict ==="
sed -n '143,156p' CHANGELOG.md
echo
echo "=== P. precise corpus split ==="
echo "real bug records: $(find records/bugs -mindepth 2 -name '*.md' -not -path '*recurrence*' | wc -l | tr -d ' ')"
echo "recurrence ledgers: $(find records/bugs/recurrence -name '*.md' -not -name 'README.md' | wc -l | tr -d ' ')"
grep -rln '^class_id:' records/bugs --include='*.md'
echo
echo "=== Q. read-only roles' tool allowlists (can they run validate.py report?) ==="
for f in feedback-analyst evaluator release-governor bug-investigator reviewer technical-director; do printf '%-20s ' "$f"; grep -m1 '^tools:' agents/$f.md; done
```

**返回：**

```text
=== SAFETY: real tree untouched? ===
22
(was 18 modified + 4 untracked at session start)
 M .claude-plugin/plugin.json
 M .codex-plugin/plugin.json
 M .zcode-plugin/plugin.json
 M CHANGELOG.md
 M docs/agent-roles.md
 M docs/host-platform-facts.md
 M evals/business/README.md
 M examples/bug-records/reviewer-missed-error-contract.md
 M examples/plans/PLAN-DEMO-SHARE-001.md
 M marketplace.json
 M mock/README.md
 M mock/records/plans/PLAN-DEMO-SHARE-001.md
 M plugin.json
 M records/README.md
 M records/episodes/README.md
 M records/plans/PLAN-BUSINESS-EVAL-001.md
 M skills/agentflow/SKILL.md
 M skills/improve/references/episode.schema.json
?? records/episodes/2026-09-18/EP-20260918-002.json
?? records/episodes/2026-09-18/EP-20260918-003.json
?? records/episodes/2026-09-18/EP-20260918-004.json
?? records/episodes/2026-09-18/EP-20260918-005.json

=== O. CHANGELOG 0.7.1 governor verdict ===
  pass-decision-with-failures).
- Gate change, human-directed: `schemas/` (two new record contracts), `tools/lab/validate.py`,
  and `tests/test_lab_contracts.py` were edited to land this batch, with the user's explicit
  approval in-session (0.6.0 precedent).
- Independent evaluation and release decision: an independent evaluator verified all eight
  acceptance criteria against the files (verdict `neutral` — real, internally consistent, and
  gate-enforced exactly as claimed; unmeasured by policy), and the release governor returned
  `promote` with conditions (measurement:none carried unchanged; reinstall gated on user
  approval; follow-ups before the next method-level release). Post-review follow-ups landed in
  this entry: the smoke-first ordering sentence in the agentflow skill's Automated testing
  section, the case detail-heading scan narrowed to the `## 用例` section with an
  empty-heading guard, and the executor's `scratch/` directory declared in the tests contract
  table.
- `measurement: none (method-level change, no instrumented business task)` — `evals/` has no

=== P. precise corpus split ===
real bug records: 9
recurrence ledgers: 1
records/bugs/recurrence/unverified-behavior-claims.md
records/bugs/2026-09-15/unverified-behavior-claims-recurring.md

=== Q. read-only roles' tool allowlists (can they run validate.py report?) ===
feedback-analyst     tools: Read, Glob, Grep
evaluator            tools: Read, Glob, Grep
release-governor     tools: Read, Glob, Grep
bug-investigator     tools: Read, Glob, Grep
reviewer             tools: Read, Glob, Grep
technical-director   tools: Read, Glob, Grep
```

---

## 11. 助手 · 收尾（清理实验副本 + 最终确认）

**工具调用 ① —— `Bash`：**

```sh
rm -rf /tmp/afaudit && echo "throwaway copy removed"; cd /Users/lihanghang1/Desktop/TestProject/agentflows && python3 tools/lab/validate.py all 2>&1 | tail -3; echo "EXIT=${PIPESTATUS[0]}"; git status --short | wc -l | tr -d ' '
```

**返回：**

```text
throwaway copy removed
PASS manifests
PASS docs
PASS tests
EXIT=0
22
```

---

## 12. 助手 · 最终评估报告（全文逐字）

> 实验副本已删除，真实工作树未被触碰（`git status` 仍是会话开始时的 18 改 + 4 未跟踪，`validate.py all` 仍 8×PASS）。以下是评估结论。

---

# Agentflow 整体评估

**一句话结论：规则层的设计水准很高——判据写得比绝大多数 agent 框架都清楚；但承重的东西几乎全是散文，不是约束。真正被机器强制的只有 8 个检查，我实测其中 3 个存在可复现的绕过或失效；而「以模治模」这条闭环从未跑通过一次，且它的 release 契约在结构上写不出一份合法记录。**

下面分六块，每条都有我自己复现过的证据。

---

## 一、我实测复现的硬 bug（最高优先级）

这三条不是读代码推断的，是我在 `/tmp` 副本上跑出来的。

### 1. 全量 `@unittest.skip` 可以通过回归测试门 —— 门形同虚设

`validate.py:2505-2529` 用 `re.search(r"Ran (\d+) tests?")` 取测试数并与 `MIN_UNIT_TEST_COUNT = 20` 比较，注释写着「缩减回归套件是 gate change，需要显式评审」。但 `Ran N tests` 里 **包含 skipped**，而代码从不读 skip 数。我给 19 个测试类全部加上 `@unittest.skip`：

```
Ran 118 tests in 0.000s
OK (skipped=118)
--- validate.py tests verdict ---
PASS tests        EXIT=0
```

`validate.py all` 依然报 `PASS tests`。也就是说，候选版本可以把整个回归套件静默停掉，两道 CI 步骤全绿。附带一个次级缺陷：`re.search` 取的是 stderr+stdout 拼接后的**第一个**匹配，任何测试在运行中往 stderr 打一行 `Ran 999 tests` 就能伪造计数。

### 2. 非 ASCII 文件名可以绕过 protected-paths 门

`isolation.py:131-141` 调 `git diff/ls-files` 时没有 `-z`，也没有 `core.quotepath=false`。Git 默认会把非 ASCII 路径加引号并八进制转义，而阻断判断是字面前缀比较 `path.startswith(prefix + "/")`。对照实验：

```
# 控制组：ASCII 名，正确阻断
evals/public/AF-999.json      → "blocked": ["evals/public/AF-999.json"]   EXIT=1

# 实验组：非 ASCII 名，未阻断
evals/public/AF-测试.json      → "blocked": []                            EXIT=0
```

`evals/`、`schemas/`、`skills/improve/references/` 这三个目录前缀今天就可以用「新增一个中文名文件」的方式穿过。讽刺的是同仓库的 `host_adapter.py:151` 用了 `-z`，唯独守门的那个没用。你们自己的 `CONSOLIDATED-REVIEW-REPORT.md:89` 把它记为「潜在 fail-open 而非现实绕过」——对目录前缀来说它已经是现实绕过了。

### 3. `policy.py` 在 `reject` 时也退出 0

`decide()` 只可能返回 `promote` / `revise` / `reject`（`policy.py:209-221`），而 `policy.py:270` 写的是：

```python
return 0 if decision["decision"] in {"promote", "revise", "reject"} else 1
```

这是恒真分支，`policy.py` **永远退出 0**。任何 `policy.py ... && <下一步>` 的脚本都会在候选被判 `reject` 时继续往下走。

### 4. `artifacts` 检查在没有记录时报 PASS

`validate.py:1923-1925` 在 `records/` 不存在时直接返回空错误列表。AGENTS.md 把这个检查称作「接受产出物前的编译步骤」，但它编译零个文件也报成功。更实际的形态是：保留 `records/` 目录、删掉底下所有记录子目录，8 个检查里 7 个通过（含 `artifacts` 和 `docs`），只有 `tests` 因为钉死的用例读了真实记录才红。`records/.DS_Store` 在盘时同样 `PASS artifacts`——这条你们半年前就自己记下来了，`examples/` walker 加了隐藏项过滤（`validate.py:1466`），`records/` walker 没加。

---

## 二、Agent loop / 编排：没有状态机，只有散文

这是架构上最根本的问题。整个 loop 的唯一结构化状态载体是 `records/plans/` 里那张 Markdown 表格（5 值状态枚举，`validate.py:559-668` 校验）。除此之外，brief、result、重试、失败全是对话里的自由文本。具体断点：

**worker result 和 review verdict 都没有 schema。** `schemas/` 下 9 个契约里没有这两个最核心的。`review.schema.json` 看着像，但它的 `required` 是 `review_id/target_project/source_revision/reviewed_docs`——那是外部文档二次评审的记录契约，不是开发线的评审结论。后果是：reviewer 返回 `decision: 看起来还行`，或者 worker 返回一段没有 `status` 的散文，**没有任何东西会发现**。14 条 hard boundary 里 11 条因此只能算 PROSE-ONLY。

**hard boundary 14（write_scope 按 diff 强制）在结构上跑不起来。** `contracts.md:24` 和 `SKILL.md:109` 都要求「记录委派时刻的 baseline revision」，但 `contracts.md:29-35` 的 brief 契约七个字段里**没有 baseline**，result 契约里也没有 revision。而唯一的执行工具 `check-write-scope.sh` 把 baseline 当 `argv[1]` 收——没有任何契约字段承载它，也没有任何 hook 或 CI 调用它。它自己的注释还承认最后要人工「减去已知的 dirty 路径」。`SKILL.md:109` 称它为 "the enforcement"，实际上它从未运行过。

**plan task 和 worker result 之间没有 join key。** plan 任务有 `T01…` ID（`validate.py:585-594` 校验唯一性），brief 和 result 都不带 `task_id`。所以「证据回写」列没有可自动化的来源，并行批次的结果也无法机械映射回行。

**执行期没有角色拥有 plan 状态列的写权限。** `plan-architect.md:37` 描述了最小 diff 回写机制，但 `roles.md:71` 说它「只写计划」；三个实现角色（`backend-engineer.md:18`、`frontend-engineer.md:18`、`bug-fixer.md:19`）都被禁止写 `records/`。`SKILL.md` 第 5~8 步没有一句让 supervisor 更新看板。于是 `SKILL.md:148` 宣称的「会话中途死亡后从 plan 恢复」所依赖的那个恢复点，**在文档化的路径上没有人写**——同一句话后半段其实已经自己承认了，真正的恢复机制是重新 diff 工作区。

**失败语义只有一层。** `contracts.md:90-94` 覆盖了预算耗尽（报 `partial`），但 subagent 崩溃、宿主工具报错、worker 返回空、`maxTurns` 触发都没有规则；没有超时值，没有升级路径，也不区分「worker 挂了」和「worker 的改动没过检查」。而 `reviewer`/`evaluator`/`release-governor` 的返回枚举里根本没有 `partial` 值——一个被截断的评审**没有合法方式报告自己被截断了**。

另外 `execution-coordinator` 这个「未来角色」被四处点名为持久队列、租约、重试、可恢复并行批次的归属者。这是诚实披露，但它同时意味着重试语义既是「现在生效的散文规则」又是「未来角色的职责」，两种说法并存。

---

## 三、RAG / 记忆层：只有写入端，没有读取端

这不是「RAG 做得不够好」，是**没有检索机制**。

写入端：10 个 schema 共 46KB，561 行记录 README，`bug-recorder.md` 68 行写作纪律，validate.py 强制 schema、状态迁移、日期目录与 `recorded_at` 一致、文件名 slug、ID 唯一、时间戳顺序、固定中文标题字面量、正文路径可解析、外部片段内嵌。

读取端：6 个 README 里 12 条 shell 单行命令。而且——

**唯一的聚合/排序面（`validate.py report` 和 `recurrence`）对所有需要它的角色都不可达。** 我逐个确认了 frontmatter：

```
feedback-analyst     tools: Read, Glob, Grep
evaluator            tools: Read, Glob, Grep
release-governor     tools: Read, Glob, Grep
bug-investigator     tools: Read, Glob, Grep
reviewer             tools: Read, Glob, Grep
technical-director   tools: Read, Glob, Grep
```

六个只读角色全都没有 Bash，跑不了 `python3 tools/lab/validate.py report`。检索退化成「让模型自己 Grep 一下 records/」。

**任务开始时没有任何机制触发读取历史记录。** `SKILL.md:103` 的 Intake 要求读仓库指令、当前 diff、架构、测试，并用 `git fetch`+`log` 校准状态——一次都没提 `records/`。全仓库唯一的指针是 `AGENTS.md:60` 一句「记录在 records/ 下，见 README」。

**recurrence 是手工维护的，只有 tier 是算出来的。** `recurrence_report()` 会比较 `agentflow_version` 与 `consolidated_in` 推导 `single/recurred/escalated`——这部分是真自动。但**类归属完全靠人工标注**：`validate.py:2178-2201` 只交叉检查那些**已经声明了** `class_id` 的记录，没有任何检查发现「这条记录本该属于某个类却没标」。现状是 9 条 bug 记录里 7 条共享 `error_kind: missing-constraint`、6 条共享 `attribution: workflow_policy`，而带 `class_id` 的只有 1 条。`escalated` 警报在人工先标类之前永远不可能触发。

而且没有任何角色负责回写 `consolidated_in`：13 步的 improve loop 在第 2 步读 ledger，第 11~13 步从不更新它。唯一的 ledger 两天 11 个版本没被碰过。

**规模上限很近。** 我量了一下：9 条 bug 记录约 15.5k tokens，9 个 episode 约 8.4k，全量扫一遍约 24k（还没算解释它们所需的 6 个 README 再 7k）。按 5 天产出 18 件（≈3.6/天）的实际速率，线性扫描在 **17~20 条记录**左右撞墙，也就是**一到两周的余量**。没有索引、没有排序、没有去重、没有压缩层——`grep -c "difflib\|similar\|cluster\|dedup\|fuzzy" tools/lab/validate.py` 是 0。

`docs/self-improvement-design.md:3` 自己写着「持久检索…尚未实现」，`docs/next-session-handoff.md:451` 里「Episode Store + SQLite FTS5」还是 `[ ]`。所以这是**已知的缺口**，不是我发现的——但它的紧迫程度被低估了：余量是周级的，不是月级的。

---

## 四、以模治模：闭环一次都没跑通，且契约自相矛盾

这是最严重的一块，因为它是整个项目的立论。

**`records/improvement/` 里只有一个 `README.md`。** 零候选、零评测结果、零对照、零 release 记录。`grep -rl '"rollback_to"'` 只命中 schema 自己。`mock/` 有 bugs/episodes/plans/reviews，独独没有 `improvement/`。**全仓库没有任何一个完整证据链实例，连 demo 都没有。** 而 `records/README.md:18-21` 断言「改进控制面的产出物交接**已实现**…不再是计划，是已校验树的一部分」——它是一棵已校验的 *schema* 树，居无一人。

**方法级 release 记录在结构上写不出来。** 我验证过：

```
release-record.schema.json:
  top-level allowed keys: [approvals, baseline_results, candidate, candidate_results,
                           decision, evaluation_result, rollback_to, rollout, schema_version]
  additionalProperties: False
$ grep -rn "measurement" schemas/ skills/improve/references/*.json
(无输出)
```

而 `skills/improve/SKILL.md:63` 强制要求「release 记录必须写明 `measurement: none (method-level…)`」。schema 里**没有 `measurement` 这个键**且 `additionalProperties: false`——遵守 SKILL 写出来的记录一定被 schema 拒绝。再加上 schema 要求完整的 `baseline_results`/`candidate_results`（含 sha256 和 8 个指标），而 0.5.x~0.7.x **每一个版本**实际都是 `measurement: none`。这就是 `records/improvement/releases/` 为什么是空的机械原因——不是没人写，是写不出合法的。

**0.7.1 的发布违反了它自己的晋级门。** `CHANGELOG.md:148-151` 原文：评估员裁定 `neutral`，release governor 返回 `promote`。对照三处：`release-record.schema.json` 的 `if decision == "promote"` 要求 `evaluation_result` 为 `const: "better"`；`policy.py:217-221` 里 `neutral` 确定性地导出 `revise`；`evaluator.md:18` 写着「neutral 不是改进」。一份合法的 0.7.1 release 记录**在结构上不可能存在**。这道门是在 CHANGELOG 散文里被满足的，而本该拦住它的那份产出物从未被写下——`validate.py artifacts` 报 PASS，因为没有东西可校验（见一·4）。

**度量效度：晋级证据由被测者自己上报。** `policy.py` 决策所用的 8 个指标全部来自 `adapter-case-result` JSON，只做 schema 形状校验（`host_adapter.py:463-479`）。`permission_violations` 是个 guardrail——它的取值方式是**问违规者本人「你违规了吗」**。只有 business 切片会用 grader 覆写 `accepted` 和 `escaped_defects`（`host_adapter.py:724-730`），`first_pass_review` 即使在那里也仍是自报；`evals/public` 一个都不覆写。

**答案在被测者的工作目录里。** `host_adapter.py:594-603` 用 `--plugin-dir <workspace>` 且 `cwd=workspace` 跑候选，而 workspace 是 `git worktree`（`isolation.py:104-120` 是 `--detach`，会 checkout 整棵树）。我确认过种子清单是被 git 跟踪的：

```
$ git ls-files evals/business/seeds/
evals/business/seeds/BT-001.seeds.json
evals/business/seeds/BT-002.seeds.json
evals/business/seeds/BT-003.seeds.json
```

`protected-paths.txt` 防的是**改** `evals/`，防不住**读**。BT-001 的三个锚点是 `"静默重投"`、`"≤30"`、`"§12.4"`，阈值 `min_seed_recall: 0.5`——有自身 cwd 读权限的模型读一个文件就是 100% 召回。

**而且不读答案也能刷分。** `seed_grader.py:80-90` 的匹配是：

```python
text = f"{finding['issue']}\n{finding['evidence']}"
return any(anchor in text for anchor in seed["strategy"]["anchors"])
```

裸子串，无词边界，不校验 issue 是否正确，不限 evidence 长度。加上 `paths_match` 是**双向**后缀匹配（`is_suffix(seed, finding) or is_suffix(finding, seed)`），猜对 basename 就够。于是**把整篇文档粘进 `evidence`**，该文档里所有种下的锚点按构造必然逐字命中——召回 1.0、`escaped_defects` 0、`accepted` true，实际评审量为零。而未匹配的 finding 明确「不计惩罚」（`seed_grader.py:17-18`），所以**刷 finding 没有任何代价，全套方案里唯一的反作弊压力（precision）被显式放弃了**。`evals/business/README.md:93` 把这称为「已知局限，不视为评分缺陷」——结合上面两条，这不是局限，而是种子机制存在理由的消失。

**闭环出口也是断的。** `grep -rn "canary\|monitor" tools/lab/*.py` = 0，`SKILL.md` 第 13 步的「晋级后监控 + 阈值失败回滚」没有任何实现。`policy.py` 可以返回 promote/reject/revise，**永远不会返回 `rollback`**，尽管 `rollback` 在 release schema 和 governor 契约的枚举里。18 个评测用例 `holdout` 全是 `false`，0 个留出集，违反 `evidence-and-release.md:91`。9 个 episode 的 `outcome` **9/9 都是 `accepted`**，`source_type` 里 0 个 `test`、0 个 `incident`、0 个 `rollback`——正是 `evidence-and-release.md:13` 明令禁止的生存者偏差。

---

## 五、冗余与漂移

**五份文档互相重述同一套规则**：`SKILL.md`(156 行) / `contracts.md`(122) / `roles.md`(90) / `docs/agent-roles.md`(409，一份没有标注的中文全镜像) / 14 个 `agents/*.md`(约 650 行)，再加 `AGENTS.md` 和 `README.md` 的部分副本。重复 3 次以上的规则族：「worker 摘要不等于验证」7 处、「浏览器自动化仅主对话」7 处、「作者不是验证者」7 处、「隐式行为检查」10 处、「预算纪律」11 处。

副本已经开始互相矛盾，这是漂移已经发生、不是风险：

| 已实现的漂移 | 证据 |
| --- | --- |
| 路由表首行说「单层小修 Supervisor 自己做」，13 行后的 Supervisor 段和 `SKILL.md:126-128` 说 supervisor 自己写的改动评审门**不可豁免** | `roles.md:12` vs `roles.md:25` vs `SKILL.md:128` |
| `docs/agent-roles.md:79` 把「可由 Supervisor 自检」放进 Reviewer 列，而 `SKILL.md:26` 明确 review 不可合并 | 中文镜像给出了英文原文禁止的授权 |
| 两个角色文件仍写「`records/` 归 Recorder 和 Plan Architect 所有」，而 0.7.0 起 test-planner/test-executor 也写 `records/tests/` | `bug-fixer.md:19`、`candidate-engineer.md:20` |
| `contracts.md:75-76` 给 worker result 加了 `cost`/`duration`，14 个角色文件无一提及 | 加进契约文档后没有传播 |
| `SKILL.md:15-16` 只绑定 10 个 agent id，漏了 `candidate-engineer`/`evaluator`/`feedback-analyst`/`release-governor`，而同一个 SKILL 加载的 `roles.md:21` 按名路由到这四个 | 按 SKILL 走的 agent 拿不到 id |

而 `validate.py docs` 抓不到上面任何一条。它只做 5 件事：agent 文件名与 frontmatter `name` 一致、`agentflow:<role>` 可解析、`schemas/*.schema.json` 路径存在、一个针对 2026-09-17 那次事故硬编码的两字面量 tripwire、以及中文镜像与 contracts 的**schema 文件名集合**相等。函数 docstring（`validate.py:2272`）声称它验证「中文镜像与英文契约保持章节对等」——代码并不做这件事。

**角色数量**：按能力（工具清单 × 只读性 × 相对作者的独立性）切，14 个角色实际是 5 类——带 shell 的写者、不带 shell 的记录写者、只读分析者、只读裁决者、不许改源码的 shell 执行者。`roles.md:53` 自己已经写出了收敛原则（「专项审计走同一个 reviewer 角色，配上对应清单的 brief，不需要独立角色」），然后**没有把它应用到** `bug-investigator`、`feedback-analyst`、`technical-director`、`release-governor`——这四个都是不到 100 词的 brief 变体。`evaluator` 与 `release-governor` 的职责分离更是纯 prompt 文本隔离，恰好撞上 hard boundary 7「不得仅凭 prompt 文本宣称隔离」。

**工具清单与正文不符**（举三个最实际的）：

- `reviewer` 是 `Read, Glob, Grep` + 禁 Bash，正文写「runs no commands」，但第 26、28 行要求「Inspect the actual diff」——没有 Bash 就没有 `git diff`，而 `SKILL.md` 第 8 步也没规定 supervisor 必须交付 diff 产出物。评审员的主要输入在交接契约里是缺失的。
- `plan-architect` 禁 `Edit` 只给 `Write`，正文第 37 行却要求「只回写状态与证据两列（最小 diff），不得重写已完成行」——最小 diff 列编辑正是 `Edit` 的语义，`Write` 只能整文件覆写。`test-planner`、`bug-recorder`（还要求「把被拒记录移到 archive/」，既无 Bash 也无删除能力）同类。
- `test-executor` 持有 Bash 和 Write，却是唯一既没有「不得改写 git 历史」行、也没有「本角色不再向下委派」条款的写者角色。

---

## 六、仓库卫生

**版本状态：HEAD 是 0.7.1，工作树声称 0.7.4。** 0.7.2/0.7.3/0.7.4 只存在于未提交的工作树（18 改 + 4 个未跟踪 episode），而已安装快照 `agentflow/0.7.4/` 是**从未提交的树构建的**。`validate.py` 注意不到这一点——`manifests` 只比较五份 manifest 彼此，从不与 git 比。其中包括对受保护路径 `skills/improve/references/episode.schema.json` 的 +41 行改动，也只在工作树里。

**四处 0.6.0 陈述**：`README.md:23`、`README.md:116`、`docs/host-native-plugin-design.md:3`、`docs/self-improvement-design.md:3`。后两处在 `PLAN-BUSINESS-EVAL-001.md:95` 里被记为「已关闭（2026-09-17 已更新为 0.6.0）」——修复方式是钉死版本号而非自维护，所以接下来四次 bump 全部重新失效。

**README 的角色/schema 清单是 0.6.0 时代的**：列 8 个实现角色（实际 14），漏掉整个 0.7.0 测试切片（`test-planner`/`test-executor`/`records/tests/` 两个 schema 在 README 里一次都没出现）；列 7 个 schema（实际 9，漏 6 个）。

**一个断链，两处都错**：`SKILL.md:99` 的 `[records/reviews/README.md](../../../records/reviews/README.md)`。我验证过，从源码树和已安装快照解析都失败，正确深度是 `../../`（同深度的 `skills/improve/SKILL.md:27` 用的就是正确层数）。

**1.6MB 会话 HTML 会随插件一起装到用户机上。** 三个 `command-code-session-*.html` 和三份根目录评审报告都在 `~/.zcode/cli/plugins/cache/agentflow-local/agentflow/0.7.4/` 里——本地目录型 marketplace 快照的是**目录**，不是 `git ls-files`。`.gitignore` 让它们从 `git status` 消失，但不阻止它们被打包。这直接违反 `SKILL.md:155`「只在用户要求持久产出物时创建仓库追踪文件」。三份报告还把同一个优先级阶梯重复了三遍，且它们的 `path:line` 引用已经失效（`CONSOLIDATED-REVIEW-REPORT.md:39` 引 `validate.py:1899`，实际在 `:2765`）——而该报告自己的判词是「留过时报告在工作区比没有报告更危险」，实际采取的动作却是把它们提交了。

**`docs/next-session-handoff.md` 是全树最具误导性的文件**：539 行，日期 2026-09-17，内容停在 0.5.2；`:7` 以「当前机器」标注了一个不存在的目录 `/Users/hang/Documents/myProject/agentflow`；`:483` 的启动提示词里写着错误的 remote（`my-agents.git`，实际是 `agentflows.git`）；`:510` 说「本机尚无可被默认检查发现的安装源」，与同文件 `:11` 和 `validate.py installed` 的 PASS 直接矛盾。而它正是这份文档指定给下一个会话读的第二份材料。

**`docs/iteration-log.md`**：12 处「当前源码」标记（至多一处可能为真，实际全假），停在 0.6.0 缺 5 个版本，每条的证据入口都指向同版本的 CHANGELOG 条目——按自己的引用列，它是 CHANGELOG 的派生索引，而 CHANGELOG 已经吸收了「为什么」这个角色。

**`evals/public/inputs/AF-009.md:3`** 要求 agent 把 bug 记录写到 `records/bugs/BUG-PARSER-001.json`——这个 JSON 契约早已被 Markdown+frontmatter 取代。一个照 brief 执行的模型会产出 validator 拒绝的产出物，而用例判它合规。更麻烦的是 `evals/` 在门内，改它属于 gate change。

**CI 与文档声称的强制范围不符**：`.github/workflows/validate.yml` 只有两步（`validate.py all` + 重复一次 unittest），**`isolation.py check-diff` 不在 CI 里**，`.git/hooks/` 只有 `*.sample`。也就是说整个门的执行完全依赖「人记得跑」。而且 remote 上 HEAD 还是 0.7.1，0.7.2~0.7.4 从未推送，这个 workflow 从没评估过当前代码。

**`mock/` 零校验**：`grep -c 'mock' tools/lab/validate.py` = 0。`mock/README.md:3` 写「不进仓库」，但它在 `8199a69` 就被提交了；`mock/records/plans/PLAN-DEMO-SHARE-001.md` 与 `examples/plans/` 下同名文件逐字节相同，0.7.2 的改动要手工改两遍。

---

## 七、如果只修五件事

1. **把 `isolation.py check-diff` 放进 CI，并把 `.github/` 纳入 protected-paths**；给那三个 git 调用加 `-z`；让 `check_diff` 在自己的 `ROOT` 落在 `--candidate` 之内时拒绝运行（现在候选可以同时提供检查器和清单）。没有这一步，门的其余部分都不成立。
2. **测试门改成读 skip 数与实际通过数，而不是 `Ran N`**；`validate.py:1923` 的空 `records/` 改为报错；`policy.py:270` 改成 `reject` 非零退出。
3. **把 `evals/business/seeds/` 移出候选 worktree**（或者不要把 worktree 同时当 `--plugin-dir` 和 `cwd`）；给 `seed_grader` 加一个 precision 项或 evidence 长度上限，让「粘贴全文」不再是取胜策略。至少让一个决策指标来自观测而非自报——`permission_violations` 最便宜（解析宿主拒绝输出）。在此之前，`promote` 的含义只是「候选自称变好了」。
4. **给 worker result 和 review verdict 各写一个 schema，并在 brief 契约里加 `baseline_revision` 和 `task_id`。** 这三个字段一加，hard boundary 14 的执行脚本才第一次具备可运行条件，plan 看板的证据回写也才有自动化来源。
5. **收敛文档面**：把 `docs/agent-roles.md` 明确标成镜像并加真正的章节对等检查（现在那个检查只比 schema 文件名集合）；删掉 `next-session-handoff.md` 和 `iteration-log.md` 或把它们降级为历史归档；把版本号从散文里拿掉、改成引用 manifest；`git rm` 三份根目录报告和三个 HTML，并把打包面从「拷目录」改成「按清单拷」。

最后提一句方法论上的观察：这个项目在**为自己的每一次失败增加一条散文规则**这件事上非常勤奋（14 条 hard boundary、判据定义、一次性 tripwire），但把规则变成检查的转化率很低——今天这份报告里的每一个发现都与 `validate.py all` 的 8×PASS、`validate.py docs` 的 PASS、`validate.py installed` 的 PASS 以及绿色 CI 共存。而仓库自己的信条是「无法复现的检查等于没跑」。按同样的标准，**无法被检查的规则等于没写**——这正是当前 Agentflow 最大的结构性问题，而不是任何单个 bug。

---

## 附录 A · 第 2 轮工具返回：`Read` 读取 `skills/agentflow/SKILL.md` 的完整原文（cat -n 格式，156 行）

```text
     1	---
     2	name: agentflow
     3	description: Use for cross-layer features, architecture changes, parallel investigation, delegated implementation, automated testing of user-visible features, or work that benefits from an explicit review gate; skip trivial single-step work where delegation would add overhead. Applies the Agentflow method with the host's own agents: supervisor, frontend/backend engineers, technical director, independent review, and test design/execution roles.
     4	---
     5	
     6	# Agentflow
     7	
     8	Apply the Agentflow development method with the current host's built-in agents, authentication, tools, permissions, and conversation history.
     9	
    10	Do not invoke or require the standalone `agentflow` CLI, its providers, its TUI, an Agentflow API key, or an Agentflow MCP server. This skill is the workflow. The host is the runtime.
    11	
    12	## Bind to the host
    13	
    14	- In **Codex**, use native subagents. Give each subagent one role and one task brief. Use the main task as the supervisor.
    15	- In **Claude Code**, prefer the plugin agents `agentflow:frontend-engineer`, `agentflow:backend-engineer`, `agentflow:technical-director`, `agentflow:reviewer`, `agentflow:bug-investigator`, `agentflow:bug-fixer`, `agentflow:bug-recorder`, `agentflow:plan-architect`, `agentflow:test-planner`, and `agentflow:test-executor` when those roles fit the task. Use the main conversation as the supervisor.
    16	- In **ZCode**, prefer the plugin agents `agentflow:frontend-engineer`, `agentflow:backend-engineer`, `agentflow:technical-director`, `agentflow:reviewer`, `agentflow:bug-investigator`, `agentflow:bug-fixer`, `agentflow:bug-recorder`, `agentflow:plan-architect`, `agentflow:test-planner`, and `agentflow:test-executor`. Use the main conversation as the supervisor. ZCode loads these from the installed plugin snapshot, so a role change in the source tree takes effect only after the plugin is reinstalled — run `python3 tools/lab/validate.py installed` to see whether the installed copy still matches the source.
    17	- In another Agent Skills compatible host, use its built-in delegation mechanism. If none exists, execute the same phases sequentially and state that independent execution was unavailable.
    18	
    19	Read [role profiles](references/roles.md) before assigning work and [contracts](references/contracts.md) before delegating implementation or review. The [hard boundaries](references/contracts.md#hard-boundaries) hold for every delegation in both workflows; check them before accepting any deliverable.
    20	
    21	For a material, uncertain, recurring, cross-layer, or high-risk bug, use the full bounded
    22	sequence `bug-investigator` → `bug-fixer` → `reviewer` → `bug-recorder`. The investigator
    23	establishes a reproducible symptom and attribution, the fixer changes code only in an assigned
    24	candidate workspace, the reviewer checks the fix, and the recorder writes the accepted bug
    25	record after verification. For a small, low-risk bug with an already verified reproduction,
    26	the supervisor may combine the investigator or recorder step, but must preserve the same
    27	diagnosis, regression, review, and state evidence. Never let the fixer approve or close its own
    28	bug.
    29	
    30	For a planning task, run the needed frontend and backend specialists in parallel, send their
    31	outputs and the technical director's interface decision to `plan-architect`, and have it
    32	write the final plan under an explicit `records/plans/` path. Plan Architect only writes the plan; the
    33	supervisor decides whether it is approved, assigns execution, integrates results, and owns the
    34	final stop or rollback decision. A future `execution-coordinator` may handle durable queues,
    35	leases, dependencies, retries, and resumable parallel batches, but it is not a current role.
    36	The plan must carry the progress board and task table (per-task status, dependencies, evidence
    37	write-back), the interfaces and shared mechanisms it passes through, its review gates, and the
    38	release order with rollback points — shape defined in records/plans/README.md, machine-checked. A plan is an execution contract, not an approval to change code. For a material
    39	feature the plan carries the design-completeness artifacts from
    40	[contracts](references/contracts.md): critical-path timing (step table as baseline), an
    41	exception matrix per critical path, and a release order paired with rollback points.
    42	
    43	## Automated testing
    44	
    45	When the user asks for automated testing of a user-visible feature — or a plan carries a
    46	test-design task — run the testing chain. `test-planner` writes the case library at an explicit
    47	`records/tests/<project>-<feature-slug>/` path: levels smoke / e2e / api / boundary, step tables
    48	whose assertions are observable (element text, navigation, whether a network request fires),
    49	boundary coverage with uncovered classes declared, and `## 流程疑点` for behaviors the spec does
    50	not define (contract: `records/tests/README.md`). `test-executor` runs it: scripted automation
    51	first (Playwright or the project's own e2e suite, headless), API cases via commands, and
    52	host-browser UI steps performed by the supervisor in the main conversation from the executor's
    53	step script — browser automation is main-conversation-only on Claude Code and ZCode — returning
    54	raw evidence (screenshots, DOM text, network log) that the executor judges. Run the smoke set
    55	first and stop on a smoke failure instead of running the full set against a broken build. Each
    56	round lands as one `run-*.md` record with per-case results, evidence, and summary counts.
    57	Failed cases carry
    58	reproduction-ready findings and become bug records through the standard chain (attribution per
    59	the records rules); flow-reasonableness findings go to the reviewer as the *Flow reasonableness
    60	(test evidence)* specialist mode. The run record's raw evidence is the review gate's
    61	end-to-end-path evidence (step 8). Credentials are supplied per session and injected at runtime —
    62	never persisted into records, scripts, or logs. Prefer a project-level Playwright setup for
    63	repeatability; the supervisor-driven route is the fallback, not the goal.
    64	
    65	## Second-pass review of external documents
    66	
    67	When the user asks for a review of documents authored under another system's rules (for example
    68	a proposal/spec/design/plan produced inside a business repository's own template system), run
    69	the independent reviewer role against those documents and land the evidence here:
    70	
    71	1. Locate or create the feature-anchored directory `records/reviews/<project>-<feature-slug>/`.
    72	   The directory is anchored on the reviewed feature, not the date: the same feature may be
    73	   reviewed repeatedly (today, tomorrow, after fixes) and every round is one more
    74	   `review-<YYYY-MM-DD>-<NNN>.md` file in the same directory. Archive **verbatim copies** of
    75	   the round's documents under `archive/<date>-<NNN>/` — one snapshot subdirectory per round so
    76	   same-named documents never collide — and record the target repository's current commit as
    77	   `source_revision`: later edits there must not retroactively change what was reviewed. A
    78	   re-review focuses on the delta since the previous round's review_id.
    79	2. The reviewer applies this repo's review contract to the snapshot: the reviewer profile's
    80	   check protocol, the **document mode** matching each reviewed document's type (proposal/PRD,
    81	   spec, design — every item needs a citation to the original text), and, where relevant, the
    82	   design-completeness artifacts above.
    83	3. File every finding as a bug record under `records/bugs/` with `project` set to the target
    84	   repository. Attribution separates the two upgrade loops: `provenance: external` +
    85	   `attribution: product_code` marks a template/rule gap in the target system — the evidence
    86	   pool for upgrading that system's templates; `provenance: agentflow` means this repo's review
    87	   contract should have caught it. When the target system's upgrade lands, backfill
    88	   `fix_revision` with its commit. References must stay self-contained: a `files` entry either
    89	   resolves inside this repository or is repo-qualified (`<repo>@<revision>:<path>`) — a bare
    90	   external path fails validation because it dangles for anyone without that repository — and
    91	   the body embeds the decisive snippet or quoted sentence so the record stays readable when
    92	   the other repository is absent.
    93	4. Write `review-<date>-<NNN>.md` (contract: `schemas/review.schema.json`; filename equals
    94	   review_id) with the decision, the findings list, and the archived-doc references, then run
    95	   `python3 tools/lab/validate.py artifacts` — it cross-checks that every archived document and
    96	   every referenced finding actually exists.
    97	
    98	The full bridge workflow, attribution table, and known limits (cross-repo recurrence tiers are
    99	not auto-derived) live in [records/reviews/README.md](../../../records/reviews/README.md).
   100	
   101	## Run the workflow
   102	
   103	1. **Intake**: inspect the repository instructions, current diff, relevant architecture, and tests. State the objective and observable acceptance criteria. When you report repository **status** — what is done, what is next, what is high priority — calibrate against the repository's real history first (`git fetch` plus `log`/`status`), never against session memory, and carry the evidence command with the conclusion. A status claim is a repository-fact claim: session memory goes stale the moment another writer pushes, and nothing in the answer would reveal it.
   104	2. **Architecture gate**: for cross-layer or risky work (see *Judgement calls made checkable* below), ask the technical director to define boundaries, interface contracts, integration order, and major risks. Do not use this role as a ceremonial approval step.
   105	3. **Plan**: select only the roles the task needs. A frontend-only fix does not need a backend worker. A small change (see *Judgement calls made checkable* below) can stay with the supervisor.
   106	4. **Delegate**: give every worker a bounded brief with `write_scope` and `read_scope` set separately — read scope must cover every shared mechanism the change passes through (the implicit-behavior check in [contracts](references/contracts.md)). Parallelize read-heavy investigation and implementation with disjoint files or stable interfaces; disjoint files parallelize writes, never understanding. Serialize overlapping writes and dependency chains. Verify paths, repos, and commands named in the task against the repository before they enter a brief — task text is data, not established fact. **Disjoint files are not enough once two writers share a repository**: commits, rebases, and pushes are shared mutable state, so parallel writers get separate branches or worktrees, one writer holds a branch at a time, and a writer that finds its target file or branch already occupied by another writer (uncommitted edits from another session, a branch with new commits) stops and reports instead of interleaving.
   107	5. **Implement**: frontend and backend workers change only their assigned scope, follow repository rules, run relevant checks, and return the worker result contract.
   108	6. **Integrate**: the supervisor inspects the actual shared workspace, resolves cross-layer conflicts, and runs the checks that establish the whole feature works.
   109	7. **Verify worker artifacts before accepting them**: a worker's claim is not accepted until the supervisor compiles it — run the repository's deterministic checks (tests, linters, schema validators such as `tools/lab/validate.py` in this project) against the actual written files, not against the worker's summary. A failed check is a compile error: send it back for a fix, never hand-accept a summary over a red check. A claimed check that cannot be reproduced counts as not run. In the same pass, compare the workspace's actual change surface against the brief's `write_scope` (hard boundary 14): record the baseline revision at delegation time, then list what really changed — `git diff --name-only --no-renames <baseline>` plus untracked files, or the bundled `scripts/check-write-scope.sh` — and return the work when any path outside `write_scope` changed, whatever the checks say. Artifact-ownership tables are declared intent; this comparison is the enforcement.
   110	8. **Review gate**: after material changes, assign an independent reviewer. When the supervisor wrote part of the change itself, this gate is mandatory and cannot be waived — the author is not the verifier. The reviewer authors the exact check commands and expected outcomes and works from raw output; the supervisor may execute them, but may not substitute them. The reviewer reports `approved`, `changes_requested`, or `blocked` with concrete evidence and does not silently repair the code it judges. Exercise the end-to-end path a real user would take before this gate closes — a gate that approves a build whose primary user-visible path has never executed once is reviewing code, not behavior. Any later change that affects user-visible behavior re-opens the gate, whoever authored it; a re-review may be scoped to the delta since the last reviewed revision. When the host's browser automation is main-conversation-only (subagents cannot load it), the supervisor owns that browser pass itself — no delegated reviewer can run it — and hands the reviewer the raw output (screenshots, DOM or text assertions) as the check evidence for user-visible frontend claims.
   111	9. **Repair once**: when review requests changes, assign one focused repair round and review again. Keep the loop bounded.
   112	10. **Decide**: the supervisor produces the final decision record from [contracts](references/contracts.md), including implementation, verification, review outcome, and remaining risks. The record carries the claims ledger: every user-visible claim mapped to the check that would fail if it were false; a claim covered only by reading code is `unverified`, and any unverified user-visible claim makes the outcome `partial`, not `complete`. When the outcome may feed the improvement loop, capture the decision record as an episode under `records/episodes/<YYYY-MM-DD>/<EP-id>.json` before the session ends (contract: `skills/improve/references/episode.schema.json` — reuse it, never a parallel carrier), because once the conversation is gone the episode is unrecoverable and nobody will remember to collect it. Since 0.7.2 this is mandatory for every **material** change — anything that opened the independent review gate — not only improvement-loop candidates. Each reviewer round is recorded in the episode's `review_roundtrips` field (at, reviewer, decision, finding, resolution): the rounds that returned `changes_requested`, what the disagreement was, and how it was resolved — so mid-flow review divergence stays auditable after the conversation is gone, not only the final verdict.
   113	
   114	## Judgement calls made checkable
   115	
   116	Three phrases decide whether a gate applies. They are defined here so that the same situation
   117	gets the same treatment every time, and so that a call can be checked afterwards instead of
   118	argued about. Apply them in this order: they qualify or trigger gates; they never waive the
   119	rule that the author is not the verifier.
   120	
   121	- **Small change** — needs no worker roles and no architecture gate. It qualifies only when
   122	  **all** of these hold: one file and one layer; no contract changes (schema, API shape, CLI
   123	  flag, config key, record format); no shared cross-cutting mechanism touched (interceptor,
   124	  global error handler, route guard, listener, middleware); the deterministic checks that
   125	  cover it pass on the actual files; and the defect it fixes has a verified reproduction.
   126	  Anything else is **material**. This class does not touch the review gate: when the
   127	  supervisor wrote part of a change — small or material — the independent reviewer gate for it
   128	  is mandatory and cannot be waived (hard boundary 1).
   129	- **Risky work** — the architecture gate (technical director) is mandatory when **any** of
   130	  these hold: an interface or contract consumed by another layer or repository changes;
   131	  persistence or the data model changes; a security, authorization, or permissions boundary
   132	  changes; the sequencing, timing, or idempotency of a shared flow changes; or the change is
   133	  costly to reverse (a migration, a release order, a published schema or record format).
   134	- **The same cause** — two consecutive failures have the same cause when the same check fails
   135	  with the same normalized signature: the same check id or command, and the same error text or
   136	  `error_kind` after timestamps and absolute paths are stripped. When the signatures differ but
   137	  you suspect one root cause, state the assumption you are about to change and record what you
   138	  compared; do not silently retry.
   139	
   140	## Recover from stalled work
   141	
   142	Before treating a failing check as a regression, run the same check against the pre-change revision — a worktree of the parent commit is enough. If it fails there too, the failure is environmental (tooling, network, host, gateway): fix the environment or report it, and do not loop workers on it. Only a check that passes on the baseline and fails on the change is evidence of a regression.
   143	
   144	Treat two consecutive failures with the same cause (see *Judgement calls made checkable*) as a signal to stop repeating the attempt. Re-read the code and error evidence, restate the assumption that failed, and choose a different approach or a smaller task boundary.
   145	
   146	If a repair/review loop still cannot pass after the bounded retry, report the blocker with evidence and the smallest decision needed from the user. Do not keep agents cycling on unchanged inputs.
   147	
   148	A session that dies mid-orchestration resumes from the versioned plan under `records/plans/` (a Markdown board: each task row carries its status and evidence, so the state is re-derivable), not from memory: re-derive each work package's state from the workspace (diff against the delegation baseline, checks, review decisions) before re-briefing, and treat a package without observed evidence as not started. Durable queues, leases, and resumable parallel batches are the future `execution-coordinator` role; today the plan file plus the repository state is the only checkpoint.
   149	
   150	## Preserve control and traceability
   151	
   152	- Follow the host's permission and sandbox rules. Delegation never expands authority.
   153	- Do not push, deploy, publish, delete remote data, or message third parties without authorization already present in the conversation. **Integrating others' work or rewriting history is the same class of act**: `git merge`, `rebase`, `cherry-pick`, or pulling remote changes into a shared branch requires per-instance user authorization, not an inference from an earlier instruction. When a push is rejected, the default is a read-only report — `git fetch` plus `log`/`diff` showing which commits and files the remote added and where they overlap — and the user chooses the integration method; do not pick merge or rebase, resolve conflicts, and push on your own.
   154	- Use stable task names and carry the parent objective into every delegated brief.
   155	- Record decisions and evidence, not hidden chain-of-thought. Use the host's task and conversation history as the default trace. Create repository trace files only when the user asks for durable project artifacts.
   156	- Keep the supervisor useful: it should resolve conflicts and make a final call, not merely summarize worker messages.
```

---

## 附录 B · 第 2 轮工具返回：`Read` 读取 `README.md` 的完整原文（cat -n 格式，120 行）

```text
     1	# Agentflow
     2	
     3	Agentflow is a host-native multi-agent development workflow for Codex, Claude Code, ZCode,
     4	and compatible Agent Skills hosts. The host owns models, authentication, tools,
     5	permissions, conversation history, and agent execution. Agentflow supplies role
     6	contracts, delegation rules, independent review, and a governed improvement method.
     7	
     8	It does not invoke or require the standalone `agentflow` CLI.
     9	
    10	## Use
    11	
    12	- Codex: install the Plugin and invoke `$agentflow`. Select **Agentflow Improve** or
    13	  invoke `$improve` only when improving Agentflow itself.
    14	- Claude Code: start development with `claude --plugin-dir .`, then invoke
    15	  `/agentflow:agentflow` or `/agentflow:improve`.
    16	- ZCode: install the plugin from the local marketplace in [`marketplace.json`](marketplace.json)
    17	  (it points at this directory). Skills resolve through `.zcode/skills/` symlinks, but **agents
    18	  load from the installed snapshot** — after changing `agents/*.md`, refresh the marketplace and
    19	  reinstall, then confirm with `python3 tools/lab/validate.py installed`.
    20	
    21	## Current maturity
    22	
    23	Version `0.6.0` provides:
    24	
    25	- a shared development Skill;
    26	- frontend, backend, technical-director, reviewer, bug-investigator, bug-fixer,
    27	  bug-recorder, and plan-architect roles;
    28	- a feedback-analysis, candidate, evaluation, and release-governance workflow;
    29	- machine-readable bug, plan, episode, candidate, evaluation-case, evaluation-result,
    30	  and release-record schemas;
    31	- a business-task measurement slice (`evals/business/`) scored deterministically against
    32	  seed defects;
    33	- Codex, Claude Code, ZCode, and portable Agent Plugin manifests.
    34	
    35	Implementation roles declare an explicit tool allowlist (`Read, Glob, Grep, Write, Edit, Bash`), so
    36	a worker does not receive the host's native delegation or MCP tools through that allowlist. Bash
    37	still follows the host's sandbox and may have capabilities that are not implied by the tool names;
    38	network isolation must be verified from the host, not inferred from this list.
    39	`bug-recorder` writes only the explicitly assigned sanitized record under `records/bugs/`, and
    40	`plan-architect` writes only the explicitly assigned plan under `records/plans/`. Neither role can
    41	close a bug, authorize code execution, or publish a Plugin. The supervisor must inspect the
    42	resulting paths and verification evidence because the host does not enforce arbitrary path
    43	constraints on the `Write` tool; see [AGENTS.md](AGENTS.md).
    44	
    45	The candidate gate surface — the evaluator and governor role files, the evaluation suite, the
    46	measurement path, the release rules, the record schemas under `schemas/`, the pinned regression
    47	test, and the list itself — is declared once in [`protected-paths.txt`](protected-paths.txt).
    48	`isolation.py check-diff` rejects a candidate diff that touches it. Run it from the trusted source
    49	checkout with the frozen parent revision:
    50	
    51	```sh
    52	python3 tools/lab/isolation.py check-diff \
    53	  --candidate <tree> \
    54	  --base <frozen-parent-revision>
    55	```
    56	
    57	`validate.py protected` keeps the list from being quietly trimmed, and `validate.py all` now also
    58	requires the five manifests to agree on name and version and runs the repository's regression tests.
    59	
    60	The three Bug roles are selectable capabilities, not a mandatory ceremony for every issue.
    61	Use the full Investigator → Fixer → Reviewer → Recorder flow for material, uncertain,
    62	recurring, cross-layer, or high-risk bugs. The supervisor may combine diagnosis or recording
    63	for a small low-risk bug with a known reproduction, while keeping the same evidence gates.
    64	Plan Architect writes the plan; Supervisor authorizes and coordinates execution. A separate
    65	Execution Coordinator is reserved for a future durable control plane.
    66	
    67	The improvement workflow is a governed skeleton. Cross-session telemetry, persistent
    68	retrieval, a private holdout service, canary rollout, and automatic rollback are not
    69	implemented yet. Human approval is the default release boundary.
    70	
    71	The workspace contains the P0 implementation slice: Bug Record and Plan contracts, sanitized
    72	positive/negative examples, fifteen public evaluation cases, a dependency-free contract
    73	validator (including the installed-snapshot drift check), an explicit host-adapter result protocol,
    74	isolation checks, a fail-closed Codex/Claude host-adapter wrapper, and a deterministic policy
    75	evaluator. Real model dogfood, private holdout service, and installation/release switch
    76	are still intentionally pending.
    77	
    78	## Business evaluation slice
    79	
    80	`evals/business/` is the measurement surface for method-level changes — the ones that alter how
    81	roles behave inside business repositories and have no regression signal in `evals/public/`. Three
    82	cases ship now: `BT-001` seed-defect document review, `BT-002` internal contradiction, `BT-003`
    83	cross-document consistency; `evals/business/README.md` documents the layout. A case points at a
    84	pinned, read-only snapshot of a business repository, asks the agent to review a set of documents,
    85	and expects one findings artifact per repetition at
    86	`findings/<case_id>/rep-<n>/findings.json` in the workspace.
    87	
    88	Scoring is deterministic and offline. Each case ships an abstracted seed list whose entries carry
    89	the document, a category, and one or more literal anchors; a seed counts as a hit when a finding
    90	names that document and its text contains an anchor. The grader reports `hits`, `missed`, and
    91	`unmatched`; `accepted` becomes "hit rate at or above the case threshold" and `escaped_defects`
    92	becomes the missed-seed count. Unmatched findings — real defects outside the seed list — are
    93	recorded, not penalized. An unknown match strategy, or a missing or unparsable findings artifact,
    94	fails closed instead of scoring zero.
    95	
    96	Two parameters carry the snapshot contract. `eval_runner.py --business-root` names the fourth
    97	isolation position (the pinned snapshot root); the adapter rejects a business request whose roots
    98	are missing or nested. `host_adapter.py --seed-patch` names the patch the snapshot was built from:
    99	a real business run requires it, checks the snapshot HEAD against the case `target_pin`, requires
   100	the patch to be cleanly reversible, and re-checks the snapshot file set and the `git diff` digest after every host call.
   101	Business requests must use a `workspace-write` permission profile because the findings artifact is
   102	written into the workspace; the snapshot itself is made read-only when seeded, and only the
   103	sanitized briefs and abstracted seed lists are public.
   104	
   105	The slice is instrument-ready, not measured: no baseline/candidate comparison has been produced
   106	yet. The smoke run is blocked on the trusted endpoint, the measured permission profile, and the
   107	snapshot placement decisions, so a method-level change without a matching business case still
   108	releases as `measurement: none`.
   109	
   110	See [`docs/agent-product-boundary.md`](docs/agent-product-boundary.md),
   111	[`docs/agent-roles.md`](docs/agent-roles.md),
   112	[`docs/self-improvement-design.md`](docs/self-improvement-design.md), and
   113	[`docs/host-platform-facts.md`](docs/host-platform-facts.md) for observed host constraints, and
   114	[`docs/iteration-log.md`](docs/iteration-log.md) for why each version changed.
   115	
   116	The source checkout currently declares version `0.6.0`. This is not by itself proof that a host is
   117	running that version: ZCode loads installed snapshots and Codex may load a separate plugin cache.
   118	Before dogfood, compare the actual host snapshot with `python3 tools/lab/validate.py installed
   119	--path <installed-plugin-root>` (or the host-specific default) and record the result. Do not switch
   120	an installation until the first human-gated dogfood run uses a verified model endpoint.
```

---

*（记录完。本文件为逐字转写的对话记录；除「收录说明」中声明的宿主注入上下文外，对话全部内容均在内。文件本身未加入 git 跟踪，是否保留/提交由用户决定。）*

























