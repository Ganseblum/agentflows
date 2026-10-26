#!/usr/bin/env bash
# pre-push.sh — 推送前的门禁。由 .git/hooks/pre-push 调用，也可手动跑。
#
# 只做一件事：在把提交推出去之前，对**将要被推送的那棵树**跑十项确定性检查。
# 不重建生成树、不装宿主——那些是发布动作，需要显式授权（见 publish.sh）。
#
# 为什么值得每次推送都跑：门禁发现的多数问题（断链、记录契约、文档链形态、版本散文）
# 在本地几秒内就能暴露，而一旦推进远端，CI 才红、别人拉到红树，代价高得多。
#
# 装法（一次性，见 install-hooks.sh）：
#   ln -sf ../../skills/agentflow/scripts/pre-push.sh .git/hooks/pre-push
# 临时跳过：
#   git push --no-verify
#
# 退出状态：0 = 全绿，放行推送；1 = 有红项，拦下推送。

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "pre-push: 不在 git 仓库内，跳过" >&2
  exit 0
}
cd "$REPO_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "pre-push: 找不到 python3，无法跑门禁。" >&2
  echo "pre-push: 这是环境缺失、不是代码缺陷，按「未运行」处理，放行推送。" >&2
  echo "pre-push: 装好 python3 后这一关才会真正生效。" >&2
  exit 0
fi

if [ ! -f "tools/lab/validate.py" ]; then
  echo "pre-push: 找不到 tools/lab/validate.py，本仓没有门禁，跳过" >&2
  exit 0
fi

# 门清单是单源：直接解析 `validate.py --list` 的输出，而不是硬编码。任何一处新增/删除
# 门项，脚本自动跟随，不再与 --list 双源（2026-10-26 审计 G24）。排除 all/installed/
# lint/report/recurrence：all 是聚合、installed 读仓外内容不属于推送前树、lint 缺依赖
# 记为未运行、后两者是只读表格不校验。
REQUIRED_KINDS="all installed lint report recurrence"
TARGETS="$(python3 tools/lab/validate.py --list \
  | grep -vE 'all runs [0-9]+ checks' \
  | while read -r kind; do
      case " $REQUIRED_KINDS " in
        *" $kind "*) ;;
        *) echo "$kind" ;;
      esac
    done)"
FAILED=""

echo "pre-push: 跑门禁（$(git rev-parse --short HEAD)）：必绿项 $TARGETS"
for target in $TARGETS; do
  if python3 tools/lab/validate.py "$target"; then
    :
  else
    FAILED="$FAILED $target"
  fi
done

# lint 需要 dev 依赖。缺依赖是「未运行」而不是「失败」——与仓库判据一致。
LINT_PYTHON="${AGENTFLOW_LINT_PYTHON:-python3}"
if "$LINT_PYTHON" -c 'import ruff, mypy' >/dev/null 2>&1; then
  python3 tools/lab/validate.py lint || FAILED="$FAILED lint"
else
  echo "SKIP lint（未运行：没有 ruff/mypy；用 AGENTFLOW_LINT_PYTHON 指定装好 dev 依赖的解释器）"
fi

if [ -n "$FAILED" ]; then
  echo "" >&2
  echo "pre-push: 门禁红 —— 推送已拦下。失败项：${FAILED}" >&2
  echo "pre-push: 先修好再推。确实要带红推送时用 \`git push --no-verify\`，并在提交说明里写清原因。" >&2
  exit 1
fi

echo "pre-push: 全绿，放行"
exit 0
