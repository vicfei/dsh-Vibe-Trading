# Changelog

## 0.3.0 (2026-11-19) — first real release: workbench complete

The V1–V3 line ships as one release (0.1.0/0.2.0 were internal development
versions, never published; the registry jumps 0.0.1 → 0.3.0).

### Engine hardening (V1)
- English-first output with `--lang zh` fallback (family rule); the
  interpreter states which parts of the question the results do NOT answer.
- **Honest-unavailable semantics**: every computed field is a number or
  `{"unavailable": reason}` — never a fake 0; win rate requires ≥10 trades.
- **Source metadata rides** with every dataset (source / adjustment /
  date-range / bars / coverage gaps >10d) — terminal brief, SVG card, trail.
- **Out-of-sample discipline**: SMA20/60 mini backtest splits trades by exit
  date into train/holdout (70/30) with frozen a-priori parameters.
- Rigor-pass bug fix: M0's `sum(1+r)-1` compounding artifact (+283.8%
  displayed where the true compounded return was −15.6%) → `math.prod(1+r)-1`.
- US history degraded upstream (tencent endpoint returns boundary bars only);
  degenerate series are refused honestly instead of computed on.

### Versioned research artifacts (V2)
- Named append-only artifacts: `--name` appends rN+1 and never rewrites;
  `artifacts list|show|diff|export`; deterministic field-level diff (numeric
  deltas, unavailable↔available transitions, findings similarity);
  self-contained markdown export.

### Workbench (V3)
- `scan` boards: momentum / volatility / volume rankings + 60d
  correlation-matrix board — zero LLM calls, unavailable ranks last.
- Indicator library: MACD(12,26,9), Wilder RSI(14), pairwise correlation.
- `chat` sessions: one data fetch, many questions (follow-ups interpret on
  the cached computed layer, one LLM call each); `/data /refresh /save /quit`;
  sessions replay via `artifacts show`.
- Typed DSH host tools (`vibe_research`, `vibe_scan`) via
  @deepseek-ai/dsh-tools — verified on the real host shape.

### Packaging
- npm package with bin shim + DSH bundle manifest + skill; hermetic test
  suite (35 checks) + CI (tests, shim, syntax, publish dry-run).

## 0.0.1 (2026-11-17)
Name-reserving placeholder.
