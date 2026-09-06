from fastapi import APIRouter

from .admin import router as admin_router
from .commands import router as commands_router
from .devices import router as devices_router
from .logs import router as logs_router
from .mqtt_auth import router as mqtt_auth_router
from .pins import router as pins_router
from .properties import router as properties_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(mqtt_auth_router)
api_v1_router.include_router(properties_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(pins_router)
api_v1_router.include_router(logs_router)
api_v1_router.include_router(commands_router)
api_v1_router.include_router(admin_router)

__all__ = ["api_v1_router"]
