#!/usr/bin/env python3
"""确定性行情层：腾讯通道拉 K 线（A股/美股/指数），指标与迷你回测纯 numpy。"""
import json, math, urllib.request


def kline(symbol):
    """symbol: sh600519 / sz000001 / sh000001(指数) / usNVDA → [(date, open, close, high, low, volume)]"""
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?param={symbol},day,,,320,qfq"
           if symbol.startswith("us") else
           f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,320,qfq")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=10).read())
    node = d["data"][symbol]
    days = node.get("qfqday") or node.get("day")
    return [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in days]


def closes(rows):
    return [r[2] for r in rows]


def sma(xs, n):
    return [sum(xs[max(0, i - n + 1):i + 1]) / len(xs[max(0, i - n + 1):i + 1]) for i in range(len(xs))]


def stats_block(rows, label):
    c = closes(rows)
    ret20 = c[-1] / c[-21] - 1
    ret60 = c[-1] / c[-61] - 1 if len(c) > 61 else float("nan")
    s60 = sma(c, 60)
    vol30 = (sum((c[i] / c[i - 1] - 1) ** 2 for i in range(-30, 0)) / 30) ** 0.5 * math.sqrt(252)
    peak = max(c[-120:])
    dd = c[-1] / peak - 1
    vols = [r[5] for r in rows]
    vz = (vols[-1] - sum(vols[-20:]) / 20) / ((sum((v - sum(vols[-20:]) / 20) ** 2 for v in vols[-20:]) / 20) ** 0.5 + 1e-9)
    return {"label": label, "last": c[-1], "ret20": ret20, "ret60": ret60,
            "above_sma60": c[-1] > s60[-1], "vol30": vol30, "dd_from_120d_peak": dd, "vol_z20": vz}


def sma_cross_backtest(rows):
    """SMA20/SMA60 金叉死叉迷你回测（全仓进出，无费率，揭示趋势结构用）。"""
    c = closes(rows)
    s20, s60 = sma(c, 20), sma(c, 60)
    pos, entry, trades, rets = 0, None, 0, []
    for i in range(60, len(c)):
        if pos == 0 and s20[i] > s60[i] and s20[i - 1] <= s60[i - 1]:
            pos, entry, trades = 1, c[i], trades + 1
        elif pos == 1 and s20[i] < s60[i] and s20[i - 1] >= s60[i - 1]:
            rets.append(c[i] / entry - 1); pos = 0
    if pos == 1:
        rets.append(c[-1] / entry - 1)
    bh = c[-1] / c[60] - 1
    return {"trades": trades, "win_rate": (sum(1 for r in rets if r > 0) / len(rets)) if rets else None,
            "sum_strategy": sum(1 + r for r in rets) - 1 if rets else 0.0, "buy_hold_260d": bh}


def svg_chart(rows, title, w=720, h=260):
    """零依赖内联 SVG：收盘线 + SMA20/60 + 成交量条。"""
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
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="monospace">'
            f'<text x="10" y="14" font-size="12">{title} · last {c[-1]:.2f}</text>'
            f'<polyline points="{path}" fill="none" stroke="#2456c4" stroke-width="1.5"/>'
            f'<polyline points="{p20}" fill="none" stroke="#e6a23c" stroke-width="1"/>'
            f'<polyline points="{p60}" fill="none" stroke="#c23531" stroke-width="1"/>'
            f'{bars}'
            f'<text x="10" y="{h-6}" font-size="10" fill="#567">blue=close orange=SMA20 red=SMA60 bars=volume · {rows[0][0]} → {rows[-1][0]} · {n} days</text></svg>')
