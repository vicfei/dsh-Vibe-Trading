#!/usr/bin/env python3
"""dsh-vibe-trading v0 — 交互式投研工作台（Vibe-Trading 式，DSH 原生）

结构致敬 HKUDS/Vibe-Trading，DSH 原生化差异点：
- **研究循环编排**（规划→取数→计算→解读）是一个确定性脚本，不是一串手工 MCP 调用；
- **数字全部出自确定性计算层**（LLM 只解读，不产数）——证据纪律延续委员会家族；
- 产出三件套：终端纪要 + 零依赖内联 SVG 交互卡 + 可审计研究轨迹（question/plan/
  data/computations/findings 全留档）。

管线（2 次 DeepSeek 调用/场，temperature=0）：
  LLM 规划探索 → 确定性层（K线/指标/迷你回测/SVG） → LLM 解读（只引用计算结果）

用法：
  python3 scripts/vibe_research.py --question "茅台 vs 大盘：量价结构谁更弱？" --symbols sh600519,sh000001
"""
import argparse, datetime as dt, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_data import kline, stats_block, sma_cross_backtest, svg_chart

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAILS = os.path.join(KIT, "trails")


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
        raise SystemExit(f"LLM 调用失败: {r.stdout[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--symbols", required=True, help="逗号分隔，如 sh600519,sh000001")
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()
    t0 = time.time()

    plan = llm(
        "你是投研规划员。给定研究问题与可用符号（A股 sh/sz+代码、指数 sh000001、美股 us+代码），"
        "输出 JSON {\"plan\":\"不超过4步的探索路径\",\"focus\":\"每个符号各看什么\"}。只规划，不结论。",
        f"问题：{args.question}\n符号：{args.symbols}", json_out=True)
    import re as _re
    try:
        plan = json.loads(plan)
    except json.JSONDecodeError:
        plan = json.loads(_re.sub(r"^```(json)?|```$", "", plan.strip(), flags=re.M).strip())

    rows_map, stats, backtests, svgs = {}, {}, {}, []
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        try:
            rows = kline(sym)
        except Exception as e:
            print(f"⚠ {sym} 取数失败: {e}", file=sys.stderr)
            continue
        rows_map[sym] = rows
        stats[sym] = stats_block(rows, sym)
        backtests[sym] = sma_cross_backtest(rows)
        svgs.append(svg_chart(rows, sym))

    computed = json.dumps({"stats": stats, "backtests": backtests}, ensure_ascii=False, indent=1, default=str)
    findings = llm(
        "你是投研解读员。纪律：**只允许引用给定的计算结果**（[S#] 引用 stats/backtests 字段），"
        "禁止编造任何数字；每个结论一条 [F#]。指出计算结果回答了问题的哪部分、哪部分仍缺数据。"
        "输出 markdown，不超过 8 条结论。",
        f"研究问题：{args.question}\n规划：{json.dumps(plan, ensure_ascii=False)}\n"
        f"符号覆盖：{list(rows_map)}\n计算结果：\n{computed}")

    html = ("<!doctype html><meta charset=utf-8><title>dsh-vibe-trading</title>"
            "<body style='font-family:monospace;max-width:760px;margin:20px auto'>"
            f"<h3>{args.question}</h3><p>plan: {plan.get('plan', '')}</p>"
            + "".join(f"<div>{s}</div>" for s in svgs)
            + "<h4>findings</h4><div style='white-space:pre-wrap'>" + findings + "</div>"
            + f"<hr><small>computed {dt.date.today()} · deepseek-chat · temperature=0 · 非投资建议</small></body>")

    print(f"## 研究问题：{args.question}\n\n**plan**：{plan.get('plan')}\n")
    for s in svgs:
        pass  # SVG 卡在 HTML 里，终端只给纪要
    print("## 计算结果（摘要）\n")
    for sym, st in stats.items():
        print(f"- **{sym}**: 现价 {st['last']:.2f} · 20日 {st['ret20']:+.1%} · 60日 {st['ret60']:+.1%} · "
              f"{'站稳' if st['above_sma60'] else '跌破'}SMA60 · 30日波动 {st['vol30']:.0%} · "
              f"距120日峰 {st['dd_from_120d_peak']:+.1%} · 量能z {st['vol_z20']:+.1f}")
        bt = backtests[sym]
        print(f"  - 趋势回测(20/60金叉,全仓无费): {bt['trades']} 笔 · 胜率 {bt['win_rate'] if bt['win_rate'] is not None else '—'} · "
              f"策略累计 {bt['sum_strategy']:+.1%} vs 持有 {bt['buy_hold_260d']:+.1%}")
    print(f"\n## 解读\n\n{findings}\n")
    print(f"── SVG 交互卡与研究轨迹已生成（--save 落盘）· 耗时 {time.time()-t0:.0f}s")

    if args.save:
        os.makedirs(TRAILS, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        base = os.path.join(TRAILS, f"{stamp}")
        open(base + ".html", "w").write(html)
        json.dump({"question": args.question, "plan": plan, "stats": stats,
                   "backtests": backtests, "findings": findings},
                  open(base + ".json", "w"), ensure_ascii=False, indent=1, default=str)
        print(f"→ {base}.html / .json", file=sys.stderr)


if __name__ == "__main__":
    main()
