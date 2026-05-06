"""
USE CASES: Лайки и мэтчи

Сценарии:
- Лайкнуть пользователя
- Получить полученные лайки
- Получить отданные лайки
- Получить взаимные мэтчи
"""

from dataclasses import dataclass
from typing import List

from application.ports import (
    UserRepository,
    LikeRepository,
    WeightRepository,
)
from application.dto.requests import LikeRequest
from domain.services.compatibility_services import CompatibilityEvaluator
from domain.services.ahp_services import AHPService


# ============================================================
# ОШИБКИ
# ============================================================

class SelfLikeError(Exception):
    """Нельзя лайкнуть самого себя."""
    pass


# ============================================================
# USE CASES
# ============================================================

@dataclass
class LikeUserUseCase:
    """
    Лайкнуть пользователя.

    Шаги:
    1. Проверить, что это не самолайк
    2. Проверить, что оба пользователя существуют
    3. Добавить лайк
    4. Если взаимно — вычислить совместимость
    """

    user_repo: UserRepository
    like_repo: LikeRepository
    weight_repo: WeightRepository
    compatibility_evaluator: CompatibilityEvaluator

    def execute(self, request: LikeRequest) -> dict:
        from application.use_cases.user_case import UserNotFoundError

        # Шаг 1: Проверка на самолайк
        if request.from_user_id == request.to_user_id:
            raise SelfLikeError("Нельзя лайкнуть самого себя")

        # Шаг 2: Проверяем существование
        from_user = self.user_repo.get_by_id(request.from_user_id)
        to_user = self.user_repo.get_by_id(request.to_user_id)

        if not from_user:
            raise UserNotFoundError(f"Пользователь {request.from_user_id} не найден")
        if not to_user:
            raise UserNotFoundError(f"Пользователь {request.to_user_id} не найден")

        # Шаг 3: Добавляем лайк
        success = self.like_repo.add(request.from_user_id, request.to_user_id)
        if not success:
            return {
                "status": "already_liked",
                "is_match": False,
                "compatibility_score": None,
                "message": f"Вы уже лайкнули {to_user.name}",
            }

        # Шаг 4: Проверяем взаимность
        is_match = self.like_repo.is_match(request.from_user_id, request.to_user_id)

        compatibility_score = None
        if is_match:
            # Вычисляем совместимость
            user_profile = self.user_repo.to_profile_dict(from_user)
            candidate_profile = self.user_repo.to_profile_dict(to_user)

            default_weights = AHPService.default_weights()
            weights = self.weight_repo.get_or_default(request.from_user_id, default_weights)

            result = self.compatibility_evaluator.evaluate(
                user_profile, candidate_profile, weights
            )
            compatibility_score = result.score

        return {
            "status": "success",
            "is_match": is_match,
            "compatibility_score": compatibility_score,
            "message": (
                    f"Вы лайкнули {to_user.name}."
                    + (" Взаимно!" if is_match else "")
            ),
        }


@dataclass
class GetReceivedLikesUseCase:
    """Получить лайки, полученные пользователем."""

    user_repo: UserRepository
    like_repo: LikeRepository

    def execute(self, user_id: int) -> List[dict]:
        from application.use_cases.user_case import UserNotFoundError

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        likes = self.like_repo.get_received(user_id)
        return [
            {
                "user_id": like.user_id,
                "user_name": like.user_name,
                "user_age": like.user_age,
                "user_city": like.user_city,
                "user_avatar": like.user_avatar,
            }
            for like in likes
        ]


@dataclass
class GetGivenLikesUseCase:
    """Получить лайки, отданные пользователем."""

    user_repo: UserRepository
    like_repo: LikeRepository

    def execute(self, user_id: int) -> List[dict]:
        from application.use_cases.user_case import UserNotFoundError

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        likes = self.like_repo.get_given(user_id)
        return [
            {
                "user_id": like.user_id,
                "user_name": like.user_name,
                "user_age": like.user_age,
                "user_city": like.user_city,
                "user_avatar": like.user_avatar,
            }
            for like in likes
        ]


@dataclass
class GetMatchesUseCase:
    """
    Получить взаимные мэтчи с оценкой совместимости.

    Сортируем по убыванию совместимости.
    """

    user_repo: UserRepository
    like_repo: LikeRepository
    weight_repo: WeightRepository
    compatibility_evaluator: CompatibilityEvaluator

    def execute(self, user_id: int) -> List[dict]:
        from application.use_cases.user_case import UserNotFoundError

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        # Получаем мэтчи
        matches = self.like_repo.get_matches(user_id)

        # Вычисляем совместимость для каждого
        user_profile = self.user_repo.to_profile_dict(user)
        default_weights = AHPService.default_weights()
        weights = self.weight_repo.get_or_default(user_id, default_weights)

        enriched = []
        for match in matches:
            match_user = self.user_repo.get_by_id(match.user_id)
            if match_user:
                match_profile = self.user_repo.to_profile_dict(match_user)
                result = self.compatibility_evaluator.evaluate(
                    user_profile, match_profile, weights
                )
                enriched.append({
                    "candidate_id": match.user_id,
                    "candidate_name": match.user_name,
                    "candidate_age": match.user_age,
                    "candidate_city": match.user_city,
                    "candidate_avatar": match.user_avatar,
                    "compatibility_score": result.score,
                })

        # Сортируем по убыванию совместимости
        enriched.sort(key=lambda m: m["compatibility_score"], reverse=True)
        return enriched