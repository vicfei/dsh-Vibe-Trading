/**
 * dsh-vibe-trading host plugin (V3.4): the research workbench as typed tools.
 *
 * Registers two agent tools on `ctx.tools` via @deepseek-ai/dsh-tools:
 *   vibe_research — plan → data → compute → interpret on real market data;
 *                   numbers only from the deterministic layer, honest-unavailable
 *                   semantics, source metadata rides, OOS backtest discipline
 *   vibe_scan     — deterministic cross-sectional board (momentum / volatility /
 *                   volume / correlation), zero LLM calls
 *
 * The tools spawn the bundled Python engine (stdlib only). Trails and cards
 * land under the calling process's cwd (./trails/), exactly like the CLI.
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineTool } from "@deepseek-ai/dsh-tools";

export const name = "vibe-trading";
export const inject = ["tools"];

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function run(args, timeoutMs = 300_000) {
  const r = spawnSync("python3", [path.join(ROOT, "scripts", "vibe_research.py"), ...args],
                      { encoding: "utf8", timeout: timeoutMs, maxBuffer: 16 * 1024 * 1024 });
  if (r.error) throw new Error(`vibe-trading: ${r.error.message}`);
  if (r.status !== 0) throw new Error(`vibe-trading exited ${r.status}: ${(r.stderr || "").slice(-400)}`);
  return (r.stdout || "").trim();
}

const LANG = { type: "string", enum: ["en", "zh"], description: "Output language (default en)." };

export async function apply(ctx) {
  ctx.tools.register(defineTool({
    name: "vibe_research",
    description:
      "Interactive market research with an orchestrated loop: plan → data → deterministic compute → interpret. " +
      "Every number comes from the deterministic layer (the LLM only interprets and must cite computed fields); " +
      "fields that cannot be computed render as unavailable with a reason, never as 0; each dataset's source " +
      "metadata (source/adjustment/range/coverage gaps) rides with the result; the SMA20/60 mini backtest reports " +
      "in-sample and out-of-sample segments with frozen a-priori parameters. A-share and index symbols via the " +
      "key-free Tencent ladder (sh600519, sz000001, sh000001); US history is currently degraded upstream and is " +
      "refused honestly. Output: terminal brief + auditable trail JSON + zero-dependency SVG card under ./trails/. " +
      "Not investment advice.",
    parameters: {
      question: { type: "string", required: true, description: "Research question, e.g. 'Moutai vs the index: whose price-volume structure is weaker?'" },
      symbols: { type: "string", required: true, description: "Comma-separated symbols, e.g. 'sh600519,sh000001'." },
      name: { type: "string", description: "Save as a named versioned artifact (appends a revision) instead of an anonymous timestamped trail." },
      lang: LANG,
    },
    output: {
      schema: { type: "object", additionalProperties: false,
                properties: { summary: { type: "string", required: true } } },
      render: (_args, value) => [{ type: "text", text: value.summary }],
    },
    execute(args) {
      const extra = ["--save", ...(args.name ? ["--name", args.name] : []),
                     ...(args.lang ? ["--lang", args.lang] : [])];
      return { summary: run(["run", "--question", args.question, "--symbols", args.symbols, ...extra]) };
    },
  }));

  ctx.tools.register(defineTool({
    name: "vibe_scan",
    description:
      "Deterministic cross-sectional board over multiple symbols — zero LLM calls, numbers from code only. " +
      "Boards: momentum (ret20), volatility (30d annualized), volume (20d z-score), correlation (60d pairwise " +
      "return-correlation matrix). Unavailable values rank last and show their reason, never dropped. Optionally " +
      "saved as a versioned artifact. Not investment advice.",
    parameters: {
      symbols: { type: "string", required: true, description: "Comma-separated symbols, e.g. 'sh600519,sz000001,sh000001'." },
      board: { type: "string", required: true, enum: ["momentum", "volatility", "volume", "correlation"] },
      name: { type: "string", description: "Save as a named versioned artifact." },
      lang: LANG,
    },
    output: {
      schema: { type: "object", additionalProperties: false,
                properties: { summary: { type: "string", required: true } } },
      render: (_args, value) => [{ type: "text", text: value.summary }],
    },
    execute(args) {
      const extra = [...(args.name ? ["--name", args.name] : []),
                     ...(args.lang ? ["--lang", args.lang] : [])];
      return { summary: run(["scan", "--symbols", args.symbols, "--board", args.board, ...extra]) };
    },
  }));
}
