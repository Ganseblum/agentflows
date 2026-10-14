# feature-demo 后端规格

## 0. 不合规项（反审 checklist）

对照 proposal 逐节挑缺口；阻塞项全关才能进 design。

| # | 缺口 | 阻塞 | 状态 |
| --- | --- | --- | --- |
| B-1 | proposal 未定义空列表的返回形态 | 阻塞 | ☑ 已关闭（本文件 §2 定义） |
| B-2 | proposal 未说明游标有效期 | 非阻塞 | ☑ 已关闭（§2 定义为 10 分钟） |
| B-3 | proposal 未给出排序稳定性保证 | 阻塞 | ☑ 已关闭（§2 以 id 为次级排序键） |

## 1. 行为条目

| # | 陈述 | 验收口径 | 标尺 |
| --- | --- | --- | --- |
| S1 | 列表接口支持游标分页 | 单次返回不超过 pageSize 条，且携带 next_cursor | `python3 -m pytest tests/test_list_cursor.py` |
| S2 | 空列表返回空数组而非 null | HTTP 200 且 body 为 `[]` | 同上用例 §空列表 |
| S3 | 游标过期返回明确错误 | HTTP 410 且 error_code 为 `CURSOR_EXPIRED` | 同上用例 §过期 |

## 2. 接口形态

| 接口 | 请求字段 | 响应字段 |
| --- | --- | --- |
| A1 | cursor(string,N) · pageSize(int,Y) · filter(object,N) | items(array) · next_cursor(string) |
