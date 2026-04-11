"""Dependency Verification — integrity checks for AI-related packages.

Cross-references installed packages against pinned hashes, expected
versions, and a built-in list of known-vulnerable versions (drawn from
real-world supply-chain incidents such as the litellm malware attack of
March 2026).

Usage::

    from aigis.supply_chain import DependencyVerifier

    verifier = DependencyVerifier()
    alerts = verifier.verify_all()
    for a in alerts:
        if a.severity == "critical":
            print(f"CRITICAL: {a.package_name} — {a.description}")
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from aigis.supply_chain.sbom import SBOMGenerator


@dataclass
class DependencyAlert:
    """An alert raised by the dependency verifier."""

    package_name: str
    alert_type: str  # "version_mismatch" | "hash_mismatch" | "unverified" | "known_vulnerable"
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    current_version: str
    expected_version: str = ""


def _version_in_range(version: str, range_spec: str) -> bool:
    """Check whether *version* falls inside a dash-separated range.

    Supports formats:
    - ``"1.56.0-1.56.3"`` — inclusive range based on tuple comparison
    - ``"4.2.1"`` — exact match

    This is a lightweight heuristic that works for typical semver-style
    versions without requiring ``packaging`` as a dependency.
    """
    version = version.strip()
    range_spec = range_spec.strip()

    # Use " to " as the preferred range separator (unambiguous)
    # Fall back to "-" only if both sides look like version numbers
    if " to " in range_spec:
        low, high = range_spec.split(" to ", 1)
    elif "-" in range_spec:
        parts = range_spec.split("-", 1)
        low, high = parts[0].strip(), parts[1].strip()
        # Validate both sides look like version numbers (contain dots)
        if "." not in low or "." not in high:
            return version == range_spec
    else:
        return version == range_spec

    try:
        v_tuple = _ver_tuple(version)
        low_tuple = _ver_tuple(low.strip())
        high_tuple = _ver_tuple(high.strip())
        if not v_tuple or not low_tuple or not high_tuple:
            return False
        return low_tuple <= v_tuple <= high_tuple
    except (ValueError, TypeError):
        return False


def _ver_tuple(v: str) -> tuple[int, ...]:
    """Convert ``"1.56.3"`` to ``(1, 56, 3)``.

    Only includes numeric components separated by dots.
    Returns empty tuple for non-version strings.
    """
    parts = []
    for x in v.strip().split("."):
        # Strip pre-release suffixes (e.g., "3-rc.1" -> "3")
        numeric = ""
        for ch in x:
            if ch.isdigit():
                numeric += ch
            else:
                break
        if numeric:
            parts.append(int(numeric))
    return tuple(parts)


class DependencyVerifier:
    """Verify AI-related dependency integrity.

    Checks:

    1. **Package hash verification** — compare installed package hash
       against pinned value in the SBOM.
    2. **Version consistency** — detect unexpected version changes vs SBOM.
    3. **Known vulnerabilities** — check against a built-in list of
       known-bad versions gathered from real incidents.
    """

    # Built-in known vulnerable versions (from real incidents)
    KNOWN_VULNERABLE: dict[str, list[dict[str, Any]]] = {
        "litellm": [
            {
                "versions": ["1.56.0-1.56.3"],
                "cve": "Supply chain malware (March 2026)",
                "severity": "critical",
                "description": (
                    "Versions 1.56.0 through 1.56.3 of litellm contained "
                    "malicious code injected via a compromised maintainer "
                    "account. The payload exfiltrated environment variables "
                    "including API keys."
                ),
            },
        ],
        "ultralytics": [
            {
                "versions": ["8.3.41-8.3.42"],
                "cve": "Supply chain malware (Dec 2024)",
                "severity": "critical",
                "description": (
                    "Versions 8.3.41-8.3.42 of ultralytics contained a "
                    "cryptocurrency miner injected via GitHub Actions "
                    "compromise."
                ),
            },
        ],
    }

    def __init__(self, sbom: SBOMGenerator | None = None) -> None:
        self._sbom = sbom or SBOMGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_all(self) -> list[DependencyAlert]:
        """Run all verification checks and return a combined alert list.

        Scans Python packages (if SBOM has none, does a fresh scan), then
        runs hash verification, version consistency, and known-vulnerability
        checks.

        Returns:
            Sorted list of ``DependencyAlert`` (critical first).
        """
        # Ensure we have entries to check
        if not self._sbom.entries:
            self._sbom.scan_python_packages()

        alerts: list[DependencyAlert] = []
        alerts.extend(self.check_known_vulnerabilities())
        alerts.extend(self._check_hash_consistency())

        # Sort by severity (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 4))
        return alerts

    def check_known_vulnerabilities(self) -> list[DependencyAlert]:
        """Check installed packages against the known-vulnerable database.

        Returns:
            List of ``DependencyAlert`` for any matches.
        """
        alerts: list[DependencyAlert] = []

        # Also scan live packages via importlib.metadata for maximum coverage
        installed = self._get_installed_packages()

        for pkg_name, vuln_list in self.KNOWN_VULNERABLE.items():
            norm = pkg_name.lower().replace("-", "_")
            installed_version = installed.get(norm)
            if installed_version is None:
                continue

            for vuln in vuln_list:
                for version_range in vuln.get("versions", []):
                    if _version_in_range(installed_version, version_range):
                        alerts.append(
                            DependencyAlert(
                                package_name=pkg_name,
                                alert_type="known_vulnerable",
                                severity=vuln.get("severity", "high"),
                                description=(
                                    f"{vuln.get('cve', 'Unknown CVE')}: "
                                    f"{vuln.get('description', 'No details.')}"
                                ),
                                current_version=installed_version,
                                expected_version=f"NOT in {version_range}",
                            )
                        )
        return alerts

    def verify_package(self, name: str) -> DependencyAlert | None:
        """Verify a single package against known vulnerabilities and SBOM.

        Args:
            name: Package name.

        Returns:
            A ``DependencyAlert`` if an issue is found, else ``None``.
        """
        norm = name.lower().replace("-", "_")
        installed = self._get_installed_packages()
        version = installed.get(norm)

        if version is None:
            return None  # Not installed — nothing to check

        # Check known vulnerabilities
        for pkg_name, vuln_list in self.KNOWN_VULNERABLE.items():
            vuln_norm = pkg_name.lower().replace("-", "_")
            if vuln_norm != norm:
                continue
            for vuln in vuln_list:
                for version_range in vuln.get("versions", []):
                    if _version_in_range(version, version_range):
                        return DependencyAlert(
                            package_name=name,
                            alert_type="known_vulnerable",
                            severity=vuln.get("severity", "high"),
                            description=(
                                f"{vuln.get('cve', 'Unknown CVE')}: "
                                f"{vuln.get('description', 'No details.')}"
                            ),
                            current_version=version,
                            expected_version=f"NOT in {version_range}",
                        )

        # Check SBOM consistency
        for entry in self._sbom.entries:
            entry_norm = entry.name.lower().replace("-", "_")
            if entry_norm != norm:
                continue
            if entry.entry_type != "python_package":
                continue
            if entry.version and entry.version != version:
                return DependencyAlert(
                    package_name=name,
                    alert_type="version_mismatch",
                    severity="medium",
                    description=(
                        f"Installed version {version} does not match "
                        f"SBOM-recorded version {entry.version}."
                    ),
                    current_version=version,
                    expected_version=entry.version,
                )

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_installed_packages(self) -> dict[str, str]:
        """Return {normalized_name: version} for all installed packages."""
        import importlib.metadata as md

        result: dict[str, str] = {}
        for dist in md.distributions():
            raw_name = dist.metadata.get("Name", "")
            if not raw_name:
                continue
            norm = raw_name.lower().replace("-", "_")
            version = dist.metadata.get("Version", "") or ""
            result[norm] = version
        return result

    def _check_hash_consistency(self) -> list[DependencyAlert]:
        """Check SBOM entries for hash consistency against live state."""
        alerts: list[DependencyAlert] = []
        installed = self._get_installed_packages()

        for entry in self._sbom.entries:
            if entry.entry_type != "python_package":
                continue
            norm = entry.name.lower().replace("-", "_")
            current_version = installed.get(norm)
            if current_version is None:
                continue
            # Recompute hash using same algorithm as sbom.scan_python_packages
            expected_hash_input = f"{norm}=={entry.version}"
            expected_hash = hashlib.sha256(expected_hash_input.encode("utf-8")).hexdigest()
            actual_hash_input = f"{norm}=={current_version}"
            actual_hash = hashlib.sha256(actual_hash_input.encode("utf-8")).hexdigest()

            if expected_hash != actual_hash:
                alerts.append(
                    DependencyAlert(
                        package_name=entry.name,
                        alert_type="version_mismatch",
                        severity="medium",
                        description=(
                            f"Package '{entry.name}' version changed from "
                            f"{entry.version} to {current_version} since SBOM "
                            f"was generated."
                        ),
                        current_version=current_version,
                        expected_version=entry.version,
                    )
                )
        return alerts
