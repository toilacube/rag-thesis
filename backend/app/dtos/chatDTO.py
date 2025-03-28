from pydantic import BaseModel

class ChatRequest(BaseModel):
    messages: list
    options: dict
