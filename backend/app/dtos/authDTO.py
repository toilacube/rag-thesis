from os import access
from pydantic import BaseModel

class LoginResponse(BaseModel):
    access_token: str

class LoginRequest(BaseModel):
    email: str
    password: str