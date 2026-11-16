# dsh-vibe-trading — interactive trading research, natively on DeepSeek Harness

**Ask a market question → a deterministic pipeline plans, pulls data, computes, and
explains — every number from code, every finding tagged to its computation.
You get a terminal brief, a zero-dependency SVG chart card, and an auditable trail.**
**提一个行情问题 → 确定性管道规划、取数、计算、解读——数字全部出自代码，
结论逐条挂靠计算字段。终端纪要 + 零依赖 SVG 交互卡 + 可审计研究轨迹。**

[![DeepSeek Harness](https://img.shields.io/badge/DSH-plugin-4E6DD4)](https://github.com/deepseek-ai) [![License: MIT](https://img.shields.io/badge/license-MIT-3da639)](LICENSE)

> Inspired by [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) —
> restructured as a native DeepSeek Harness experience. Not affiliated; independent
> community project. Family: [dsh-TradingAgents](https://github.com/vicfei/dsh-TradingAgents)
> (bull/bear committee) · [dsh-ai-hedge-fund](https://github.com/vicfei/dsh-ai-hedge-fund) (persona fund).

## Why a plugin (Vibe-Trading ships an MCP server — isn't `mcp.json` enough?)

| | raw Vibe-Trading MCP in DSH | **dsh-vibe-trading** |
|---|---|---|
| Interaction | you drive tool calls per step | **the research loop is orchestrated** — plan → data → compute → explain in one command |
| Numbers | produced inside model-driven calls | **deterministic compute layer** — LLM only interprets, cites fields `[F#]`, invents nothing |
| Artifact | chat text | **terminal brief + inline-SVG chart card + full trail** (question/plan/stats/backtests/findings) |
| Auditability | — | every finding points at the computation that produced it; gaps stated honestly |

## Quick start (zero extra keys)

```bash
git clone https://github.com/vicfei/dsh-vibe-trading && cd dsh-vibe-trading
python3 scripts/vibe_research.py --save \
  --question "茅台 vs 上证指数：近 20 日谁更弱，量价结构给出什么信号？" \
  --symbols sh600519,sh000001
```

Real smoke run (2026-11-16, 6s, 2 LLM calls, temperature=0): identified the index as
the weaker leg (ret20 −3.44% vs +9.73%), flagged “缩量上行 vs 缩量下行” structure,
and **honestly declined to lean on the 4-trade backtest sample** — findings cite
their computation fields throughout. Open `trails/*.html` for the chart card.

## What's in the box

- A-share / index / US K-lines via the CN-reachable Tencent ladder (no keys)
- Stats: ret20/60, SMA60 posture, 30d vol, drawdown from 120d peak, volume z-score
- Mini trend backtest (SMA20/60 cross, position-only, fees excluded — structure probe, not advice)
- Zero-dependency inline SVG chart cards (offline-safe, no CDN)
- Auditable trail JSON + the family evidence discipline (numbers from code, LLM interprets)

## Status & roadmap

v0 engine smoke-tested on real data. See [ROADMAP](ROADMAP.md) — M1 adds the
deterministic screener & factor library, the DSH Web canvas card integration,
and the cordis plugin form (`dsh plugin add dsh-vibe-trading`).

## Credits & disclaimer

Inspired by HKUDS/Vibe-Trading — independent native re-implementation, MIT.
**Not investment advice.** Backtests are structural probes with fees excluded.
