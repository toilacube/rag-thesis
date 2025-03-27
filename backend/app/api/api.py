
from fastapi import APIRouter

from app.api import auth
from app.api import chat


main_router = APIRouter()

main_router.include_router(auth.router, prefix="/auth", tags=["auth"])
main_router.include_router(chat.router, prefix="/chat", tags=["chat"])
