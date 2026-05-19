# Pending: CIMD Private-IP SSRF Coverage

**Date:** 2026-05-19
**Domain:** agent-tool-abuse (cycle 1, fourth pass)
**Research basis:** `research/2026-05-19T09-00_1-agent-tool-abuse.md`

---

## Title

Extend SSRF detection to cover RFC 1918 / link-local private IP ranges in MCP Client ID Metadata Document (CIMD) URLs

## Motivation

The MCP November 2025 specification update (2025-11-25) introduced Client ID Metadata Documents (CIMD): a client identifies itself by registering a URL that the Authorization Server must fetch to retrieve client metadata. Post-release analysis identified that CIMD URLs are themselves a new SSRF vector: a malicious MCP client can register a CIMD URL pointing at an internal endpoint (10.x.x.x, 192.168.x.x, or the IMDS address 169.254.169.254), causing the Authorization Server to make requests to internal infrastructure.

The existing `mcp_ssrf_metadata_endpoint` rule covers cloud IMDS addresses (169.254.169.254, metadata.google.internal, etc.) but does NOT cover private IP ranges from RFC 1918:
- Class A: 10.0.0.0/8
- Class B: 172.16.0.0/12
- Class C: 192.168.0.0/16

A CIMD URL like `https://10.0.0.1/admin/` or `https://192.168.1.1/config/` embedded in an MCP client registration could cause the AS to reach internal services.

## Proposed Change

Extend `mcp_ssrf_metadata_endpoint` or add a sibling rule `mcp_ssrf_private_ip` covering:
- `https?://10\.\d{1,3}\.\d{1,3}\.\d{1,3}`
- `https?://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}`
- `https?://192\.168\.\d{1,3}\.\d{1,3}`

Combined with `client_id` or `client_metadata_url` field context to limit FPs.

## Why Held Back

Private IP addresses appear legitimately in development/staging environment tool descriptions. Without source-aware scanning (tool description vs. OAuth metadata vs. tool response), the FP rate could be high for developers who access local services via MCP.

The CIMD context (client metadata registration) is the specific concern — the rule should ideally apply only when the IP appears in the context of OAuth client registration fields (`client_id`, `client_metadata_url`, `authorization_endpoint`).

## Suggested Next Step for Human Reviewer

1. Implement as a compound pattern: `(?:client_id|client_metadata_url|jwks_uri).{0,100}https?://(?:10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)` to restrict the scope to OAuth metadata field contexts.
2. Review FP rate against a corpus of legitimate OAuth client registration documents.
3. Source: https://modelcontextprotocol.io/specification/2025-11-25/changelog and https://aaronparecki.com/2025/11/25/1/mcp-authorization-spec-update
