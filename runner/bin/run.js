#!/usr/bin/env node
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Parse --config JSON
function parseConfigArg(argv) {
  const i = argv.indexOf("--config");
  if (i !== -1 && argv[i + 1]) {
    try { return JSON.parse(argv[i + 1]); } catch (e) {
      console.error("[mcp-service-registry] Invalid --config JSON:", e.message);
      process.exit(1);
    }
  }
  return {};
}

function isExec(p) {
  try { return p && fs.existsSync(p) && fs.statSync(p).isFile(); } catch { return false; }
}

// Resolve a usable Python binary
function resolvePython() {
  // 1) Explicit override
  const override = process.env.PYTHON_BIN;
  if (isExec(override)) return override;

  // 2) Virtualenv
  const venv = process.env.VIRTUAL_ENV;
  if (venv) {
    const pyVenv = path.join(venv, "bin", "python");
    if (isExec(pyVenv)) return pyVenv;
    const pyVenv3 = path.join(venv, "bin", "python3");
    if (isExec(pyVenv3)) return pyVenv3;
  }

  // 3) Common macOS locations
  const candidates = [
    "/opt/homebrew/bin/python3",      // Homebrew Apple Silicon
    "/usr/local/bin/python3",         // Homebrew Intel
    "/usr/bin/python3",               // System Python
  ];

  for (const c of candidates) if (isExec(c)) return c;

  // 4) Fallback to PATH lookups
  // Using `command -v` through a shell to find python3 or python
  const which = async (cmd) => {
      try {
          const {spawnSync} = await import("node:child_process");
          const out = spawnSync("bash", ["-lc", `command -v ${cmd} || true`], {encoding: "utf8"});
          const p = out.stdout.trim();
          return isExec(p) ? p : null;
      } catch {
          return null;
      }
  };
  // Top preference is python3
  // Note: top-level await is not allowed here, so return null and handle outside if needed
  return null;
}

const cfg = parseConfigArg(process.argv);

// Defaults + overrides
const host  = cfg.host  || process.env.SERVICE_REGISTRY_HOST || "127.0.0.1";
const port  = Number(cfg.port || process.env.SERVICE_REGISTRY_PORT || 7001);
const debug = Boolean(cfg.debug ?? (process.env.SERVICE_REGISTRY_DEBUG || "").toLowerCase() === "true");

// Optional Perplexity passthrough
if (cfg.perplexityApiKey) process.env.PERPLEXITY_API_KEY = cfg.perplexityApiKey;
if (cfg.perplexityModel) process.env.PERPLEXITY_MODEL = cfg.perplexityModel;

// Repo root two levels up from this file
const repoRoot = path.resolve(__dirname, "..", "..");

// Env for Python app
const env = {
  ...process.env,
  SERVICE_REGISTRY_HOST: String(host),
  SERVICE_REGISTRY_PORT: String(port),
  SERVICE_REGISTRY_DEBUG: String(debug),
  PYTHONPATH: [repoRoot, process.env.PYTHONPATH || ""].filter(Boolean).join(path.delimiter),
};

// Resolve Python synchronously
let PY_BIN = process.env.PYTHON_BIN || null;

// venv or common paths
if (!PY_BIN) {
  const venv = process.env.VIRTUAL_ENV;
  const tries = [
    venv ? path.join(venv, "bin", "python") : null,
    venv ? path.join(venv, "bin", "python3") : null,
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
    "/usr/bin/python3",
  ].filter(Boolean);
  PY_BIN = tries.find(isExec) || null;
}

// Final guard
if (!PY_BIN) {
  console.error("ERROR: Python interpreter not found.");
  console.error("Quick fixes:");
  console.error("  1) Install Homebrew Python:   brew install python");
  console.error("  2) Or set an explicit path:   export PYTHON_BIN=/opt/homebrew/bin/python3");
  process.exit(127);
}

console.log(`[mcp-service-registry] Using Python: ${PY_BIN}`);
console.log(`[mcp-service-registry] Starting ServiceRegistry at http://${host}:${port}/mcp`);

const child = spawn(
  PY_BIN,
  ["-m", "registry.service_registry_server"],   // run as module so `import core...` resolves with cwd + PYTHONPATH
  { stdio: "inherit", env, cwd: repoRoot }
);

["SIGINT", "SIGTERM"].forEach(sig => process.on(sig, () => { try { child.kill(sig); } catch {} }));
child.on("exit", code => process.exit(code ?? 0));