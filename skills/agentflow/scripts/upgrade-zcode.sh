#!/usr/bin/env bash
# upgrade-zcode.sh — 把本仓的新版本装进 ZCode，并验证装进去的确实是你刚发的那个版本。
#
# 为什么需要这个脚本：ZCode 的图形界面「刷新该市场」对 git 源不可靠（2026-10-26 实测：
# 两次点击都返回 OK，但克隆目录的 mtime 与版本号一次都没变）。而 ZCode 自带的 CLI
# （`zcode.cjs plugins marketplace update` / `plugins update`）实测会真正重新拉取并原地升级
# 到新版本目录，因此升级走 CLI，不走界面。
#
# 用法：
#   bash skills/agentflow/scripts/upgrade-zcode.sh                 # 升级到本仓当前版本
#   bash skills/agentflow/scripts/upgrade-zcode.sh --dry-run       # 只报告计划，不做改动
#   bash skills/agentflow/scripts/upgrade-zcode.sh --marketplace <id> --plugin <name>
#
# 前置：本仓工作树已经提交并推送（脚本不推送，也不替你决定推送）。
#
# 退出状态：0 = 已升级并验证通过；1 = 某一步失败（原始输出随行打印）；2 = 用法错误。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MARKETPLACE="agentflow-local"
PLUGIN="agentflow"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --marketplace) MARKETPLACE="${2:?--marketplace 需要一个值}"; shift 2 ;;
    --plugin) PLUGIN="${2:?--plugin 需要一个值}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "error: 未知参数 $1" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# --- 1. 定位 ZCode CLI -------------------------------------------------------
# 优先用已装应用内的实现；它由宿主随应用更新，比任何缓存副本都权威。
ZCODE_CLI=""
for candidate in \
  "/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs" \
  "$HOME/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs"
do
  if [ -f "$candidate" ]; then ZCODE_CLI="$candidate"; break; fi
done
if [ -z "$ZCODE_CLI" ]; then
  if command -v zcode >/dev/null 2>&1; then ZCODE_CLI=""; else
    fail "找不到 ZCode CLI：既没有 /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs，也没有 PATH 里的 zcode"
  fi
fi

zcode_run() {
  if [ -n "$ZCODE_CLI" ]; then node "$ZCODE_CLI" "$@"; else zcode "$@"; fi
}

# --- 2. 本仓版本（唯一真源：plugin.json）-------------------------------------
TARGET_VERSION="$(python3 - "$REPO_ROOT/plugin.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])
PY
)"
[ -n "$TARGET_VERSION" ] || fail "读不出本仓 plugin.json 的 version"

say "本仓版本：${TARGET_VERSION}"
say "目标市场：$MARKETPLACE    插件：$PLUGIN"

# --- 3. 确认工作树已提交（未提交的改动装不进任何地方）------------------------
if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  say "注意：工作树有未提交改动。打包树取自工作树，装进去的内容会与 git 记录不一致。"
  say "      （脚本不阻止，但你要知道装的是什么。）"
fi

# --- 3b. 强制本仓与远端一致 ------------------------------------------------
# 2026-10-26 的真实事故：只 bump 了 manifest 没重建 runtime 就发布，远端于是出现
# plugin.json=0.17.2 而 packaging/runtime/plugin.json=0.17.1；git marketplace 装的正是
# runtime 那棵树，结果市场显示新版、装进去的仍是旧版。下面三项检查就是拦这一类。
if [ "$DRY_RUN" != "1" ]; then
  if [ -n "$(git -C "$REPO_ROOT" status --porcelain -- packaging plugin.json marketplace.json .zcode-plugin .claude-plugin .codex-plugin .qoder-plugin)" ]; then
    fail "发布面有未提交改动——先 rebuild、提交并推送，再运行本脚本（git marketplace 装的是远端那棵树，不是你的工作树）"
  fi
  if ! git -C "$REPO_ROOT" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    fail "当前分支没有 upstream——无法确认远端已是同一提交"
  fi
  HEAD_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
  UPSTREAM_SHA="$(git -C "$REPO_ROOT" rev-parse '@{u}')"
  if [ "$HEAD_SHA" != "$UPSTREAM_SHA" ]; then
    fail "本地 HEAD ($(printf '%.7s' "$HEAD_SHA")) 与 upstream ($(printf '%.7s' "$UPSTREAM_SHA")) 不同——先 push"
  fi
  say "本仓 HEAD 与 upstream 一致：$(printf '%.7s' "$HEAD_SHA")"
fi

# --- 4. 重建生成树 + 跑门（装之前必须绿）-------------------------------------
# lint 需要 dev 依赖（ruff/mypy）。缺它们时门会 FAIL，但那属于「未运行」而不是失败——
# 仓库自己的判据是「无法复现的检查记为未运行，绝不计为通过」。这里把 lint 单独拆出来跑，
# 缺依赖时明确报「未运行」，其余十项照常判红。带 lint 的解释器由 AGENTFLOW_LINT_PYTHON 指定。
say ""
say "[1/5] 重建 packaging/runtime"
if [ "$DRY_RUN" = "1" ]; then say "  (dry-run 跳过)"; else python3 "$REPO_ROOT/packaging/build_runtime.py"; fi

say ""
say "[2/5] 跑门槛（必绿项从 validate.py --list 解析；lint 缺 dev 依赖时记为未运行）"
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
      fail "门禁红（$target）——先在仓内修好再发版，不要带着红门装进宿主"
    fi
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
    "$LINT_PYTHON" "$REPO_ROOT/tools/lab/validate.py" lint || fail "门禁红（lint）"
  else
    say "SKIP lint（未运行：当前解释器没有 ruff/mypy；用 AGENTFLOW_LINT_PYTHON 指向装好 dev 依赖的解释器可实跑）"
  fi
fi

# --- 5. 确认生成树里的版本与目标一致（防止忘了 bump）-------------------------
RUNTIME_VERSION="$(python3 - "$REPO_ROOT/packaging/runtime/plugin.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])
PY
)"
if [ "$RUNTIME_VERSION" != "$TARGET_VERSION" ]; then
  fail "生成树版本 $RUNTIME_VERSION ≠ 源版本 $TARGET_VERSION —— 重新跑 build_runtime.py"
fi
say "  生成树版本一致：${RUNTIME_VERSION}"

# --- 6. 刷新市场（这一步会重新 git clone）------------------------------------
# 每次刷新前先确认远端已经能读到目标版本：刚 push 完时 GitHub 侧可能还没同步，此时刷新
# 拿到的是旧提交，装上去就是旧版本。重试而不是立刻判失败——这是发布竞态，不是版本错了。
clone_version() {
  local manifest="$HOME/.zcode/cli/plugins/marketplaces/$MARKETPLACE/marketplace.json"
  [ -f "$manifest" ] || { printf '?'; return; }
  python3 - "$manifest" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
plugins = d.get("plugins") or []
print(plugins[0].get("version", "?") if plugins else "?")
PY
}

say ""
say "[3/5] 刷新市场 ${MARKETPLACE}（CLI 会真正重新拉取）"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  attempt=1
  max_attempts=5
  while :; do
    zcode_run plugins marketplace update "$MARKETPLACE" || fail "刷新市场失败"
    seen="$(clone_version)"
    if [ "$seen" = "$TARGET_VERSION" ]; then
      say "  克隆已更新到 ${seen}（第 ${attempt} 次刷新）"
      break
    fi
    if [ "$attempt" -ge "$max_attempts" ]; then
      say "  克隆仍是 ${seen}，不是 ${TARGET_VERSION}"
      fail "刷新 ${max_attempts} 次仍未拿到 ${TARGET_VERSION}。常见原因：远端尚未推送该版本，或 GitHub 侧缓存未同步。先确认 \`git ls-remote origin main\` 已含该提交，再重跑。"
    fi
    say "  克隆仍是 ${seen}（第 ${attempt} 次），远端可能尚未同步，10 秒后重试"
    sleep 10
    attempt=$((attempt + 1))
  done
fi

# --- 7. 校验市场里看到的就是目标版本 ----------------------------------------
say ""
say "[4/5] 确认市场已看到 ${TARGET_VERSION}"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  CLONE_VERSION="$(clone_version)"
  say "  克隆里的市场版本：${CLONE_VERSION}"
  if [ "$CLONE_VERSION" != "$TARGET_VERSION" ]; then
    fail "克隆仍是 ${CLONE_VERSION}，不是 ${TARGET_VERSION}"
  fi
fi

# --- 8. 升级插件 -------------------------------------------------------------
say ""
say "[5/5] 升级 ${PLUGIN}@${MARKETPLACE}"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
  say ""
  say "dry-run 结束：未做任何改动。"
  exit 0
fi
zcode_run plugins update "$PLUGIN@$MARKETPLACE" || fail "升级失败"

# --- 9. 验证装进去的版本 -----------------------------------------------------
INSTALLED="$HOME/.zcode/cli/plugins/cache/$MARKETPLACE/$PLUGIN/$TARGET_VERSION"
if [ ! -d "$INSTALLED" ]; then
  fail "升级后找不到安装目录 $INSTALLED"
fi

CHECKER="$INSTALLED/tools/lab/doc_chain.py"
if [ -f "$CHECKER" ]; then
  say ""
  say "装后检查器自报版本：$(python3 "$CHECKER" --version)"
fi

say ""
say "与源面逐文件比对："
python3 "$REPO_ROOT/tools/lab/validate.py" installed --path "$INSTALLED" || fail "安装面与源面不一致"

say ""
say "完成：ZCode 已装 ${TARGET_VERSION}。重启 ZCode 后生效（角色从快照加载）。"
