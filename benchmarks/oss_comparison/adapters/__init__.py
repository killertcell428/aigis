"""Pluggable adapters for OSS guardrail tools.

Each adapter exposes the same interface (see ``base.Adapter``) so the driver
can swap implementations without knowing which tool it is talking to.
"""

from benchmarks.oss_comparison.adapters.base import Adapter, Verdict

__all__ = ["Adapter", "Verdict"]
