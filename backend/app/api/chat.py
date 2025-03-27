from fastapi import APIRouter, HTTPException
import os
import httpx
from app.core.api_reponse import api_response
from app.dtos.chatDTO import ChatRequest

router = APIRouter()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2") 
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434") 

@router.post("/ollama")
async def ollama_chat(request: ChatRequest):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": request.messages,
        "options": request.options,
    }

    ollama_url = f"{OLLAMA_API_BASE}/api/chat"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(ollama_url, json=payload)
            print('response',response.text)

            full_response = ""
            async for chunk in response.aiter_bytes():
                chunk_str = chunk.decode('utf-8')
                full_response += chunk_str

            return api_response(
                data={"response": full_response},
                message="Successfully fetched response from Ollama."
            )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while connecting to Ollama: {e}"
            )
