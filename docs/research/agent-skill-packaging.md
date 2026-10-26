# Research: Composable agent-skill packaging patterns

**Ticket:** [#2](https://github.com/apexshift/sageo/issues/2)  
**Branch:** `research/agent-skill-packaging`  
**Scope:** Patterns that could inform SageO’s hybrid Markdown+Python skill library layout (grilling ticket [#8](https://github.com/apexshift/sageo/issues/8)). Research only — no layout freeze here.

**Product filter:** SageO organises Skills by five capability pillars; contracts/docs in Markdown; executable Skills in Python where they must run; Agents compose Skills; Evidence and Human review gates are mandatory.

---

## 1. Agent Skills open standard (`SKILL.md`)

### What it is

Anthropic published **Agent Skills** as an open standard at [agentskills.io](https://agentskills.io/specification). A skill is a **directory** whose only required file is `SKILL.md` (YAML frontmatter + Markdown body). Optional conventional subdirs: `scripts/`, `references/`, `assets/`.

### Frontmatter (spec)

| Field | Required | Notes |
| --- | --- | --- |
| `name` | Yes | 1–64 chars; lowercase `a-z`, `0-9`, hyphens; no leading/trailing/consecutive hyphens; **must match parent directory name** |
| `description` | Yes | 1–1024 chars; what it does **and when to use it** |
| `license` | No | License name or bundled file reference |
| `compatibility` | No | Env requirements (≤500 chars) |
| `metadata` | No | Arbitrary string→string map (e.g. `author`, `version`) |
| `allowed-tools` | No | Experimental; space-separated pre-approved tools |

Source: [Agent Skills Specification](https://agentskills.io/specification).

### Progressive disclosure (composability mechanism)

Three load tiers keep many skills cheap in context:

1. **Metadata** (~100 tokens/skill): `name` + `description` always available for discovery.
2. **Instructions**: full `SKILL.md` body loaded when the skill is selected (keep under ~500 lines / ~5k tokens recommended).
3. **Resources**: `scripts/`, `references/`, `assets/` loaded or executed only when referenced.

Sources: [agentskills.io/specification](https://agentskills.io/specification); [Claude Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview); [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).

### Hybrid Markdown + code in one skill folder

Official anatomy matches SageO’s hybrid intent:

```text
skill-name/
├── SKILL.md           # contract + procedural instructions
├── references/        # on-demand docs
├── assets/            # templates / static resources
└── scripts/           # executable helpers (Python, Bash, JS, …)
```

Scripts are run via the agent’s shell/code-execution environment; **script source need not enter context** — only outputs do. Relative paths from the skill root; keep references one level deep from `SKILL.md`.

Sources: [Claude Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview); [anthropics/skills](https://github.com/anthropics/skills).

### Distribution surfaces (Claude ecosystem)

| Surface | Packaging |
| --- | --- |
| Claude Code | Filesystem: `.claude/skills/<name>/` (project) or `~/.claude/skills/` (personal); also Claude Code Plugins / marketplace |
| claude.ai | ZIP upload of skill folder (folder name = skill name) |
| Claude API / managed agents | Upload as zip or files → `skill_*` id; or mount from GitHub |

Sources: [Claude Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview); [Managed agents skills](https://platform.claude.com/docs/en/managed-agents/skills); [anthropics/skills README](https://github.com/anthropics/skills).

### Cross-agent adoption

The same `SKILL.md` directory format is the authoring unit for OpenAI Codex (and related tooling). Codex distinguishes:

- **Skill** = authoring unit (`SKILL.md` + optional scripts/refs/assets).
- **Plugin** = installable distribution unit that can bundle one or more skills, optional MCP config, and presentation assets.

Discovery paths differ by host (e.g. `.agents/skills/`, `.claude/skills/`, `.cursor/skills/`) but the **on-disk skill shape is shared**.

Sources: [OpenAI Codex skills](https://developers.openai.com/codex/skills) (and successor docs under learn.chatgpt.com); secondary corroboration of path matrix in ecosystem write-ups citing first-party docs.

### Relevance to SageO

**Highest fit.** SageO’s locked hybrid policy (Markdown contracts + Python where execution is needed) maps directly onto `SKILL.md` + `scripts/`. Progressive disclosure supports a large pillar-organised library without dumping every skill into every Agent context. Use `metadata` for SageO-specific fields (pillar, version, Evidence requirements) without forking the open format.

---

## 2. MCP tool packs (servers as packages)

### What it is

[Model Context Protocol](https://modelcontextprotocol.io/) exposes **tools, resources, and prompts** from a server process to any MCP host. Packaging is about shipping a **runnable server**, not a Markdown procedure.

### Registry package types

The official MCP Registry (`server.json`) supports multiple artifact backends:

| `registryType` | Artifact | Typical invoke |
| --- | --- | --- |
| `npm` | Public npm package | `npx` / node bin |
| `pypi` | Public PyPI package | `uvx` / console script |
| `nuget` | NuGet | `dnx` / binary |
| `cargo` | crates.io | `cargo install` → PATH binary |
| `oci` | Docker/OCI image | container runtime |
| `mcpb` | MCP Bundle zip on GitHub/GitLab Releases | one-click desktop install |

Ownership verification differs by type (e.g. `mcpName` in `package.json` for npm; `<!-- mcp-name: … -->` in README for PyPI/NuGet; OCI label `io.modelcontextprotocol.server.name`; MCPB requires `fileSha256`).

Source: [MCP Registry Supported Package Types](https://modelcontextprotocol.io/registry/package-types).

### MCPB (formerly DXT)

An **MCP Bundle** (`.mcpb`) is a zip archive with a local MCP server + `manifest.json` for one-click install in Claude Desktop and other supporting clients. Renamed from Desktop Extensions (`.dxt`) in 2025; format otherwise continuous. Tooling: `@anthropic-ai/mcpb` (`mcpb init` / `mcpb pack`).

Sources: [Build a desktop extension with MCPB](https://claude.com/docs/connectors/building/mcpb); [Desktop Extensions research note](https://www.anthropic.com/research/desktop-extensions).

### Python MCP server packaging shape

Typical path for SageO-adjacent stacks:

1. Implement server with official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp` on PyPI; `uv add "mcp[cli]"`).
2. Expose a **console script** / `uvx`-runnable entry.
3. Publish to PyPI; optionally register metadata in MCP Registry with `registryType: pypi`.
4. Optionally also ship `.mcpb` for non-developer installers.

Sources: [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk); [MCP package types](https://modelcontextprotocol.io/registry/package-types).

### Relevance to SageO

**Complementary, not a skill-folder substitute.** MCP packs are right for **connectors and deterministic tool surfaces** (e.g. read-only GSC/GA4 adapters in P3) that Agents/Skills call. They do **not** replace progressive-disclosure procedural Skills. SageO Skills may *instruct* how to use an MCP tool; the MCP server is a separate packaging concern. Prefer PyPI + stdio for developer/agent runtimes; consider MCPB only if desktop one-click distribution becomes a product goal (likely P5).

---

## 3. Python entry-point / plugin packages

### What it is

PyPA **entry points** let an installed distribution advertise named callables or modules for discovery by a host package (`importlib.metadata.entry_points`). Groups such as `console_scripts` create CLI wrappers; custom groups (e.g. `myapp.plugins`) implement plugin registries.

Sources: [Entry points specification](https://packaging.python.org/en/latest/specifications/entry-points/); [Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/).

### Three discovery styles (PyPA guide)

1. **Naming convention** — e.g. scan modules matching `flask_*` via `pkgutil.iter_modules`.
2. **Namespace packages** — plugins drop modules under `myapp.plugins.*`.
3. **Package metadata (entry points)** — preferred explicit registry; declared in `pyproject.toml`:

```toml
[project.entry-points."sageo.skills"]
crawl-audit = "sageo_skills.crawl_audit:run"
```

### Hybrid pattern in the wild: ship `SKILL.md` inside a Python wheel

Projects such as [datalayer/agent-skills](https://github.com/datalayer/agent-skills) package skills as Python distributions that **include non-Python data** (`SKILL.md`, scripts) via the build backend’s wheel artifacts / package-data, with optional extras per skill (`skills-pdf`, etc.). Discovery can then be: pip/uv install → files on disk under site-packages **or** entry points pointing at skill modules/paths.

The PyPI project [`skill`](https://pypi.org/project/skill/) similarly treats Agent Skills as installable units and exposes its own extension registries via entry points (`skill.agent_targets`, translators, backends, validators).

### Relevance to SageO

**Strong fit for executable Skills and optional third-party skill packs.** Use:

- **In-repo library:** filesystem `SKILL.md` trees (open standard) as source of truth for Agents.
- **Installable runtime:** `pyproject.toml` package that installs Python modules + packages skill Markdown/assets as package data; optional `[project.entry-points."sageo.skills"]` (or similar) for programmatic discovery of callables.
- **Extras** for heavy optional deps (SEO crawlers, PDF, etc.) so the core library stays light.

Do not make entry points the *only* skill definition — that would break Markdown-first progressive disclosure and cross-agent portability.

---

## 4. Markdown-first skill / instruction conventions

### Agent Skills (`SKILL.md`) — on-demand procedures

Covered in §1. Best for **composable, task-triggered** workflows.

### Always-on project instructions (`AGENTS.md` / `CLAUDE.md`)

Separate convention: a root (or nested) Markdown file loaded for **standing** repo rules (build commands, layout, house style). SageO already uses root `AGENTS.md`. Codex and others treat this as distinct from Skills: AGENTS.md ≈ always relevant context; Skills ≈ progressive procedures.

Source: Codex customization docs; Anthropic/Claude Code project instruction patterns; SageO `AGENTS.md`.

### Cursor Rules (`.mdc`)

Cursor-specific Markdown-with-frontmatter rules (`description`, `globs`, `alwaysApply`). Overlaps conceptually with skills but is **not** the open Agent Skills directory format. Cursor can also consume `.agents/skills/` / `.claude/skills/` for true skills. Prefer Agent Skills for SageO portability; keep Cursor Rules out of the core library layout.

### README-as-skill / folder README conventions

Pre-standard agent repos often used a skill folder with `README.md` as the instruction doc. The open standard now **requires `SKILL.md`** with constrained frontmatter. New SageO skills should use `SKILL.md`, not README-as-contract.

### Relevance to SageO

Keep a clean split:

| Artifact | Role |
| --- | --- |
| `AGENTS.md` (+ `docs/agents/`, `GLOSSARY.md`, ADRs) | Always-on governance and domain |
| `**/SKILL.md` trees | Composable Skills (pillar library) |
| Python under `scripts/` or package modules | Deterministic execution |
| MCP servers | External tool/connectors |

---

## 5. Pattern comparison (for layout decisions)

| Pattern | Unit of composition | Primary artifact | Discovery | Execution | Fits SageO hybrid? |
| --- | --- | --- | --- | --- | --- |
| Agent Skills (`SKILL.md`) | One skill directory | Markdown + optional scripts | Metadata in host prompt | Agent reads MD; runs scripts | **Yes — primary** |
| Codex Plugin | Installable bundle of skills (+ optional MCP) | Plugin package wrapping skills | Plugin installers | Same as skills | Later (distribution) |
| MCP server package | Tool/resource server | npm/PyPI/OCI/MCPB | MCP Registry + client config | stdio/HTTP process | **Yes — connectors** |
| Python entry points | Callable/plugin module | Wheel + `pyproject.toml` | `importlib.metadata` | Import/call in-process | **Yes — runtime discovery** |
| Namespace / naming plugins | Module under convention | Python packages | `pkgutil` | Import | Optional |
| AGENTS.md-style | Repo/session policy | Plain Markdown | Always loaded | N/A (instructions) | Already in use |
| Cursor `.mdc` rules | Editor-scoped rules | `.mdc` | Cursor only | N/A | Avoid as core |

---

## Implications for SageO layout

Inputs for grilling ticket **Freeze hybrid Markdown+Python layout** (#8):

1. **Adopt the Agent Skills directory shape as the skill source of truth.** Each Skill = one folder named after `name`, with required `SKILL.md` (YAML frontmatter + body). Prefer conventional `scripts/`, `references/`, `assets/` when needed. Align frontmatter with [agentskills.io](https://agentskills.io/specification); put SageO fields (`pillar`, `version`, Evidence-related flags) under `metadata:` or documented extensions rather than inventing a parallel format.

2. **Organise the library by capability pillar, not outcome pillar.** Tree under something like `skills/<pillar-slug>/<skill-name>/` (exact slug set is a layout decision). Outcome pillars (SEO/AIO/GEO) stay positioning/framing, not folder taxonomy — consistent with the master map.

3. **Colocate Python with the skill that owns it.** Prefer `skills/.../scripts/*.py` for skill-local helpers (matches progressive disclosure). Promote shared libraries to a proper Python package (e.g. `src/sageo/…`) when reused across Skills/Agents; reference them from `SKILL.md` rather than duplicating.

4. **Treat MCP packaging as a parallel track for connectors.** Do not nest MCP server projects inside each skill folder by default. Plan `connectors/` (or similar) as PyPI-installable MCP servers with `console_scripts` / `uvx`, registered later if needed. Skills document *how* to use connectors; servers *are* the tools.

5. **Plan installability without coupling authoring to wheels.** Author in-repo as Markdown-first trees. When packaging for P5, ship the same trees as package data (and optional entry points for Python callables). Avoid “entry-point-only” skills that cannot be loaded by Claude/Codex-style hosts.

6. **Keep `AGENTS.md` / glossary / ADRs outside the skill library.** Standing governance stays at repo docs roots; Skills stay progressive and composable.

7. **Versioning:** Spec leaves version in optional `metadata`. Layout ticket should decide whether version is (a) frontmatter-only, (b) mirrored in Python package version, or (c) both with a single source — master map already notes “version is a metadata field” as not-yet-specified beyond that.

8. **What not to copy into core layout:** Cursor-only `.mdc` as the skill format; README-as-skill without `SKILL.md`; one mega-Markdown file per pillar; MCPB as a prerequisite for the skill library (defer to packaging/distribution phase).

### Recommended default for #8 to grill

> **Filesystem Agent-Skills layout by capability pillar, with optional `scripts/` per skill; shared Python in a src package; MCP connectors as separate installable servers; distribution later via package data + optional entry points.**

---

## Sources (primary)

- [Agent Skills Specification](https://agentskills.io/specification) — agentskills.io  
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Claude Platform docs  
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Anthropic engineering  
- [Introducing Agent Skills](https://claude.com/blog/skills) — Claude product blog  
- [anthropics/skills](https://github.com/anthropics/skills) — first-party skill examples + template  
- [MCP Registry package types](https://modelcontextprotocol.io/registry/package-types) — Model Context Protocol  
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — official Python MCP implementation  
- [Build with MCPB](https://claude.com/docs/connectors/building/mcpb) — Claude connectors docs  
- [Desktop Extensions](https://www.anthropic.com/research/desktop-extensions) — Anthropic (DXT → MCPB)  
- [Entry points specification](https://packaging.python.org/en/latest/specifications/entry-points/) — PyPA  
- [Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/) — PyPA  
- [OpenAI Codex skills](https://developers.openai.com/codex/skills) — Codex / OpenAI developers (skills vs plugins)  
- SageO master map [#1](https://github.com/apexshift/sageo/issues/1); glossary `GLOSSARY.md`
