# ROADMAP — dsh-vibe-trading

North star: the third block of the three-repo family, same playbook as
[dsh-TradingAgents](https://github.com/vicfei/dsh-TradingAgents) /
[dsh-ai-hedge-fund](https://github.com/vicfei/dsh-ai-hedge-fund):
**100–300★ in 30 days**, riding the HKUDS/Vibe-Trading (38.5k★) search gravity.

## Positioning discipline (this repo's own)

Upstream Vibe-Trading is itself an MCP server — **the plugin must win on deep
integration**: orchestrated research loop, deterministic compute layer (numbers
from code), interactive cards, auditable trail. Any release that degenerates
into "MCP call wrapper" forfeits its reason to exist (the README table says so).

**Competitive read (2026-11-19 deep-dive, issue #1)**: the incumbent is not
just big — its honesty engineering (grounding registry, versioned research
artifacts, unavailable-not-zero, out-of-sample discipline, source-metadata
disclosure) is converging on our soul. Response: **win the governance depth
lane, never the breadth lane**. Explicitly renounced: broker connectors,
desktop app, IM channels, 19-broker matrices. Four clean-room idea adoptions
(ideas, not code — upstream is MIT but family discipline is net-room):
versioned artifacts + revision diff, unavailable ≠ 0 ≠ empty-set semantics,
train→freeze→holdout OOS discipline, data-source metadata riding with every
dataset.

## Star strategy (shared with the other two repos)

1. Name = traffic: keep `Vibe-Trading` full name; npm `dsh-vibe-trading` locked (0.0.1 live).
2. Keyword matrix: vibe-trading, deepseek-harness, dsh, quant-research, factor,
   interactive-charts, technical-analysis, ic-memo, research-trail.
3. Hook: the **6-second real-data demo** ("question in, research pack out") —
   the SVG card is post-ready; the revision-diff demo (V2) becomes hook #2.
4. Channels: three-repo same-day combo, cross-links; this repo's asset =
   interactive-card screenshot vs a raw-MCP conversation.
5. awesome-dsh submission after npm 0.1.0 (family queue: #16227 / #16447 / #16751 precedent).

## Milestones

### M0 · Engine smoke ✅ (2026-11-16)
LLM plans → deterministic layer (K-lines / stats / SMA-cross backtest /
inline SVG) → LLM interprets with [F#] field citations and small-sample
self-exposure. Real data 6s per run (茅台 vs 上证), trail HTML+JSON on disk.

### V1 · Release train + engine hardening → npm 0.1.0 (next session)
- [ ] V1.1 EN-first: engine output English default + `--lang zh` fallback;
      README pure EN + `README.zh-CN.md` translation (international-first rule)
- [ ] V1.2 honest-unavailable semantics: every stat/backtest field is
      `{value | unavailable + reason}` (insufficient sample / missing data /
      non-finite) — never 0, never silently dropped; trail records the reasons
- [ ] V1.3 source metadata rides: each dataset carries
      {source, symbols, date_range, adjustment, fetched_at, coverage gaps},
      rendered on card + trail (the "calibers ride" DNA, data edition —
      cross-links the dsh-WrenAI discipline)
- [ ] V1.4 out-of-sample discipline: mini backtest splits train/holdout —
      parameters selected on train only, frozen, holdout reported separately
      with an explicit in-sample vs out-of-sample line
- [ ] V1.5 npm 0.1.0 release train: root package + bin shim + dsh.bundle +
      skill + hermetic tests + CI (the dsh-WrenAI kit pattern); owner publish;
      awesome-dsh submission

### V2 · Versioned research artifacts → npm 0.2.0 (the counter-moat)
- [ ] trail promoted to first-class artifact: named, dated; question + evidence
      fields + conclusion + source metadata; `vibe save / list / show / diff /
      export` (JSON + Markdown)
- [ ] revisions: re-ask with new evidence → new revision, any two revisions
      diffable (content, evidence, conclusion) — "research that outlives the
      chat, in open files you own"
- [ ] artifact search across trails (question / symbol / date)

### V3 · Workbench (0.3.x)
- [ ] cross-sectional screener: multi-symbol momentum / volatility / volume
      anomaly boards (deterministic ranking, same [F#] citation discipline)
- [ ] indicator library: MACD / RSI / correlation matrix (+ northbound flow if
      reachable key-free)
- [ ] multi-question session: continuous follow-ups, one accumulating trail
- [ ] DSH Web canvas card (dsh-plugin-canvas precedent) + cordis typed tools

### V4 · Factor workshop (0.4.x)
- [ ] factor DSL: expression → deterministic compute; quick IC backtest with
      walk-forward (OOS discipline inherited from V1.4)
- [ ] family interop: one-key send a trail to dsh-TradingAgents as the
      committee's evidence pack (IC-MEMO feeding); dsh-ai-hedge-fund persona
      valuation consumes the same trail

### V5 · Ecosystem (0.5.x)
- [ ] RESEARCH-TRAIL spec (IC-MEMO's sister file): format versioned, stdlib
      validator, CI enforcement — third family interchange format
- [ ] searchable question history as an asset — persisted into a WeKnora
      knowledge base via the family bridge pattern (zero bespoke storage)
- [ ] monthly incumbent digest: track upstream releases, documented idea
      intake (compete with a notebook, not vibes)

## Discipline (non-negotiable)

- Numbers come only from the deterministic layer; findings cite [F#] fields;
  insufficient samples must self-expose; unavailable is never rendered as 0.
- No advice (interpret structure, don't call direction); SVG cards stay
  zero-dependency (no CDN).
- Trails are append-only — revisions add, never rewrite.
