from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import database
import numpy as np

# Импортируем наши алгоритмы
from MAI_alg import (
    calculate_ahp_weights,
    build_matrix_from_comparisons,
    suggest_improvements
)
from copm_alg import (
    compute_compatibility,
    compute_batch_compatibility
)

app = FastAPI(title="Сервис подбора супруга")

# Для React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== МОДЕЛИ ДАННЫХ ==========

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    bio: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    bio: Optional[str] = None
    avatar: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    looking_for: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None


class LikeRequest(BaseModel):
    from_user_id: int
    to_user_id: int


# ========== НОВЫЕ МОДЕЛИ ДЛЯ МАИ И СОВМЕСТИМОСТИ ==========

class CriteriaComparison(BaseModel):
    """Модель для одного парного сравнения"""
    criterion_a: str
    criterion_b: str
    value: float  # 1, 3, 5, 7, 9 или обратные 1/3, 1/5 и т.д.


class AHPRequest(BaseModel):
    """Запрос на расчет весов МАИ"""
    criteria_names: List[str]
    comparisons: List[CriteriaComparison]


class AHPResponse(BaseModel):
    """Ответ с результатами МАИ"""
    weights: Dict[str, float]
    lambda_max: float
    ci: float
    cr: float
    is_consistent: bool
    missing_comparisons: List[List[str]]
    suggestions: List[Dict[str, Any]] = []


class CompatibilityRequest(BaseModel):
    """Запрос на расчет совместимости"""
    user_id: int
    candidate_ids: Optional[List[int]] = None  # Если None - со всеми
    use_saved_weights: bool = True  # Использовать сохраненные веса или пересчитать


class CompatibilityResponse(BaseModel):
    """Ответ с результатами совместимости"""
    user_id: int
    user_name: str
    weights_used: Dict[str, float]
    weights_consistent: bool
    candidates: List[Dict[str, Any]]
    top_match: Optional[Dict[str, Any]]


class UserPreferences(BaseModel):
    """Модель для сохранения предпочтений пользователя"""
    user_id: int
    criteria_weights: Dict[str, float]
    criteria_comparisons: List[CriteriaComparison]


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def convert_user_to_profile(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Конвертирует пользователя из БД в профиль для алгоритма совместимости.
    """
    return {
        "user_id": user["id"],
        "name": user["name"],
        "возраст": user["age"],
        "пол": user["gender"],
        "город": user["city"],
        # Добавляем заглушки для критериев, которых нет в БД
        # В реальном проекте эти поля нужно добавить в таблицу users
        "доброта": user.get("kindness", 5),
        "доход": user.get("income", 5),
        "внешность": user.get("appearance", 5),
        "интересы": user.get("interests", []),
        "образование": user.get("education", "среднее"),
        "религия": user.get("religion", "не важно"),
    }


# Стандартные критерии для сервиса знакомств
DEFAULT_CRITERIA = [
    "возраст",
    "город",
    "образование",
    "доход",
    "внешность",
    "интересы",
    "религия"
]

# Стандартные веса (равномерные)
DEFAULT_WEIGHTS = {criterion: 1.0 / len(DEFAULT_CRITERIA) for criterion in DEFAULT_CRITERIA}


# ========== БАЗОВЫЕ ЭНДПОИНТЫ ==========

@app.get("/")
def home():
    return {"message": "Сервис подбора супруга с интеллектуальным подбором работает!"}


@app.get("/api/people", response_model=List[UserResponse])
def get_all_people():
    users = database.get_all_users()
    return users


@app.get("/api/people/{user_id}", response_model=UserResponse)
def get_person_by_id(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.post("/api/register")
def register(user: UserCreate):
    existing = database.get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    password_hash = database.hash_password(user.password)

    user_id = database.create_user(
        email=user.email,
        password_hash=password_hash,
        name=user.name,
        age=user.age,
        gender=user.gender,
        looking_for=user.looking_for,
        city=user.city,
        bio=user.bio
    )

    # Инициализируем стандартные веса для нового пользователя
    database.save_user_weights(user_id, DEFAULT_WEIGHTS)

    return {"id": user_id, "message": "Регистрация успешна"}


@app.post("/api/login")
def login(user: UserLogin):
    db_user = database.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if db_user["password_hash"] != database.hash_password(user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    return {
        "id": db_user["id"],
        "email": db_user["email"],
        "name": db_user["name"],
        "message": "Вход выполнен успешно"
    }


@app.put("/api/people/{user_id}")
def update_user(user_id: int, updates: UserUpdate):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    if update_data:
        database.update_user(user_id, **update_data)

    return {"message": "Данные обновлены"}


@app.delete("/api/people/{user_id}")
def delete_user(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    database.delete_user(user_id)
    return {"message": "Профиль удалён"}


# ========== НОВЫЕ ЭНДПОИНТЫ ДЛЯ МАИ ==========

@app.post("/api/ahp/calculate", response_model=AHPResponse)
def calculate_ahp(request: AHPRequest):
    """
    Вычисляет веса критериев методом МАИ на основе парных сравнений.
    """
    try:
        # Конвертируем сравнения в нужный формат
        comparisons = [comp.dict() for comp in request.comparisons]

        # Строим матрицу и вычисляем веса
        matrix, missing = build_matrix_from_comparisons(
            request.criteria_names,
            comparisons
        )

        result = calculate_ahp_weights(matrix)

        # Конвертируем веса в словарь
        weights_dict = {
            criterion: result["weights"][i]
            for i, criterion in enumerate(request.criteria_names)
        }

        # Если матрица несогласована, предлагаем улучшения
        suggestions = []
        if not result["is_consistent"]:
            suggestions = suggest_improvements(matrix, request.criteria_names)

        return AHPResponse(
            weights=weights_dict,
            lambda_max=result["lambda_max"],
            ci=result["ci"],
            cr=result["cr"],
            is_consistent=result["is_consistent"],
            missing_comparisons=[[a, b] for a, b in missing],
            suggestions=suggestions
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка расчета МАИ: {str(e)}")


@app.post("/api/ahp/save/{user_id}")
def save_user_weights(user_id: int, preferences: UserPreferences):
    """
    Сохраняет веса критериев для пользователя.
    """
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Сохраняем веса в БД
    database.save_user_weights(user_id, preferences.criteria_weights)
    database.save_user_comparisons(user_id, [comp.dict() for comp in preferences.criteria_comparisons])

    return {
        "message": "Веса сохранены",
        "weights": preferences.criteria_weights
    }


@app.get("/api/ahp/weights/{user_id}")
def get_user_weights(user_id: int):
    """
    Получает сохраненные веса критериев пользователя.
    """
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    weights = database.get_user_weights(user_id)
    if not weights:
        weights = DEFAULT_WEIGHTS

    return {
        "user_id": user_id,
        "weights": weights,
        "criteria_list": list(weights.keys())
    }


# ========== ЭНДПОИНТЫ ДЛЯ СОВМЕСТИМОСТИ ==========

@app.post("/api/compatibility/calculate", response_model=CompatibilityResponse)
def calculate_compatibility(request: CompatibilityRequest):
    """
    Вычисляет совместимость пользователя с кандидатами.
    """
    # Получаем профиль пользователя
    user = database.get_user_by_id(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Получаем веса
    if request.use_saved_weights:
        weights = database.get_user_weights(request.user_id)
        if not weights:
            weights = DEFAULT_WEIGHTS
        is_consistent = True  # Предполагаем, что сохраненные веса проверены
    else:
        # Если не используем сохраненные, берем стандартные
        weights = DEFAULT_WEIGHTS
        is_consistent = True

    # Получаем кандидатов
    if request.candidate_ids:
        candidates = []
        for cand_id in request.candidate_ids:
            cand = database.get_user_by_id(cand_id)
            if cand:
                candidates.append(cand)
    else:
        # Все пользователи противоположного пола
        all_users = database.get_all_users()
        candidates = [
            u for u in all_users
            if u["id"] != request.user_id
               and u["gender"] == user["looking_for"]
        ]

    # Конвертируем профили
    user_profile = convert_user_to_profile(user)
    candidate_profiles = [convert_user_to_profile(c) for c in candidates]

    # Вычисляем совместимость
    compatibility_results = compute_batch_compatibility(
        user_profile=user_profile,
        candidates_profiles=candidate_profiles,
        criteria_weights=weights
    )

    # Добавляем ID кандидатов в результаты
    for i, result in enumerate(compatibility_results):
        result["candidate_id"] = candidates[i]["id"]

    # Находим топ-матч
    top_match = compatibility_results[0] if compatibility_results else None

    return CompatibilityResponse(
        user_id=request.user_id,
        user_name=user["name"],
        weights_used=weights,
        weights_consistent=is_consistent,
        candidates=compatibility_results[:20],  # Топ-20
        top_match=top_match
    )


@app.get("/api/compatibility/recommendations/{user_id}")
def get_recommendations(user_id: int, limit: int = 10):
    """
    Получает персонализированные рекомендации для пользователя.
    """
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Получаем веса
    weights = database.get_user_weights(user_id)
    if not weights:
        weights = DEFAULT_WEIGHTS

    # Получаем всех подходящих кандидатов
    all_users = database.get_all_users()
    candidates = [
        u for u in all_users
        if u["id"] != user_id
           and u["gender"] == user["looking_for"]
    ]

    # Конвертируем и вычисляем
    user_profile = convert_user_to_profile(user)
    candidate_profiles = [convert_user_to_profile(c) for c in candidates]

    results = compute_batch_compatibility(
        user_profile=user_profile,
        candidates_profiles=candidate_profiles,
        criteria_weights=weights
    )

    # Добавляем базовую информацию о кандидатах
    for i, result in enumerate(results[:limit]):
        candidate = candidates[i]
        result["candidate_id"] = candidate["id"]
        result["candidate_name"] = candidate["name"]
        result["candidate_age"] = candidate["age"]
        result["candidate_city"] = candidate["city"]
        result["candidate_avatar"] = candidate.get("avatar")

    return {
        "user_id": user_id,
        "recommendations": results[:limit],
        "total_candidates": len(results)
    }


# ========== ЭНДПОИНТЫ ДЛЯ ЛАЙКОВ ==========

@app.post("/api/like")
def like_person(request: LikeRequest):
    if request.from_user_id == request.to_user_id:
        raise HTTPException(status_code=400, detail="Нельзя лайкнуть самого себя")

    from_user = database.get_user_by_id(request.from_user_id)
    to_user = database.get_user_by_id(request.to_user_id)

    if not from_user:
        raise HTTPException(status_code=404, detail="Отправитель не найден")
    if not to_user:
        raise HTTPException(status_code=404, detail="Получатель не найден")

    success = database.add_like(request.from_user_id, request.to_user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Лайк уже существует")

    is_match = database.check_match(request.from_user_id, request.to_user_id)

    # Если мэтч - вычисляем совместимость
    compatibility_score = None
    if is_match:
        user_profile = convert_user_to_profile(from_user)
        candidate_profile = convert_user_to_profile(to_user)
        weights = database.get_user_weights(request.from_user_id) or DEFAULT_WEIGHTS

        compat_result = compute_compatibility(
            user_profile,
            candidate_profile,
            weights
        )
        compatibility_score = compat_result["compatibility_score"]

    return {
        "status": "success",
        "is_match": is_match,
        "compatibility_score": compatibility_score,
        "message": f"Вы лайкнули {to_user['name']}" + (" Взаимно! 🎉" if is_match else "")
    }


@app.get("/api/likes/received/{user_id}")
def get_received_likes(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    likes = database.get_likes_received(user_id)
    return {"received_likes": likes}


@app.get("/api/likes/given/{user_id}")
def get_given_likes(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    likes = database.get_likes_given(user_id)
    return {"given_likes": likes}


@app.get("/api/matches/{user_id}")
def get_matches(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    matches = database.get_matches(user_id)

    # Добавляем совместимость к каждому мэтчу
    user_profile = convert_user_to_profile(user)
    weights = database.get_user_weights(user_id) or DEFAULT_WEIGHTS

    for match in matches:
        match_profile = convert_user_to_profile(match)
        compat_result = compute_compatibility(user_profile, match_profile, weights)
        match["compatibility_score"] = compat_result["compatibility_score"]

    # Сортируем мэтчи по совместимости
    matches.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)

    return {"matches": matches}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)