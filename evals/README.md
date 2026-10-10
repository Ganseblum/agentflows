# 评测工作区

`public/` 包含十五个离线回归用例（`AF-001`–`AF-015`），其脱敏输入在 `public/inputs/` 下。它们
测的是工作流决策与权限边界，而非模型质量。私有 holdout 用例必须放在本项目之外，也必须放在
候选 worktree 之外。

`business/` 是方法级业务切片：其三个公开用例覆盖打种后的文档审查缺陷、内部矛盾与跨文档一致性。
`measurement.status=complete` 的发布记录必须写明业务用例 id 并保留 baseline/candidate 链；
否则使用 `measurement.status=none` 并给出明确依据，不得称该改动为已验证。

整个套件是 [`protected-paths.txt`](../protected-paths.txt) 声明的发布门的一部分：候选不得编辑用例、其输入，
或据以度量它的验收标准。

用确定性校验器校验套件，然后使用 baseline/candidate runner：

```sh
python3 tools/lab/validate.py evals
python3 tools/lab/eval_runner.py run --help
python3 tools/lab/eval_runner.py compare --help
```

用例契约与宿主 adapter 协议见 [public/README.md](public/README.md) 与
[../tools/lab/README.md](../tools/lab/README.md)。
