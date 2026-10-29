/**
 * Electron main: launch gating, New Run Start, Progress via sageo.operator.
 * Ready-check and Start go through the bridge (no parallel validation).
 */
const { app, BrowserWindow, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");

const { configPath, loadConfig, runOperatorCommand } = require("./runtime");

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 720,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, "renderer", "index.html"));
  return win;
}

function bootstrapPython() {
  return process.env.SAGEO_BOOTSTRAP_PYTHON || process.env.PYTHON || "python3";
}

function activeInterpreter() {
  const cfgPath = configPath(app);
  const config = loadConfig(cfgPath);
  return (config && config.interpreter) || bootstrapPython();
}

function activeConfig() {
  return loadConfig(configPath(app));
}

function runsRootFor(config) {
  if (!config) return null;
  if (config.runs_root && String(config.runs_root).trim()) {
    return String(config.runs_root).trim();
  }
  return path.join(config.checkout_root, "runs");
}

function finishOrSaveArgs(cfgPath, fields) {
  const interpreter =
    String(fields.interpreter || "").trim() || bootstrapPython();
  const args = [
    "finish-wizard",
    "--config-path",
    cfgPath,
    "--checkout-root",
    String(fields.checkout_root || ""),
    "--interpreter",
    interpreter,
  ];
  if (fields.runs_root && String(fields.runs_root).trim()) {
    args.push("--runs-root", String(fields.runs_root).trim());
  }
  return { interpreter, args };
}

ipcMain.handle("operator:get-launch", async () => {
  const cfgPath = configPath(app);
  if (!fs.existsSync(cfgPath)) {
    return {
      view: "wizard",
      errors: ["runtime config missing or invalid"],
      config: null,
      ready: null,
    };
  }
  const config = loadConfig(cfgPath);
  const interpreter = (config && config.interpreter) || bootstrapPython();
  return runOperatorCommand(interpreter, [
    "resolve-launch",
    "--config-path",
    cfgPath,
  ]).payload;
});

ipcMain.handle("operator:finish-wizard", async (_event, fields) => {
  const cfgPath = configPath(app);
  const { interpreter, args } = finishOrSaveArgs(cfgPath, fields);
  return runOperatorCommand(interpreter, args).payload;
});

ipcMain.handle("operator:save-settings", async (_event, fields) => {
  const cfgPath = configPath(app);
  const { interpreter, args } = finishOrSaveArgs(cfgPath, fields);
  return runOperatorCommand(interpreter, args).payload;
});

ipcMain.handle("operator:list-runs", async () => {
  const config = activeConfig();
  const runsRoot = runsRootFor(config);
  if (!runsRoot) return [];
  const result = runOperatorCommand(activeInterpreter(), [
    "list-runs",
    "--runs-root",
    runsRoot,
  ]);
  return Array.isArray(result.payload) ? result.payload : [];
});

ipcMain.handle("operator:start-thin-audit", async (_event, fields) => {
  const config = activeConfig();
  if (!config) {
    return {
      ok: false,
      errors: ["runtime config missing or invalid"],
      warnings: [],
    };
  }
  const runsRoot = runsRootFor(config);
  const args = [
    "start-thin-audit",
    "--checkout-root",
    config.checkout_root,
    "--runs-root",
    runsRoot,
    "--site-url",
    String(fields.site_url || ""),
    "--reach",
    String(fields.reach || "national"),
  ];
  if (fields.goal && String(fields.goal).trim()) {
    args.push("--goal", String(fields.goal).trim());
  }
  if (fields.gsc_property && String(fields.gsc_property).trim()) {
    args.push("--gsc-property", String(fields.gsc_property).trim());
  }
  if (fields.ga4_property && String(fields.ga4_property).trim()) {
    args.push("--ga4-property", String(fields.ga4_property).trim());
  }
  const result = runOperatorCommand(activeInterpreter(), args);
  if (!result.payload || !result.payload.run_id) {
    return {
      ok: false,
      errors: result.payload.errors || ["start-thin-audit failed"],
      warnings: [],
      payload: result.payload,
    };
  }
  return { ok: true, errors: [], ...result.payload };
});

ipcMain.handle("operator:get-progress", async (_event, runId) => {
  const config = activeConfig();
  const runsRoot = runsRootFor(config);
  if (!runsRoot || !runId) return null;
  return runOperatorCommand(activeInterpreter(), [
    "get-progress",
    "--runs-root",
    runsRoot,
    "--run-id",
    String(runId),
  ]).payload;
});

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
