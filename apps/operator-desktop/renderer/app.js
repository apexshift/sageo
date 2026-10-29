/* Renderer: wizard vs shell chrome. No Run submit in #164. */

const wizardView = document.getElementById("view-wizard");
const shellView = document.getElementById("view-shell");
const wizardErrors = document.getElementById("wizard-errors");
const settingsErrors = document.getElementById("settings-errors");
const runList = document.getElementById("run-list");
const stageEmpty = document.getElementById("stage-empty");
const stageNewRun = document.getElementById("stage-new-run");
const stageSettings = document.getElementById("stage-settings");

let currentConfig = null;

function show(el) {
  el.classList.remove("hidden");
}

function hide(el) {
  el.classList.add("hidden");
}

function renderErrors(node, errors) {
  node.innerHTML = "";
  for (const err of errors || []) {
    const li = document.createElement("li");
    li.textContent = err;
    node.appendChild(li);
  }
}

function setStage(name) {
  hide(stageEmpty);
  hide(stageNewRun);
  hide(stageSettings);
  if (name === "empty") show(stageEmpty);
  if (name === "new-run") show(stageNewRun);
  if (name === "settings") show(stageSettings);
}

function fillRuntimeForm(prefix, config) {
  const checkout = document.getElementById(`${prefix}checkout_root`);
  const interpreter = document.getElementById(`${prefix}interpreter`);
  const runs = document.getElementById(`${prefix}runs_root`);
  if (!config) {
    checkout.value = "";
    interpreter.value = "";
    runs.value = "";
    return;
  }
  checkout.value = config.checkout_root || "";
  interpreter.value = config.interpreter || "";
  runs.value = config.runs_root || "";
}

function showWizard(decision) {
  hide(shellView);
  show(wizardView);
  currentConfig = decision.config;
  fillRuntimeForm("", decision.config);
  renderErrors(wizardErrors, decision.errors || []);
}

async function showShell(decision) {
  hide(wizardView);
  show(shellView);
  currentConfig = decision.config;
  fillRuntimeForm("settings_", decision.config);
  const runs = (await window.sageoOperator.listRuns()) || [];
  runList.innerHTML = "";
  for (const row of runs) {
    const li = document.createElement("li");
    li.textContent = row.goal || row.run_id;
    runList.appendChild(li);
  }
  setStage("empty");
}

async function boot() {
  const decision = await window.sageoOperator.getLaunch();
  if (decision.view === "shell") {
    await showShell(decision);
  } else {
    showWizard(decision);
  }
}

document.getElementById("runtime-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const fields = {
    checkout_root: document.getElementById("checkout_root").value,
    interpreter: document.getElementById("interpreter").value,
    runs_root: document.getElementById("runs_root").value,
  };
  const decision = await window.sageoOperator.finishWizard(fields);
  if (decision.view === "shell") {
    await showShell(decision);
  } else {
    showWizard(decision);
  }
});

document.getElementById("settings-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const fields = {
    checkout_root: document.getElementById("settings_checkout_root").value,
    interpreter: document.getElementById("settings_interpreter").value,
    runs_root: document.getElementById("settings_runs_root").value,
  };
  const decision = await window.sageoOperator.saveSettings(fields);
  renderErrors(settingsErrors, decision.errors || []);
  if (decision.view === "shell") {
    currentConfig = decision.config;
    fillRuntimeForm("settings_", decision.config);
  }
});

document.getElementById("new-run-btn").addEventListener("click", () => setStage("new-run"));
document.getElementById("empty-new-run-btn").addEventListener("click", () => setStage("new-run"));
document.getElementById("settings-btn").addEventListener("click", () => {
  fillRuntimeForm("settings_", currentConfig);
  setStage("settings");
});

boot();
