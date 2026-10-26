#!/usr/bin/env bash
# install-hooks.sh — 把仓内的 git hook 装进 .git/hooks（幂等，可重复跑）。
#
# 为什么 hook 本体放在 skills/agentflow/scripts/ 而不直接写 .git/hooks：.git/ 不受版本控制，
# 换台机器、重新 clone、或别人接手时 hook 就没了，而且没人知道它曾经存在。把本体纳进仓库、
# 只把 .git/hooks/ 当成软链入口，规则才有版本、有评审、可回滚。
#
# 用法：
#   bash skills/agentflow/scripts/install-hooks.sh            # 安装
#   bash skills/agentflow/scripts/install-hooks.sh --check    # 只检查已安装且未漂移
#   bash skills/agentflow/scripts/install-hooks.sh --remove    # 卸载
#
# 退出状态：0 = 已就绪；1 = 安装失败或漂移；2 = 用法错误。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK_SRC="skills/agentflow/scripts/pre-push.sh"
HOOK_DST=".git/hooks/pre-push"
MODE="install"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --remove) MODE="remove"; shift ;;
    -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "error: 未知参数 $1" >&2; exit 2 ;;
  esac
done

cd "$REPO_ROOT"

[ -d .git ] || { echo "FAIL: 本目录不是 git 工作树的根（没有 .git）" >&2; exit 1; }
[ -f "$HOOK_SRC" ] || { echo "FAIL: 找不到 ${HOOK_SRC}" >&2; exit 1; }

case "$MODE" in
  install)
    chmod +x "$HOOK_SRC"
    mkdir -p .git/hooks
    if [ -e "$HOOK_DST" ] && [ ! -L "$HOOK_DST" ]; then
      echo "注意：已存在非软链的 ${HOOK_DST}，先备份为 ${HOOK_DST}.bak"
      mv "$HOOK_DST" "${HOOK_DST}.bak"
    fi
    ln -sfn "../../${HOOK_SRC}" "$HOOK_DST"
    echo "已安装：${HOOK_DST} → ../../${HOOK_SRC}"
    echo "验证：git push 前会自动跑十项门禁。用 --no-verify 可临时跳过。"
    ;;
  check)
    if [ ! -L "$HOOK_DST" ]; then
      echo "FAIL: ${HOOK_DST} 不存在或不是软链（hook 未安装）" >&2
      exit 1
    fi
    TARGET="$(readlink "$HOOK_DST")"
    if [ "$TARGET" != "../../${HOOK_SRC}" ]; then
      echo "FAIL: ${HOOK_DST} 指向 ${TARGET}，期望 ../../${HOOK_SRC}（已漂移）" >&2
      exit 1
    fi
    [ -x "$HOOK_SRC" ] || { echo "FAIL: ${HOOK_SRC} 没有可执行位" >&2; exit 1; }
    echo "OK: hook 已安装且未漂移（${HOOK_DST} → ${TARGET}）"
    ;;
  remove)
    if [ -L "$HOOK_DST" ]; then
      rm "$HOOK_DST"
      echo "已移除：${HOOK_DST}"
    else
      echo "无需移除：${HOOK_DST} 不存在或不是软链"
    fi
    ;;
esac
