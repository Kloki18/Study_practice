"""
ИНФРАСТРУКТУРА: Репозиторий весов критериев

Работает с таблицей user_weights.
Веса хранятся как JSON-строка.
"""

import json
from typing import Optional, Dict

from infrastructure.db.connection import get_connection


class WeightRepository:
    """Репозиторий для хранения весов критериев пользователя."""

    def save(self, user_id: int, weights: Dict[str, float]) -> None:
        """Сохранить веса (создать или обновить)."""
        weights_json = json.dumps(weights, ensure_ascii=False)

        conn = get_connection()
        conn.execute(
            """
            INSERT INTO user_weights (user_id, weights, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET 
                weights = excluded.weights,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, weights_json)
        )
        conn.commit()
        conn.close()

    def get(self, user_id: int) -> Optional[Dict[str, float]]:
        """Получить веса пользователя."""
        conn = get_connection()
        row = conn.execute(
            "SELECT weights FROM user_weights WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if row:
            return json.loads(row["weights"])
        return None

    def get_or_default(self, user_id: int, defaults: Dict[str, float]) -> Dict[str, float]:
        """Получить веса или стандартные, если не заданы."""
        weights = self.get(user_id)
        return weights if weights else defaults

    def delete(self, user_id: int) -> bool:
        """Удалить веса пользователя."""
        conn = get_connection()
        cursor = conn.execute(
            "DELETE FROM user_weights WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success