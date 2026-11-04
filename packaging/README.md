# 运行时打包

`marketplace.json` 把 ZCode 指向 `packaging/runtime`，而不是仓库根。该目录是生成的。它
不是权威来源。

```sh
python3 packaging/build_runtime.py
```

该脚本把可安装面（运行时面）复制到 `packaging/runtime`：只含 `agents/`、`skills/`、四个宿主插件目录
（`.zcode-plugin/`、`.claude-plugin/`、`.codex-plugin/`、`.qoder-plugin/`），以及 `plugin.json`、
`marketplace.json`。除此之外的一切（记录、实验、源码检查器、文档、测试）都不复制——它们不是
插件的运行时内容。

重建后刷新本地 marketplace 并重新安装，让宿主加载最新面。仓库根的 `agents/`、`skills/` 与生成树
应保持一致：每次发布都先重建再安装。Claude 的 `--plugin-dir .` 与 Codex 继续使用源码树。

从 skills 指向记录根的相对链接只在源码检出中可解析。
