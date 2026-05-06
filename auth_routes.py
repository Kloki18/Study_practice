"""
API: Авторизация

POST /api/register — регистрация
POST /api/login — вход
"""

from fastapi import APIRouter, Depends, HTTPException

from application.dto.requests import RegisterRequest, LoginRequest
from application.use_cases.auth_case import (
    RegisterUseCase,
    LoginUseCase,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from presentation.api.dependencies import (
    get_register_use_case,
    get_login_use_case,
)

router = APIRouter(prefix="/api", tags=["Авторизация"])


@router.post("/register")
def register(
    request: RegisterRequest,
    use_case: RegisterUseCase = Depends(get_register_use_case),
):
    """
    Регистрация нового пользователя.
    """
    try:
        result = use_case.execute(request)
        return result
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    """
    Вход в систему.
    """
    try:
        result = use_case.execute(request)
        return result
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))