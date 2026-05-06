"""
DEPENDENCY INJECTION

Собирает все зависимости для use cases.
Презентационный слой получает готовые use cases через Depends().
"""

from infrastructure.db.connection import init_database
from infrastructure.db.user_repository import UserRepository
from infrastructure.db.weight_repository import WeightRepository
from infrastructure.db.like_repository import LikeRepository
from infrastructure.algorithms.ahp_calculator import NumpyAHPCalculator
from infrastructure.algorithms.similarity_functions import create_default_similarity_functions
from infrastructure.algorithms.hash_service import Sha256HashService

from domain.services.ahp_services import AHPService
from domain.services.compatibility_services import CompatibilityEvaluator

from application.use_cases.auth_case import RegisterUseCase, LoginUseCase
from application.use_cases.user_case import (
    GetAllUsersUseCase,
    GetUserByIdUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
)
from application.use_cases.ahp_case import (
    CalculateWeightsUseCase,
    SaveWeightsUseCase,
    GetWeightsUseCase,
)
from application.use_cases.compability_case import (
    CalculateCompatibilityUseCase,
    GetRecommendationsUseCase,
)
from application.use_cases.likes_case import (
    LikeUserUseCase,
    GetReceivedLikesUseCase,
    GetGivenLikesUseCase,
    GetMatchesUseCase,
)


# ============================================================
# ИНИЦИАЛИЗАЦИЯ ИНФРАСТРУКТУРЫ
# ============================================================

# Инициализируем БД при старте
init_database()

# Создаём репозитории (синглтоны)
user_repo = UserRepository()
weight_repo = WeightRepository()
like_repo = LikeRepository()

# Создаём сервисы
hash_service = Sha256HashService()
ahp_calculator = NumpyAHPCalculator()
ahp_service = AHPService(ahp_calculator)
similarity_functions = create_default_similarity_functions()
compatibility_evaluator = CompatibilityEvaluator(similarity_functions)


# ============================================================
# ФАБРИКИ USE CASES (для FastAPI Depends)
# ============================================================

def get_register_use_case() -> RegisterUseCase:
    return RegisterUseCase(user_repo, weight_repo, hash_service)


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(user_repo, hash_service)


def get_all_users_use_case() -> GetAllUsersUseCase:
    return GetAllUsersUseCase(user_repo)


def get_user_by_id_use_case() -> GetUserByIdUseCase:
    return GetUserByIdUseCase(user_repo)


def get_update_user_use_case() -> UpdateUserUseCase:
    return UpdateUserUseCase(user_repo)


def get_delete_user_use_case() -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo)


def get_calculate_weights_use_case() -> CalculateWeightsUseCase:
    return CalculateWeightsUseCase(ahp_service)


def get_save_weights_use_case() -> SaveWeightsUseCase:
    return SaveWeightsUseCase(weight_repo)


def get_get_weights_use_case() -> GetWeightsUseCase:
    return GetWeightsUseCase(weight_repo)


def get_calculate_compatibility_use_case() -> CalculateCompatibilityUseCase:
    return CalculateCompatibilityUseCase(
        user_repo, weight_repo, compatibility_evaluator
    )


def get_recommendations_use_case() -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(
        user_repo, weight_repo, compatibility_evaluator
    )


def get_like_user_use_case() -> LikeUserUseCase:
    return LikeUserUseCase(
        user_repo, like_repo, weight_repo, compatibility_evaluator
    )


def get_received_likes_use_case() -> GetReceivedLikesUseCase:
    return GetReceivedLikesUseCase(user_repo, like_repo)


def get_given_likes_use_case() -> GetGivenLikesUseCase:
    return GetGivenLikesUseCase(user_repo, like_repo)


def get_matches_use_case() -> GetMatchesUseCase:
    return GetMatchesUseCase(
        user_repo, like_repo, weight_repo, compatibility_evaluator
    )