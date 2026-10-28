---
name: crawl-issue-extractor
description: >-
  Extract and classify crawl issues from a crawl-log fixture (or via the
  crawl_serp connector) and emit Evidence. Use when turning crawl captures into
  structured client-error, server-error, redirect, timeout, and soft-404
  findings.
metadata:
  version: "0.1.0"
  capability_pillar: technical-foundation
  primary_outcome: SEO
  evidence_requirement: full
  human_review_gate: not_required
  connectors: crawl_serp
  inputs: crawl-log
  outputs: findings, evidence
---

## Purpose

Extract and classify **crawl issues** from a crawl-log snapshot into Skill-level
findings: HTTP 4xx client errors, HTTP 5xx server errors, long redirect chains,
timeouts, and soft-404 candidates. Soft-404 and connector failures use
`needs_human_verification`. Remediations are owned by Agents and Orchestrator
Human review gates. This is the only Core Skill that declares the `crawl_serp`
connector class; live connector packs land in P3 — tests mock the seam.

## Inputs

- **crawl-log** — map with `entries` (list). Each entry may include `url`,
  `status` (int or null), `redirect_count` (int), and `error` (`null` |
  `"timeout"` | `"soft_404"` | other string).
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.
- **crawl_serp** — optional connector object exposing
  `fetch_crawl_log(job_id) -> crawl-log map`. Used only when `crawl_log` is
  omitted.
- **job_id** — required with `crawl_serp` when loading via the connector.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/extract.py` →
`extract_crawl_issues(crawl_log=None, *, source, observed_at=None, crawl_serp=None, job_id=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `crawl-log-heuristics`)

Connector failures map to NHV with `verification_reason` in
`missing_credentials` | `auth_failed` | `rate_limited` | `timeout` |
`upstream_error` | `empty_result`.

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Resolve the crawl-log: use the caller-supplied map, or call
   `crawl_serp.fetch_crawl_log(job_id)`. No live APIs in hermetic tests.
2. If the connector raises `CrawlSerpError`, or returns an empty/invalid log →
   fail `crawl.connector` with NHV Evidence and stop (`empty_result` /
   `upstream_error` as appropriate).
3. Require `entries` to be a list of maps. A caller-supplied empty list is
   valid (all category findings pass with zero counts). An empty list from
   the connector is `empty_result` NHV (step 2).
4. Classify each entry:
   - **client error** — `status` in 400–499
   - **server error** — `status` in 500–599
   - **long redirect** — `redirect_count` > 2
   - **timeout** — `error` equals `timeout`
   - **soft_404** — `error` equals `soft_404` (NHV; status may still be 200)
5. Emit pass/fail findings for `crawl.client_error`, `crawl.server_error`,
   `crawl.redirect_chain`, and `crawl.timeout`.
6. If any soft-404 candidates → fail `crawl.soft_404` with
   `needs_human_verification` Evidence.
7. Return `{findings, evidence}`.
