---
name: dsh-vibe-trading
description: Interactive trading research workbench for DeepSeek Harness — orchestrated plan→data→compute→explain loop; numbers only from the deterministic layer with honest-unavailable semantics, source metadata riding on every dataset, out-of-sample backtest discipline, zero-dependency SVG cards, auditable research trails.
---

Use this skill when asked a market/quant research question ("which leg is
weaker", "price-volume structure", "compare X and Y", "how is the trend at
this level"). The loop is a deterministic script — you orchestrate, it
computes. `dsh-vibe-trading` must be on PATH (installed with the package;
requires python3, stdlib only). LLM key: the engine reads `DEEPSEEK_API_KEY`
from ~/.bashrc export lines.

## Run

```bash
dsh-vibe-trading --question "Moutai vs the index: whose price-volume structure is weaker?" \
  --symbols sh600519,sh000001 --save
dsh-vibe-trading --question "<问题>" --symbols sh600519,sh000001 --lang zh   # Chinese fallback
```

Symbols: A-shares `sh`/`sz`+code, index `sh000001`, US `us`+code. Data rides
with source metadata (tencent-ifzq, qfq, date range, coverage gaps).

## Discipline

- Numbers come only from the deterministic layer; findings must cite [S#]/[F#]
  fields; unavailable fields are reported as unavailable — never guessed around.
- Backtests are structure probes (no fees, frozen a-priori params, in-sample vs
  out-of-sample reported separately) — not advice.
- Trails are append-only evidence; never edit a saved trail by hand.
