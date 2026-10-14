# 文档链 linter 的实跑样例

> 用途：`validate.py examples` 会用 `tools/lab/doc_chain.py` 真跑这两个目录，把 C1–C11
> （结构与密度判据）钉在真实文件上——在此之前它们只在自测夹具里跑过，本仓任何一条真实链
> 都没被结构判据检查过。
>
> - `good/feature-demo/`：合格密链，必须**通过**（退出码 0）。
> - `bad/feature-demo-thin/`：原始薄链（每个阶段「存在」但没有密度），必须**失败**且报出
>   契约表、失败分支时序图、线框图与 plan 落点四类发现。
>
> 改这两个目录时同步改判据或期望——它们是夹具，不是文档样板。新增失败形态请另建目录并在
> `validate.py` 的 `DOC_CHAIN_EXAMPLE_EXPECTATIONS` 里声明期望发现。
