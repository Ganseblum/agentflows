#!/usr/bin/env bash
# upgrade-codex.sh — 把本仓当前版本装进 Codex，并验证装进去的确实是你刚发的那个版本。
#
# 与 ZCode 的差别（2026-10-26 实测）：
#   - Codex 的 personal 市场是一个本地 source：`~/.agents/plugins/marketplace.json` 里
#     `source: {source: "local", path: "./plugins/agentflow"}`，而 `~/plugins/agentflow`
#     是指向本仓工作树的符号链接。因此 Codex 读的**就是你的工作树**，没有远端克隆这一层，
#     也就不存在 ZCode 那种「刷新拿到旧提交」的竞态。
#   - 因此这里不需要推送、不需要刷市场；只需要 `codex plugin add agentflow@personal`，
#     它会把工作树快照进 `~/.codex/plugins/cache/personal/agentflow/<version>/`。
#   - 代价是**装进去的是工作树当时的样子**，包括未提交改动。所以本脚本先跑门，红则拒绝。
#
# 用法：
#   bash skills/agentflow/scripts/upgrade-codex.sh              # 装当前工作树并验证
#   bash skills/agentflow/scripts/upgrade-codex.sh --dry-run     # 只报告计划
#   bash skills/agentflow/scripts/upgrade-codex.sh --marketplace personal --plugin agentflow
#
# 退出状态：0 = 已安装并验证通过；1 = 某一步失败；2 = 用法错误。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MARKETPLACE="personal"
PLUGIN="agentflow"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --marketplace) MARKETPLACE="${2:?--marketplace 需要一个值}"; shift 2 ;;
    --plugin) PLUGIN="${2:?--plugin 需要一个值}"; shift 2 ;;
    -h|--help) sed -n '2,22p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "error: 未知参数 $1" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# --- 1. 前置：codex CLI ------------------------------------------------------
command -v codex >/dev/null 2>&1 || fail "找不到 codex CLI（PATH 里没有）；先安装 Codex CLI"

# --- 2. 本仓版本 -------------------------------------------------------------
TARGET_VERSION="$(python3 - "$REPO_ROOT/plugin.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])
PY
)"
[ -n "$TARGET_VERSION" ] || fail "读不出本仓 plugin.json 的 version"

say "本仓版本：${TARGET_VERSION}"
say "目标市场：${MARKETPLACE}    插件：${PLUGIN}"

# --- 3. 告知工作树状态（Codex 装的就是工作树，脏树会被一起装进去）------------
if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  say ""
  say "注意：工作树有未提交改动。Codex 的 personal 市场直接读工作树，"
  say "      这些改动会被一起装进缓存（与 git 记录不一致，但确实会生效）。"
  say "      未提交改动清单（前 10 条）："
  git -C "$REPO_ROOT" status --porcelain | head -10 | sed 's/^/        /'
fi

# --- 4. 重建生成树 + 门（装之前必须绿）---------------------------------------
say ""
say "[1/4] 重建 packaging/runtime"
if [ "$DRY_RUN" = "1" ]; then say "  (dry-run 跳过)"; else python3 "$REPO_ROOT/packaging/build_runtime.py"; fi

say ""
say "[2/4] 跑门槛（必绿项从 validate.py --list 解析；lint 缺 dev 依赖时记为未运行）"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  # 门清单单源：解析 `validate.py --list`，排除 all/installed/lint/report/recurrence
  # （2026-10-26 审计 G24）。
  REQUIRED_KINDS="all installed lint report recurrence"
  TARGETS="$(python3 "$REPO_ROOT/tools/lab/validate.py" --list \
    | grep -vE 'all runs [0-9]+ checks' \
    | grep -vxE 'all|installed|lint|report|recurrence' \
    | tr '
' ' ')"
  for target in $TARGETS; do
    if ! python3 "$REPO_ROOT/tools/lab/validate.py" "$target"; then
      fail "门禁红（${target}）——先在仓内修好再装进宿主"
    fi
  done
  LINT_PYTHON="${AGENTFLOW_LINT_PYTHON:-python3}"
  if "$LINT_PYTHON" -c 'import ruff, mypy' >/dev/null 2>&1; then
    "$LINT_PYTHON" "$REPO_ROOT/tools/lab/validate.py" lint || fail "门禁红（lint）"
  else
    say "SKIP lint（未运行：当前解释器没有 ruff/mypy；用 AGENTFLOW_LINT_PYTHON 指向装好 dev 依赖的解释器可实跑）"
  fi
fi

# --- 5. 确认 personal 市场指向本仓 ------------------------------------------
say ""
say "[3/4] 确认 ${MARKETPLACE} 市场指向本仓"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  MARKET_ROOT="$(codex plugin marketplace list 2>/dev/null | awk -v m="$MARKETPLACE" '$1==m {print $2}')"
  [ -n "$MARKET_ROOT" ] || fail "找不到市场 ${MARKETPLACE}；用 \`codex plugin marketplace list\` 查看可用市场"
  say "  市场根：${MARKET_ROOT}"
  LINK_PATH="$MARKET_ROOT/plugins/$PLUGIN"
  if [ -e "$LINK_PATH" ]; then
    REAL="$(cd "$LINK_PATH" && pwd -P)"
    say "  ${LINK_PATH} → ${REAL}"
    if [ "$REAL" != "$REPO_ROOT" ]; then
      say "  注意：该路径指向 ${REAL}，不是本仓 ${REPO_ROOT}。"
      say "        若要装本仓，先把链接指过来：ln -sfn ${REPO_ROOT} ${LINK_PATH}"
      fail "市场源不是本仓，拒绝继续（避免装错东西）"
    fi
  else
    fail "市场源 ${LINK_PATH} 不存在；先建立链接：ln -sfn ${REPO_ROOT} ${LINK_PATH}"
  fi
fi

# --- 6. 安装 -----------------------------------------------------------------
say ""
say "[4/4] 安装 ${PLUGIN}@${MARKETPLACE}"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
  say ""
  say "dry-run 结束：未做任何改动。"
  exit 0
fi
codex plugin add "${PLUGIN}@${MARKETPLACE}" || fail "安装失败"

# --- 7. 验证 -----------------------------------------------------------------
INSTALLED="$HOME/.codex/plugins/cache/$MARKETPLACE/$PLUGIN/$TARGET_VERSION"
[ -d "$INSTALLED" ] || fail "安装后找不到缓存目录 ${INSTALLED}"

CHECKER="$INSTALLED/tools/lab/doc_chain.py"
if [ -f "$CHECKER" ]; then
  say ""
  say "装后检查器自报版本：$(python3 "$CHECKER" --version)"
fi

say ""
say "与源面逐文件比对："
if ! python3 "$REPO_ROOT/tools/lab/validate.py" installed --path "$INSTALLED"; then
  fail "安装面与源面不一致（通常是工作树在安装期间被改动，重跑本脚本）"
fi

say ""
say "完成：Codex 已装 ${TARGET_VERSION}（缓存 ${INSTALLED}）。"
say "      Codex 每次会话读该缓存，通常无需重启；若行为未变，重开一个会话。"
