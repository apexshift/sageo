# Research: Electron vs Tauri for a Python-backed operator desktop

**Ticket:** [#143](https://github.com/apexshift/sageo/issues/143)  
**Branch:** `research/electron-vs-tauri-operator-desktop`  
**Scope:** Practical trade-offs between Electron and Tauri (plus one close alternative) for a local desktop operator app that shells over a SageO Python runtime (Orchestrator, Agents, `runs/<id>/`). Research only — toolkit lock is grilling ticket [#147](https://github.com/apexshift/sageo/issues/147).

**Product filter:** Parent map [#142](https://github.com/apexshift/sageo/issues/142) destination is a locked product/UX spec for a sidebar + main-stage operator shell. Near-term the GUI shells over a **local SageO checkout/venv** (Python ≥3.11). Fully bundled installers for clean machines are **out of this destination** (listed under Not yet specified / later effort). Glossary terms: Run directory, Evidence, Decision log, Human review gate, Orchestrator.

**Method:** Prefer primary sources (official Electron / Tauri / Wails docs and packaging guides). Treat third-party size benchmarks as secondary signal only, and note when they measure empty apps rather than Python-sidecar bundles.

---

## 1. What “fit” means for SageO

| Need | Why it matters |
| --- | --- |
| **Spawn / talk to local Python** | Orchestrator + Agents live in the SageO Python package; the GUI is a shell, not a rewrite |
| **Read/watch `runs/<id>/`** | Evidence + Decision log are append-only artifacts under the Run directory |
| **Sidebar + main-stage UI** | Map preference: app shell with nav + stage for start Run → progress → findings → Human review gates |
| **macOS-first packaging path** | Signing + notarization will gate any future non-dev distribution |
| **Defer full bundling** | Clean-machine one-click installer is explicitly out of #142; avoid letting future packaging dominate near-term shell choice — but flag hard blockers early |

SageO today: `requires-python = ">=3.11"`, hybrid Markdown + Python Skills/Agents/Orchestrator, local `runs/` gitignored contents (`pyproject.toml`, `docs/architecture.md`, `GLOSSARY.md`).

---

## 2. Architecture at a glance

| Dimension | Electron | Tauri 2 |
| --- | --- | --- |
| **UI renderer** | Bundled Chromium | OS WebView (WKWebView macOS, WebView2 Windows, WebKitGTK Linux) |
| **App / backend process** | Node.js **main** process (+ optional utility processes) | Rust host binary |
| **Frontend** | Any web stack in renderer(s); IPC via preload + `contextBridge` | Any web stack; IPC via Tauri commands / events; capabilities ACL |
| **Python integration** | `child_process.spawn` / `fork` from main (or helpers via `utilityProcess` for Node workers) | `tauri-plugin-shell` spawn/execute; first-class **sidecar** (`bundle.externalBin`) for bundled binaries (docs cite PyInstaller Python CLIs) |
| **FS access model** | Node `fs` in main (full, unless App Sandbox / MAS) | `tauri-plugin-fs` with **explicit path scopes** in capabilities |
| **Typical empty-app size order** | Tens–hundreds of MB (ships Chromium + Node) | Single-digit MB shell (uses system WebView) |

Sources: [Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model); [Tauri sidecar](https://v2.tauri.app/develop/sidecar/); [Tauri shell plugin](https://v2.tauri.app/plugin/shell/); [Tauri fs plugin](https://v2.tauri.app/plugin/file-system/).

---

## 3. App size

### Facts

- **Electron** embeds Chromium and Node into each app binary/distribution. Official packaging docs describe bundling “your app code together with the Electron binary” via Forge/`@electron/packager`; they do not advertise a small footprint. Independently measured empty/minimal Electron installers commonly land ~80–150+ MB (Windows NSIS examples around ~100 MB; macOS empty builds often ~100–300+ MB depending on arch and locales). Secondary: [Electron packaging tutorial](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging); community measurements e.g. [Dawloom Electron alternatives 2026](https://dawloom.com/blog/electron-alternatives/) (Electron ~106 MB NSIS vs Tauri ~1 MB for the *same minimal app*).
- **Tauri** does **not** ship a browser. The distributable is a native Rust binary plus OS WebView dependency. Official sidecar docs emphasise preventing users from installing extra runtimes; empty-app installers are routinely reported in the ~1–15 MB range. Secondary corroboration: same Dawloom / Elanis-style empty-app comparisons.
- **Python changes the math.** Official Tauri sidecar guidance explicitly lists “Python CLI applications or API servers bundled using `pyinstaller`” as a common `externalBin` use case ([Embedding External Binaries](https://v2.tauri.app/develop/sidecar/)). A PyInstaller (or similar) SageO sidecar will typically add **tens to hundreds of MB** (interpreter + stdlib + deps + frozen Skills tree). Once that lands, the GUI-shell delta (Chromium vs WebView) is a smaller fraction of total download than empty-app tables imply.

### Relevance to SageO

Near-term (checkout + venv): neither toolkit’s installer size matters — operators already have a SageO tree and Python. Later bundling: expect **Python runtime weight to dominate**; do not pick Tauri solely on empty-app MB, and do not dismiss Electron solely on Chromium MB without modelling the frozen SageO payload.

---

## 4. macOS packaging / signing friction

### Shared Apple requirements (both toolkits)

1. Apple Developer Program membership (paid for distribution / notarization).
2. Xcode / macOS build host for signing.
3. **Developer ID Application** certificate for direct distribution outside the Mac App Store.
4. **Notarization** (and preferably stapling) for Gatekeeper on modern macOS — unsigned or only ad-hoc signed apps force operators through Privacy & Security overrides.

Sources: [Electron code signing](https://www.electronjs.org/docs/latest/tutorial/code-signing); [Tauri macOS code signing](https://v2.tauri.app/distribute/sign/macos/); Apple Developer Program.

### Electron-specific

- Ecosystem path: **Electron Forge** (recommended) wires `@electron/packager`, `@electron/osx-sign`, `@electron/notarize`. Config surfaces `osxSign` / `osxNotarize` (Apple ID + app-specific password or API key / team id).
- Hardened Runtime + entitlements matter: Electron needs at least JIT-related entitlements (`com.apple.security.cs.allow-jit`, and historically unsigned-executable-memory on older Electron). Child processes / helpers inherit entitlements via `entitlementsInherit` patterns in electron-builder docs.
- **Mac App Store** builds require App Sandbox and the MAS Electron build — hostile to arbitrary filesystem paths and free-form Python spawning. Direct Developer ID distribution (not MAS) is the realistic path for an operator tool that must see a checkout’s `runs/`.
- Unsigned apps: OS makes download/launch painful; several APIs (`safeStorage`, login items, `autoUpdater` / Squirrel.Mac) misbehave without proper signing.

Sources: [Electron code signing](https://www.electronjs.org/docs/latest/tutorial/code-signing); [Electron Forge packaging](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging); [electron-builder macOS notarization](https://www.electron.build/v26/docs/notarization) (secondary tooling, widely used).

### Tauri-specific

- Configure `bundle.macOS.signingIdentity` or `APPLE_SIGNING_IDENTITY`; CI typically uses `APPLE_CERTIFICATE` + `APPLE_CERTIFICATE_PASSWORD` (base64 `.p12`).
- Notarization via App Store Connect API (`APPLE_API_ISSUER`, `APPLE_API_KEY`, `APPLE_API_KEY_PATH`) or Apple ID (`APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID`).
- Ad-hoc identity `"-"` can sign for Apple Silicon local runs but **does not** remove unknown-developer Gatekeeper prompts for downloaded apps.
- Free Apple Developer accounts cannot notarize.

Source: [Tauri macOS Code Signing](https://v2.tauri.app/distribute/sign/macos/).

### Friction verdict

**Comparable for distribution.** Both need the same Apple membership, certs, notarization, and a Mac in the loop. Electron has more years of blog/CI recipes; Tauri’s env-var flow is well documented for v2. Neither removes the hard cost of Developer ID + notarization when non-dev operators download a build. **Sandbox/MAS is a likely blocker for both** if the app must spawn project-local Python and read arbitrary Run directories — prefer Developer ID outside the App Store.

---

## 5. Calling / spawning a local Python process

### Near-term: shell over checkout / venv (in-destination)

| | Electron | Tauri |
| --- | --- | --- |
| **Mechanism** | Main process Node `child_process.spawn(venvPython, args, { cwd })`; stdio pipes; optional HTTP/JSON-RPC to a small local Orchestrator server the child starts | `tauri-plugin-shell`: allowlisted `Command.create` / `spawn` with `cmd` + arg validators in capabilities; or Rust `std::process` / `ShellExt` from commands |
| **Ceremony** | Low — Node APIs are unrestricted in non-sandboxed main | Medium — every executable name and arg pattern must be declared in capabilities (`shell:allow-spawn` / `shell:allow-execute`) |
| **Pointing at a venv** | Pass absolute path to `.venv/bin/python` (operator- or settings-selected SageO root) | Same path works, but must fit allowlist / validators; dynamic paths need careful capability design (`validator` regexes or broad allow — security trade-off) |
| **Long-lived Orchestrator** | Common pattern: spawn once on app start, supervise, kill on quit | Same pattern via shell spawn + event listeners on stdout; sidecar API is aimed more at *bundled* binaries |

Sources: [Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model) (main has full Node); Node.js `child_process` (standard library used by Electron main); [Tauri shell plugin](https://v2.tauri.app/plugin/shell/); [Tauri sidecar](https://v2.tauri.app/develop/sidecar/).

### Later: bundled Python for non-dev operators (out of destination, but flag blockers)

| | Electron | Tauri |
| --- | --- | --- |
| **Official story** | Ship binary under `extraResources` / `asarUnpack`; `spawn` from `process.resourcesPath`; sign nested helpers | First-class `bundle.externalBin` sidecars; target-triple-suffixed binaries; docs call out PyInstaller Python CLIs/servers |
| **macOS gotcha** | Nested unsigned Python/PyInstaller binaries break under Hardened Runtime / library validation; entitlements and per-binary signing required (community reports of “works in dev, child fails in production”) | Sidecar is packaged by Tauri bundler; nested signing still required for notarization — same Apple rules, slightly more opinionated layout |
| **SageO-specific risk** | Freezing a hybrid Skills tree (dynamic Markdown + Python, plugins, connectors) with PyInstaller/briefcase is non-trivial either way | Same freeze problem; Tauri does not solve Python packaging — it only embeds the resulting binary |

Sources: [Tauri sidecar](https://v2.tauri.app/develop/sidecar/); Apple forums / Electron packaging discussions on child processes under Hardened Runtime (secondary); Electron Forge packaging overview.

### Relevance

For **#142’s near-term shell**, Electron’s spawn path is the least ceremony. Tauri is fully capable but forces an allowlist design up front (good security hygiene, slower prototype). For **future bundling**, Tauri’s sidecar is the clearer first-party story; Electron remains workable with `extraResources` discipline. The true blocker for non-dev operators is **freezing SageO’s Python surface**, not the GUI toolkit.

---

## 6. Filesystem access to Run directories

SageO contract: Run directory `runs/<id>/` holds append-only Evidence and Decision log JSON/JSONL (`GLOSSARY.md`, `docs/architecture.md`). The operator app must list runs, read artifacts, and likely **watch** for appends while a Run is active.

### Electron

- Main process: Node `fs` / `fs.promises`, `fs.watch` or libraries such as `chokidar`.
- Renderer must not get raw Node; expose narrow IPC APIs via `contextBridge` (current Electron security default: context isolation on, nodeIntegration off).
- Non-sandboxed Developer ID apps: can read any operator-selected SageO root (e.g. dialog to pick repo path, then `runs/`).
- MAS sandbox: would need security-scoped bookmarks / entitlements — poor fit.

Source: [Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model) (preload + contextBridge).

### Tauri

- `@tauri-apps/plugin-fs`: read/write/watch with **scopes**. Default permission set covers app-specific dirs (`AppConfig`, `AppData`, …), **not** an arbitrary checkout path.
- Permissions alone are insufficient — scopes must list paths (e.g. `$HOME/**/runs/**` or a dialog-selected directory registered into the scope at runtime via `FsExt` / `scope.allow_directory` in Rust).
- `watch` / `watchImmediate` available (enable `watch` feature on `tauri-plugin-fs`).
- Path traversal (`..`) blocked by the plugin.

Source: [Tauri File System plugin](https://v2.tauri.app/plugin/file-system/).

### Relevance

Both can implement Run browsing. Electron is permissive by default in main (discipline via IPC design). Tauri is deny-by-default (discipline via capabilities) — better threat model, more config for “operator cloned SageO somewhere under `$HOME`.” Prefer a **user-selected SageO root** in either toolkit rather than hard-coding paths.

---

## 7. UI stacks for sidebar + main-stage shell

Both toolkits host ordinary web UIs. A sidebar + main-stage operator shell maps cleanly onto React/Vue/Svelte/Solid + any layout primitives (CSS grid/flex, Radix, shadcn/ui, MUI, etc.).

| Concern | Electron | Tauri |
| --- | --- | --- |
| **Templates / starters** | Forge templates; large community IDE-like shells (VS Code itself is Electron — existence proof for sidebar/activity-bar + editor stage) | `create-tauri-app` scaffolds for React, Vue, Svelte, Solid, vanilla |
| **Desktop chrome** | Mature: BrowserWindow, native menus, dialogs, tray; multi-window well worn | Native menus, dialogs, multi-window via Tauri 2 window APIs; slightly younger ecosystem |
| **DevTools** | Full Chromium DevTools, identical across OSes | WebView DevTools; behaviour can differ by OS WebView engine |
| **Rendering consistency** | Same Chromium everywhere | WKWebView vs WebView2 vs WebKitGTK differences (CSS/JS edge cases) — test matrix wider |
| **Fit for #142 IA** | No blocker | No blocker |

Sources: [Electron process model / BrowserWindow](https://www.electronjs.org/docs/latest/tutorial/process-model); Tauri create-app / window docs (project scaffolding); product reality that VS Code / Slack / Discord ship Electron sidebar-heavy UIs.

**Verdict:** UI maturity is **not** a deciding factor for a sidebar + main-stage operator shell. Prefer the toolkit that fits Python/FS packaging; pick the frontend stack independently (React + a headless component kit is enough for the UX spec).

---

## 8. What would block a non-dev operator when bundling becomes a goal

These are **later-effort** risks (map Not yet specified). Flag for #147 so the UX spec does not paint into a corner.

1. **SageO freeze complexity** — Packaging Skills (`SKILL.md` + `scripts/`), Agents, Orchestrator, optional connectors, and Python ≥3.11 into a relocatable tree (PyInstaller/briefcase/uv-managed embed) is the dominant engineering cost. Toolkit choice only embeds the result.
2. **Nested binary signing** — PyInstaller onecfile/onedir produces executables and `.so`/`.dylib` loads that must satisfy Hardened Runtime / notarization. Failure mode: GUI launches, Python child dies silently on macOS production builds.
3. **App Sandbox / Mac App Store** — Incompatible with free-form `runs/` paths and venv/sidecar spawn unless heavily redesigned (security-scoped resources, fixed container dirs). Plan on **Developer ID + notarized DMG/ZIP**, not MAS, unless product strategy changes.
4. **Windows WebView2 (Tauri)** — Required on older Windows; Win11 usually present. Electron self-contains Chromium (larger, fewer host deps).
5. **Builder toolchain on CI** — Electron: Node + Forge/builder. Tauri: Node (frontend) + **Rust toolchain** + platform C toolchains. Operators never need these; release engineers do.
6. **Auto-update + Python payload** — Updating a 200 MB+ Python sidecar differs from updating a thin UI shell; need a versioning story relative to the SageO package (already a #142 open question).
7. **Secrets / connectors** — GSC/GA4/crawl-serp env credentials must land outside the asar/bundle in a writable, non-world-readable location; independent of Electron vs Tauri but easy to get wrong in first installer.

---

## 9. Close alternative (one paragraph): Wails

**Wails** (v3 stable for desktop per [wails.io](https://wails.io/)) pairs a **Go** backend with the same class of **OS WebView** as Tauri (no bundled Chromium), producing small binaries and auto-generated JS bindings from Go. It is a credible lightweight Electron alternative for Go-centric teams, with official packaging/signing paths and experimental mobile. For SageO it is a **weak third**: the runtime of record is Python, not Go — a Wails shell would still spawn/embed Python while adding a third language (Go) the repo does not use, without Tauri’s first-party Python-sidecar documentation or Electron’s Node spawn ergonomics. Consider only if the team deliberately standardises on Go for native desktop hosts; otherwise leave it out of #147’s shortlist.

---

## 10. Comparison matrix (operator-desktop lens)

| Dimension | Electron | Tauri 2 | Edge for SageO near-term |
| --- | --- | --- | --- |
| **App size (UI shell)** | Large (Chromium + Node) | Small (OS WebView) | Tauri (moot until bundling) |
| **App size (with frozen Python)** | Large + sidecar | Smaller shell + same sidecar class | Weak Tauri edge |
| **macOS sign / notarize** | Forge / osx-sign / notarize; well documented | Env-var cert + notarize; well documented | Tie |
| **Spawn local venv Python** | Trivial `child_process` | Shell plugin + allowlist | **Electron** |
| **Bundled Python sidecar** | `extraResources` + spawn (manual) | Official `externalBin` + shell sidecar | **Tauri** |
| **Read/watch `runs/<id>/`** | Node `fs` in main | Scoped `plugin-fs` (+ watch feature) | Electron easier; Tauri safer defaults |
| **Sidebar + main-stage UI** | Excellent (web + mature desktop chrome) | Excellent (web + native chrome) | Tie |
| **Cross-OS UI sameness** | Chromium everywhere | WebView variance | Electron |
| **Security default** | Powerful main process — must design IPC tightly | Capabilities deny-by-default | Tauri |
| **Team skills match** | Node/TS likely for UI already | Adds Rust for host/commands | Electron (unless Rust is welcome) |
| **Non-dev bundling blockers** | Nested sign + Python freeze | Nested sign + Python freeze + Rust CI | Tie (Python freeze dominates) |

---

## 11. Recommendation seed (for #147 — not a lock)

> **Seed for grilling [#147](https://github.com/apexshift/sageo/issues/147):** For the #142 product/UX spec’s *near-term* implementation guidance — a sidebar + main-stage shell over a **local SageO checkout/venv** — prefer **Electron** as the assumed toolkit. Spawning project-local Python ≥3.11 and reading/watching `runs/<id>/` is the path of least resistance in a Node main process; macOS signing/notarization friction is comparable to Tauri when distribution eventually matters; and empty-app size advantages of Tauri shrink once a frozen Python payload exists. Treat **Tauri** as the strong alternative if #147 prioritises capability-scoped FS, smaller UI shell, and a first-class sidecar story *ahead of* Node DX — especially if bundled installers move into scope sooner than the map currently allows. Do **not** assume Mac App Store distribution. Do **not** let toolkit choice pretend to solve SageO Python freezing. **Wails** stays a footnote unless the team wants Go.

Locking the toolkit, recording packaging implications that remain out of destination, and updating #142 Decisions so far are **#147’s job** — not this research ticket.

---

## Implications for #147 (grill toolkit)

Lock one of:

- **A. Electron** for UX-spec implementation guidance — recommend **A** given current destination (local runtime, bundling deferred). Document: main-process Python supervise pattern; IPC surface for Run directory; Developer ID (not MAS) packaging assumption; Python freeze remains Not yet specified.
- **B. Tauri 2** if the grill explicitly weights deny-by-default FS/shell ACL and future sidecar bundling over Node spawn ergonomics. Document: capability scopes for SageO root + `runs/`; shell allowlist for venv or sidecar; Rust as release-engineering dependency.
- **C. Defer toolkit in the UX spec** (“toolkit-agnostic wireframes”) — only if #147 cannot decide; costs less precise implementation notes for prototype tickets.

Out of scope for #147: implementing the GUI, choosing React vs Vue, building PyInstaller sidecars, or editing this research file’s facts without new primary sources.

---

## Sources (primary)

- [Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model) — main / renderer / utilityProcess  
- [Electron code signing](https://www.electronjs.org/docs/latest/tutorial/code-signing) — macOS sign + notarize requirements  
- [Electron packaging tutorial (Forge)](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging)  
- [utilityProcess](https://www.electronjs.org/docs/latest/api/utility-process) — Node child workers (not a substitute for Python spawn)  
- [Tauri Embedding External Binaries (sidecar)](https://v2.tauri.app/develop/sidecar/) — `externalBin`, PyInstaller called out  
- [Tauri Shell plugin](https://v2.tauri.app/plugin/shell/) — spawn/execute + capabilities  
- [Tauri File System plugin](https://v2.tauri.app/plugin/file-system/) — scopes, defaults, watch  
- [Tauri macOS Code Signing](https://v2.tauri.app/distribute/sign/macos/) — certs, notarization env vars, ad-hoc  
- [Wails](https://wails.io/) — Go + OS WebView alternative  
- SageO: `pyproject.toml` (`requires-python = ">=3.11"`), `GLOSSARY.md` (Run directory), `docs/architecture.md`, map [#142](https://github.com/apexshift/sageo/issues/142)

### Secondary (size / cross-checks only)

- [Dawloom: Electron alternatives 2026](https://dawloom.com/blog/electron-alternatives/) — measured empty-app installer sizes  
- [Elanis web-to-desktop-framework-comparison](https://github.com/Elanis/web-to-desktop-framework-comparison) — empty-app size/memory matrix  
- [electron-builder macOS notarization](https://www.electron.build/v26/docs/notarization) — entitlements patterns used in the wild  
