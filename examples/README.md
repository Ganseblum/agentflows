# 契约示例

`issues/`、`plans/` 和 `testing/` 含有结构上有效、经脱敏的示例。`doc-chain/` 是文档链 linter
（`tools/lab/doc_chain.py`）的正反例组：密链必须通过全部结构检查；2026-09-20 形状的薄链必须
失败并报出相应判据。`invalid/` 下的文件是被
有意拒绝的：校验器同时检查它们的 JSON Schema 以及 schema 无法单独表达的跨文档不变量（该组
由 `validate.py examples` 每次编译实跑，撤离即门红）。`decisions/` 是 C15–C17 决策门的 opt-in 演示语料（问题台账与
拍板口条目的正反例，未打标不受检，打标后按判据检查）。

运行：

```sh
python3 tools/lab/validate.py examples
```
