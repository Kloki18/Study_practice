"""
USE CASES: Пользователи

Сценарии:
- Получить всех пользователей
- Получить пользователя по ID
- Обновить профиль
- Удалить профиль
"""

from dataclasses import dataclass
from typing import List, Optional

from application.ports import UserRepository
from application.dto.requests import UpdateUserRequest


# ============================================================
# ОШИБКИ
# ============================================================

class UserNotFoundError(Exception):
    """Пользователь не найден."""
    pass


# ============================================================
# USE CASES
# ============================================================

@dataclass
class GetAllUsersUseCase:
    """Получить всех активных пользователей."""

    user_repo: UserRepository

    def execute(self) -> List[dict]:
        users = self.user_repo.get_all_active()
        return [
            self._format_user(u)
            for u in users
        ]

    @staticmethod
    def _format_user(user) -> dict:
        """Форматирует пользователя для ответа (без пароля)."""
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "looking_for": user.looking_for,
            "city": user.city,
            "bio": user.bio,
            "avatar": user.avatar,
            "income": user.income,
            "appearance": user.appearance,
            "education": user.education,
            "religion": user.religion,
            "kindness": user.kindness,
            "interests": user.interests,
        }


@dataclass
class GetUserByIdUseCase:
    """Получить пользователя по ID."""

    user_repo: UserRepository

    def execute(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        return GetAllUsersUseCase._format_user(user)


@dataclass
class UpdateUserUseCase:
    """Обновить профиль пользователя."""

    user_repo: UserRepository

    def execute(self, user_id: int, request: UpdateUserRequest) -> dict:
        # Проверяем, что пользователь существует
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        # Собираем только не-None поля
        fields = {
            k: v for k, v in request.model_dump().items()
            if v is not None
        }

        if fields:
            self.user_repo.update(user_id, fields)

        return {"message": "Данные обновлены", "updated_fields": list(fields.keys())}


@dataclass
class DeleteUserUseCase:
    """Удалить профиль (мягкое удаление)."""

    user_repo: UserRepository

    def execute(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

        self.user_repo.deactivate(user_id)
        return {"message": "Профиль удалён"}