#!/usr/bin/env python3
"""Deterministic market layer: Tencent-ladder K-lines (A-shares/US/index),
indicators and the mini backtest in pure stdlib.

Honesty contract (V1.2/V1.3/V1.4):
- every computed field is a number/bool OR {"unavailable": reason} — never a
  fake 0, never silently dropped;
- every dataset carries a metadata envelope (source, range, adjustment,
  coverage gaps) that rides into cards and trails;
- the mini backtest reports train/holdout segments separately with frozen
  a-priori parameters (out-of-sample discipline).
"""
import datetime as dt
import json, math, urllib.request

MIN_TRADES_FOR_WIN_RATE = 10
GAP_DAYS = 10  # calendar-day jump above which a coverage gap is reported


def avail(value, requirement):
    """honest-unavailable wrapper: non-finite → {'unavailable': requirement}"""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return {"unavailable": requirement}
    return value


def coverage_gaps(rows, threshold=GAP_DAYS):
    """calendar-day jumps above threshold, reported as possible data holes"""
    gaps = []
    for i in range(1, len(rows)):
        a = dt.date.fromisoformat(rows[i - 1][0][:10])
        b = dt.date.fromisoformat(rows[i][0][:10])
        ndays = (b - a).days
        if ndays > threshold:
            gaps.append({"from": rows[i - 1][0], "to": rows[i][0], "calendar_days": ndays})
    return gaps


def kline(symbol):
    """symbol: sh600519 / sz000001 / sh000001(index) / usNVDA
    → (rows, meta): rows = [(date, open, close, high, low, volume)], meta rides with the data."""
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?param={symbol},day,,,320,qfq"
           if symbol.startswith("us") else
           f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,320,qfq")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=10).read())
    node = d["data"][symbol]
    days = node.get("qfqday") or node.get("day")
    rows = [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in days]
    if symbol.startswith("us") and len(rows) < 30:
        # known upstream limitation: the tencent US endpoint currently returns
        # only boundary bars for some tickers — fail honestly instead of
        # computing on a degenerate series
        raise ValueError(f"tencent US endpoint returned {len(rows)} bars for {symbol} "
                         "(boundary-only response; US history is degraded — tracked for a fallback source)")
    meta = {"source": "tencent-ifzq", "adjustment": "qfq (forward-adjusted)",
            "symbol": symbol, "bars": len(rows), "requested_bars": 320,
            "date_range": [rows[0][0], rows[-1][0]],
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "coverage_gaps": coverage_gaps(rows)}
    return rows, meta


def closes(rows):
    return [r[2] for r in rows]


def sma(xs, n):
    return [sum(xs[max(0, i - n + 1):i + 1]) / len(xs[max(0, i - n + 1):i + 1]) for i in range(len(xs))]


def ema(xs, n):
    """standard exponential moving average, seeded with the first value"""
    out, k = [], 2 / (n + 1)
    for i, x in enumerate(xs):
        out.append(x if i == 0 else x * k + out[-1] * (1 - k))
    return out


def macd(xs, fast=12, slow=26, signal=9):
    """→ (macd_line, signal_line, histogram); last-bar values are what stats carry"""
    line = [a - b for a, b in zip(ema(xs, fast), ema(xs, slow))]
    sig = ema(line, signal)
    return line, sig, [a - b for a, b in zip(line, sig)]


def rsi(xs, n=14):
    """Wilder-smoothed RSI → last value"""
    if len(xs) < n + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(xs)):
        ch = xs[i] - xs[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
    if al == 0:
        return 100.0
    rs = ag / al
    return 100 - 100 / (1 + rs)


def pearson(a, b):
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((x - mb) ** 2 for x in b) ** 0.5
    return num / (da * db) if da and db else None


def daily_returns(c):
    return [c[i] / c[i - 1] - 1 for i in range(1, len(c))]


def corr_matrix(closes_by_sym, window=60):
    """pairwise correlation of the last `window` daily returns (aligned by tail)"""
    rets = {s: daily_returns(c)[-window:] for s, c in closes_by_sym.items()}
    out = {}
    for a in rets:
        out[a] = {}
        for b in rets:
            if a == b:
                out[a][b] = 1.0
            else:
                n = min(len(rets[a]), len(rets[b]))
                out[a][b] = avail(pearson(rets[a][-n:], rets[b][-n:]),
                                  f"fewer than 2 aligned returns")
    return out


def rank_syms(stats, key):
    """rank symbols by key, descending; unavailable ranks last — never dropped.
    Deterministic: ties break alphabetically."""
    def rk(item):
        v = item[1].get(key)
        return (1, "", 0.0) if isinstance(v, dict) else (0, "", -float(v))
    return [s for s, _ in sorted(stats.items(), key=lambda it: (rk(it)[0], rk(it)[2], it[0]))]


def stats_block(rows, label):
    c = closes(rows)
    n = len(c)

    def need(minimum, fn):
        if n < minimum:
            return {"unavailable": f"needs >= {minimum} closes, got {n}"}
        return avail(fn(), "non-finite result")

    s60 = sma(c, 60)
    vols = [r[5] for r in rows]
    mean20 = sum(vols[-20:]) / 20 if n >= 20 else None
    vz = ((vols[-1] - mean20) / ((sum((v - mean20) ** 2 for v in vols[-20:]) / 20) ** 0.5 + 1e-9)
          if mean20 is not None else None)
    return {"label": label,
            "last": avail(c[-1], "no closes"),
            "ret20": need(21, lambda: c[-1] / c[-21] - 1),
            "ret60": need(61, lambda: c[-1] / c[-61] - 1),
            "above_sma60": (c[-1] > s60[-1]) if n >= 60 else {"unavailable": f"needs >= 60 closes for SMA60, got {n}"},
            "vol30": need(31, lambda: (sum((c[i] / c[i - 1] - 1) ** 2 for i in range(-30, 0)) / 30) ** 0.5 * math.sqrt(252)),
            "dd_from_120d_peak": need(121, lambda: c[-1] / max(c[-120:]) - 1),
            "vol_z20": need(21, lambda: vz),
            "macd_hist": need(35, lambda: macd(c)[2][-1]),
            "rsi14": need(15, lambda: avail(rsi(c, 14), "non-finite RSI"))}


def _win_rate(rets):
    if len(rets) < MIN_TRADES_FOR_WIN_RATE:
        return {"unavailable": f"{len(rets)} trades < {MIN_TRADES_FOR_WIN_RATE} minimum"}
    return sum(1 for r in rets if r > 0) / len(rets)


def sma_cross_backtest(rows, train_frac=0.7):
    """SMA20/60 golden/death cross mini backtest (full-position, no fees — a
    structure probe). Out-of-sample discipline: trades are split by exit date
    into a train segment and a holdout segment; parameters are fixed a priori
    (no selection is performed), so the holdout confirms rather than selects."""
    c = closes(rows)
    s20, s60 = sma(c, 20), sma(c, 60)
    split = int(len(c) * train_frac)
    pos, entry, trades = 0, None, 0
    trade_rets, exit_idx = [], []
    for i in range(60, len(c)):
        if pos == 0 and s20[i] > s60[i] and s20[i - 1] <= s60[i - 1]:
            pos, entry, trades = 1, c[i], trades + 1
        elif pos == 1 and s20[i] < s60[i] and s20[i - 1] >= s60[i - 1]:
            trade_rets.append(c[i] / entry - 1); exit_idx.append(i); pos = 0
    if pos == 1:
        trade_rets.append(c[-1] / entry - 1); exit_idx.append(len(c) - 1)

    def seg(rets_idx_pairs):
        rets = [r for r, _ in rets_idx_pairs]
        return {"trades": len(rets),
                "win_rate": _win_rate(rets),
                "sum_strategy": (math.prod(1 + r for r in rets) - 1) if rets else 0.0}

    train_pairs = [(r, i) for r, i in zip(trade_rets, exit_idx) if i < split]
    hold_pairs = [(r, i) for r, i in zip(trade_rets, exit_idx) if i >= split]
    train = seg(train_pairs); hold = seg(hold_pairs)
    train["buy_hold"] = c[split - 1] / c[60] - 1 if len(c) > split > 60 else {"unavailable": "window too short"}
    hold["buy_hold"] = c[-1] / c[split] - 1 if len(c) > split > 60 else {"unavailable": "window too short"}
    train["span"] = [rows[60][0] if len(rows) > 60 else None, rows[split - 1][0]]
    hold["span"] = [rows[split][0], rows[-1][0]]
    return {"trades": trades,
            "win_rate": _win_rate(trade_rets),
            "trade_returns": trade_rets,
            "sum_strategy": (math.prod(1 + r for r in trade_rets) - 1) if trade_rets else 0.0,
            "buy_hold_260d": c[-1] / c[60] - 1 if len(c) > 60 else {"unavailable": "window too short"},
            "train": train, "holdout": hold,
            "oos_note": "parameters fixed a priori (SMA20/60; no selection performed) — "
                        "the holdout segment confirms, it does not select"}


def svg_chart(rows, title, meta=None, w=720, h=260):
    """Zero-dependency inline SVG: close line + SMA20/60 + volume bars,
    with the data-source metadata line riding along (V1.3)."""
    c = closes(rows)
    s20, s60 = sma(c, 20), sma(c, 60)
    vols = [r[5] for r in rows]
    n = len(c)
    lo, hi = min(min(c), min(s60[60:])) * 0.99, max(c) * 1.01
    def X(i): return 40 + i * (w - 60) / (n - 1)
    def Y(v): return 20 + (hi - v) * (h - 80) / (hi - lo)
    path = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(c))
    p20 = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s20) if not math.isnan(v))
    p60 = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s60) if not math.isnan(v))
    vmax = max(vols) + 1e-9
    bars = "".join(f'<rect x="{X(i)-1:.1f}" y="{h-30-vols[i]/vmax*40:.1f}" width="2" height="{vols[i]/vmax*40:.1f}" fill="#8aa" opacity="0.5"/>' for i in range(n))
    if meta:
        src = (f"source {meta['source']} · {meta['adjustment']} · {meta['date_range'][0]} → {meta['date_range'][1]} "
               f"· {meta['bars']}/{meta['requested_bars']} bars"
               + (f" · {len(meta['coverage_gaps'])} coverage gap(s)" if meta.get("coverage_gaps") else " · no gaps"))
    else:
        src = ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="monospace">'
            f'<text x="10" y="14" font-size="12">{title} · last {c[-1]:.2f}</text>'
            f'<polyline points="{path}" fill="none" stroke="#2456c4" stroke-width="1.5"/>'
            f'<polyline points="{p20}" fill="none" stroke="#e6a23c" stroke-width="1"/>'
            f'<polyline points="{p60}" fill="none" stroke="#c23531" stroke-width="1"/>'
            f'{bars}'
            f'<text x="10" y="{h-18}" font-size="10" fill="#567">{src}</text>'
            f'<text x="10" y="{h-6}" font-size="10" fill="#567">blue=close orange=SMA20 red=SMA60 bars=volume · {n} days</text></svg>')
