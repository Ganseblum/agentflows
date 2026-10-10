#!/usr/bin/env bash
# check-write-scope.sh — 校验工作区的实际改动面是否落在声明的写范围之内。
#
# Agentflow supervisor 在接受产物时运行本脚本（硬边界 14）：worker 的真实写入面以仓库
# diff 所示为准，而非其摘要所主张的内容。脚本列出基线 revision 与当前工作树之间发生
# 变更的每个路径——已提交、已暂存、未暂存、已删除、重命名两侧以及未跟踪——当任何变更
# 路径落在声明的范围之外时以失败退出。
#
# 用法：
#   scripts/check-write-scope.sh <base-revision> <scope-path>...
#
#   <base-revision>  委派工作时记录的 revision（即当时的 HEAD）。
#                    自那时起发生的一切变更都会与范围进行比对。
#   <scope-path>...  写范围：文件或目录。目录涵盖其下的全部内容。
#                    用 "." 表示允许整棵树。
#
# 说明：
#   - 委派时已经 dirty 的路径也会显示为变更；要么从干净的树委派，要么在阅读报告时
#     减去已知的 dirty 路径。
#   - 未跟踪文件会计入；被忽略的文件（按 .gitignore）不计入。
#
# 退出状态：所有变更路径都在范围内时为 0；任一变更路径在范围之外时为 1；
# 用法错误时为 2。

set -eu

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <base-revision> <scope-path>..." >&2
  exit 2
fi

base="$1"
shift
scopes=("$@")

if ! git rev-parse --verify --quiet "$base^{commit}" >/dev/null; then
  echo "error: 找不到基线 revision: $base" >&2
  exit 2
fi

changed=()
while IFS= read -r path; do
  [ -n "$path" ] && changed+=("$path")
done < <(git diff --name-only --no-renames "$base")
while IFS= read -r path; do
  changed+=("$path")
done < <(git ls-files --others --exclude-standard)

# `case` 模式不会进行路径名展开，这与 `[ ]` 内不加引号的 `*` 不同。
in_scope() {
  path="$1"
  for scope in ${scopes[@]+"${scopes[@]}"}; do
    normalized="${scope%/}"
    case "$path" in
      "$normalized" | "$normalized"/*) return 0 ;;
    esac
  done
  return 1
}

out_of_scope=()
count=0
for path in ${changed[@]+"${changed[@]}"}; do
  count=$((count + 1))
  if ! in_scope "$path"; then
    out_of_scope+=("$path")
  fi
done

if [ "${#out_of_scope[@]}" -gt 0 ]; then
  echo "FAIL: 共 $count 个变更路径中有 ${#out_of_scope[@]} 个在声明的写范围之外："
  for path in ${out_of_scope[@]+"${out_of_scope[@]}"}; do
    echo "  $path"
  done
  exit 1
fi

echo "OK: 共 $count 个变更路径，全部位于声明的写范围之内。"
