const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("sageoOperator", {
  getLaunch: () => ipcRenderer.invoke("operator:get-launch"),
  finishWizard: (fields) => ipcRenderer.invoke("operator:finish-wizard", fields),
  saveSettings: (fields) => ipcRenderer.invoke("operator:save-settings", fields),
  listRuns: () => ipcRenderer.invoke("operator:list-runs"),
  startThinAudit: (fields) =>
    ipcRenderer.invoke("operator:start-thin-audit", fields),
  getProgress: (runId) => ipcRenderer.invoke("operator:get-progress", runId),
});
