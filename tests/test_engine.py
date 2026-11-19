#!/usr/bin/env python3
"""Hermetic engine tests — no LLM, no network. Synthetic klines only.
Run: python3 tests/test_engine.py   (exits non-zero on any FAIL)"""
import datetime as dt
import math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import market_data as md
import vibe_research as vr

FAILS = []


def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        FAILS.append(name)


def synth(n=320, base=100.0, amp=0.15, period=60, vol=1000.0):
    """sine-wave prices → guaranteed SMA20/60 crossings; contiguous daily dates"""
    rows, d = [], dt.date(2025, 1, 1)
    for i in range(n):
        price = base * (1 + amp * math.sin(2 * math.pi * i / period))
        rows.append((d.isoformat(), price * 0.99, price, price * 1.01, price * 0.98,
                     vol + (i % 7) * 50))
        d += dt.timedelta(days=1)
    return rows


rows = synth()
c = md.closes(rows)

# 1. stats_block full window: numeric fields present and finite
st = md.stats_block(rows, "t")
for k in ("last", "ret20", "ret60", "vol30", "dd_from_120d_peak", "vol_z20"):
    v = st[k]
    check("stats %s numeric" % k, isinstance(v, (int, float)) and math.isfinite(v))
check("above_sma60 is bool", isinstance(st["above_sma60"], bool))

# 2. honest-unavailable on short windows
st30 = md.stats_block(rows[:30], "t")
check("ret60 unavailable with reason", isinstance(st30["ret60"], dict) and "61" in st30["ret60"]["unavailable"])
check("dd unavailable with reason", isinstance(st30["dd_from_120d_peak"], dict) and "121" in st30["dd_from_120d_peak"]["unavailable"])
check("sma60 posture unavailable", isinstance(st30["above_sma60"], dict))

# 3. win-rate honesty: small samples unavailable
check("win_rate <10 trades unavailable", isinstance(md._win_rate([0.1] * 4), dict)
      and "4 trades < 10" in md._win_rate([0.1] * 4)["unavailable"])
check("win_rate >=10 trades numeric", md._win_rate([0.1] * 9 + [-0.2]) == 0.9)

# 4. backtest: structure + OOS discipline + compounding regression (M0 bug)
bt = md.sma_cross_backtest(rows)
check("backtest has train/holdout", "train" in bt and "holdout" in bt)
check("oos note states a priori", "a priori" in bt["oos_note"] and "does not select" in bt["oos_note"])
check("sine wave produces trades", bt["trades"] >= 2)
if bt["trade_returns"]:
    expected = math.prod(1 + r for r in bt["trade_returns"]) - 1
    check("compounding = prod(1+r)-1 (M0 regression)", abs(bt["sum_strategy"] - expected) < 1e-9)
    check("compounding != sum(1+r)-1 artifact", abs(bt["sum_strategy"] - (sum(1 + r for r in bt["trade_returns"]) - 1)) > 1e-6)
spans = bt["train"]["span"] + bt["holdout"]["span"]
check("segment spans populated", all(spans))
check("train+holdout trades == total", bt["train"]["trades"] + bt["holdout"]["trades"] == bt["trades"])

# 5. coverage gaps: >10 calendar-day jumps reported, contiguous not
check("no gaps on contiguous series", md.coverage_gaps(rows) == [])
gappy = [r for r in rows[:100]] + [r for r in rows[110:]]
g = md.coverage_gaps(gappy)
check("11-day jump detected", len(g) == 1 and g[0]["calendar_days"] == 11)

# 6. renderer + i18n safety
check("f() renders unavailable", vr.f({"unavailable": "why so"}, "{:+.1%}") == "n/a (why so)")
check("f() renders number", vr.f(0.156, "{:+.1%}") == "+15.6%")
try:
    vr.t("plan_prompt")
    check("t() never formats prompts (JSON braces safe)", True)
except (KeyError, IndexError, ValueError):
    check("t() never formats prompts (JSON braces safe)", False)
for lang in ("en", "zh"):
    vr.LANG = lang
    check("bt_train renders in %s" % lang, "a→b" in vr.t("bt_train", span="a→b", trades=1, sumret="+1%", bh="+2%"))
vr.LANG = "en"

# 7. SVG card carries the source metadata line
meta = {"source": "t", "adjustment": "qfq", "date_range": ["a", "b"], "bars": 3, "requested_bars": 4, "coverage_gaps": []}
svg = md.svg_chart(rows, "t", meta)
check("svg carries source line", "source t · qfq" in svg and "3/4 bars" in svg)

# 8. versioned artifacts: append-only revisions + deterministic diff (V2)
import tempfile
import artifacts as art
with tempfile.TemporaryDirectory() as td:
    os.environ["VIBE_TRAILS_DIR"] = td
    try:
        base_trail = {"schema": "research-trail/1", "question": "q1", "plan": {"plan": "p"},
                      "datasets": {"sym": {"source": "t", "adjustment": "qfq", "date_range": ["a", "b"],
                                           "bars": 10, "requested_bars": 320, "coverage_gaps": []}},
                      "stats": {"sym": {"label": "sym", "last": 100.0, "ret20": 0.05,
                                        "ret60": {"unavailable": "needs >= 61 closes, got 30"},
                                        "above_sma60": True, "vol30": 0.2,
                                        "dd_from_120d_peak": -0.1, "vol_z20": 0.5}},
                      "backtests": {"sym": {"trades": 2, "sum_strategy": 0.1, "win_rate": {"unavailable": "2 trades < 10 minimum"},
                                            "buy_hold_260d": 0.05, "trade_returns": [0.05, 0.05],
                                            "train": {}, "holdout": {}, "oos_note": "apriori"}},
                      "findings": "same findings text", "_html": "<html>r1</html>"}
        rev1, _ = art.save("Demo Kit", dict(base_trail))
        import copy
        t2 = copy.deepcopy(base_trail)
        t2["stats"]["sym"]["ret20"] = 0.08
        t2["stats"]["sym"]["ret60"] = 0.20
        t2["backtests"]["sym"]["trades"] = 3
        t2["backtests"]["sym"]["sum_strategy"] = 0.12
        t2["findings"] = "rewritten findings"
        t2["_html"] = "<html>r2</html>"
        rev2, _ = art.save("Demo Kit", t2)
        check("revisions append 1,2", (rev1, rev2) == (1, 2))
        _, ta = art.load("demo-kit", 1)
        check("append-only: r1 unchanged", ta["stats"]["sym"]["ret20"] == 0.05
              and isinstance(ta["stats"]["sym"]["ret60"], dict)
              and "_html" not in ta)
        d = art.diff_trails(ta, art.load("demo-kit", 2)[1])
        check("diff: numeric delta", "ret20: " in d and "Δ" in d)
        check("diff: became available", "became available" in d)
        check("diff: backtest trades", "backtest.trades" in d and "2 → 3" in d)
        check("diff: findings rewritten note", "findings rewritten" in d)
        listed = art.list_artifacts()
        check("list shows demo-kit r2", listed and listed[0]["name"] == "demo-kit" and listed[0]["revisions"] == 2)
        meta2, tb = art.load("demo-kit", 2)
        md_out = art.export_markdown(meta2, tb)
        check("export markdown carries revision", "revision r2" in md_out and "not investment advice" in md_out)
    finally:
        os.environ.pop("VIBE_TRAILS_DIR", None)

print("result:", "GREEN" if not FAILS else "RED (%d)" % len(FAILS))
sys.exit(1 if FAILS else 0)
