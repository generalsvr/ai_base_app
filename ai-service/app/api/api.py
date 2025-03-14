from fastapi import APIRouter

from app.api.endpoints import ai
from app.core.config import settings

api_router = APIRouter()

# Include all API routers
api_router.include_router(ai.router, prefix=settings.API_PREFIX) 