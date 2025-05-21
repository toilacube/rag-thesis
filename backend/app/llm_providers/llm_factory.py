from typing import Optional, Tuple, Any
from openai import AsyncOpenAI
import httpx # Still needed for general HTTP knowledge, though not directly for OpenAI client
import logging

from app.config.config import getConfig, Config
from fastapi import Depends

logger = logging.getLogger(__name__)

# OllamaClient class is now REMOVED

class LLMFactory:
    @staticmethod
    def create_async_client(
        app_config: Config,
        provider: Optional[str] = None,
    ) -> Tuple[AsyncOpenAI, str]: # Now always returns AsyncOpenAI client
        """
        Create an AsyncOpenAI client instance and model name based on the provider.
        Supports "openai" and "gemini" (via OpenAI SDK compatibility).
        """
        provider_to_use = provider or app_config.CHAT_PROVIDER

        if provider_to_use == "openai":
            if not app_config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured for CHAT_PROVIDER 'openai'.")
            logger.info(f"Creating OpenAI client with model: {app_config.OPENAI_MODEL}")
            return AsyncOpenAI(api_key=app_config.OPENAI_API_KEY), app_config.OPENAI_MODEL
        
        elif provider_to_use == "gemini":
            if not app_config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured for CHAT_PROVIDER 'gemini'.")
            
            # The base_url should point to the root of the Gemini API that's OpenAI-compatible.
            # Example: "https://generativelanguage.googleapis.com/v1beta"
            # The OpenAI SDK will append things like "/chat/completions" or "/models/{model_name}:generateContent"
            # based on the operation.
            # For chat completions, it usually expects a path like "/chat/completions" under the base_url.
            # Google's documentation for OpenAI library compatibility should be checked for the exact base_url.
            # A common pattern for Gemini with OpenAI library is:
            # base_url="https://generativelanguage.googleapis.com/v1beta/models" and then model="gemini-pro"
            # Or base_url="https://generativelanguage.googleapis.com/v1beta" and model="gemini-pro"
            # Let's assume the config GEMINI_API_BASE_URL is the correct root.
            logger.info(f"Creating Gemini (via OpenAI SDK) client. Base URL: {app_config.GEMINI_API_BASE_URL}, Model: {app_config.GEMINI_MODEL}")
            return AsyncOpenAI(
                api_key=app_config.GEMINI_API_KEY,
                base_url=app_config.GEMINI_API_BASE_URL
            ), app_config.GEMINI_MODEL
        
        # Remove Ollama provider section
        # elif provider_to_use == "ollama":
        #     ...
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_to_use}. Supported: 'openai', 'gemini'.")

# Dependency for FastAPI (can be removed if LLMService directly instantiates or gets config)
# def get_llm_factory_and_config(app_config: Config = Depends(getConfig)) -> Tuple[LLMFactory, Config]:
#      return LLMFactory(), app_config