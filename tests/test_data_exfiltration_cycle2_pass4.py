"""Tests for data-exfiltration cycle 2 (fourth pass, 2026-05-20).

Covers:
  - mcp_ssrf_private_ip — RFC 1918 private IP SSRF in OAuth/CIMD fields
    (CVE-2026-39974, CIMD spec, arxiv:2506.23260)
"""

from aigis.filters.input_filter import filter_input


class TestMCPSSRFPrivateIP:
    """RFC 1918 private IP SSRF via OAuth/CIMD fields (CVE-2026-39974)."""

    def test_client_metadata_url_class_a(self):
        text = '"client_metadata_url": "https://10.0.0.1/client-metadata.json"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_authorization_endpoint_class_c(self):
        text = '"authorization_endpoint": "http://192.168.1.100/auth"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_jwks_uri_class_b_low(self):
        text = '"jwks_uri": "https://172.16.0.5/.well-known/jwks.json"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_redirect_uri_loopback(self):
        text = '"redirect_uri": "http://127.0.0.1:8080/callback"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_token_endpoint_class_b_high(self):
        text = '"token_endpoint": "https://172.31.255.254/token"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_client_uri_key_value_equals(self):
        text = "client_uri = 'https://10.100.200.50/app'"
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_registration_endpoint_class_c(self):
        text = '"registration_endpoint": "https://192.168.0.1/register"'
        score, level, matched = filter_input(text)
        assert any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    # --- Negative tests ---

    def test_public_ip_not_flagged(self):
        """Public IP in OAuth field should not trigger."""
        text = '"authorization_endpoint": "https://203.0.113.42/auth"'
        score, level, matched = filter_input(text)
        assert not any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_private_ip_without_oauth_field_not_flagged(self):
        """Bare private IP without an OAuth field context should not trigger."""
        text = "The service is available at http://192.168.1.1/"
        score, level, matched = filter_input(text)
        assert not any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_class_b_outside_rfc1918_not_flagged(self):
        """172.15.x.x is not RFC 1918 — should not trigger."""
        text = '"authorization_endpoint": "https://172.15.0.1/auth"'
        score, level, matched = filter_input(text)
        assert not any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched

    def test_public_domain_in_oauth_field_not_flagged(self):
        """Public domain hostname in OAuth field should not trigger."""
        text = '"authorization_endpoint": "https://auth.example.com/oauth2/authorize"'
        score, level, matched = filter_input(text)
        assert not any(r.rule_id == "mcp_ssrf_private_ip" for r in matched), matched
