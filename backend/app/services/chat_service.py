import logging
from typing import List, Optional, Tuple, Dict, Any, AsyncIterator, Union
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status
import json # Added
import base64 # Added

from app.models.models import Chat, Message, User, Project, ChatProject
from app.dtos.chatDTO import ChatCreate, ChatResponse
from app.dtos.messageDTO import MessageCreate, MessageResponse
from db.database import get_db_session
from app.services.llm_service import LLMService, get_llm_service
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.llm_providers.prompt_factory import ChatPromptFactory
from datetime import datetime, UTC
from sqlalchemy import desc

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
        # Join Chat with ChatProject in a single query and order by updated_at
        chat_with_projects = (
            self.db.query(Chat, ChatProject.project_id)
            .join(ChatProject, Chat.id == ChatProject.chat_id)
            .filter(Chat.user_id == user_id)
            .order_by(desc(Chat.updated_at))
            .all()
        )
        
        # Get all chat IDs to fetch messages in bulk
        chat_ids = [chat.id for chat, _ in chat_with_projects]
        
        # Fetch all messages for all chats in a single query
        # Group messages by chat_id for easier access
        all_messages = {}
        if chat_ids:
            messages_query = (
                self.db.query(Message)
                .filter(Message.chat_id.in_(chat_ids))
                .order_by(Message.created_at.asc())
                .all()
            )
            
            # Group messages by chat_id
            for message in messages_query:
                if message.chat_id not in all_messages:
                    all_messages[message.chat_id] = []
                all_messages[message.chat_id].append(message)
        
        # Build the response
        response_chats = []
        for chat, project_id in chat_with_projects:
            if project_id is None:
                logger.warning(f"Chat {chat.id} is missing a project link. Skipping.")
                continue
                
            # Get messages for this chat from our grouped dictionary
            chat_messages = all_messages.get(chat.id, [])
            
            response_chats.append(
                ChatResponse(
                    id=chat.id, 
                    title=chat.title, 
                    user_id=chat.user_id,
                    project_id=project_id, 
                    created_at=chat.created_at, 
                    updated_at=chat.updated_at,
                    messages=[MessageResponse.model_validate(msg) for msg in chat_messages]
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
        # Use a join to get chat and project_id in a single query
        chat_with_project = (
            self.db.query(Chat, ChatProject.project_id)
            .join(ChatProject, Chat.id == ChatProject.chat_id, isouter=True)
            .filter(Chat.id == chat_id, Chat.user_id == user_id)
            .first()
        )
        
        if not chat_with_project:
            return None
            
        chat_db, project_id = chat_with_project
        
        if project_id is None:
            logger.error(f"Critical: Chat {chat_id} exists but has no project link.")
            
        # Get messages in a separate query
        messages_db = (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        
        return ChatResponse(
            id=chat_db.id,
            title=chat_db.title,
            user_id=chat_db.user_id,
            project_id=project_id,
            created_at=chat_db.created_at,
            updated_at=chat_db.updated_at,
            messages=[MessageResponse.model_validate(msg) for msg in messages_db]
        )

    def _save_message_to_db(self, chat_id: int, role: str, content: str) -> Message:
        now = datetime.now(UTC)
        message_db = Message(
            chat_id=chat_id, role=role, content=content,
            created_at=now, updated_at=now
        )
        self.db.add(message_db)
        chat_db_to_update = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if chat_db_to_update:
            chat_db_to_update.updated_at = now
        self.db.commit()
        self.db.refresh(message_db)
        return message_db

    async def save_user_message(self, chat_id: int, user_id: int, message_create_dto: MessageCreate) -> MessageResponse:
        chat = self.get_chat_by_id(chat_id=chat_id, user_id=user_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or access denied.")
        
        user_message_db = self._save_message_to_db(chat_id, "user", message_create_dto.content)
        return MessageResponse.model_validate(user_message_db)

    async def process_and_stream_assistant_response(
        self,
        chat_id: int,
        user_id: int,
        user_question: str
    ) -> AsyncIterator[Union[str, MessageResponse, Dict[str, Any]]]: # Added Dict for citation_payload
        """
        Processes the user's question, decides on RAG, calls LLM stream,
        saves the full assistant response, and yields deltas, citation payload, and final saved DTO.
        """
        chat = self.get_chat_by_id(chat_id=chat_id, user_id=user_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found (unexpected).")
        if chat.project_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat session is not linked to a project.")

        history_for_llm = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
        rag_decision_history = history_for_llm[:-1] if history_for_llm and history_for_llm[-1]["role"] == "user" else history_for_llm
        rag_decision = await self.llm_service.decide_rag_necessity(rag_decision_history, user_question)

        full_assistant_content_parts = []
        final_llm_data = None
        prompt_for_llm_generation = ""
        
        # This list will hold contexts formatted for the prompt factory and for the citation JSON
        contexts_for_prompt_and_citation: List[Dict[str, Any]] = []

        if rag_decision and rag_decision.get("need_rag"):
            logger.info(f"Chat {chat_id}: RAG needed. Reason: {rag_decision.get('reason', 'N/A')}")
            try:
                # Enrich the query for better vector search
                enriched_query = await self.llm_service.enrich_query_for_rag(rag_decision_history, user_question)
                search_query = enriched_query if enriched_query else user_question
                
                if enriched_query:
                    logger.info(f"Chat {chat_id}: Using enriched query for vector search")
                else:
                    logger.info(f"Chat {chat_id}: Query enrichment failed, using original query")
                
                retrieved_qdrant_hits = self.qdrant_service.search_chunks(
                    query_text=search_query, project_id=chat.project_id, limit=7 # Limit to 3 contexts for now
                )
                if retrieved_qdrant_hits:
                    for i, hit in enumerate(retrieved_qdrant_hits):
                        payload = hit.payload or {}
                        # Prepare context for both prompt (needs index_1) and citation JSON (needs specific metadata)
                        context_data = {
                            "index_1": i + 1, # For mustache template numbering
                            "text": payload.get("text", ""),
                            "metadata": { # For citation JSON and potentially for prompt if template uses it
                                "document_id": payload.get("document_id"),
                                "project_id": payload.get("project_id"),
                                "file_name": payload.get("file_name"),
                                "chunk_id": payload.get("chunk_metadata", {}).get("chunk_id"),
                                "headers": payload.get("chunk_metadata", {}).get("headers")
                                # Add other metadata from payload.chunk_metadata if needed by frontend
                            }
                        }
                        contexts_for_prompt_and_citation.append(context_data)
                    logger.info(f"Chat {chat_id}: Retrieved {len(contexts_for_prompt_and_citation)} chunks for RAG.")

                    # 1. Construct and yield citation_payload if contexts were found
                    citation_json_for_frontend = {
                        "context": [
                            {
                                "page_content": ctx["text"],
                                "metadata": ctx["metadata"] # Already structured correctly
                            } for ctx in contexts_for_prompt_and_citation
                        ]
                    }
                    json_string = json.dumps(citation_json_for_frontend)
                    base64_encoded_citations = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
                    yield { # New event type for citation payload
                        "type": "citation_payload",
                        "data": base64_encoded_citations
                    }

                    # 2. Prepare prompt for LLM using the formatted contexts
                    # contexts_for_prompt_and_citation already contains 'index_1', 'text', 'metadata'
                    prompt_for_llm_generation = ChatPromptFactory.rag_answer_prompt(
                        history_for_llm,
                        user_question,
                        contexts_for_prompt_and_citation # Pass the list of dicts
                    )
                else:
                    logger.info(f"Chat {chat_id}: No chunks retrieved for RAG. Proceeding without RAG context.")
                    prompt_for_llm_generation = ChatPromptFactory.normal_answer_prompt(history_for_llm, user_question)
            except Exception as e:
                logger.error(f"Chat {chat_id}: Error during RAG retrieval: {e}", exc_info=True)
                yield {"type": "delta", "content": "Error during information retrieval. "} # Yield an error delta
                prompt_for_llm_generation = ChatPromptFactory.normal_answer_prompt(history_for_llm, user_question)
        else: # No RAG needed
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
                # If LLM didn't produce content but final_data has it (e.g. some providers)
                if not "".join(full_assistant_content_parts) and item.get("full_content"):
                     full_assistant_content_parts.append(item.get("full_content"))
                break
            elif isinstance(item, dict) and item.get("type") == "error":
                logger.error(f"Chat {chat_id}: LLM stream error: {item.get('message')}")
                partial_content = "".join(full_assistant_content_parts)
                error_message_suffix = f"\n[ERROR: Stream interrupted: {item.get('message', 'Unknown LLM Error')}]"
                full_assistant_content_parts.append(error_message_suffix) # Append error to what was gathered
                final_llm_data = item
                break

        final_assistant_content = "".join(full_assistant_content_parts)
        if not final_assistant_content: # Ensure there's always some content
            if final_llm_data and final_llm_data.get("type") == "error":
                final_assistant_content = final_llm_data.get("full_content", "Sorry, I encountered an error generating a response.")
            elif final_llm_data and final_llm_data.get("full_content"):
                 final_assistant_content = final_llm_data.get("full_content")
            else:
                final_assistant_content = "Sorry, I could not generate a response for your query."
        
        assistant_message_db = self._save_message_to_db(chat_id, "assistant", final_assistant_content)
        yield MessageResponse.model_validate(assistant_message_db)

def get_chat_service(
    db: Session = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service)
) -> ChatService:
    return ChatService(db=db, llm_service=llm_service, qdrant_service=qdrant_service)
