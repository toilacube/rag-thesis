import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncIterator, Union

from openai import AsyncOpenAI # Direct import
from openai.types.chat import ChatCompletionChunk # For type hinting

from app.config.config import Config, getConfig
from app.llm_providers.llm_factory import LLMFactory
from fastapi import Depends

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, app_config: Config = Depends(getConfig)):
        self.app_config = app_config

    async def get_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None, # Provider override
        model_name: Optional[str] = None, # Model override
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None # e.g. {"type": "json_object"}
    ) -> AsyncIterator[Union[str, Dict[str, Any]]]:
        """
        Gets a streaming chat completion from OpenAI or Gemini (via OpenAI SDK).
        Yields text deltas (str) then a final dictionary with full content and usage.
        """
        selected_provider = provider or self.app_config.CHAT_PROVIDER
        full_response_text_parts = []
        collected_usage_data = {
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0
        }

        try:
            # LLMFactory now returns AsyncOpenAI client directly for supported providers
            client: AsyncOpenAI
            client, resolved_model_name = LLMFactory.create_async_client(
                # app_config=self.app_config,
                provider=selected_provider
            )
            
            current_model_name = model_name or resolved_model_name
            current_temperature = temperature if temperature is not None else self.app_config.LLM_DEFAULT_TEMPERATURE
            current_max_tokens = max_tokens or self.app_config.LLM_DEFAULT_MAX_TOKENS

            logger.info(f"Requesting STREAMING chat completion from {selected_provider} model {current_model_name}")
            
            completion_kwargs = {
                "model": current_model_name,
                "messages": messages,
                "temperature": current_temperature,
                # "max_tokens": current_max_tokens,
                "stream": True,
                "stream_options": {"include_usage": True} # For OpenAI and potentially Gemini via SDK
            }
            if response_format:
                completion_kwargs["response_format"] = response_format
            
            response_stream = await client.chat.completions.create(**completion_kwargs)
            
            chunk: ChatCompletionChunk # Type hint for clarity
            async for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta_content = chunk.choices[0].delta.content
                    full_response_text_parts.append(delta_content)
                    yield delta_content
                
                if chunk.usage: # This will be on the final chunk when include_usage=True
                    collected_usage_data["prompt_tokens"] = getattr(chunk.usage, 'prompt_tokens', 0)
                    collected_usage_data["completion_tokens"] = getattr(chunk.usage, 'completion_tokens', 0)
                    collected_usage_data["total_tokens"] = getattr(chunk.usage, 'total_tokens', 0)
                    # For OpenAI, the last chunk with usage has empty choices.delta.content
                    # So, we don't expect more content deltas after this.

            final_full_content = "".join(full_response_text_parts)
            logger.info(f"Stream finished for {selected_provider}. Full content length: {len(final_full_content)}. Usage: {collected_usage_data}")
            yield {
                "type": "final_data",
                "full_content": final_full_content,
                "usage": collected_usage_data
            }

        except Exception as e:
            logger.error(f"Error in get_chat_completion_stream from {selected_provider}: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"LLM streaming error: {str(e)}",
                "full_content": "".join(full_response_text_parts) + f"\n[ERROR: Stream interrupted: {str(e)}]",
                "usage": collected_usage_data # Partial usage if any was collected
            }

    async def decide_rag_necessity(self, history: List[Dict[str, str]], user_question: str) -> Optional[Dict[str, Any]]:
        """
        Uses LLM to decide if RAG is needed. Non-streaming.
        Returns a dictionary like {"need_rag": True/False, "reason": "..."} or None on error.
        """
        from app.llm_providers.prompt_factory import ChatPromptFactory # Local import
        
        prompt = ChatPromptFactory.rag_decision_prompt(history, user_question)
        
        selected_provider = self.app_config.CHAT_PROVIDER
        client: AsyncOpenAI
        client, resolved_model_name = LLMFactory.create_async_client(
            provider=selected_provider
        )
        
        messages_for_decision = [{"role": "user", "content": prompt}]
        # For OpenAI and Gemini (via OpenAI SDK), use response_format for JSON
        response_format_json = {"type": "json_object"}
        
        try:
            logger.info(f"Requesting RAG decision from {selected_provider} model {resolved_model_name}")
            completion_kwargs = {
                "model": resolved_model_name,
                "messages": messages_for_decision,
                "temperature": 0.1,
                "max_tokens": 200,
                "stream": False, # Non-streaming for this decision
                "response_format": response_format_json # For OpenAI/Gemini
            }

            completion = await client.chat.completions.create(**completion_kwargs)
            content = completion.choices[0].message.content
            
            if content:
                json_str = content.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[len("```json"):].strip()
                if json_str.endswith("```"):
                    json_str = json_str[:-len("```")].strip()
                
                try:
                    decision = json.loads(json_str)
                    if "need_rag" in decision and isinstance(decision["need_rag"], bool):
                        logger.info(f"RAG decision: {decision}")
                        return decision
                    else:
                        logger.error(f"LLM RAG decision response missing 'need_rag' boolean or invalid format: {content}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse RAG decision JSON from LLM: {e}. Content: {content}")
            return None
        except Exception as e:
            logger.error(f"Error getting RAG decision from {selected_provider}: {e}", exc_info=True)
            return None

def get_llm_service(app_config: Config = Depends(getConfig)) -> LLMService:
    return LLMService(app_config)
