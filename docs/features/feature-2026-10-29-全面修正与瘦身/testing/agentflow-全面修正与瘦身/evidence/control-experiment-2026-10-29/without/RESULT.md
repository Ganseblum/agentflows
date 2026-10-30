# RESULT

## 改动文件

- `sales.py`：新增可选参数 `--top N`。有 `--top` 时按总额降序输出前 N 个区域，同额按区域名升序；
  无 `--top` 时保持原行为（按区域名升序、输出全部）。`N < 1` 与金额解析失败均走 `parser.error`，
  退出码 2、stderr 非空；输出格式保持 `<region>\t<total with 2 decimals>`。
- `tests/test_sales.py`：新增 5 个回归测试（`--top` 取前 N 降序、同额按名字升序、N 大于区域数、
  `--top 0` 退出 2 且有 stderr、金额非法退出 2 且有 stderr 且 stdout 为空）。原有 1 个测试未改动。

## 测试运行记录（共 2 次 unittest 运行）

1. 基线，改动前：
   `cd /tmp/agentflow-experiment-2026-10-29/without && python3 -m unittest discover -s tests -v`
   → Ran 1 test，OK，exit 0。
2. 改动后：
   `cd /tmp/agentflow-experiment-2026-10-29/without && python3 -m unittest discover -s tests -v`
   → Ran 6 tests，OK，exit 0。

补充（手工 CLI 验证，不计入上面的测试运行次数）：用临时 CSV 直接跑 `sales.py`，
观察到：无 `--top` 输出按区域名升序全集；`--top 2` 输出 `east 30.00 / west 20.00`；
`--top 0` 退出 2 且 stderr 为 `sales.py: error: --top must be at least 1`；
金额为 `oops` 时退出 2 且 stderr 为 `sales.py: error: invalid amount value: could not convert string to float: 'oops'`。

## 失败 / 返工轮次

0 轮。首次实现后测试即全绿，没有出现失败后返工。

## 完成与否的依据

- 全部 6 个测试通过（含原有 1 个未改动测试），说明无回归。
- 手工观察到的 4 组 CLI 行为分别对应 TASK.md 的 4 条要求：`--top N` 的排序与截断、
  无 `--top` 时行为不变、`N < 1` 退出 2 且 stderr 非空、金额非法退出 2 且 stderr 非空；
  输出两列格式与两位小数逐字核对一致。
- 只在 `sales.py` 与 `tests/` 内改动，未提交 git。
