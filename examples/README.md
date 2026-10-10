# 契约示例

`issues/`、`plans/` 和 `testing/` 含有结构上有效、经脱敏的示例。`invalid/` 下的文件是被
有意拒绝的：校验器同时检查它们的 JSON Schema 以及 schema 无法单独表达的跨文档不变量。

运行：

```sh
python3 tools/lab/validate.py examples
```
