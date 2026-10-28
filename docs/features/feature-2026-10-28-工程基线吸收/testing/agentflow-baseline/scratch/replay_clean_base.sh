#!/bin/sh
# 在干净副本上复跑本批改动：克隆当前提交（不含工作树里其它会话的未提交改动），
# 只叠加本批声明的改动，再跑文档链与全量门。共享工作树被其它会话占用时用它取证。
#
# 对四个同时混有另一会话 ID 格式改名的文件（SKILL.md / templates/README.md /
# templates/testing/plan.md / agents/test-planner.md），按本批的具体行做 hunk-only 修补，
# 不把另一会话的 REV/TP/ISS 格式改名带进副本。
#
# 用法：sh docs/features/feature-2026-10-28-工程基线吸收/testing/agentflow-baseline/scratch/replay_clean_base.sh
set -eu

REPO=$(git rev-parse --show-toplevel)
DEST=$(mktemp -d /tmp/af-clean-base-XXXXXX)
echo "# clean-base replay"
echo "base_ref=$(git -C "$REPO" rev-parse HEAD)"
echo "dest=$DEST"
git clone -q --no-hardlinks "$REPO" "$DEST"
cd "$DEST"

copy() {
  mkdir -p "$(dirname "$1")"
  cp "$REPO/$1" "$1"
}

for f in \
  CHANGELOG.md \
  docs/quickstart.md \
  plugin.json \
  marketplace.json \
  .zcode-plugin/plugin.json \
  .claude-plugin/plugin.json \
  .codex-plugin/plugin.json \
  agents/backend-engineer.md \
  agents/frontend-engineer.md \
  skills/agentflow/templates/engineering/baseline.md \
  skills/agentflow/templates/feature/design/be/backend.md \
  skills/agentflow/templates/feature/design/fe/frontend.md \
  skills/agentflow/templates/feature/spec/fe/frontend.md \
  skills/agentflow/templates/feature/prototype/README.md
do
  copy "$f"
done

mkdir -p "docs/features/feature-2026-10-28-工程基线吸收"
cp -R "$REPO/docs/features/feature-2026-10-28-工程基线吸收/." "docs/features/feature-2026-10-28-工程基线吸收/"

python3.12 - "$REPO" <<'PY'
import sys
from pathlib import Path

Dest = Path.cwd()

def insert_after(path: Path, anchor: str, snippet: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith(anchor))
    lines[idx + 1:idx + 1] = snippet.splitlines()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def insert_before(path: Path, anchor: str, snippet: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith(anchor))
    lines[idx:idx] = snippet.splitlines()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:60]}")
    path.write_text(text.replace(old, new), encoding="utf-8")

# 三处共享索引只叠加本批自己的行/句，不带入其它会话的重命名。
insert_after(
    Dest / "docs/features/README.md",
    "| [`feature-2026-10-28-评测整改批`]",
    "| [`feature-2026-10-28-工程基线吸收`](feature-2026-10-28-工程基线吸收/) | 外部工程语料吸收（工程基线模板与 Init 六项 / 后端数据与配置核对 / 原型可点性 / 测试设计三维 / 前端实现纪律） | 原四项实施与独立评审通过；FE 增量实现与门禁完成，但独立评审未运行（用户拒绝委派，T12 ⚠）；未提交、未推送、未重装；状态以 `plan/PLAN-BASE-001.md` 为准 |",
)
insert_before(
    Dest / "index.md",
    "- 2026-10-28 评审欠账清偿批（立项：",
    "- 2026-10-28 工程基线吸收批（工程基线模板与 Init 六项 / 后端数据与配置核对 / 原型可点性 / 测试设计三维 / 前端实现纪律；原四项已评审，FE 增量独立评审未运行；0.21.0 未发布）——见 [批次入口](docs/features/feature-2026-10-28-工程基线吸收/README.md)、[计划](docs/features/feature-2026-10-28-工程基线吸收/plan/PLAN-BASE-001.md)",
)
insert_after(
    Dest / "docs/releases/pending-test.md",
    "| 6 | 评测整改批 0.20.0",
    "| 7 | 工程基线吸收批 0.21.0（分支 `feature-2026-10-28-评审欠账清偿`）：工程基线模板与 Init 六项 / 后端数据与配置核对 / 原型可点性 / 测试设计三维 | ① 合并后重建生成树并重装，`validate.py installed` 转绿；② 新目标仓接入时确认 Init 确实问到工程基线并落入口路径；③ 按 `templates/engineering/baseline.md` 在一个真实仓落一份基线，检查每条 `<填>` 是否都有事实来源 | **未做**：本批只完成本地实现与干净副本门验证（批次链 linter PASS、干净副本 `validate.py all` 11/11 PASS；共享树因另一会话未提交改动为红），见批次 `testing/agentflow-baseline/evidence/`；未提交、未推送、未重装。①②③ 待发布与真实接入后执行，不记为已验收 |",
)
replace(
    Dest / "docs/releases/pending-test.md",
    "Init 约定（五项）",
    "Init 约定（当时为五项；现为六项，见第 7 行）",
)
replace(
    Dest / "docs/releases/pending-test.md",
    "SKILL.md Init 五项与 AGENTS.md",
    "SKILL.md Init 当时的五项与 AGENTS.md",
)

# 深链契约：只叠本批两处，不带入其它会话的 ISS 重命名。
chain = Dest / "skills/agentflow/references/document-chain.md"
text = chain.read_text(encoding="utf-8")
anchor = "  前要求的产品预览。\n"
addition = (
    "  **原型要能点。** 每个可见控件要么有真实反馈（筛选、弹层、翻页、状态变更、toast）要么明确\n"
    "  `disabled`；隐藏态（hover 工具条、折叠区、内嵌面板）要能通过交互显现；列表页有工具栏与行内动作，\n"
    "  详情或编辑至少能打开 Modal / Drawer。假数据的字段名、枚举值、ID 形态与分页结构要和真实接口一致，\n"
    "  数值随筛选或时间范围变化；无法演示的能力标注「演示 / 规划稿」，不用 toast 冒充已实现。\n"
    "  这条靠人工逐页点击判定——插件没有对应的机器门，脚本扫描只能当线索（实测初筛 102 个问题页 / 1403 个死按钮、真实缺口 8 页；单位不同不能直接算误报率），\n"
    "  不能拿扫描通过代替走查。\n"
)
if anchor not in text:
    raise SystemExit("prototype anchor not found")
text = text.replace(anchor, anchor + addition, 1)
old = (
    "  覆盖方向按八个方向逐个别默许跳过：功能 / 速度容量 / 权限安全 / 版本平台兼容 / 异常恢复 /\n"
    "  页面操作体验 / 数据一致 / 日志监控。"
)
new = (
    "  覆盖方向按十一个方向逐个不默许跳过：功能 / 速度容量 / 权限安全 / 版本平台兼容 / 异常恢复 /\n"
    "  页面操作体验 / 数据一致性 / 日志与监控 / 并发与竞态 / 生命周期与清理 / 契约与兼容。"
)
if old not in text:
    raise SystemExit("directions anchor not found")
chain.write_text(text.replace(old, new, 1), encoding="utf-8")
print("shared docs patched")
PY

python3.12 - "$REPO" <<'PY'
import sys
from pathlib import Path

repo = Path(sys.argv[1])
Dest = Path.cwd()

def wl(path: str) -> list[str]:
    return (repo / path).read_text(encoding="utf-8").splitlines()

def replace_line(path: Path, prefix: str, new: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith(prefix))
    lines[idx] = new
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def insert_after(path: Path, anchor_line: str, snippet: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if anchor_line in ln)
    lines[idx + 1:idx + 1] = snippet
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:60]}")
    path.write_text(text.replace(old, new), encoding="utf-8")

# SKILL.md：只叠 Init 六项与工程基线入口两处，保留基线里的 REV 旧格式。
skill = Dest / "skills/agentflow/SKILL.md"
six = next(ln for ln in wl("skills/agentflow/SKILL.md") if ln.startswith("1. 与用户确认六项"))
para = next(ln for ln in wl("skills/agentflow/SKILL.md") if ln.startswith("   小节还要写明**工程基线入口**"))
replace_line(skill, "1. 与用户确认五项", six)
insert_after(skill, "输出里出现 finding 不许口头绕过", ["", para])

# hosts.md：只在 Init 行加「工程基线入口」，不带入另一会话新增的 repo-rules 链接。
hosts = Dest / "skills/agentflow/references/hosts.md"
replace(
    hosts,
    "| 仓库接入（Init） | 该仓的具体约定：检查命令、文档落点、分支前缀实例 |",
    "| 仓库接入（Init） | 该仓的具体约定：检查命令、文档落点、工程基线入口、分支前缀实例 |",
)

# templates/README.md：只插 engineering 行，保留基线里的 ISS 旧格式。
row = next(ln for ln in wl("skills/agentflow/templates/README.md") if ln.startswith("| [engineering/baseline.md]"))
insert_after(Dest / "skills/agentflow/templates/README.md", "| [host/README.md]", [row])

# plan.md：只加三行方向、判定口径并把「八个方向」改「十一个方向」，保留 TP/ISS 旧格式。
plan = Dest / "skills/agentflow/templates/testing/plan.md"
plan_text = plan.read_text(encoding="utf-8")
plan_text = plan_text.replace("<填：八个方向逐个回答", "<填：十一个方向逐个回答", 1)
lines = plan_text.splitlines()
idx = next(i for i, ln in enumerate(lines) if ln.startswith("| 日志与监控 |"))
lines[idx + 1:idx + 1] = [
    "| 并发与竞态 | （填写） | （填写） | （填写） |",
    "| 生命周期与清理 | （填写） | （填写） | （填写） |",
    "| 契约与兼容 | （填写） | （填写） | （填写） |",
    "",
    "**三类易漏维度的判定口径**：并发与竞态看连点、重复提交、旧请求晚返回覆盖新状态、重试导致重复副作用；生命周期与清理看卸载后回调、路由切换残留、轮询/监听/Observer/对象 URL 是否释放；契约与兼容看字段省略、空串、`null`、零值、未知枚举、旧数据与老配置。按功能形态取最小必测集：表单提交、异步列表、上传、登录/会话、配置开关各自至少覆盖主路径、最关键失败、状态切换与重复提交；未覆盖的形态显式声明。",
]
plan.write_text("\n".join(lines) + "\n", encoding="utf-8")

# test-planner.md：只插三维度一句，保留基线里的 TP 旧格式。
sentence = next(ln for ln in wl("agents/test-planner.md") if ln.startswith("  - 除默认边界类外，逐项判定三类易漏维度"))
insert_after(Dest / "agents/test-planner.md", "未覆盖的类要在表中声明，绝不沉默。", [sentence])
print("mixed files patched hunk-only")
PY

# 真实工作树里存在但 git 不跟踪的空目录（另一批计划引用了它们）；副本里补建，避免把
# 「空目录不入库」误读成本批引入的 C9 缺口。
mkdir -p \
  "docs/features/feature-2026-10-28-评审欠账清偿/testing" \
  "docs/features/feature-2026-10-28-评测整改批/reviews" \
  "docs/features/feature-2026-10-28-表达面与角色治理/reviews"

# 版本与生成树
python3.12 - <<'PY'
from pathlib import Path
for name in ["plugin.json", "marketplace.json", ".zcode-plugin/plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]:
    p = Path(name)
    text = p.read_text(encoding="utf-8")
    if '"version": "0.21.0"' not in text:
        raise SystemExit(f"expected 0.21.0 in {name}")
    print(f"{name}: 0.21.0")
PY
python3.12 packaging/build_runtime.py

git add -A
git -c user.name=clean-base-verify -c user.email=clean-base-verify@example.invalid commit -q -m "verify: clean-base replay of feature-2026-10-28-工程基线吸收"
echo "clone_commit=$(git rev-parse HEAD)"

echo
echo '$ python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-工程基线吸收"'
python3.12 tools/lab/doc_chain.py "docs/features/feature-2026-10-28-工程基线吸收"
echo "doc_chain_exit=$?"

echo
echo '$ AGENTFLOW_LINT_PYTHON=<real .venv>/bin/python python3.12 tools/lab/validate.py all'
AGENTFLOW_LINT_PYTHON="$REPO/.venv/bin/python" python3.12 tools/lab/validate.py all
echo "validate_all_exit=$?"
