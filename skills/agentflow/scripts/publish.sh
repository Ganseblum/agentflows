#!/usr/bin/env bash
# publish.sh — 一次发版：bump → 重建 → 跑门 → 提交 → 推送 → 装进 Codex → 装进 ZCode。
#
# 为什么不是一个 git hook：git 没有 post-push 钩子。pre-push 在推送**之前**触发，那时
# upstream 还没更新，ZCode 那段（要求 HEAD == upstream）必然失败；post-commit 则在每次
# 提交时触发，与「发版」不是同一个动作。所以做成一一条显式命令——你敲它，就是这次发版的
# 授权；不敲，什么都不会发生。这与仓库「推送与发布需当次授权」的纪律一致。
#
# 用法：
#   bash skills/agentflow/scripts/publish.sh                 # 树干净时：直接推送并双端安装
#   bash skills/agentflow/scripts/publish.sh -m "解决什么"    # 有改动时：提交这批改动再发
#   bash skills/agentflow/scripts/publish.sh --bump patch -m "..."   # 顺便把补丁号 +1
#   bash skills/agentflow/scripts/publish.sh --no-push       # 只本地安装，不推远端
#   bash skills/agentflow/scripts/publish.sh --dry-run       # 只报告将要做什么
#
# 顺序是刻意的：**先 bump、再重建**。反过来会造出「manifest 已是新版、生成树还是旧版」
# 的远端状态，而 git marketplace 装的正是生成树（2026-10-26 的真实事故）。
#
# 退出状态：0 = 全部完成；1 = 某步失败（后续步骤不再执行）；2 = 用法错误。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MESSAGE=""
BUMP=""
DO_PUSH=1
DRY_RUN=0
SKIP_CODEX=0
SKIP_ZCODE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    -m|--message) MESSAGE="${2:?--message 需要一个值}"; shift 2 ;;
    --bump) BUMP="${2:?--bump 需要 patch|minor|major}"; shift 2 ;;
    --no-push) DO_PUSH=0; shift ;;
    --skip-codex) SKIP_CODEX=1; shift ;;
    --skip-zcode) SKIP_ZCODE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,24p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "error: 未知参数 $1" >&2; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
step() { printf '\n=== %s ===\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
run()  { if [ "$DRY_RUN" = "1" ]; then say "  [dry-run] $*"; else "$@"; fi; }

cd "$REPO_ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
say "仓：$REPO_ROOT"
say "分支：$BRANCH"

# --- 1. 分支与远端前提 -------------------------------------------------------
case "$BRANCH" in
  release_sim_*|release_pre_*|release_prod_*)
    fail "当前在 ${BRANCH}（测试/回归/正式分支）。代码改动只允许落在 feature-* 或主干，先切分支" ;;
esac
if [ "$DO_PUSH" = "1" ]; then
  git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1 \
    || fail "分支 ${BRANCH} 没有 upstream；先 git push -u origin ${BRANCH}"
fi

# --- 2. bump 版本（必须在重建之前）-------------------------------------------
CURRENT_VERSION="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' plugin.json)"
say "当前版本：$CURRENT_VERSION"

if [ -n "$BUMP" ]; then
  case "$BUMP" in
    patch|minor|major) ;;
    *) fail "--bump 只接受 patch|minor|major" ;;
  esac
  NEW_VERSION="$(python3 - "$CURRENT_VERSION" "$BUMP" <<'PY'
import sys
current, part = sys.argv[1], sys.argv[2]
major, minor, patch = (int(x) for x in current.split(".")[:3])
if part == "major":
    major, minor, patch = major + 1, 0, 0
elif part == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1
print(f"{major}.{minor}.{patch}")
PY
)"
  step "1/7 bump 版本 ${CURRENT_VERSION} → ${NEW_VERSION}"
  if [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] 将改写六份 manifest"
  else
    python3 - "$NEW_VERSION" <<'PY'
import json, pathlib, sys
new = sys.argv[1]
targets = [
    ("plugin.json", None),
    ("marketplace.json", ("plugins", 0, "version")),
    (".zcode-plugin/plugin.json", None),
    (".claude-plugin/plugin.json", None),
    (".codex-plugin/plugin.json", None),
    (".qoder-plugin/plugin.json", None),
]
for name, pointer in targets:
    path = pathlib.Path(name)
    document = json.loads(path.read_text(encoding="utf-8"))
    if pointer:
        document[pointer[0]][pointer[1]][pointer[2]] = new
    else:
        document["version"] = new
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("  六份 manifest 已更新")
PY
    CURRENT_VERSION="$NEW_VERSION"
  fi
else
  step "1/7 版本未变（${CURRENT_VERSION}）"
  say "  提示：ZCode 按版本号建缓存目录，版本不变时可能复用旧缓存。发版通常应带 --bump patch。"
fi

# --- 3. 重建生成树（bump 之后）----------------------------------------------
step "2/7 重建 packaging/runtime"
run python3 packaging/build_runtime.py

# --- 4. 跑门 ----------------------------------------------------------------
step "3/7 跑门槛（必绿项从 validate.py --list 解析；lint 缺 dev 依赖时记为未运行）"
if [ "$DRY_RUN" = "1" ]; then
  say "  [dry-run] 跳过"
else
  # 门清单单源：解析 `validate.py --list`，排除 all/installed/lint/report/recurrence
  # （2026-10-26 审计 G24）。
  REQUIRED_KINDS="all installed lint report recurrence"
  TARGETS="$(python3 tools/lab/validate.py --list \
    | grep -vE 'all runs [0-9]+ checks' \
    | grep -vxE 'all|installed|lint|report|recurrence' \
    | tr '\n' ' ')"
  for target in $TARGETS; do
    python3 tools/lab/validate.py "$target" || fail "门禁红（${target}）——修好再发版"
  done
  # 解释器优先级与 pre-push.sh / validate.py 保持一致：显式环境变量 > 仓内 .venv > python3。
# 探测只扩大「找得到工具」的路径；缺 ruff/mypy 仍按未运行处理（2026-10-28 评测整改批 G4）。
if [ -n "${AGENTFLOW_LINT_PYTHON:-}" ]; then
  LINT_PYTHON="$AGENTFLOW_LINT_PYTHON"
elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  LINT_PYTHON="$REPO_ROOT/.venv/bin/python"
else
  LINT_PYTHON="python3"
fi
  if "$LINT_PYTHON" -c 'import ruff, mypy' >/dev/null 2>&1; then
    "$LINT_PYTHON" tools/lab/validate.py lint || fail "门禁红（lint）"
  else
    say "SKIP lint（未运行：没有 ruff/mypy；用 AGENTFLOW_LINT_PYTHON 指定装好 dev 依赖的解释器）"
  fi
fi

# --- 5. 提交 ----------------------------------------------------------------
step "4/7 提交"
DIRTY="$(git status --porcelain)"
if [ -z "$DIRTY" ]; then
  say "  工作树干净，无内容可提交"
else
  if [ -z "$MESSAGE" ]; then
    say "  待提交改动："
    printf '%s\n' "$DIRTY" | head -20 | sed 's/^/        /'
    if [ "$DRY_RUN" = "1" ]; then
      say "  [dry-run] 真实运行时会要求 -m \"...\" 才能继续"
    else
      fail "工作树有改动但没给 -m 提交说明。加 -m \"一句话说清改了什么\" 后再跑"
    fi
  elif [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] git add -A && git commit -m \"${MESSAGE}\""
  else
    git add -A
    git commit -q -m "$MESSAGE"
    say "  已提交：$(git log --oneline -1)"
  fi
fi

# --- 6. 推送 ----------------------------------------------------------------
step "5/7 推送"
if [ "$DO_PUSH" = "0" ]; then
  say "  --no-push：跳过"
elif [ "$DRY_RUN" = "1" ]; then
  say "  [dry-run] git push origin ${BRANCH}"
else
  git push origin "$BRANCH"
  say "  已推送 $(git rev-parse --short HEAD) → origin/${BRANCH}"
fi

# --- 7. 双端安装 ------------------------------------------------------------
if [ "$SKIP_CODEX" = "1" ]; then
  step "6/7 Codex"
  say "  --skip-codex：跳过"
else
  step "6/7 装进 Codex"
  if [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] bash skills/agentflow/scripts/upgrade-codex.sh"
  else
    bash skills/agentflow/scripts/upgrade-codex.sh
  fi
fi

if [ "$SKIP_ZCODE" = "1" ]; then
  step "7/7 ZCode"
  say "  --skip-zcode：跳过"
else
  step "7/7 装进 ZCode"
  if [ "$DO_PUSH" = "0" ]; then
    say "  跳过：--no-push 时本地 HEAD ≠ upstream，ZCode 那段（要求两者一致）会拒绝。"
    say "        要装 ZCode，去掉 --no-push。"
  elif [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] bash skills/agentflow/scripts/upgrade-zcode.sh"
  else
    bash skills/agentflow/scripts/upgrade-zcode.sh
  fi
fi

step "完成"
say "版本 ${CURRENT_VERSION}"
say "提醒："
say "  - CHANGELOG 不会自动写；发版前手动补一条（本脚本不猜你改了什么）。"
say "  - ZCode 需要重启才加载新快照；Codex 通常重开会话即可。"
