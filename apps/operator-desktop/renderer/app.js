/* Renderer: wizard, New Run → Progress → Findings → Review. */

const wizardView = document.getElementById("view-wizard");
const shellView = document.getElementById("view-shell");
const wizardErrors = document.getElementById("wizard-errors");
const settingsErrors = document.getElementById("settings-errors");
const runList = document.getElementById("run-list");
const stageEmpty = document.getElementById("stage-empty");
const stageNewRun = document.getElementById("stage-new-run");
const stageProgress = document.getElementById("stage-progress");
const stageFindings = document.getElementById("stage-findings");
const stageReview = document.getElementById("stage-review");
const stageSettings = document.getElementById("stage-settings");
const progressGate = document.getElementById("progress-gate");
const progressAgents = document.getElementById("progress-agents");
const progressWarnings = document.getElementById("progress-warnings");
const goToReviewBtn = document.getElementById("go-to-review-btn");
const goToFindingsBtn = document.getElementById("go-to-findings-btn");
const progressIdle = document.getElementById("progress-idle");
const newRunWarnings = document.getElementById("new-run-warnings");
const newRunErrors = document.getElementById("new-run-errors");
const findingsList = document.getElementById("findings-list");
const findingsDetail = document.getElementById("findings-detail");
const filterConfidence = document.getElementById("filter-confidence");
const filterAgent = document.getElementById("filter-agent");
const reviewEmpty = document.getElementById("review-empty");
const reviewBody = document.getElementById("review-body");
const reviewPaused = document.getElementById("review-paused");
const reviewDecision = document.getElementById("review-decision");
const reviewEvidenceLinks = document.getElementById("review-evidence-links");
const operatorNote = document.getElementById("operator-note");
const reviewResult = document.getElementById("review-result");

let currentConfig = null;
let selectedRunId = null;
let selectedFindingId = null;
let progressTimer = null;
let lastStartWarnings = [];
let cachedFindings = [];

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
  hide(stageProgress);
  hide(stageFindings);
  hide(stageReview);
  hide(stageSettings);
  if (name === "empty") show(stageEmpty);
  if (name === "new-run") show(stageNewRun);
  if (name === "progress") show(stageProgress);
  if (name === "findings") show(stageFindings);
  if (name === "review") show(stageReview);
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
  stopProgressWatch();
  hide(shellView);
  show(wizardView);
  currentConfig = decision.config;
  fillRuntimeForm("", decision.config);
  renderErrors(wizardErrors, decision.errors || []);
}

function statusBadge(status) {
  const span = document.createElement("span");
  span.className = `badge badge-${status || "unknown"}`;
  span.textContent = status || "unknown";
  return span;
}

function confidenceBadge(row) {
  const span = document.createElement("span");
  if (row.is_nhv) {
    span.className = "badge badge-nhv";
    span.textContent = "NHV";
  } else {
    span.className = `badge badge-conf-${row.confidence || "unknown"}`;
    span.textContent = row.confidence || "unknown";
  }
  return span;
}

async function refreshSidebar(selectId) {
  const runs = (await window.sageoOperator.listRuns()) || [];
  runList.innerHTML = "";
  for (const row of runs) {
    const li = document.createElement("li");
    li.className = "run-row";
    if (row.run_id === selectId) li.classList.add("selected");
    li.dataset.runId = row.run_id;
    const title = document.createElement("div");
    title.className = "run-title";
    title.textContent = row.goal || row.run_id;
    const meta = document.createElement("div");
    meta.className = "run-meta";
    meta.textContent = [row.site_host, row.reach].filter(Boolean).join(" · ");
    li.appendChild(title);
    li.appendChild(meta);
    li.appendChild(statusBadge(row.status));
    li.addEventListener("click", () => openProgress(row.run_id));
    runList.appendChild(li);
  }
  return runs;
}

async function showShell(decision) {
  hide(wizardView);
  show(shellView);
  currentConfig = decision.config;
  fillRuntimeForm("settings_", decision.config);
  const runs = await refreshSidebar(selectedRunId);
  if (!runs.length) {
    selectedRunId = null;
    setStage("empty");
  } else if (selectedRunId) {
    await openProgress(selectedRunId);
  } else {
    setStage("empty");
  }
}

function renderProgress(snap) {
  if (!snap) return;
  renderErrors(progressWarnings, lastStartWarnings);
  progressGate.textContent = `gate_state: ${snap.gate_state}`;
  progressAgents.innerHTML = "";
  if (snap.empty_schedule) {
    const li = document.createElement("li");
    li.textContent = "No Agents scheduled (ask_human / empty).";
    progressAgents.appendChild(li);
  } else {
    for (const agent of snap.agents || []) {
      const li = document.createElement("li");
      li.textContent = `${agent.name} — ${agent.status}`;
      progressAgents.appendChild(li);
    }
  }
  if (snap.gate_state === "awaiting_approval" && snap.paused_agent) {
    goToReviewBtn.textContent = `Go to Review (${snap.paused_agent})`;
    show(goToReviewBtn);
    hide(progressIdle);
  } else {
    hide(goToReviewBtn);
    if (snap.gate_state === "closed") show(progressIdle);
    else hide(progressIdle);
  }
  const hasAgents = (snap.agents || []).some((a) => a.status === "completed");
  if (hasAgents || lastStartWarnings.length) {
    show(goToFindingsBtn);
  } else {
    hide(goToFindingsBtn);
  }
}

function stopProgressWatch() {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
}

function startProgressWatch(runId) {
  stopProgressWatch();
  const tick = async () => {
    const snap = await window.sageoOperator.getProgress(runId);
    renderProgress(snap);
    await refreshSidebar(runId);
    if (!snap || snap.gate_state === "closed") {
      stopProgressWatch();
    }
  };
  tick();
  progressTimer = setInterval(tick, 1000);
}

async function openProgress(runId, warnings) {
  selectedRunId = runId;
  if (warnings !== undefined) {
    lastStartWarnings = warnings || [];
  }
  setStage("progress");
  await refreshSidebar(runId);
  startProgressWatch(runId);
}

function renderFindingsDetail(row) {
  if (!row) {
    findingsDetail.innerHTML = `<p class="muted">Select a finding.</p>`;
    return;
  }
  const parts = [
    `<h3>${escapeHtml(row.title)}</h3>`,
    `<p><strong>Agent:</strong> ${escapeHtml(row.agent)}</p>`,
    `<p><strong>Confidence:</strong> ${escapeHtml(row.confidence)}</p>`,
    `<p><strong>Claim:</strong> ${escapeHtml(row.claim)}</p>`,
    `<p><strong>Source:</strong> ${escapeHtml(row.source)}</p>`,
    `<p><strong>Method:</strong> ${escapeHtml(row.method || "—")}</p>`,
    `<p><strong>observed_at:</strong> ${escapeHtml(row.observed_at)}</p>`,
  ];
  if (row.is_nhv) {
    parts.push(
      `<p class="nhv-reason"><strong>verification_reason:</strong> ${escapeHtml(
        row.verification_reason || "—"
      )}</p>`
    );
  }
  findingsDetail.innerHTML = parts.join("");
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderFindingsList(rows) {
  findingsList.innerHTML = "";
  for (const row of rows) {
    const li = document.createElement("li");
    li.className = "finding-row";
    if (row.id === selectedFindingId) li.classList.add("selected");
    const title = document.createElement("div");
    title.className = "finding-title";
    title.textContent = row.title;
    const meta = document.createElement("div");
    meta.className = "finding-meta";
    meta.textContent = row.agent;
    li.appendChild(title);
    li.appendChild(meta);
    li.appendChild(confidenceBadge(row));
    li.addEventListener("click", () => {
      selectedFindingId = row.id;
      renderFindingsList(rows);
      renderFindingsDetail(row);
    });
    findingsList.appendChild(li);
  }
  if (!rows.length) {
    findingsDetail.innerHTML = `<p class="muted">No findings match filters.</p>`;
  }
}

function refreshAgentFilterOptions(rows) {
  const current = filterAgent.value;
  const agents = [...new Set(rows.map((r) => r.agent).filter(Boolean))].sort();
  filterAgent.innerHTML = `<option value="">all</option>`;
  for (const agent of agents) {
    const opt = document.createElement("option");
    opt.value = agent;
    opt.textContent = agent;
    filterAgent.appendChild(opt);
  }
  if (agents.includes(current)) filterAgent.value = current;
}

function filterCachedFindings() {
  const confidence = filterConfidence.value || "";
  const agent = filterAgent.value || "";
  return cachedFindings.filter((row) => {
    if (confidence && row.confidence !== confidence) return false;
    if (agent && row.agent !== agent) return false;
    return true;
  });
}

async function openFindings(runId, preferFindingId) {
  selectedRunId = runId;
  stopProgressWatch();
  setStage("findings");
  await refreshSidebar(runId);
  cachedFindings = (await window.sageoOperator.listFindings({ runId })) || [];
  refreshAgentFilterOptions(cachedFindings);
  const filtered = filterCachedFindings();
  if (preferFindingId) selectedFindingId = preferFindingId;
  renderFindingsList(filtered);
  const selected = filtered.find((r) => r.id === selectedFindingId) || filtered[0];
  if (selected) {
    selectedFindingId = selected.id;
    renderFindingsDetail(selected);
  } else {
    renderFindingsDetail(null);
  }
}

async function openReview(runId, options = {}) {
  selectedRunId = runId;
  stopProgressWatch();
  setStage("review");
  await refreshSidebar(runId);
  if (!options.keepResult) {
    reviewResult.textContent = "";
  }
  if (options.resultMessage) {
    reviewResult.textContent = options.resultMessage;
  }
  if (!options.keepNote) {
    operatorNote.value = "";
  }
  const review = await window.sageoOperator.getReview(runId);
  if (!review || !review.gate_open) {
    show(reviewEmpty);
    hide(reviewBody);
    reviewEmpty.textContent =
      (review && review.empty_message) ||
      "No Human review gate is open for this Run.";
    return;
  }
  hide(reviewEmpty);
  show(reviewBody);
  reviewPaused.textContent = `Paused Agent: ${review.paused_agent}`;
  reviewDecision.textContent = JSON.stringify(review.decision || {}, null, 2);
  reviewEvidenceLinks.innerHTML = "";
  for (const finding of review.linked_findings || []) {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "linkish";
    btn.textContent = finding.title || finding.id;
    btn.addEventListener("click", () => openFindings(runId, finding.id));
    li.appendChild(btn);
    reviewEvidenceLinks.appendChild(li);
  }
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

document.getElementById("new-run-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  renderErrors(newRunErrors, []);
  renderErrors(newRunWarnings, []);
  const fields = {
    site_url: document.getElementById("site_url").value,
    gsc_property: document.getElementById("gsc_property").value,
    ga4_property: document.getElementById("ga4_property").value,
    reach: document.getElementById("reach").value,
    goal: document.getElementById("goal").value,
  };
  const result = await window.sageoOperator.startThinAudit(fields);
  if (!result.ok) {
    renderErrors(newRunErrors, result.errors || ["Start failed"]);
    return;
  }
  renderErrors(newRunWarnings, result.warnings || []);
  selectedRunId = result.run_id;
  await refreshSidebar(result.run_id);
  await openProgress(result.run_id, result.warnings || []);
});

document.getElementById("new-run-btn").addEventListener("click", () => {
  stopProgressWatch();
  setStage("new-run");
});
document.getElementById("empty-new-run-btn").addEventListener("click", () => {
  stopProgressWatch();
  setStage("new-run");
});
document.getElementById("settings-btn").addEventListener("click", () => {
  stopProgressWatch();
  fillRuntimeForm("settings_", currentConfig);
  setStage("settings");
});

goToReviewBtn.addEventListener("click", () => {
  if (selectedRunId) openReview(selectedRunId);
});
goToFindingsBtn.addEventListener("click", () => {
  if (selectedRunId) openFindings(selectedRunId);
});

document.querySelectorAll("[data-stage]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!selectedRunId) return;
    const stage = btn.getAttribute("data-stage");
    if (stage === "progress") openProgress(selectedRunId);
    if (stage === "findings") openFindings(selectedRunId);
    if (stage === "review") openReview(selectedRunId);
  });
});

filterConfidence.addEventListener("change", () => {
  if (selectedRunId) openFindings(selectedRunId, selectedFindingId);
});
filterAgent.addEventListener("change", () => {
  if (selectedRunId) openFindings(selectedRunId, selectedFindingId);
});

async function submitReview(approved) {
  if (!selectedRunId) return;
  if (!approved) {
    const ok = window.confirm(
      "Reject this Human review gate? The Run will stop at this Agent."
    );
    if (!ok) return;
  }
  const result = await window.sageoOperator.resumeRun({
    runId: selectedRunId,
    approved,
    operator_note: operatorNote.value,
  });
  const verb = approved ? "Approve" : "Reject";
  if (!result.ok) {
    reviewResult.textContent = (result.errors || [`${verb} failed`]).join("; ");
    return;
  }
  const message = `${approved ? "Approved" : "Rejected"}. gate_state=${result.gate_state}`;
  reviewResult.textContent = message;
  await refreshSidebar(selectedRunId);
  if (approved && result.gate_state !== "awaiting_approval") {
    // Stay briefly on Review with the result, then continue into Progress.
    await openProgress(selectedRunId);
    return;
  }
  // Reject, or Approve into the next open gate: stay on Review showing result.
  await openReview(selectedRunId, { keepResult: true, resultMessage: message });
}

document.getElementById("approve-btn").addEventListener("click", () => {
  submitReview(true);
});
document.getElementById("reject-btn").addEventListener("click", () => {
  submitReview(false);
});

boot();
