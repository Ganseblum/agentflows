#!/usr/bin/env python3
"""评审成本基线测量（只读宿主用量库，不改任何文件）。

用途：改动前后用同一口径复测，避免「换了查询方式就得出不同结论」。

    python3 review-cost-baseline.py                 # 全部历史
    python3 review-cost-baseline.py --since 2026-10-28
    python3 review-cost-baseline.py --since 2026-10-28 --until 2026-11-05

口径说明：
- 只统计 agentflow:reviewer / reviewer 两类子代理会话。
- 轮次 = model_usage 里一次模型请求；步 = part 表里一次 step-finish。
- 「检索轮」= 该步发出的工具全部是 Grep/Glob（找位置），不含 Read。
- 「重复读」= 同一会话里对同一 file_path 的第 2 次及以后的 Read。
- 推理占比用 reasoning 文本字符 / 输出 token 的比值判断，不假设固定换算率。
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sqlite3
import statistics as st
from datetime import datetime, timedelta, timezone

DB = os.path.expanduser("~/.zcode/cli/db/db.sqlite")
AGENTS = ("zcode-agentflow:reviewer", "zcode-reviewer")
CODE_EXT = (".go", ".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".java",
            ".rs", ".sql", ".yaml", ".yml", ".sh")


def ms(t: str | None) -> int | None:
    if not t:
        return None
    return int(datetime.fromisoformat(t).replace(tzinfo=timezone(timedelta(hours=8))).timestamp() * 1000)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="起始日期 YYYY-MM-DD（含）")
    ap.add_argument("--until", help="结束日期 YYYY-MM-DD（不含）")
    args = ap.parse_args()
    lo, hi = ms(args.since), ms(args.until)

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    ph = ",".join("?" * len(AGENTS))

    where = ""
    params: list[object] = list(AGENTS)
    if lo:
        where += " and started_at >= ?"
        params.append(lo)
    if hi:
        where += " and started_at < ?"
        params.append(hi)

    sids = [r[0] for r in con.execute(
        f"select distinct session_id from model_usage where agent in ({ph}){where}", params)]
    if not sids:
        print("没有匹配的评审会话")
        return 0

    reqs = [{"session_id": r["session_id"], "duration_ms": r["duration_ms"],
             "ttft": r["ttft"], "o": r["o"]} for r in con.execute(
        f"select session_id,duration_ms,time_to_first_token_ms ttft,output_tokens o "
        f"from model_usage where agent in ({ph}){where} and status='completed'", params)]

    sessions = []
    for sid in sids:
        paths: collections.Counter[str] = collections.Counter()
        rounds = search_rounds = read_rounds = reason_chars = text_chars = 0
        step_tools: list[str] = []
        for r in con.execute(
                "select data from part where session_id=? order by time_created,id", (sid,)):
            try:
                d = json.loads(r["data"])
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "reasoning":
                reason_chars += len(d.get("text") or "")
            elif t == "text":
                text_chars += len(d.get("text") or "")
            elif t == "tool":
                name = d.get("tool")
                step_tools.append(name)
                if name == "Read":
                    fp = (d.get("state", {}).get("input") or {}).get("file_path")
                    if fp:
                        paths[fp] += 1
            elif t == "step-finish":
                rounds += 1
                if step_tools and all(x in ("Grep", "Glob") for x in step_tools):
                    search_rounds += 1
                elif "Read" in step_tools:
                    read_rounds += 1
                step_tools = []
        mine = [x for x in reqs if x["session_id"] == sid]
        if rounds < 5 or not mine:
            continue
        dup = sum(v - 1 for v in paths.values() if v > 1)
        sessions.append({
            "sid": sid, "rounds": rounds, "reqs": len(mine),
            "minutes": sum((x["duration_ms"] or 0) for x in mine) / 60000,
            "search": search_rounds, "read": read_rounds, "dup": dup,
            "uniq": len(paths), "rchars": reason_chars, "tchars": text_chars,
            "out": sum(x["o"] or 0 for x in mine),
        })

    if not sessions:
        print("没有可用于统计的评审会话（少于 5 步的会话已排除）")
        return 0

    def m(key: str) -> float:
        return st.median([s[key] for s in sessions])

    tot_out = sum(s["out"] for s in sessions)
    tot_rc = sum(s["rchars"] for s in sessions)
    tot_tc = sum(s["tchars"] for s in sessions)
    req = [x for x in reqs if x["session_id"] in {s["sid"] for s in sessions}]
    gen = sum(max(0, (x["duration_ms"] or 0) - (x["ttft"] or 0)) for x in req)
    wait = sum((x["ttft"] or 0) for x in req)
    decode = tot_out / (gen / 1000) if gen else 0

    print(f"窗口          : {args.since or '全部'} .. {args.until or '至今'}")
    print(f"评审会话      : {len(sessions)}")
    print(f"模型请求      : {len(req)}")
    print()
    print("中位会话")
    print(f"  时长        : {m('minutes'):.1f} 分钟")
    print(f"  轮次        : {m('rounds'):.0f}")
    print(f"  检索轮      : {m('search'):.0f}  ({m('search') / m('rounds') * 100:.1f}% of 轮次)")
    print(f"  读取轮      : {m('read'):.0f}")
    print(f"  重复读      : {m('dup'):.0f} 次")
    print(f"  唯一文件    : {m('uniq'):.0f}")
    print(f"  每轮均摊    : {m('minutes') / m('rounds') * 60:.1f} 秒")
    print()
    print("合计")
    print(f"  等首字      : {wait / 3600000:.1f} 小时 ({wait / max(wait + gen, 1) * 100:.0f}%)")
    print(f"  生成        : {gen / 3600000:.1f} 小时 ({gen / max(wait + gen, 1) * 100:.0f}%)")
    print(f"  解码速率    : {decode:.0f} tokens/s")
    print(f"  输出 token  : {tot_out / 1e6:.2f}M")
    print(f"  推理字符占比: {tot_rc / max(tot_rc + tot_tc, 1) * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
