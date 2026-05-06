"""
USE CASES: Метод Анализа Иерархий (МАИ)

Сценарии:
- Рассчитать веса по парным сравнениям
- Сохранить веса для пользователя
- Получить сохранённые веса
"""

from dataclasses import dataclass
from typing import List, Dict

from application.ports import WeightRepository
from application.dto.requests import (
    CalculateWeightsRequest,
    SaveWeightsRequest,

)
from domain.services.ahp_services import (
    AHPService,
    Comparison,
)


# ============================================================
# USE CASES
# ============================================================

@dataclass
class CalculateWeightsUseCase:
    """
    Рассчитать веса критериев методом МАИ.

    Использует доменный сервис AHPService.
    """

    ahp_service: AHPService

    def execute(self, request: CalculateWeightsRequest) -> dict:
        """
        Выполнить расчёт весов.

        Returns:
            dict с весами, λ_max, CI, CR, признаком согласованности
        """
        # Преобразуем DTO в доменные объекты
        comparisons = [
            Comparison(
                criterion_a=comp.criterion_a,
                criterion_b=comp.criterion_b,
                value=comp.value,
            )
            for comp in request.comparisons
        ]

        # Строим матрицу
        matrix = self.ahp_service.build_matrix(
            criteria=request.criteria,
            comparisons=comparisons,
        )

        # Вычисляем веса
        result = self.ahp_service.calculate_weights(matrix)

        # Формируем ответ
        weights_dict = result.to_dict(request.criteria)

        return {
            "weights": weights_dict,
            "lambda_max": result.lambda_max,
            "ci": result.ci,
            "cr": result.cr,
            "is_consistent": result.is_consistent,
            "criteria_list": request.criteria,
        }


@dataclass
class SaveWeightsUseCase:
    """Сохранить веса критериев для пользователя."""

    weight_repo: WeightRepository

    def execute(self, user_id: int, request: SaveWeightsRequest) -> dict:
        """Сохранить веса в БД."""
        self.weight_repo.save(user_id, request.weights)

        return {
            "message": "Веса сохранены",
            "weights": request.weights,
        }


@dataclass
class GetWeightsUseCase:
    """Получить сохранённые веса пользователя."""

    weight_repo: WeightRepository

    def execute(self, user_id: int) -> dict:
        """
        Получить веса.
        Если не сохранены — вернуть стандартные.
        """
        from domain.services.ahp_services import AHPService

        default_weights = AHPService.default_weights()
        weights = self.weight_repo.get_or_default(user_id, default_weights)

        return {
            "user_id": user_id,
            "weights": weights,
            "criteria_list": list(weights.keys()),
        }