from fastapi import APIRouter

from app.api import auth, chat, project, document, user_permission


main_router = APIRouter()

main_router.include_router(auth.router, prefix="/auth", tags=["auth"])
main_router.include_router(chat.router, prefix="/chat", tags=["chat"])
main_router.include_router(project.router, prefix="/project", tags=["project"])
main_router.include_router(document.router, prefix="/document", tags=["document"])
main_router.include_router(user_permission.router, prefix="/users", tags=["users"])
