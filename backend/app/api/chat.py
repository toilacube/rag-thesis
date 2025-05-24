import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Tuple, AsyncIterator, Dict, Any # Added Dict, Any
from fastapi.responses import StreamingResponse
import json

# Remove pytest.Config import, it's not used for SSE data formatting directly.
# from pytest import Config 

from app.config.config import getConfig, Config # Corrected import
from app.core.api_reponse import api_response
from app.dtos.chatDTO import ChatCreate, ChatResponse
from app.dtos.messageDTO import MessageCreate, MessageResponse
from app.services.chat_service import ChatService, get_chat_service
from app.core.security import get_current_user
from app.models.models import User
from app.services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter()

# ... (test_llm_chat_stream, get_user_chats, create_new_chat, get_specific_chat remain the same) ...
@router.post("/test-stream")
async def test_llm_chat_stream(
    test_prompt: str = "Hello, tell me a very short story.",
    llm_service: LLMService = Depends(get_llm_service),
    app_config: Config = Depends(getConfig) 
):
    logger.info(f"--- Testing LLM Stream with provider: {app_config.CHAT_PROVIDER} ---")
    logger.info(f"Test prompt: {test_prompt}")
    messages = [{"role": "user", "content": test_prompt}]
    async def event_generator():
        provider_name = app_config.CHAT_PROVIDER
        model_name = "N/A"
        if provider_name == 'openai': model_name = app_config.OPENAI_MODEL
        elif provider_name == 'gemini': model_name = app_config.GEMINI_MODEL
        
        yield f"data: {json.dumps({'type': 'info', 'message': f'Starting stream with provider: {provider_name}, model: {model_name}'})}\n\n"
        try:
            async for item in llm_service.get_chat_completion_stream(messages=messages):
                if isinstance(item, str):
                    logger.debug(f"Stream delta: {item}")
                    yield f"data: {json.dumps({'type': 'delta', 'content': item})}\n\n"
                elif isinstance(item, dict) and item.get("type") == "final_data":
                    logger.info(f"Stream final data: {item}")
                    yield f"data: {json.dumps({'type': 'final_data', 'data': item})}\n\n"
                    break 
                elif isinstance(item, dict) and item.get("type") == "error":
                    logger.error(f"Stream error data: {item}")
                    yield f"data: {json.dumps({'type': 'error_data', 'data': item})}\n\n"
                    break
            yield f"data: {json.dumps({'type': 'stream_end', 'message': 'LLM stream finished.'})}\n\n"
        except Exception as e:
            logger.error(f"Exception in test_llm_stream event_generator: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'critical_error', 'message': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'stream_end', 'message': 'LLM stream finished with critical error.'})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    chats = chat_service.get_chats_for_user(user_id=current_user.id)
    return chats

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_new_chat(
    chat_create_dto: ChatCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    chat = chat_service.create_chat_session(user_id=current_user.id, chat_create_dto=chat_create_dto)
    return chat

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_specific_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    chat = chat_service.get_chat_by_id(chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found or access denied.")
    return chat

@router.post("/{chat_id}/message")
async def send_message_to_chat_streamed(
    chat_id: int,
    message_create_dto: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    if message_create_dto.role != "user":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message role must be 'user'.")

    try:
        user_message_response = await chat_service.save_user_message(
            chat_id=chat_id,
            user_id=current_user.id,
            message_create_dto=message_create_dto
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to save user message for chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save user message: {str(e)}")

    async def event_generator():
        yield f"data: {json.dumps({'type': 'user_message_saved', 'message': user_message_response.model_dump(mode='json')})}\n\n"
        
        try:
            async for item in chat_service.process_and_stream_assistant_response(
                chat_id=chat_id,
                user_id=current_user.id,
                user_question=message_create_dto.content
            ):
                if isinstance(item, str):  # Text delta
                    yield f"data: {json.dumps({'type': 'delta', 'content': item})}\n\n"
                elif isinstance(item, MessageResponse):  # Final saved assistant message DTO
                    yield f"data: {json.dumps({'type': 'assistant_message_saved', 'message': item.model_dump(mode='json')})}\n\n"
                elif isinstance(item, dict) and item.get("type") == "citation_payload": # Handle new citation payload
                    yield f"data: {json.dumps(item)}\n\n" # item is already a dict {"type": "citation_payload", "data": "..."}
                # Ensure other dict types (like potential errors from LLMService not caught yet) are handled or logged
                elif isinstance(item, dict):
                     logger.warning(f"Received unhandled dictionary item in stream for chat {chat_id}: {item}")
                     # Potentially yield it if it's an error type meant for client
                     if item.get("type") == "error_from_llm_service_TODO": # Example, if LLMService yields errors differently
                         yield f"data: {json.dumps(item)}\n\n"


            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
        except HTTPException as e:
             yield f"data: {json.dumps({'type': 'error', 'detail': e.detail, 'status_code': e.status_code})}\n\n"
             yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
        except Exception as e:
            logger.error(f"Error during assistant response streaming for chat {chat_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': 'An unexpected error occurred while generating the response.'})}\n\n"
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")