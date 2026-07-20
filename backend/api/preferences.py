"""Preferences and goals routes (BUILD_SPEC §9)."""

import uuid

from fastapi import APIRouter, Depends, Request

from backend.api.responses import ok
from backend.application import goals as goals_service
from backend.application import preferences as prefs_service
from backend.auth.dependencies import current_user_id
from backend.schemas.identity import GoalIn, GoalOut, PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api/v1", tags=["preferences", "goals"])


@router.get("/preferences")
def read_preferences(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, PreferencesOut(values=prefs_service.read_preferences(user_id)))


@router.put("/preferences")
def write_preferences(
    request: Request, body: PreferencesIn, user_id: uuid.UUID = Depends(current_user_id)
):
    return ok(request, PreferencesOut(values=prefs_service.write_preferences(user_id, body.values)))


@router.get("/goals")
def list_goals(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, [GoalOut.model_validate(g) for g in goals_service.list_goals(user_id)])


@router.post("/goals")
def create_goal(request: Request, body: GoalIn, user_id: uuid.UUID = Depends(current_user_id)):
    goal = goals_service.create_goal(
        user_id, body.goal_type, body.description, body.target_date, body.status
    )
    return ok(request, GoalOut.model_validate(goal))
