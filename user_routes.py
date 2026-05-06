"""
API: Пользователи

GET    /api/people          — все пользователи
GET    /api/people/{id}     — пользователь по ID
PUT    /api/people/{id}     — обновить профиль
DELETE /api/people/{id}     — удалить профиль
"""

from fastapi import APIRouter, Depends, HTTPException

from application.dto.requests import UpdateUserRequest
from application.use_cases.user_case import (
    GetAllUsersUseCase,
    GetUserByIdUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    UserNotFoundError,
)
from presentation.api.dependencies import (
    get_all_users_use_case,
    get_user_by_id_use_case,
    get_update_user_use_case,
    get_delete_user_use_case,
)

router = APIRouter(prefix="/api", tags=["Пользователи"])


@router.get("/people")
def get_all_people(
    use_case: GetAllUsersUseCase = Depends(get_all_users_use_case),
):
    """Получить всех активных пользователей."""
    users = use_case.execute()
    return {"users": users, "total": len(users)}


@router.get("/people/{user_id}")
def get_person(
    user_id: int,
    use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case),
):
    """Получить пользователя по ID."""
    try:
        return use_case.execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/people/{user_id}")
def update_person(
    user_id: int,
    request: UpdateUserRequest,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
):
    """Обновить данные пользователя."""
    try:
        return use_case.execute(user_id, request)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/people/{user_id}")
def delete_person(
    user_id: int,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
):
    """Удалить пользователя (мягкое удаление)."""
    try:
        return use_case.execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))