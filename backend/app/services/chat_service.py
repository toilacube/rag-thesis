import logging
from typing import List, Optional, Tuple, Dict, Any, AsyncIterator, Union # Added AsyncIterator, Union
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.models.models import Chat, Message, User, Project, ChatProject
from app.dtos.chatDTO import ChatCreate, ChatResponse
from app.dtos.messageDTO import MessageCreate, MessageResponse
from db.database import get_db_session
from app.services.llm_service import LLMService, get_llm_service
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.llm_providers.prompt_factory import ChatPromptFactory
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, 
                    db: Session = Depends(get_db_session),
                    llm_service: LLMService = Depends(get_llm_service),
                    qdrant_service: QdrantService = Depends(get_qdrant_service)):
        self.db = db
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service

    # Non-streaming methods remain largely the same
    def get_chats_for_user(self, user_id: int) -> List[ChatResponse]:
        chats_db = self.db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
        response_chats = []
        for chat_db in chats_db:
            chat_project_link = self.db.query(ChatProject).filter(ChatProject.chat_id == chat_db.id).first()
            project_id = chat_project_link.project_id if chat_project_link else None
            if project_id is None:
                logger.warning(f"Chat {chat_db.id} is missing a project link. Skipping.")
                continue
            messages_db = self.db.query(Message).filter(Message.chat_id == chat_db.id).order_by(Message.created_at.asc()).all()
            response_chats.append(
                ChatResponse(
                    id=chat_db.id, title=chat_db.title, user_id=chat_db.user_id,
                    project_id=project_id, created_at=chat_db.created_at, updated_at=chat_db.updated_at,
                    messages=[MessageResponse.model_validate(msg) for msg in messages_db]
                )
            )
        return response_chats

    def create_chat_session(self, user_id: int, chat_create_dto: ChatCreate) -> ChatResponse:
        project = self.db.query(Project).filter(Project.id == chat_create_dto.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID {chat_create_dto.project_id} not found.")
        now = datetime.now(UTC)
        new_chat = Chat(title=chat_create_dto.title, user_id=user_id, created_at=now, updated_at=now)
        self.db.add(new_chat)
        self.db.commit()
        self.db.refresh(new_chat)
        chat_project_link = ChatProject(chat_id=new_chat.id, project_id=chat_create_dto.project_id)
        self.db.add(chat_project_link)
        self.db.commit()
        return ChatResponse(
            id=new_chat.id, title=new_chat.title, user_id=new_chat.user_id,
            project_id=chat_create_dto.project_id, created_at=new_chat.created_at,
            updated_at=new_chat.updated_at, messages=[]
        )

    def get_chat_by_id(self, chat_id: int, user_id: int) -> Optional[ChatResponse]:
        chat_db = self.db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
        if not chat_db: return None
        chat_project_link = self.db.query(ChatProject).filter(ChatProject.chat_id == chat_db.id).first()
        project_id = chat_project_link.project_id if chat_project_link else None
        if project_id is None:
            logger.error(f"Critical: Chat {chat_id} exists but has no project link.")
            # Potentially raise an error or handle as per application requirements
        messages_db = self.db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
        return ChatResponse(
            id=chat_db.id, title=chat_db.title, user_id=chat_db.user_id,
            project_id=project_id, created_at=chat_db.created_at, updated_at=chat_db.updated_at,
            messages=[MessageResponse.model_validate(msg) for msg in messages_db]
        )

    def _save_message_to_db(self, chat_id: int, role: str, content: str) -> Message:
        now = datetime.now(UTC)
        message_db = Message(
            chat_id=chat_id, role=role, content=content,
            created_at=now, updated_at=now
        )
        self.db.add(message_db)
        # Update chat's updated_at timestamp
        chat_db_to_update = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if chat_db_to_update:
            chat_db_to_update.updated_at = now
        self.db.commit()
        self.db.refresh(message_db)
        return message_db

    async def save_user_message(self, chat_id: int, user_id: int, message_create_dto: MessageCreate) -> MessageResponse:
        """Saves the user message and returns its DTO. Verifies chat ownership."""
        chat = self.get_chat_by_id(chat_id=chat_id, user_id=user_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or access denied.")
        
        user_message_db = self._save_message_to_db(chat_id, "user", message_create_dto.content)
        return MessageResponse.model_validate(user_message_db)

    async def process_and_stream_assistant_response(
        self, 
        chat_id: int, 
        user_id: int, # For fetching historical messages correctly
        user_question: str # The latest user question content
    ) -> AsyncIterator[Union[str, MessageResponse]]: # Yields text deltas (str) or final MessageResponse
        """
        Processes the user's question, decides on RAG, calls LLM stream,
        saves the full assistant response, and yields deltas and final saved DTO.
        """
        chat = self.get_chat_by_id(chat_id=chat_id, user_id=user_id) # Verifies ownership and gets chat details
        if not chat:
            # This should ideally not be reached if save_user_message was called first and succeeded
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found (unexpected).")
        if chat.project_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat session is not linked to a project.")

        # History for LLM: all messages from DB for this chat + the latest user question (already saved)
        history_for_llm = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
        # The latest user message is already in chat.messages because get_chat_by_id fetches fresh data

        logger.info(f"Chat {chat_id}: Deciding RAG for query: '{user_question[:50]}...'")
        # History for RAG decision should not include the current question itself as part of "history"
        rag_decision_history = history_for_llm[:-1] if history_for_llm and history_for_llm[-1]["role"] == "user" else history_for_llm

        rag_decision = await self.llm_service.decide_rag_necessity(rag_decision_history, user_question)
        
        full_assistant_content_parts = []
        final_llm_data = None
        prompt_for_llm_generation = ""
        context_for_llm = []

        if rag_decision and rag_decision.get("need_rag"):
            logger.info(f"Chat {chat_id}: RAG needed. Reason: {rag_decision.get('reason', 'N/A')}")
            try:
                retrieved_chunks_qdrant = self.qdrant_service.search_chunks(
                    query_text=user_question, project_id=chat.project_id, limit=3
                )
                if retrieved_chunks_qdrant:
                    for hit in retrieved_chunks_qdrant:
                        payload = hit.payload or {}
                        context_for_llm.append({
                            "text": payload.get("text", ""),
                            "metadata": payload.get("chunk_metadata", {"file_name": "Unknown", "chunk_id": str(hit.id)})
                        })
                    logger.info(f"Chat {chat_id}: Retrieved {len(context_for_llm)} chunks for RAG.")
                else:
                    logger.info(f"Chat {chat_id}: No chunks retrieved for RAG.")
                prompt_for_llm_generation = ChatPromptFactory.rag_answer_prompt(history_for_llm, user_question, context_for_llm)
            except Exception as e:
                logger.error(f"Chat {chat_id}: Error during RAG retrieval: {e}", exc_info=True)
                yield "Error during information retrieval. " # Yield an error delta
                # Fallback to normal answer or end stream with error? For now, let it try normal prompt.
                prompt_for_llm_generation = ChatPromptFactory.normal_answer_prompt(history_for_llm, user_question)
        else:
            if rag_decision: logger.info(f"Chat {chat_id}: RAG not needed. Reason: {rag_decision.get('reason', 'N/A')}")
            else: logger.warning(f"Chat {chat_id}: Could not determine RAG necessity. Proceeding without RAG.")
            prompt_for_llm_generation = ChatPromptFactory.normal_answer_prompt(history_for_llm, user_question)

        messages_for_llm_stream = [{"role": "user", "content": prompt_for_llm_generation}]
        
        async for item in self.llm_service.get_chat_completion_stream(messages=messages_for_llm_stream):
            if isinstance(item, str):
                full_assistant_content_parts.append(item)
                yield item  # Yield text delta
            elif isinstance(item, dict) and item.get("type") == "final_data":
                final_llm_data = item
                break # End of LLM stream
            elif isinstance(item, dict) and item.get("type") == "error": # Handle error from LLMService stream
                logger.error(f"Chat {chat_id}: LLM stream error: {item.get('message')}")
                full_assistant_content_parts.append(item.get("full_content", "[Error in LLM response]")) # Use partial if available
                final_llm_data = item # Store it to save error message
                break


        final_assistant_content = "".join(full_assistant_content_parts)
        if not final_assistant_content and final_llm_data and final_llm_data.get("type") != "error":
             final_assistant_content = final_llm_data.get("full_content", "Sorry, I could not generate a response.")
        elif not final_assistant_content:
             final_assistant_content = "Sorry, I encountered an issue generating a response."


        assistant_message_db = self._save_message_to_db(chat_id, "assistant", final_assistant_content)
        yield MessageResponse.model_validate(assistant_message_db) # Yield final saved DTO

def get_chat_service(
    db: Session = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service)
) -> ChatService:
    return ChatService(db=db, llm_service=llm_service, qdrant_service=qdrant_service)