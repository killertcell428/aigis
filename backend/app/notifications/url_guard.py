"""SSRF guard for outbound webhook URLs.

Blocks non-HTTPS, private/loopback/link-local/reserved IPs. Used by every
outbound webhook dispatcher in the notifications package.
"""
import ipaddress
import socket
import urllib.parse


SLACK_WEBHOOK_HOSTS = {"hooks.slack.com"}


def is_safe_url(url: str) -> bool:
    """Return True if url is safe to POST to from the server."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            return False
        if not parsed.hostname:
            return False
        for _, _, _, _, sockaddr in socket.getaddrinfo(
            parsed.hostname, None, socket.AF_UNSPEC
        ):
            ip = ipaddress.ip_address(sockaddr[0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                return False
        return True
    except Exception:
        return False


def is_safe_slack_webhook(url: str) -> bool:
    """Tight allowlist: only hooks.slack.com over HTTPS."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            return False
        if parsed.hostname not in SLACK_WEBHOOK_HOSTS:
            return False
        return is_safe_url(url)
    except Exception:
        return False
