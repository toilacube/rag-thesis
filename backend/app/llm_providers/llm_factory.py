from typing import Optional, Tuple, Any
from fastapi import Depends
from openai import AsyncOpenAI
import httpx

from app.config.config import getConfig, Config

# Dont need this ollama client
class OllamaClient:
    """A simple client to interact with Ollama's chat API, mimicking AsyncOpenAI structure for convenience."""
    def __init__(self, base_url: str, model: str, temperature: float):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.chat = self.Chat(self)

    class Chat:
        def __init__(self, outer):
            self.outer = outer
            self.completions = self.Completions(outer)

        class Completions:
            def __init__(self, outer):
                self.outer = outer

            async def create(self, model: str, messages: list, temperature: float, stream: bool = False, max_tokens: Optional[int] = None, response_format: Optional[dict] = None):
                # stream and max_tokens are not directly used in this simple Ollama client example for non-streaming
                # response_format for Ollama needs to be handled by prompt if it's for JSON mode
                
                payload = {
                    "model": model or self.outer.model,
                    "messages": messages,
                    "temperature": temperature if temperature is not None else self.outer.temperature,
                    "stream": stream,
                    "options": {}
                }
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
                if response_format and response_format.get("type") == "json_object":
                     payload["format"] = "json"


                ollama_url = f"{self.outer.base_url}/api/chat"
                async with httpx.AsyncClient(timeout=120.0) as client: # Increased timeout
                    try:
                        response = await client.post(ollama_url, json=payload)
                        response.raise_for_status() # Raise an exception for HTTP error codes
                        
                        if stream:
                            # Placeholder for actual streaming implementation if needed later
                            # For now, we'll aggregate if stream=True is passed but not handled by this simple client
                            full_response_data = await response.json() # This won't work for actual stream
                            class MockChoice:
                                def __init__(self, content):
                                    self.message = self.Message(content)
                                class Message:
                                    def __init__(self, content):
                                        self.content = content
                            class MockUsage:
                                 def __init__(self):
                                     self.total_tokens = 0 # Ollama API doesn't easily give token counts
                                     self.prompt_tokens = 0
                                     self.completion_tokens = 0

                            class MockCompletion:
                                def __init__(self, content):
                                    self.choices = [MockChoice(content)]
                                    self.usage = MockUsage() # Add a mock usage object
                            return MockCompletion(full_response_data.get("message", {}).get("content", ""))

                        else:
                            response_data = response.json()
                            # Mimic OpenAI's response structure
                            class Choice:
                                class Message:
                                    def __init__(self, content, role="assistant"):
                                        self.content = content
                                        self.role = role
                                def __init__(self, message_content):
                                    self.message = self.Message(message_content)
                            
                            class Usage: # Mock usage for Ollama
                                def __init__(self, prompt_tokens=0, completion_tokens=0, total_tokens=0):
                                    self.prompt_tokens = response_data.get("prompt_eval_count", 0)
                                    self.completion_tokens = response_data.get("eval_count", 0)
                                    self.total_tokens = self.prompt_tokens + self.completion_tokens


                            class CompletionResponse:
                                def __init__(self, content):
                                    self.choices = [Choice(content)]
                                    self.usage = Usage() # Add usage info if available

                            return CompletionResponse(response_data.get("message", {}).get("content", ""))

                    except httpx.HTTPStatusError as e:
                        # Log or handle HTTP errors from Ollama
                        raise Exception(f"Ollama API request failed: {e.response.status_code} - {e.response.text}") from e
                    except Exception as e:
                        raise Exception(f"Error calling Ollama: {e}") from e
                        
class LLMFactory:
    @staticmethod
    def create_async_client(
        app_config: Config, # Pass the whole config object
        provider: Optional[str] = None,
    ) -> Tuple[Any, str]: # Returns (client, model_name)
        """
        Create an LLM client instance and model name based on the provider.
        """
        provider_to_use = provider or app_config.CHAT_PROVIDER

        if provider_to_use == "openai":
            if not app_config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured.")
            return AsyncOpenAI(api_key=app_config.OPENAI_API_KEY), app_config.OPENAI_MODEL
        
        elif provider_to_use == "gemini": # Using OpenAI library for Gemini via compatible endpoint
            if not app_config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured.")
            # The Gemini API via Google AI Studio can be called with OpenAI's library
            # by setting the base_url appropriately.
            # Example: "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            # The model name for the API call might be just "gemini-pro" or part of the URL.
            # For simplicity, we assume the model name is what's passed to `client.chat.completions.create`
            # and the base_url points to the correct root for the API.
            return AsyncOpenAI(
                api_key=app_config.GEMINI_API_KEY,
                base_url=f"{app_config.GEMINI_API_BASE_URL}/models" # Adjust if base_url should include /models
            ), app_config.GEMINI_MODEL # e.g., "gemini-pro"
        
        elif provider_to_use == "ollama":
            return OllamaClient(
                base_url=app_config.OLLAMA_API_BASE,
                model=app_config.OLLAMA_CHAT_MODEL,
                temperature=app_config.LLM_DEFAULT_TEMPERATURE # Default temp for client
            ), app_config.OLLAMA_CHAT_MODEL
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_to_use}")

def get_llm_factory_provider(app_config: Config = Depends(getConfig)): # Dependency for factory
     return LLMFactory(), app_config