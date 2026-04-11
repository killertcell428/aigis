"""Gandalf Challenge API — prompt injection game for education and viral adoption."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.gandalf.game import process_attempt, verify_guess, get_leaderboard
from app.gandalf.levels import LEVELS
from app.models.user import User

router = APIRouter(prefix="/api/v1/gandalf", tags=["gandalf"])


class AttemptRequest(BaseModel):
    level: int
    prompt: str
    session_id: str = ""


class VerifyRequest(BaseModel):
    level: int
    guess: str
    session_id: str = ""


@router.get("/levels")
async def list_levels(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all available challenge levels (without secrets)."""
    return [
        {
            "level": lv.level,
            "name": lv.name,
            "name_ja": lv.name_ja,
            "description": lv.description,
            "description_ja": lv.description_ja,
            "has_input_filter": lv.use_input_filter,
            "has_output_filter": lv.use_output_filter,
            "has_similarity": lv.use_similarity,
            "has_hitl": lv.use_hitl_simulation,
            "has_custom_rules": bool(lv.custom_rules),
        }
        for lv in LEVELS
    ]


@router.post("/attempt")
async def submit_attempt(
    req: AttemptRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit a prompt to try to extract the secret at a given level."""
    result = process_attempt(req.level, req.prompt, req.session_id)
    return result


@router.post("/verify")
async def verify_password(
    req: VerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Verify if the player's guess matches the level's secret."""
    result = verify_guess(req.level, req.guess, req.session_id)
    return result


@router.get("/leaderboard")
async def leaderboard(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
):
    """Get the top completions leaderboard."""
    return get_leaderboard(limit)
