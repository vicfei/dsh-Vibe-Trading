---
name: dsh-vibe-trading
description: Interactive trading research workbench (Vibe-Trading style) for DeepSeek Harness — orchestrated plan→data→compute→explain loop, numbers from a deterministic layer only, honest-unavailable semantics, OOS backtest discipline, screener boards, versioned research artifacts, zero-dependency SVG chart cards.
---

Use this skill when asked a market/quant research question ("which leg is
weaker", "price-volume structure", "compare X and Y", "rank these symbols",
"this position's trend"). The loop is a deterministic script — you orchestrate,
it computes. Requires python3 on PATH (stdlib only); LLM key read from
`DEEPSEEK_API_KEY` in ~/.bashrc.

## Run

```bash
dsh-vibe-trading run --question "Moutai vs the index: whose price-volume structure is weaker?" \
  --symbols sh600519,sh000001 --name moutai-vs-index
dsh-vibe-trading run --question "<问题>" --symbols sh600519,sh000001 --lang zh   # Chinese fallback
dsh-vibe-trading scan --symbols sh600519,sz000001,sh000001 --board momentum     # deterministic board
dsh-vibe-trading chat --symbols sh600519,sh000001 --name my-session             # multi-question REPL
dsh-vibe-trading artifacts list / show <name> / diff <name> 1 2 / export <name> # versioned trails
```

Symbols: A-share `sh`/`sz`+code, index `sh000001`; US history is degraded
upstream and refused honestly. Data rides with source metadata (tencent-ifzq,
qfq, date range, coverage gaps). Host tools `vibe_research` / `vibe_scan` are
registered for agent presets.

## Discipline

- Numbers only from the compute layer; findings must cite fields ([F#]); the model
  never invents figures. Small samples get flagged as small samples.
- Unavailable fields are reported as unavailable with a reason — never guessed
  around, never rendered as 0.
- Report "answered / still-missing" honestly — data gaps are part of the deliverable.
- The HTML card is self-contained SVG (no CDN) — safe to share/attach.
- Backtests are fee-free structural probes with in-sample/out-of-sample split;
  never present them as advice.
- Trails and artifact revisions are append-only evidence — never edit by hand.
