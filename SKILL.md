---
name: dsh-vibe-trading
description: Interactive trading research workbench (Vibe-Trading style) for DeepSeek Harness — orchestrated plan→data→compute→explain loop, numbers from a deterministic layer only, zero-dependency SVG chart cards, auditable research trails.
---

Use this skill when asked a market/quant research question ("谁更弱", "量价结构",
"对比 X 和 Y", "这个位置趋势怎么样"). The loop is a deterministic script —
you orchestrate, it computes.

## Run

```bash
KIT=<this-directory>
python3 $KIT/scripts/vibe_research.py --save --question "<question>" --symbols sh600519,sh000001
```

Symbols: A-share `sh600519`/`sz000001`, index `sh000001`, US `usNVDA`.

## Discipline

- Numbers only from the compute layer; findings must cite fields ([F#]); the model
  never invents figures. Small samples get flagged as small samples.
- Report "answered / still-missing" honestly — data gaps are part of the deliverable.
- The HTML card is self-contained SVG (no CDN) — safe to share/attach.
- Backtests are fee-free structural probes; never present them as advice.
