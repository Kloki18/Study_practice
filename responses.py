"""
DTO: Исходящие ответы

Pydantic-модели для формирования ответов API.
Use cases возвращают словари/объекты, а presentation оборачивает в эти DTO.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ========== ПОЛЬЗОВАТЕЛИ ==========

class UserResponse(BaseModel):
    """Ответ с данными пользователя (без пароля)."""
    id: int
    email: str
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    income: int = 5
    appearance: int = 5
    education: str = "среднее"
    religion: str = "не важно"
    kindness: int = 5
    interests: List[str] = []


class UserListResponse(BaseModel):
    """Ответ со списком пользователей."""
    users: List[UserResponse]
    total: int


# ========== АВТОРИЗАЦИЯ ==========

class AuthResponse(BaseModel):
    """Ответ при регистрации или входе."""
    user_id: int
    email: str
    name: str
    message: str


# ========== МАИ ==========

class WeightsResponse(BaseModel):
    """Ответ с результатами расчёта весов."""
    user_id: int
    weights: Dict[str, float]
    lambda_max: float
    ci: float
    cr: float
    is_consistent: bool
    criteria_list: List[str]


class SavedWeightsResponse(BaseModel):
    """Ответ после сохранения весов."""
    message: str
    weights: Dict[str, float]


# ========== СОВМЕСТИМОСТЬ ==========

class CandidateInfo(BaseModel):
    """Информация о кандидате с оценкой совместимости."""
    candidate_id: int
    candidate_name: str
    candidate_age: Optional[int] = None
    candidate_city: Optional[str] = None
    candidate_avatar: Optional[str] = None
    compatibility_score: float  # 0-100
    best_criterion: Optional[str] = None
    worst_criterion: Optional[str] = None
    average_similarity: Optional[float] = None


class CompatibilityResponse(BaseModel):
    """Ответ с результатами совместимости."""
    user_id: int
    user_name: str
    weights_used: Dict[str, float]
    weights_consistent: bool
    candidates: List[CandidateInfo]
    top_match: Optional[CandidateInfo] = None


class RecommendationsResponse(BaseModel):
    """Ответ с персонализированными рекомендациями."""
    user_id: int
    recommendations: List[CandidateInfo]
    total_candidates: int


# ========== ЛАЙКИ ==========

class LikeInfoResponse(BaseModel):
    """Информация о лайке."""
    user_id: int
    user_name: str
    user_age: int
    user_city: str
    user_avatar: Optional[str] = None


class LikesListResponse(BaseModel):
    """Список лайков."""
    likes: List[LikeInfoResponse]


class LikeActionResponse(BaseModel):
    """Ответ на действие лайка."""
    status: str
    is_match: bool
    compatibility_score: Optional[float] = None
    message: str


class MatchResponse(BaseModel):
    """Ответ со списком мэтчей."""
    matches: List[CandidateInfo]