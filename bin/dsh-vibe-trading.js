#!/usr/bin/env node
// dsh-vibe-trading CLI shim — spawns the stdlib-only Python engine with args passed through.
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const engine = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "scripts", "vibe_research.py");
const args = process.argv.slice(2);
const candidates = process.platform === "win32" ? ["python", "python3"] : ["python3", "python"];

for (const py of candidates) {
  const r = spawnSync(py, [engine, ...args], { stdio: "inherit" });
  if (!r.error) process.exit(r.status ?? 1);
}
console.error("dsh-vibe-trading: python3 not found on PATH (the engine is stdlib-only Python 3, no pip installs needed)");
process.exit(127);
