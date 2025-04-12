
from fastapi import APIRouter

from app.api import auth, chat, project


main_router = APIRouter()

main_router.include_router(auth.router, prefix="/auth", tags=["auth"])
main_router.include_router(chat.router, prefix="/chat", tags=["chat"])
main_router.include_router(project.router, prefix="/project", tags=["project"])
