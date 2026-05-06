"""
ИНТЕРФЕЙС: Сервис хеширования паролей
"""

from abc import ABC, abstractmethod


class HashService(ABC):
    """Абстрактный сервис для хеширования и проверки паролей."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Захэшировать пароль."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Проверить, соответствует ли пароль хэшу."""
        raise NotImplementedError