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
import market_data as md
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
        "sym_line": "- **{sym}**: last {last} · 20d {ret20} · 60d {ret60} · {above} SMA60 · 30d vol {vol30} · from 120d peak {dd} · volume z {vz} · RSI14 {rsi} · MACD-h {macdh}",
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
        "sym_line": "- **{sym}**: 现价 {last} · 20日 {ret20} · 60日 {ret60} · {above} SMA60 · 30日波动 {vol30} · 距120日峰 {dd} · 量能z {vz} · RSI14 {rsi} · MACD-h {macdh}",
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


def run_research(question, symbols_csv):
    """plan → deterministic layer → interpret. Returns the full trail dict (+_html)."""
    t0 = time.time()
    plan = parse_json_loose(llm(t("plan_prompt"),
                                f"Question: {question}\nSymbols: {symbols_csv}", json_out=True))
    rows_map, datasets, stats, backtests, svgs = {}, {}, {}, {}, []
    for sym in [s.strip() for s in symbols_csv.split(",") if s.strip()]:
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
    if not rows_map:
        raise SystemExit("no symbol data fetched — nothing to research")
    computed = json.dumps({"stats": stats, "backtests": backtests}, ensure_ascii=False, indent=1, default=str)
    findings = llm(t("interpret_prompt"),
                   f"Research question: {question}\nPlan: {json.dumps(plan, ensure_ascii=False)}\n"
                   f"Symbols covered: {list(rows_map)}\nComputed results:\n{computed}")
    html = ("<!doctype html><meta charset=utf-8><title>dsh-vibe-trading</title>"
            "<body style='font-family:monospace;max-width:760px;margin:20px auto'>"
            f"<h3>{question}</h3><p>plan: {plan.get('plan', '')}</p>"
            + "".join(f"<div>{s}</div>" for s in svgs)
            + f"<h4>findings</h4><div style='white-space:pre-wrap'>{findings}</div>"
            + f"<hr><small>{t('computed_line', date=dt.date.today())}</small></body>")
    return {"schema": "research-trail/1", "question": question, "plan": plan,
            "datasets": datasets, "stats": stats, "backtests": backtests,
            "findings": findings, "secs": int(time.time() - t0), "_html": html}


BOARDS = {"momentum": "ret20", "volatility": "vol30", "volume": "vol_z20"}


def run_scan(symbols_csv, board):
    """Deterministic cross-sectional scan — zero LLM calls."""
    t0 = time.time()
    stats, datasets, closes_map = {}, {}, {}
    for sym in [s.strip() for s in symbols_csv.split(",") if s.strip()]:
        try:
            rows, meta = kline(sym)
        except Exception as e:
            print(t("fetch_fail", sym=sym, e=e), file=sys.stderr)
            continue
        stats[sym] = stats_block(rows, sym)
        datasets[sym] = meta
        closes_map[sym] = md.closes(rows)
    if not stats:
        raise SystemExit("no symbol data fetched — nothing to scan")
    trail = {"schema": "research-trail/1", "question": f"scan:{board} over {symbols_csv}",
             "plan": {"plan": "deterministic scan — no LLM calls, numbers from code only"},
             "datasets": datasets, "stats": stats, "backtests": {}, "findings": "",
             "board": board, "secs": int(time.time() - t0)}
    if board == "correlation":
        trail["correlation"] = md.corr_matrix(closes_map, 60)
    else:
        trail["board_ranking"] = md.rank_syms(stats, BOARDS[board])
    return trail


def render_board(trail):
    board = trail.get("board")
    if not board:
        return
    print(f"\n## board: {board} · deterministic ranking · unavailable ranks last\n")
    stats = trail.get("stats", {})
    if board == "correlation":
        cm = trail.get("correlation", {})
        syms = list(cm)
        print("| | " + " | ".join(syms) + " |")
        print("|---|" + "---|" * len(syms))
        for a in syms:
            print(f"| **{a}** | " + " | ".join(f(cm[a].get(b), "{:+.2f}") for b in syms) + " |")
    else:
        key = BOARDS[board]
        ranked = trail.get("board_ranking") or list(stats)
        print(f"| rank | symbol | {key} (board key) | ret20 | vol30 | vol_z20 | rsi14 |")
        print("|---|---|---|---|---|---|---|")
        for i, sym in enumerate(ranked, 1):
            st = stats[sym]
            print(f"| {i} | {sym} | {f(st.get(key), '{:+.4g}')} | {f(st.get('ret20'), '{:+.1%}')} "
                  f"| {f(st.get('vol30'), '{:.0%}')} | {f(st.get('vol_z20'), '{:+.1f}')} "
                  f"| {f(st.get('rsi14'), '{:.0f}')} |")


def render_brief(trail):
    """Terminal brief, live runs and stored revisions alike."""
    print(t("question", q=trail.get("question", "")) + "\n")
    print(f"{t('plan')}: {trail.get('plan', {}).get('plan', '')}\n")
    print(t("computed") + "\n")
    oos_notes = set()
    for sym, st in trail.get("stats", {}).items():
        above = st["above_sma60"]
        print(t("sym_line", sym=sym, last=f(st["last"], "{:.2f}"), ret20=f(st["ret20"], "{:+.1%}"),
                ret60=f(st["ret60"], "{:+.1%}"),
                above=t("above_yes") if above is True else (t("above_no") if above is False else f(above, "{}")),
                vol30=f(st["vol30"], "{:.0%}"), dd=f(st["dd_from_120d_peak"], "{:+.1%}"),
                vz=f(st["vol_z20"], "{:+.1f}"), rsi=f(st.get("rsi14", {"unavailable": "n/a"}), "{:.0f}"),
                macdh=f(st.get("macd_hist", {"unavailable": "n/a"}), "{:+.2f}")))
        if sym in trail.get("datasets", {}):
            print(t("src_line", src=src_text(trail["datasets"][sym])))
        bt = trail.get("backtests", {}).get(sym)
        if bt:
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
    if trail.get("board"):
        render_board(trail)
    print(f"\n{t('findings')}\n\n{trail.get('findings', '')}\n" if trail.get("findings") else "")
    art = trail.get("artifact")
    if art:
        print(f"── artifact {art['name']} · r{art['rev']} · saved {art['saved_at']}")
    secs = trail.get("secs")
    if trail.get("board"):
        print(f"── scan · {secs}s · deterministic, zero LLM calls · numbers from code only")
    elif secs is not None:
        print(t("footer", secs=secs))


def main():
    global LANG
    argv = sys.argv[1:]
    if argv[:1] not in (["run"], ["artifacts"], ["scan"], ["chat"]) and argv:
        argv = ["run"] + argv
    ap = argparse.ArgumentParser(prog="dsh-vibe-trading")
    sub = ap.add_subparsers(dest="cmd")
    run = sub.add_parser("run", help="plan → data → compute → interpret (legacy flag surface)")
    run.add_argument("--question", required=True)
    run.add_argument("--symbols", required=True, help="comma-separated, e.g. sh600519,sh000001")
    run.add_argument("--name", help="save as a named versioned artifact (appends a new revision)")
    run.add_argument("--save", action="store_true", help="save an anonymous timestamped trail")
    run.add_argument("--lang", choices=("en", "zh"), default="en",
                     help="output language (default en; zh is the fallback)")
    scan = sub.add_parser("scan", help="deterministic cross-sectional board (no LLM calls)")
    scan.add_argument("--symbols", required=True)
    scan.add_argument("--board", required=True, choices=sorted(list(BOARDS) + ["correlation"]))
    scan.add_argument("--name", help="save as a named versioned artifact")
    scan.add_argument("--lang", choices=("en", "zh"), default="en")
    art = sub.add_parser("artifacts", help="versioned research artifacts (append-only)")
    asub = art.add_subparsers(dest="action", required=True)
    asub.add_parser("list")
    sh = asub.add_parser("show")
    sh.add_argument("name")
    sh.add_argument("-r", type=int, default=None, help="revision (default: latest)")
    df = asub.add_parser("diff")
    df.add_argument("name")
    df.add_argument("r1", type=int)
    df.add_argument("r2", type=int)
    ex = asub.add_parser("export")
    ex.add_argument("name")
    ex.add_argument("-r", type=int, default=None, help="revision (default: latest)")
    ex.add_argument("--stdout", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "scan":
        LANG = args.lang
        trail = run_scan(args.symbols, args.board)
        render_brief(trail)
        if args.name:
            import artifacts
            rev, base = artifacts.save(args.name, trail)
            print(t("saved", base=base) + f" (artifact {artifacts.slugify(args.name)} r{rev})", file=sys.stderr)
        return

    if args.cmd == "artifacts":
        import artifacts
        if args.action == "list":
            rows = artifacts.list_artifacts()
            if not rows:
                print("no artifacts yet — run with --name <slug> to create one")
            for r in rows:
                print(f"{r['name']}\tr{r['revisions']}\t{r['last_at']}\t{r['question'][:60]}")
        elif args.action == "show":
            meta, trail = artifacts.load(args.name, args.r)
            render_brief(trail)
        elif args.action == "diff":
            _, a = artifacts.load(args.name, args.r1)
            _, b = artifacts.load(args.name, args.r2)
            print(f"## diff {args.name}: r{args.r1} → r{args.r2}\n")
            print(artifacts.diff_trails(a, b))
        elif args.action == "export":
            meta, trail = artifacts.load(args.name, args.r)
            md = artifacts.export_markdown(meta, trail)
            if args.stdout:
                print(md)
            else:
                out = f"{meta['name']}-r{trail.get('artifact', {}).get('rev', 'x')}.md"
                open(out, "w").write(md)
                print(f"→ {out}", file=sys.stderr)
        return

    LANG = args.lang
    trail = run_research(args.question, args.symbols)
    render_brief(trail)
    if args.name:
        import artifacts
        rev, base = artifacts.save(args.name, trail)
        print(t("saved", base=base) + f" (artifact {artifacts.slugify(args.name)} r{rev})", file=sys.stderr)
    elif args.save:
        os.makedirs(TRAILS, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        base = os.path.join(TRAILS, stamp)
        open(base + ".html", "w").write(trail["_html"])
        json.dump({k: v for k, v in trail.items() if not k.startswith("_")},
                  open(base + ".json", "w"), ensure_ascii=False, indent=1, default=str)
        print(t("saved", base=base), file=sys.stderr)


if __name__ == "__main__":
    main()
