"""
ИНФРАСТРУКТУРА: Репозиторий пользователей

Реализует интерфейс UserRepository из application/interfaces/
Только здесь: SQL-запросы к таблице users.
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from infrastructure.db.connection import get_connection


@dataclass
class UserRow:
    """DTO для строки из БД (сырые данные)."""
    id: int
    email: str
    password_hash: str
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    bio: Optional[str]
    avatar: Optional[str]
    income: int
    appearance: int
    education: str
    religion: str
    kindness: int
    interests: list  # десериализованный список
    is_active: bool


class UserRepository:
    """Репозиторий для работы с пользователями."""

    # ========== ОСНОВНЫЕ CRUD ==========

    def get_all_active(self) -> List[UserRow]:
        """Получить всех активных пользователей."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1"
        ).fetchall()
        conn.close()
        return [self._row_to_user(r) for r in rows]

    def get_by_id(self, user_id: int) -> Optional[UserRow]:
        """Найти пользователя по ID."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_active = 1",
            (user_id,)
        ).fetchone()
        conn.close()
        return self._row_to_user(row) if row else None

    def get_by_email(self, email: str) -> Optional[UserRow]:
        """Найти пользователя по email (включая неактивных — для логина)."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()
        return self._row_to_user(row) if row else None

    def create(self, user_data: Dict[str, Any]) -> int:
        """Создать нового пользователя. Возвращает ID."""
        conn = get_connection()

        interests_json = json.dumps(user_data.get("interests", []), ensure_ascii=False)

        cursor = conn.execute(
            """
            INSERT INTO users (
                email, password_hash, name, age, gender, looking_for, city,
                bio, avatar, income, appearance, education, religion, kindness, interests
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_data["email"],
                user_data["password_hash"],
                user_data["name"],
                user_data["age"],
                user_data["gender"],
                user_data["looking_for"],
                user_data["city"],
                user_data.get("bio"),
                user_data.get("avatar"),
                user_data.get("income", 5),
                user_data.get("appearance", 5),
                user_data.get("education", "среднее"),
                user_data.get("religion", "не важно"),
                user_data.get("kindness", 5),
                interests_json,
            )
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id

    def update(self, user_id: int, fields: Dict[str, Any]) -> bool:
        """Обновить поля пользователя."""
        if not fields:
            return False

        # Разрешённые для обновления поля
        allowed = {
            "name", "age", "gender", "looking_for", "city",
            "bio", "avatar", "income", "appearance",
            "education", "religion", "kindness", "interests"
        }

        updates = []
        values = []

        for field, value in fields.items():
            if field in allowed and value is not None:
                if field == "interests":
                    value = json.dumps(value, ensure_ascii=False)
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return False

        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

        conn = get_connection()
        cursor = conn.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def deactivate(self, user_id: int) -> bool:
        """Мягкое удаление (is_active = 0)."""
        conn = get_connection()
        cursor = conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    # ========== ПРЕОБРАЗОВАНИЕ ==========

    @staticmethod
    @staticmethod
    def _row_to_user(row) -> UserRow:
        """Преобразовать sqlite3.Row в UserRow."""
        if row is None:
            return None

        # Десериализуем interests из JSON
        try:
            interests = json.loads(row["interests"])
        except (json.JSONDecodeError, TypeError):
            interests = []

        return UserRow(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            name=row["name"],
            age=row["age"],
            gender=row["gender"],
            looking_for=row["looking_for"],
            city=row["city"],
            bio=row["bio"],
            avatar=row["avatar"],
            income=row["income"],
            appearance=row["appearance"],
            education=row["education"],
            religion=row["religion"],
            kindness=row["kindness"],
            interests=interests,
            is_active=bool(row["is_active"]),
        )

    @staticmethod
    def to_profile_dict(user: UserRow) -> Dict[str, Any]:
        """
        Преобразовать UserRow в словарь для алгоритма совместимости.

        Это маппинг между терминами БД и терминами алгоритма:
        - БД: income → Алгоритм: доход
        - БД: kindness → Алгоритм: доброта
        """
        return {
            "user_id": user.id,
            "name": user.name,
            "возраст": user.age,
            "пол": user.gender,
            "город": user.city,
            "доброта": user.kindness,
            "доход": user.income,
            "внешность": user.appearance,
            "интересы": user.interests,
            "образование": user.education,
            "религия": user.religion,
        }