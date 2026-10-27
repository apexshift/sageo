"""Classify query and page intent hermetically and emit Evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

INFORMATIONAL_QUERY = frozenset(
    {
        "how",
        "what",
        "why",
        "when",
        "where",
        "who",
        "guide",
        "tutorial",
        "meaning",
        "define",
        "vs",
        "versus",
        "examples",
    }
)
TRANSACTIONAL_QUERY = frozenset(
    {
        "buy",
        "price",
        "cheap",
        "deal",
        "coupon",
        "order",
        "purchase",
        "shop",
        "discount",
        "cost",
    }
)
NAVIGATIONAL_QUERY = frozenset(
    {
        "login",
        "log-in",
        "signin",
        "sign-in",
        "official",
        "website",
        "homepage",
        "portal",
    }
)

TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

INFORMATIONAL_PAGE = (
    re.compile(r"\bhow to\b", re.I),
    re.compile(r"\bguide\b", re.I),
    re.compile(r"\btutorial\b", re.I),
    re.compile(r"\bwhat is\b", re.I),
    re.compile(r"\bfaq\b", re.I),
)
TRANSACTIONAL_PAGE = (
    re.compile(r"\bbuy\b", re.I),
    re.compile(r"\badd to cart\b", re.I),
    re.compile(r"\bprice\b", re.I),
    re.compile(r"\bfree shipping\b", re.I),
    re.compile(r'"@type"\s*:\s*"Product"', re.I),
)
NAVIGATIONAL_PAGE = (
    re.compile(r"\bofficial\b", re.I),
    re.compile(r"\blog[\s-]?in\b", re.I),
    re.compile(r"\bsign[\s-]?in\b", re.I),
    re.compile(r"\bhome\s*page\b", re.I),
)


def classify_intent(
    query: str,
    page_html: str,
    *,
    source_query: str,
    source_page: str,
    source_bundle: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Classify query/page intent and whether they match; return findings + Evidence.

    Hermetic keyword/structure heuristics only (no network I/O / LLM).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    query_intents = _query_intents(query)
    page_intents = _page_intents(page_html)

    if len(query_intents) == 1:
        q_intent = next(iter(query_intents))
        findings.append(
            _finding("intent.query", "pass", f"Query classified as {q_intent}.")
        )
        evidence_items.append(
            _evidence(
                f"Query '{query.strip()}' matches {q_intent} cues.",
                source=source_query,
                observed_at=observed,
                confidence="high",
            )
        )
    elif len(query_intents) == 0:
        findings.append(
            _finding(
                "intent.query",
                "fail",
                "Query intent could not be classified from hermetic cues.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Query '{query.strip()}' matched no informational, transactional, "
                "or navigational cue set.",
                source=source_query,
                observed_at=observed,
                confidence="high",
            )
        )
        q_intent = None
    else:
        labels = ", ".join(sorted(query_intents))
        findings.append(
            _finding(
                "intent.query",
                "fail",
                f"Query intent is ambiguous across {labels}.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Query '{query.strip()}' matched multiple intent cue sets: {labels}.",
                source=source_query,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Query matches more than one intent class under hermetic heuristics"
                ),
            )
        )
        findings.append(
            _finding(
                "intent.ambiguous",
                "fail",
                "Query intent signals conflict and need human verification.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Ambiguous query intent classes: {labels}.",
                source=source_query,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Conflicting query intent cues make a single class unreliable"
                ),
            )
        )
        q_intent = None

    if len(page_intents) == 1:
        p_intent = next(iter(page_intents))
        findings.append(
            _finding("intent.page", "pass", f"Page classified as {p_intent}.")
        )
        claim = {
            "informational": "Page title/H1 match informational cues (how-to / guide style).",
            "transactional": "Page signals match transactional cues (buy/price/product).",
            "navigational": "Page signals match navigational cues (login/official/home).",
        }[p_intent]
        evidence_items.append(
            _evidence(
                claim,
                source=source_page,
                observed_at=observed,
                confidence="high",
            )
        )
    elif len(page_intents) == 0:
        findings.append(
            _finding(
                "intent.page",
                "fail",
                "Page intent could not be classified from hermetic cues.",
            )
        )
        evidence_items.append(
            _evidence(
                "Page title/H1/body matched no informational, transactional, "
                "or navigational cue set.",
                source=source_page,
                observed_at=observed,
                confidence="high",
            )
        )
        p_intent = None
    else:
        labels = ", ".join(sorted(page_intents))
        findings.append(
            _finding(
                "intent.page",
                "fail",
                f"Page intent is ambiguous across {labels}.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Page matched multiple intent cue sets: {labels}.",
                source=source_page,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Page matches more than one intent class under hermetic heuristics"
                ),
            )
        )
        if "intent.ambiguous" not in {f["id"] for f in findings}:
            findings.append(
                _finding(
                    "intent.ambiguous",
                    "fail",
                    "Page intent signals conflict and need human verification.",
                )
            )
            evidence_items.append(
                _evidence(
                    f"Ambiguous page intent classes: {labels}.",
                    source=source_page,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Conflicting page intent cues make a single class unreliable"
                    ),
                )
            )
        p_intent = None

    if q_intent is not None and p_intent is not None:
        if q_intent == p_intent:
            findings.append(
                _finding(
                    "intent.match",
                    "pass",
                    f"Query and page intents match ({q_intent}).",
                )
            )
            evidence_items.append(
                _evidence(
                    f"Query intent {q_intent} matches page intent {p_intent}.",
                    source=source_bundle,
                    observed_at=observed,
                    confidence="high",
                )
            )
        else:
            findings.append(
                _finding(
                    "intent.match",
                    "fail",
                    f"Query intent ({q_intent}) does not match page intent ({p_intent}).",
                )
            )
            evidence_items.append(
                _evidence(
                    f"Query intent {q_intent} does not match page intent {p_intent}.",
                    source=source_bundle,
                    observed_at=observed,
                    confidence="high",
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _query_intents(query: str) -> set[str]:
    tokens = {t.strip(".,!?\"'").lower() for t in query.split() if t.strip()}
    matched: set[str] = set()
    if tokens & INFORMATIONAL_QUERY:
        matched.add("informational")
    if tokens & TRANSACTIONAL_QUERY:
        matched.add("transactional")
    if tokens & NAVIGATIONAL_QUERY:
        matched.add("navigational")
    return matched


def _page_intents(html: str) -> set[str]:
    title = _plain_text(TITLE_RE.search(html).group(1) if TITLE_RE.search(html) else "")
    h1s = [_plain_text(m.group(1)) for m in H1_RE.finditer(html)]
    head = " ".join([title, *h1s])
    body = _plain_text(TAG_RE.sub(" ", html))
    corpus = f"{head}\n{body}"

    matched: set[str] = set()
    if any(rx.search(head) or rx.search(corpus) for rx in INFORMATIONAL_PAGE):
        matched.add("informational")
    if any(rx.search(corpus) for rx in TRANSACTIONAL_PAGE):
        matched.add("transactional")
    if any(rx.search(head) for rx in NAVIGATIONAL_PAGE):
        matched.add("navigational")
    return matched


def _plain_text(raw: str) -> str:
    text = TAG_RE.sub(" ", raw)
    return WHITESPACE_RE.sub(" ", text).strip()


def _finding(finding_id: str, status: str, summary: str) -> dict[str, str]:
    return {"id": finding_id, "status": status, "summary": summary}


def _evidence(
    claim: str,
    *,
    source: str,
    observed_at: str,
    confidence: str,
    verification_reason: str | None = None,
) -> dict[str, str]:
    item = {
        "claim": claim,
        "source": source,
        "observed_at": observed_at,
        "confidence": confidence,
        "method": "query-page-intent-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
