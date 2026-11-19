# PR body（提交 awesome-dsh-plugin 用——owner 发布 npm 0.3.0 后执行）

**Adds vicfei/dsh-Vibe-Trading — interactive trading research workbench, numbers from code (tools)**

One file added: `data/plugins/vicfei__dsh-Vibe-Trading--npm.yml`.

- Install: `dsh plugin add dsh-vibe-trading` (npm 0.3.0; declares `dsh.bundle`
  + `cordis.patch.yml`; skill `skills/dsh-vibe-trading/` + `dsh-vibe-trading`
  CLI spawning the stdlib-only Python engine + typed host tools
  `vibe_research` / `vibe_scan` via @deepseek-ai/dsh-tools)
- What it does: an orchestrated plan→data→compute→explain loop where **every
  number comes from the deterministic layer** — the LLM only interprets and
  cites computed fields. Honest-unavailable semantics (unavailable-with-reason,
  never a fake 0), source metadata riding on every dataset, out-of-sample
  backtest discipline, deterministic screener boards, multi-question sessions,
  and **versioned append-only research artifacts with revision diff** —
  research that outlives the chat, in open files the user owns.
- Real working code: 35 hermetic checks + CI green; typed tools verified on
  the real host shape; live smokes on real A-share data throughout development.
- Inspired by HKUDS/Vibe-Trading (MIT) — independent native re-implementation
  for DeepSeek Harness, zero upstream code. Not investment advice. Family:
  dsh-TradingAgents · dsh-ai-hedge-fund.

PR 执行命令（owner 在 npm 0.3.0 发布后跑）：

```bash
cd /tmp && git clone --depth 1 git@ssh.github.com:vicfei/awesome-dsh-plugin.git && cd awesome-dsh-plugin
git checkout -b add-dsh-vibe-trading
cp ~/dsh-vibe-trading/docs/marketplace-submission/vicfei__dsh-Vibe-Trading--npm.yml data/plugins/
git add data/plugins/vicfei__dsh-Vibe-Trading--npm.yml
git commit -m "Add vicfei/dsh-Vibe-Trading (interactive trading research workbench)"
git push -f origin add-dsh-vibe-trading
# 开 PR：base awesome-dsh-plugin/awesome-dsh-plugin ← vicfei:add-dsh-vibe-trading，body 用上文
```
