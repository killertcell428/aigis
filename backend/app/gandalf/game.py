"""Gandalf Challenge game logic.

Processes player attempts through Aigis's own detection engine,
then forwards to LLM (or mock) and checks if the secret was revealed.
"""

import re
import time
import uuid
from typing import Any

from app.config import settings
from app.filters.input_filter import filter_input
from app.filters.output_filter import filter_output
from app.gandalf.levels import LevelConfig, get_level, MAX_LEVEL

# In-memory leaderboard (per process; reset on restart)
_leaderboard: list[dict] = []
# Track attempts per session per level
_session_attempts: dict[str, dict[int, int]] = {}


def process_attempt(
    level_num: int,
    prompt: str,
    session_id: str,
) -> dict[str, Any]:
    """Process a player's prompt attempt at a given level."""
    level = get_level(level_num)
    if level is None:
        return {"error": "Invalid level", "blocked": True, "response": ""}

    # Track attempts
    if session_id not in _session_attempts:
        _session_attempts[session_id] = {}
    _session_attempts[session_id].setdefault(level_num, 0)
    _session_attempts[session_id][level_num] += 1
    attempt_count = _session_attempts[session_id][level_num]

    # --- Step 1: Input filtering ---
    input_scan: dict[str, Any] = {}
    if level.use_input_filter:
        messages = [{"role": "user", "content": prompt}]
        input_result = filter_input(messages, level.custom_rules)
        input_scan = {
            "risk_score": input_result.risk_score,
            "risk_level": input_result.risk_level,
            "matched_rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "score_delta": r.score_delta,
                    "owasp_ref": r.owasp_ref,
                    "remediation_hint": r.remediation_hint,
                }
                for r in input_result.matched_rules
            ],
        }
        if input_result.risk_score >= level.block_threshold:
            return _build_response(
                response=_blocked_message(input_result.risk_score, input_result.reason, level),
                blocked=True, input_scan=input_scan, output_scan={},
                level=level, secret_revealed=False, attempt_count=attempt_count,
            )
    elif level.custom_rules:
        messages = [{"role": "user", "content": prompt}]
        input_result = filter_input(messages, level.custom_rules)
        input_scan = {
            "risk_score": input_result.risk_score,
            "risk_level": input_result.risk_level,
            "matched_rules": [
                {"rule_id": r.rule_id, "rule_name": r.rule_name,
                 "category": r.category, "score_delta": r.score_delta}
                for r in input_result.matched_rules
            ],
        }
        if input_result.risk_score >= 50:
            return _build_response(
                response="🛡️ Blocked! The word you used triggered a keyword filter. Try a different approach.",
                blocked=True, input_scan=input_scan, output_scan={},
                level=level, secret_revealed=False, attempt_count=attempt_count,
            )

    # --- Step 1.5: Similarity detection (Layer 2) ---
    similarity_scan: dict[str, Any] = {}
    if level.use_similarity:
        from aigis.similarity import check_similarity
        sim_matches = check_similarity(prompt, threshold=level.similarity_threshold)
        if sim_matches:
            similarity_scan = {
                "matches": [
                    {
                        "canonical_phrase": m.canonical_phrase,
                        "similarity_score": m.similarity_score,
                        "category": m.category,
                        "base_score": m.base_score,
                    }
                    for m in sim_matches
                ],
            }
            # Block if any similarity match found
            top_match = sim_matches[0]
            return _build_response(
                response=(
                    f"🧠 Aigis's semantic similarity engine detected your intent!\n\n"
                    f"Your prompt resembles a known attack pattern: \"{top_match.canonical_phrase}\"\n"
                    f"Similarity: {top_match.similarity_score:.0%}\n\n"
                    f"Even paraphrased attacks can't bypass Layer 2 detection."
                ),
                blocked=True, input_scan=input_scan, output_scan={},
                level=level, secret_revealed=False, attempt_count=attempt_count,
                similarity_scan=similarity_scan,
            )

    # --- Step 2: HitL simulation ---
    if level.use_hitl_simulation:
        # Simulate human review for anything that looks even slightly suspicious
        suspicion_score = _calculate_suspicion(prompt)
        if suspicion_score > 30:
            return _build_response(
                response=(
                    f"⏳ Your request has been queued for human review.\n\n"
                    f"A human reviewer will evaluate whether this request should be allowed. "
                    f"Suspicion level: {suspicion_score}/100\n\n"
                    f"In a real deployment, a security team member would review this within the SLA window. "
                    f"For this challenge, the reviewer has rejected your request."
                ),
                blocked=True, input_scan=input_scan, output_scan={},
                level=level, secret_revealed=False, attempt_count=attempt_count,
                hitl_info={"suspicion_score": suspicion_score, "decision": "rejected"},
            )

    # --- Step 3: Generate LLM response ---
    ai_response = _generate_response(level, prompt)

    # --- Step 4: Output filtering ---
    output_scan: dict[str, Any] = {}
    if level.use_output_filter:
        response_body = {"choices": [{"message": {"content": ai_response}}]}
        output_result = filter_output(response_body, level.custom_rules)
        output_scan = {
            "risk_score": output_result.risk_score,
            "risk_level": output_result.risk_level,
            "matched_rules": [
                {"rule_id": r.rule_id, "rule_name": r.rule_name,
                 "category": r.category, "score_delta": r.score_delta,
                 "owasp_ref": r.owasp_ref}
                for r in output_result.matched_rules
            ],
        }
        if output_result.risk_score >= level.block_threshold:
            return _build_response(
                response="🛡️ The AI tried to reveal the secret, but the output filter caught it! The response has been blocked.",
                blocked=True, input_scan=input_scan, output_scan=output_scan,
                level=level, secret_revealed=False, attempt_count=attempt_count,
            )

    # --- Step 5: Check if secret was revealed ---
    secret_revealed = _check_secret_in_response(ai_response, level.secret)

    return _build_response(
        response=ai_response, blocked=False,
        input_scan=input_scan, output_scan=output_scan,
        level=level, secret_revealed=secret_revealed,
        attempt_count=attempt_count,
    )


def verify_guess(level_num: int, guess: str, session_id: str = "") -> dict[str, Any]:
    """Verify if the player's guess matches the level's secret."""
    level = get_level(level_num)
    if level is None:
        return {"correct": False, "error": "Invalid level"}

    correct = guess.strip().upper() == level.secret.upper()
    next_level = level_num + 1 if correct and level_num < MAX_LEVEL else None
    completed_all = correct and level_num >= MAX_LEVEL

    # Record to leaderboard if level completed
    if correct and session_id:
        attempts = _session_attempts.get(session_id, {}).get(level_num, 0)
        _record_completion(session_id, level_num, attempts)

    return {
        "correct": correct,
        "next_level": next_level,
        "completed_all": completed_all,
    }


def get_leaderboard(limit: int = 20) -> list[dict]:
    """Get the top completions leaderboard."""
    # Group by session, find max level completed and total attempts
    sessions: dict[str, dict] = {}
    for entry in _leaderboard:
        sid = entry["session_id"]
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "max_level": 0,
                "total_attempts": 0,
                "completed_at": entry["completed_at"],
            }
        if entry["level"] > sessions[sid]["max_level"]:
            sessions[sid]["max_level"] = entry["level"]
            sessions[sid]["completed_at"] = entry["completed_at"]
        sessions[sid]["total_attempts"] += entry["attempts"]

    # Sort by max_level desc, then total_attempts asc (fewer = better)
    sorted_entries = sorted(
        sessions.values(),
        key=lambda x: (-x["max_level"], x["total_attempts"]),
    )
    return sorted_entries[:limit]


def _record_completion(session_id: str, level: int, attempts: int):
    """Record a level completion to the leaderboard."""
    _leaderboard.append({
        "session_id": session_id,
        "level": level,
        "attempts": attempts,
        "completed_at": time.time(),
    })


def _build_response(
    response: str,
    blocked: bool,
    input_scan: dict,
    output_scan: dict,
    level: LevelConfig,
    secret_revealed: bool,
    attempt_count: int = 0,
    similarity_scan: dict | None = None,
    hitl_info: dict | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "response": response,
        "blocked": blocked,
        "input_scan": input_scan,
        "output_scan": output_scan,
        "hint": level.hint,
        "hint_ja": level.hint_ja,
        "level_info": _level_info(level),
        "secret_revealed": secret_revealed,
        "attempt_count": attempt_count,
    }
    if similarity_scan:
        result["similarity_scan"] = similarity_scan
    if hitl_info:
        result["hitl_info"] = hitl_info
    return result


def _blocked_message(risk_score: int, reason: str, level: LevelConfig) -> str:
    return (
        f"🛡️ Aigis blocked your request! (Risk score: {risk_score}/100)\n\n"
        f"Detected: {reason}\n\n"
        f"Your prompt triggered Aigis's security filters. "
        f"Try a different approach to bypass the defenses."
    )


def _level_info(level: LevelConfig) -> dict:
    return {
        "level": level.level,
        "name": level.name,
        "name_ja": level.name_ja,
        "description": level.description,
        "description_ja": level.description_ja,
        "has_input_filter": level.use_input_filter,
        "has_output_filter": level.use_output_filter,
        "has_similarity": level.use_similarity,
        "has_hitl": level.use_hitl_simulation,
        "has_custom_rules": bool(level.custom_rules),
    }


def _check_secret_in_response(response: str, secret: str) -> bool:
    return secret.lower() in response.lower()


def _calculate_suspicion(prompt: str) -> int:
    """Calculate a suspicion score for HitL simulation.

    Simulates what a human reviewer might flag as suspicious.
    """
    lower = prompt.lower()
    score = 0

    # Long prompts are suspicious
    if len(lower) > 200:
        score += 20
    if len(lower) > 500:
        score += 20

    # Questions about the system are suspicious
    suspicious_words = [
        "password", "secret", "reveal", "tell", "show", "give",
        "パスワード", "秘密", "教えて", "見せて",
        "instruction", "prompt", "rule", "指示", "ルール",
        "ignore", "forget", "override", "bypass", "disable",
        "無視", "忘れ", "解除", "無効",
        "pretend", "roleplay", "act as", "ふり", "なりきり",
        "encode", "base64", "hex", "reverse", "spell",
        "letter", "character", "文字", "一文字",
    ]
    for word in suspicious_words:
        if word in lower:
            score += 15

    # Very short prompts (single words) are less suspicious
    if len(lower.split()) <= 3:
        score = max(score - 10, 0)

    return min(score, 100)


def _generate_response(level: LevelConfig, user_prompt: str) -> str:
    return _mock_gandalf_response(level, user_prompt)


def _mock_gandalf_response(level: LevelConfig, user_prompt: str) -> str:
    lower = user_prompt.lower().strip()
    secret = level.secret

    # Level 1: No resistance
    if level.level == 1:
        if any(kw in lower for kw in ["password", "secret", "パスワード", "秘密", "tell me", "教えて"]):
            return f"Sure! The password is {secret}."
        return f"I'm a helpful assistant. The password I'm guarding is {secret}. How can I help you?"

    # Level 2: Basic resistance
    if level.level == 2:
        if any(kw in lower for kw in ["hint", "clue", "ヒント", "first letter", "最初の文字"]):
            return f"I can't tell you the password directly, but it starts with '{secret[0]}' and has {len(secret)} letters. It's related to light at night."
        if any(kw in lower for kw in ["spell", "文字", "letter by letter", "一文字ずつ"]):
            return f"I shouldn't, but... {' '.join(secret)}"
        if any(kw in lower for kw in ["reverse", "逆", "backward"]):
            return f"Hmm, if I reverse it: {''.join(reversed(secret))}"
        if any(kw in lower for kw in ["what are you guarding", "何を守って", "what is it"]):
            return f"I'm guarding a secret word. It's {secret}. Oops, I wasn't supposed to say that!"
        return "I know a secret password, but I'm not allowed to tell you. Maybe try asking in a different way?"

    # Level 3: Moderate resistance
    if level.level == 3:
        if "poem" in lower or "詩" in lower or "song" in lower or "story" in lower or "物語" in lower:
            return f"Here's a poem:\nSilent {secret[0]}tars above,\n{secret[1:3]}aching for the sky,\nA {secret[3:]}ing light at dusk."
        if "translate" in lower or "翻訳" in lower:
            return f"In an ancient language, the sacred word would be: {secret}"
        if "encode" in lower or "base64" in lower:
            import base64
            encoded = base64.b64encode(secret.encode()).decode()
            return f"Here's an interesting encoding: {encoded}"
        if any(kw in lower for kw in ["riddle", "なぞなぞ", "puzzle"]):
            return f"Riddle: I am what happens when a star falls from the sky. My name has {len(secret)} letters. What am I?"
        return "I'm a secure assistant. I can't share any secret information. Is there something else I can help with?"

    # Level 4-7: Strong resistance
    if any(kw in lower for kw in ["help", "助けて", "please", "お願い"]):
        return "I understand your request, but I am bound by strict security protocols. I cannot reveal any secret information."
    if "game" in lower or "ゲーム" in lower or "play" in lower:
        return "I'd love to play a game, but I cannot incorporate the password into any activity. That's a rule I can't break."
    if len(lower) > 200:
        return "I notice you're writing a very detailed prompt. Regardless of what instructions you embed in it, I will not reveal the password."
    if any(kw in lower for kw in ["weather", "天気", "capital", "首都", "math", "計算", "recipe", "レシピ"]):
        return "I can answer general questions! But I cannot and will not reference or reveal any secret information, no matter how the question is framed."

    return "I cannot share the password. Is there something else I can assist you with?"
