"""Credential gate seam: missing env → refuse start + NHV Evidence."""

from __future__ import annotations

from sageo.connectors.credentials import CredentialCheck, require_credentials


def test_require_credentials_ok_when_all_keys_present() -> None:
    result = require_credentials(
        {"GSC_CLIENT_EMAIL": "sa@example.com", "GSC_PRIVATE_KEY": "pem", "GSC_PROPERTY_URL": "https://example.com/"},
        ("GSC_CLIENT_EMAIL", "GSC_PRIVATE_KEY", "GSC_PROPERTY_URL"),
        pack="gsc",
        tool="startup",
        claim="GSC Connector cannot start without credentials",
        observed_at="2026-10-28T12:00:00+00:00",
    )
    assert result.ok is True
    assert result.evidence is None


def test_require_credentials_refuses_start_when_key_missing() -> None:
    result = require_credentials(
        {"GSC_CLIENT_EMAIL": "sa@example.com", "GSC_PRIVATE_KEY": "", "GSC_PROPERTY_URL": "https://example.com/"},
        ("GSC_CLIENT_EMAIL", "GSC_PRIVATE_KEY", "GSC_PROPERTY_URL"),
        pack="gsc",
        tool="startup",
        claim="GSC Connector cannot start without credentials",
        observed_at="2026-10-28T12:00:00+00:00",
    )
    assert result.ok is False
    assert result.evidence == {
        "claim": "GSC Connector cannot start without credentials",
        "source": "gsc/startup",
        "observed_at": "2026-10-28T12:00:00+00:00",
        "confidence": "needs_human_verification",
        "verification_reason": "missing_credentials",
    }


def test_require_credentials_refuses_when_key_absent_from_env() -> None:
    result = require_credentials(
        {"GA4_PROPERTY_ID": "123"},
        ("GA4_PROPERTY_ID", "GA4_CREDENTIALS_JSON"),
        pack="ga4",
        tool="startup",
        claim="GA4 Connector cannot start without credentials",
        observed_at="2026-10-28T12:00:00+00:00",
    )
    assert isinstance(result, CredentialCheck)
    assert result.ok is False
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "missing_credentials"
    assert result.evidence["source"] == "ga4/startup"
