/**
 * Main-process runtime helpers (hermetic without Electron).
 * Ready-check always goes through `python -m sageo.operator` (bridge).
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

function configPath(appLike) {
  const root = appLike.userDataPath || (appLike.getPath && appLike.getPath("userData"));
  return path.join(root, "runtime.json");
}

function loadConfig(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
    if (!data || typeof data !== "object") return null;
    if (!data.checkout_root || !data.interpreter) return null;
    return {
      checkout_root: String(data.checkout_root),
      interpreter: String(data.interpreter),
      runs_root: data.runs_root ? String(data.runs_root) : null,
    };
  } catch {
    return null;
  }
}

function saveConfig(filePath, config) {
  const payload = {
    checkout_root: config.checkout_root,
    interpreter: config.interpreter,
  };
  if (config.runs_root) payload.runs_root = config.runs_root;
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function runOperatorCommand(interpreter, args) {
  const completed = spawnSync(interpreter, ["-m", "sageo.operator", ...args], {
    encoding: "utf8",
    env: process.env,
  });
  let payload = {
    view: "wizard",
    errors: ["operator bridge command failed"],
    config: null,
    ready: null,
  };
  const stdout = (completed.stdout || "").trim();
  if (stdout) {
    try {
      payload = JSON.parse(stdout);
    } catch (err) {
      payload = {
        view: "wizard",
        errors: [`invalid bridge JSON: ${err.message}`],
        config: null,
        ready: null,
      };
    }
  } else if (completed.error) {
    payload = {
      view: "wizard",
      errors: [`interpreter spawn failed: ${completed.error.message}`],
      config: null,
      ready: null,
    };
  } else if (completed.stderr) {
    payload = {
      view: "wizard",
      errors: [String(completed.stderr).trim()],
      config: null,
      ready: null,
    };
  }
  return { status: completed.status, payload };
}

module.exports = {
  configPath,
  loadConfig,
  saveConfig,
  runOperatorCommand,
};
