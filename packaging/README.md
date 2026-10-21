# 运行时打包

`marketplace.json` 把 ZCode 指向 `packaging/runtime`，而不是仓库根。该目录是生成的。它
不是权威来源。

```sh
python3 packaging/build_runtime.py
```

门会核对这棵生成树的新鲜度：`python3 tools/lab/validate.py manifests` 在 `packaging/runtime`
存在时把它与源面逐字节对照（manifest 名字/版本 + 白名单内每个文件），漂移即门红并提示重建——
因为 marketplace 装的就是这棵树，过期快照会静默装出旧角色。项数以
`python3 tools/lab/validate.py --list` 自报为准，文档不手写计数。
改过 `agents/`、`skills/`、`schemas/` 或任何 manifest 之后重建它，再复跑该检查。

该副本只复制一份白名单：`agents/`、`skills/`、`schemas/`、三个宿主插件目录（`.zcode-plugin/`、
`.claude-plugin/`、`.codex-plugin/`），以及 `plugin.json`、`marketplace.json`、`protected-paths.txt`；
除此之外的一切都不复制。生成后 `verify` 还会拒绝在顶层出现以下名称（它们是记录、实验或源码树）：
`issues`、`episodes`、`plans`、`improvements`、`releases`、`reviews`、`tests`、`tools`、`docs`、`evals`、
`examples`、`.git`、`packaging`。

生成后刷新本地 marketplace 并重新安装。`python3 tools/lab/validate.py
installed` 仍把那些运行时文件与仓库根比较，而不是与本目录比较。Claude 的
`--plugin-dir .` 与 Codex 继续使用源码树。

从 skills 指向记录根的相对链接只在源码检出中可解析。
