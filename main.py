"""
ТОЧКА ВХОДА

Собирает всё приложение:
- FastAPI
- CORS для фронтенда
- Роутеры из presentation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api import (
    auth_router,
    user_router,
    ahp_router,
    compatibility_router,
    like_router,
)

# ============================================================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ============================================================

app = FastAPI(
    title="Сервис подбора супруга",
    description="API для сервиса знакомств с интеллектуальным подбором",
    version="1.0.0",
)

# ============================================================
# CORS (для React-фронтенда)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React dev server (Vite)
        "http://localhost:3000",  # React dev server (CRA)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# ============================================================

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(ahp_router)
app.include_router(compatibility_router)
app.include_router(like_router)


# ============================================================
# КОРНЕВОЙ ЭНДПОИНТ
# ============================================================

@app.get("/")
def home():
    """Проверка, что сервер запущен."""
    return {
        "message": "Сервис подбора супруга работает!",
        "docs": "/docs",
        "version": "1.0.0",
    }


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Автоперезагрузка при изменениях
    )