import logging
from typing import List, Optional, Tuple, Dict, Any
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

    def get_chats_for_user(self, user_id: int) -> List[ChatResponse]:
        chats_db = self.db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
        response_chats = []
        for chat_db in chats_db:
            # Get associated project_id from ChatProject table
            chat_project_link = self.db.query(ChatProject).filter(ChatProject.chat_id == chat_db.id).first()
            project_id = chat_project_link.project_id if chat_project_link else None # Should always exist if created correctly

            if project_id is None: # Should not happen with proper creation
                logger.warning(f"Chat {chat_db.id} is missing a project link.")
                # Decide how to handle: skip, or return with None project_id
                # For now, let's assume it must have a project_id
                continue


            messages_db = self.db.query(Message).filter(Message.chat_id == chat_db.id).order_by(Message.created_at.asc()).all()
            response_chats.append(
                ChatResponse(
                    id=chat_db.id,
                    title=chat_db.title,
                    user_id=chat_db.user_id,
                    project_id=project_id,
                    created_at=chat_db.created_at,
                    updated_at=chat_db.updated_at,
                    messages=[MessageResponse.model_validate(msg) for msg in messages_db]
                )
            )
        return response_chats

    def create_chat_session(self, user_id: int, chat_create_dto: ChatCreate) -> ChatResponse:
        project = self.db.query(Project).filter(Project.id == chat_create_dto.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID {chat_create_dto.project_id} not found.")

        now = datetime.now(UTC)
        new_chat = Chat(
            title=chat_create_dto.title,
            user_id=user_id,
            created_at=now,
            updated_at=now
        )
        self.db.add(new_chat)
        self.db.commit()
        self.db.refresh(new_chat)

        # Link chat to project
        chat_project_link = ChatProject(chat_id=new_chat.id, project_id=chat_create_dto.project_id)
        self.db.add(chat_project_link)
        self.db.commit()

        return ChatResponse(
            id=new_chat.id,
            title=new_chat.title,
            user_id=new_chat.user_id,
            project_id=chat_create_dto.project_id,
            created_at=new_chat.created_at,
            updated_at=new_chat.updated_at,
            messages=[]
        )

    def get_chat_by_id(self, chat_id: int, user_id: int) -> Optional[ChatResponse]:
        chat_db = self.db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
        if not chat_db:
            return None
        
        chat_project_link = self.db.query(ChatProject).filter(ChatProject.chat_id == chat_db.id).first()
        project_id = chat_project_link.project_id if chat_project_link else None
        if project_id is None:
             logger.error(f"Critical: Chat {chat_id} exists but has no project link.")
             # This indicates a data integrity issue if a chat must have a project.
             # Depending on strictness, could raise an internal server error.
             # For now, we'll allow it to proceed but log heavily.
        
        messages_db = self.db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
        return ChatResponse(
            id=chat_db.id,
            title=chat_db.title,
            user_id=chat_db.user_id,
            project_id=project_id, # Can be None if link is missing
            created_at=chat_db.created_at,
            updated_at=chat_db.updated_at,
            messages=[MessageResponse.model_validate(msg) for msg in messages_db]
        )

    async def add_message_to_chat(self, chat_id: int, user_id: int, message_create_dto: MessageCreate) -> Tuple[Optional[MessageResponse], Optional[MessageResponse]]:
        chat = self.get_chat_by_id(chat_id=chat_id, user_id=user_id) # This also verifies ownership
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or access denied.")
        
        if chat.project_id is None: # Chat must be linked to a project for RAG
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat session is not linked to a project, RAG cannot be performed.")

        now = datetime.now(UTC)
        # 1. Save user message
        user_message = Message(
            chat_id=chat_id,
            role="user",
            content=message_create_dto.content,
            created_at=now,
            updated_at=now
        )
        self.db.add(user_message)
        self.db.commit()
        self.db.refresh(user_message)

        # Prepare history for LLM
        history_for_llm = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
        history_for_llm.append({"role": user_message.role, "content": user_message.content}) # Add current user message

        # 2. RAG Decision Step
        logger.info(f"Chat {chat_id}: Deciding RAG necessity for query: '{user_message.content[:50]}...'")
        rag_decision = await self.llm_service.decide_rag_necessity(history_for_llm[:-1], user_message.content) # Exclude current user msg from history for decision prompt
        
        assistant_content: Optional[str] = None
        
        if rag_decision and rag_decision.get("need_rag"):
            logger.info(f"Chat {chat_id}: RAG needed. Reason: {rag_decision.get('reason', 'N/A')}")
            # Perform RAG
            try:
                retrieved_chunks_qdrant = self.qdrant_service.search_chunks(
                    query_text=user_message.content,
                    project_id=chat.project_id, # Use the project_id associated with the chat
                    limit=3 # Configurable limit
                )
                context_for_llm = []
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
                    
                answer_prompt = ChatPromptFactory.rag_answer_prompt(history_for_llm, user_message.content, context_for_llm)
                messages_for_llm = [{"role": "user", "content": answer_prompt}] # Entire prompt as user message
                assistant_content, _ = await self.llm_service.get_chat_completion(messages=messages_for_llm)

            except Exception as e:
                logger.error(f"Chat {chat_id}: Error during RAG retrieval or LLM call: {e}", exc_info=True)
                assistant_content = "I encountered an error trying to find relevant information. Please try rephrasing your question."
        else:
            if rag_decision:
                logger.info(f"Chat {chat_id}: RAG not needed. Reason: {rag_decision.get('reason', 'N/A')}")
            else:
                logger.warning(f"Chat {chat_id}: Could not determine RAG necessity. Proceeding without RAG.")
            
            # Normal LLM call without RAG
            normal_prompt = ChatPromptFactory.normal_answer_prompt(history_for_llm, user_message.content)
            messages_for_llm = [{"role": "user", "content": normal_prompt}]
            assistant_content, _ = await self.llm_service.get_chat_completion(messages=messages_for_llm)

        if assistant_content is None:
            assistant_content = "I'm sorry, I couldn't generate a response at this time." # Fallback

        # 3. Save assistant message
        assistant_message_db = Message(
            chat_id=chat_id,
            role="assistant",
            content=assistant_content,
            created_at=datetime.now(UTC), # Slightly after user message
            updated_at=datetime.now(UTC)
        )
        self.db.add(assistant_message_db)
        
        # Update chat's updated_at timestamp
        chat_db_to_update = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if chat_db_to_update:
            chat_db_to_update.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(assistant_message_db)

        return MessageResponse.model_validate(user_message), MessageResponse.model_validate(assistant_message_db)

def get_chat_service(
     db: Session = Depends(get_db_session),
     llm_service: LLMService = Depends(get_llm_service),
     qdrant_service: QdrantService = Depends(get_qdrant_service)
 ) -> "ChatService": # Forward reference for type hint
     return ChatService(db=db, llm_service=llm_service, qdrant_service=qdrant_service)