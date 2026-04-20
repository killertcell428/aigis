"""Tests for the meeting-transcript classifier."""

from aigis.filters.meeting_transcript import (
    Segment,
    classify_transcript,
    safe_to_summarise,
)


def test_benign_meeting_is_public():
    segs = [
        Segment(speaker="Alice", ts=0.0, text="Morning everyone."),
        Segment(speaker="Bob", ts=5.0, text="Let's go over the agenda."),
    ]
    r = classify_transcript(segs)
    assert r.overall_sensitivity == "public"
    assert all(c.sensitivity == "public" for c in r.classifications)


def test_email_bumps_to_internal_and_redacts():
    segs = [
        Segment(speaker="A", ts=0, text="Send it to bob.smith@example.com please."),
    ]
    r = classify_transcript(segs)
    assert r.overall_sensitivity == "internal"
    assert "email" in r.classifications[0].pii_kinds
    assert "bob.smith@example.com" not in r.redacted_segments[0].text
    assert "[REDACTED_EMAIL_" in r.redacted_segments[0].text


def test_mynumber_triggers_regulated():
    segs = [
        Segment(speaker="HR", ts=0, text="マイナンバーは 123456789012 です。"),
    ]
    r = classify_transcript(segs)
    assert r.overall_sensitivity == "regulated"
    assert "mynumber" in r.classifications[0].pii_kinds


def test_phi_triggers_regulated():
    segs = [
        Segment(speaker="Doc", ts=0, text="The patient's diagnosis is hypertension."),
    ]
    r = classify_transcript(segs)
    assert r.overall_sensitivity == "regulated"


def test_salary_triggers_confidential():
    segs = [
        Segment(speaker="CFO", ts=0, text="給与の引き上げは来期から。"),
    ]
    r = classify_transcript(segs)
    assert r.overall_sensitivity == "confidential"


def test_consent_withdrawal_propagates_backwards():
    segs = [
        Segment(speaker="A", ts=0, text="Hi, here's my idea."),
        Segment(speaker="A", ts=4, text="My new project is..."),
        Segment(speaker="B", ts=9, text="Actually, please stop recording this."),
        Segment(speaker="A", ts=12, text="OK, sorry."),
    ]
    r = classify_transcript(segs, consent_lookback_seconds=10)
    assert r.classifications[2].consent_flag  # the speaker who withdrew
    # The two prior segments within the 10s lookback must also be flagged.
    assert r.classifications[1].consent_flag
    assert r.classifications[0].consent_flag
    # The segment AFTER withdrawal is not lookback-flagged by this pass.
    assert not r.classifications[3].consent_flag


def test_safe_to_summarise_gate():
    confidential = classify_transcript(
        [Segment(speaker="x", ts=0, text="We are planning a merger.")]
    )
    assert not safe_to_summarise(confidential, target_clearance="internal")
    assert safe_to_summarise(confidential, target_clearance="confidential")


def test_japanese_consent_phrase_detected():
    segs = [Segment(speaker="A", ts=0, text="録音しないでください。")]
    r = classify_transcript(segs)
    assert r.classifications[0].consent_flag
