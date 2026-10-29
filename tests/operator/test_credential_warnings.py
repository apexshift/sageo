"""Operator bridge: warn-and-allow when Connector ids lack credentials."""

from __future__ import annotations

from sageo.operator import connector_credential_warnings


def test_no_warnings_when_optional_ids_omitted() -> None:
    assert connector_credential_warnings(gsc_property=None, ga4_property=None) == ()
    assert connector_credential_warnings(gsc_property="", ga4_property="  ") == ()


def test_warn_when_gsc_id_set_without_credentials() -> None:
    warnings = connector_credential_warnings(
        gsc_property="sc-domain:example.com",
        ga4_property=None,
        env={},
    )
    assert len(warnings) == 1
    assert "GSC" in warnings[0]
    assert "missing" in warnings[0].lower() or "without" in warnings[0].lower()


def test_warn_when_ga4_id_set_without_credentials() -> None:
    warnings = connector_credential_warnings(
        gsc_property=None,
        ga4_property="properties/123",
        env={"GA4_PROPERTY_ID": ""},
    )
    assert len(warnings) == 1
    assert "GA4" in warnings[0]


def test_no_warning_when_gsc_credentials_present() -> None:
    warnings = connector_credential_warnings(
        gsc_property="sc-domain:example.com",
        ga4_property=None,
        env={
            "GSC_CLIENT_EMAIL": "bot@example.com",
            "GSC_PRIVATE_KEY": "-----BEGIN KEY-----",
            "GSC_PROPERTY_URL": "sc-domain:example.com",
        },
    )
    assert warnings == ()


def test_warn_and_allow_both_connectors() -> None:
    warnings = connector_credential_warnings(
        gsc_property="sc-domain:example.com",
        ga4_property="properties/9",
        env={},
    )
    assert len(warnings) == 2
    assert any("GSC" in w for w in warnings)
    assert any("GA4" in w for w in warnings)
