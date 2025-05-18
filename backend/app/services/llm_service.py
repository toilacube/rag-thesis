import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.config.config import Config, getConfig
from app.llm_providers.llm_factory import LLMFactory
from fastapi import Depends

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, app_config: Config = Depends(getConfig)):
        self.app_config = app_config
        # Client and model are initialized per call to allow dynamic provider/model if needed,
        # or could be initialized once if always using the default.
        # For simplicity, LLMFactory.create_async_client will be called in methods.

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None, # Override default provider
        model_name: Optional[str] = None, # Override default model
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None # e.g. {"type": "json_object"}
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]: # (content, usage_data)
        """
        Gets a chat completion from the configured LLM provider.
        Returns the content string and usage dictionary.
        """
        selected_provider = provider or self.app_config.CHAT_PROVIDER
        
        try:
            client, resolved_model_name = LLMFactory.create_async_client(
                app_config=self.app_config,
                provider=selected_provider
            )
            
            current_model_name = model_name or resolved_model_name
            current_temperature = temperature if temperature is not None else self.app_config.LLM_DEFAULT_TEMPERATURE
            current_max_tokens = max_tokens or self.app_config.LLM_DEFAULT_MAX_TOKENS

            logger.info(f"Requesting chat completion from {selected_provider} model {current_model_name} with temp {current_temperature}")
            
            completion_kwargs = {
                "model": current_model_name,
                "messages": messages,
                "temperature": current_temperature,
                "max_tokens": current_max_tokens,
            }
            if response_format:
                completion_kwargs["response_format"] = response_format
             
            # For Ollama, response_format might need to be passed differently or handled by prompt
            if selected_provider == "ollama" and response_format and response_format.get("type") == "json_object":
                # Ollama uses a top-level "format: json" in payload if client supports it
                # The OllamaClient in llm_factory handles this.
                pass


            completion = await client.chat.completions.create(**completion_kwargs)
            
            content = completion.choices[0].message.content
            usage = completion.usage # Assuming OpenAI-like usage object
            
            usage_data = {
                "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(usage, 'completion_tokens', 0),
                "total_tokens": getattr(usage, 'total_tokens', 0),
            }
            logger.info(f"Completion received. Usage: {usage_data}")
            return content, usage_data

        except Exception as e:
            logger.error(f"Error getting chat completion from {selected_provider}: {e}", exc_info=True)
            return None, None

    async def decide_rag_necessity(self, history: List[Dict[str, str]], user_question: str) -> Optional[Dict[str, Any]]:
        """
        Uses LLM to decide if RAG is needed.
        Returns a dictionary like {"need_rag": True/False, "reason": "..."} or None on error.
        """
        from app.llm_providers.prompt_factory import ChatPromptFactory # Local import to avoid circularity if any
        
        prompt = ChatPromptFactory.rag_decision_prompt(history, user_question)
        messages = [{"role": "user", "content": prompt}] # Simplified: entire prompt as user message

        # Force JSON response from LLM if provider supports it
        # For OpenAI, it's response_format={"type": "json_object"}
        # For Ollama, it's "format": "json" in the payload, handled by OllamaClient
        response_format_json = {"type": "json_object"}

        content, _ = await self.get_chat_completion(
            messages=messages,
            temperature=0.5, # Low temp for deterministic decision
            # max_tokens=150, # Ample for the JSON response
            # response_format=response_format_json
        )

        if content:
            try:
                # Extract JSON from the content string if it's wrapped
                # Basic extraction, might need more robust parsing for some models
                json_content_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
                if json_content_match:
                    json_str = json_content_match.group(1)
                else: # Assume the content is the JSON string itself
                    json_str = content.strip()
                    
                decision = json.loads(json_str)
                if "need_rag" in decision and isinstance(decision["need_rag"], bool):
                    return decision
                else:
                    logger.error(f"LLM RAG decision response missing 'need_rag' boolean: {content}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse RAG decision JSON from LLM: {e}. Content: {content}")
        return None

def get_llm_service(app_config: Config = Depends(getConfig)) -> LLMService:
    return LLMService(app_config)