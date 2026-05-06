"""
API: Лайки и мэтчи

POST /api/like                   — лайкнуть
GET  /api/likes/received/{id}    — полученные лайки
GET  /api/likes/given/{id}       — отданные лайки
GET  /api/matches/{id}           — взаимные мэтчи
"""

from fastapi import APIRouter, Depends, HTTPException

from application.dto.requests import LikeRequest
from application.use_cases.likes_case import (
    LikeUserUseCase,
    GetReceivedLikesUseCase,
    GetGivenLikesUseCase,
    GetMatchesUseCase,
    SelfLikeError,
)
from application.use_cases.user_case import UserNotFoundError
from presentation.api.dependencies import (
    get_like_user_use_case,
    get_received_likes_use_case,
    get_given_likes_use_case,
    get_matches_use_case,
)

router = APIRouter(prefix="/api", tags=["Лайки"])


@router.post("/like")
def like_person(
    request: LikeRequest,
    use_case: LikeUserUseCase = Depends(get_like_user_use_case),
):
    """Лайкнуть пользователя."""
    try:
        return use_case.execute(request)
    except SelfLikeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/likes/received/{user_id}")
def get_received_likes(
    user_id: int,
    use_case: GetReceivedLikesUseCase = Depends(get_received_likes_use_case),
):
    """Получить список тех, кто лайкнул пользователя."""
    try:
        likes = use_case.execute(user_id)
        return {"received_likes": likes}
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/likes/given/{user_id}")
def get_given_likes(
    user_id: int,
    use_case: GetGivenLikesUseCase = Depends(get_given_likes_use_case),
):
    """Получить список тех, кого лайкнул пользователь."""
    try:
        likes = use_case.execute(user_id)
        return {"given_likes": likes}
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/matches/{user_id}")
def get_matches(
    user_id: int,
    use_case: GetMatchesUseCase = Depends(get_matches_use_case),
):
    """Получить взаимные мэтчи с оценкой совместимости."""
    try:
        matches = use_case.execute(user_id)
        return {"matches": matches}
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))