"""Cross-Session Analysis -- detect attacks that span multiple sessions.

Detects temporally decoupled attacks such as memory poisoning planted
in one session that activates in a later session, slow escalation across
conversations, and recurring threat patterns.

Academic basis:
  - arxiv 2604.02623: temporally decoupled memory poisoning

Usage::

    from aigis.cross_session import SessionStore, CrossSessionCorrelator, SleeperDetector

    store = SessionStore()
    correlator = CrossSessionCorrelator(store)
    alerts = correlator.analyze(window_days=30)

    detector = SleeperDetector(store)
    sleeper_alerts = detector.scan(current_session)
"""

from aigis.cross_session.correlator import CorrelationAlert, CrossSessionCorrelator
from aigis.cross_session.sleeper import SleeperAlert, SleeperDetector
from aigis.cross_session.store import SessionRecord, SessionStore

__all__ = [
    "SessionStore",
    "SessionRecord",
    "CrossSessionCorrelator",
    "CorrelationAlert",
    "SleeperDetector",
    "SleeperAlert",
]
