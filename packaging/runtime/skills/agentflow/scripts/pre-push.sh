#!/usr/bin/env bash
# pre-push.sh — 推送前的门禁。由 .git/hooks/pre-push 调用，也可手动跑（无 stdin 时校验 HEAD）。
#
# 只做一件事：在提交被推出去之前，把**将要被推送的那些提交**逐一检出到临时工作树，
# 对那棵树跑确定性检查。检查对象是提交树，不是当前工作区——工作区可以带着尚未提交的
# 修复，而"坏提交留在历史里、工作区已经改好"正是最容易蒙混过关的场景（2026-10-26
# L3 复核的副本实验已证实旧脚本会放行这种推送）。
# 不重建生成树、不装宿主——那些是发布动作，需要显式授权（见 publish.sh）。
#
# 边界：本 hook 防的是「本地漏跑门」，不防「提交同时改写门本身」——被推送的提交如果
# 改弱了 tools/lab/validate.py 或 gate/，结论就由该提交自己的门给出。防篡改由
# protected-paths.txt + `isolation.py check-diff` + 人工评审负责（审核 G08 有意未把
# check-diff 接进 push 路径）。
#
# 装法（一次性，见 install-hooks.sh）：
#   ln -sf ../../skills/agentflow/scripts/pre-push.sh .git/hooks/pre-push
# 临时跳过：
#   git push --no-verify
# 允许「未运行」放行（缺解释器、缺 lint 依赖、待推送提交无门禁时默认拦下；设了才放行）：
#   AGENTFLOW_PREPUSH_ALLOW_UNRUN=1 git push
#
# 退出状态：0 = 待推送提交全部通过，或显式允许未运行项，或本次推送不含任何待校验提交（纯删除）；
#           1 = 有红项或无法验证，拦下推送。

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "pre-push: 不在 git 仓库内，跳过" >&2
  exit 0
}
cd "$REPO_ROOT"

# 单一解释器：探测 ruff/mypy 与真正跑 lint 必须是同一个，否则探测结果不代表调用结果
# （旧脚本用 AGENTFLOW_LINT_PYTHON 探测、用写死的 python3 调用）。门的其余项也用它，
# gate 内部的子进程一律是 sys.executable，因此解释器在整条链上保持一致。
GATE_PYTHON="${AGENTFLOW_GATE_PYTHON:-${AGENTFLOW_LINT_PYTHON:-python3}}"
ALLOW_UNRUN="${AGENTFLOW_PREPUSH_ALLOW_UNRUN:-0}"
FAILED=""
UNRUN=""
CHECKED=""

if ! command -v "$GATE_PYTHON" >/dev/null 2>&1; then
  echo "pre-push: 找不到解释器 ${GATE_PYTHON}，无法验证待推送提交。" >&2
  echo "pre-push: 未运行不等于通过——默认拦下。装好 python3 或 dev 依赖后重试；" >&2
  echo "pre-push: 确需放行时显式设 AGENTFLOW_PREPUSH_ALLOW_UNRUN=1 或 git push --no-verify，" >&2
  echo "pre-push: 并在提交说明里写清为什么这次推送没有经过门禁。" >&2
  if [ "$ALLOW_UNRUN" = "1" ]; then
    echo "pre-push: AGENTFLOW_PREPUSH_ALLOW_UNRUN=1，放行（本次推送未经门禁验证）" >&2
    exit 0
  fi
  exit 1
fi

# --- 收集待推送提交 ---------------------------------------------------------
# git 通过 stdin 传入：<本地 ref> <本地 SHA> <远端 ref> <远端 SHA>。
# 删除分支或标签时本地 SHA 全零，跳过；手动运行（stdin 是终端或为空）退回校验 HEAD。
# 空行不算 ref；非空但不足四字段、或本地 SHA 不是十六进制的行按无法识别拦下——
# 畸形输入不能降级成「只包含删除操作」而放行。
SHAS=()
SAW_REF=0
if [ ! -t 0 ]; then
  while IFS=' ' read -r local_ref local_sha remote_ref _remote_sha || [ -n "${local_ref:-}" ] || [ -n "${local_sha:-}" ]; do
    if [ -z "${local_ref:-}" ] && [ -z "${local_sha:-}" ]; then
      continue
    fi
    if [ -z "${local_ref:-}" ] || [ -z "${local_sha:-}" ] || [ -z "${remote_ref:-}" ]; then
      echo "pre-push: stdin 行格式无法识别：${local_ref:-} ${local_sha:-} ${remote_ref:-}" >&2
      exit 1
    fi
    case "$local_sha" in
      *[!0-9a-fA-F]*)
        echo "pre-push: stdin 中的本地 SHA 不是十六进制：$local_sha" >&2
        exit 1
        ;;
    esac
    SAW_REF=1
    case "$local_sha" in
      *[!0]*) SHAS+=("$local_sha") ;;
    esac
  done
fi
if [ "${#SHAS[@]}" -eq 0 ]; then
  if [ "$SAW_REF" = "1" ]; then
    echo "pre-push: 本次推送只包含删除操作，没有需要校验的提交，放行"
    exit 0
  fi
  if ! HEAD_SHA="$(git rev-parse --verify --quiet HEAD)"; then
    echo "pre-push: 无法解析 HEAD（仓库没有提交？），无法验证" >&2
    exit 1
  fi
  SHAS=("$HEAD_SHA")
  echo "pre-push: 没有收到待推送 ref（手动运行），改校验 HEAD $(git rev-parse --short "$HEAD_SHA")"
fi

UNIQUE_SHAS="$(printf '%s\n' "${SHAS[@]}" | sort -u)"

TMP_DIRS=()
WORKTREES=()
cleanup() {
  local w t
  for w in "${WORKTREES[@]:-}"; do
    [ -n "$w" ] && git worktree remove --force "$w" >/dev/null 2>&1
  done
  for t in "${TMP_DIRS[@]:-}"; do
    [ -n "$t" ] && rm -rf "$t"
  done
  git worktree prune >/dev/null 2>&1
}
trap cleanup EXIT

for sha in $UNIQUE_SHAS; do
  short="$(git rev-parse --short "$sha" 2>/dev/null || printf '%s' "${sha:0:7}")"
  # 推 annotated tag 时 stdin 给的是 tag 对象 SHA；这里显式剥离到 commit 再检出，
  # 不依赖 git 对 worktree add 的隐式 tag 剥离行为（事实口径，不是「不剥就会失败」的断言）。
  if ! commit_sha="$(git rev-parse --verify --quiet "${sha}^{commit}")"; then
    echo "pre-push: 待推送对象 $short 不是本地可读的提交，无法验证" >&2
    FAILED="$FAILED ${short}:unreadable"
    continue
  fi

  tmp="$(mktemp -d "${TMPDIR:-/tmp}/agentflow-pre-push.XXXXXX")"
  wt="$tmp/tree"
  # 只收 stdout；git 的错误留在终端，否则「无法检出」永远不说明真实原因。
  if ! git worktree add --detach --quiet "$wt" "$commit_sha" >/dev/null; then
    echo "pre-push: 无法把待推送提交 $short 检出到临时工作树，无法验证" >&2
    FAILED="$FAILED ${short}:checkout"
    rm -rf "$tmp"
    continue
  fi
  TMP_DIRS+=("$tmp")
  WORKTREES+=("$wt")

  if [ ! -f "$wt/tools/lab/validate.py" ]; then
    # 判断依据用提交的父树，不用当前工作区：工作区可能已经被 `git rm` 弄脏，
    # 那会把「本次推送删掉了门禁」误判成「本仓本来就没有门禁」。
    parent="$(git rev-parse --verify --quiet "${commit_sha}^" 2>/dev/null || true)"
    if [ -n "$parent" ] && git cat-file -e "${parent}:tools/lab/validate.py" 2>/dev/null; then
      echo "pre-push: 待推送提交 ${short} 删除了 tools/lab/validate.py，无法验证" >&2
      FAILED="$FAILED ${short}:gate-missing"
    else
      echo "pre-push: 待推送提交 ${short} 的树与父树都没有 tools/lab/validate.py，记为未运行" >&2
      UNRUN="$UNRUN ${short}:no-gate"
    fi
    continue
  fi

  # 门清单以**待推送提交**的 --list 为单源：用本地树的门清单去检查另一棵树，会在门项
  # 增删的提交上给出与目标树不匹配的结论。排除 all/installed/lint/report/recurrence
  # 的理由同前：all 是聚合、installed 读仓外内容不属于推送提交、lint 单独按依赖处理、
  # 后两者是只读表格不校验。
  #
  # 不屏蔽 stderr：解释器过旧时 validate.py 在 stderr 说明原因并以 2 退出，屏蔽后只会
  # 得到「门清单为空」，把排查引向错误方向（AGENTS.md 禁止屏蔽命令输出）。
  #
  # `env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE`：实测 git 2.x 调 pre-push 时只导出
  # GIT_EDITOR/GIT_PREFIX/GIT_EXEC_PATH，不含这三个；但若某个宿主版本导出了它们，
  # `cd "$wt"` 只换 cwd 不换 GIT_DIR，依赖 git 的门项会读主仓索引而误判为绿。
  # 显式清掉是廉价的防御，且不影响没有这些变量的情形。
  GATE_ENV=(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE)
  if TARGETS="$(cd "$wt" && "${GATE_ENV[@]}" "$GATE_PYTHON" tools/lab/validate.py --list \
    | grep -vE 'all runs [0-9]+ checks' \
    | grep -vxE 'all|installed|lint|report|recurrence' \
    | tr '\n' ' ')"; then
    :
  else
    echo "pre-push: 待推送提交 $short 的门清单读取失败，无法验证" >&2
    FAILED="$FAILED ${short}:targets"
    continue
  fi
  if [ -z "${TARGETS// /}" ]; then
    echo "pre-push: 待推送提交 $short 的门清单为空或读取失败，无法验证" >&2
    echo "pre-push: 常见原因是解释器过旧（需 >= 3.10）或 tools/lab/validate.py 无法启动；" >&2
    echo "pre-push: 用 AGENTFLOW_GATE_PYTHON 指定解释器后重试。" >&2
    FAILED="$FAILED ${short}:targets"
    continue
  fi

  echo "pre-push: 校验待推送提交 ${short}（临时检出，不用工作区）：$TARGETS"
  for target in $TARGETS; do
    if ( cd "$wt" && "${GATE_ENV[@]}" "$GATE_PYTHON" tools/lab/validate.py "$target" ); then
      :
    else
      FAILED="$FAILED ${short}:${target}"
    fi
  done

  # lint 需要 dev 依赖。缺依赖是「未运行」而不是「失败」，但未运行同样不授予放行资格：
  # 默认拦下，只有显式 ALLOW_UNRUN=1 才放行并保留告警。
  if "$GATE_PYTHON" -c 'import ruff, mypy' >/dev/null 2>&1; then
    if ! ( cd "$wt" && "${GATE_ENV[@]}" "$GATE_PYTHON" tools/lab/validate.py lint ); then
      FAILED="$FAILED ${short}:lint"
    fi
  else
    echo "pre-push: lint 未运行（$GATE_PYTHON 缺 ruff/mypy）；用 AGENTFLOW_GATE_PYTHON 指定装好 dev 依赖的解释器" >&2
    UNRUN="$UNRUN ${short}:lint"
  fi
  CHECKED="$CHECKED $short"
done

if [ -n "$FAILED" ]; then
  echo "" >&2
  echo "pre-push: 门禁红 —— 推送已拦下。失败项：${FAILED}" >&2
  echo "pre-push: 先修好再推。确实要带红推送时用 \`git push --no-verify\`，并在提交说明里写清原因。" >&2
  exit 1
fi

if [ -n "$UNRUN" ]; then
  echo "" >&2
  echo "pre-push: 有检查未运行：${UNRUN}" >&2
  echo "pre-push: 未运行不等于通过；默认拦下。lint 未运行请装 dev 依赖（或指定 AGENTFLOW_GATE_PYTHON），" >&2
  echo "pre-push: 无门禁（no-gate）请补上 tools/lab/validate.py；" >&2
  echo "pre-push: 或显式设 AGENTFLOW_PREPUSH_ALLOW_UNRUN=1 放行这次推送并在提交说明里写清原因。" >&2
  if [ "$ALLOW_UNRUN" = "1" ]; then
    echo "pre-push: AGENTFLOW_PREPUSH_ALLOW_UNRUN=1，放行（未运行项未经验证）" >&2
    exit 0
  fi
  exit 1
fi

if [ -z "${CHECKED// /}" ]; then
  # 按构造不可达：每个 tip 要么进 CHECKED，要么进 FAILED/UNRUN，二者都已在上方处理。
  # 保留为 fail-closed 兜底，避免将来改动把「没检查任何东西」变成成功。
  echo "pre-push: 内部状态异常：没有任何提交被校验，也无法归因到未运行项，拦下" >&2
  exit 1
fi

echo "pre-push: 全绿，放行（已校验：${CHECKED}）"
exit 0
