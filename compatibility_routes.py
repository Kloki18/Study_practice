"""
API: Совместимость

POST /api/compatibility/calculate              — рассчитать совместимость
GET  /api/compatibility/recommendations/{id}   — получить рекомендации
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from application.dto.requests import CompatibilityRequest
from application.use_cases.compability_case import (
    CalculateCompatibilityUseCase,
    GetRecommendationsUseCase,
    NoCandidatesError,
)
from application.use_cases.user_case import UserNotFoundError
from presentation.api.dependencies import (
    get_calculate_compatibility_use_case,
    get_recommendations_use_case,
)

router = APIRouter(prefix="/api/compatibility", tags=["Совместимость"])


@router.post("/calculate")
def calculate_compatibility(
    request: CompatibilityRequest,
    use_case: CalculateCompatibilityUseCase = Depends(
        get_calculate_compatibility_use_case
    ),
):
    """Рассчитать совместимость пользователя с кандидатами."""
    try:
        return use_case.execute(request)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoCandidatesError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
    use_case: GetRecommendationsUseCase = Depends(get_recommendations_use_case),
):
    """Получить персонализированные рекомендации."""
    try:
        return use_case.execute(user_id, limit)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoCandidatesError as e:
        raise HTTPException(status_code=404, detail=str(e))