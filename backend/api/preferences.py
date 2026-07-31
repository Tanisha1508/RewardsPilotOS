"""Preferences and goals routes (BUILD_SPEC §9)."""

import uuid

from fastapi import APIRouter, Depends, Request

from backend.api.responses import ok
from backend.application import goals as goals_service
from backend.application import preferences as prefs_service
from backend.auth.dependencies import current_user_id
from backend.schemas.identity import GoalIn, GoalOut, GoalPatch, PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api/v1", tags=["preferences", "goals"])


@router.get("/preferences")
def read_preferences(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(
        request,
        PreferencesOut(
            values=prefs_service.read_preferences(user_id),
            sources=prefs_service.read_preference_sources(user_id),
        ),
    )


@router.put("/preferences")
def write_preferences(
    request: Request, body: PreferencesIn, user_id: uuid.UUID = Depends(current_user_id)
):
    return ok(
        request,
        PreferencesOut(
            values=prefs_service.write_preferences(user_id, body.values),
            sources=prefs_service.read_preference_sources(user_id),
        ),
    )


@router.delete("/preferences/{key}")
def remove_preference(request: Request, key: str, user_id: uuid.UUID = Depends(current_user_id)):
    """`PUT /preferences` merges, so it can set a key but never unset one.
    Without this a preference could be changed but not removed."""
    prefs_service.remove_preference(user_id, key)
    return ok(request, {"key": key, "deleted": True})


@router.get("/goals")
def list_goals(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, [GoalOut.model_validate(g) for g in goals_service.list_goals(user_id)])


@router.post("/goals")
def create_goal(request: Request, body: GoalIn, user_id: uuid.UUID = Depends(current_user_id)):
    goal = goals_service.create_goal(
        user_id, body.goal_type, body.description, body.target_date, body.status
    )
    return ok(request, GoalOut.model_validate(goal))


@router.patch("/goals/{goal_id}")
def update_goal(
    request: Request,
    goal_id: uuid.UUID,
    body: GoalPatch,
    user_id: uuid.UUID = Depends(current_user_id),
):
    # `exclude_unset` is what makes this PATCH rather than PUT: a field the
    # client did not send is left alone, while an explicit null clears it —
    # which matters for target_date, where "no deadline" is a real edit.
    goal = goals_service.update_goal(user_id, goal_id, **body.model_dump(exclude_unset=True))
    return ok(request, GoalOut.model_validate(goal))


@router.delete("/goals/{goal_id}")
def delete_goal(
    request: Request, goal_id: uuid.UUID, user_id: uuid.UUID = Depends(current_user_id)
):
    goals_service.delete_goal(user_id, goal_id)
    return ok(request, {"goal_id": str(goal_id), "deleted": True})
