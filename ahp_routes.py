"""
API: Метод Анализа Иерархий (МАИ)

POST /api/ahp/calculate       — рассчитать веса
POST /api/ahp/save/{user_id}  — сохранить веса
GET  /api/ahp/weights/{user_id} — получить веса
"""

from fastapi import APIRouter, Depends, HTTPException

from application.dto.requests import CalculateWeightsRequest, SaveWeightsRequest
from application.use_cases.ahp_case import (
    CalculateWeightsUseCase,
    SaveWeightsUseCase,
    GetWeightsUseCase,
)
from presentation.api.dependencies import (
    get_calculate_weights_use_case,
    get_save_weights_use_case,
    get_get_weights_use_case,
)

router = APIRouter(prefix="/api/ahp", tags=["МАИ"])


@router.post("/calculate")
def calculate_weights(
    request: CalculateWeightsRequest,
    use_case: CalculateWeightsUseCase = Depends(get_calculate_weights_use_case),
):
    """
    Рассчитать веса критериев методом МАИ на основе парных сравнений.
    """
    try:
        return use_case.execute(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка расчёта: {str(e)}")


@router.post("/save/{user_id}")
def save_weights(
    user_id: int,
    request: SaveWeightsRequest,
    use_case: SaveWeightsUseCase = Depends(get_save_weights_use_case),
):
    """Сохранить веса критериев для пользователя."""
    return use_case.execute(user_id, request)


@router.get("/weights/{user_id}")
def get_weights(
    user_id: int,
    use_case: GetWeightsUseCase = Depends(get_get_weights_use_case),
):
    """Получить сохранённые веса пользователя."""
    return use_case.execute(user_id)