#!/usr/bin/env bash
# check-write-scope.sh — verify the workspace's actual change surface against a declared write scope.
#
# Agentflow supervisors run this at acceptance time (hard boundary 14): a worker's real write
# surface is what the repository diff shows, not what its summary claims. The script lists every
# path that changed between a baseline revision and the current working tree — committed, staged,
# unstaged, deleted, both sides of a rename, and untracked — and fails when any changed path falls
# outside the declared scope.
#
# Usage:
#   scripts/check-write-scope.sh <base-revision> <scope-path>...
#
#   <base-revision>  the revision recorded when the work was delegated (HEAD at that moment).
#                    Everything that changed since is compared against the scope.
#   <scope-path>...  the write scope: files or directories. A directory covers everything under
#                    it. Use "." to allow the whole tree.
#
# Notes:
#   - Paths already dirty at delegation time also appear as changes; either delegate from a
#     clean tree or subtract the known-dirty paths when reading the report.
#   - Untracked files are included; ignored files (per .gitignore) are not.
#
# Exit status: 0 when every changed path is inside the scope, 1 when any path is outside,
# 2 on a usage error.

set -eu

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <base-revision> <scope-path>..." >&2
  exit 2
fi

base="$1"
shift
scopes=("$@")

if ! git rev-parse --verify --quiet "$base^{commit}" >/dev/null; then
  echo "error: base revision not found: $base" >&2
  exit 2
fi

changed=()
while IFS= read -r path; do
  [ -n "$path" ] && changed+=("$path")
done < <(git diff --name-only --no-renames "$base")
while IFS= read -r path; do
  changed+=("$path")
done < <(git ls-files --others --exclude-standard)

# `case` patterns do not undergo pathname expansion, unlike an unquoted `*` inside `[ ]`.
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
  echo "FAIL: ${#out_of_scope[@]} of $count changed path(s) outside the declared write scope:"
  for path in ${out_of_scope[@]+"${out_of_scope[@]}"}; do
    echo "  $path"
  done
  exit 1
fi

echo "OK: $count changed path(s), all within the declared write scope."
