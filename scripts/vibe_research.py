#!/usr/bin/env python3
"""dsh-vibe-trading v0 — interactive trading research workbench (Vibe-Trading style, native to DSH)

Structure inspired by HKUDS/Vibe-Trading; the DSH-native differentiators:
- **an orchestrated research loop** (plan → data → compute → interpret) as one
  deterministic script, not a chain of hand-driven MCP calls;
- **numbers come only from the deterministic compute layer** (the LLM interprets,
  never produces figures) — the evidence discipline of the committee family;
- three deliverables: terminal brief + zero-dependency inline SVG card +
  an auditable research trail (question/plan/data/computations/findings).

Honesty contract: fields render as numbers or "n/a (reason)" — unavailable is
never 0; every dataset's source metadata rides with it; the mini backtest
reports in-sample and out-of-sample segments separately (frozen a-priori params).

Pipeline (2 DeepSeek calls per run, temperature=0):
  LLM plans the exploration → deterministic layer (K-lines / stats / mini
  backtest / SVG) → LLM interprets, citing only the computed results.

Usage:
  python3 scripts/vibe_research.py --question "Moutai vs the index: whose price-volume structure is weaker?" --symbols sh600519,sh000001
  python3 scripts/vibe_research.py --question "茅台 vs 大盘：量价结构谁更弱？" --lang zh
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_data import kline, stats_block, sma_cross_backtest, svg_chart

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAILS = os.path.join(KIT, "trails")

# English is the first language (family rule); Chinese is the --lang zh fallback.
LANG = "en"
STR = {
    "en": {
        "fetch_fail": "⚠ {sym} fetch failed: {e}",
        "question": "## Question: {q}",
        "plan": "**plan**",
        "computed": "## Computed results (summary)",
        "sym_line": "- **{sym}**: last {last} · 20d {ret20} · 60d {ret60} · {above} SMA60 · 30d vol {vol30} · from 120d peak {dd} · volume z {vz}",
        "above_yes": "above",
        "above_no": "below",
        "src_line": "  - data: {src}",
        "bt_line": "  - trend backtest (SMA20/60 cross, full-position, no fees): {trades} trades · win rate {wr} · strategy {sumret} vs buy&hold {bh}",
        "bt_train": "  - in-sample {span}: {trades} trades · strategy {sumret} vs buy&hold {bh}",
        "bt_hold": "  - out-of-sample {span}: {trades} trades · strategy {sumret} vs buy&hold {bh}",
        "oos_note_line": "── OOS discipline: {note}",
        "findings": "## Interpretation",
        "footer": "── SVG interactive card + research trail generated (--save writes files) · {secs}s",
        "saved": "→ {base}.html / .json",
        "computed_line": "computed {date} · deepseek-chat · temperature=0 · not investment advice",
        "plan_prompt": ("You are a research planner. Given the research question and the available symbols "
                        "(A-shares sh/sz+code, index sh000001, US us+code), output JSON "
                        '{"plan":"an exploration path of at most 4 steps","focus":"what to look at for each symbol"}. '
                        "Plan only, no conclusions."),
        "interpret_prompt": ("You are a research interpreter. Discipline: **you may ONLY cite the given computed "
                             "results** (cite stats/backtests fields as [S#]); inventing any number is forbidden; "
                             "one [F#] per conclusion. Fields rendered as {\"unavailable\": reason} must be "
                             "reported as unavailable with that reason — never guessed around. State which parts "
                             "of the question the results answer and which parts still lack data. "
                             "Output markdown, at most 8 findings. Write in English."),
    },
    "zh": {
        "fetch_fail": "⚠ {sym} 取数失败: {e}",
        "question": "## 研究问题：{q}",
        "plan": "**plan**",
        "computed": "## 计算结果（摘要）",
        "sym_line": "- **{sym}**: 现价 {last} · 20日 {ret20} · 60日 {ret60} · {above} SMA60 · 30日波动 {vol30} · 距120日峰 {dd} · 量能z {vz}",
        "above_yes": "站稳",
        "above_no": "跌破",
        "src_line": "  - 数据: {src}",
        "bt_line": "  - 趋势回测(20/60金叉,全仓无费): {trades} 笔 · 胜率 {wr} · 策略累计 {sumret} vs 持有 {bh}",
        "bt_train": "  - 样本内 {span}: {trades} 笔 · 策略 {sumret} vs 持有 {bh}",
        "bt_hold": "  - 样本外 {span}: {trades} 笔 · 策略 {sumret} vs 持有 {bh}",
        "oos_note_line": "── 样本外纪律: {note}",
        "findings": "## 解读",
        "footer": "── SVG 交互卡与研究轨迹已生成（--save 落盘）· {secs}s",
        "saved": "→ {base}.html / .json",
        "computed_line": "computed {date} · deepseek-chat · temperature=0 · 非投资建议",
        "plan_prompt": ("你是投研规划员。给定研究问题与可用符号（A股 sh/sz+代码、指数 sh000001、美股 us+代码），"
                        "输出 JSON {\"plan\":\"不超过4步的探索路径\",\"focus\":\"每个符号各看什么\"}。只规划，不结论。"),
        "interpret_prompt": ("你是投研解读员。纪律：**只允许引用给定的计算结果**（[S#] 引用 stats/backtests 字段），"
                             "禁止编造任何数字；每个结论一条 [F#]。以 {\"unavailable\": 原因} 呈现的字段必须如实"
                             "报告为不可用并给出原因，不得绕过臆测。指出计算结果回答了问题的哪部分、哪部分仍缺数据。"
                             "输出 markdown，不超过 8 条结论。用中文写。"),
    },
}


def t(key, **kw):
    s = STR[LANG].get(key, key)
    return s.format(**kw) if kw else s  # prompt strings carry literal JSON braces — never format them


def f(v, spec):
    """honest renderer: {'unavailable': reason} → 'n/a (reason)', else formatted number."""
    if isinstance(v, dict) and "unavailable" in v:
        return f"n/a ({v['unavailable']})"
    return spec.format(v)


def src_text(meta):
    s = (f"{meta['source']} · {meta['adjustment']} · {meta['date_range'][0]} → {meta['date_range'][1]} "
         f"· {meta['bars']}/{meta['requested_bars']} bars")
    if meta.get("coverage_gaps"):
        s += f" · {len(meta['coverage_gaps'])} coverage gap(s) > 10d"
    return s


def llm(sysmsg, user, json_out=False):
    key = subprocess.run(["bash", "-c", 'grep -m1 "^export DEEPSEEK_API_KEY=" ~/.bashrc | cut -d= -f2'],
                         capture_output=True, text=True).stdout.strip().strip('"')
    body = {"model": "deepseek-chat", "temperature": 0,
            "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": user}]}
    if json_out:
        body["response_format"] = {"type": "json_object"}
    r = subprocess.run(["curl", "-s", "-m", "180", "https://api.deepseek.com/chat/completions",
                        "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
                        "-d", json.dumps(body)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)["choices"][0]["message"]["content"]
    except Exception:
        raise SystemExit(f"LLM call failed: {r.stdout[:200]}")


def parse_json_loose(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"^```(json)?|```$", "", s.strip(), flags=re.M).strip())


def main():
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--symbols", required=True, help="comma-separated, e.g. sh600519,sh000001")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--lang", choices=("en", "zh"), default="en",
                    help="output language (default en; zh is the fallback)")
    args = ap.parse_args()
    LANG = args.lang
    t0 = time.time()

    plan = parse_json_loose(llm(t("plan_prompt"),
                                f"Question: {args.question}\nSymbols: {args.symbols}", json_out=True))

    rows_map, datasets, stats, backtests, svgs = {}, {}, {}, {}, []
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        try:
            rows, meta = kline(sym)
        except Exception as e:
            print(t("fetch_fail", sym=sym, e=e), file=sys.stderr)
            continue
        rows_map[sym] = rows
        datasets[sym] = meta
        stats[sym] = stats_block(rows, sym)
        backtests[sym] = sma_cross_backtest(rows)
        svgs.append(svg_chart(rows, sym, meta))

    computed = json.dumps({"stats": stats, "backtests": backtests}, ensure_ascii=False, indent=1, default=str)
    findings = llm(t("interpret_prompt"),
                   f"Research question: {args.question}\nPlan: {json.dumps(plan, ensure_ascii=False)}\n"
                   f"Symbols covered: {list(rows_map)}\nComputed results:\n{computed}")

    html = ("<!doctype html><meta charset=utf-8><title>dsh-vibe-trading</title>"
            "<body style='font-family:monospace;max-width:760px;margin:20px auto'>"
            f"<h3>{args.question}</h3><p>plan: {plan.get('plan', '')}</p>"
            + "".join(f"<div>{s}</div>" for s in svgs)
            + f"<h4>findings</h4><div style='white-space:pre-wrap'>{findings}</div>"
            + f"<hr><small>{t('computed_line', date=dt.date.today())}</small></body>")

    print(t("question", q=args.question) + "\n")
    print(f"{t('plan')}: {plan.get('plan')}\n")
    print(t("computed") + "\n")
    oos_notes = set()
    for sym, st in stats.items():
        above = st["above_sma60"]
        print(t("sym_line", sym=sym, last=f(st["last"], "{:.2f}"), ret20=f(st["ret20"], "{:+.1%}"),
                ret60=f(st["ret60"], "{:+.1%}"),
                above=t("above_yes") if above is True else (t("above_no") if above is False else f(above, "{}")),
                vol30=f(st["vol30"], "{:.0%}"), dd=f(st["dd_from_120d_peak"], "{:+.1%}"),
                vz=f(st["vol_z20"], "{:+.1f}")))
        print(t("src_line", src=src_text(datasets[sym])))
        bt = backtests[sym]
        print(t("bt_line", trades=bt["trades"], wr=f(bt["win_rate"], "{:.0%}"),
                sumret=f(bt["sum_strategy"], "{:+.1%}"), bh=f(bt["buy_hold_260d"], "{:+.1%}")))
        for seg_key, seg_str in (("train", "bt_train"), ("holdout", "bt_hold")):
            seg = bt[seg_key]
            span = "→".join(x for x in seg["span"] if x)
            print(t(seg_str, span=span, trades=seg["trades"],
                    sumret=f(seg["sum_strategy"], "{:+.1%}"), bh=f(seg["buy_hold"], "{:+.1%}")))
        oos_notes.add(bt["oos_note"])
    for note in oos_notes:
        print(t("oos_note_line", note=note))
    print(f"\n{t('findings')}\n\n{findings}\n")
    print(t("footer", secs=int(time.time() - t0)))

    if args.save:
        os.makedirs(TRAILS, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        base = os.path.join(TRAILS, stamp)
        open(base + ".html", "w").write(html)
        json.dump({"schema": "research-trail/1", "question": args.question, "plan": plan,
                   "datasets": datasets, "stats": stats,
                   "backtests": backtests, "findings": findings},
                  open(base + ".json", "w"), ensure_ascii=False, indent=1, default=str)
        print(t("saved", base=base), file=sys.stderr)


if __name__ == "__main__":
    main()
