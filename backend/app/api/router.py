from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.health import router as health_router
from .routes.meetings import router as meetings_router
from .routes.workspace import router as workspace_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(meetings_router)
api_router.include_router(workspace_router)
