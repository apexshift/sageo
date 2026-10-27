"""Score answer-extractability signals from page HTML and emit Evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

LEAD_WORD_LIMIT = 40

H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
LIST_RE = re.compile(r"<(ul|ol)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
LI_RE = re.compile(r"<li\b[^>]*>", re.IGNORECASE)
DL_RE = re.compile(r"<dl\b[^>]*>(.*?)</dl>", re.IGNORECASE | re.DOTALL)
DT_RE = re.compile(r"<dt\b[^>]*>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def score_extractability(
    html: str,
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Score hermetic extractability signals on ``html``; return findings + Evidence.

    Checks a single H1, a short answer-first lead paragraph, and list/Q&A
    structure. Hermetic: no network I/O and no LLM calls.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    h1_texts = [_plain_text(m.group(1)) for m in H1_RE.finditer(html)]
    h1_texts = [t for t in h1_texts if t]

    if len(h1_texts) == 1:
        findings.append(
            _finding("extractability.h1", "pass", "Page has a single clear H1.")
        )
        evidence_items.append(
            _evidence(
                f"Page has exactly one H1: '{h1_texts[0]}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    elif len(h1_texts) == 0:
        findings.append(
            _finding("extractability.h1", "fail", "Page has no H1 heading.")
        )
        evidence_items.append(
            _evidence(
                "No H1 element with text was observed on the page.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "extractability.h1",
                "fail",
                f"Page has {len(h1_texts)} H1 headings; answer topic is ambiguous.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Page has {len(h1_texts)} H1 elements: "
                + " vs ".join(f"'{t}'" for t in h1_texts)
                + ".",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        findings.append(
            _finding(
                "extractability.signal_conflict",
                "fail",
                "Multiple H1 headings conflict on the primary answer topic.",
            )
        )
        evidence_items.append(
            _evidence(
                "Multiple H1 headings disagree on the primary extractable topic.",
                source=source,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "More than one H1 makes the primary answer topic ambiguous "
                    "for extraction"
                ),
            )
        )

    paragraphs = [_plain_text(m.group(1)) for m in P_RE.finditer(html)]
    paragraphs = [t for t in paragraphs if t]
    if not paragraphs:
        findings.append(
            _finding(
                "extractability.lead",
                "fail",
                "Page has no paragraph lead for an answer-first extract.",
            )
        )
        evidence_items.append(
            _evidence(
                "No non-empty paragraph was observed near the start of the page.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        lead = paragraphs[0]
        word_count = _word_count(lead)
        if word_count <= LEAD_WORD_LIMIT:
            findings.append(
                _finding(
                    "extractability.lead",
                    "pass",
                    f"First paragraph is a short answer-first lead (≤{LEAD_WORD_LIMIT} words).",
                )
            )
            evidence_items.append(
                _evidence(
                    f"First paragraph has {word_count} words and is within the "
                    f"answer-first lead limit (≤{LEAD_WORD_LIMIT} words).",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
        else:
            findings.append(
                _finding(
                    "extractability.lead",
                    "fail",
                    f"First paragraph exceeds the answer-first lead limit "
                    f"(>{LEAD_WORD_LIMIT} words).",
                )
            )
            evidence_items.append(
                _evidence(
                    f"First paragraph has {word_count} words, above the "
                    f"answer-first lead limit (≤{LEAD_WORD_LIMIT} words).",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )

    structure_claim = _structure_claim(html)
    if structure_claim is not None:
        findings.append(
            _finding(
                "extractability.structure",
                "pass",
                "Page includes extractable list or Q&A structure.",
            )
        )
        evidence_items.append(
            _evidence(
                structure_claim,
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "extractability.structure",
                "fail",
                "Page lacks list, definition list, or question-style H2 structure.",
            )
        )
        evidence_items.append(
            _evidence(
                "No extractable list (≥2 items), definition list, or "
                "question-style H2 headings were observed.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    return {"findings": findings, "evidence": evidence_items}


def _structure_claim(html: str) -> str | None:
    for match in LIST_RE.finditer(html):
        if len(LI_RE.findall(match.group(2))) >= 2:
            return "Page includes an ordered or unordered list with at least 2 items."
    for match in DL_RE.finditer(html):
        if len(DT_RE.findall(match.group(1))) >= 1:
            return "Page includes a definition list with at least one term."
    question_h2 = [
        _plain_text(m.group(1))
        for m in H2_RE.finditer(html)
        if _plain_text(m.group(1)).endswith("?")
    ]
    if len(question_h2) >= 2:
        return (
            f"Page includes {len(question_h2)} question-style H2 headings "
            "usable as Q&A structure."
        )
    return None


def _plain_text(raw: str) -> str:
    text = TAG_RE.sub(" ", raw)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def _word_count(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


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
        "method": "html-extractability-parse",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
