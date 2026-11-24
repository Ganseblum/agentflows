# 运行时打包

`marketplace.json` 指向 `packaging/runtime`。源码在仓库根。脚本使用 Python 3.10+。

```sh
python3 packaging/build_runtime.py
```

载荷包含 `agents/`、`skills/`、四个宿主的清单目录及 `plugin.json`、`marketplace.json`。
打包先验证源码清单，在同一父目录构建并核对生成包，成功后才替换原包。自定义目的地必须是新路径
或本插件的生成目录。已有普通目录及符号链接会被拒绝。

## 升级与核验

| 宿主 | 本仓入口 |
| --- | --- |
| Codex | `bash skills/agentflow/scripts/upgrade-codex.sh --mode local`。首次安装先在 Codex 里注册本地 marketplace，适配器沿用已配置来源。 |
| ZCode | `bash skills/agentflow/scripts/upgrade-zcode.sh --mode auto`。默认沿用已配置的本地或 Git 来源，可用 `--mode local` 或 `--mode remote` 验证所选类型。 |
| Claude Code | 源码根运行 `claude --plugin-dir .`；需验证生成包时使用 `--plugin-dir packaging/runtime`。 |
| Qoder | `qoder plugins install packaging/runtime --scope user`，或通过 Qoder 桌面扩展设置安装该目录的 ZIP。 |

升级脚本支持 `--dry-run`、`--marketplace` 和 `--plugin`。安装后运行
`python3 skills/agentflow/scripts/workflow.py install-verify --expected-tree packaging/runtime --installed <缓存目录>`，
使用 Codex 源码缓存时加 `--codex-source`。这一步核对文件集合、字节和执行位。

### 排查技能发现与加载

1. 用上述安装核验确认运行时和缓存载荷一致。记录宿主版本、插件版本和安装路径。
2. 在实际目标工作区重新枚举入口，保存宿主原始输出与警告。Codex CLI 可读 app-server 的 `skills/list`，ZCode 可用 `skills list --json`，Claude Code 可读新会话的技能菜单或 SDK 初始化清单，Cursor 在对应工作区看 Skills/Rules。已发现但路径不符时，检查是否被工作区或用户同名入口遮住。菜单条目存在且无法触发时，再查启用设置、元数据警告和触发描述。
3. 需要证明生效时，在不含同名入口的临时工作区另开一次会话。Skill 探针验证加载路径及一个新版独有特征。常驻规则探针验证新会话在读文件前就能复述该规则中的唯一标记。记录所选入口、实际原始输出、退出码以及未验证的宿主或表面；枚举和会话行为分别记录。

本机各宿主的观察见[宿主平台事实](../docs/host-platform-facts.md)。

## 发布检查

`python3 skills/agentflow/scripts/check_skill_refs.py` 检查源码和生成包的清单版本，以及分发文件的
链接、标题锚点和声明的加载者。重建前可加 `--source-only` 校验源码。

`publish.sh` 只接受已准备好的提交，或带提交说明的已暂存批次。发布入口拒绝未暂存与未跟踪改动，
核对版本节和实际载荷后才进入提交或推送。使用 `--dry-run` 查看计划；`--no-push` 允许只做本地动作。
