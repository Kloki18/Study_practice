import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_NAME = "dating.db"


def get_db_connection():
    """Создаёт соединение с базой данных"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицы при первом запуске"""
    conn = get_db_connection()
    cursor = conn.cursor()

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
            is_active INTEGER DEFAULT 1
        )
    """)

    # Таблица лайков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id),
            UNIQUE(from_user_id, to_user_id)
        )
    """)

    # Таблица для хранения весов критериев
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_weights (
            user_id INTEGER PRIMARY KEY,
            weights TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Таблица для хранения истории сравнений
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comparisons TEXT NOT NULL,
            cr REAL,
            is_consistent BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Добавляем новые колонки в users, если их нет
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN income INTEGER DEFAULT 5")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN appearance INTEGER DEFAULT 5")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN interests TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN education TEXT DEFAULT 'среднее'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN religion TEXT DEFAULT 'не важно'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN kindness INTEGER DEFAULT 5")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ВЕСАМИ И СРАВНЕНИЯМИ ==========

def save_user_weights(user_id: int, weights: Dict[str, float]):
    """Сохраняет веса критериев пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()

    weights_json = json.dumps(weights)

    cursor.execute("""
        INSERT INTO user_weights (user_id, weights, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET 
            weights = ?,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, weights_json, weights_json))

    conn.commit()
    conn.close()


def get_user_weights(user_id: int) -> Optional[Dict[str, float]]:
    """Получает сохраненные веса пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT weights FROM user_weights WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None


def save_user_comparisons(user_id: int, comparisons: List[Dict], cr: float = None, is_consistent: bool = None):
    """Сохраняет историю парных сравнений"""
    conn = get_db_connection()
    cursor = conn.cursor()

    comparisons_json = json.dumps(comparisons)

    cursor.execute("""
        INSERT INTO user_comparisons (user_id, comparisons, cr, is_consistent, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, comparisons_json, cr, is_consistent))

    conn.commit()
    conn.close()


def get_user_comparisons(user_id: int) -> Optional[List[Dict]]:
    """Получает последнюю историю сравнений пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT comparisons FROM user_comparisons 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None


def get_user_comparisons_history(user_id: int) -> List[Dict]:
    """Получает всю историю сравнений пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, comparisons, cr, is_consistent, created_at 
        FROM user_comparisons 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "comparisons": json.loads(row["comparisons"]),
            "cr": row["cr"],
            "is_consistent": bool(row["is_consistent"]) if row["is_consistent"] is not None else None,
            "created_at": row["created_at"]
        })

    return history


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

def get_all_users() -> List[Dict]:
    """Получить всех активных пользователей"""
    conn = get_db_connection()
    users = conn.execute("""
        SELECT id, email, name, age, gender, looking_for, city, bio, avatar,
               income, appearance, interests, education, religion, kindness
        FROM users WHERE is_active = 1
    """).fetchall()
    conn.close()

    result = []
    for user in users:
        user_dict = dict(user)
        # Парсим JSON-поля
        if "interests" in user_dict and user_dict["interests"]:
            try:
                user_dict["interests"] = json.loads(user_dict["interests"])
            except:
                user_dict["interests"] = []
        else:
            user_dict["interests"] = []
        result.append(user_dict)

    return result


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получить пользователя по ID"""
    conn = get_db_connection()
    user = conn.execute("""
        SELECT id, email, name, age, gender, looking_for, city, bio, avatar,
               income, appearance, interests, education, religion, kindness
        FROM users WHERE id = ? AND is_active = 1
    """, (user_id,)).fetchone()
    conn.close()

    if user:
        user_dict = dict(user)
        # Парсим JSON-поля
        if "interests" in user_dict and user_dict["interests"]:
            try:
                user_dict["interests"] = json.loads(user_dict["interests"])
            except:
                user_dict["interests"] = []
        else:
            user_dict["interests"] = []
        return user_dict
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Получить пользователя по email (с паролем для авторизации)"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND is_active = 1",
        (email,)
    ).fetchone()
    conn.close()

    if user:
        user_dict = dict(user)
        # Парсим JSON-поля
        if "interests" in user_dict and user_dict["interests"]:
            try:
                user_dict["interests"] = json.loads(user_dict["interests"])
            except:
                user_dict["interests"] = []
        else:
            user_dict["interests"] = []
        return user_dict
    return None


def create_user(email: str, password_hash: str, name: str, age: int, gender: str,
                looking_for: str, city: str, bio: str = None,
                income: int = 5, appearance: int = 5, interests: List[str] = None,
                education: str = "среднее", religion: str = "не важно", kindness: int = 5) -> int:
    """Создать нового пользователя"""
    conn = get_db_connection()

    interests_json = json.dumps(interests if interests else [])

    cursor = conn.execute(
        """
        INSERT INTO users (email, password_hash, name, age, gender, looking_for, city, bio,
                          income, appearance, interests, education, religion, kindness)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (email, password_hash, name, age, gender, looking_for, city, bio,
         income, appearance, interests_json, education, religion, kindness)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def update_user(user_id: int, **kwargs) -> bool:
    """Обновить данные пользователя"""
    allowed_fields = ['name', 'age', 'gender', 'looking_for', 'city', 'bio', 'avatar',
                      'income', 'appearance', 'education', 'religion', 'kindness']
    updates = []
    values = []

    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            if field == 'interests':
                updates.append(f"{field} = ?")
                values.append(json.dumps(value))
            else:
                updates.append(f"{field} = ?")
                values.append(value)

    if not updates:
        return False

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

    conn = get_db_connection()
    cursor = conn.execute(query, values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def delete_user(user_id: int) -> bool:
    """Мягкое удаление пользователя"""
    conn = get_db_connection()
    cursor = conn.execute(
        "UPDATE users SET is_active = 0 WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


# ========== ФУНКЦИИ ДЛЯ ЛАЙКОВ ==========

def add_like(from_user_id: int, to_user_id: int) -> bool:
    """Добавить лайк"""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)",
            (from_user_id, to_user_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_likes_received(user_id: int) -> List[Dict]:
    """Получить всех, кто лайкнул этого пользователя"""
    conn = get_db_connection()
    likes = conn.execute("""
        SELECT u.id, u.name, u.age, u.city, u.avatar
        FROM likes l
        JOIN users u ON l.from_user_id = u.id
        WHERE l.to_user_id = ? AND u.is_active = 1
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(like) for like in likes]


def get_likes_given(user_id: int) -> List[Dict]:
    """Получить всех, кого лайкнул этот пользователь"""
    conn = get_db_connection()
    likes = conn.execute("""
        SELECT u.id, u.name, u.age, u.city, u.avatar
        FROM likes l
        JOIN users u ON l.to_user_id = u.id
        WHERE l.from_user_id = ? AND u.is_active = 1
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(like) for like in likes]


def check_match(user1_id: int, user2_id: int) -> bool:
    """Проверить, есть ли взаимный лайк"""
    conn = get_db_connection()
    result = conn.execute("""
        SELECT COUNT(*) as count
        FROM likes
        WHERE (from_user_id = ? AND to_user_id = ?)
        OR (from_user_id = ? AND to_user_id = ?)
    """, (user1_id, user2_id, user2_id, user1_id)).fetchone()
    conn.close()
    return result['count'] == 2


def get_matches(user_id: int) -> List[Dict]:
    """Получить всех, с кем есть взаимный лайк"""
    conn = get_db_connection()
    matches = conn.execute("""
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
    """, (user_id, user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(match) for match in matches]


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def seed_test_data():
    """Добавить тестовых пользователей"""
    if len(get_all_users()) == 0:
        test_users = [
            {
                "email": "anna@example.com",
                "password": hash_password("123"),
                "name": "Анна",
                "age": 25,
                "gender": "female",
                "looking_for": "male",
                "city": "Москва",
                "bio": "Люблю путешествия и кофе",
                "income": 7,
                "appearance": 8,
                "interests": ["путешествия", "кофе", "книги", "йога"],
                "education": "высшее",
                "religion": "православие",
                "kindness": 9
            },
            {
                "email": "denis@example.com",
                "password": hash_password("123"),
                "name": "Денис",
                "age": 28,
                "gender": "male",
                "looking_for": "female",
                "city": "Санкт-Петербург",
                "bio": "Спорт и активный отдых",
                "income": 8,
                "appearance": 7,
                "interests": ["спорт", "туризм", "велосипед"],
                "education": "высшее",
                "religion": "не важно",
                "kindness": 7
            },
            {
                "email": "maria@example.com",
                "password": hash_password("123"),
                "name": "Мария",
                "age": 23,
                "gender": "female",
                "looking_for": "male",
                "city": "Казань",
                "bio": "Ищу серьёзные отношения",
                "income": 5,
                "appearance": 9,
                "interests": ["танцы", "музыка", "кино"],
                "education": "среднее специальное",
                "religion": "ислам",
                "kindness": 8
            },
            {
                "email": "alexey@example.com",
                "password": hash_password("123"),
                "name": "Алексей",
                "age": 30,
                "gender": "male",
                "looking_for": "female",
                "city": "Москва",
                "bio": "Предприниматель, люблю горы",
                "income": 9,
                "appearance": 8,
                "interests": ["бизнес", "горы", "лыжи", "путешествия"],
                "education": "высшее",
                "religion": "не важно",
                "kindness": 6
            },
            {
                "email": "elena@example.com",
                "password": hash_password("123"),
                "name": "Елена",
                "age": 27,
                "gender": "female",
                "looking_for": "male",
                "city": "Новосибирск",
                "bio": "Книги и йога",
                "income": 6,
                "appearance": 8,
                "interests": ["книги", "йога", "психология", "путешествия"],
                "education": "высшее",
                "religion": "буддизм",
                "kindness": 9
            },
        ]

        for user_data in test_users:
            create_user(
                email=user_data["email"],
                password_hash=user_data["password"],
                name=user_data["name"],
                age=user_data["age"],
                gender=user_data["gender"],
                looking_for=user_data["looking_for"],
                city=user_data["city"],
                bio=user_data["bio"],
                income=user_data["income"],
                appearance=user_data["appearance"],
                interests=user_data["interests"],
                education=user_data["education"],
                religion=user_data["religion"],
                kindness=user_data["kindness"]
            )

        print("✅ Добавлено 5 тестовых пользователей")
        print("📧 Логины: anna@example.com, denis@example.com и т.д.")
        print("🔑 Пароль для всех: 123")


# Инициализация БД при импорте
init_db()
seed_test_data()