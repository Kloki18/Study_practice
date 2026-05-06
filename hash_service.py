"""
ИНФРАСТРУКТУРА: Сервис хеширования паролей

Реализует интерфейс HashService из application/interfaces/
Использует SHA-256 (как в оригинальном database.py).
"""

import hashlib

from application.ports.hash_services import HashService


class Sha256HashService(HashService):
    """Хеширование паролей через SHA-256."""

    def hash(self, password: str) -> str:
        """Захэшировать пароль."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, password: str, password_hash: str) -> bool:
        """Проверить, соответствует ли пароль хэшу."""
        return self.hash(password) == password_hash