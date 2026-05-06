"""
USE CASES: Авторизация

Сценарии:
- Регистрация нового пользователя
- Вход в систему
"""

from dataclasses import dataclass

from application.ports import (
    UserRepository,
    WeightRepository,
    HashService,
)
from application.dto.requests import RegisterRequest, LoginRequest


# ============================================================
# ОШИБКИ ДОМЕНА
# ============================================================

class EmailAlreadyExistsError(Exception):
    """Email уже зарегистрирован."""
    pass


class InvalidCredentialsError(Exception):
    """Неверный email или пароль."""
    pass


# ============================================================
# USE CASES
# ============================================================

@dataclass
class RegisterUseCase:
    """
    Регистрация нового пользователя.

    Шаги:
    1. Проверить, что email не занят
    2. Захэшировать пароль
    3. Создать пользователя
    4. Сохранить стандартные веса для алгоритма
    """

    user_repo: UserRepository
    weight_repo: WeightRepository
    hash_service: HashService

    def execute(self, request: RegisterRequest) -> dict:
        """
        Выполнить регистрацию.

        Returns:
            dict с id, email, name нового пользователя

        Raises:
            EmailAlreadyExistsError: если email уже используется
        """
        # Шаг 1: Проверяем email
        existing = self.user_repo.get_by_email(request.email)
        if existing:
            raise EmailAlreadyExistsError(
                f"Email '{request.email}' уже зарегистрирован"
            )

        # Шаг 2: Хэшируем пароль
        password_hash = self.hash_service.hash(request.password)

        # Шаг 3: Создаём пользователя
        user_id = self.user_repo.create({
            "email": request.email,
            "password_hash": password_hash,
            "name": request.name,
            "age": request.age,
            "gender": request.gender,
            "looking_for": request.looking_for,
            "city": request.city,
            "bio": request.bio,
        })

        # Шаг 4: Инициализируем стандартные веса
        from domain.services.ahp_services import AHPService
        default_weights = AHPService.default_weights()
        self.weight_repo.save(user_id, default_weights)

        return {
            "user_id": user_id,
            "email": request.email,
            "name": request.name,
            "message": "Регистрация успешна",
        }


@dataclass
class LoginUseCase:
    """
    Вход в систему.

    Шаги:
    1. Найти пользователя по email
    2. Проверить пароль
    3. Вернуть данные пользователя
    """

    user_repo: UserRepository
    hash_service: HashService

    def execute(self, request: LoginRequest) -> dict:
        """
        Выполнить вход.

        Returns:
            dict с id, email, name пользователя

        Raises:
            InvalidCredentialsError: если email не найден или пароль неверный
        """
        # Шаг 1: Ищем пользователя
        user = self.user_repo.get_by_email(request.email)
        if not user:
            raise InvalidCredentialsError("Неверный email или пароль")

        # Шаг 2: Проверяем пароль
        if not self.hash_service.verify(request.password, user.password_hash):
            raise InvalidCredentialsError("Неверный email или пароль")

        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "message": "Вход выполнен успешно",
        }