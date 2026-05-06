"""
ИНФРАСТРУКТУРА: Подключение к SQLite

Только здесь:
- sqlite3.connect()
- row_factory
- Управление соединениями
"""

import sqlite3
from pathlib import Path

DB_NAME = "dating.db"


def get_connection() -> sqlite3.Connection:
    """
    Создать соединение с БД.

    Возвращает соединение с row_factory=sqlite3.Row,
    чтобы результаты запросов были похожи на словари.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Включаем внешние ключи
    return conn


def init_database() -> None:
    """Создать все таблицы, если их нет."""
    conn = get_connection()
    cursor = conn.cursor()

    # ========== ПОЛЬЗОВАТЕЛИ ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            looking_for TEXT NOT NULL,
            city TEXT NOT NULL,
            bio TEXT,
            avatar TEXT,
            income INTEGER DEFAULT 5,
            appearance INTEGER DEFAULT 5,
            education TEXT DEFAULT 'среднее',
            religion TEXT DEFAULT 'не важно',
            kindness INTEGER DEFAULT 5,
            interests TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1
        )
    """)

    # ========== ЛАЙКИ ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(from_user_id, to_user_id)
        )
    """)

    # ========== ВЕСА КРИТЕРИЕВ ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_weights (
            user_id INTEGER PRIMARY KEY,
            weights TEXT NOT NULL,  -- JSON
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()