from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Tuple

from app.core.api_reponse import api_response # Your existing response wrapper
from app.dtos.chatDTO import ChatCreate, ChatResponse
from app.dtos.messageDTO import MessageCreate, MessageResponse
from app.services.chat_service import ChatService, get_chat_service # Corrected import
from app.core.security import get_current_user
from app.models.models import User

router = APIRouter()

@router.get("/", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service) # Use new get_chat_service
):
    """Get all chat sessions for the current authenticated user."""
    chats = chat_service.get_chats_for_user(user_id=current_user.id)
    return chats # FastAPI will wrap this in your api_response if you set it globally, or do it manually

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_new_chat(
    chat_create_dto: ChatCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat session linked to a project."""
    chat = chat_service.create_chat_session(user_id=current_user.id, chat_create_dto=chat_create_dto)
    return chat

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_specific_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a specific chat session by ID, if it belongs to the current user."""
    chat = chat_service.get_chat_by_id(chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found or access denied.")
    return chat

@router.post("/{chat_id}/message", response_model=Tuple[MessageResponse, MessageResponse])
async def send_message_to_chat(
    chat_id: int,
    message_create_dto: MessageCreate, # Only content and role (user)
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to a specific chat session.
    The user's message is saved, and an assistant's response (potentially RAG-enhanced) is generated and saved.
    Returns both the saved user message and the assistant's message.
    """
    if message_create_dto.role != "user": # Ensure message being sent is from user
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message role must be 'user'.")

    user_msg, assistant_msg = await chat_service.add_message_to_chat(
        chat_id=chat_id, 
        user_id=current_user.id, 
        message_create_dto=message_create_dto
    )
    if not user_msg or not assistant_msg: # Should not happen if service raises HTTPExceptions for critical errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process message.")
    return user_msg, assistant_msg