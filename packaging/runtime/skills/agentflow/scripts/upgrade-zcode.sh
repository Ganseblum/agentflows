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

# --- 4. 重建生成树 + 跑门（装之前必须绿）-------------------------------------
say ""
say "[1/5] 重建 packaging/runtime"
if [ "$DRY_RUN" = "1" ]; then say "  (dry-run 跳过)"; else python3 "$REPO_ROOT/packaging/build_runtime.py"; fi

say ""
say "[2/5] 跑门槛（schema / examples / artifacts / protected / manifests / docs / tests / doc_chain / doc_chain_live / decision_gate）"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  if ! python3 "$REPO_ROOT/tools/lab/validate.py" all; then
    fail "门禁红——先在仓内修好再发版，不要带着红门装进宿主"
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
say ""
say "[3/5] 刷新市场 ${MARKETPLACE}（CLI 会真正重新拉取）"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  zcode_run plugins marketplace update "$MARKETPLACE" || fail "刷新市场失败"
fi

# --- 7. 校验市场里看到的就是目标版本 ----------------------------------------
say ""
say "[4/5] 确认市场已看到 $TARGET_VERSION"
if [ "$DRY_RUN" = "1" ]; then
  say "  (dry-run 跳过)"
else
  MARKET_VERSION="$(zcode_run plugins marketplace list 2>/dev/null | python3 -c '
import re, sys
text = sys.stdin.read()
for line in text.splitlines():
    if line.startswith("- ") and "agentflow" in line:
        m = re.search(r":\s*(\d+)\s+plugins", line)
        if m:
            print("listed")
            break
' || true)"
  # 市场清单只报插件数，不报版本；版本以克隆里的 manifest 为准。
  CLONE_MANIFEST="$HOME/.zcode/cli/plugins/marketplaces/$MARKETPLACE/marketplace.json"
  if [ -f "$CLONE_MANIFEST" ]; then
    CLONE_VERSION="$(python3 - "$CLONE_MANIFEST" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
plugins = d.get("plugins") or []
print(plugins[0].get("version", "?") if plugins else "?")
PY
)"
    say "  克隆里的市场版本：$CLONE_VERSION"
    if [ "$CLONE_VERSION" != "$TARGET_VERSION" ]; then
      fail "克隆仍是 ${CLONE_VERSION}，不是 ${TARGET_VERSION} —— 市场刷新没有生效（检查远端是否已推送）"
    fi
  else
    say "  注意：找不到克隆清单 ${CLONE_MANIFEST}，跳过该步核对"
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
