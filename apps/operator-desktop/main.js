/**
 * Electron main: launch gating and Finish/Settings call sageo.operator.
 * Ready-check is bridge-only (no parallel checkout/import validation).
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
  // Prefer saved interpreter; fall back to bootstrap for resolve-launch.
  const config = loadConfig(cfgPath);
  const interpreter =
    (config && config.interpreter) || bootstrapPython();
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

ipcMain.handle("operator:list-runs-empty", async () => {
  // #164: empty Run list chrome only; listing ships with later tickets.
  return [];
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
