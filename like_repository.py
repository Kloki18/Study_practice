"""
ИНФРАСТРУКТУРА: Репозиторий лайков

Работает с таблицей likes.
Взаимные лайки = мэтч.
"""

from typing import List, Dict
from dataclasses import dataclass

from infrastructure.db.connection import get_connection


@dataclass
class LikeInfo:
    """Информация о лайке (кто и кого)."""
    user_id: int
    user_name: str
    user_age: int
    user_city: str
    user_avatar: str = None


class LikeRepository:
    """Репозиторий для работы с лайками."""

    def add(self, from_user_id: int, to_user_id: int) -> bool:
        """
        Добавить лайк.
        Возвращает True если лайк добавлен, False если уже существует.
        """
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)",
                (from_user_id, to_user_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:  # sqlite3.IntegrityError — дубликат
            return False

    def get_received(self, user_id: int) -> List[LikeInfo]:
        """Кто лайкнул этого пользователя."""
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.age, u.city, u.avatar
            FROM likes l
            JOIN users u ON l.from_user_id = u.id
            WHERE l.to_user_id = ? AND u.is_active = 1
            """,
            (user_id,)
        ).fetchall()
        conn.close()
        return [
            LikeInfo(
                user_id=row["id"],
                user_name=row["name"],
                user_age=row["age"],
                user_city=row["city"],
                user_avatar=row["avatar"],
            )
            for row in rows
        ]

    def get_given(self, user_id: int) -> List[LikeInfo]:
        """Кого лайкнул этот пользователь."""
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.age, u.city, u.avatar
            FROM likes l
            JOIN users u ON l.to_user_id = u.id
            WHERE l.from_user_id = ? AND u.is_active = 1
            """,
            (user_id,)
        ).fetchall()
        conn.close()
        return [
            LikeInfo(
                user_id=row["id"],
                user_name=row["name"],
                user_age=row["age"],
                user_city=row["city"],
                user_avatar=row["avatar"],
            )
            for row in rows
        ]

    def is_match(self, user1_id: int, user2_id: int) -> bool:
        """Проверить взаимный лайк."""
        conn = get_connection()
        row = conn.execute(
            """
            SELECT COUNT(*) as cnt
            FROM likes
            WHERE (from_user_id = ? AND to_user_id = ?)
               OR (from_user_id = ? AND to_user_id = ?)
            """,
            (user1_id, user2_id, user2_id, user1_id)
        ).fetchone()
        conn.close()
        return row["cnt"] == 2

    def get_matches(self, user_id: int) -> List[LikeInfo]:
        """Получить все взаимные лайки (мэтчи)."""
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT DISTINCT u.id, u.name, u.age, u.city, u.avatar
            FROM likes l1
            JOIN users u ON (
                (l1.from_user_id = ? AND l1.to_user_id = u.id) OR
                (l1.to_user_id = ? AND l1.from_user_id = u.id)
            )
            JOIN likes l2 ON (
                (l2.from_user_id = u.id AND l2.to_user_id = ?) OR
                (l2.to_user_id = u.id AND l2.from_user_id = ?)
            )
            WHERE u.is_active = 1 AND u.id != ?
            """,
            (user_id, user_id, user_id, user_id, user_id)
        ).fetchall()
        conn.close()
        return [
            LikeInfo(
                user_id=row["id"],
                user_name=row["name"],
                user_age=row["age"],
                user_city=row["city"],
                user_avatar=row["avatar"],
            )
            for row in rows
        ]