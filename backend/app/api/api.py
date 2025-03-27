
from fastapi import APIRouter

from app.api import auth


main_router = APIRouter()

main_router.include_router(auth.router, prefix="/auth", tags=["auth"])
