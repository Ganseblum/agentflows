#!/usr/bin/env bash
# publish.sh — 校验发布内容、按需重建与提交、推送并按配置本地安装。
#
# 为什么不是一个 git hook：git 没有 post-push 钩子。pre-push 在推送**之前**触发，那时
# upstream 还没更新，ZCode 那段（要求 HEAD == upstream）必然失败；post-commit 则在每次
# 提交时触发，与「发版」不是同一个动作。所以做成一一条显式命令——你敲它，就是这次发版的
# 授权；不敲，什么都不会发生。这与仓库「推送与发布需当次授权」的纪律一致。
#
# 用法：
#   bash skills/agentflow/scripts/publish.sh                 # 树干净时：直接推送并双端安装
#   bash skills/agentflow/scripts/publish.sh -m "解决什么"    # 提交已明确暂存的改动及生成包再发
#   bash skills/agentflow/scripts/publish.sh --bump patch -m "..."   # 顺便把补丁号 +1
#   bash skills/agentflow/scripts/publish.sh --no-push       # 不推送；有 -m 时仍可提交本地版
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
PYTHON_BIN="${AGENTFLOW_PYTHON:-python3}"

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

"$PYTHON_BIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "需要 Python 3.10+，可通过 AGENTFLOW_PYTHON 指定解释器"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
say "仓：$REPO_ROOT"
say "分支：$BRANCH"

# --- 1. 分支与远端前提 -------------------------------------------------------
case "$BRANCH" in
  HEAD) fail "当前为 detached HEAD。请在明确的发布分支上运行" ;;
  release_sim_*|release_pre_*|release_prod_*)
    fail "当前在 ${BRANCH}（测试/回归/正式分支）。代码改动只允许落在 feature-* 或主干，先切分支" ;;
esac
if [ "$DO_PUSH" = "1" ]; then
  git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1 \
    || fail "分支 ${BRANCH} 没有 upstream；先 git push -u origin ${BRANCH}"
fi

# 发布只接受工作区干净的提交，或明确已暂存的一批。
# 检查在 bump、重建或提交之前，避免把其他会话的文件带入发布。
if ! git diff --quiet --; then
  git diff --name-only --
  fail "存在未暂存改动；只接受已明确暂存的发布内容"
fi
UNTRACKED="$(git ls-files --others --exclude-standard)"
if [ -n "$UNTRACKED" ]; then
  say "$UNTRACKED"
  fail "存在未跟踪文件；发布入口不会自动将其加入提交"
fi
if [ -z "$MESSAGE" ] && { [ -n "$BUMP" ] || ! git diff --cached --quiet --; }; then
  fail "版本变更或已暂存的内容需用 -m 给出提交说明"
fi
step "发布预检"
"$PYTHON_BIN" -B skills/agentflow/scripts/check_skill_refs.py --source-only

# --- 2. bump 版本（必须在重建之前）-------------------------------------------
CURRENT_VERSION="$("$PYTHON_BIN" -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' plugin.json)"
say "当前版本：$CURRENT_VERSION"

NEW_VERSION="$CURRENT_VERSION"
if [ -n "$BUMP" ]; then
  case "$BUMP" in
    patch|minor|major) ;;
    *) fail "--bump 只接受 patch|minor|major" ;;
  esac
  NEW_VERSION="$("$PYTHON_BIN" - "$CURRENT_VERSION" "$BUMP" <<'PY'
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
fi
if ! "$PYTHON_BIN" - "$NEW_VERSION" <<'PY'
from pathlib import Path
import re
import sys
version = re.escape(sys.argv[1])
raise SystemExit(0 if re.search(r"^## " + version + r"(?:\s|$)",
                               Path("CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE) else 1)
PY
then
  fail "CHANGELOG.md 缺少 ${NEW_VERSION} 的版本节"
fi

if [ -n "$BUMP" ]; then
  step "1/6 bump 版本 ${CURRENT_VERSION} → ${NEW_VERSION}"
  if [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] 将改写六份 manifest"
  else
    "$PYTHON_BIN" - "$NEW_VERSION" <<'PY'
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
  fi
else
  step "1/6 版本未变（${CURRENT_VERSION}）"
  say "  提示：ZCode 按版本号建缓存目录，版本不变时可能复用旧缓存。发版通常应带 --bump patch。"
fi

step "2/6 核对发布载荷"
if [ -n "$MESSAGE" ]; then
  run "$PYTHON_BIN" -B packaging/build_runtime.py
fi
if [ "$DRY_RUN" = "1" ] && [ -n "$MESSAGE" ]; then
  say "  [dry-run] 重建后核对所有清单、链接和载荷"
else
  "$PYTHON_BIN" -B skills/agentflow/scripts/check_skill_refs.py
  "$PYTHON_BIN" -B skills/agentflow/scripts/workflow.py install-verify \
    --expected-tree packaging/runtime --installed . --codex-source
fi

step "3/6 提交"
if [ -n "$MESSAGE" ]; then
  if [ -n "$BUMP" ]; then
    run git add -- plugin.json marketplace.json .zcode-plugin/plugin.json \
      .claude-plugin/plugin.json .codex-plugin/plugin.json .qoder-plugin/plugin.json
  fi
  run git add -- packaging/runtime
  if [ "$DRY_RUN" = "1" ] || ! git diff --cached --quiet --; then
    run git commit -m "$MESSAGE"
  fi
fi

# --- 6. 推送 ----------------------------------------------------------------
step "4/6 推送"
if [ "$DO_PUSH" = "0" ]; then
  say "  --no-push：跳过"
elif [ "$DRY_RUN" = "1" ]; then
  say "  [dry-run] git push origin ${BRANCH}"
else
  git push origin "$BRANCH"
  say "  已推送 $(git rev-parse --short HEAD) → origin/${BRANCH}"
fi

# --- 7. 双端安装（有就装，没就跳过）-----------------------------------------
if [ "$SKIP_CODEX" = "1" ]; then
  step "5/6 Codex"
  say "  --skip-codex：跳过"
elif ! command -v codex >/dev/null 2>&1; then
  step "5/6 Codex"
  say "  跳过：本机没有 codex CLI"
else
  step "5/6 装进 Codex"
  if [ "$DRY_RUN" = "1" ]; then
    say "  [dry-run] bash skills/agentflow/scripts/upgrade-codex.sh"
  else
    bash skills/agentflow/scripts/upgrade-codex.sh
  fi
fi

if [ "$SKIP_ZCODE" = "1" ]; then
  step "6/6 ZCode"
  say "  --skip-zcode：跳过"
elif [ ! -f "/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs" ] && ! command -v zcode >/dev/null 2>&1; then
  step "6/6 ZCode"
  say "  跳过：本机没有 ZCode CLI"
elif [ "$DO_PUSH" = "0" ]; then
  step "6/6 ZCode"
  say "  跳过：--no-push 时本地 HEAD ≠ upstream，ZCode 那段（要求两者一致）会拒绝。"
  say "        要装 ZCode，去掉 --no-push。"
elif [ "$DRY_RUN" = "1" ]; then
  step "6/6 ZCode"
  say "  [dry-run] bash skills/agentflow/scripts/upgrade-zcode.sh"
else
  step "6/6 装进 ZCode"
  bash skills/agentflow/scripts/upgrade-zcode.sh
fi

step "完成"
say "版本 ${NEW_VERSION}"
say "提醒："
say "  - ZCode 需要重启才加载新快照；Codex 通常重开会话即可。"
