from dataclasses import dataclass, field
from typing import List, Optional
from copy import copy


@dataclass
class UserId:
    """Value Object для идентификатора пользователя"""
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("ID пользователя должен быть положительным числом")


@dataclass
class Email:
    """Value Object для email"""
    value: str

    def __post_init__(self):
        # Простейшая валидация, без регулярок
        if "@" not in self.value or "." not in self.value:
            raise ValueError(f"Некорректный email: {self.value}")


@dataclass
class User:
    """
    Сущность пользователя.

    Это главный бизнес-объект предметной области "сервис знакомств".
    Содержит ВСЕ бизнес-правила, связанные с пользователем:
    - Какие данные можно менять
    - Кого можно лайкнуть
    - Является ли пользователь активным
    """

    # Идентификатор (value object)
    user_id: UserId

    # Учётные данные
    email: Email
    password_hash: str

    # Базовая информация
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    bio: Optional[str] = None
    avatar: Optional[str] = None

    # Признак активности (для мягкого удаления)
    is_active: bool = True

    # Расширенные данные профиля (для алгоритма совместимости)
    income: int = 5  # 1-10
    appearance: int = 5  # 1-10
    kindness: int = 5  # 1-10
    interests: List[str] = field(default_factory=list)
    education: str = "среднее"
    religion: str = "не важно"

    # ========== ВАЛИДАЦИЯ ПРИ СОЗДАНИИ ==========

    def __post_init__(self):
        """Проверяем целостность данных при создании"""
        if self.age < 18:
            raise ValueError("Пользователь должен быть совершеннолетним")
        if self.age > 120:
            raise ValueError("Некорректный возраст")
        if self.gender not in ("male", "female"):
            raise ValueError("Пол должен быть 'male' или 'female'")
        if self.looking_for not in ("male", "female"):
            raise ValueError("Параметр looking_for должен быть 'male' или 'female'")

    # ========== БИЗНЕС-МЕТОДЫ ==========

    def can_like(self, target: 'User') -> bool:
        """Проверяет, может ли пользователь лайкнуть другого.

        Бизнес-правила:
        1. Нельзя лайкнуть самого себя
        2. Нельзя лайкнуть пользователя противоположного пола (не того, кого ищет)
        3. Нельзя лайкнуть неактивного пользователя
        """
        if self.user_id == target.user_id:
            return False
        if not target.is_active:
            return False
        if target.gender != self.looking_for:
            return False
        return True

    def is_match(self, other_likes_me: bool, i_like_them: bool) -> bool:
        """Проверяет, есть ли взаимный мэтч (чистая логика)."""
        return i_like_them and other_likes_me

    def deactivate(self) -> None:
        """Мягкое удаление профиля."""
        self.is_active = False

    def reactivate(self) -> None:
        """Восстановление профиля."""
        self.is_active = True

    # ========== МЕТОДЫ ОБНОВЛЕНИЯ ДАННЫХ ==========

    def update_profile(self, **kwargs) -> 'User':
        """
        Обновляет поля профиля (иммутабельно).
        Возвращает НОВЫЙ объект с изменёнными полями.
        """
        updated_user = copy(self)
        allowed_fields = [
            'name', 'age', 'gender', 'looking_for', 'city',
            'bio', 'avatar', 'income', 'appearance',
            'education', 'religion', 'kindness'
        ]

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(updated_user, field, value)

        # Повторная валидация
        updated_user.__post_init__()
        return updated_user

    # ========== ПРЕДСТАВЛЕНИЕ ДЛЯ АЛГОРИТМА ==========

    def to_profile_dict(self) -> dict:
        """
        Конвертирует в словарь профиля для алгоритма совместимости.
        ЭТОТ МЕТОД НЕ ДОЛЖЕН БЫТЬ В DOMAIN в идеале.
        Но пока оставим для простоты переходного периода.

        Правильнее: использовать отдельный маппер в application слое.
        """
        return {
            "user_id": self.user_id.value,
            "name": self.name,
            "возраст": self.age,
            "пол": self.gender,
            "город": self.city,
            "доброта": self.kindness,
            "доход": self.income,
            "внешность": self.appearance,
            "интересы": self.interests,
            "образование": self.education,
            "религия": self.religion,
        }