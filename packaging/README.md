# 运行时打包

`marketplace.json` 把 ZCode 指向 `packaging/runtime`，而不是仓库根。该目录是生成的。它
不是权威来源。

```sh
python3 packaging/build_runtime.py
```

该副本包含 `agents/`、`skills/`、`schemas/`、五份 manifest、宿主插件包装，以及
`protected-paths.txt`。它排除记录根（`issues/`、`episodes/`、`plans/`、`improvements/`、
`releases/`、`reviews/`）、`_archive/`、`tests/`、`tools/`、`docs/`、`evals/`、`mock/` 和
`examples/`。

生成后刷新本地 marketplace 并重新安装。`python3 tools/lab/validate.py
installed` 仍把那些运行时文件与仓库根比较，而不是与本目录比较。Claude 的
`--plugin-dir .` 与 Codex 继续使用源码树。

从 skills 指向记录根的相对链接只在源码检出中可解析。
